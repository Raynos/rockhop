"""One parent-guarded selected shoe edit, not a production or moving-art pass.

Blender -b -t 2 --python-exit-code 1 --python author.py -- FRESH_OUTPUT
Keep the actual own-side selected exterior. Remove its obsolete hidden heel
floor, retain a thin collar return, and author only the measured left toe lip.
No optimizer, body mask, global registration, source overwrite or native70 pass.
"""
import hashlib
import json
from pathlib import Path
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


def make_boot(source, side, origin, basis, out):
    original = points(source)
    original_faces = faces(source)
    source_names, source_weights = fields(source)
    source_tree = BVHTree.FromPolygons(original.tolist(), original_faces.tolist(), all_triangles=True)
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
    source_xyz = [bm.verts.layers.float.new('boot80_source_'+axis) for axis in 'xyz']
    for v in bm.verts:
        v[old_id] = v.index+1
        for k, layer in enumerate(source_xyz):
            v[layer] = v.co[k]
    source_face = bm.faces.layers.int.new('boot80_original_face_plus_one')
    for f in bm.faces:
        f[source_face] = f.index+1
    originals = set(bm.verts)
    plane = .090
    # This is an ordinary topology cut on the EXISTING cavity. No fitted body
    # shell is generated. Coplanar exterior splits preserve the exterior shape.
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
        plane_co=(0., 0., plane), plane_no=(0., 0., 1.), dist=1e-8,
        clear_inner=False, clear_outer=False)
    for v in bm.verts:
        if v not in originals:
            v[old_id] = 0
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    tree = BVHTree.FromBMesh(bm)
    heel_ray = origin+basis@np.array([-.030, -.010, .35])
    hit, _, seed_id, _ = tree.ray_cast(Vector(heel_ray), Vector((0., 0., -1.)))
    assert hit is not None and .006 < hit.z < .025, 'Measured inner footbed seed changed'
    removed = connected(bm.faces[seed_id], lambda f: max(v.co.z for v in f.verts) <= plane+1e-7)
    removed_points = np.array([v.co[:] for f in removed for v in f.verts])
    local = (removed_points-origin)@basis
    assert len(removed) > 100 and len(removed) < len(original_faces)//2
    assert local[:, 2].min() > -.001 and local[:, 0].max() < .11, 'Cavity selection reached exterior sole/toe'
    deleted_source_faces = sorted({f[source_face]-1 for f in removed})
    assert deleted_source_faces[0] >= 0, 'A removed face lost its own-side source parent'
    bmesh.ops.delete(bm, geom=list(removed), context='FACES')
    bm.normal_update()
    boundary = [e for e in bm.edges if e.is_boundary]
    assert boundary and all(abs(v.co.z-plane) < 2e-7 for e in boundary for v in e.verts)
    assert all(sum(e.is_boundary for e in v.link_edges) == 2 for e in boundary for v in e.verts)
    # The first opposite-facing wall bounds the already-selected leather.
    # Move ONLY unshared interior-return vertices to 1.5 mm inside that wall;
    # the wearer is a verification object, never the shape generator.
    def radial(p):
        d = np.array(p)-origin
        d[2] = 0
        assert np.linalg.norm(d) > .005
        return d/np.linalg.norm(d)

    def inward(f):
        return f.calc_center_median().z >= plane-1e-7 and np.dot(f.normal[:], radial(f.calc_center_median())) < -.05

    inside = set()
    for edge in boundary:
        for face in edge.link_faces:
            inside.update(connected(face, inward))
    interior_vertices = {v for f in inside for v in f.verts if all(g in inside for g in v.link_faces)}
    changed_return, unresolved_return = [], []
    for v in interior_vertices:
        before = v.co.copy()
        d = radial(before)
        hit, normal, face_id, distance = source_tree.ray_cast(before+Vector(d)*1e-5, Vector(d), .035)
        if hit is None or np.dot(normal[:], d) <= .05:
            unresolved_return.append(v[old_id]-1)
            continue
        travel = max(0., distance+1e-5-.0015)
        assert travel < .025
        if travel > 0:
            v.co += Vector(d)*travel
            changed_return.append({'originalVertexId': v[old_id]-1, 'outerBearingSourceFace': face_id,
                                   'before': list(before), 'after': list(v.co)})
    bm.normal_update()
    toe_faces = set()
    toe_original_vertices = set()
    if side == 'L':
        # One deliberate connected toe-to-welt reinforcement patch; selected
        # crown, outsole and all right-toe vertices are outside this operation.
        def toe_domain(f):
            p = (np.array(f.calc_center_median())-origin)@basis
            return (.180 < p[0] < .214 and .030 < p[1] < .065 and .002 < p[2] < .023
                    and np.dot(f.normal[:], basis[:, 1]-.45*basis[:, 2]) > .15)
        bm.faces.ensure_lookup_table()
        candidates = [f for f in bm.faces if toe_domain(f)]
        assert candidates
        seed = min(candidates, key=lambda f: np.linalg.norm((np.array(f.calc_center_median())-origin)@basis-
                                                          np.array([.196, .047, .011])))
        toe_faces = connected(seed, toe_domain)
        assert 10 < len(toe_faces) < 15000
        toe_original_vertices = {v[old_id]-1 for f in toe_faces for v in f.verts if v[old_id] > 0}
        before_verts = set(bm.verts)
        # Blender's ordinary Inset Region creates a connected border and
        # interpolates UV/vertex-group data. Depth is outward, not a field solve.
        # https://docs.blender.org/api/5.1/bmesh.ops.html#bmesh.ops.inset_region
        bmesh.ops.inset_region(bm, faces=list(toe_faces), use_boundary=True,
            use_even_offset=True, use_interpolate=True, use_relative_offset=False,
            use_edge_rail=False, thickness=.002, depth=.003, use_outset=False)
        for v in bm.verts:
            if v not in before_verts:
                v[old_id] = 0
    bm.normal_update()
    assert all(f.calc_area() > 0 for f in bm.faces)
    assert all(e.is_manifold or e.is_boundary for e in bm.edges)
    # Existing source vertices keep their exact own-side bind even if Blender's
    # inset data interpolation touched them. Only newly created vertices interpolate.
    deform = bm.verts.layers.deform.active
    assert deform is not None
    for v in bm.verts:
        if v[old_id] > 0:
            row = v[deform]
            row.clear()
            for group, weight in enumerate(source_weights[v[old_id]-1]):
                if weight > 0:
                    row[group] = float(weight)
    # Save editable n-gons/quads as authored. The native output and source arrays
    # explicitly remain dense; a compact family/bake is a separate pending unit.
    bm.to_mesh(target.data)
    bm.free()
    target.data.update()
    target['boot80_status'] = 'UNACCEPTED_SELECTED_WEARER_SOURCE_DERIVATIVE'
    target['boot80_source_object'] = source.name
    target['boot80_source_native_sha256'] = PINS['native70'][1]
    target['boot80_method'] = 'Internal heel floor removal; source-bounded thin collar return; own-side selected toe lip'
    names, weights = fields(target)
    assert names == ['DEF-foot.'+side, 'DEF-toe.'+side, 'DEF-shin.'+side+'.001']
    assert np.isfinite(weights).all() and (weights >= 0).all() and np.max(np.abs(weights.sum(1)-1)) < 1e-5
    ids = np.array([r.value-1 for r in target.data.attributes['boot80_original_vertex_plus_one'].data], '<i4')
    assert names == source_names
    inherited = ids >= 0
    assert np.array_equal(weights[inherited], source_weights[ids[inherited]])
    p = points(target)
    inherited_delta = np.linalg.norm(p[inherited]-original[ids[inherited]], axis=1)
    allowed_edits = toe_original_vertices | {v['originalVertexId'] for v in changed_return if v['originalVertexId'] >= 0}
    protected_vertices = inherited & ~np.isin(ids, list(allowed_edits))
    assert np.array_equal(p[protected_vertices], original[ids[protected_vertices]]), 'An unselected exterior/source vertex moved'
    np.savez_compressed(out/(side+'-derivative.npz'), vertices=p, triangles=faces(target),
        namedWeights=weights, groupNames=np.array(names), originalVertexIds=ids)
    return target, {'sourceVertices': len(original), 'sourceTriangles': len(original_faces),
        'derivativeVertices': len(p), 'derivativeTriangles': len(faces(target)),
        'removedOriginalFaceIds': deleted_source_faces, 'cutHeightM': plane,
        'removedRegionLocalBoundsM': [local.min(0).tolist(), local.max(0).tolist()],
        'retainedInnerReturnVerticesChanged': changed_return, 'unresolvedReturnOriginalVertexIds': unresolved_return,
        'leftToeInputFaces': len(toe_faces), 'newInterpolatedVertices': int((ids < 0).sum()),
        'originalOwnSideFieldsExactOnInheritedVertices': True,
        'allUnselectedOriginalVertexPositionsExact': True,
        'toeOriginalVertexIdsPermittedToChange': sorted(toe_original_vertices),
        'maximumInheritedVertexEditM': float(inherited_delta.max()),
        'native70QualificationInherited': False, 'compactProduction': False,
        'skinPolicy': 'Own-side native fields retained exactly; new cut/inset fields use Blender source interpolation, no mirroring or rank pruning.',
        'pbrPolicy': 'Own-side genuine selected materials/UV carried for construction inspection. Fresh compact UV and selected-detail bake remain pending.'}


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
        for side, source in zip(('L', 'R'), sources):
            origin, basis = frame(canonical, side)
            _, report['sides'][side] = make_boot(source, side, origin, basis, out)
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
