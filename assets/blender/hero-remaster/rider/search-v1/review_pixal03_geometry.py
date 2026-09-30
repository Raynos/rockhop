"""Read-only P3 gray export/topology diagnostics; never repairs a body."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
import trimesh
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[5]
ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
OUT = REPO / 'docs/evidence/hero-remaster/rider-search-v1/diagnostics/pixal03'
OUT.mkdir(parents=True, exist_ok=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


records = []
for tier in ['working', 'reduced']:
    source = ROOT / 'pixal/03' / f'{tier}.glb'
    folder = ROOT / 'diagnostics' / f'pixal03-{tier}-gray'
    destination = OUT / tier
    destination.mkdir(exist_ok=True)
    before = sha(source)
    m = json.loads((folder / 'manifest.json').read_text())
    assert m['inputSHA256'] == before and len(m['views']) == 9
    assert m['rendererSHA256'] == sha(REPO / 'assets/blender/hero-remaster/rider/search-v1/render_raw.py')
    assert m['grayDiagnostic'] is True
    board = Image.new('RGB', (1536, 2388), (23, 23, 23))
    draw = ImageDraw.Draw(board)
    frames = []
    for k, v in enumerate(m['views']):
        assert abs(v['yaw'] - 180 - k * 40) < 1e-10
        frame = folder / v['file']
        x, y = k % 3 * 512, k // 3 * 796
        board.paste(Image.open(frame).convert('RGB'), (x, y + 28))
        draw.text((x + 8, y + 8), f'P3 {tier} geometry / relative yaw {k * 40}', fill='white')
        frames.append({'file': v['file'], 'sha256': sha(frame), 'yaw': v['yaw']})
    board.save(destination / 'board.png')
    shutil.copy2(folder / 'manifest.json', destination / 'manifest.json')
    mesh = trimesh.load(source, force='mesh', process=False)
    vertices_before = len(mesh.vertices)
    # Analysis copy ignores UV/normal seams for edge counts only, never repair.
    mesh.merge_vertices(merge_tex=True, merge_norm=True, digits_vertex=8)
    counts = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))
    assert sha(source) == before
    records.append({'tier': tier, 'sourceSHA256': before, 'verticesBefore': vertices_before,
                    'positionWeldedVertices': len(mesh.vertices), 'sourceFaces': len(mesh.faces),
                    'blenderImportedTriangles': m['triangles'],
                    'boundaryEdges': int((counts == 1).sum()),
                    'nonManifoldEdges': int((counts > 2).sum()),
                    'watertightAfterPositionWeld': bool(mesh.is_watertight),
                    'frames': frames, 'boardSHA256': sha(destination / 'board.png')})
(OUT / 'verification.json').write_text(json.dumps({
    'status': 'diagnosis only, no correction attempted', 'candidate': 'P3',
    'records': records, 'sourceBytesUnchanged': True,
    'positionWeldAnalysis': {'digits': 8, 'mergeTextureAndNormalSeams': True, 'writesSource': False},
    'limits': ['Edge counts depend on the declared weld and do not certify visible anatomy or rig quality',
               'No rig, sitting, physics or contact qualification',
               'GLB/import counts differ by one triangle per export; cause not isolated, not rounded away'],
}, indent=2) + '\n')
print('P3 gray exports: eighteen exact-yaw frames, source hashes and read-only topology verified')
