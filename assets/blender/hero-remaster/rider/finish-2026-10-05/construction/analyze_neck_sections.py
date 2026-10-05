"""Read-only localization of the body04d section failure; no candidate edits."""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import numpy as np

owned = Path(__file__).resolve().parent
root = owned.parents[5]
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body04d'
fields_path = owned / 'body04d/authored-neck-fields.npz'
f0_path = evidence.parent / 'foundation-source.npz'
witness_path = evidence.parent.parent / 'runtime/body04d-contact-witnesses.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
n, f = np.load(fields_path), np.load(f0_path)
witness = json.loads(witness_path.read_text())
count = len(n['commonU'])
start = len(n['headRestXYZ']) - 8 * count
rings = []
for ring in range(8):
    p = n['headRestXYZ'][start + ring * count:start + (ring + 1) * count]
    theta = np.unwrap(np.arctan2(p[:, 1], p[:, 0] - .035))
    delta = np.diff(np.r_[theta, theta[0] + 2 * np.pi])
    rings.append({'ring': ring, 'angularBacktrackingEdges': int(np.count_nonzero(delta < 0)),
                  'minimumAngularIncrementRadians': float(delta.min()), 'minimumZ': float(p[:, 2].min()), 'maximumZ': float(p[:, 2].max())})
slivers = []
for pair in witness['records'][0]['fields']['four']['body/body']['classifiedWitnesses']:
    for side in pair['sides']:
        ids = side['nativeDerivativeVertexIDs']
        if any(x['nativeIDs'] == ids for x in slivers):
            continue
        p = n['bodyRestXYZ'][ids].astype(float)
        refs = n['bodyAttributeEdgeSources'][ids]
        errors = []
        for point, (a, b, t) in zip(p, refs):
            q = (1 - t) * f['displayBodyXYZ'][int(a)].astype(float) + t * f['displayBodyXYZ'][int(b)].astype(float)
            errors.append(float(np.linalg.norm(point - q)))
        slivers.append({'nativeIDs': ids, 'actualTriangleID': side['triangle'], 'sourcePolygonID': side['sourcePolygonID'],
                        'twiceTriangleAreaM2': float(np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))),
                        'sourceEdges': refs[:, :2].astype(int).tolist(), 'maximumFloat32EdgeInterpolationErrorM': max(errors),
                        'actualTrianglesMatchAuthoredCachedTriangleRow': bool(np.array_equal(n['bodyTriangles'][side['triangle']], ids))})
# One nominated flat canonical cut. This is a source topology measurement,
# not a newly authored model or an anatomy acceptance result.
p, tri, cut = f['canonicalXYZ'], f['canonicalTriangles'], np.float32(1.55)
adj, points = defaultdict(set), {}
for face in tri[np.any(p[tri, 2] < cut, axis=1) & np.any(p[tri, 2] >= cut, axis=1)]:
    edges = []
    for a, b in zip(face, np.roll(face, -1)):
        if (p[a, 2] < cut) != (p[b, 2] < cut):
            key = tuple(sorted((int(a), int(b))))
            t = (float(cut) - p[a, 2]) / (p[b, 2] - p[a, 2])
            points[key] = p[a].astype(float) + t * (p[b].astype(float) - p[a].astype(float))
            edges.append(key)
    assert len(edges) == 2
    adj[edges[0]].add(edges[1]); adj[edges[1]].add(edges[0])
assert len(adj) == 104 and all(len(x) == 2 for x in adj.values())
first = next(iter(adj)); previous = None; current = first; seen = set(); ring = []
while current not in seen:
    seen.add(current); ring.append(points[current]); nxt = sorted(adj[current] - ({previous} if previous else set()))[0]; previous, current = current, nxt
assert current == first and len(seen) == len(adj)
ring = np.array(ring)
area = np.sum(ring[:, 0] * np.roll(ring[:, 1], -1) - ring[:, 1] * np.roll(ring[:, 0], -1))
if area < 0:
    ring = ring[::-1]
theta = np.unwrap(np.arctan2(ring[:, 1], ring[:, 0] - .035))
delta = np.diff(np.r_[theta, theta[0] + 2 * np.pi])
report = {'status': 'READ_ONLY_FAILED_SECTION_DIAGNOSIS_AND_PROPOSED_ALTERNATIVE', 'inputs': {str(x.relative_to(root)): sha(x) for x in [fields_path, f0_path, witness_path]},
          'recipeSHA256': sha(__file__), 'actualBodySliverWitnesses': slivers, 'actualLoftRings': rings,
          'diagnosis': 'Sampled head-self witnesses are new outer loft rings 4-6, not the inner cap. The body shoulder boundary is correctly cyclic but intrinsically non-star-shaped. Varying-height ray sections blended toward its concavity fold near the base. Source-edge n-gon retessellation also produces nearly collinear Float32 slivers; original body vertices remain unchanged.',
          'flatCanonicalCut': {'z': float(cut), 'singleClosedLoopVertices': len(ring), 'degreeCounts': dict(Counter(len(x) for x in adj.values())), 'angularBacktrackingEdges': int(np.count_nonzero(delta < 0)), 'minimumAngularIncrementRadians': float(delta.min()), 'bounds': [ring.min(axis=0).tolist(), ring.max(axis=0).tolist()]},
          'nextMechanism': 'Restore missing original canonical neck triangles to a single Z=1.55 body cut. Preserve actual source triangle diagonals and explicit edge-split fans. Connect the source head Z=1.575 cut to that planar neck cut using monotone polar-angle sections, not arclength mapping to a concave nonplanar shoulder seam. Keep the inner head closure at the upper cut. Body stays at or below 1.55 and head at or above 1.55 in rest, giving a declared half-space check before skin motion.',
          'requiredPreflight': ['One simple monotone-angle loop per section, consistent winding and explicit finite triangle areas.', 'Body/head rest half-space separation, proper head-self/body-self zero, actual save/reopen triangle parity.', 'Protected original upper incident polygons/corner frames retained exactly; original 34 objects and 51 controls preserved.', 'FULL source field retained outside the admitted neck; authored at-most-four new seam field, actual native/manual stress and grounded motion validation.'],
          'limits': ['Witness diagnosis covers capped classified pairs, not a whole-contact histogram.', 'A planar source loop is not a constructed candidate or a rest/motion/art pass.', 'Polar-angle containment and future triangulation need actual full-surface checks; no numerical threshold is relaxed.', 'No body05 source edit or experiment has run.']}
(evidence / 'section-failure-analysis.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'slivers': slivers, 'flatCanonicalCut': report['flatCanonicalCut']}, indent=2))
