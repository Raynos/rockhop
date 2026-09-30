"""Make a silent-by-default local audition page from actual delivered files.

Audio elements use controls/preload=none; never autoplay. Excerpts are MP3,
not duplicate full-length masters. Kept beside measured remaster evidence.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def excerpt(source: Path, dest: Path, start: float, duration: float = 12, gain_db: float = 0) -> None:
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
                    '-ss', str(start), '-i', str(source), '-t', str(duration),
                    '-af', f'volume={gain_db}dB',
                    '-c:a', 'libmp3lame', '-b:a', '128k', str(dest)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT/'docs/evidence/audio-remaster/audition')
    parser.add_argument('--dsp', type=Path, default=ROOT/'harness/out/audio-remaster/dsp-ab')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    picks = json.loads((ROOT/'assets/audio/picks.json').read_text())
    baseline = (args.before/'cues.generated.ts').read_text()
    cards = []
    for cue, record in picks['cues'].items():
        entry = record['entry']
        after = args.out/(cue+'-after.mp3')
        riding = cue in ('coast', 'alpine', 'quarry', 'snowline')
        gain = -6 if riding else -4
        excerpt(ROOT/'public/audio'/entry['file'], after, entry['pre'], min(12, entry['len']), gain)
        old = re.search(rf"{cue}: \{{ file: '([^']+)'", baseline)
        before_control = ''
        if old:
            before = args.out/(cue+'-before.mp3')
            excerpt(args.before/old.group(1), before, .5, gain_db=-8 if riding else -6)
            before_control = f'<label>Original<audio controls preload="none" src="{before.name}"></audio></label>'
        metric = record['verify']
        cards.append(f'<article><h2>{html.escape(cue.title())}</h2>{before_control}'
                     f'<label>Remaster<audio controls preload="none" src="{after.name}"></audio></label>'
                     f'<small>{metric["lufs"]} LUFS · {metric["tp_dbtp"]} dBTP · '
                     f'{entry["len"]:.1f}s full cue · preview uses scene gain {gain} dB</small></article>')
    # Archived visuals are reused only after exact input/physics/timeline
    # verification; the newly rendered audio remains an offline mix proxy.
    ride = args.out.parent/'ride-remaster.mp4'
    ride_html = ('<h2>Played ride with remastered audio</h2><p>Archived C1 visuals use the identical recorded input, '
                 'verified finish and end state. Audio is a newly rendered offline mix of the delivered score, '
                 'synthesis and recordings; native browser compression and phone speakers still need listening.</p>'
                 '<video controls preload="none" src="../ride-remaster.mp4"></video>') if ride.exists() else ''
    crash = args.out.parent/'crash-restart-remaster.mp3'
    if crash.exists():
        ride_html += '<h2>Played crash and restart</h2><audio controls preload="none" src="../crash-restart-remaster.mp3"></audio>'
    sound_cards = []
    for family in ('engine', 'eight-surfaces', 'material-landings', 'crash-restart',
                   'crowd', 'race-cues', 'fallback-menu', 'fallback-results',
                   'environment-0', 'environment-1', 'environment-2',
                   'environment-3', 'environment-4', 'environment-coast',
                   'environment-alpine', 'environment-quarry', 'menu-controls'):
        controls = []
        for version in ('before', 'after'):
            source = args.dsp/(family+'-'+version+'.wav')
            if not source.exists():
                continue
            dest = args.out/(family+'-'+version+'.mp3')
            excerpt(source, dest, 0, 16)
            controls.append(f'<label>{version.title()}<audio controls preload="none" src="{dest.name}"></audio></label>')
        if controls:
            sound_cards.append(f'<article><h2>{html.escape(family.replace("-", " ").title())}</h2>'
                               +''.join(controls)+'<small>Seeded offline sound fixture</small></article>')
    recorded_cards = []
    manifest = json.loads((ROOT/'src/audio/samples/manifest.json').read_text())
    layers = {**{name: clips[0] for name, clips in manifest['oneshots'].items() if clips},
              **manifest['beds']}
    for family, clip in layers.items():
        dest = args.out/('recorded-'+family+'.mp3')
        excerpt(ROOT/'public/audio/sfx'/clip['file'], dest, clip['start'], min(12, clip['duration']),
                20*math.log10(clip['gain']))
        recorded_cards.append(f'<article><h2>{html.escape(family)}</h2><audio controls preload="none" '
                              f'src="{dest.name}"></audio><small>Delivered recording with sample gain; '
                              'event gain and ducking are heard in the played mixes.</small></article>')
    document = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Rockhop audio remaster</title>
<style>body{margin:0;padding:32px;background:#0b2227;color:#f5f0dc;font:17px/1.5 system-ui}
main{max-width:1040px;margin:auto}h1{font-size:36px;margin:0}p{color:#b6c9c5;max-width:72ch}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:20px}
article{padding:20px;background:#17363b;border:1px solid #315357;border-radius:12px}
h2{margin:0 0 12px;font-size:22px}label{display:block;margin-bottom:12px;font-size:13px;color:#c4d8d2}
audio{display:block;width:100%;margin-top:6px}small{color:#a1c1b7}video{width:100%;margin:16px 0}
</style><main><h1>Rockhop · Audio remaster</h1>
<p>New Rockhop score generated locally with MiniMax-Music3, new recorded sound layers with
MOSS-SoundEffect-v2.0, and remastered physics-driven synthesis. Press Play to audition; this page
never plays automatically. Music excerpts apply each version's scene gain so the comparison
retains the game's nominal loudness; the labels show the underlying master measurements.</p>
<p>Numerical checks cover loudness, peaks, loop boundaries and runtime behavior.
Musical taste and the balance on an actual iPhone still need your ears.</p><div class="grid">'''
    document += '\n'.join(cards)+'</div>'+ride_html+'<h2>Sound families · before / after</h2><div class="grid">'
    document += '\n'.join(sound_cards)+'</div><h2>New recorded layers</h2><div class="grid">'
    document += '\n'.join(recorded_cards)+'</div></main></html>'
    (args.out/'index.html').write_text(document)
    print(args.out/'index.html')


if __name__ == '__main__':
    main()
