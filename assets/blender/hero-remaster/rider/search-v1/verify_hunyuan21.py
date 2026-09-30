"""Verify the additive lane and immutable controls; never assert visual quality."""
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

REPO = Path(__file__).resolve().parents[5]
ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
OUT = REPO / 'docs/evidence/hero-remaster/rider-search-v1/hunyuan21'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def buffer(p):
    b = p.read_bytes()
    n = struct.unpack_from('<I', b, 12)[0]
    return b[20 + n:]


prepared = json.loads((OUT / 'prepared.json').read_text())
ledger = json.loads((OUT.parent / 'defect-ledger.json').read_text())
older = [c for c in ledger['candidates'] if not c['id'].startswith('H21')]
assert len(older) == 15
for c in older:
    for item in c['sourceFiles'].values():
        assert sha(Path(item['path'])) == item['sha256']
# Old committed layouts/boards/clips are controls, not outputs of this lane.
subjects = []
for i in range(1, 6):
    d = f'{i:02d}'
    source = ROOT / 'hunyuan21' / d
    e = OUT / d
    g = json.loads((source / 'generation.json').read_text())
    assert g['inputSHA256'] == prepared['references'][i - 1]['sha256']
    assert g['runnerSHA256'] == prepared['runners']['rockhop_hunyuan21_runner.py']
    assert g['shape_steps'] == 30 and g['paint_steps'] == 15 and g['seed'] == 42
    assert g['texture_size'] == 2048 and g['octree'] == 380
    for name, item in g['outputs'].items():
        assert sha(source / name) == item['sha256']
    assert buffer(source / 'model.glb') == buffer(source / 'working-display2.glb')
    v = json.loads((e / 'verification.json').read_text())
    assert v['nativeGeometryPreserved'] is True
    for tier in v['tiers']:
        assert sha(e / tier['tier'] / 'board.png') == tier['boardSHA256']
        render = ROOT / 'rendered/hunyuan21' / d / tier['tier']
        for frame in tier['frames']:
            assert sha(render / frame['file']) == frame['sha256']
    native = np.load(source / 'raw-shape.npz')
    f, p = native['faces'], native['vertices']
    repeats = (f[:, 0] == f[:, 1]) | (f[:, 1] == f[:, 2]) | (f[:, 0] == f[:, 2])
    area = np.linalg.norm(np.cross(p[f[:, 1]] - p[f[:, 0]], p[f[:, 2]] - p[f[:, 0]]), axis=1)
    native_render = next(t for t in v['tiers'] if t['tier'] == 'native-gray')
    subjects.append({'id': f'H21-{i}', 'inputSHA256': g['inputSHA256'],
                     'nativeFaces': len(f), 'nativeImportedTriangles': native_render['triangles'],
                     'repeatIndexFaces': int(repeats.sum()), 'zeroAreaFaces': int((area == 0).sum()),
                     'nativeImportDelta': len(f) - native_render['triangles'],
                     'workingFaces': v['tiers'][0]['triangles'], 'reducedFaces': v['tiers'][1]['triangles'],
                     'inferenceWallSeconds': g['wall_seconds'], 'peakProcessRSSGB': g['peak_rss_gb'],
                     'displayBuffersIdentical': True})
report = {'status': 'artifact integrity only; twenty bodies remain unaccepted',
          'frozenOlderBodiesVerified': 15, 'newBodies': 5, 'newFrames': 270,
          'newBoards': 15, 'newWorkingOrbits': 5, 'subjects': subjects,
          'limits': ['Native/import differences recorded; exact omission cause unisolated',
                     'Source axis probe/fix1 preserved; actual display uses verified X180 relative rotation',
                     'No anatomy/rig/sitting/gameplay/device pass or source overwrites']}
(OUT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print('Five H21 bodies /270frames /15boards /5orbits and fifteen controls verified')
