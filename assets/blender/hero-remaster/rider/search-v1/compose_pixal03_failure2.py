"""Preserve P3 baseline and both failed fixes without retouching body pixels."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[5]
ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
RUN = ROOT / 'variants/pixal03-repair2'
OUT = REPO / 'docs/evidence/hero-remaster/rider-search-v1/variants/pixal03-repair2'
OUT.mkdir(parents=True, exist_ok=True)
FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
records = []

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def layout(name, inputs, labels, columns, width=384, height=576):
    rows = (len(inputs) + columns - 1) // columns
    canvas = Image.new('RGB', (columns * width, rows * (height + 64)), (24, 27, 31))
    draw = ImageDraw.Draw(canvas)
    for i, (path, label) in enumerate(zip(inputs, labels)):
        im = Image.open(path).convert('RGB')
        im.thumbnail((width, height), Image.Resampling.LANCZOS)
        x, y = (i % columns) * width, (i // columns) * (height + 64)
        canvas.paste(im, (x + (width - im.width) // 2, y + 64))
        draw.multiline_text((x + 8, y + 8), label, font=FONT, fill='white')
    output = OUT / name
    canvas.save(output)
    records.append({'file': name, 'sha256': sha(output),
                    'sources': [{'path': str(p), 'sha256': sha(p)} for p in inputs]})

for tier, step in [('working', 4), ('gray', 1)]:
    inputs = [RUN / 'rendered' / tier / f'{i * step:04d}.png' for i in range(9)]
    layout(f'{tier}-board.png', inputs,
           [f'FAILED fix2 / {tier}\nrelative yaw {i * 40} degrees' for i in range(9)], 3)
    shutil.copyfile(RUN / 'rendered' / tier / 'manifest.json', OUT / f'{tier}-manifest.json')
layout('baseline-two-failures.png', [
    ROOT / 'diagnostics/pixal03-working-gray/0000.png',
    ROOT / 'variants/pixal03-repair1/diagnosis/rendered/0000.png',
    RUN / 'rendered/gray/0000.png',
], ['P3 baseline / gray', 'FAILED fix1 / partial export\ninvalid geometry warning',
    'FAILED fix2 / gray\nmissing body surfaces'], 3, 512, 768)
layout('painted-baseline-fix2.png', [ROOT / 'rendered/pixal/03/working/0000.png',
    RUN / 'rendered/working/0000.png'], ['P3 unchanged baseline', 'FAILED fix2 / baked export'], 2, 512, 768)
for name in ['attempt.json', 'geometry.json', 'result.json', 'process.json', 'readonly-topology.json']:
    shutil.copyfile(RUN / name, OUT / name)
log = (ROOT / 'variants/pixal03-repair2.log').read_text()
errors = [line for line in log.splitlines() if 'duplicate' in line.lower()]
(OUT / 'validation-excerpt.txt').write_text('\n'.join(errors[:20]) + f'\nTotal duplicate diagnostic lines: {len(errors)}\n')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i',
                str(RUN / 'rendered/working/%04d.png'), '-frames:v', '36',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                '-movflags', '+faststart', str(OUT / 'working-orbit.mp4')], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
    '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames,width,height,r_frame_rate',
    '-of', 'json', str(OUT / 'working-orbit.mp4')], text=True))
assert probe['streams'][0]['nb_read_frames'] == '36'
ledger = json.loads((REPO / 'docs/evidence/hero-remaster/rider-search-v1/defect-ledger.json').read_text())
sources = [s for c in ledger['candidates'] for s in c['sourceFiles'].values()]
for source in sources:
    assert sha(Path(source['path'])) == source['sha256'], source['path']
for source in ledger['runtimePreservation']['files']:
    assert sha(REPO / source['path']) == source['sha256'], source['path']
(OUT / 'verification.json').write_text(json.dumps({
    'verdict': 'FAILED P3 correction2; two-failure stop requires human choice',
    'layouts': records, 'orbit': probe, 'orbitSHA256': sha(OUT / 'working-orbit.mp4'),
    'frames': [{'path': str(p), 'sha256': sha(p)} for tier in ['working', 'gray']
               for p in sorted((RUN / 'rendered' / tier).glob('*.png'))],
    'preservedCandidateSourceFiles': len(sources),
    'preservedRuntimeFiles': len(ledger['runtimePreservation']['files']),
    'limits': ['Pixel layout only; no retouch', 'Static unrigged orbit; no animation/gameplay pass',
               'Fix1 partial export warned invalid geometry; pre-export silhouette unestablished',
               'Read-only topology comparison is diagnostic, never body acceptance'],
}, indent=2) + '\n')
print('Preserved failed2 boards, 36-frame orbit and source/runtime hashes')
