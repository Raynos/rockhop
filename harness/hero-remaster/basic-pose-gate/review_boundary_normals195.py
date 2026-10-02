"""Field-specific source-normal diagnosis, separate from UV chart names."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/extrinsic-seam195'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB

source = B / 'source-preserving-garment185/operator/rider.glb'
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
g = GLB(source)
p = g.j['meshes'][0]['primitives'][0]
P, N = [g.array(p['attributes'][k]) for k in ['POSITION', 'NORMAL']]
F = g.array(p['indices']).reshape(-1, 3).astype(np.int64)
U, q = np.unique(P, axis=0, return_inverse=True)
z = np.load(B / 'source-ruled194/construction.npz')
assert hashlib.sha256((B / 'source-ruled194/construction.npz').read_bytes()).hexdigest() == 'ee45bb5e0e9612c9b8a3e7ac433fc02824f5ebff319f8da0217692164dd69777'
prov = json.loads((B / 'source-ruled194/construction-provenance.json').read_text())
bad_ids = sorted({x['physicalID'] for x in prov['constructionFailures'] if x['type'] == 'missing_retained_boundary_chart_normal'})
assert bad_ids == [3486, 5437, 8638, 9294, 10649, 11167]
kept = set(z['sourceKeptFaceIDs'].tolist())
records = []
for v in bad_ids:
    rows = np.flatnonzero(q == v)
    retained_rows = sorted({int(row) for fi in np.flatnonzero((q[F] == v).any(axis=1)) if int(fi) in kept for row in F[fi] if q[row] == v})
    failed_corners = [c for c in prov['newCornerProvenance'] if c['physicalID'] == v and c['normalSource'] is None]
    assert retained_rows and failed_corners
    unique_normals = np.unique(N[rows], axis=0)
    matches = [any(np.array_equal(z['attribute_NORMAL'][c['newAccessorRow']], N[r]) for r in retained_rows) for c in failed_corners]
    records.append({'physicalID': v, 'sourceAliases': rows.tolist(), 'retainedNormalDonorRows': retained_rows, 'uniqueSourceNormals': unique_normals.tolist(), 'fallbackCornerRows': [c['newAccessorRow'] for c in failed_corners], 'everyFallbackMatchesAnActualRetainedNormalExactly': all(matches), 'uvChartMissingDoesNotEstablishNumericNormalMismatch': all(matches)})
assert sum(len(x['fallbackCornerRows']) for x in records) == 18
report = {'status': 'SOURCE_BOUNDARY_NORMAL_FIELD_DIAGNOSIS_ONLY', 'sourceSHA256': hashlib.sha256(source.read_bytes()).hexdigest(), 'dumpSHA256': hashlib.sha256((B / 'source-ruled194/construction.npz').read_bytes()).hexdigest(), 'records': records, 'allFallbackNormalsNumericallyRetainedExact': all(x['everyFallbackMatchesAnActualRetainedNormalExactly'] for x in records), 'provenanceLabelCorrection': 'Frozen194 normalRule says retained_matched_chart even for missing donors. Select the18 failures by normalSource:null and named construction failure records. Original dump/report remain intact; parent corrected its initial filter before generating this report.', 'limits': 'Does not reverse194 rejection:127 geometric crossings remain. No source or candidate changed, no render/rig/motion/art pass. Next normal policy must identify normal field/crease continuity separately from UV islands; keep frozen194chart-provenance failure intact.'}
E.mkdir(parents=True, exist_ok=True)
assert not (E / 'parent-normal-diagnosis.json').exists()
(E / 'parent-normal-diagnosis.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'records'}))
