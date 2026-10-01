"""Parent source preservation and literal full-motion failure review; CPU only."""
from pathlib import Path
import hashlib
import json
import struct
import numpy as np

ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT = Path('docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01')
source = ROOT/'rig-adapter01/body-bind34/rider.glb'
raw = source.read_bytes()
sha = lambda b: hashlib.sha256(b).hexdigest()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20+n])
blob = raw[28+n:]

def acc(i):
    a = doc['accessors'][i]
    v = doc['bufferViews'][a['bufferView']]
    widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    dtype = {5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]
    assert 'byteStride' not in v and 'sparse' not in a
    return np.frombuffer(blob, dtype=dtype, count=a['count']*widths[a['type']],
        offset=v.get('byteOffset', 0)+a.get('byteOffset', 0)).reshape(a['count'], -1)

cuff_path = ROOT/'garment-rebuild01/cuff-ankle-transition155/transition155.npz'
neck_path = ROOT/'garment-rebuild01/shoulder-transition155/transition.npz'
cuff = np.load(cuff_path)
neck = np.load(neck_path)
fit = np.load(ROOT/'garment-rebuild01/cage04/fit04.npz')
assert np.array_equal(cuff['native_positions'], fit['positions'])
source_checks = []
for i in range(2):
    primitive = doc['meshes'][0]['primitives'][i]
    for name in ['POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0']:
        assert np.array_equal(cuff[f'source{i}_{name}'], acc(primitive['attributes'][name]))
        source_checks.append(f'primitive{i}:{name}')
hood = doc['meshes'][0]['primitives'][2]
for field, attr in [('protectedHoodPositions', 'POSITION'), ('protectedHoodNormals', 'NORMAL'),
                    ('protectedHoodUV', 'TEXCOORD_0')]:
    assert np.array_equal(neck[field], acc(hood['attributes'][attr]))
assert np.array_equal(neck['protectedHoodTriangles'], acc(hood['indices']).reshape(-1, 3))
source_checks.extend(['hood:POSITION', 'hood:NORMAL', 'hood:TEXCOORD_0', 'hood:indices'])
assert int((cuff['native_weights19'] > 0).sum(1).max()) <= 4
motion = json.loads((OUT/'full-motion155/report.json').read_text())
assert motion['frames'] == 480 and motion['physicalPoseEveryFrame']
assert motion['sourceSHA256'] == sha(raw)
assert len({o['sha256'] for o in motion['outputs']}) == 1
record = motion['outputs'][0]
bytes_ = (ROOT/'garment-rebuild01/full-motion155'/record['file']).read_bytes()
assert sha(bytes_) == record['sha256']
M = np.frombuffer(bytes_, dtype='<f8').reshape(480, 19, 4, 4).transpose(0, 1, 3, 2)
offender_doc = json.loads((OUT/'cuff-ankle-transition155/frame39-offenders.json').read_text())
assert offender_doc['frame'] == 39
failures = []
for offender in offender_doc['offenders']:
    ids = offender['nativeVertexIDs']
    P = cuff['native_positions'][ids]
    W = cuff['native_weights19'][ids]
    posed = np.einsum('vj,jab,vb->va', W, M[39, :, :3, :], np.c_[P, np.ones(len(P))])
    assert np.allclose(posed, offender['newPosedPositions'], atol=1e-14, rtol=0)
    area = np.linalg.norm(np.cross(P[1]-P[0], P[2]-P[0]))
    new_area = np.linalg.norm(np.cross(posed[1]-posed[0], posed[2]-posed[0]))
    ratio = float(new_area/area)
    assert abs(ratio-offender['newAreaRatio']) < 1e-12 and ratio < .25
    failures.append({'frame': 39, 'nativeQuad': offender['sourceNativeQuadID'],
        'vertices': ids, 'areaRatio': ratio})
shoulder = json.loads((OUT/'shoulder-transition155/audit-report.json').read_text())
assert shoulder['actualRidingFrames'] == 480 and shoulder['maximumSeamPositionDeltaM'] == 0
crossings = [{k: row[k] for k in ['sample', 'strictNoncoplanarCrossings']}
    for row in shoulder['intersectionRows']]
assert crossings[0]['sample'] == 'rest' and crossings[0]['strictNoncoplanarCrossings'] == 185
assert source.read_bytes() == raw
report = {'sourceSHA256': sha(raw), 'cuffArtifactSHA256': sha(cuff_path.read_bytes()),
    'shoulderArtifactSHA256': sha(neck_path.read_bytes()), 'sourceChecks': source_checks,
    'nativeCuffRestPositionsExact': True, 'nativeMaximumSkinInfluences': 4,
    'matrixFrames': 480, 'allPrimitiveMatrixBytesEqual': True,
    'independentlyReproducedCuffFailures': failures, 'shoulderCrossingWitnesses': crossings,
    'parentDecision': 'Retain cuff/ankle regional progress, reject whole transition candidate. Stop annular shoulder construction; build anatomical upper yoke. Correct literal wrist failures before moving appearance review.',
    'limits': ['Numerical rejection only; no new full-body/face grade or accepted moving character.',
        'Source attributes and source34 retained; no model was promoted or published.',
        'Existing C19 physical posing/lean, contact sockets and preferred head/hood remain protected.']}
(OUT/'parent-transition-review155.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
