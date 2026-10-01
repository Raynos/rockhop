"""Freeze external authored comparison and inventory every normal-speed frame."""
from pathlib import Path
import hashlib, json, shutil
from PIL import Image, ImageDraw
ROOT = Path('/Users/raynos/projects/games/rockhop')
SOURCE = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/hoodie-repair02')
OUT = ROOT/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/independent-v6-audit156'
TMP = ROOT/'harness/out/hero-remaster/rider-selection/v6-review156'
TMP.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
records = []
for name in ['foundation-v6-before-after-normal-speed.mp4', 'foundation-v6-inspected-before-after.png']:
    src, dst = SOURCE/'deliverables'/name, OUT/name
    if dst.exists():
        assert sha(src) == sha(dst), 'Refuse replacing archived evidence'
    else:
        shutil.copyfile(src, dst)
    records.append({'source': str(src), 'archive': str(dst), 'sha256': sha(dst)})
frames = [SOURCE/'renders/encoded-v6'/f'{i:04d}.png' for i in range(85)]
assert all(p.exists() for p in frames)
# The 12 leading and 24 trailing frames are documented identical holds.
assert len({sha(p) for p in frames[:13]}) == 1
assert len({sha(p) for p in frames[60:]}) == 1
assert len({sha(p) for p in frames}) == 49
pages = []
for start in range(0, 49, 7):
    panel = Image.new('RGB', (1152, 1852), '#171c25')
    draw = ImageDraw.Draw(panel)
    for j,k in enumerate(range(start, min(start+7,49))):
        x,y = (j%2)*576, (j//2)*463
        draw.text((x+8,y+4),f'Authored frame {k}/48 — control above / v6 below',fill='white')
        with Image.open(frames[12+k]) as im:
            panel.paste(im.resize((576,439)),(x,y+24))
    dst = TMP/f'ordered-{start//7:02d}.jpg'
    panel.save(dst, quality=94)
    pages.append(str(dst))
report = {'kind': 'Frozen authored v6 movie evidence, not game physics footage',
    'artifacts': records, 'frameCount':85, 'fps':24, 'uniqueFrames':49,
    'frameSHA256':[sha(p) for p in frames], 'orderedReviewPages':pages,
    'limits':['Frame inventory and montage creation are not a parent appearance pass.',
        'Full body and face lack matched target cameras/lighting; no score assigned.']}
(OUT/'film-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'frames':85,'unique':49,'pages':pages}))
