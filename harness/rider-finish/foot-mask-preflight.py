"""Prepare exact body05 foot-envelope and provisional sole IDs from frozen arrays."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
for key in ('fields', 'intake', 'full-source', 'foundation', 'out', 'manifest'):
    parser.add_argument('--' + key, required=True)
parser.add_argument('--semantic-threshold', type=float, default=.95)
parser.add_argument('--sole-height-m', type=float, default=.04)
args = parser.parse_args()
fields_path, directory, full_path, foundation_path, out, manifest = [Path(getattr(args, key.replace('-', '_'))).resolve() for key in ('fields', 'intake', 'full-source', 'foundation', 'out', 'manifest')]
assert not out.exists() and not manifest.exists()
assert args.semantic_threshold == .95 and args.sole_height_m == .04
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(fields_path) == '36277520249bcd2a8058a76c2f4a7595d7c460d3196e9bc59b3aa3a31690cb2d'
assert sha(full_path) == 'deb04faa6a5ca85ca9617cb963d84d5e62074aee281507c5a755fcbe8387d91c'
native_path = directory / 'report.json'
native = json.loads(native_path.read_text())
assert next(iter(native['sourcePins'].values())) == '58c59f6e8b3e1a3c792e628040a137714fcf62f9ff8989578e2429a038e59661'
rest_path = directory / native['rest']['path']
assert sha(rest_path) == native['rest']['sha256']
rest = json.loads(gzip.decompress(rest_path.read_bytes()))
fields, full, foundation = [np.load(path) for path in (fields_path, full_path, foundation_path)]
names = rest['jointOrder']
assert names == fields['boneNames'].tolist() == full['boneNames'].tolist() and len(names) == 51
xyz = np.array(rest['parts']['body']['xyz'])
triangles = np.array(rest['parts']['body']['faces'], np.int32)
world_matrix = np.array(rest['parts']['body']['objectWorld'])
world = (np.column_stack((xyz, np.ones(len(xyz)))) @ world_matrix.T)[:, :3]
assert np.array_equal(xyz.astype(np.float32), fields['bodyRestXYZ'])
assert np.array_equal(triangles, fields['bodyTriangles'])
refs = fields['bodyAttributeEdgeSources']
ancestry = fields['bodyCanonicalTriangleAncestry']
actual = {field: np.array(rest['parts']['body'][field + 'RawWeights']) for field in ('full', 'four')}
canonical = {'full': full['originalFullWeights'], 'four': foundation['canonicalWeights']}
for field in ('full', 'four'):
    actual[field] = actual[field] / actual[field].sum(axis=1)[:, None]
    canonical[field] = canonical[field] / canonical[field].sum(axis=1)[:, None]
canonical_triangles = foundation['canonicalTriangles']
points = world[triangles]
cross = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
area2 = np.linalg.norm(cross, axis=1)
normal = cross / area2[:, None]

def boundary(ids):
    edges = {}
    for triangle in triangles[ids]:
        for index in range(3):
            edge = tuple(sorted((int(triangle[index]), int(triangle[(index + 1) % 3]))))
            edges[edge] = edges.get(edge, 0) + 1
    return np.array([edge for edge, count in edges.items() if count == 1], np.int32).reshape(-1, 2), sum(count > 2 for count in edges.values())

def components(ids):
    remaining = set(map(int, ids)); by_vertex = {}
    for tid in ids:
        for vertex in triangles[tid]:
            by_vertex.setdefault(int(vertex), set()).add(int(tid))
    sizes = []
    while remaining:
        stack = [remaining.pop()]; count = 0
        while stack:
            tid = stack.pop(); count += 1
            for vertex in triangles[tid]:
                adjacent = by_vertex[int(vertex)] & remaining
                remaining -= adjacent; stack.extend(adjacent)
        sizes.append(count)
    return sorted(sizes, reverse=True)

arrays = {'boneNames': np.array(names), 'bodyTriangles': triangles, 'bodyPointCanonicalEdgeAncestry': refs,
          'bodyCanonicalTriangleAncestry': ancestry, 'bodyRestLocalXYZ': xyz.astype(np.float32),
          'bodyRestWorldXYZ': world, 'bodyObjectWorldRows': world_matrix}
records = {}
for side in ('L', 'R'):
    columns = [names.index('foot.' + side), names.index('ball.' + side)]
    mass = {field: actual[field][:, columns].sum(axis=1) for field in ('full', 'four')}
    canonical_mass = {field: canonical[field][:, columns].sum(axis=1) for field in ('full', 'four')}
    eligible = (mass['full'] > args.semantic_threshold) | (mass['four'] > args.semantic_threshold)
    canonical_eligible = (canonical_mass['full'] > args.semantic_threshold) | (canonical_mass['four'] > args.semantic_threshold)
    core = np.flatnonzero(np.all(eligible[triangles], axis=1))
    envelope = np.flatnonzero(np.any(eligible[triangles], axis=1))
    fringe = np.setdiff1d(envelope, core)
    vertices = np.unique(triangles[envelope])
    floor_min = float(world[np.flatnonzero(eligible), 2].min())
    underside = envelope[(normal[envelope, 2] < 0) & (points[envelope, :, 2].max(axis=1) <= floor_min + args.sole_height_m)]
    nonsole = np.setdiff1d(envelope, underside)
    canonical_envelope = np.flatnonzero(np.any(canonical_eligible[canonical_triangles], axis=1))
    actual_canonical = ancestry[envelope]
    assert np.all(actual_canonical >= 0)
    assert np.array_equal(np.sort(actual_canonical), canonical_envelope)
    assert np.all(refs[vertices, 0] == refs[vertices, 1]) and np.all(refs[vertices, 2] == 0)
    canonical_vertices = refs[vertices, 0].astype(np.int32)
    assert np.array_equal(xyz[vertices].astype(np.float32), full['originalFullXYZ'][canonical_vertices].astype(np.float32))
    bound, nonmanifold = boundary(envelope)
    sole_bound, sole_nonmanifold = boundary(underside)
    arrays.update({side + 'EligibleSemanticNativeVertexIDs': np.flatnonzero(eligible).astype(np.int32),
                   side + 'FootCoreTriangleIDs': core.astype(np.int32), side + 'FootEnvelopeTriangleIDs': envelope.astype(np.int32),
                   side + 'FootFringeTriangleIDs': fringe.astype(np.int32), side + 'FootEnvelopeNativeVertexIDs': vertices.astype(np.int32),
                   side + 'FootEnvelopeCanonicalVertexIDs': canonical_vertices, side + 'FootEnvelopeCanonicalTriangleIDs': actual_canonical.astype(np.int32),
                   side + 'ProvisionalUndersideTriangleIDs': underside.astype(np.int32), side + 'NonsolePenetrationEligibleTriangleIDs': nonsole.astype(np.int32),
                   side + 'FootEnvelopeBoundaryEdges': bound, side + 'ProvisionalUndersideBoundaryEdges': sole_bound})
    records[side] = {'semanticVertices': int(eligible.sum()), 'footCoreTriangles': len(core), 'footFringeTriangles': len(fringe),
                     'completeFootEnvelopeTriangles': len(envelope), 'completeFootEnvelopeVertices': len(vertices),
                     'provisionalUndersideTriangles': len(underside), 'nonsolePenetrationEligibleTriangles': len(nonsole),
                     'everyCanonicalFootEnvelopeTriangleOccursExactlyOnce': True, 'footPointCanonicalIdentityAncestryExact': True,
                     'canonicalRestXYZExact': True, 'footEnvelopeComponents': components(envelope), 'soleComponents': components(underside),
                     'footEnvelopeBoundaryEdges': len(bound), 'footEnvelopeNonmanifoldEdges': nonmanifold,
                     'soleBoundaryEdges': len(sole_bound), 'soleNonmanifoldEdges': sole_nonmanifold,
                     'eligibleNativeMinimumZWorldM': floor_min, 'worldBoundsM': [world[vertices].min(axis=0).tolist(), world[vertices].max(axis=0).tolist()],
                     'fullEnvelopeRestAreaM2': float(area2[envelope].sum() / 2),
                     'provisionalUndersideRestAreaM2': float(area2[underside].sum() / 2),
                     'provisionalUndersideProjectedRestAreaM2': float(np.abs(cross[underside, 2]).sum() / 2),
                     'restNearFloor5mmEnvelopeTriangles': int(np.count_nonzero(points[envelope, :, 2].min(axis=1) <= .005)),
                     'minimumTriangleArea2M2': float(area2[envelope].min()), 'FOURFULLSemanticEligibleDifferentVertexIDs': np.flatnonzero((mass['full'] > .95) != (mass['four'] > .95)).tolist()}
manifest.parent.mkdir(parents=True, exist_ok=True)
np.savez_compressed(manifest, **arrays)
report = {'status': 'UNACCEPTED_BODY05_FULLFOOT_AND_PROVISIONAL_SOLE_MASK_PREFLIGHT_ONLY',
          'inputPins': {str(path): sha(path) for path in (fields_path, full_path, foundation_path, native_path, rest_path)},
          'nativeSourcePins': native['sourcePins'], 'recipeSHA256': sha(__file__), 'numpy': np.__version__,
          'manifest': str(manifest), 'manifestSHA256': sha(manifest), 'manifestBytes': manifest.stat().st_size,
          'frameCalibration': {'units': 'metres', 'nativeAxes': '+Xforward/+Zup/-Yleft', 'floorWorldZ': 0,
                               'bodyObjectWorldRows': world_matrix.tolist(), 'rigWorldRows': rest['rigWorldRows'],
                               'worldOffsetPolicy': 'Original+.65X source placement retained; no wrapper offset or ankle recentering is applied to foot/floor metrics.'},
          'maskContract': {'semanticMassThresholdExclusive': .95, 'semanticBones': ['foot.L', 'ball.L', 'foot.R', 'ball.R'],
                           'wholeFootEligibility': 'Union FULL/FOUR semantic vertices; ALL triangles incident to ANY eligible vertex, including ankle fringe and dorsal/nonsole faces.',
                           'provisionalUnderside': 'Envelope triangle with rest true geometric normalWorld.Z<0 and every vertex no more than40mm above that foot semantic minimumZ.',
                           'penetrationEligibility': 'Every complete foot-envelope triangle remains eligible regardless underside membership.',
                           'soleHeightExtentM': .04}, 'feet': records,
          'plannedPatchMethod': {'surface': 'Evaluate these exact triangles on the SAME candidate and exact saved own51 poses; retain per-triangle source IDs.',
                                 'floorPatch': 'Clip actual triangle polygons to the signed floor slab[-1mm,+5mm], then project to worldXY and measure polygon area plus finite patch union/hull. Hull area is a bound and cannot fill gaps for a contact claim.',
                                 'penetration': 'On ALL envelope triangles, clip the portion belowZ=-1mm; report signed minimum, affected triangle IDs, true affected surface area and projected area. No provisional underside exclusion.',
                                 'support': 'Report declared support/flight phases and full patch slip through forward/reverse clocks; a floor gap or hull alone does not certify load balance.'},
          'COM': {'status': 'UNMEASURED_UNDEFINED_MASS_MODEL', 'reason': 'No declared segment masses/densities or watertight whole-body model has been qualified. Pelvis is not COM; bare-body geometry centroid is not physiological balance.'},
          'limits': ['Source-array preflight only; no Blender/native job, new pose generation,688batch, save/export, movie or GPU work.',
                     'All canonical semantic-envelope surfaces are included exactly, but semantic threshold/fringe and40mm underside coverage remain provisional anatomical masks requiring parent/source-author review.',
                     'Mask connectivity/ancestry and rest geometry do not qualify footwear, grounded support, motion contact, art or device performance.',
                     'No existing grounded04 sole metrics transfer to this mask or to a future candidate.']}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
print(json.dumps(records, indent=2))
