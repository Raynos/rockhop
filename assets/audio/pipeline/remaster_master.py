"""Detected-beat loops and verified MP3 delivery, following Wildshard Music v3.

Analysis runtime: ~/ml/music/analysis/.venv/bin/python. All neural screening
is local and serial; --screen must run after music generation has exited.
Raw sources stay outside git. --publish replaces files only after all pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, sosfilt

from analyze import SR, lufs, longest_silence, true_peak_db
from publish import circular, limiter, peaking_sos, verify, write_generated

ROOT = Path(__file__).resolve().parents[3]
TARGET = -18.0
CUES = ('menu', 'map', 'coast', 'alpine', 'quarry', 'snowline')


def stereo_silence(x: np.ndarray) -> float:
    # Sum channel energy: a wide/antiphase mix can cancel to a quiet mid
    # signal while both speakers remain audible.
    return longest_silence(np.sqrt(np.mean(x*x, axis=1)))


def encode(pcm: np.ndarray, dest: str) -> None:
    # Native headless WebKit decodes MP3 but rejects AAC even for controls.
    # Wrap padding protects music from codec priming in either browser.
    with tempfile.TemporaryDirectory() as temp:
        wav = Path(temp)/'source.wav'
        sf.write(wav, pcm, SR, subtype='FLOAT')
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
                        '-i', str(wav), '-c:a', 'libmp3lame', '-b:a', '160k', '-ar', str(SR), dest], check=True)


def read(path: Path) -> np.ndarray:
    x, sr = sf.read(path, always_2d=True, dtype='float64')
    if sr != SR:
        x = resample_poly(x, SR, sr, axis=0)
    return x


def loop_points(x: np.ndarray, requested_bpm: float) -> dict:
    mono = librosa.resample(x.mean(1), orig_sr=SR, target_sr=22050)
    onset = librosa.onset.onset_strength(y=mono, sr=22050)
    _, beats = librosa.beat.beat_track(onset_envelope=onset, sr=22050,
                                     start_bpm=requested_bpm, units='time')
    beats = np.asarray(beats)
    if len(beats) < 36:
        raise ValueError('Too few detected beats for an eight-bar loop')
    tempo = 60 / np.median(np.diff(beats))
    if tempo > requested_bpm * 1.5:
        frames = librosa.time_to_frames(beats, sr=22050)
        parity = int(np.argmax([onset[frames[k::2]].sum() for k in (0, 1)]))
        beats = beats[parity::2]
        tempo = 60 / np.median(np.diff(beats))
    # A fast twelve-bar phrase can be shorter than 24 seconds. Permit that
    # complete phrase (with beat-tracker jitter tolerance), while retaining
    # the same continuity, boundary and instrumental gates.
    minimum_duration = min(24, .95*48*60/tempo)
    S = np.abs(librosa.stft(mono))
    low = S[librosa.fft_frequencies(sr=22050) < 200].sum(0)
    low_onset = np.maximum(0, np.diff(low, prepend=low[0]))
    frames = librosa.time_to_frames(beats, sr=22050)
    downbeat = int(np.argmax([sum(low_onset[max(0, j-2):j+3].max(initial=0)
                                 for j in frames[k::4]) for k in range(4)]))
    chroma = librosa.feature.chroma_stft(S=S, sr=22050)
    mel = librosa.power_to_db(librosa.feature.melspectrogram(S=S**2, sr=22050, n_mels=32))
    mel = (mel - mel.mean(1, keepdims=True)) / (mel.std(1, keepdims=True) + 1e-6)
    feat = np.vstack([chroma, mel * .2])
    fps = 22050 / 512
    candidates = []
    for i in range(downbeat, len(beats), 4):
        a = float(beats[i])
        if a < 3 or a > len(x) / SR * .45:
            continue
        for bars in (8, 12, 16, 20, 24, 28):
            j = i + 4 * bars
            if j >= len(beats):
                continue
            b = float(beats[j])
            if not minimum_duration <= b-a <= 52 or b > len(x)/SR - 1:
                continue
            ia, ib, w = int(a*fps), int(b*fps), int(.7*fps)
            left, right = feat[:, ia-w:ia+w], feat[:, ib-w:ib+w]
            sim = float(np.sum(left*right) / (np.linalg.norm(left)*np.linalg.norm(right)+1e-12))
            rms_a = np.sqrt(np.mean(x[int((a-.3)*SR):int((a+.3)*SR)]**2))
            rms_b = np.sqrt(np.mean(x[int((b-.3)*SR):int((b+.3)*SR)]**2))
            delta = abs(20*np.log10((rms_a+1e-9)/(rms_b+1e-9)))
            candidates.append((sim - .025*delta, a, b, bars, delta))
    if not candidates:
        raise ValueError('No valid loop on detected downbeats')
    best = max(c[0] for c in candidates)
    # A good boundary must not win over a continuous groove. Check the body
    # before ranking so an otherwise usable take can yield a different cut.
    continuous = [c for c in candidates if stereo_silence(x[round(c[1]*SR):round(c[2]*SR)]) <= .5]
    if continuous:
        candidates = continuous
        best = max(c[0] for c in candidates)
    score, a, b, bars, delta = max((c for c in candidates if c[0] >= best-.05), key=lambda c:c[2]-c[1])
    start, end = round(a*SR), round(b*SR)
    return dict(start=start, end=end, bars=bars, bpm=round(bars*4*60/((end-start)/SR), 4),
                similarity=round(score, 4), boundary_level_db=round(delta, 2),
                requested_bpm=requested_bpm, detected_beats=len(beats))


def screening(path: Path, caption: str) -> dict:
    from remaster_generate import memory_gate
    memory_gate(6)
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model
    from transformers import ClapModel, ClapProcessor

    torch.set_num_threads(4)
    x, sr = sf.read(path, always_2d=True, dtype='float32')
    model = get_model('htdemucs', repo=Path.home()/'projects/weights/manual/facebook/demucs').eval()
    torch.manual_seed(0)
    y = resample_poly(x, model.samplerate, sr, axis=0).astype(np.float32)
    with torch.no_grad():
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        stems = apply_model(model, torch.from_numpy(y.T.copy())[None], device=device,
                            split=True, overlap=.25, shifts=0, progress=False)[0]
    voice = stems[model.sources.index('vocals')].cpu().numpy().T
    ratio = float(np.mean(voice**2)/max(np.mean(y**2), 1e-12))
    del stems, model
    import gc
    gc.collect()
    if device == 'mps':
        torch.mps.empty_cache()
    weights = Path.home()/'projects/weights/manual/laion/clap-htsat-fused'
    clap, proc = ClapModel.from_pretrained(str(weights)).eval(), ClapProcessor.from_pretrained(str(weights))
    mono = resample_poly(x.mean(1), 48000, sr).astype(np.float32)
    chunks = [mono[int(t*48000):int((t+8)*48000)] for t in (4, 20, 36) if len(mono)>(t+8)*48000]
    texts = [caption, 'a person singing a song, lead vocals or humming', 'instrumental music with no singing']
    with torch.no_grad():
        # Transformers versions return either a tensor or a pooled output.
        def tensor(v):
            return v if isinstance(v, torch.Tensor) else v.pooler_output
        aud = torch.nn.functional.normalize(tensor(clap.get_audio_features(**proc(
            audio=chunks, sampling_rate=48000, return_tensors='pt'))), dim=-1)
        txt = torch.nn.functional.normalize(tensor(clap.get_text_features(**proc(
            text=texts, padding=True, truncation=True, return_tensors='pt'))), dim=-1)
        sims = (aud@txt.T).mean(0).numpy()
    return dict(vocal_energy_pct=round(ratio*100, 3), cue_fit=round(float(sims[0]), 5),
                vocal_semantic=round(float(sims[1]), 5), instrumental_semantic=round(float(sims[2]), 5))


def master(pcm: np.ndarray, target: float, periodic: bool = False) -> np.ndarray:
    gain_db = target-lufs(pcm)
    for _ in range(8):
        scaled = pcm*10**(gain_db/20)
        mastered = circular(lambda y:limiter(y, -2.5), scaled) if periodic else limiter(scaled, -2.5)
        error = target-lufs(mastered)
        if abs(error)<.05:
            return mastered
        gain_db += error
    raise ValueError('Peak-limited master cannot reach target loudness')


def body_for(x: np.ndarray, points: dict, cue: str) -> np.ndarray:
    a, b = points['start'], points['end']
    body = x[a:b].copy()
    # Equal-gain one-beat crossfade into the actual approach to the loop head.
    n = min(round(60/points['bpm']*SR), a, len(body)//4)
    ramp = np.linspace(0, 1, n, endpoint=False)[:, None]
    body[-n:] = body[-n:]*(1-ramp) + x[a-n:a]*ramp
    if cue in ('coast', 'alpine', 'quarry', 'snowline'):
        body = circular(lambda y:sosfilt(peaking_sos(180, -3.5, .7), y, axis=0), body)
    return master(body, TARGET, periodic=True)


def encode_verified(body: np.ndarray, cue: str, dest: Path, target: float, looped: bool) -> dict:
    correction = 0.0
    for _ in range(6):
        pad = SR//2
        pcm = np.concatenate([body[-pad:], body, body[:pad]]) if looped else body
        encode(pcm, str(dest))
        checked = verify(str(dest), cue, len(body) if looped else 0, pcm)
        error = target-checked['lufs']
        if abs(error)<=.2:
            checked['codec_loudness_correction_db'] = round(correction, 3)
            return checked
        # Lossy encoding can change integrated level. Correct the measured
        # decoded delivery, retaining the same peak ceiling and loop state.
        correction += error
        body = master(body, lufs(body)+error, periodic=looped)
    raise ValueError(f'{cue}: decoded loudness did not converge')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('raw', type=Path)
    parser.add_argument('--screen', action='store_true')
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--check-only', action='store_true', help='Master and verify staged files without changing delivery')
    args = parser.parse_args()
    model_manifest = Path(__file__).with_name('remaster-model.json')
    model_provenance = dict(path=str(model_manifest.relative_to(ROOT)),
                            sha256=hashlib.sha256(model_manifest.read_bytes()).hexdigest())
    reports = {}
    for path in sorted(args.raw.glob('*.wav')):
        if not path.with_suffix('.json').exists():
            print(f'Skipping incomplete source: {path.name}', flush=True)
            continue
        side = json.loads(path.with_suffix('.json').read_text())
        if side['cue'] not in CUES:
            continue
        cache = path.with_suffix('.remaster.json')
        report = json.loads(cache.read_text()) if cache.exists() else {}
        if report.get('loop_version') != 4:
            x = read(path)
            report.update(stem=path.stem, cue=side['cue'], loop=loop_points(x, side['bpm']),
                          silence_s=stereo_silence(x), raw_lufs=round(lufs(x), 2),
                          raw_tp_dbtp=round(true_peak_db(x), 2), loop_version=4,
                          raw_duration_s=round(len(x)/SR, 6))
            report.pop('loop_silence_s', None)
        if 'loop_silence_s' not in report:
            x = read(path)
            report['loop_silence_s'] = stereo_silence(x[report['loop']['start']:report['loop']['end']])
        if args.screen and 'screen' not in report:
            report['screen'] = screening(path, side['caption'])
        cache.write_text(json.dumps(report, indent=2)+'\n')
        reports[path.stem] = report
        print(json.dumps(report), flush=True)
    if not args.publish and not args.check_only:
        return
    picks = {}
    for cue in CUES:
        pool = [r for r in reports.values() if r['cue']==cue and 'screen' in r and r['loop_silence_s']<=.5
                and r['loop']['similarity']>=.15
                and r['screen']['vocal_energy_pct']<=3]
        # Wildshard's analyze.py records CLAP's vocal guess as advisory: it
        # calls full-band instrumental takes vocal. Stem energy is the gate.
        if not pool:
            raise ValueError(f'{cue}: no screened instrumental candidate qualifies')
        picks[cue] = max(pool, key=lambda r:r['screen']['cue_fit'] + .1*r['loop']['similarity'])
    entries, delivery = {}, {}
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        for cue, report in picks.items():
            path = args.raw / (report['stem']+'.wav')
            body = body_for(read(path), report['loop'], cue)
            dest = stage/(cue+'.mp3')
            checked = encode_verified(body, cue, dest, TARGET, True)
            assert abs(checked['lufs']-TARGET)<=.5, (cue, checked)
            assert checked['tp_dbtp']<=-1, (cue, checked)
            for key in ('seam', 'seam_offset2112'):
                assert checked[key]['seam_click']<1 and abs(checked[key]['seam_step_db'])<1.5, (cue, checked)
            name = cue+'-'+hashlib.sha256(dest.read_bytes()).hexdigest()[:8]+'.mp3'
            dest.rename(stage/name)
            entries[cue] = dict(file=name, loop=True, pre=.5, len=len(body)/SR, gainDb=0,
                                bpm=report['loop']['bpm'], bytes=(stage/name).stat().st_size)
            delivery[cue] = dict(stem=report['stem'], entry=entries[cue], verify=checked,
                                 source=json.loads(path.with_suffix('.json').read_text()), analysis=report,
                                 raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        # Results reuses a short title excerpt with a clean ending fade.
        title = read(args.raw/(picks['menu']['stem']+'.wav'))
        rms = np.sqrt(np.mean(title.reshape(-1, 2)**2, axis=1))
        end = int(np.flatnonzero(rms>rms.max()*.01)[-1])
        sting = title[max(0, end-4*SR):end].copy()
        sting[:int(.01*SR)] *= np.linspace(0, 1, int(.01*SR))[:, None]
        sting[-int(.6*SR):] *= np.linspace(1, 0, int(.6*SR))[:, None]**2
        sting = master(sting, -16)
        dest = stage/'results.mp3'
        checked = encode_verified(sting, 'results', dest, -16, False)
        assert checked['tp_dbtp']<=-1
        assert abs(checked['lufs']+16)<=.5, checked
        name = 'results-'+hashlib.sha256(dest.read_bytes()).hexdigest()[:8]+'.mp3'
        dest.rename(stage/name)
        entries['results'] = dict(file=name, loop=False, pre=0, len=len(sting)/SR, gainDb=0,
                                  bpm=entries['menu']['bpm'], bytes=(stage/name).stat().st_size)
        delivery['results'] = dict(stem=picks['menu']['stem'], entry=entries['results'], verify=checked,
                                    trim_end_sample=end, source=delivery['menu']['source'],
                                    raw_sha256=delivery['menu']['raw_sha256'])
        total = sum(e['bytes'] for e in entries.values())
        assert total<=15*1024*1024
        if args.check_only:
            print(json.dumps(dict(total_bytes=total, verified={cue: {'stem': r['stem'], 'verify': r['verify']}
                                                               for cue, r in delivery.items()})), flush=True)
            return
        public = ROOT/'public/audio'
        for path in [*public.glob('*.m4a'), *public.glob('*.mp3')]:
            if path.name not in {e['file'] for e in entries.values()}:
                path.unlink()
        for path in stage.glob('*.mp3'):
            (public/path.name).write_bytes(path.read_bytes())
        write_generated(entries, "assets/audio/pipeline/remaster_master.py")
        (ROOT/'assets/audio/picks.json').write_text(json.dumps(
            dict(total_bytes=total, target_lufs=TARGET, model_manifest=model_provenance,
                 cues=delivery), indent=2)+'\n')
        print(f'Published {len(entries)} cues, {total} bytes', flush=True)


if __name__ == '__main__':
    main()
