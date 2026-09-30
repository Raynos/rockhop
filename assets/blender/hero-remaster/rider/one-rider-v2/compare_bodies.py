"""Read-only common PBR/gray views of five preserved new-body donors."""
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[5]
COMP = Path('/Users/raynos/Documents/Codex/2026-09-30/task-2/comparison')
LOCAL = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
RUNTIME = LOCAL / 'one-rider-v2/body-review'
OUT = REPO / 'docs/evidence/hero-remaster/one-rider-v2/body-review'
RENDER = Path(__file__).with_name('render_matched.py')
BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 19)
rows = [
    ('H21-4', LOCAL / 'hunyuan21/04/working-display2.glb', 'hunyuan21', 0),
    ('P3 original', LOCAL / 'pixal/03/working.glb', 'pixal', 0),
    ('COMP-A Pixal', COMP / 'results/pixal/model.glb', 'pixal', 0),
    ('COMP-B H21', COMP / 'results/hunyuan21/model.glb', 'hunyuan21', 180),
    ('COMP-C TRELLIS', COMP / 'results/trellis/rider-reference-01.glb', 'trellis', 0),
]
OUT.mkdir(parents=True, exist_ok=True)
records = []
for n, (label, source, engine, x_rotation) in enumerate(rows):
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    for gray in [False, True]:
        tier = 'gray' if gray else 'pbr'
        folder = RUNTIME / str(n) / tier
        folder.mkdir(parents=True, exist_ok=True)
        command = [BLENDER, '-b', '-t', '6', '--factory-startup', '--python-exit-code', '1',
                   '--python', str(RENDER), '--', '--input', str(source), '--out', str(folder),
                   '--engine', engine, '--x-rotation', str(x_rotation), '--yaws', '0,45,90,180']
        if gray:
            command.append('--gray')
        if not (folder / 'manifest.json').exists():
            with (folder / 'render.log').open('w') as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=True)
        m = json.loads((folder / 'manifest.json').read_text())
        assert m['inputSHA256'] == before == hashlib.sha256(source.read_bytes()).hexdigest()
        assert m['inputSHA256After'] == before
        assert m['rendererSHA256'] == hashlib.sha256(RENDER.read_bytes()).hexdigest()
        assert [v['yaw'] for v in m['views']] == [0, 45, 90, 180]
        dest = OUT / str(n) / tier
        dest.mkdir(parents=True, exist_ok=True)
        (dest / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n')
        records.append({'id': label, 'tier': tier, 'source': str(source), 'sourceSHA256': before,
                        'command': command, 'frames': [{'file': v['file'], 'yaw': v['yaw'],
                        'sha256': hashlib.sha256((folder / v['file']).read_bytes()).hexdigest()} for v in m['views']]})
        print(label, tier, 'verified', flush=True)
for tier in ['pbr', 'gray']:
    image = Image.new('RGB', (5 * 360, 2 * 590), (24, 27, 31))
    draw = ImageDraw.Draw(image)
    for n, (label, *_rest) in enumerate(rows):
        for r, frame in enumerate([0, 3]):
            im = Image.open(RUNTIME / str(n) / tier / f'{frame:04d}.png').convert('RGB')
            im.thumbnail((360, 540), Image.Resampling.LANCZOS)
            x, y = n * 360, r * 590
            image.paste(im, (x, y + 50))
            draw.text((x + 8, y + 12), f'{label} / {"front" if r == 0 else "back"}', font=font, fill='white')
    image.save(OUT / f'front-back-{tier}.jpg', quality=95, subsampling=0)
(OUT / 'verification.json').write_text(json.dumps({'status': 'direction comparison only; no refinement or rigging',
    'records': records, 'rendererSHA256': hashlib.sha256(RENDER.read_bytes()).hexdigest(),
    'limits': ['Actual native PBR preserved; separate gray views', 'Same CPU camera/light/display height',
               'Different generator settings, same reference family', 'Historical production not a donor',
               'No GPU workload, source mutation, anatomy or motion acceptance']}, indent=2) + '\n')
