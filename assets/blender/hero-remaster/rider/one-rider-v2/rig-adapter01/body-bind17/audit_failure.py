"""Read-only independent ray/source-frame audit of the frozen failed graft."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import numpy as np

ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
EVIDENCE = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind17/construction01')
failure = json.loads((EVIDENCE / 'clearance-registration-failure.json').read_text())
frozen = np.load(ROOT / 'body-bind17/construction01/clearance-registration-failure.npz')
probe = np.array(failure['worstProbe']['probePositionM'])
xyz = frozen['actualCorneaPositions'][frozen['actualCorneaTriangles']]
yz = xyz[:, :, 1:]
a, b = yz[:, 1] - yz[:, 0], yz[:, 2] - yz[:, 0]
d = probe[1:] - yz[:, 0]
det = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
ids = np.flatnonzero(abs(det) > 1e-15)
u = (d[ids, 0] * b[ids, 1] - d[ids, 1] * b[ids, 0]) / det[ids]
w = (a[ids, 0] * d[ids, 1] - a[ids, 1] * d[ids, 0]) / det[ids]
bary = np.c_[1 - u - w, u, w]
valid = (bary >= -1e-8).all(axis=1)
ids, bary = ids[valid], bary[valid]
hits = np.sum(bary * xyz[ids, :, 0], axis=1)
order = np.argsort(hits)
ray = [{'triangle': int(ids[i]), 'barycentric': bary[i].tolist(), 'xM': float(hits[i])} for i in order]
assert len(ray) >= 1
assert abs(hits.max() - failure['worstProbe']['actualCorneaFrontXM']) < 1e-12
triangle = frozen['positions'][failure['worstProbe']['globalVertexIDs']]
assert np.array_equal(triangle.astype(float), np.array(failure['worstProbe']['trianglePositionsM']))
assert np.allclose(np.array(failure['worstProbe']['barycentricProbe']) @ triangle, probe, atol=0, rtol=0)
assert np.isfinite(frozen['positions']).all()

native = np.load(ROOT / 'anatomical-eye-donor01/standalone01/fitted-native-L-lids.npz')
quads = native['quads']
edges = Counter(tuple(sorted((int(a), int(b)))) for f in quads for a, b in zip(f, np.roll(f, -1)))
adj = defaultdict(list)
for (a, b), count in edges.items():
    if count == 1:
        adj[a].append(b)
        adj[b].append(a)
remaining = set(adj)
loops = []
while remaining:
    first = min(remaining)
    loop, previous, current = [first], None, first
    while True:
        nxt = next(i for i in adj[current] if i != previous)
        if nxt == first:
            break
        assert nxt not in loop
        loop.append(nxt)
        previous, current = current, nxt
    remaining -= set(loop)
    loops.append(loop)
loops.sort(key=lambda q: np.ptp(native['positions'][q, 1]) * np.ptp(native['positions'][q, 2]))
aperture = loops[0]
assert np.array_equal(frozen['nativeSourcePositions'], native['positions'])
assert np.array_equal(frozen['nativeRegisteredPositions'][aperture], native['positions'][aperture])

source_native = np.load(ROOT / 'anatomical-eye-donor01/native-source.npz')['positions']
helper = source_native[14598:14670]
design = np.c_[2 * helper, np.ones(len(helper))]
fit = np.linalg.lstsq(design, np.sum(helper * helper, axis=1), rcond=None)[0]
center = fit[:3]
radius = np.sqrt(fit[3] + center @ center)
scale = failure['nativeSourceScale']
source = ROOT / 'body-bind11/guarded-correction01/rider.glb'
sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert sha == failure['sourceSHA256']
exports = list((ROOT / 'body-bind17').rglob('*.glb'))
assert not exports
report = {
    'status': 'FROZEN FAILED CONSTRUCTION; independent CPU diagnostic only',
    'sourceSHA256': sha,
    'sourceUnchanged': True,
    'candidateGLBCount': len(exports),
    'GPUWorkPerformed': False,
    'diagnosticNPZSHA256': hashlib.sha256((ROOT / 'body-bind17/construction01/clearance-registration-failure.npz').read_bytes()).hexdigest(),
    'worstProbeCategory': failure['worstProbe']['category'],
    'worstProbePositionM': probe.tolist(),
    'actualCorneaRayIntersections': ray,
    'corneaRayHitCount': len(ray),
    'closedSphereInteriorEstablished': False,
    'frontRayPenetrationM': float(hits.max() - probe[0]),
    'requiredShiftM': failure['requiredEyeDepthShiftM'],
    'unchangedSafetyBoundM': failure['safetyBoundM'],
    'nativeAperturePositionMaximumDeltaM': 0.0,
    'nativeSourceFrame': {
        'CC0Source': '/Users/raynos/Library/Application Support/Blender/5.1/extensions/user_default/mpfb/data/3dobjs/base.obj',
        'helperVertexRangeHalfOpen': [14598, 14670],
        'helperSphereFittedCenterRaw': center.tolist(),
        'eyeJointRaw': failure['nativeBasisEyeJointRaw'],
        'helperSphereFittedRadiusRaw': float(radius),
        'helperSphereFittedRadiusM': float(radius * scale),
        'helperForwardExtentRelativeToJointM': float((helper[:, 2].max() - failure['nativeBasisEyeJointRaw'][2]) * scale),
        'actualEyeDonorForwardExtentRelativeToTargetCenterM': float(frozen['actualCorneaPositions'][:, 0].max() - failure['targetUnshiftedGlobeCenterM'][0]),
        'properRotation': 'native (X,Y,Z) -> rider (Z,Y,-X)',
    },
    'limits': [
        'The inward-wall vertex lies 9.178 mm behind the actual corneal front ray within its Y/Z projection. This verifies the conservative front-clearance rejection.',
        'Only one corneal ray hit exists at this probe. A closed globe interior or actual wall/globe triangle intersection is not proved by this guard.',
        'The all-graft-front-clearance rule may be too conservative for a deliberately inward wall; parent must distinguish a registration failure from a guard applicability failure before choosing another construction.',
        'Positive-Z local construction precedes the negative-Z failure; whole-graft export, conservation, texture, normals and motion checks were never reached.',
        'The source helper/actual donor forward-depth difference is a frame finding; it does not by itself explain or solve the inward-wall failure.',
        'No safety bound was relaxed. No appearance or game-ready claim is made.',
    ],
}
(EVIDENCE / 'failure-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
