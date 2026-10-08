"""One source-retaining CSG forefoot/quarter reconstruction; no bake/render.

Parent checkpoints source and grants one guarded serial CPU2 lease first.
blender -b -t 2 --python-exit-code 1 --python THIS -- FRESH_OUTPUT
Exact selected exterior survives outside the two bounded operands. No fitting
displacements, whole-boot remesh, decimation or fallback. Save before judging.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform, closest_point_on_tri
from mathutils.kdtree import KDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONFIG_PATH = HERE / 'author-inputs.json'
C = json.loads(CONFIG_PATH.read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def pin(row):
    path = ROOT / row['path']
    assert sha(path) == row['sha256'], ('Changed input', row['path'])
    return path


def helpers():
    path = pin(C['readOnlyHelpers'])
    spec = importlib.util.spec_from_file_location('boot04_read_only_helpers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def body_signature(body, rig):
    state = {'positions': [tuple(v.co) for v in body.data.vertices],
             'faces': [tuple(p.vertices) for p in body.data.polygons],
             'weights': [[(g.group, g.weight) for g in v.groups] for v in body.data.vertices],
             'groupNames': [g.name for g in body.vertex_groups],
             'UV': [tuple(d.uv) for d in body.data.uv_layers.active.data],
             'rest75': [(b.name, tuple(b.head_local), tuple(b.tail_local),
                         tuple(tuple(row) for row in b.matrix_local)) for b in rig.data.bones],
             'pose75': [tuple(tuple(row) for row in b.matrix_basis) for b in rig.pose.bones],
             'visibility': [body.hide_render, body.hide_viewport, body.hide_get()]}
    return hashlib.sha256(json.dumps(state, separators=(',', ':')).encode()).hexdigest()


def hull(points):
    """Convex planar shoe-cavity section joins toes; never fits selected mesh."""
    points = sorted(set(tuple(p) for p in points))
    assert len(points) >= 3

    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

    lower, upper = [], []
    for sequence, output in ((points, lower), (points[::-1], upper)):
        for p in sequence:
            while len(output) >= 2 and cross(output[-2], output[-1], p) <= 0:
                output.pop()
            output.append(p)
    return np.array(lower[:-1]+upper[:-1], dtype=np.float64)


def radial_section(polygon, count):
    """One consistently ordered ring, sampled from a convex cavity contour."""
    center = polygon.mean(0)
    a, b = polygon, np.roll(polygon, -1, axis=0)
    edge = b-a
    result = []
    for angle in np.arange(count)*2.*math.pi/count:
        direction = np.array([math.sin(angle), math.cos(angle)])
        # center + t*direction = a + u*edge, with positive t.
        denominator = direction[0]*edge[:, 1]-direction[1]*edge[:, 0]
        valid = np.abs(denominator) > 1e-12
        relative = a-center
        t = np.full(len(a), -1.)
        u = np.full(len(a), -1.)
        t[valid] = (relative[valid, 0]*edge[valid, 1]-relative[valid, 1]*edge[valid, 0])/denominator[valid]
        u[valid] = (relative[valid, 0]*direction[1]-relative[valid, 1]*direction[0])/denominator[valid]
        hits = t[valid & (t > 0.) & (u >= -1e-8) & (u <= 1.+1e-8)]
        assert len(hits)
        result.append(center+direction*hits.min())
    return np.array(result)


def make_solid(name, rings, frame, origin, materials, material_index):
    count = len(rings[0])
    local = np.concatenate(rings)
    vertices = local @ frame.T + origin
    faces = []
    for i in range(len(rings)-1):
        for j in range(count):
            k = (j+1) % count
            faces.append((i*count+j, i*count+k, (i+1)*count+k, (i+1)*count+j))
    faces.extend((tuple(range(count-1, -1, -1)),
                  tuple((len(rings)-1)*count+j for j in range(count))))
    assert len(faces) <= C['limits']['maxOperandFaces']
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], faces)
    for material in materials:
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.material_index = material_index
    mesh.uv_layers.new(name='SelectedSourceUV')
    mesh.attributes.new('Boot04SourceFaceRowPlusOne', 'INT', 'FACE')
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_render = True
    obj.hide_set(True)
    obj['acceptedArt'] = False
    obj['authoringOperandOnly'] = True
    return obj


def outer_last(side, frame, origin, materials):
    profiles = np.array(C['profilesLongBottomRoofLateralWidthMedialWidthM'])[::-1]
    # Densify the explicit authored sections, with no source/body projection.
    xs = np.unique(np.r_[profiles[:, 0], np.arange(profiles[0, 0], profiles[-1, 0], C['outerLongitudinalStepM'])])
    rings = []
    for x in xs:
        bottom, roof, lateral, medial = [np.interp(x, profiles[:, 0], profiles[:, k]) for k in range(1, 5)]
        low, high = -lateral, medial
        width, height = high-low, roof-bottom
        center = (high+low)/2.
        # Broad ball wall and rounded toe crown; anatomical width remains full
        # until94% of roof height. Existing selected crown/detail is often higher.
        anchors = np.array([(bottom, low+.10*width), (bottom, high-.10*width),
                            (bottom+.06*height, high), (bottom+.35*height, high),
                            (bottom+.78*height, high-.01*width),
                            (bottom+.94*height, high-.03*width), (roof, center+.20*width),
                            (roof, center-.20*width), (bottom+.94*height, low+.03*width),
                            (bottom+.78*height, low+.01*width), (bottom+.35*height, low),
                            (bottom+.06*height, low)])
        # Arc length preserves the manually defined section instead of fitting
        # an ellipse to the existing U-shaped cavity.
        closed = np.vstack((anchors, anchors[0]))
        lengths = np.r_[0., np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))]
        t = np.arange(C['outerRingSamples'])/C['outerRingSamples']*lengths[-1]
        yz = np.column_stack([np.interp(t, lengths, closed[:, k]) for k in range(2)])
        yz[:, 1] *= 1 if side == 'R' else -1
        rings.append(np.column_stack((np.full(len(yz), x), yz)))
    return make_solid('Boot04AuthoredOuterLast.'+side, rings, frame, origin, materials, 1)


def cavity_last(side, frame, origin, materials, native):
    local = (native['vertices']-origin) @ frame
    mask = ((local[:, 0] > -.25) & (local[:, 0] < .10) &
            (local[:, 1] < C['cavityTopM']) & (local[:, 1] > -.01) & (np.abs(local[:, 2]) < .10))
    faces = native['faces'][np.any(mask[native['faces']], axis=1)]
    points = local[mask]
    minimum, maximum = points[:, 0].min(), points[:, 0].max()
    ease = C['innerEaseM']
    xs = np.unique(np.r_[minimum-ease, np.arange(minimum+1e-5, maximum, C['cavityLongitudinalStepM']), maximum+ease])
    rings = []
    angles = np.arange(24)*2*math.pi/24.
    disk = ease*np.column_stack((np.sin(angles), np.cos(angles)))
    for x in xs:
        query = np.clip(x, minimum+1e-5, maximum-1e-5)
        distances = local[:, 0]-query
        crossing_faces = faces[(distances[faces].min(1) <= 0.) & (distances[faces].max(1) >= 0.)]
        intersections = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            da, db = distances[crossing_faces[:, a]], distances[crossing_faces[:, b]]
            hit = (da < 0.) != (db < 0.)
            alpha = da[hit]/(da[hit]-db[hit])
            p = local[crossing_faces[hit, a]] + alpha[:, None]*(local[crossing_faces[hit, b]]-local[crossing_faces[hit, a]])
            p = p[(p[:, 1] >= -.01) & (p[:, 1] <= C['cavityTopM']) & (np.abs(p[:, 2]) < .10)]
            intersections.extend(p[:, 1:])
        assert len(intersections) >= 3, ('Actual foot cavity section missing', side, float(query))
        contour = hull(intersections)
        # Actual sagittal foot sections make the toe chamber. Open ankle slices
        # close above the entire selected collar/tongue, at the declared20cm.
        if -.040 <= query <= .040:
            high = contour[contour[:, 0] > .12]
            if len(high):
                contour = hull(np.vstack((contour, [[C['cavityTopM'], high[:, 1].min()],
                                                    [C['cavityTopM'], high[:, 1].max()]])))
        contour = hull((contour[:, None, :]+disk[None, :, :]).reshape((-1, 2)))
        yz = radial_section(contour, C['cavityRingSamples'])
        rings.append(np.column_stack((np.full(len(yz), x), yz)))
    obj = make_solid('Boot04ContinuousInnerCavity.'+side, rings, frame, origin, materials, 2)
    return obj, mask


def apply_boolean(target, operand, operation):
    bpy.ops.object.select_all(action='DESELECT')
    target.hide_set(False)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    mod = target.modifiers.new('Boot04 regional '+operation, 'BOOLEAN')
    mod.operation, mod.solver, mod.object = operation, 'EXACT', operand
    print('BOOT04_BOOLEAN_START', target.name, operation, 'operandFaces', len(operand.data.polygons), flush=True)
    start = time.monotonic()
    bpy.ops.object.modifier_apply(modifier=mod.name)
    elapsed = time.monotonic()-start
    assert len(target.data.polygons) <= C['limits']['maxResultFacesPerBoot']
    print('BOOT04_BOOLEAN_SAVED_IN_MEMORY', operation, round(elapsed, 3), flush=True)
    return {'operation': operation, 'operand': operand.name, 'operandFaces': len(operand.data.polygons),
            'resultFaces': len(target.data.polygons), 'seconds': elapsed}


def bvh(mesh):
    return BVHTree.FromPolygons([v.co for v in mesh.vertices], [p.vertices for p in mesh.polygons])


def inside(tree, point):
    # Three distinct oblique rays; edge/tangent ambiguity is a failed witness.
    verdicts = []
    for raw in ((1., .371, .173), (.229, 1., .417), (.319, .213, 1.)):
        direction = Vector(raw).normalized()
        origin, hits = Vector(point), 0
        for _ in range(64):
            location, _, _, distance = tree.ray_cast(origin, direction, 2.)
            if location is None:
                break
            hits += 1
            origin = location+direction*1e-6
        else:
            raise AssertionError('Ray parity exceeded64 crossings')
        verdicts.append(bool(hits % 2))
    assert len(set(verdicts)) == 1, ('Ambiguous volume witness', tuple(point), verdicts)
    return verdicts[0]


def mesh_points(mesh):
    return np.array([tuple(v.co) for v in mesh.vertices])


def map_and_verify(target, source, frame, origin):
    mesh, original = target.data, source.data
    mesh.calc_loop_triangles()
    source_tree = bvh(original)
    donor_centers = KDTree(len(original.polygons))
    for polygon in original.polygons:
        donor_centers.insert(polygon.center, polygon.index)
    donor_centers.balance()
    original_points = mesh_points(original)
    local = (original_points-origin) @ frame
    face_centers = np.array([tuple(p.center) for p in original.polygons])
    face_normals = np.array([tuple(p.normal) for p in original.polygons])
    centers, normals = (face_centers-origin) @ frame, face_normals @ frame
    radial = centers[:, [0, 2]] - np.array([-.015, -.010 if frame[0, 0] > 0 else .010])
    inner_ids = np.where((centers[:, 0] > -.065) & (centers[:, 0] < .035) &
                         (centers[:, 1] > .035) & (centers[:, 1] < .09) &
                         (np.sum(normals[:, [0, 2]]*radial, axis=1) < -.004))[0]
    assert len(inner_ids), 'Actual selected inner-quarter PBR region missing'
    inner_tree = BVHTree.FromPolygons([v.co for v in original.vertices], [original.polygons[int(i)].vertices for i in inner_ids])
    uv = mesh.uv_layers.active or mesh.uv_layers.new(name='SelectedSourceUV')
    old_uv = original.uv_layers.active
    source_id = mesh.attributes['Boot04SourceFaceRowPlusOne']
    corner_ids = mesh.attributes.new('Boot04CornerSourceTriangle', 'INT', 'CORNER')
    corner_distance = mesh.attributes.new('Boot04CornerSourceDistanceM', 'FLOAT', 'CORNER')
    origin_kind = mesh.attributes.new('Boot04SurfaceKind', 'INT', 'FACE')
    untouched, split, new_exterior, new_inner, inner_fallback, misses = [], 0, 0, 0, 0, []
    exterior_local_correspondence = 0
    distances = []
    for polygon in mesh.polygons:
        kind = polygon.material_index
        assert kind in (0, 1, 2), ('Unexpected CSG material ancestry', kind)
        origin_kind.data[polygon.index].value = kind
        if kind == 0:
            ancestor = int(source_id.data[polygon.index].value)-1
            assert 0 <= ancestor < len(original.polygons), 'Boolean lost selected source-face ancestry'
            old = original.polygons[ancestor]
            lookup = {tuple(original.vertices[v].co): tuple(old_uv.data[l].uv)
                      for v, l in zip(old.vertices, old.loop_indices)}
            actual = [tuple(mesh.vertices[v].co) for v in polygon.vertices]
            unchanged = len(actual) == 3 and set(actual) == set(lookup)
            for point, loop in zip(actual, polygon.loop_indices):
                corner_ids.data[loop].value = ancestor
                if unchanged:
                    assert tuple(uv.data[loop].uv) == lookup[point], 'Surviving selected cornerUV changed'
            if unchanged:
                untouched.append(ancestor)
            else:
                split += 1
            continue
        new_exterior += kind == 1
        new_inner += kind == 2
        for loop in polygon.loop_indices:
            point = mesh.vertices[mesh.loops[loop].vertex_index].co
            normal = polygon.normal.normalized()
            location, donor_normal, ancestor, distance = source_tree.ray_cast(
                point+normal*C['UVRayReachM'], -normal, 2.*C['UVRayReachM'])
            compatible = location is not None and donor_normal.dot(normal) >= C['minimumDonorNormalDot']
            if not compatible and kind == 1:
                # A newly raised quarter lip can lie above the old short collar.
                # Correspond to a nearby facing selected exterior triangle,
                # within25mm; never silently use an opposing inner-wall chart.
                for _, candidate, candidate_distance in donor_centers.find_n(point, 32):
                    old_candidate = original.polygons[candidate]
                    if candidate_distance <= .025 and old_candidate.normal.dot(normal) >= C['minimumDonorNormalDot']:
                        tri = [original.vertices[v].co for v in old_candidate.vertices]
                        location = closest_point_on_tri(point, *tri)
                        ancestor = candidate
                        compatible = True
                        exterior_local_correspondence += 1
                        break
            if not compatible and kind == 2:
                location, donor_normal, inner_index, distance = inner_tree.find_nearest(point)
                assert location is not None
                ancestor = int(inner_ids[inner_index])
                inner_fallback += 1
            elif not compatible:
                # Keep the actual authored mesh and failure receipt. A nearest
                # unrelated island or generic black material is not a fallback.
                misses.append({'polygon': polygon.index, 'loop': loop, 'point': tuple(point)})
                continue
            old = original.polygons[int(ancestor)]
            assert len(old.vertices) == 3
            p = [original.vertices[v].co for v in old.vertices]
            texture = [Vector((*old_uv.data[l].uv, 0.)) for l in old.loop_indices]
            sample = barycentric_transform(location, *p, *texture)
            uv.data[loop].uv = sample[:2]
            corner_ids.data[loop].value = int(ancestor)
            nearest_distance = (point-location).length
            corner_distance.data[loop].value = nearest_distance
            distances.append(nearest_distance)
        polygon.use_smooth = True
    unchanged_set = set(untouched)
    original_centers_local = (face_centers-origin) @ frame
    protected = np.where((original_centers_local[:, 0] > -.105) &
                         (np.max(local[np.array([p.vertices[:] for p in original.polygons])][:, :, 1], axis=1) < -.012))[0]
    assert set(map(int, protected)) <= unchanged_set, 'Protected original rear tread changed'
    # These are witnesses for genuine selected details, not appearance scores.
    lace = np.where((original_centers_local[:, 0] < -.045) & (original_centers_local[:, 0] > -.11) &
                    (original_centers_local[:, 1] > .080))[0]
    retained_lace = len(set(map(int, lace)) & unchanged_set)
    receipt = {'unchangedOriginalTrianglesExactUV': len(untouched), 'splitOriginalSourceTriangles': split,
               'newExteriorFaces': new_exterior, 'newCavityFaces': new_inner,
               'newInnerLiningCornersUsingActualOriginalInnerQuarterPBR': inner_fallback,
               'newExteriorCornersUsingBoundedFacingOriginalTriangle': exterior_local_correspondence,
               'retainedOriginalLaceTongueTriangles': retained_lace, 'originalLaceTongueDomainTriangles': len(lace),
               'protectedRearTreadTrianglesExact': len(protected), 'exteriorCorrespondenceMisses': misses,
               'mappedNewCornerMaximumSourceDistanceM': max(distances, default=0.),
               'UVPolicy': 'Unchanged original corners exact; split original faces retain Boolean-interpolated original charts; new exterior corners ray-correspond to same-side actual selected triangles; genuinely new inner lining explicitly borrows actual original inner-quarter PBR. No supplied normal map exists.',
               'finalRegionalUnwrapAndBakeRequired': True}
    return receipt


def bind(target, frame, origin, side, rig):
    for group in list(target.vertex_groups):
        target.vertex_groups.remove(group)
    groups = {name: target.vertex_groups.new(name=name) for name in
              ('DEF-foot.'+side, 'DEF-toe.'+side, 'DEF-shin.'+side+'.001')}
    local = (mesh_points(target.data)-origin) @ frame
    smooth = lambda t: np.clip(t, 0., 1.)**2*(3.-2.*np.clip(t, 0., 1.))
    toe = .08*smooth((-local[:, 0]-.105)/.060)
    shin = .12*smooth((local[:, 1]-.080)/.060)
    toe[local[:, 1] < .026] = 0.
    shin[local[:, 1] < .026] = 0.
    for i in range(len(local)):
        for name, weight in zip(groups, (1.-toe[i]-shin[i], toe[i], shin[i])):
            if weight:
                groups[name].add([i], float(weight), 'REPLACE')
    mod = target.modifiers.new('Single unchanged native75 shared wearer', 'ARMATURE')
    mod.object = rig
    target.parent = rig
    target.matrix_parent_inverse = rig.matrix_world.inverted()
    assert max(abs(sum(g.weight for g in v.groups)-1.) for v in target.data.vertices) < 2e-6


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/C['outputRoot']) and not out.exists()
    h = helpers()
    all_pins = [C[key] for key in ('workingOutfit', 'canonicalArrays', 'selectedOriginal', 'extraction',
                                  'readOnlyHelpers', 'readOnlyInputs', 'reviewRenderer')]
    all_pins += list(C['sections'].values())+list(C['selectedMaps'].values())
    for row in all_pins:
        pin(row)
    extracted = json.loads(pin(C['extraction']).read_text())
    sections = {side: json.loads(pin(row).read_text()) for side, row in C['sections'].items()}
    native = dict(np.load(pin(C['canonicalArrays'])))
    bpy.ops.wm.open_mainfile(filepath=str(pin(C['workingOutfit'])))
    body, rig = (bpy.data.objects[C['objects'][key]] for key in ('body', 'rig'))
    assert len(rig.data.bones) == 75 and rig.animation_data is None
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    before_body = body_signature(body, rig)
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'REGIONAL_CSG_IN_PROGRESS', 'inputs': C,
              'recipeSHA256': sha(__file__), 'controlsSHA256': sha(CONFIG_PATH), 'sides': {}}
    native_path = out/'anatomical-selected-boots.blend'

    def checkpoint(stage):
        report['status'] = stage
        assert body_signature(body, rig) == before_body
        bpy.ops.wm.save_as_mainfile(filepath=str(native_path), compress=True)
        report['native'] = {'path': str(native_path.relative_to(ROOT)), 'sha256': sha(native_path)}
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')

    for side, source_name in C['objects']['boots'].items():
        source = bpy.data.objects[source_name]
        # Persisted extraction JSON has lists where in-memory snapshots use
        # modifier tuples. Normalize representation, not source measurements.
        assert json.loads(json.dumps(h.state(source))) == extracted['sides'][side]['sourceState']
        assert len(source.data.polygons) <= C['limits']['maxOriginalFacesPerBoot']
        frame, origin = np.array(sections[side]['footFrame']), np.array(sections[side]['footOrigin'])
        original_state = h.state(source)
        target = source.copy()
        target.data = source.data.copy()
        target.name = 'Boot04SelectedAnatomical.'+side
        bpy.context.scene.collection.objects.link(target)
        for mod in list(target.modifiers):
            target.modifiers.remove(mod)
        assert len(target.data.materials) == 1
        material = target.data.materials[0]
        new_outer, new_inner = material.copy(), material.copy()
        new_outer.name, new_inner.name = 'Boot04ActualSelectedNewExterior.'+side, 'Boot04ActualSelectedAuthoredInnerLining.'+side
        materials = (material, new_outer, new_inner)
        target.data.materials.append(new_outer)
        target.data.materials.append(new_inner)
        target.data.attributes.new('Boot04SourceFaceRowPlusOne', 'INT', 'FACE').data.foreach_set(
            'value', np.arange(1, len(target.data.polygons)+1, dtype=np.int32))
        outer = outer_last(side, frame, origin, materials)
        cavity, mask = cavity_last(side, frame, origin, materials, native)
        receipt = {'source': source_name, 'target': target.name, 'booleans': [],
                   'cavityEaseM': C['innerEaseM'], 'outerOperandVertices': len(outer.data.vertices),
                   'cavityOperandVertices': len(cavity.data.vertices), 'sourceOriginalRetainedAsComparison': True}
        report['sides'][side] = receipt
        receipt['booleans'].append(apply_boolean(target, outer, 'UNION'))
        # Test actual anatomical coverage of the solid before carving its cavity.
        union_tree = bvh(target.data)
        points = native['vertices'][mask]
        local_points = (points-origin) @ frame
        under_collar = local_points[:, 1] <= C['coverageThroughHeightM']
        uncovered = [i for i in np.where(under_collar)[0] if not inside(union_tree, points[i])]
        receipt['canonicalFootVerticesBelowCollar'] = int(np.sum(under_collar))
        receipt['preCavityOuterCoverageMisses'] = [points[i].tolist() for i in uncovered]
        checkpoint('UNACCEPTED_ACTUAL_OUTER_UNION_SAVED_'+side)
        assert not uncovered, 'Authored exterior does not enclose actual below-collar foot'
        receipt['booleans'].append(apply_boolean(target, cavity, 'DIFFERENCE'))
        bind(target, frame, origin, side, rig)
        checkpoint('UNACCEPTED_ACTUAL_NEW_TOPOLOGY_CAVITY_SAVED_'+side)
        bm = bmesh.new()
        bm.from_mesh(target.data)
        pending_vertices = set(bm.verts)
        components = 0
        while pending_vertices:
            pending = [pending_vertices.pop()]
            components += 1
            while pending:
                vertex = pending.pop()
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if other in pending_vertices:
                        pending_vertices.remove(other)
                        pending.append(other)
        receipt['topology'] = {'vertices': len(bm.verts), 'faces': len(bm.faces),
                               'connectedComponents': components,
                               'boundaryEdges': sum(e.is_boundary for e in bm.edges),
                               'nonManifoldEdges': sum(not e.is_manifold for e in bm.edges),
                               'zeroAreaFaces': sum(f.calc_area() < 1e-18 for f in bm.faces)}
        bm.free()
        assert components == 1, 'CSG split the selected boot into disconnected pieces'
        assert not any(receipt['topology'][key] for key in ('boundaryEdges', 'nonManifoldEdges', 'zeroAreaFaces'))
        final_tree = bvh(target.data)
        samples = list(points)
        foot_faces = native['faces'][np.all(mask[native['faces']], axis=1)]
        samples.extend(native['vertices'][foot_faces].mean(1))
        inside_leather, clearances = [], []
        for i, point in enumerate(samples):
            if inside(final_tree, point):
                inside_leather.append(i)
            _, _, _, distance = final_tree.find_nearest(Vector(point))
            clearances.append(float(distance))
        receipt['actualFootSurfaceWitness'] = {'verticesAndTriangleCentroids': len(samples),
                                               'insideLeatherSampleRows': inside_leather,
                                               'minimumDistanceM': min(clearances)}
        receipt['materialAncestry'] = map_and_verify(target, source, frame, origin)
        checkpoint('UNACCEPTED_ACTUAL_GEOMETRY_PBR_CORRESPONDENCE_SAVED_'+side)
        assert not inside_leather and min(clearances) >= C['minimumMeasuredClearanceM']
        assert not receipt['materialAncestry']['exteriorCorrespondenceMisses']
        assert receipt['materialAncestry']['newExteriorFaces'] > 0 and receipt['materialAncestry']['newCavityFaces'] > 0
        assert receipt['materialAncestry']['retainedOriginalLaceTongueTriangles'] > 0
        target['acceptedArt'] = False
        target['selectedOriginalSHA256'] = C['selectedOriginal']['sha256']
        target['regionalAuthoringMethod'] = 'Explicit anatomical outer last UNION, continuous actual foot cavity DIFFERENCE; original geometry/UV survive outside observed replacement regions'
        target['finalUVAndBakePending'] = True
        for operand in (outer, cavity):
            operand.hide_render = True
            operand.hide_set(True)
        target.hide_render = False
        source.hide_render = True
        source.hide_set(True)
        expected = dict(original_state)
        expected['visibility'] = [True, False, True]
        assert h.state(source) == expected
        checkpoint('UNACCEPTED_BILATERAL_AUTHORING_PARTIAL_'+side)
    for row in all_pins:
        pin(row)
    checkpoint('UNACCEPTED_SAVED_BILATERAL_SELECTED_REGION_REST_REVIEW_PENDING')
    # Read-only renderer specs, with explicitly matched anatomical views.
    for side, receipt in report['sides'].items():
        frame, origin = np.array(sections[side]['footFrame']), np.array(sections[side]['footOrigin'])
        focus = origin+frame @ np.array([-.095, .058, 0.])
        medial = 1 if side == 'R' else -1
        views = {name: (focus+frame @ np.array(offset)).tolist() for name, offset in
                 [('anatomical-lateral', [0., .12, -.65*medial]),
                  ('anatomical-medial', [0., .12, .65*medial]),
                  ('toe-threequarter', [-.50, .30, .36*medial]),
                  ('heel-threequarter', [.50, .25, .32*medial]), ('top', [-.03, .70, 0.]) ]}
        for role, obj in (('selected-source', receipt['source']), ('new-topology', receipt['target'])):
            spec = {'accepted': False, 'native': report['native'], 'mode': 'stills', 'objects': [obj],
                    'bodyObject': body.name, 'rigObject': rig.name, 'focus': focus.tolist(),
                    'orthoScale': .38, 'views': views,
                    'limits': ['Actual originalPBR comparison; complete body mesh visible.',
                               'Rest diagnostics can reject; played ankle/toe/outfit/bike/native/engine/device gates remain open.']}
            (out/(side+'-'+role+'-review.json')).write_text(json.dumps(spec, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'native': report['native'], 'noBakeOrRender': True}))


if __name__ == '__main__':
    main()
