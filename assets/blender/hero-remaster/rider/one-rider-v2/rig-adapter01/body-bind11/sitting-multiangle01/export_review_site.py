"""Publishable gallery of actual current clips; no character or animation edits."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from PIL import Image, ImageDraw

repo = Path('/Users/raynos/projects/games/rockhop')
recipe = Path(__file__).resolve().parent
evidence = repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/fixture02'
decoded = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/decoded-evidence/fixture02')
site = repo / 'harness/out/hero-remaster/rider-review-site'
assets = site / 'dist/media'
assets.mkdir(parents=True, exist_ok=True)
(site / '.openai').mkdir(exist_ok=True)
hosting = site / '.openai/hosting.json'
if not hosting.exists():
    hosting.write_text(json.dumps({'static': {'directory': 'dist'}}, indent=2) + '\n')
shutil.copy2(recipe / 'review.html', site / 'dist/index.html')
receipts = []
for angle in ['front', 'side', 'rear-three-quarter']:
    folder = evidence / angle
    frames = sorted((decoded / angle / 'decoded').glob('*.png'))
    assert len(frames) == 24
    board = Image.new('RGB', (1536, 2688), (24, 24, 24))
    draw = ImageDraw.Draw(board)
    nine = Image.new('RGB', (1536, 1980), (24, 24, 24))
    ndraw = ImageDraw.Draw(nine)
    for i, frame in enumerate(frames):
        im = Image.open(frame).convert('RGB')
        im.thumbnail((384, 420))
        x, y = (i % 4) * 384, (i // 4) * 448
        board.paste(im, (x, y))
        draw.text((x + 8, y + 425), f'{angle} sample {i}', fill='white')
    board.save(folder / 'decoded-all24.jpg', quality=94)
    # Nine actual samples, not generated intermediate poses.
    for i, frame_index in enumerate([0, 3, 6, 9, 12, 15, 18, 21, 23]):
        im = Image.open(frames[frame_index]).convert('RGB')
        x, y = (i % 3) * 512, (i // 3) * 660
        nine.paste(im, (x, y))
        ndraw.text((x + 12, y + 642), f'{frame_index / 12:.2f}s', fill='white')
    nine.save(assets / f'{angle}-nine.jpg', quality=94)
    Image.open(frames[0]).convert('RGB').save(assets / f'{angle}-poster.jpg', quality=92)
    for filename in ['played.mp4', 'half-speed.mp4', 'decoded-all24.jpg']:
        dest = assets / f'{angle}-{filename}'
        shutil.copy2(folder / filename, dest)
        if filename.endswith('.mp4'):
            # Lossless rewrap moves moov first for mobile streaming.
            temp = dest.with_suffix('.fast.mp4')
            subprocess.run(['ffmpeg', '-v', 'error', '-i', str(dest), '-c', 'copy',
                            '-movflags', '+faststart', str(temp)], check=True)
            temp.replace(dest)
        receipts.append({'file': str(dest.relative_to(site)), 'source': str(folder / filename),
                         'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
source = repo / 'docs/evidence/hero-remaster/one-rider-v2/parent-assembly/white-target02/target-left-actual-right.png'
shutil.copy2(source, assets / 'target-comparison.png')
# Actual short in-game evidence, clearly separate from the authored sitting clip.
for name, source in [
    ('gameplay-body', repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind11/played01/textured/played.mp4'),
    ('gameplay-face', repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind11/face-focus02/textured/played.mp4')]:
    dest = assets / f'{name}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(source), '-c', 'copy',
                    '-movflags', '+faststart', '-y', str(dest)], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(source), '-frames:v', '1',
                    '-y', str(assets / f'{name}.jpg')], check=True)
    receipts.append({'file': str(dest.relative_to(site)), 'source': str(source),
                     'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
manifest = json.loads((evidence / 'render-manifest.json').read_text())
(evidence / 'site-media-receipt.json').write_text(json.dumps({
    'sourceSHA256': manifest['sourceSHA256'], 'sourceUnchanged': True,
    'sittingAction': manifest['action'], 'normalSamples': 24,
    'halfSpeed': 'same poses with doubled presentation time; no new animation samples',
    'files': receipts, 'limits': 'Diagnostic current rider; hip, sleeve and face gates remain open.'
}, indent=2) + '\n')
print(json.dumps({'site': str(site), 'mediaFiles': len(list(assets.iterdir()))}))
