"""Freeze T1's first export correction beside its unchanged baseline.

Run after the recorded Blender renders; no inference or source mesh mutation.
Pixel-only layouts retain source frames and expose texture/geometry separately.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[5]
ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
VARIANT = ROOT / 'variants/trellis-01-export1'
OUT = REPO / 'docs/evidence/hero-remaster/rider-search-v1/variants/trellis-01-export1'
OUT.mkdir(parents=True, exist_ok=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


inventory = json.loads((ROOT / 'trellis-files.json').read_text())
assert all(sha(f['path']) == f['sha256'] for f in inventory['files'])
model_sha = sha(VARIANT / 'working.glb')
records = []
for tier, count in [('working', 36), ('gray-full', 9)]:
    folder = VARIANT / tier
    m = json.loads((folder / 'manifest.json').read_text())
    assert m['inputSHA256'] == model_sha
    assert m['rendererSHA256'] == sha(REPO / 'assets/blender/hero-remaster/rider/search-v1/render_raw.py')
    assert m['triangles'] == 55000 and len(m['views']) == count
    ids = list(range(0, 36, 4)) if count == 36 else list(range(9))
    width, height, header = 512, 768, 28
    board = Image.new('RGB', (width * 3, (height + header) * 3), (23, 23, 23))
    draw = ImageDraw.Draw(board)
    for k, frame in enumerate(ids):
        view = m['views'][frame]
        assert abs(view['yaw'] - k * 40) < 1e-10
        x, y = k % 3 * width, k // 3 * (height + header)
        board.paste(Image.open(folder / view['file']).convert('RGB'), (x, y + header))
        draw.text((x + 8, y + 8), f'T1 export correction 1 / {tier} / yaw {k * 40}', fill='white')
    destination = OUT / tier
    destination.mkdir(exist_ok=True)
    board.save(destination / 'board.png')
    shutil.copy2(folder / 'manifest.json', destination / 'manifest.json')
    records.append({'tier': tier, 'manifestSHA256': sha(folder / 'manifest.json'),
                    'boardSHA256': sha(destination / 'board.png'),
                    'frames': [{'file': v['file'], 'yaw': v['yaw'], 'sha256': sha(folder / v['file'])} for v in m['views']]})

video = OUT / 'working/orbit.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '12', '-i',
                str(VARIANT / 'working/%04d.png'), '-frames:v', '36', '-c:v',
                'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '4', str(video)], check=True)
stream = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams',
                    'v:0', '-count_frames', '-show_entries', 'stream=nb_read_frames,r_frame_rate',
                    '-of', 'json', str(video)], text=True))['streams'][0]
assert stream['nb_read_frames'] == '36' and stream['r_frame_rate'] == '12/1'
gray_sources = [
    REPO / 'harness/out/hero-remaster/rider-search-v1/trellis-working-gray/0000.png',
    ROOT / 'rendered/trellis/01/native-gray/0000.png',
    VARIANT / 'gray-full/0000.png',
]
labels = ['T1 baseline export — gray', 'T1 native — gray', 'T1 export correction 1 — gray']
compare = Image.new('RGB', (1536, 796), (23, 23, 23))
draw = ImageDraw.Draw(compare)
for i, (source, label) in enumerate(zip(gray_sources, labels)):
    compare.paste(Image.open(source).convert('RGB'), (i * 512, 28))
    draw.text((i * 512 + 8, 8), label, fill='white')
compare.save(OUT / 'gray-comparison.png')
for filename in ['attempt.json', 'working.reduction.json']:
    shutil.copy2(VARIANT / filename, OUT / filename)
dump(OUT / 'verification.json', {
    'defect': 'T-EXPORT-01', 'attempt': 1, 'status': 'artifact integrity only; parent verdict separate',
    'originalTrellisSourcesIntact': True, 'variantSHA256': model_sha,
    'nativeSHA256': sha(ROOT / 'trellis/01.npz'), 'highfaceSHA256': sha(VARIANT / 'highface.glb'),
    'sourceRecipes': [{'path': str(ROOT / 'launcher-source' / name), 'sha256': sha(ROOT / 'launcher-source' / name)}
                      for name in ['trellis_rebake.py', 'reduce_hunyuan.py']],
    'frames': records, 'video': {'sha256': sha(video), 'frames': 36, 'fps': 12},
    'grayComparisonSources': [{'path': str(p), 'sha256': sha(p)} for p in gray_sources],
    'limits': ['No new inference, rig or physics changes', 'Baseline never overwritten',
               'Higher-face native bake and Blender DECIMATE still leave native defects'],
})
print('T1 variant: 45 frame hashes, two boards, gray comparison and 36-frame orbit verified')
