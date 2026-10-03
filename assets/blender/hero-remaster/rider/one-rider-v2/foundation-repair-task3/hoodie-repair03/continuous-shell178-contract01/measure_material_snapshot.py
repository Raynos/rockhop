"""Literal whole-cloth triangle and area/edge diagnostic of a supplied pose.
No normal-only pass, pose fitting, garment thickness or contact certificate.
"""
from pathlib import Path
import json, hashlib, sys
import numpy as np
sys.dont_write_bytecode = True

R = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
source, pose, output = map(Path, sys.argv[1:4])
assert not output.exists()
z, q = dict(np.load(source)), dict(np.load(pose))
# Only import the independently written generic whole-cloth predicate/audit.
code = (R/'hoodie-repair02/qa-lane/scripts/tube06_rest_qualify.py').read_text()
ns = {}
exec(compile(code[:code.index('\nsource_weld =')], 'independent-literal-audit', 'exec'), ns)
positions = [q[f'p{i}'] for i in range(5)]
tris = [z[f'tr{i}'] for i in range(5)]
weld = [z[f'physicalWeld{i}'] for i in range(5)]
ancestry = [z[f'sourceFaceAncestry{i}'] for i in range(5)]
kind = [z[f'faceKind{i}'] for i in range(5)]
audit, _ = ns['audit']('material snapshot', positions, tris, weld, ancestry, kind)
metrics = []
affected_faces = set()
affected_aliases = np.array([], dtype=int)
for side in ['L', 'R']:
    affected_faces.update(map(int, z.get('embedAffectedSourceFaces'+side, [])))
    affected_aliases = np.r_[affected_aliases, z.get('embedSourceAliases'+side, [])].astype(int)
for i in [0, 2]:
    tr = tris[i]
    rest, posed = z[f'p{i}'][tr], positions[i][tr]
    rest_area = np.linalg.norm(np.cross(rest[:, 1]-rest[:, 0], rest[:, 2]-rest[:, 0]), axis=1)
    posed_area = np.linalg.norm(np.cross(posed[:, 1]-posed[:, 0], posed[:, 2]-posed[:, 0]), axis=1)
    fraction = posed_area / np.maximum(rest_area, 1e-30)
    new = np.array([str(k).startswith(('body-cap', 'new-tube')) for k in kind[i]])
    affected = np.isin(z[f'physicalWeld{i}'][tr], affected_aliases).any(1) if len(affected_aliases) else new
    edges = np.unique(np.sort(np.r_[tr[:, [0, 1]], tr[:, [1, 2]], tr[:, [2, 0]]], axis=1), axis=0)
    rest_len = np.linalg.norm(z[f'p{i}'][edges[:, 0]]-z[f'p{i}'][edges[:, 1]], axis=1)
    posed_len = np.linalg.norm(positions[i][edges[:, 0]]-positions[i][edges[:, 1]], axis=1)
    stretch = posed_len / np.maximum(rest_len, 1e-30)
    use = rest_len >= .005
    metrics.append({'primitive': i, 'faces': len(tr), 'newCapTubeFaces': int(new.sum()),
                    'quarterAreaCollapsedAll': int((fraction < .25).sum()),
                    'quarterAreaCollapsedNewCapTube': int(((fraction < .25) & new).sum()),
                    'declaredAffectedFaces': int(affected.sum()),
                    'quarterAreaCollapsedAffected': int(((fraction < .25) & affected).sum()),
                    'areaRatioP01': float(np.percentile(fraction, 1)),
                    'meaningfulEdgeMinimumRestLengthM': .005,
                    'meaningfulEdgeStretchMaximum': float(stretch[use].max()),
                    'meaningfulEdgeStretchP99': float(np.percentile(stretch[use], 99))})
pairs = audit['all_crossing_witnesses']
new_pairs = [p for p in pairs if any(f['kind'].startswith(('body-cap', 'new-tube')) for f in p['faces'])]
affected_sets = {i: set(np.flatnonzero(np.isin(z[f'physicalWeld{i}'][tris[i]], affected_aliases).any(1))) for i in [0, 2]} if len(affected_aliases) else {}
affected_pairs = [p for p in pairs if any(f['face'] in affected_sets.get(f['primitive'], set()) for f in p['faces'])] if affected_sets else new_pairs
sections = []
for side in ['L', 'R']:
    if 'tubeRows'+side not in z:
        continue
    rows = z['tubeRows'+side]
    rest_ring, posed_ring = z['p0'][rows], positions[0][rows]
    def polygon_area_vector(ring):
        local = ring-ring.mean(axis=1, keepdims=True)
        return .5*np.cross(local, np.roll(local, -1, axis=1)).sum(axis=1)
    a = np.linalg.norm(polygon_area_vector(rest_ring), axis=1)
    b = np.linalg.norm(polygon_area_vector(posed_ring), axis=1)
    ratio = b/np.maximum(a, 1e-30)
    sections.append({'side': side, 'materialSections': len(rows),
                     'polygonAreaRatioMinimum': float(ratio.min()),
                     'polygonAreaRatioMedian': float(np.median(ratio)),
                     'perSectionRatios': ratio.tolist(),
                     'limits': 'Area-vector polygon diagnostic only; nonplanar sections, closed body volume, cloth thickness and pressure are not certified.'})
report = {'status': 'Literal offline diagnostic; no acceptance inferred',
          'sourceSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'poseSHA256': hashlib.sha256(pose.read_bytes()).hexdigest(),
          'wholeClothTriangleAudit': audit, 'areaAndEdgeMetrics': metrics,
          'newCapTubeInvolvedCrossingPairs': len(new_pairs),
          'declaredAffectedRegionInvolvedCrossingPairs': len(affected_pairs),
          'affectedScope': 'Faces incident to any declared original source embedding alias across primitive0 AND primitive2; cap/tube face kinds for non-embedding candidates.',
          'tubeMaterialSectionDiagnostics': sections,
          'limits': 'Strict transverse triangle crossings only; coplanar/tangent contact and garment thickness unclassified. Finite supplied pose only. No saddle/support/volume/continuous/runtime certificate.'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'wholeClothTriangleAudit'}, indent=2))
