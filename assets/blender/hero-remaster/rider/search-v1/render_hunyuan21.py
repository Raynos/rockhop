"""Additive 2.1 body review; common frozen camera, original lane untouched."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import numpy as np
import trimesh
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument('--design', choices=['01', '02', '03', '04', '05'], required=True)
a = parser.parse_args()
REPO = Path(__file__).resolve().parents[5]
ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
RENDER = Path(__file__).with_name('render_raw.py')
BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'
source = ROOT / 'hunyuan21' / a.design
base = ROOT / 'rendered/hunyuan21' / a.design
evidence = REPO / 'docs/evidence/hero-remaster/rider-search-v1/hunyuan21' / a.design
base.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


assert sha(RENDER) == '38da920203ac1f1b7e9cfb085eb6783702e5c4487c710a6022768fdd5658ddae'
generation = json.loads((source / 'generation.json').read_text())
for name, item in generation['outputs'].items():
    assert sha(source / name) == item['sha256']
assert generation['seed'] == 42 and generation['shape_steps'] == 30
assert generation['texture_size'] == 2048
# Native trimesh GLB retains the original vertices/indices (GLB stores float32).
native = np.load(source / 'raw-shape.npz')
mesh = trimesh.load(source / 'raw-shape.glb', process=False, force='mesh')
assert np.array_equal(mesh.faces, native['faces'])
assert np.array_equal(mesh.vertices, native['vertices'].astype(np.float32))
reduced = source / 'reduced.glb'
if not reduced.exists():
    with (source / 'reduction.log').open('w') as log:
        subprocess.run([BLENDER, '-b', '--factory-startup', '--python-exit-code', '1',
                        '--python', str(ROOT / 'launcher-source/reduce_hunyuan.py'), '--',
                        str(source / 'model.glb'), str(reduced), '20000', '1024'],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
records = []
for tier, model, n, gray in [('working', source / 'model.glb', 36, False),
                            ('reduced', reduced, 9, False),
                            ('native-gray', source / 'raw-shape.glb', 9, True)]:
    folder = base / tier
    folder.mkdir(exist_ok=True)
    before = sha(model)
    if not (folder / 'manifest.json').exists():
        cmd = [BLENDER, '-b', '--factory-startup', '--python-exit-code', '1',
               '--python', str(RENDER), '--', '--input', str(model),
               '--out', str(folder), '--frames', str(n)]
        if gray:
            cmd.append('--gray')
        with (folder / 'render.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
    m = json.loads((folder / 'manifest.json').read_text())
    assert m['inputSHA256'] == before == sha(model)
    assert m['rendererSHA256'] == sha(RENDER) and len(m['views']) == n
    board = Image.new('RGB', (1536, 2388), (23, 23, 23))
    draw = ImageDraw.Draw(board)
    ids = list(range(0, 36, 4)) if n == 36 else list(range(9))
    for k, frame in enumerate(ids):
        assert abs(m['views'][frame]['yaw'] - k * 40) < 1e-10
        x, y = k % 3 * 512, k // 3 * 796
        board.paste(Image.open(folder / f'{frame:04d}.png').convert('RGB'), (x, y + 28))
        draw.text((x + 8, y + 8), f'H21-{int(a.design)} / {tier} / yaw {k * 40}', fill='white')
    board.save(folder / 'board.png')
    dest = evidence / tier
    dest.mkdir(exist_ok=True)
    for name in ['board.png', 'manifest.json']:
        shutil.copy2(folder / name, dest / name)
    if n == 36:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '12', '-i',
                        str(folder / '%04d.png'), '-frames:v', '36', '-c:v', 'libx264',
                        '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '4',
                        str(folder / 'orbit.mp4')], check=True)
        video = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames',
            '-show_entries', 'stream=nb_read_frames,r_frame_rate', '-of', 'json',
            str(folder / 'orbit.mp4')], text=True))['streams'][0]
        assert video['nb_read_frames'] == '36' and video['r_frame_rate'] == '12/1'
        shutil.copy2(folder / 'orbit.mp4', dest / 'orbit.mp4')
    records.append({'tier': tier, 'triangles': m['triangles'], 'sourceSHA256': before,
                    'boardSHA256': sha(dest / 'board.png'), 'frames': [
                        {'file': v['file'], 'yaw': v['yaw'], 'sha256': sha(folder / v['file'])}
                        for v in m['views']]})
shutil.copy2(source / 'generation.json', evidence / 'generation.json')
shutil.copy2(reduced.with_suffix('.reduction.json'), evidence / 'reduction.json')
(evidence / 'verification.json').write_text(json.dumps({
    'status': 'artifact integrity; body remains unaccepted', 'id': 'H21-' + str(int(a.design)),
    'nativeFaces': len(native['faces']), 'nativeGeometryPreserved': True,
    'rendererSHA256': sha(RENDER), 'tiers': records,
    'limits': ['2.1 30step shape /15step PBR differs from older turbo recipe',
               'Common metallic0 diagnostic only; source PBR preserved',
               'No rig, sitting, gameplay or device acceptance']}, indent=2) + '\n')
print('H21-' + str(int(a.design)), 'native/working/reduced and 54 frames verified')
