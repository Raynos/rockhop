"""Mix the exact-input silent ride witness with delivered score/sample assets.

This is an offline audition proxy using the live gains and recorded model
envelopes, not an audio recording from a physical phone. Physics/input hash
and full timeline are checked against the source film before muxing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from publish import decode, limiter
from analyze import SR, lufs, true_peak_db

ROOT = Path(__file__).resolve().parents[3]


def envelope(events: dict, key: str, count: int, initial: float, tau: float,
             *, decibels: bool = False, music: bool = False) -> np.ndarray:
    rows = events['envelope']
    if not rows or abs(rows[0]['time']) > 1/SR:
        raise ValueError('Envelope must begin at the witness origin')
    out = np.empty(count)
    value, previous_db, target = initial, 0.0, initial
    time_constant = tau
    for i, row in enumerate(rows):
        at = min(count, round(row['time']*SR))
        end = min(count, round(rows[i+1]['time']*SR)) if i+1<len(rows) else count
        requested = row[key]
        if not music or abs(requested-previous_db)>=.5:
            if music:
                time_constant = .06 if requested>previous_db else .4
            target = 10**(-requested/20) if decibels else requested
            previous_db = requested
        n = max(0, end-at)
        if n:
            # Web Audio setTargetAtTime follows this exponential exactly.
            out[at:end] = target+(value-target)*np.exp(-np.arange(n)/(SR*time_constant))
            value = target+(value-target)*np.exp(-n/(SR*time_constant))
    return out


def loop(buffer: np.ndarray, start: float, length: float, count: int) -> np.ndarray:
    a, n = round(start*SR), round(length*SR)
    if n <= 0 or a+n > len(buffer):
        raise ValueError('Loop points exceed decoded PCM')
    return buffer[a:a+n][np.arange(count)%n]


def mix(witness: Path, stem: str, zone: str) -> tuple[np.ndarray, dict]:
    events = json.loads((witness/(stem+'-events.json')).read_text())
    pcm, sr = sf.read(witness/(stem+'-procedural.wav'), always_2d=True)
    assert sr == SR
    cues = json.loads((ROOT/'assets/audio/picks.json').read_text())['cues']
    music = cues[zone]['entry']
    score = loop(decode(str(ROOT/'public/audio'/music['file'])), music['pre'], music['len'], len(pcm))
    music_gain = 10**(-6/20)*envelope(events, 'musicDuckDb', len(pcm), 1, .4, decibels=True, music=True)
    fade = np.minimum(1, np.arange(len(pcm))/(SR*.35))
    transition = next((r['time'] for r in events['envelope'] if r['scene']=='results'), None)
    timeline = np.arange(len(pcm))/SR
    if transition is not None:
        elapsed = np.maximum(0, timeline-transition)
        fade *= np.where(timeline<transition, 1, np.where(elapsed<.96, np.exp(-elapsed/.16), 0))
        sting = cues['results']['entry']
        decoded = decode(str(ROOT/'public/audio'/sting['file']))
        at, start = round(transition*SR), round(sting['pre']*SR)
        n = min(len(pcm)-at, round(sting['len']*SR), len(decoded)-start)
        attack = np.minimum(1, np.arange(n)/(SR*.02))
        pcm[at:at+n] += decoded[start:start+n]*(10**(-4/20)*music_gain[at:at+n]/10**(-6/20)*attack)[:, None]
    pcm += score * (music_gain*fade)[:, None]
    manifest_bytes = (ROOT/'src/audio/samples/manifest.json').read_bytes()
    assert events['audio']['sampleManifestSha256'] == hashlib.sha256(manifest_bytes).hexdigest(), 'Re-render the witness after sample delivery changes'
    manifest = json.loads(manifest_bytes)
    cache = {}
    def buffer(file: str) -> np.ndarray:
        if file not in cache:
            cache[file] = decode(str(ROOT/'public/audio/sfx'/file))
        return cache[file]
    recorded = np.zeros_like(pcm)
    bed = manifest['beds'].get(zone)
    if bed:
        sample = loop(buffer(bed['file']), bed['start'], bed['duration'], len(pcm))
        if sample.shape[1] == 1:
            sample = np.repeat(sample, 2, axis=1)
        gain = envelope(events, 'ambientGain', len(pcm), 0, .2)*bed['gain']
        if transition is not None:
            gain[timeline>=transition] = 0 # Live SamplePlayer stops its bed on entering results.
        recorded += sample*gain[:, None]
    counts = {}
    restart_times = [r['time'] for r in events['events'] if r['event']['type']=='restart']
    last_transient_time = -1.0
    for transient in events['transients']:
        if any(last_transient_time < r <= transient['time'] for r in restart_times):
            counts.clear()
        last_transient_time = transient['time']
        family = transient['family']
        clips = manifest['oneshots'].get(family)
        if not clips:
            raise ValueError(f'Witness suppressed {family} but delivered sample is missing')
        counter = counts.get(family, 0)
        clip = clips[counter%len(clips)]
        counts[family] = counter+1
        src = buffer(clip['file'])
        a, n = round(clip['start']*SR), round(clip['duration']*SR)
        sample = src[a:a+n].mean(1)
        t = transient['time']
        stop = next((r for r in restart_times if r > t), len(pcm)/SR)
        if transition is not None and t<transition:
            stop = min(stop, transition)
        sample = sample[:max(0, round((stop-t)*SR))]
        if not len(sample):
            continue
        pan = np.clip(transient['pan'], -1, 1)
        gains = np.array([np.cos((pan+1)*np.pi/4), np.sin((pan+1)*np.pi/4)])
        ramp = np.ones(len(sample))
        f = min(round(.008*SR), len(sample))
        ramp[:f] *= np.linspace(0, 1, f)
        f = min(round(.025*SR), len(sample))
        ramp[-f:] *= np.linspace(1, 0, f)
        sample = sample[:, None]*gains*np.clip(transient['gain'], 0, 1)*clip['gain']*ramp[:, None]
        at = round(t*SR)
        n = min(len(sample), len(pcm)-at)
        if n>0:
            recorded[at:at+n] += sample[:n]
    duck = envelope(events, 'duckDb', len(pcm), 1, .015, decibels=True)
    pcm += recorded*duck[:, None]
    # Default master slider .8 is squared in the live system. An offline
    # lookahead safety limiter approximates the downstream shared compressor.
    pcm = limiter(pcm*.8**2, -2.5)
    report = dict(input=events['recording'], physics=events['physics'], channels=2,
                  sample_rate=SR, duration_s=len(pcm)/SR, master_slider=.8,
                  lufs=round(lufs(pcm), 2), tp_dbtp=round(true_peak_db(pcm), 2),
                  music=dict(ride_file=music['file'], results_file=cues['results']['entry']['file'], results_at_s=transition,
                             assumption='Predecoded cues; actual loading latency is covered by runtime regressions, not this offline proxy.'),
                  limit='Offline mix proxy; neural/DSP assets and model envelopes are real, native browser compressor and phone speakers are not recorded.')
    return pcm, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--witness', type=Path, default=ROOT/'harness/out/audio-remaster')
    parser.add_argument('--out', type=Path, default=ROOT/'docs/evidence/audio-remaster')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    reports = {}
    for stem, dest in [('c1-ride', 'ride-remaster'), ('c1-crash-restart', 'crash-restart-remaster')]:
        pcm, report = mix(args.witness, stem, 'coast')
        wav = args.out/(dest+'.wav')
        sf.write(wav, pcm, SR, subtype='PCM_16')
        report['pcm_sha256'] = hashlib.sha256(pcm.astype('<f4').tobytes()).hexdigest()
        if stem == 'c1-ride':
            source = ROOT/'docs/evidence/course-remaster/baseline-clips/c1-low-tide'
            capture = json.loads((source/'capture.json').read_text())
            assert report['input']['sha256'] == capture['recording']['sha256']
            finish = report['physics']['finish']
            assert finish['hash'] == capture['verifiedFinish']['hash']
            assert finish['time'] == capture['verifiedFinish']['timeSeconds']
            assert finish['tick'] == capture['verifiedFinish']['tick']
            assert report['physics']['finalHash'] == capture['capture']['endOfClipHash']
            assert report['duration_s'] == capture['capture']['durationSeconds']
            assert hashlib.sha256((source/'clip.mp4').read_bytes()).hexdigest() == capture['video']['sha256']
            report['video_source'] = str(source.relative_to(ROOT)/'clip.mp4')
            report['capture'] = capture
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
                            '-i', str(source/'clip.mp4'), '-i', str(wav), '-map', '0:v:0', '-map', '1:a:0',
                            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart',
                            str(args.out/(dest+'.mp4'))], check=True)
        else:
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(wav),
                            '-c:a', 'libmp3lame', '-b:a', '128k', str(args.out/(dest+'.mp3'))], check=True)
        decoded_path = args.out/(dest+('.mp4' if stem=='c1-ride' else '.mp3'))
        checked = decode(str(decoded_path))
        report['decoded_tp_dbtp'] = round(true_peak_db(checked), 2)
        assert report['decoded_tp_dbtp']<=-1, report
        reports[stem] = report
        wav.unlink()
    (args.out/'played-mixes.json').write_text(json.dumps(reports, indent=2)+'\n')
    print(json.dumps({k:{key:v[key] for key in ('lufs', 'tp_dbtp', 'decoded_tp_dbtp')} for k,v in reports.items()}))


if __name__ == '__main__':
    main()
