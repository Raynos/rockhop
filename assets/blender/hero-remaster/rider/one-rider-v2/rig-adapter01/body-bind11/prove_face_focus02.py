"""Verify the camera-only change against the preserved actual replay."""
from pathlib import Path
import json
import shutil
import numpy as np

base = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind11')
out = base / 'face-focus02'
old = json.loads((base / 'played01/textured/report.json').read_text())
reports = {s: json.loads((out / s / 'report.json').read_text()) for s in ['textured', 'gray']}
assert all(not r.get('failure') and r['errors'] == [] and len(r['samples']) == 72 for r in reports.values())
for surface, report in reports.items():
    for previous, current in zip(old['samples'], report['samples']):
        assert all(previous[key] == current[key] for key in ['state', 'debug', 'hash', 'positions', 'privateClothRim'])
        assert all(previous['effectiveCamera'][key] == current['effectiveCamera'][key]
                   for key in ['position', 'quaternion', 'fov', 'zoom', 'distance'])
    shutil.copy2(out / surface / 'frames/0018.png', out / f'actual-front-{surface}.png')
# Each isolated Vite preview has its own ephemeral port. Compare consumed
# content and logical filename, not transport origin or response order.
def consumed(report):
    return sorted((row['url'].rsplit('/', 1)[-1], row['sha256'], row['status'])
                  for row in report['loaded'])


assert consumed(reports['textured']) == consumed(reports['gray'])
for a, b in zip(reports['textured']['samples'], reports['gray']['samples']):
    assert all(a[key] == b[key] for key in ['state', 'debug', 'effectiveCamera', 'surfaceFocus'])
samples = reports['textured']['samples']
local = np.array([s['surfaceFocus']['headLocal'] for s in samples])
projected = np.array([s['surfaceFocus']['projectedAfter'] for s in samples])
drift = np.linalg.norm(local - local[0], axis=1)
assert drift.max() < 1e-5, 'Camera must not disguise a skinned face drifting away from the head bone'
assert np.linalg.norm(projected[:, :2], axis=1).max() < 1e-6
proof = {'sourceSHA256': 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754',
    'samples': len(samples), 'stateDebugHashBonesExactToPrior': 72,
    'cameraTransformFOVZoomDistanceExactToPrior': 72, 'pairedSurfaceCameraStateExact': 72,
    'skinnedFaceVertex': samples[0]['surfaceFocus'],
    'maximumHeadLocalDriftM': float(drift.max()),
    'maximumCenteredNDCError': float(np.linalg.norm(projected[:, :2], axis=1).max()),
    'limits': 'Only private camera view window changes. Fixed source face vertex is a framing anchor, not an anatomical eye landmark. Same partial orbit; not nine-angle appearance acceptance.'}
(out / 'camera-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, indent=2))
