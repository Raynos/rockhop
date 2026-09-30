"""Rank Rockhop MOSS takes and build compact MP3 atlas/zone loops, silently.
Adapted in purpose from Wildshard sfx_build.py; no imports of that checkout.
Run with ~/ml/music/analysis/.venv/bin/python sfx_build.py <raw-dir>.
CLAP is a semantic proxy, never a listening verdict. Decoded MP3 is measured.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
import librosa
import numpy as np
import soundfile as sf
from sfx_generate import memory_gate

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RATE = 48000
CLAP = Path.home() / 'projects/weights/manual/laion/clap-htsat-fused'
MODEL_SOURCE = 'https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0'
NEGATIVES = ['a person speaking intelligible words', 'music with melody and instruments', 'silence']
BED_NAMES = ['coast', 'alpine', 'quarry', 'snowline']


def qualifies(row, family, kind):
    if row['rank'] is None:
        return False
    if row['match'] in NEGATIVES:
        return False
    limit = 2 if kind == 'bed' or family == 'grunt' else 3
    return row['rank'] <= limit and (kind != 'bed' or row['best_bed'] == family)


def selected_window(audio, offset_s, sr, kind):
    """Return the actual scored window, including nonzero source offsets."""
    if kind != 'bed':
        return audio
    start = round(offset_s * sr)
    return audio[start:min(len(audio), start + 10 * sr)].copy()


def append_atlas(atlas, cursor, audio, sr, gain):
    clip = {'file':'ATLAS', 'start':cursor / sr, 'duration':len(audio) / sr, 'gain':gain}
    pad = np.zeros((round(.15 * sr), 1), dtype='float32')
    atlas.extend([audio, pad])
    return cursor + len(audio) + len(pad), clip


def loop_metrics(decoded, start, end, sr):
    a, b = round(start * sr), min(len(decoded), round(end * sr))
    body = decoded[a:b]
    delta = float(abs(body[-1] - body[0]))
    derivative = float(np.percentile(np.abs(np.diff(body)), 95))
    n = min(round(.05 * sr), len(body) // 2)
    head = float(np.sqrt(np.mean(body[:n] ** 2)))
    tail = float(np.sqrt(np.mean(body[-n:] ** 2)))
    step = abs(20 * np.log10(max(head, 1e-9) / max(tail, 1e-9)))
    ratio = delta / max(derivative, 1e-9)
    return {'wrap_delta':delta, 'ordinary_step_p95':derivative, 'wrap_derivative_ratio':ratio, 'wrap_energy_step_db_50ms':float(step), 'seam_proxy_pass':bool(ratio <= 3 and step <= 6)}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tensor(out):
    if hasattr(out, 'norm'):
        return out
    pooled = getattr(out, 'pooler_output', None)
    return pooled if pooled is not None else out[0]


def loudness(path):
    p = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True, check=True)
    tail = p.stderr[p.stderr.rfind('Summary:'):]
    values = []
    for pat in [r'I:\s+(-?[\d.]+) LUFS', r'Peak:\s+(-?[\d.]+) dBFS']:
        m = re.search(pat, tail)
        values.append(float(m.group(1)) if m else -70.0)
    return values


def trim(x, sr, cap):
    env = np.abs(x).max(axis=1)
    idx = np.flatnonzero(env > max(env.max() * 10 ** (-42 / 20), 1e-5))
    if not len(idx):
        raise ValueError('Silent source cannot ship')
    a = max(int(idx[0]) - round(.008 * sr), 0)
    b = min(int(idx[-1]) + round(.05 * sr), len(x), a + round(cap * sr))
    y = x[a:b].copy()
    n = min(round(.025 * sr), len(y) // 4)
    y[:n] *= np.linspace(0, 1, n)[:, None]
    y[-n:] *= np.linspace(1, 0, n)[:, None]
    return y, a / sr


def normalize(x, sr, target, scratch):
    path = scratch / 'level.wav'
    sf.write(path, x, sr, subtype='FLOAT')
    level, peak = loudness(path)
    gain = min(target - level, -2.5 - peak)
    return x * 10 ** (gain / 20), {'source_lufs': level, 'source_truepeak_dbfs': peak, 'gain_db': round(gain, 3), 'target_lufs': target}


def encode(x, sr, out, scratch, mono=False):
    if out.suffix != '.mp3':
        raise ValueError('New Rockhop SFX delivery must be MP3')
    channels = 1 if mono else 2
    bitrate = '96k' if channels == 1 else '128k'
    command = ['ffmpeg', '-y', '-loglevel', 'error', '-i', str(scratch / 'encode.wav'), '-ar', str(RATE), '-ac', str(channels), '-c:a', 'libmp3lame', '-b:a', bitrate, '-write_xing', '1', str(out)]
    sf.write(scratch / 'encode.wav', x, sr, subtype='FLOAT')
    subprocess.run(command, check=True)
    level, peak = loudness(out)
    if peak > -1:
        x *= 10 ** ((-1.5 - peak) / 20)
        sf.write(scratch / 'encode.wav', x, sr, subtype='FLOAT')
        subprocess.run(command, check=True)
        level, peak = loudness(out)
    if peak > -1:
        raise ValueError(f'{out}: decoded true peak {peak} exceeds ceiling')
    decoded = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(out), '-f', 'f32le', '-ac', str(channels), '-ar', str(RATE), '-'], capture_output=True, check=True)
    decoded_channels = np.frombuffer(decoded.stdout, dtype=np.float32).reshape(-1, channels)
    decoded = decoded_channels.mean(axis=1)
    ref = x.mean(axis=1).astype(np.float32)
    n = min(len(decoded), len(ref), RATE * 8)
    corr = np.fft.irfft(np.fft.rfft(decoded[:n], 2*n) * np.conj(np.fft.rfft(ref[:n], 2*n)))
    lag = (int(np.argmax(np.r_[corr[-4096:], corr[:4096]])) - 4096) / RATE
    metrics = {'codec':'MP3 libmp3lame', 'bitrate':bitrate, 'channels':channels, 'lufs': level, 'truepeak_dbfs': peak, 'decode_lag_s': lag, 'decoded_duration_s': len(decoded) / RATE, 'bytes': out.stat().st_size, 'sha256': digest(out), 'decoded_clipped_samples': int((np.abs(decoded_channels) >= 1).sum())}
    if metrics['decoded_clipped_samples']:
        raise ValueError(f'{out}: decoded PCM clips')
    name = out.stem + '-' + metrics['sha256'][:12] + '.mp3'
    final = out.with_name(name)
    out.replace(final)
    return name, metrics, decoded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('raw', type=Path)
    ap.add_argument('--out', type=Path, default=REPO/'public/audio/sfx')
    ap.add_argument('--manifest', type=Path, default=REPO/'src/audio/samples/manifest.json')
    ap.add_argument('--report', type=Path, default=HERE/'sfx_report.json')
    ap.add_argument('--skip-clap', action='store_true', help='Technical smoke build only; never a semantic qualification')
    ap.add_argument('--require-fp32-decoder', action='store_true',
                    help='Exclude preliminary sources with rounded waveform decoder weights')
    args = ap.parse_args()
    model_manifest = HERE/'sfx-model.json'
    model_provenance = {'path':str(model_manifest.relative_to(REPO)), 'sha256':digest(model_manifest)}
    jobs = json.loads((HERE/'sfx_jobs.json').read_text())['families']
    names = list(jobs)
    descriptions = [jobs[n]['desc'] for n in names] + NEGATIVES
    resource_snapshot = None
    if not args.skip_clap:
        resource_snapshot = memory_gate(3)  # CPU CLAP + features; also run under the shared model lock.
        import torch
        from transformers import ClapModel, ClapProcessor
        torch.set_num_threads(4)
        model = ClapModel.from_pretrained(str(CLAP), local_files_only=True).eval()
        processor = ClapProcessor.from_pretrained(str(CLAP), local_files_only=True)
        with torch.no_grad():
            texts = torch.nn.functional.normalize(tensor(model.get_text_features(**processor(text=descriptions, return_tensors='pt', padding=True))), dim=-1)
        scale = float(model.logit_scale_a.detach().exp())
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {'version':1, 'model':'MOSS-SoundEffect v2.0', 'licence':'Apache-2.0', 'source':MODEL_SOURCE, 'oneshots':{}, 'beds':{}}
    report = {'semantic_proxy':'CLAP laion/clap-htsat-fused (no listening judgment)', 'qualification':{'beds':'rank<=2 and own zone leads all biome descriptions','crowd':'rank<=3','grunt':'rank<=2','negative_winner_rejects':NEGATIVES,'loop':'wrap derivative ratio<=3 and 50ms RMS energy step<=6dB','variant':'second qualified take p>=80% of best'}, 'skip_clap':args.skip_clap, 'resource_snapshot':resource_snapshot, 'incomplete_sources':[], 'families':{}, 'files':{}}
    report['qualification']['original_fp32_decoder_required'] = args.require_fp32_decoder
    report['model_manifest'] = model_provenance
    report['excluded_decoder_sources'] = []
    atlas = []
    cursor = 0
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp)
        for family, job in jobs.items():
            candidates = []
            for wav in sorted((args.raw/'moss'/family).glob('*.wav')):
                if '.partial.' in wav.name or not wav.with_suffix('.json').is_file():
                    report['incomplete_sources'].append(str(wav))
                    continue
                side = json.loads(wav.with_suffix('.json').read_text())
                if args.require_fp32_decoder and (side.get('waveform_decode') != 'float32' or
                        side.get('decoder_weights') != 'original float32 checkpoint reloaded'):
                    report['excluded_decoder_sources'].append(str(wav))
                    continue
                x, sr = sf.read(wav, always_2d=True, dtype='float32')
                if sr != RATE:
                    x = librosa.resample(x.T, orig_sr=sr, target_sr=RATE).T
                sr = RATE
                if len(x) < sr*.08 or not np.isfinite(x).all() or np.abs(x).max() < 1e-5:
                    continue
                if job['kind'] == 'oneshot':
                    x, offset = trim(x.mean(axis=1, keepdims=True), sr, float(job['duration']))
                else:
                    offset = 0
                # Nonverbal reactions are short; environmental takes are scored on several ten-second windows.
                windows = [(0, x)] if len(x) <= sr*10 else [(i/sr, x[i:i+sr*10]) for i in range(0, len(x)-sr*10+1, sr*5)]
                scores = []
                for start, y in windows:
                    if args.skip_clap:
                        scores.append({'rank':None, 'match':None, 'p':None, 'offset_s':start, 'best_bed':None})
                    else:
                        with torch.no_grad():
                            inp = processor(audio=[y.mean(axis=1)], sampling_rate=sr, return_tensors='pt')
                            features = torch.nn.functional.normalize(tensor(model.get_audio_features(**inp)), dim=-1)
                            sims = (features @ texts.T)[0]
                        idx = names.index(family)
                        bed_match = max(BED_NAMES, key=lambda bed:float(sims[names.index(bed)]))
                        scores.append({'rank':int((sims>sims[idx]).sum())+1, 'p':round(float(torch.softmax(sims*scale,0)[idx]),4), 'match':descriptions[int(sims.argmax())], 'offset_s':start, 'best_bed':bed_match})
                passing = [score for score in scores if qualifies(score, family, job['kind'])]
                best = max(passing or scores, key=lambda s: s['p'] or 0)
                subtype = sf.info(wav).subtype
                fullscale = int((np.abs(x) >= .99997).sum())
                candidates.append({'wav':str(wav), 'sha256':digest(wav), 'source':side, 'source_format':subtype, 'source_peak':float(np.abs(x).max()), 'source_fullscale_samples':fullscale, 'source_pcm_rail_samples':fullscale if subtype not in ('FLOAT', 'DOUBLE') else 0, 'trim_start_s':offset, 'windows':scores, **best, 'audio':x})
            if not candidates:
                report['families'][family] = {'fallback':'no valid source'}
                continue
            candidates.sort(key=lambda c: (qualifies(c, family, job['kind']), c['p'] or 0), reverse=True)
            selected = candidates[0]
            report['families'][family] = {'selected_seed':selected['source']['seed'], 'takes':[{k:v for k,v in c.items() if k!='audio'} for c in candidates]}
            if not args.skip_clap and not qualifies(selected, family, job['kind']):
                report['families'][family]['fallback'] = 'CLAP family/negative qualification failed; focused retry required'
                continue
            x = selected_window(selected['audio'], selected['offset_s'], sr, job['kind'])
            report['families'][family]['selected_trim_start_s'] = selected['trim_start_s'] + selected['offset_s']
            if job['kind'] == 'oneshot':
                variants = [selected] + [c for c in candidates[1:] if qualifies(c, family, job['kind']) and c['p'] >= selected['p'] * .8][:1] if not args.skip_clap else [selected]
                manifest['oneshots'][family] = []
                variant_metrics = []
                for variant in variants:
                    y, metrics = normalize(variant['audio'], sr, -18, scratch)
                    cursor, clip = append_atlas(atlas, cursor, y, sr, .55 if family=='grunt' else .4)
                    manifest['oneshots'][family].append(clip)
                    variant_metrics.append({'seed':variant['source']['seed'], **metrics})
                report['families'][family]['selected_seeds'] = [v['source']['seed'] for v in variants]
                report['families'][family]['normalization'] = variant_metrics
            else:
                # Crossfade into the removed head. At wrap, the last sample continues the head at .75 s.
                n = min(round(.75*sr), len(x)//4)
                fade = np.linspace(0,1,n)[:,None]
                y = x[n:].copy()
                y[-n:] = x[-n:]*(1-fade)+x[:n]*fade
                y, metrics = normalize(y, sr, -26, scratch)
                # Decode loop points away from codec start/end transients: 200 ms of cyclic guard at both edges.
                guard = min(round(.2 * sr), len(y) // 4)
                guarded = np.concatenate([y[-guard:], y, y[:guard]])
                name, encoded, decoded = encode(guarded, sr, args.out/f'bed-{family}.mp3', scratch)
                lag = max(0,encoded['decode_lag_s']) + guard / sr
                duration = min(len(y)/sr,encoded['decoded_duration_s']-lag)
                encoded.update(loop_metrics(decoded, lag, lag + duration, sr))
                if encoded['seam_proxy_pass'] or args.skip_clap:
                    manifest['beds'][family] = {'file':name, 'start':lag, 'duration':duration, 'gain':.7}
                else:
                    report['families'][family]['fallback'] = 'Decoded loop proxy failed; focused retry required'
                    review = args.raw / 'review'
                    review.mkdir(parents=True, exist_ok=True)
                    (args.out / name).replace(review / name)
                report['families'][family]['normalization'] = metrics
                report['families'][family]['decoded_metrics'] = encoded
                if family in manifest['beds']:
                    report['files'][name] = encoded
            print(f'[sfx_build] {family}: seed {selected["source"]["seed"]}, CLAP rank {selected["rank"]}', flush=True)
        if atlas:
            # Native macOS WebKit leaves a 576-sample offset on mono MP3.
            # Stereo MP3 aligns with Chromium/ffmpeg; runtime averages the
            # identical channels back to mono before its equal-power pan.
            stereo_atlas = np.repeat(np.concatenate(atlas), 2, axis=1)
            name, encoded, _ = encode(stereo_atlas,RATE,args.out/'reactions.mp3',scratch)
            encoded['runtime_channel_mapping'] = 'Dual mono averaged to mono before equal-power panning'
            report['files'][name] = encoded
            for clips in manifest['oneshots'].values():
                for clip in clips:
                    clip['file'] = name
                    clip['start'] += max(0,encoded['decode_lag_s'])
                    if clip['start']+clip['duration'] > encoded['decoded_duration_s']:
                        raise ValueError('Atlas clip exceeds decoded duration')
        report['total_bytes'] = sum(v['bytes'] for v in report['files'].values())
        for family, row in report['families'].items():
            row['shipped'] = family in manifest['oneshots'] or family in manifest['beds']
        args.manifest.write_text(json.dumps(manifest,indent=2)+'\n')
        args.report.write_text(json.dumps(report,indent=2)+'\n')
        # Exact selected prompts, seeds and generator provenance travel with the shipped assets.
        (args.out/'provenance.json').write_text(json.dumps({'model_source':MODEL_SOURCE,'model_manifest':model_provenance,'model_licence':'Apache-2.0','weights_redistributed':False,'review':'Objective semantic/loudness/seam proxies; human listening pending','qualification':report['qualification'],'families':{f:{'shipped':v['shipped'],'seed':v.get('selected_seed'),'selected_seeds':v.get('selected_seeds'),'selected_trim_start_s':v.get('selected_trim_start_s'),'takes':v.get('takes',[]),'fallback':v.get('fallback')} for f,v in report['families'].items()},'files':report['files']},indent=2)+'\n')
        print(f'[sfx_build] {len(report["files"])} files, {report["total_bytes"]} bytes',flush=True)

if __name__ == '__main__':
    main()
