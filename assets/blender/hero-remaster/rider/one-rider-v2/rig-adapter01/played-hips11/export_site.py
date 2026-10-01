"""Add actual current hip motion to the existing private phone gallery."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

repo = Path('/Users/raynos/projects/games/rockhop')
evidence = repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-hips11/framed02'
recipe = repo / 'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/review.html'
site = repo / 'harness/out/hero-remaster/rider-review-site'
media = site / 'dist/media'
rows = []
cards = []
for angle, label in [('side', 'Side'), ('rear-three-quarter', 'Rear three-quarter')]:
    for surface in ['textured', 'gray']:
        folder = evidence / angle / surface
        report = json.loads((folder / 'report.json').read_text())
        assert report['sourceSHA256'] == 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
        assert report['cameraVersion'] == 'orbit02' and report['frames'] == 264 and not report['errors']
        stem = f'hips-{angle}-{surface}'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(folder / 'played.mp4'), '-c', 'copy', '-movflags', '+faststart', str(media / f'{stem}.mp4')], check=True)
        archive = json.loads((folder / 'frames-archive.json').read_text())
        # Actual decoded sample 75, no generated/retouched pixels.
        decoded = Path(archive['privateDecodedFrames']) / '0076.png'
        from PIL import Image
        Image.open(decoded).convert('RGB').save(media / f'{stem}.jpg', quality=93)
        shutil.copy2(folder / 'decoded-003.jpg', media / f'{stem}-frames.jpg')
        cards.append(f'<article class="card"><div class="label"><h3>{label} · {surface}</h3></div><video controls muted playsinline loop preload="metadata" poster="media/{stem}.jpg" src="media/{stem}.mp4"></video><div class="links"><a href="media/{stem}.mp4">Open video</a><a href="media/{stem}-frames.jpg">Landing frame sequence</a></div></article>')
        rows.append({'source': str(folder / 'played.mp4'), 'sourceSHA256': report['sourceSHA256'], 'video': stem + '.mp4', 'videoSHA256': hashlib.sha256((media / f'{stem}.mp4').read_bytes()).hexdigest(), 'frames':264, 'seconds':22})
section = '<h2>Hip deformation during riding</h2>\n<p>Close side and rear views of the same recorded ride: maximum lean, landing and recovery. Gray renders remove the rider textures to expose the shape. The buttocks collapse and the groin/hoodie hem opens; these defects are still being fixed. These are seated gameplay clips, separate from the standing-to-sitting animation above.</p>\n<section class="gameplay" aria-label="Matched actual hip motion">\n' + '\n'.join(cards) + '\n</section>\n'
html = recipe.read_text()
if '<h2>Hip deformation during riding</h2>' in html:
    begin = html.index('<h2>Hip deformation during riding</h2>')
    end = html.index('<details>', begin)
    html = html[:begin] + html[end:]
html = html.replace('<details>', section + '<details>', 1)
recipe.write_text(html)
(site / 'dist/index.html').write_text(html)
(evidence / 'site-media.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps({'clips':len(rows), 'site':str(site)}))
