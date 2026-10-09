"""One parent-guarded selected shoe edit, not a production or moving-art pass.

Blender -b -t 2 --python-exit-code 1 --python author04.py -- FRESH_OUTPUT
Pinned actual inner-component repair; author.py through author03.py stay frozen.
Keep the actual own-side selected exterior. Remove its obsolete hidden heel
floor, retain a thin collar return, and author only the measured left toe lip.
No optimizer, body mask, global registration, source overwrite or native70 pass.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT/'harness/out/rider-rebuild/selected-boot-wearer80'
REFERENCE = 'RiderBody__FullAnatomyReference'
PINS = {
    'source75': ('harness/out/rider-rebuild/selected-boot-family75/cpu01/source.json',
                 '22236d6c2f4a874a57c7f945a4e1b186d6d400dab04c006f3658f96afc8e7ed1'),
    'native70': ('harness/out/rider-rebuild/selected-boot-native70/native01/UNACCEPTED-selected-production-full.blend',
                 'ffac10be163895d2ecb76d6552c9e357b86122d522543b7117974884be0ea52c'),
    'native47': ('harness/out/rider-rebuild/selected-sleeve-component47/intake01/UNACCEPTED-selected-sleeve-intake47.blend',
                 'ff2ba521943db9b8586e75ed674fc8122d7612df5cf5d609ffb9ef48c9016bc7'),
    'reference05': ('harness/out/rider-rebuild/selected-seated-anatomical09/reference05/original-full-reference.npz',
                    '01f752d72e94dbab81cc7a193adbd2dd7bba26df919b48454d8937fa9665dcc5'),
    'body02': ('docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz',
               'e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2'),
    'native52': ('harness/out/rider-rebuild/selected-ankle-native52/native01/UNACCEPTED-ankle-field42-native52.blend',
                 '38955c39ce9faa660f879b15c2f8349c9d077bf77dd61b753c7b225524172630'),
    'ankleRows': ('assets/blender/rider-rebuild/selected-ankle-field42/field-rows.json',
                  'c2908e7ef95b4d1420167da996616f8bc998ae037c369bce3c3182d29988d0af'),
    'classification': ('harness/out/rider-rebuild/selected-boot-wearer80/classify01/classification.json',
                       '2eb416699bb85ed4f257de719705651e5ad45b89347f82b494ed7b4a243f34a8'),
    'gameplayMatrices': ('harness/out/rider-rebuild/selected-authoring-motion11/gameplay-converted02/measured-gameplay-native-world.json',
                         'f3e0444768655bf72500a9245745a559586a7717b3f6cb6b600b6e9d1d05c153'),
    'genericMatrices': ('harness/out/rider-rebuild/selected-authoring-motion11/native05/action-06-RiderRangeOfMotion/native-action-matrices.npz',
                        '8d045c8f1c69dada4675f61d4ab745ae1fe74f403946cc706fce33fcbcfc6f49'),
    'genericReceipt': ('harness/out/rider-rebuild/selected-authoring-motion11/native05/action-06-RiderRangeOfMotion/receipt.json',
                       'c79a3d24a129e0b6063075335cd4c82bd10e522938c4bbad04088dd4aae6e6bc'),
    'frozenAuthor80': ('assets/blender/rider-rebuild/selected-boot-wearer80/author.py',
                       '8ddea96db75b58180b05aa1a06ccc27f8c457e2abe3224a7cd962b58ab2b733c'),
    'frozenAuthor03': ('assets/blender/rider-rebuild/selected-boot-wearer80/author03.py',
                       'fd4006aa7fb372a2e522acda5e9ccc5569294f0925e0dd0972a9a4e7a32c7eac'),
    'cutPrecision01': ('harness/out/rider-rebuild/selected-boot-wearer80/cutprecision01/cut-precision.json',
                       '63e84b41047680d3bfad678da8de958ff69275fc606cb0a51c0e0e8909d8e9ee'),
    'selection': ('harness/out/rider-rebuild/selected-boot-wearer80/selection01/selection.json',
                  '8484fb23b19d3edcda3a1b3b995c735e219b2ecaf4431eeaaa2503bd02b309bc'),
    'floorOwnership': ('harness/out/rider-rebuild/selected-boot-wearer80/floor01/ownership.json',
                       '27509e6dcb72627e681b3a801187aad60e71a83a9b64a46cd10450067a56d334'),
    'witness31': ('assets/blender/rider-rebuild/selected-production-family31/witness.py',
                  '95c7813b503c7d5539b2d7082e14229d484060bacefae294d28160e2c30755d5'),
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def checked(row):
    p = ROOT/row[0]
    assert sha(p) == row[1], str(p)
    return p


def points(obj):
    p = np.empty((len(obj.data.vertices), 3), '<f4')
    obj.data.vertices.foreach_get('co', p.ravel())
    return p


def faces(obj):
    obj.data.calc_loop_triangles()
    f = np.empty((len(obj.data.loop_triangles), 3), '<i4')
    obj.data.loop_triangles.foreach_get('vertices', f.ravel())
    return f


def fields(obj):
    names = [g.name for g in obj.vertex_groups]
    w = np.zeros((len(obj.data.vertices), len(names)), '<f4')
    for v in obj.data.vertices:
        for g in v.groups:
            w[v.index, g.group] = g.weight
    return names, w


def witness(obj):
    names, weights = fields(obj)
    h = hashlib.sha256(points(obj).tobytes()+faces(obj).tobytes()+weights.tobytes())
    h.update(json.dumps(names).encode())
    for uv in obj.data.uv_layers:
        a = np.empty((len(uv.data), 2), '<f4')
        uv.data.foreach_get('uv', a.ravel())
        h.update(uv.name.encode()+a.tobytes())
    return h.hexdigest()


def rest(rig):
    return [(b.name, list(b.head_local), list(b.tail_local), [list(r) for r in b.matrix_local])
            for b in rig.data.bones]


def append(path, names):
    with bpy.data.libraries.load(str(path), link=False) as (available, loaded):
        assert all(n in available.objects for n in names)
        loaded.objects = names
    for obj in loaded.objects:
        if obj.name not in bpy.context.scene.objects:
            bpy.context.scene.collection.objects.link(obj)
    return loaded.objects


def rebind(obj, rig):
    assert obj.matrix_world.is_identity and obj.matrix_parent_inverse.is_identity
    donors = {m.object for m in obj.modifiers if m.type == 'ARMATURE'}
    if obj.parent is not None:
        donors.add(obj.parent)
    assert donors and all(d.type == 'ARMATURE' and rest(d) == rest(rig) for d in donors)
    obj.parent = rig
    for m in obj.modifiers:
        if m.type == 'ARMATURE':
            m.object = rig
    assert obj.matrix_world.is_identity and obj.matrix_parent_inverse.is_identity


def frame(body, side):
    names = body['jointNames'].tolist()
    ankle = body['jointHeads'][names.index('DEF-foot.'+side)].astype(float)
    toe = body['jointHeads'][names.index('DEF-toe.'+side)].astype(float)
    forward = toe-ankle
    forward[2] = 0
    forward /= np.linalg.norm(forward)
    medial = np.cross([0., 0., 1.], forward)
    if medial[0]*(1 if side == 'R' else -1) < 0:
        medial *= -1
    ankle[2] = 0
    return ankle, np.column_stack([forward, medial, [0., 0., 1.]])


def connected(seed, permitted):
    result, pending = set(), [seed]
    while pending:
        face = pending.pop()
        if face in result or not permitted(face):
            continue
        result.add(face)
        pending.extend(f for e in face.edges for f in e.link_faces if f not in result)
    return result


PLANE = .090


def mesh_array(items, attribute, width=1, dtype=np.int32):
    data = np.empty((len(items), width), dtype)
    items.foreach_get(attribute, data.ravel())
    return data[:, 0] if width == 1 else data


def selection_evidence(side, original, original_faces, origin, basis, selection, ownership):
    prior, floor = selection['sides'][side], ownership['sides'][side]
    selected = np.load(checked((prior['selectedIds']['path'], prior['selectedIds']['sha256'])))
    assert selected.dtype == np.dtype('<i4') and np.array_equal(selected, np.unique(selected))
    assert len(selected) == prior['selectedOriginalTriangles'] == {'L': 131148, 'R': 131070}[side]
    assert len(original_faces) == prior['sourceTriangleCount'] == 610934
    assert len(prior['cutRings']) == 1 and not prior['failedPredicates']['beyondForward110mm']['fails']
    assert ownership['selectionPin'] == list(PINS['selection'])
    assert ownership['bodyPin'] == list(PINS['body02'])
    assert ownership['sourcePins']['source'] == list(PINS['source75'])
    assert ownership['actual47Correspondence'] == {'vertices': 2638, 'positionsExact': True, 'namedFieldsExact': True}
    assert floor['sourceFaces'] == 858 and not floor['unsupportedOwnership'] and not floor['outsideActualFootProjection']
    assert floor['upNormalZRange'][0] > 0 and floor['outerBottomToFloorM'][0] > 0
    low_rows = json.loads(checked((floor['faceEvidence']['path'], floor['faceEvidence']['sha256'])).read_text())
    local = (original.astype(float)-origin)@basis
    low_ids = selected[local[original_faces[selected], 2].min(1) <= -.001]
    assert np.array_equal(low_ids, np.array([r['sourceTriangleId'] for r in low_rows], '<i4'))
    assert all(r['innerFloorOwnershipSupported'] and r['actualWearerHits'] for r in low_rows)
    # Only pinned inner-component faces may be clipped. A crossing original
    # edge and its two original triangle owners identify each new cut vertex.
    crossings, edge_owners = {}, {}
    for face_id in selected:
        tri = original_faces[face_id]
        z = original[tri, 2].astype(float)
        if not z.min() < PLANE < z.max():
            continue
        keys = [tuple(sorted((int(tri[a]), int(tri[b])))) for a, b in ((0, 1), (1, 2), (2, 0))
                if (z[a]-PLANE)*(z[b]-PLANE) < 0]
        assert len(keys) == 2
        crossings[int(face_id)] = frozenset(keys)
        for key in keys:
            edge_owners.setdefault(key, set()).add(int(face_id))
    ring = prior['cutRings'][0]
    assert len(crossings) == len(edge_owners) == {'L': 883, 'R': 876}[side]
    assert set(crossings) == set(ring['sourceTriangleIds'])
    assert all(len(owners) == 2 for owners in edge_owners.values())
    for index, face_id in enumerate(ring['sourceTriangleIds']):
        previous = ring['sourceTriangleIds'][index-1]
        edge, = crossings[face_id] & crossings[previous]
        a, b = original[list(edge)].astype(float)
        point = a+(PLANE-a[2])/(b[2]-a[2])*(b-a)
        assert np.max(np.abs((point-origin)@basis-ring['localPointsM'][index])) < 1e-10
    return selected, prior, crossings, edge_owners


def protected_faces(target, source, original_faces, inherited_ids, excluded):
    """Prove every non-operated source triangle, corner UV and material survives."""
    source_count = len(original_faces)
    parents = mesh_array(target.data.attributes['boot80_original_face_plus_one'].data, 'value')-1
    assert np.all((parents >= 0) & (parents < source_count))
    protected = np.setdiff1d(np.arange(source_count), np.array(sorted(excluded), np.int32))
    count = np.bincount(parents, minlength=source_count)
    assert np.all(count[protected] == 1), 'An unselected source face was lost or split'
    lookup = np.full(source_count, -1, np.int32)
    lookup[parents] = np.arange(len(parents))
    polygon_ids = lookup[protected]
    starts = mesh_array(target.data.polygons, 'loop_start')[polygon_ids]
    assert np.all(mesh_array(target.data.polygons, 'loop_total')[polygon_ids] == 3)
    loops = starts[:, None]+np.arange(3)
    native_ids = mesh_array(target.data.loops, 'vertex_index')[loops]
    ids = inherited_ids[native_ids]
    expected = original_faces[protected]
    rotations = np.argmax(ids[:, :, None] == expected[:, None, :], axis=2)
    assert np.array_equal(ids, np.take_along_axis(expected, rotations, axis=1))
    assert np.all((np.roll(rotations, -1, axis=1)-rotations) % 3 == 1), 'Protected face winding changed'
    assert np.array_equal(points(target)[native_ids], points(source)[ids]), 'Protected face geometry moved'
    assert np.array_equal(mesh_array(target.data.polygons, 'material_index')[polygon_ids],
                          mesh_array(source.data.polygons, 'material_index')[protected])
    assert list(target.data.materials) == list(source.data.materials)
    assert [u.name for u in target.data.uv_layers] == [u.name for u in source.data.uv_layers]
    for actual_uv, source_uv in zip(target.data.uv_layers, source.data.uv_layers):
        before = mesh_array(source_uv.data, 'uv', 2, np.float32).reshape(-1, 3, 2)[protected]
        before = np.take_along_axis(before, rotations[:, :, None], axis=1)
        actual = mesh_array(actual_uv.data, 'uv', 2, np.float32)[loops]
        assert np.array_equal(actual, before), ('Protected source UV changed', source_uv.name)
        assert actual_uv.active_render == source_uv.active_render
    assert target.data.uv_layers.active.name == source.data.uv_layers.active.name
    return {'sourceTriangles': int(len(protected)), 'geometryTopologyWindingUVMaterialExact': True}


def make_boot(source, side, origin, basis, out, selection, ownership):
    original, original_faces = points(source), faces(source)
    source_names, source_weights = fields(source)
    assert source_names == ['DEF-foot.'+side, 'DEF-toe.'+side, 'DEF-shin.'+side+'.001']
    assert len(source.data.polygons) == len(original_faces)
    assert np.all(mesh_array(source.data.polygons, 'loop_total') == 3)
    assert np.array_equal(mesh_array(source.data.loops, 'vertex_index').reshape(-1, 3), original_faces)
    selected, prior, crossings, edge_owners = selection_evidence(
        side, original, original_faces, origin, basis, selection, ownership)
    selected_set = set(selected.tolist())
    target = source.copy()
    target.data = source.data.copy()
    target.name = 'UNACCEPTED.Boot80Wearer.'+side
    bpy.context.scene.collection.objects.link(target)
    target.hide_render = False
    target.hide_set(False)
    bm = bmesh.new()
    bm.from_mesh(target.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    old_id = bm.verts.layers.int.new('boot80_original_vertex_plus_one')
    edge_a = bm.verts.layers.int.new('boot80_cut_edge_a_plus_one')
    edge_b = bm.verts.layers.int.new('boot80_cut_edge_b_plus_one')
    edge_t = bm.verts.layers.float.new('boot80_cut_edge_t')
    raw_fields = [bm.verts.layers.float.new('boot80_raw_field_'+str(k)) for k in range(len(source_names))]
    for v in bm.verts:
        v[old_id] = v.index+1
        for k, layer in enumerate(raw_fields):
            v[layer] = float(source_weights[v.index, k])
    source_face = bm.faces.layers.int.new('boot80_original_face_plus_one')
    inner_return = bm.faces.layers.int.new('boot80_inner_return')
    toe_patch = bm.faces.layers.int.new('boot80_left_toe_reinforcement')
    for face in bm.faces:
        face[source_face] = face.index+1
    selected_faces = [bm.faces[i] for i in selected]
    chosen_edges = {e for f in selected_faces for e in f.edges}
    chosen_vertices = {v for f in selected_faces for v in f.verts}
    cut_edge_orders = {}
    for edge in chosen_edges:
        if (edge.verts[0].co.z-PLANE)*(edge.verts[1].co.z-PLANE) < 0:
            assert {f[source_face]-1 for f in edge.link_faces} <= selected_set
            order = tuple(v[old_id]-1 for v in edge.verts)
            key = tuple(sorted(order))
            assert {f[source_face]-1 for f in edge.link_faces} == edge_owners[key]
            cut_edge_orders[key] = order
    assert set(cut_edge_orders) == set(edge_owners)
    originals = set(bm.verts)
    bmesh.ops.bisect_plane(bm, geom=list(chosen_vertices)+list(chosen_edges)+selected_faces,
        plane_co=(0., 0., PLANE), plane_no=(0., 0., 1.), dist=1e-8,
        clear_inner=False, clear_outer=False)
    cut_vertices, cut_witness_rows = {}, []
    for v in bm.verts:
        if v in originals:
            assert np.array_equal(np.array(v.co[:], '<f4'), original[v[old_id]-1])
            continue
        v[old_id] = 0
        owners = {f[source_face]-1 for f in v.link_faces}
        assert owners <= crossings.keys()
        edge_candidates = set.intersection(*(set(crossings[i]) for i in owners))
        key, = edge_candidates
        assert key not in cut_vertices and owners == edge_owners[key]
        cut_vertices[key] = v
        a, b = original[list(key)].astype(float)
        t = float((PLANE-a[2])/(b[2]-a[2]))
        cut = (a+t*(b-a)).astype('<f4')
        # The native bisect uses a float32 plane and interpolation. Verify its
        # raw operation exactly in the ACTUAL full-mesh edge endpoint order.
        # The final source ledger still uses the original double 0.09 below.
        raw_cut = np.asarray(v.co[:], '<f4')
        aa, bb = original[list(cut_edge_orders[key])].astype('<f4')
        da = np.float32(aa[2]-np.float32(PLANE))
        db = np.float32(bb[2]-np.float32(PLANE))
        native_t = np.float32(da/np.float32(da-db))
        native_cut = np.asarray(aa+native_t*(bb-aa), '<f4')
        assert raw_cut.tobytes() == native_cut.tobytes(), (
            'Native cut differs from exact float32 edge operation', key,
            cut_edge_orders[key], raw_cut.tolist(), native_cut.tolist())
        v.co = Vector(cut.tolist())
        saved_cut = np.asarray(v.co[:], '<f4')
        assert saved_cut.tobytes() == cut.tobytes(), ('Canonical double-plane cut write changed', key)
        cut_witness_rows.append((key, cut_edge_orders[key], sorted(owners), raw_cut, saved_cut, t, native_t))
        v[edge_a], v[edge_b], v[edge_t] = key[0]+1, key[1]+1, t
        row = ((1-t)*source_weights[key[0]].astype(float)+t*source_weights[key[1]]).astype('<f4')
        for k, layer in enumerate(raw_fields):
            v[layer] = float(row[k])
    assert set(cut_vertices) == set(edge_owners), 'The actual source-edge cut circuit changed'
    # Reconstruct cut UVs from that same original edge, separately for each
    # original triangle corner. UV seams stay distinct; fields are never pruned.
    for uv_source in source.data.uv_layers:
        uv_layer = bm.loops.layers.uv[uv_source.name]
        uv = mesh_array(uv_source.data, 'uv', 2, np.float32).reshape(-1, 3, 2)
        for face in bm.faces:
            parent = face[source_face]-1
            if parent not in crossings:
                continue
            original_ids = original_faces[parent].tolist()
            for loop in face.loops:
                v = loop.vert
                if v[old_id]:
                    value = uv[parent, original_ids.index(v[old_id]-1)]
                else:
                    key = (v[edge_a]-1, v[edge_b]-1)
                    a, b = original[list(key)].astype(float)
                    t = (PLANE-a[2])/(b[2]-a[2])
                    value = ((1-t)*uv[parent, original_ids.index(key[0])].astype(float)+
                             t*uv[parent, original_ids.index(key[1])]).astype('<f4')
                loop[uv_layer].uv = value.tolist()
    removed = {f for f in bm.faces if f[source_face]-1 in selected_set and max(v.co.z for v in f.verts) <= PLANE+1e-7}
    assert sorted(f[source_face]-1 for f in removed) == selected.tolist()
    seed, = [f for f in removed if f[source_face]-1 == prior['seedTriangleId']]
    assert connected(seed, lambda f: f in removed) == removed
    cut_edges = {e for f in removed for e in f.edges if any(g not in removed for g in e.link_faces)}
    assert len(cut_edges) == len(crossings)
    actual_cut_parents = set()
    for edge in cut_edges:
        assert len(edge.link_faces) == 2
        parent, = {f[source_face]-1 for f in edge.link_faces}
        keys = frozenset((v[edge_a]-1, v[edge_b]-1) for v in edge.verts)
        assert keys == crossings[parent]
        actual_cut_parents.add(parent)
    assert actual_cut_parents == set(crossings)
    assert all(sum(e in cut_edges for e in v.link_edges) == 2 for v in cut_vertices.values())
    # This small ledger witnesses the cut operation before the separately
    # recorded collar edit may move its new boundary vertices.
    cut_witness_rows.sort(key=lambda row: row[0])
    cut_witness_file = out/(side+'-actual-cut-provenance.npz')
    np.savez_compressed(cut_witness_file,
        sourceEdges=np.asarray([r[0] for r in cut_witness_rows], '<i4'),
        actualBMeshEndpointOrders=np.asarray([r[1] for r in cut_witness_rows], '<i4'),
        sourceOwnerTriangleIds=np.asarray([r[2] for r in cut_witness_rows], '<i4'),
        rawBMeshCoordinates=np.asarray([r[3] for r in cut_witness_rows], '<f4'),
        finalCutCoordinatesBeforeCollar=np.asarray([r[4] for r in cut_witness_rows], '<f4'),
        originalDoublePlaneT=np.asarray([r[5] for r in cut_witness_rows], '<f8'),
        nativeFloat32PlaneT=np.asarray([r[6] for r in cut_witness_rows], '<f4'))
    del cut_witness_rows
    measured_ring = prior['cutRings'][0]
    cut_area = measured_ring['areaM2']
    # Exact source-face and edge ancestry replaces the rejected global min-Z
    # proxy. Floor01 proves that the disputed low faces are inside the shoe.
    bmesh.ops.delete(bm, geom=list(removed), context='FACES')
    bm.normal_update()
    boundary = {e for e in bm.edges if e.is_boundary}
    assert boundary == cut_edges and all(abs(v.co.z-PLANE) < 2e-7 for e in boundary for v in e.verts)

    def radial(point):
        direction = np.array(point)-origin
        direction[2] = 0
        assert np.linalg.norm(direction) > .005
        return direction/np.linalg.norm(direction)

    def inward(face):
        return (min(v.co.z for v in face.verts) >= PLANE-1e-7 and
                np.dot(face.normal[:], radial(face.calc_center_median())) < -.05)

    inside = set()
    for edge in boundary:
        face, = edge.link_faces
        if face not in inside:
            inside.update(connected(face, inward))
    assert inside and all(all(f in inside for f in e.link_faces) for e in boundary)
    return_parents = {f[source_face]-1 for f in inside}
    for face in inside:
        face[inner_return] = 1
    interior_vertices = {v for f in inside for v in f.verts if all(g in inside for g in v.link_faces)}
    outside_ids = np.array(sorted(set(range(len(original_faces)))-selected_set-return_parents), np.int32)
    outside_tree = BVHTree.FromPolygons(original.tolist(), original_faces[outside_ids].tolist(), all_triangles=True)
    changed_return, return_bearings = [], []
    for v in interior_vertices:
        before = v.co.copy()
        direction = radial(before)
        hit, normal, index, distance = outside_tree.ray_cast(before+Vector(direction)*1e-5, Vector(direction), .035)
        assert hit is not None and np.dot(normal[:], direction) > .05, ('Collar exterior bearing missing', v[old_id]-1)
        distance += 1e-5
        travel = max(0., distance-.0015)
        assert travel < .025
        if travel:
            v.co += Vector(direction)*travel
            changed_return.append({'originalVertexId': v[old_id]-1, 'before': list(before), 'after': list(v.co)})
        return_bearings.append({'originalVertexId': v[old_id]-1, 'cutEdgeOriginalVertexIds': [v[edge_a]-1, v[edge_b]-1],
            'outerSourceTriangleId': int(outside_ids[index]), 'outerPoint': list(hit),
            'retainedThicknessM': float(distance-travel)})
    del outside_tree
    bm.normal_update()
    toe_faces, toe_parents, toe_original_vertices = set(), set(), set()
    if side == 'L':
        def toe_domain(face):
            p = (np.array(face.calc_center_median())-origin)@basis
            return (.180 < p[0] < .214 and .030 < p[1] < .065 and .002 < p[2] < .023
                    and np.dot(face.normal[:], basis[:, 1]-.45*basis[:, 2]) > .15)
        candidates = [f for f in bm.faces if toe_domain(f)]
        assert candidates
        seed = min(candidates, key=lambda f: np.linalg.norm((np.array(f.calc_center_median())-origin)@basis-
                                                           np.array([.196, .047, .011])))
        toe_faces = connected(seed, toe_domain)
        assert 10 < len(toe_faces) < 15000
        toe_parents = {f[source_face]-1 for f in toe_faces}
        assert not toe_parents & (selected_set | return_parents)
        toe_original_vertices = {v[old_id]-1 for f in toe_faces for v in f.verts if v[old_id] > 0}
        for face in toe_faces:
            face[toe_patch] = 1
        before_verts = set(bm.verts)
        bmesh.ops.inset_region(bm, faces=list(toe_faces), use_boundary=True,
            use_even_offset=True, use_interpolate=True, use_relative_offset=False,
            use_edge_rail=False, thickness=.002, depth=.003, use_outset=False)
        for v in bm.verts:
            if v not in before_verts:
                v[old_id] = v[edge_a] = v[edge_b] = 0
                v[edge_t] = 0
    bm.normal_update()
    assert all(f.calc_area() > 0 for f in bm.faces)
    assert all(e.is_manifold or e.is_boundary for e in bm.edges)
    assert {e for e in bm.edges if e.is_boundary} == boundary
    # Scalar custom data carries all raw source fields through local inset
    # interpolation. No deform-layer normalizer, mirroring, or rank pruning.
    deform = bm.verts.layers.deform.active
    assert deform is not None
    for v in bm.verts:
        row = source_weights[v[old_id]-1] if v[old_id] > 0 else np.array([v[layer] for layer in raw_fields], '<f4')
        assert np.isfinite(row).all() and (row >= 0).all() and abs(float(row.sum())-1) < 1e-5
        v[deform].clear()
        for group, weight in enumerate(row):
            if weight > 0:
                v[deform][group] = float(weight)
            v[raw_fields[group]] = float(weight)
    bm.to_mesh(target.data)
    bm.free()
    target.data.update()
    names, weights = fields(target)
    ids = mesh_array(target.data.attributes['boot80_original_vertex_plus_one'].data, 'value')-1
    assert names == source_names
    inherited = ids >= 0
    assert np.array_equal(weights[inherited], source_weights[ids[inherited]])
    raw = np.column_stack([mesh_array(target.data.attributes['boot80_raw_field_'+str(k)].data, 'value', dtype=np.float32)
                           for k in range(len(names))])
    assert np.array_equal(weights, raw), 'Complete scalar source-field transfer changed'
    p = points(target)
    allowed = toe_original_vertices | {r['originalVertexId'] for r in changed_return if r['originalVertexId'] >= 0}
    protected = inherited & ~np.isin(ids, list(allowed))
    assert np.array_equal(p[protected], original[ids[protected]])
    protected_result = protected_faces(target, source, original_faces, ids, selected_set | return_parents | toe_parents)
    normals = mesh_array(target.data.corner_normals, 'vector', 3, np.float32)
    assert np.isfinite(normals).all() and np.all(np.linalg.norm(normals, axis=1) > .9), 'Undefined derivative shading normal'
    target['boot80_status'] = 'UNACCEPTED_SELECTED_WEARER_SOURCE_DERIVATIVE'
    target['boot80_source_object'] = source.name
    target['boot80_source_native_sha256'] = PINS['native70'][1]
    target['boot80_method'] = 'Pinned inner circuit; source-bounded collar return; local selected left toe reinforcement'
    array_file = out/(side+'-derivative.npz')
    triangle_array = faces(target)
    polygon_parents = mesh_array(target.data.attributes['boot80_original_face_plus_one'].data, 'value')-1
    triangle_parents = polygon_parents[mesh_array(target.data.loop_triangles, 'polygon_index')]
    np.savez_compressed(array_file, vertices=p, triangles=triangle_array, namedWeights=weights,
        groupNames=np.array(names), originalVertexIds=ids,
        polygonOriginalFaceIds=polygon_parents, triangleOriginalFaceIds=triangle_parents,
        cutEdgeA=mesh_array(target.data.attributes['boot80_cut_edge_a_plus_one'].data, 'value')-1,
        cutEdgeB=mesh_array(target.data.attributes['boot80_cut_edge_b_plus_one'].data, 'value')-1,
        cutEdgeT=mesh_array(target.data.attributes['boot80_cut_edge_t'].data, 'value', dtype=np.float32))
    bearing_file = out/(side+'-collar-bearings.json')
    bearing_file.write_text(json.dumps(return_bearings, indent=2)+'\n')
    return target, {'sourceVertices': len(original), 'sourceTriangles': len(original_faces),
        'derivativeVertices': len(p), 'derivativeTriangles': len(faces(target)),
        'removedOriginalFaceIds': selected.tolist(), 'cutHeightM': PLANE,
        'cavityRemovalGuard': {'pinnedComponentParentsExact': True, 'singleLiteralSourceEdgeCircuit': True,
            'sourceCutEdges': len(cut_vertices), 'sourceCutAreaM2': cut_area,
            'floorOwnershipPin': PINS['floorOwnership'], 'heightMinimumUsedAsOwnership': False},
        'actualCutProvenance': {'path': str(cut_witness_file.relative_to(ROOT)), 'sha256': sha(cut_witness_file),
            'rawSameFloat32OperationBitExact': True, 'finalDoublePlaneWriteBitExact': True,
            'doublePlaneM': PLANE, 'nativeFloat32PlaneM': float(np.float32(PLANE)),
            'recordedCutEdges': len(cut_vertices), 'stage': 'After canonical cut write; before removal and collar edit'},
        'protectedExterior': protected_result,
        'retainedInnerReturnVerticesChanged': changed_return,
        'collarBearings': {'path': str(bearing_file.relative_to(ROOT)), 'sha256': sha(bearing_file)},
        'leftToeInputFaces': len(toe_parents), 'newInterpolatedVertices': int((ids < 0).sum()),
        'originalOwnSideFieldsExactOnInheritedVertices': True, 'completeRawFieldsTransferred': True,
        'allUnselectedOriginalVertexPositionsExact': True,
        'toeOriginalVertexIdsPermittedToChange': sorted(toe_original_vertices),
        'maximumInheritedVertexEditM': float(np.linalg.norm(p[inherited]-original[ids[inherited]], axis=1).max()),
        'native70QualificationInherited': False, 'compactProduction': False,
        'arrayPackage': {'path': str(array_file.relative_to(ROOT)), 'sha256': sha(array_file)},
        'skinPolicy': 'Own-side raw fields exact on inherited vertices; original-edge linear cut fields and complete scalar inset interpolation; no mirror, normalization or rank pruning.',
        'pbrPolicy': 'Genuine selected materials; every unoperated original face has exact topology, positions, corner UV and material. Compact UV/detail bake pending.'}

def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(OUT) and out != OUT and not out.exists()
    files = {name: checked(pin) for name, pin in PINS.items()}
    out.mkdir(parents=True)
    report = {'acceptedArt': False, 'status': 'UNACCEPTED_BOOT80_CONSTRUCTION_STARTED',
              'sourcePins': PINS, 'recipeSHA256': sha(__file__), 'sides': {}}

    def write():
        (out/'construction.json').write_text(json.dumps(report, indent=2)+'\n')

    write()
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        rig, body = append(files['native47'], ['RiderSkeleton', REFERENCE])
        assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
        assert body.matrix_world.is_identity
        canonical = dict(np.load(files['body02']))
        reference = dict(np.load(files['reference05']))
        bp = points(body)
        assert np.array_equal(bp, reference[REFERENCE+'_basis'])
        source_ids = reference[REFERENCE+'__SOURCE_VERTEX_ID']
        assert [r.value for r in body.data.attributes['_SOURCE_VERTEX_ID'].data] == source_ids.tolist()
        lookup = {int(v): i for i, v in enumerate(canonical['nativeSourceVertexIds'])}
        below = np.flatnonzero(bp[:, 2] < .24)
        assert len(below) == 2638
        names, bw = fields(body)
        for i in below:
            k = lookup[int(source_ids[i])]
            assert np.array_equal(bp[i], canonical['vertices'][k])
            actual = {n: float(v) for n, v in zip(names, bw[i]) if v > 0}
            expected = {n: float(v) for n, v in zip(canonical['jointNames'], canonical['nativeCoefficients'][k]) if v > 0}
            assert actual == expected
        report['actual47Below24cmMatchesNative02'] = {'vertices': len(below), 'positionsExact': True, 'namedFieldsExact': True}
        write()
        jeans, = append(files['native52'], ['RiderJeans'])
        rebind(jeans, rig)
        jnames, jw = fields(jeans)
        ankle_rows = json.loads(files['ankleRows'].read_text())
        assert len(ankle_rows) == 3318
        for row in ankle_rows:
            assert {n: float(v) for n, v in zip(jnames, jw[row['nativeID']]) if v > 0 and n in rig.data.bones} == row['after']
        source_meta = json.loads(files['source75'].read_text())
        package = source_meta['arrays']
        raw = checked((package['path'], package['sha256'])).read_bytes()
        sources = append(files['native70'], ['ActualSelectedBoot.L', 'ActualSelectedBoot.R'])
        for side, source in zip(('L', 'R'), sources):
            rebind(source, rig)
            for suffix, actual in [('Positions', points(source)), ('Triangles', faces(source))]:
                layout = package['layout'][side+suffix]
                expected = np.frombuffer(raw, dtype=layout['dtype'], count=layout['byteLength']//4,
                                         offset=layout['byteOffset']).reshape(layout['shape'])
                assert np.array_equal(actual, expected)
        for donor in list(bpy.data.objects):
            if donor.type == 'ARMATURE' and donor != rig:
                assert not any(o.parent == donor or any(m.type == 'ARMATURE' and m.object == donor for m in o.modifiers)
                               for o in bpy.data.objects if o != donor)
                bpy.data.objects.remove(donor, do_unlink=True)
        assert [o for o in bpy.data.objects if o.type == 'ARMATURE'] == [rig]
        protected = {o.name: witness(o) for o in [body, jeans, *sources]}
        rest_before = rest(rig)
        body.hide_render = False
        body.hide_set(False)
        jeans.hide_render = False
        jeans.hide_set(False)
        targets = []
        selection = json.loads(files['selection'].read_text())
        ownership = json.loads(files['floorOwnership'].read_text())
        for side, source in zip(('L', 'R'), sources):
            origin, basis = frame(canonical, side)
            target, report['sides'][side] = make_boot(source, side, origin, basis, out, selection, ownership)
            targets.append(target)
            source.hide_render = True
            source.hide_set(True)
            write()
        assert protected == {o.name: witness(o) for o in [body, jeans, *sources]}
        assert rest(rig) == rest_before
        jp = points(jeans)
        lower = np.flatnonzero(jp[:, 2] < .24)
        np.savez_compressed(out/'actual-wearer-jeans-corridor.npz',
            bodyVertices=bp[below], bodyOriginalIds=below, bodyNamedWeights=bw[below], bodyGroupNames=np.array(names),
            jeansVertices=jp[lower], jeansOriginalIds=lower, jeansNamedWeights=jw[lower], jeansGroupNames=np.array(jnames))
        saved_witness = runpy.run_path(str(files['witness31']))
        report['expectedSavedSceneWitness'] = saved_witness['retained']({o.name: o for o in [body, jeans, *sources, *targets]}, rig)
        report['expectedDerivativeAttributeWitness'] = {o.name: {
            name: saved_witness['array_sha'](o.data.attributes[name].data, 'value', 1, np.int32)
            for name in ('boot80_original_vertex_plus_one', 'boot80_original_face_plus_one', 'boot80_inner_return',
                         'boot80_cut_edge_a_plus_one', 'boot80_cut_edge_b_plus_one', 'boot80_left_toe_reinforcement')}
            for o in targets}
        report['expectedDerivativeFloatAttributeWitness'] = {o.name: {
            name: saved_witness['array_sha'](o.data.attributes[name].data, 'value', 1, np.float32)
            for name in ('boot80_cut_edge_t', 'boot80_raw_field_0', 'boot80_raw_field_1', 'boot80_raw_field_2')}
            for o in targets}
        report['expectedDerivativeNormalWitness'] = {o.name:
            saved_witness['array_sha'](o.data.corner_normals, 'vector', 3, np.float32) for o in targets}
        write()
        native = out/'UNACCEPTED-selected-wearer-boot-pair80.blend'
        assert bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
        for key, row in PINS.items():
            checked(row)
        report.update(status='UNACCEPTED_BOOT80_PAIR_SAVED_REOPEN_CONTACT_MOTION_PENDING',
            native={'path': str(native.relative_to(ROOT)), 'sha256': sha(native)},
            originalSourcesBodyJeansAnd75RestUnchanged=True, actual52AnkleRowsPreserved=3318,
            pendingAllPoseCorridorInputs={key: PINS[key] for key in ('gameplayMatrices', 'genericMatrices', 'genericReceipt')},
            limits='Construction source pair only. Dense derivative; no compact allocation, independent native reopen, complete 3D/posed collar or foot contact, source-detail bake, moving-art, engine or device acceptance. Parent must assess actual all-pose body/jeans corridor on shared75.')
        write()
    except Exception as error:
        report.update(status='REJECTED_BOOT80_CONSTRUCTION', failure=repr(error))
        write()
        raise


if __name__ == '__main__':
    main()
