"""Intended-final selected exterior, genuine rim and complete anatomical cavity.

Use only after the source classification checkpoint. A real short-boot socket
chart replaces whole-bounds registration; the certified lower inner source alone
is removed. The exact selected exterior and upper rim undergo one global smooth
displacement solve. Anatomical geometry supplies only the new inward cavity.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/boots'
SOURCE = PREP / 'retopology-prototype.npz'
DENSE = PREP / 'cleaned-donor.npz'
BODY = ROOT / 'docs/evidence/rider-rebuild/glove-charts01/target01/native-body.npz'
NATIVE = ROOT / 'harness/out/rider-rebuild/selected-boot02/selected-boot-checkpoint.blend'
WITNESS = ROOT / 'docs/evidence/rider-rebuild/boot-cavity-rebuild01/classification01/source-semantic-witness.npz'
GEOMETRY = ROOT / 'assets/blender/rider-rebuild/glove-charts01/geometry-checks.py'
HELPER = Path(__file__).with_name('cavity-geometry.py')
DENSE_HELPER = Path(__file__).with_name('dense-cavity-lineage.py')
PINS = {
    SOURCE: 'd420da6bc7db4fa02ea095266dc174ff07cd3fb657cb0b01b91a319aa6b17853',
    DENSE: '9849de6444632c2dcd1e1d76fda42ac27a7cbe8c7d2c0263ab2082e24b94777f',
    WITNESS: 'f6ff1252fb6a92d47d600e2c3b3c678c7f4a7cce86184be8d9936d416fce3526',
    HELPER: 'a961bc0c408cc87d1acb000e475e2cc9438eb231de3e343179b0c385c7ab0515',
    BODY: 'b34897b3c1fe810d7bd77806a1635f8132b3a43e66986986c218ab23cfad2f45',
    NATIVE: '2e836f508a9799325225affe2cbf1e6347c818ef3eaac2884c8cf48f56d435df',
    GEOMETRY: 'd9b6080dc6380b23e35eaf3978b539b930955e052c4254d869d7e7ff3b8746fa'}
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 1
out = Path(args[0]).resolve()
assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild')
out.mkdir(parents=True, exist_ok=False)
report = {'accepted': False, 'status': 'RUNNING_SOURCE_CAVITY_CONSTRUCTION',
          'recipeSHA256': SHA(__file__), 'helperSHA256': SHA(HELPER),
          'witnessSHA256': SHA(WITNESS), 'boots': [],
          'limits': ['Intended-final construction candidate only; parent plays and judges.',
                     'Compact source inherited UV is invalid and never copied.',
                     'New compact UV requires actual dense PBR/geometric-normal transfer.',
                     'Original source, complete wearer and shared75 rest remain intact.']}

def save():
    (out / 'fit.json').write_text(json.dumps(report, indent=2) + '\n')

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def mesh_arrays(mesh):
    mesh.calc_loop_triangles()
    return np.asarray([tuple(v.co) for v in mesh.vertices]), np.asarray([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)

def body_snapshot(body):
    names = {g.index: g.name for g in body.vertex_groups}
    return [(tuple(v.co), sorted((names[g.group], g.weight) for g in v.groups if g.weight > 0)) for v in body.data.vertices]

def rest_snapshot(rig):
    return [(b.name, tuple(b.head_local), tuple(b.tail_local), tuple(tuple(row) for row in b.matrix_local)) for b in rig.data.bones]

def anatomical_volume(body, side, height, room=0., closed=True):
    bm = bmesh.new(); bm.from_mesh(body.data); bm.normal_update()
    if room:
        for vertex in bm.verts:
            vertex.co += vertex.normal * room
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                         plane_co=(0, 0, height), plane_no=(0, 0, 1), clear_outer=True, dist=1e-7)
    sign = 1 if side == 'L' else -1
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x * sign < 0], context='VERTS')
    boundary = [e for e in bm.edges if e.is_boundary]
    assert boundary and all(abs(v.co.z - height) < 2e-6 for e in boundary for v in e.verts)
    if closed:
        bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
    bmesh.ops.triangulate(bm, faces=list(bm.faces)); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if closed and bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.verts.index_update()
    vertices = np.asarray([tuple(v.co) for v in bm.verts]); faces = np.asarray([[v.index for v in f.verts] for f in bm.faces], dtype=np.int32)
    bm.free(); return vertices, faces

def nearest_obstacle(points, tree, padding):
    signed, goals = [], []
    padding = np.broadcast_to(padding, (len(points),))
    for point, room in zip(points, padding):
        p = Vector(point); hit, normal, row, distance = tree.find_nearest(p)
        assert hit is not None and normal.length > .99
        signed.append(float(distance if (p - hit).dot(normal) >= 0 else -distance))
        goals.append(tuple(hit + normal * float(room)))
    return np.asarray(signed), np.asarray(goals)

def source_chart(source_vertices, target, side):
    names = target['jointNames'].tolist()
    ankle = target['jointHeads'][names.index('DEF-foot.' + side)]
    toe = target['jointHeads'][names.index('DEF-toe.' + side)]
    forward = np.r_[toe[:2] - ankle[:2], 0.]; forward /= np.linalg.norm(forward)
    frame = np.column_stack([-forward, [0., 0., 1.], np.cross(-forward, [0., 0., 1.])])
    ids = [names.index('DEF-foot.' + side), names.index('DEF-toe.' + side)]
    mask = (target['nativeCoefficients'][:, ids].sum(1) > .25) & (target['vertices'][:, 2] < ankle[2] + .025)
    footprint = (target['vertices'][mask] - ankle) @ frame
    # Actual toe and heel SOLE anchors, not raised tongue/strap/whole Y bounds.
    toe_source, heel_source, heel_sole_source = source_vertices[0], source_vertices[4985], source_vertices[3537]
    assert toe_source[0] < -.99 and heel_source[0] > .97 and heel_source[1] < -.50
    toe_target = float(footprint[:, 0].min()) - .014
    heel_target = float(footprint[:, 0].max()) + .012
    sx = (heel_target - toe_target) / (heel_source[0] - toe_source[0])
    width_min = float(footprint[:, 2].min()) - .008
    width_max = float(footprint[:, 2].max()) + .008
    foot_source = source_vertices[source_vertices[:, 1] < .10]
    sz = (width_max - width_min) / np.ptp(foot_source[:, 2])
    # Retain source vertical proportions of the compact short boot. The actual
    # collar is below the anatomical ankle, while the tongue reaches above it.
    sy = sx
    offset = np.array([toe_target - sx * toe_source[0],
                       float(target['vertices'][mask, 2].min()) - .010 - sy * heel_sole_source[1],
                       width_min - sz * foot_source[:, 2].min()])
    mirror = np.diag([1., 1., -1. if side == 'L' else 1.])
    if side == 'L':
        offset[2] = width_min + sz * foot_source[:, 2].max()
    affine = np.eye(4); affine[:3, :3] = frame @ np.diag([sx, sy, sz]) @ mirror
    # X/Z offsets are relative to the ankle; source Y offset is absolute Z.
    translation = ankle.copy(); translation[2] = 0.
    affine[:3, 3] = translation + frame @ offset
    collar = sy * .18001 + offset[1]
    return affine, collar, frame, dict(sourceToeVertex=0, sourceHeelSoleVertex=4985,
                                    sourceSoleVertex=3537, sourceAnchors=[toe_source.tolist(), heel_source.tolist(), heel_sole_source.tolist()],
                                    targetToeHeelAxis=[toe_target, heel_target], scales=[sx, sy, sz],
                                    actualAnkleHead=ankle.tolist(), nativeCollarHeightM=collar,
                                    footYawDegrees=float(np.degrees(np.arctan2(forward[0], -forward[1]))))

try:
    assert all(SHA(p) == digest for p, digest in PINS.items())
    helper = load_module(HELPER, 'selected_boot_cavity_geometry')
    geometry = load_module(GEOMETRY, 'selected_boot_surface_geometry')
    source = dict(np.load(SOURCE)); target = dict(np.load(BODY)); witness = dict(np.load(WITNESS))
    assert np.array_equal(source['vertices'], witness['sourceVertices']) and np.array_equal(source['faces'], witness['sourceFaces'])
    clipped = helper.cut_only_inner(source['vertices'], source['faces'], witness['sourceInnerVisibleMask'], .18001)
    source_loop = helper.one_boundary(clipped['faces'])
    assert len(source_loop) == 98 and abs(clipped['vertices'][source_loop, 1] - .18001).max() < 1e-12
    report['sourceCutTopology'] = helper.topology(clipped['vertices'], clipped['faces'])
    report['sourceOwnership'] = {'innerRimVertices': 98,
                               'untouchedExteriorTriangles': int((~witness['sourceInnerVisibleMask']).sum()),
                               'removedOriginalFaces': int(len(source['faces']) - len(np.unique(clipped['sourceFaceIDs']))),
                               'cutPolicy': 'Certified source inner only, original exterior/tongue/laces/strap untouched'}
    np.savez_compressed(out / 'source-cut-ownership.npz', **clipped,
                        sourceInnerVisibleMask=witness['sourceInnerVisibleMask'],
                        sourceCavityRimLoop=source_loop)
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    before_body, before_rest = body_snapshot(body), rest_snapshot(rig)
    assert np.array_equal(target['vertices'], np.asarray([tuple(v.co) for v in body.data.vertices]))
    names = target['jointNames'].tolist(); body_xyz, body_faces = target['vertices'], target['faces']
    for side in ('R', 'L'):
        affine, cuff, frame, chart = source_chart(source['vertices'], target, side)
        reference = clipped['vertices'] @ affine[:3, :3].T + affine[:3, 3]
        faces = clipped['faces'].copy()
        if side == 'L': faces = faces[:, ::-1]
        loop = helper.one_boundary(faces)
        assert abs(reference[loop, 2] - cuff).max() < 1e-12
        obstacle_v, obstacle_f = anatomical_volume(body, side, float(reference[:, 2].max()) + .035)
        tree = BVHTree.FromPolygons([Vector(row) for row in obstacle_v], obstacle_f.tolist(), all_triangles=True)
        assert (reference[:, 0] * (1 if side == 'L' else -1) > .01).all()
        inner_v, inner_f = anatomical_volume(body, side, cuff, room=.0015, closed=False)
        inner_loop = helper.one_boundary(inner_f); center = inner_v[inner_loop].mean(0)
        angles = np.arctan2(reference[loop, 1] - center[1], reference[loop, 0] - center[0])
        radius = helper.ray_radius(inner_v[inner_loop], center, angles) + .002
        rim_targets = np.column_stack([center[0] + radius * np.cos(angles),
                                      center[1] + radius * np.sin(angles), np.full(len(loop), cuff)])
        edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
        a, b = edges.T; lengths = np.linalg.norm(reference[a] - reference[b], axis=1)
        weights = np.clip(np.median(lengths) / lengths, .2, 5.) * 15
        # Preserve separate material surfaces: source upper inner band requires
        # cavity room, while genuine outer leather requires greater separation.
        # Driving both to one radius would collapse the actual material wall.
        exterior_faces = ~witness['sourceInnerVisibleMask'][clipped['sourceFaceIDs']]
        exterior_vertex = np.zeros(len(reference), dtype=bool)
        exterior_vertex[np.unique(faces[exterior_faces])] = True
        padding = np.where(exterior_vertex, .0065, .0035)
        current = reference.copy(); record = {'side': side, 'chart': chart, 'iterations': []}; report['boots'].append(record)
        for iteration in range(12):
            signed, target_positions = nearest_obstacle(current, tree, padding)
            active = signed < padding; penalty = np.ones(len(current)) * .10
            goal = np.zeros_like(current); goal[active] = target_positions[active] - reference[active]; penalty[active] = 200.
            goal[loop] = rim_targets - reference[loop]; penalty[loop] = 2000.
            displacement, residual = helper.solve_displacement(a, b, weights, penalty, goal, len(current))
            assert residual < 2e-5, 'Unconverged source displacement field'
            proposed = reference + displacement; proposed[loop] = rim_targets
            maximum_step = float(np.linalg.norm(proposed - current, axis=1).max())
            step = min(1., .008 / max(maximum_step, 1e-12))
            for backtrack in range(13):
                next_positions = current + step * (proposed - current)
                if helper.orientation_path(current, next_positions, faces): break
                step *= .5
            else:
                raise AssertionError('No orientation-preserving global source step')
            current = next_positions
            current[loop, 2] = cuff
            record['iterations'].append({'iteration': iteration, 'bodyConstraints': int(active.sum()),
                                         'minimumVertexClearanceM': float(signed.min()), 'CGResidual': residual,
                                         'maximumProposedStepM': maximum_step, 'step': step, 'backtracks': backtrack})
        deformation = geometry.deformation_metrics(current, reference, faces)
        record['maximumSourceRimTargetErrorM'] = float(np.linalg.norm(current[loop] - rim_targets, axis=1).max())
        record['minimumPrincipalStretch'] = float(deformation['principalStretches'].min())
        record['maximumPrincipalStretch'] = float(deformation['principalStretches'].max())
        # Persist source/reference/fitted identity BEFORE any qualified-candidate
        # assertion. Failures retain useful real-source construction witnesses.
        np.savez_compressed(out / ('fitted-outer-' + side + '.npz'), vertices=current, faces=faces,
                            referenceVertices=reference, cutReferenceVerticesSource=clipped['vertices'],
                            sourceToNativeAffine=affine, sourceCavityRimLoop=loop,
                            sourceVertexIDs=clipped['sourceVertexIDs'], sourceFaceIDs=clipped['sourceFaceIDs'],
                            sourceEdgeVertexIDs=clipped['sourceEdgeVertexIDs'], sourceEdgeInterpolationT=clipped['sourceEdgeInterpolationT'],
                            sourceCompactVertices=source['vertices'], sourceCompactFaces=source['faces'],
                            sourceInnerVisibleMask=witness['sourceInnerVisibleMask'], **deformation)
        save()
        assert record['maximumSourceRimTargetErrorM'] < 1e-7, 'True source rim constraints did not converge'
        assert helper.orientation_path(reference, current, faces), 'Source chart path reverses a reference face'
        assert record['minimumPrincipalStretch'] >= .60 and record['maximumPrincipalStretch'] <= 1.70, 'Source exterior distortion fails bounded shape preservation'
        samples = np.vstack([current, current[faces].mean(1)])
        clearance = geometry.signed_distances(samples, obstacle_v, obstacle_f, chunk_size=32)
        assert not clearance['ambiguous'].any()
        record['minimumOuterVertexAndCentroidClearanceM'] = float(clearance['signedDistance'].min()); save()
        assert record['minimumOuterVertexAndCentroidClearanceM'] >= .001, 'Source exterior still penetrates complete foot obstacle'
        outer_room = geometry.certify_clearance(current, faces, obstacle_v, obstacle_f,
                                               minimum=.001, max_depth=3, max_samples=50000)
        record['fullSurfaceOuterPositiveRoom'] = outer_room; save()
        assert outer_room['qualified'], 'Source outer positive room is unqualified'
        outer_assay = geometry.self_intersections(np.vstack([current, obstacle_v]),
                                                 np.vstack([faces, obstacle_f + len(current)]))
        pairs = outer_assay['intersectingPairs']
        cross = pairs[(pairs[:, 0] < len(faces)) != (pairs[:, 1] < len(faces))]
        source_self = pairs[(pairs[:, 0] < len(faces)) & (pairs[:, 1] < len(faces))]
        record['outerBodyTriangleIntersections'] = len(cross); record['sourceOuterSelfIntersections'] = len(source_self); save()
        assert len(cross) == len(source_self) == 0, 'Full source/body or source self triangle intersection'
        inner_clearance = geometry.signed_distances(np.vstack([inner_v, inner_v[inner_f].mean(1)]), obstacle_v, obstacle_f, chunk_size=32)
        record['minimumInnerVertexAndCentroidClearanceM'] = float(inner_clearance['signedDistance'].min()); save()
        assert not inner_clearance['ambiguous'].any() and inner_clearance['signedDistance'].min() >= .0005
        inner_room = geometry.certify_clearance(inner_v, inner_f, obstacle_v, obstacle_f,
                                               minimum=.0005, max_depth=3, max_samples=50000)
        record['fullSurfaceInnerPositiveRoom'] = inner_room; save()
        assert inner_room['qualified'], 'Anatomical inner positive room is unqualified'
        bridge = helper.annulus(current, faces, inner_v, inner_f)
        all_v = np.vstack([current, inner_v]); all_f = np.vstack([faces, inner_f[:, ::-1] + len(current), bridge])
        shell_topology = helper.topology(all_v, all_f); record['shellTopology'] = shell_topology; save()
        assert shell_topology['boundaryEdges'] == shell_topology['nonmanifoldEdges'] == shell_topology['sameDirectionInteriorEdges'] == 0
        shell_assay = geometry.self_intersections(all_v, all_f)
        record['shellSelfIntersections'] = len(shell_assay['intersectingPairs']); save()
        assert record['shellSelfIntersections'] == 0, 'Source/cavity/rim self intersections'
        obj = bpy.data.objects['ActualSelectedBoot.' + side]
        assert obj.matrix_world.is_identity, 'Actual native footwear requires identity world matrix'
        mesh = bpy.data.meshes.new('Actual selected exterior and complete wearer cavity ' + side)
        mesh.from_pydata(all_v, [], all_f); mesh.update()
        for material in obj.data.materials: mesh.materials.append(material)
        obj.data = mesh; obj.vertex_groups.clear()
        field_faces = body_faces[(body_xyz[body_faces, 0] * (1 if side == 'L' else -1) > 0).all(1)
                                & (body_xyz[body_faces, 2] < reference[:, 2].max() + .07).all(1)]
        field_tree = BVHTree.FromPolygons([Vector(row) for row in body_xyz], field_faces.tolist(), all_triangles=True)
        groups = {}; fields = np.zeros((len(all_v), len(names)))
        for vertex in mesh.vertices:
            hit, normal, row, distance = field_tree.find_nearest(vertex.co)
            tri = field_faces[row]; xyz = body_xyz[tri]; e0, e1 = xyz[1] - xyz[0], xyz[2] - xyz[0]
            uv = np.linalg.lstsq(np.column_stack([e0, e1]), np.asarray(hit) - xyz[0], rcond=None)[0]
            bary = np.maximum([1 - uv.sum(), uv[0], uv[1]], 0.); bary /= bary.sum()
            field = bary @ target['nativeCoefficients'][tri]; slots = np.argsort(field)[::-1][:4]
            total = float(field[slots].sum()); assert total > 0
            fields[vertex.index, slots] = field[slots] / total
            for slot in slots:
                if field[slot] <= 0: continue
                name = names[int(slot)]
                if name not in groups: groups[name] = obj.vertex_groups.new(name=name)
                groups[name].add([vertex.index], float(fields[vertex.index, slot]), 'REPLACE')
        face_source = mesh.attributes.new('_SOURCE_FACE_ID', 'INT', 'FACE')
        face_role = mesh.attributes.new('_SOURCE_OUTER_FACE', 'INT', 'FACE')
        for face in mesh.polygons:
            face.use_smooth = True
            face_source.data[face.index].value = int(clipped['sourceFaceIDs'][face.index]) if face.index < len(faces) else -1
            face_role.data[face.index].value = int(face.index < len(faces))
        # Coherent intended UV layout is constructed here. No invalid inherited
        # compact point atlas is copied or claimed to be original artwork.
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=.75, island_margin=.015)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj['sourceAppearanceStatus'] = 'COHERENT_COMPACT_UV_REQUIRES_FITTED_ORIGINAL_DENSE_PBR_BAKE'
        sole = current[current[:, 2] <= float(current[:, 2].min()) + .0015]
        np.savez_compressed(out / ('anatomical-cavity-' + side + '.npz'), vertices=inner_v, faces=inner_f,
                            cuffLoop=inner_loop, bridgeFaces=bridge, fittedSourceRim=current[loop])
        np.savez_compressed(out / ('boot-final-geometry-' + side + '.npz'), vertices=all_v, faces=all_f,
                            nativeFourCoefficients=fields, jointNames=target['jointNames'],
                            actualSolePatchVertices=sole, solePatchCenter=sole.mean(0), footFrame=frame,
                            sourceCavityRimLoop=loop, preservedSourceFaceCount=len(faces),
                            preservedSourceVertexCount=len(current), nativeCollarHeightM=cuff,
                            sourceEdgeVertexIDs=clipped['sourceEdgeVertexIDs'],
                            sourceEdgeInterpolationT=clipped['sourceEdgeInterpolationT'])
        record['actualSolePatchCenterM'] = sole.mean(0).tolist()
        record['nativeVertices'] = len(mesh.vertices); record['nativeTriangles'] = len(all_f)
        record['appearanceStatus'] = 'Needs fitted actual dense maps and dense cut ownership; geometry is not art accepted'
        save()
    assert before_body == body_snapshot(body) and before_rest == rest_snapshot(rig)
    report['qualifiedRestFit'] = True
    report['restFitScope'] = 'Both rest boots: complete anatomical foot/calf obstacle, bounded source strain, full-surface positive room, zero full triangle body/self intersections, closed material shell. No motion, art or dense appearance acceptance.'
    save()
    # Preserve the finished geometry unit before the independent dense detail
    # invocation. Pending dense lineage/bake never becomes substituted artwork.
    report['denseAppearanceStatus'] = 'PENDING_INDEPENDENT_ORIGINAL_DENSE_INNER_CUT_PAIR_AND_4K_BAKE'
    report['nextDenseRecipe'] = {'path': str(Path(__file__).with_name('pair-fitted-dense.py')),
                               'sourceHelperSHA256': SHA(DENSE_HELPER)}
    assert all(SHA(p) == digest for p, digest in PINS.items())
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'selected-boot-cavity.blend'))
    report['native'] = {'path': str(out / 'selected-boot-cavity.blend'), 'sha256': SHA(out / 'selected-boot-cavity.blend')}
    report['bodyAnd75RestByteValuesPreserved'] = True
    report['bodyAnd75RestUntouched'] = True
    report['status'] = 'SOURCE_CAVITY_GEOMETRY_CANDIDATE_UNACCEPTED_DENSE_APPEARANCE_PENDING'
except BaseException as error:
    report['status'] = 'REJECTED_BEFORE_NATIVE_CANDIDATE'
    report['error'] = type(error).__name__ + ': ' + str(error)
    raise
finally:
    save(); print(json.dumps({key: report[key] for key in ('status', 'error', 'native') if key in report}))
