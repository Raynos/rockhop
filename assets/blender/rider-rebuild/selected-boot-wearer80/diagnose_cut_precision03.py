"""Read-only numerical cut reproduction on the actual minimal crossing patch.

Blender -b -t 2 --python-exit-code 1 --python diagnose_cut_precision03.py -- FRESH_OUTPUT
This builds an in-memory BMesh fixture, not a shoe candidate or native scene.
It retains every original crossing edge's two source triangle owners. The
omitted non-crossing faces and original whole-mesh edge order mean this is a
local equivalent operation, not a replay of author03's complete BMesh state.
No source coordinate replacement, face deletion, collar/toe edit, or native save.
"""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import bmesh
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT/'harness/out/rider-rebuild/selected-boot-wearer80'
PLANE = .090
PINS = {
    'source': ('harness/out/rider-rebuild/selected-boot-family75/cpu01/source.json',
               '22236d6c2f4a874a57c7f945a4e1b186d6d400dab04c006f3658f96afc8e7ed1'),
    'selection': ('harness/out/rider-rebuild/selected-boot-wearer80/selection01/selection.json',
                  '8484fb23b19d3edcda3a1b3b995c735e219b2ecaf4431eeaaa2503bd02b309bc'),
    'constructor': ('assets/blender/rider-rebuild/selected-boot-wearer80/author03.py',
                    'fd4006aa7fb372a2e522acda5e9ccc5569294f0925e0dd0972a9a4e7a32c7eac'),
}


def checked(row):
    path = ROOT/row[0]
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row[1], row[0]
    return path


def ulps(a, b):
    def ordered(values):
        bits = np.asarray(values, '<f4').view('<u4')
        return np.where(bits & 0x80000000, ~bits, bits | 0x80000000).astype(np.int64)
    return np.abs(ordered(a)-ordered(b)).tolist()


def compare(raw, point):
    rounded = np.asarray(point, '<f4')
    error = np.abs(raw.astype(float)-rounded.astype(float))
    return {'point64': np.asarray(point, float).tolist(), 'point32': rounded.tolist(),
            'absoluteErrorM': error.tolist(), 'maximumErrorM': float(error.max()),
            'distanceM': float(np.linalg.norm(error)), 'coordinateULPDistance': ulps(raw, rounded)}


def side_fixture(side, positions, triangles, selection):
    prior = selection['sides'][side]
    selected = np.load(checked((prior['selectedIds']['path'], prior['selectedIds']['sha256'])))
    assert len(selected) == prior['selectedOriginalTriangles'] == {'L': 131148, 'R': 131070}[side]
    z = positions[triangles[selected], 2]
    crossing_ids = selected[(z.min(1) < PLANE) & (z.max(1) > PLANE)]
    assert len(prior['cutRings']) == 1
    assert set(crossing_ids) == set(prior['cutRings'][0]['sourceTriangleIds'])
    assert len(crossing_ids) == {'L': 883, 'R': 876}[side]
    owners, face_edges = {}, {}
    for source_face in crossing_ids:
        tri = triangles[source_face]
        edges = {tuple(sorted((int(tri[a]), int(tri[b])))) for a, b in ((0, 1), (1, 2), (2, 0))
                 if (float(positions[tri[a], 2])-PLANE)*(float(positions[tri[b], 2])-PLANE) < 0}
        assert len(edges) == 2
        face_edges[int(source_face)] = edges
        for edge in edges:
            owners.setdefault(edge, set()).add(int(source_face))
    assert len(owners) == len(crossing_ids) and all(len(v) == 2 for v in owners.values())
    bm = bmesh.new()
    vertex_id = bm.verts.layers.int.new('original_vertex_plus_one')
    face_id = bm.faces.layers.int.new('original_face_plus_one')
    source_vertices = np.unique(triangles[crossing_ids])
    vertices = {}
    for index in source_vertices:
        vertex = bm.verts.new(positions[index].tolist())
        vertex[vertex_id] = int(index)+1
        vertices[int(index)] = vertex
    for index in crossing_ids:
        face = bm.faces.new([vertices[int(i)] for i in triangles[index]])
        face[face_id] = int(index)+1
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    edge_orders = {}
    for edge in bm.edges:
        order = [v[vertex_id]-1 for v in edge.verts]
        key = tuple(sorted(order))
        if key in owners:
            assert {f[face_id]-1 for f in edge.link_faces} == owners[key]
            edge_orders[key] = order
    assert set(edge_orders) == set(owners)
    originals = set(bm.verts)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
        plane_co=(0., 0., PLANE), plane_no=(0., 0., 1.), dist=1e-8,
        clear_inner=False, clear_outer=False)
    rows, unmatched, found = [], [], set()
    for vertex in bm.verts:
        if vertex in originals:
            assert np.array_equal(np.asarray(vertex.co[:], '<f4'), positions[vertex[vertex_id]-1])
            continue
        raw = np.asarray(vertex.co[:], '<f4')
        actual_owners = {f[face_id]-1 for f in vertex.link_faces}
        candidates = set.intersection(*(face_edges[i] for i in actual_owners)) if actual_owners <= face_edges.keys() else set()
        if len(candidates) != 1:
            unmatched.append({'rawBMeshPoint': raw.tolist(), 'ownerIds': sorted(actual_owners),
                              'candidateEdges': sorted(candidates)})
            continue
        key, = candidates
        assert key not in found and actual_owners == owners[key]
        found.add(key)
        a, b = positions[list(key)].astype(float)
        t64 = float((PLANE-a[2])/(b[2]-a[2]))
        plane32 = float(np.float32(PLANE))
        t32plane = float((plane32-a[2])/(b[2]-a[2]))
        comparisons = {'doublePlane': compare(raw, a+t64*(b-a)),
                       'float32Plane': compare(raw, a+t32plane*(b-a))}
        # Expose both ordinary float32 interpolation expressions in the actual
        # fixture edge order. These are numerical references, not fitted values.
        aa, bb = positions[edge_orders[key]].astype('<f4')
        da, db = np.float32(aa[2]-np.float32(PLANE)), np.float32(bb[2]-np.float32(PLANE))
        tf = np.float32(da/np.float32(da-db))
        comparisons['float32DifferenceLerp'] = compare(raw, np.asarray(aa+tf*(bb-aa), '<f4'))
        comparisons['float32WeightedLerp'] = compare(raw, np.asarray(np.float32(1-tf)*aa+tf*bb, '<f4'))
        delta = b-a
        actual_t = float(np.dot(raw.astype(float)-a, delta)/np.dot(delta, delta))
        rows.append({'sourceEdge': list(key), 'sourceEndpoints': [a.tolist(), b.tolist()],
            'sourceOwnerTriangleIds': sorted(actual_owners), 'fixtureBMeshEdgeOrder': edge_orders[key],
            'rawBMeshPoint': raw.tolist(), 'rawBMeshPointFloat32Bits': raw.view('<u4').tolist(),
            'doublePlaneT': t64, 'float32PlaneT': t32plane, 'fixtureFloat32ArithmeticT': float(tf),
            'projectedRawT': actual_t, 'rawDistanceToOriginalEdgeM': float(np.linalg.norm(raw.astype(float)-(a+actual_t*delta))),
            'comparisons': comparisons,
            'failsAuthor03DoublePlanePredicate': comparisons['doublePlane']['maximumErrorM'] >= 2e-7})
    bm.free()
    rows.sort(key=lambda r: r['sourceEdge'])
    return rows, {'sourceCrossingTriangles': len(crossing_ids), 'sourceVerticesInFixture': len(source_vertices),
        'expectedCutEdges': len(owners), 'recordedCutEdges': len(rows), 'unmatchedCutVertices': unmatched,
        'missingSourceEdges': sorted(set(owners)-found),
        'doublePlanePredicateFailures': [r['sourceEdge'] for r in rows if r['failsAuthor03DoublePlanePredicate']],
        'maximumErrorsM': {name: max(r['comparisons'][name]['maximumErrorM'] for r in rows)
                          for name in rows[0]['comparisons']},
        'maximumCoordinateULPDistance': {name: max(max(r['comparisons'][name]['coordinateULPDistance']) for r in rows)
                                         for name in rows[0]['comparisons']}}


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(BASE) and out != BASE and not out.exists()
    files = {key: checked(pin) for key, pin in PINS.items()}
    source, selection = [json.loads(files[k].read_text()) for k in ('source', 'selection')]
    assert selection['pins']['source'] == list(PINS['source'])
    package = source['arrays']
    raw = checked((package['path'], package['sha256'])).read_bytes()
    arrays = {key: np.frombuffer(raw, dtype=row['dtype'],
              count=row['byteLength']//np.dtype(row['dtype']).itemsize,
              offset=row['byteOffset']).reshape(row['shape']) for key, row in package['layout'].items()}
    out.mkdir(parents=True)
    report = {'status': 'READ_ONLY_CROSSING_PATCH_NUMERIC_DIAGNOSTIC', 'acceptedArt': False,
        'pins': PINS, 'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'pythonVersion': sys.version, 'blenderVersion': bpy.app.version_string,
        'plane64M': PLANE, 'plane32M': float(np.float32(PLANE)), 'bisectDistanceM': 1e-8, 'sides': {},
        'limits': 'Actual source crossing patch and exact original crossing-edge owners; in-memory BMesh only. Local numerical reproduction, not identical whole-mesh edge ordering/state from author03. No replacement, deletion, candidate/native save, fit, art or acceptance.'}
    for side in ('L', 'R'):
        rows, summary = side_fixture(side, arrays[side+'Positions'], arrays[side+'Triangles'], selection)
        path = out/(side+'-cut-edges.json')
        path.write_text(json.dumps(rows, indent=2, allow_nan=False)+'\n')
        summary['edgeEvidence'] = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        report['sides'][side] = summary
        (out/'cut-precision.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': report['status'], 'output': str(out)}))


if __name__ == '__main__':
    main()
