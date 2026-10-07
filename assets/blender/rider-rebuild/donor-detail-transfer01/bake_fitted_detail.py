"""Intended-final compact unwrap and ACTUAL fitted dense appearance bake.

Run only after source checkpoint + parent serial OS resource admission:
blender --background --threads 2 --python-exit-code 1 --python THIS -- MANIFEST FRESH_OUT
The manifest pins a corrected native fit, postcut reference/fitted triangle NPZ,
original dense/corner-UV/maps and explicit cap cuts, support/cage and lining policy.
No original source is saved, edited or substituted on missing coverage.
"""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from transport_core import clip_source_triangles, triangle_frame, transport_point, validate_support, validate_transported_triangles

sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pinned(row):
    path = Path(row['path']).resolve()
    assert path.is_file() and sha(path) == row['sha256'], ('Missing/changed intended-final input', str(path))
    return path

def mesh(name, vertices, faces):
    data = bpy.data.meshes.new(name+'Mesh'); data.from_pydata(vertices, [], faces); data.update()
    obj = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(obj)
    for polygon in data.polygons: polygon.use_smooth = True
    return obj

def fingerprint(obj):
    names = {g.index: g.name for g in obj.vertex_groups}
    return hashlib.sha256(json.dumps({'vertices': [list(v.co) for v in obj.data.vertices],
        'faces': [list(p.vertices) for p in obj.data.polygons],
        'fields': [sorted((names[g.group], g.weight) for g in v.groups if g.weight > 0) for v in obj.data.vertices],
        'ids': {a.name: [d.value for d in a.data] for a in obj.data.attributes if a.data_type == 'INT'},
        'matrixWorld': [list(row) for row in obj.matrix_world]}, separators=(',', ':')).encode()).hexdigest()

def material(name):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    mat.node_tree.nodes.clear()
    output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    return mat, output

def unwrap(obj):
    # Retain rejected inherited compact UV only as source lineage, then author a
    # single unambiguous render atlas in this new derivative. Masters stay intact.
    inherited = {layer.name: np.asarray([tuple(d.uv) for d in layer.data]) for layer in obj.data.uv_layers}
    for layer in list(obj.data.uv_layers): obj.data.uv_layers.remove(layer)
    layer = obj.data.uv_layers.new(name='ActualCoherentDenseBakeAtlas'); layer.active_render = True
    obj.data.uv_layers.active = layer
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.01, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    layer = obj.data.uv_layers.active
    assert layer and all(0 <= x <= 1 for d in layer.data for x in d.uv), 'Coherent derivative atlas outside unit square'
    return layer, inherited

def bake_image(scene, source, target, destination, name, kind, out, size=4096):
    image = bpy.data.images.new(name, size, size, alpha=True)
    image.colorspace_settings.name = 'sRGB' if name.endswith('albedo') else 'Non-Color'
    image.generated_color = (0, 0, 0, 0)
    for node in destination: node.image = image
    bpy.ops.object.select_all(action='DESELECT'); source.select_set(True); target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.bake(type=kind)
    image.file_format = 'PNG'; image.filepath_raw = str(out/(name+'.png')); image.save(); image.pack()
    return image, {'path': image.filepath_raw, 'sha256': sha(image.filepath_raw), 'width': size, 'height': size}

def support_pixels(image, target, outer_count):
    size = image.size[0]; assert list(image.size) == [size, size]
    raw = np.empty(size*size*4, dtype=np.float32); image.pixels.foreach_get(raw)
    pixels = raw.reshape(size, size, 4)[:, :, :3]
    ownership = np.zeros((size, size), dtype=np.uint16)
    for face in list(target.data.polygons)[:outer_count]:
        uv = np.asarray([tuple(target.data.uv_layers.active.data[i].uv) for i in face.loop_indices]) * (size-1)
        low, high = np.floor(uv.min(0)).astype(int), np.ceil(uv.max(0)).astype(int)
        x, y = np.meshgrid(np.arange(low[0], high[0]+1)+.5, np.arange(low[1], high[1]+1)+.5)
        p = np.stack([x, y], axis=2)
        side = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            edge, q = uv[j]-uv[i], p-uv[i]
            side.append(edge[0]*q[:, :, 1]-edge[1]*q[:, :, 0])
        signs = np.stack(side)
        interior = (signs > 1e-6).all(0) | (signs < -1e-6).all(0)
        ownership[low[1]:high[1]+1, low[0]:high[0]+1] += interior.astype(np.uint16)
    assert not (ownership > 1).any(), 'Coherent atlas has overlapping exterior pixel ownership'
    mask = ownership == 1
    inside = mask.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): inside &= np.roll(mask, (dy, dx), axis=(0, 1))
    inside[[0, -1], :] = False; inside[:, [0, -1]] = False
    assert inside.any(), 'No measurable exterior atlas pixels'
    missing = inside & (pixels.min(axis=2) < .95)
    receipt = {'outerInteriorPixels': int(inside.sum()), 'missingSourceSupportPixels': int(missing.sum()),
               'overlappingExteriorInteriorPixels': int((ownership > 1).sum()),
               'edgeExclusionPixels': 1, 'whiteMinimumChannel': .95,
               'policy': 'Actual selected-to-active constant-white authority; misses must fail, never colour-filled'}
    assert not missing.any(), ('Actual source bake has unsupported interior pixels', receipt)
    return receipt

def main(manifest_path, out):
    assert not out.exists(), 'Preserve preceding source/art experiments'
    assert out.is_relative_to(HERE.parents[3]/'harness/out/rider-rebuild'), 'Private output only; never write player/source master paths'
    specification = json.loads(manifest_path.read_text())
    assert specification['schema'] == 'rockhop-fitted-dense-detail-v1'
    assert specification['accepted'] is False and specification['mapSize'] == 4096
    source_native = pinned(specification['native']); fit_path = pinned(specification['fit'])
    fit_receipt_path = pinned(specification['fitReceipt'])
    fit_receipt = json.loads(fit_receipt_path.read_text())
    assert 'REJECTED' not in fit_receipt.get('status', '').upper(), 'Never bake a rejected fit experiment'
    assert fit_receipt.get('native', {}).get('sha256') == specification['native']['sha256'], 'Fit receipt lacks this native candidate'
    assert fit_receipt.get('bodyAnd75RestUntouched') is True, 'Fit must preserve its actual body/rest input'
    dense_path = pinned(specification['dense']); maps = {k: pinned(v) for k, v in specification['maps'].items()}
    assert set(maps) == {'albedo', 'metallicRoughness'}
    fit, dense = dict(np.load(fit_path)), dict(np.load(dense_path))
    reference, input_current, faces = fit['referenceVertices'], fit['vertices'], fit['faces']
    # Bake transport follows the actual Blender float32 native point operator,
    # not extra double-precision solver digits that never entered the mesh.
    current = input_current.astype(np.float32).astype(np.float64)
    assert reference.shape == current.shape and np.isfinite(reference).all() and np.isfinite(current).all()
    affine = fit['sourceToNativeAffine']
    assert affine.shape == (4, 4) and np.isfinite(affine).all() and abs(np.linalg.det(affine[:3, :3])) > 1e-12
    planes = specification['referenceClipPlanes']
    # Native aperture masks are deliberate; no implicit source cap retention.
    original_reference = dense['vertices'] @ affine[:3, :3].T + affine[:3, 3]
    # Existing source cavity/rim anatomy may need semantic selection rather than
    # a plane cut. Selection is explicit original dense rows, never guessed from
    # a closed-boundary count or fabricated from unsupported proximity.
    selection = specification['denseFaceSelection']
    if selection['kind'] == 'explicit-original-dense-face-rows':
        selection_path = pinned(selection['rows'])
        selected_rows = np.asarray(np.load(selection_path)['originalDenseFaceRows'], dtype=np.int64)
        assert len(selected_rows) > 0 and len(np.unique(selected_rows)) == len(selected_rows)
        assert selected_rows.min() >= 0 and selected_rows.max() < len(dense['faces'])
        assert selection['denseSourceSHA256'] == specification['dense']['sha256']
    else:
        assert selection['kind'] == 'all-original-dense-faces-explicitly-qualified'
        selected_rows = np.arange(len(dense['faces']))
    dense_faces, original_uv = dense['faces'].copy(), dense['originalCornerUV'].copy()
    original_normals = dense['donorCornerNormals'].copy()
    if np.linalg.det(affine[:3, :3]) < 0:
        dense_faces = dense_faces[:, ::-1]; original_uv = original_uv[:, ::-1]
        original_normals = original_normals[:, ::-1]
    source_corners, selected_face_ids, original_bary, removed_selected = clip_source_triangles(original_reference, dense_faces[selected_rows], planes)
    original_face_ids = selected_rows[selected_face_ids]
    removed = selected_rows[removed_selected]
    corner_uv = np.einsum('nci,nij->ncj', original_bary, original_uv[original_face_ids])
    # Shared exact reference points receive one fitted map, independent of atlas seams.
    unique, inverse = np.unique(source_corners.reshape(-1, 3), axis=0, return_inverse=True)
    source_tree = BVHTree.FromPolygons([Vector(p) for p in reference], faces.tolist(), all_triangles=True)
    owner, bary, distance = [], [], []
    for point in unique:
        hit, _, face, error = source_tree.find_nearest(Vector(point))
        assert hit is not None, 'Dense point has no supported postcut reference triangle'
        triangle = reference[faces[face]]
        normal = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0]); denom = normal @ normal
        assert denom > 1e-30
        v = np.cross(np.asarray(hit)-triangle[0], triangle[2]-triangle[0]) @ normal / denom
        w = np.cross(triangle[1]-triangle[0], np.asarray(hit)-triangle[0]) @ normal / denom
        weights = np.asarray([1-v-w, v, w]); assert weights.min() >= -1e-7
        weights = np.maximum(weights, 0); weights /= weights.sum()
        owner.append(face); bary.append(weights); distance.append(error)
    owner, bary = np.asarray(owner, dtype=np.int32), np.asarray(bary)
    distances = validate_support(unique, reference[faces], owner, bary, specification['maximumReferenceSupportDistanceM'])
    frames = np.asarray([triangle_frame(current[face]) @ np.linalg.inv(triangle_frame(reference[face])) for face in faces])
    jacobians = frames[owner]
    residual = unique - np.einsum('ni,nij->nj', bary, reference[faces[owner]])
    fitted = np.einsum('ni,nij->nj', bary, current[faces[owner]]) + np.einsum('nij,nj->ni', jacobians, residual)
    minimum_orientation = validate_transported_triangles(source_corners, fitted[inverse].reshape(-1, 3, 3), jacobians[inverse].reshape(-1, 3, 3, 3))
    maximum_residual = float(np.linalg.norm(np.einsum('nij,nj->ni', jacobians, residual), axis=1).max())
    # Original saved dense corner normal authority follows the same deformation,
    # including the declared source-to-native affine and mirrored winding.
    corner_normals = np.einsum('nci,nij->ncj', original_bary, original_normals[original_face_ids])
    corner_normals = corner_normals @ np.linalg.inv(affine[:3, :3])
    fitted_corner_frames = jacobians[inverse].reshape(-1, 3, 3, 3)
    fitted_corner_normals = np.linalg.solve(fitted_corner_frames.transpose(0, 1, 3, 2), corner_normals[..., None])[..., 0]
    fitted_corner_normals /= np.linalg.norm(fitted_corner_normals, axis=2)[:, :, None]
    assert np.isfinite(fitted_corner_normals).all()
    cage_offset = specification['cageOffsetM']; ray_distance = specification['maximumRayDistanceM']
    assert cage_offset > maximum_residual + .001 and ray_distance >= 2*cage_offset
    assert .001 < cage_offset <= .03 and ray_distance <= .06, 'Explicit bounded cage admission'
    out.mkdir(parents=True)
    np.savez_compressed(out/'dense-fitted-lineage.npz', uniqueReferencePoints=unique, uniqueFittedPoints=fitted,
        postcutCompactFaceRows=owner, postcutCompactBarycentrics=bary, originalLocalResidual=residual,
        referenceToFittedJacobians=jacobians, denseOriginalTriangleRows=dense['originalTriangleRows'][original_face_ids],
        denseOriginalFaceRows=original_face_ids, denseOriginalCornerBarycentrics=original_bary,
        denseCornerUV=corner_uv, fittedDenseCornerNormals=fitted_corner_normals,
        fittedDenseFaces=inverse.reshape(-1, 3), removedOriginalFaceRows=removed,
        explicitlyExcludedOriginalDenseFaceRows=np.setdiff1d(np.arange(len(dense['faces'])), selected_rows))
    bpy.ops.wm.open_mainfile(filepath=str(source_native))
    target = bpy.data.objects[specification['objectName']]
    assert target.type == 'MESH' and target.matrix_world.is_identity
    before = fingerprint(target)
    assert np.array_equal(np.asarray([tuple(v.co) for v in target.data.vertices])[:len(current)], current)
    assert len(target.data.polygons) >= len(faces)
    assert np.array_equal(np.asarray([tuple(p.vertices) for p in target.data.polygons[:len(faces)]]), faces)
    outer_count = len(faces)
    rest = [(o.name, [(b.name, list(b.head_local), list(b.tail_local), [list(r) for r in b.matrix_local]) for b in o.data.bones])
            for o in bpy.data.objects if o.type == 'ARMATURE']
    _, inherited_uv = unwrap(target)
    np.savez_compressed(out/'original-compact-uv-lineage.npz', **inherited_uv)
    appearance = mesh('FittedActualDenseAppearanceAuthority', fitted.tolist(), inverse.reshape(-1, 3).tolist())
    appearance.data.normals_split_custom_set(fitted_corner_normals.reshape(-1, 3).tolist())
    original_layer = appearance.data.uv_layers.new(name='OriginalDenseSelectedAtlas')
    for face, uvs in zip(appearance.data.polygons, corner_uv):
        for loop, uv in zip(face.loop_indices, uvs): original_layer.data[loop].uv = uv
    authority, authority_output = material('ActualSelectedDenseEmissionAuthority')
    emission = authority.node_tree.nodes.new('ShaderNodeEmission'); emission.inputs['Color'].default_value = (1, 1, 1, 1)
    authority.node_tree.links.new(emission.outputs[0], authority_output.inputs['Surface'])
    source_image_node = authority.node_tree.nodes.new('ShaderNodeTexImage')
    appearance.data.materials.append(authority)
    destination, destination_output = material('ActualSelectedCoherentDenseTransferredPBR')
    bsdf = destination.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    destination.node_tree.links.new(bsdf.outputs[0], destination_output.inputs['Surface'])
    active = destination.node_tree.nodes.new('ShaderNodeTexImage'); destination.node_tree.nodes.active = active
    target.data.materials.clear(); target.data.materials.append(destination)
    lining = specification.get('liningPolicy')
    destinations = [active]
    if len(target.data.polygons) > outer_count:
        assert lining and lining['kind'] == 'authored-original-source-derived-lining', 'Missing explicit lining/rim authority'
        assert lining['sourceMapSHA256'] == specification['maps']['albedo']['sha256'] and lining['sourceUVProbes']
        original_image = bpy.data.images.load(str(maps['albedo']), check_existing=False)
        width, height = original_image.size
        original_pixels = np.empty(width*height*4, dtype=np.float32); original_image.pixels.foreach_get(original_pixels)
        pixels = original_pixels.reshape(height, width, 4)[:, :, :3]
        sampled = []
        for uv in lining['sourceUVProbes']:
            assert len(uv) == 2 and min(uv) >= 0 and max(uv) <= 1
            x, y = np.rint(np.asarray(uv)*[pixels.shape[1]-1, pixels.shape[0]-1]).astype(int)
            sampled.append(pixels[y, x])
        encoded = np.mean(sampled, axis=0)
        linear = np.where(encoded <= .04045, encoded/12.92, ((encoded+.055)/1.055)**2.4)
        lining_material, lining_output = material('AuthoredSourceDerivedLiningWithoutOriginalFaceAncestry')
        lining_bsdf = lining_material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        lining_bsdf.inputs['Base Color'].default_value = (*linear, 1)
        lining_bsdf.inputs['Roughness'].default_value = float(lining['roughness'])
        lining_material.node_tree.links.new(lining_bsdf.outputs[0], lining_output.inputs['Surface'])
        lining_active = lining_material.node_tree.nodes.new('ShaderNodeTexImage'); lining_material.node_tree.nodes.active = lining_active
        destinations.append(lining_active); target.data.materials.append(lining_material)
        for face in target.data.polygons[outer_count:]: face.material_index = 1
        lining = {**lining, 'sampledSourceLinearBaseColor': linear.tolist(), 'noClaimOfOriginalFaceAncestry': True}
    for face in target.data.polygons[:outer_count]: face.material_index = 0
    target.data.update()
    normals = np.asarray([tuple(v.normal) for v in target.data.vertices])
    cage_points = np.asarray([tuple(v.co) for v in target.data.vertices]) + normals*cage_offset
    cage = mesh('ExplicitMeasuredDenseBakeCage', cage_points.tolist(), [list(p.vertices) for p in target.data.polygons])
    cage.hide_render = True
    fitted_tree = BVHTree.FromPolygons([Vector(p) for p in fitted], inverse.reshape(-1, 3).tolist(), all_triangles=True)
    # Every exterior face gets actual normal-direction support witnesses; finite
    # rays retain source owners so neighbouring fingers/sheets cannot be hidden.
    rays = []
    for face_id, face in enumerate(faces):
        for weights in ([1/3]*3, [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]):
            weights = np.asarray(weights); point = weights @ current[face]
            normal = weights @ normals[face]; normal /= np.linalg.norm(normal)
            hit, source_normal, hit_face, length = fitted_tree.ray_cast(Vector(point+normal*cage_offset), Vector(-normal), ray_distance)
            assert hit is not None and np.dot(source_normal, normal) > .05, ('Missing/outward-invalid fitted dense source ray', face_id)
            # Source triangle must belong to this face's local correspondence
            # neighbourhood, rather than another nearby leg/finger/shell sheet.
            source_owners = owner[inverse.reshape(-1, 3)[hit_face]]
            local_vertices = set(face.tolist())
            assert any(local_vertices.intersection(faces[row].tolist()) for row in source_owners), ('Ray hits unrelated dense source patch', face_id, hit_face)
            rays.append((face_id, hit_face, float(length)))
    scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 1
    scene.render.bake.use_selected_to_active = True; scene.render.bake.use_cage = True
    scene.render.bake.cage_object = cage.name; scene.render.bake.cage_extrusion = 0
    scene.render.bake.max_ray_distance = ray_distance; scene.render.bake.margin = 16
    scene.render.bake.normal_space = 'TANGENT'
    # Check real source support before colouring any missed pixels.
    support, support_receipt = bake_image(scene, appearance, target, destinations, 'actual-dense-support', 'EMIT', out)
    coverage = support_pixels(support, target, outer_count)
    baked, receipts = {}, {'support': support_receipt}
    authority.node_tree.links.new(source_image_node.outputs['Color'], emission.inputs['Color'])
    for role in ('albedo', 'metallicRoughness'):
        image = bpy.data.images.load(str(maps[role]), check_existing=False)
        image.colorspace_settings.name = 'sRGB' if role == 'albedo' else 'Non-Color'; source_image_node.image = image
        baked[role], receipts[role] = bake_image(scene, appearance, target, destinations, 'actual-dense-'+role, 'EMIT', out)
    baked['normal'], receipts['normal'] = bake_image(scene, appearance, target, destinations, 'actual-dense-normal', 'NORMAL', out)
    # Native material consumes precisely these actual 4K derivative images.
    for role in ('albedo', 'metallicRoughness', 'normal'):
        node = destination.node_tree.nodes.new('ShaderNodeTexImage'); node.image = baked[role]
        if role == 'albedo': destination.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
        elif role == 'metallicRoughness':
            split = destination.node_tree.nodes.new('ShaderNodeSeparateColor'); split.mode = 'RGB'
            destination.node_tree.links.new(node.outputs['Color'], split.inputs['Color'])
            destination.node_tree.links.new(split.outputs['Green'], bsdf.inputs['Roughness'])
            destination.node_tree.links.new(split.outputs['Blue'], bsdf.inputs['Metallic'])
        else:
            normal_node = destination.node_tree.nodes.new('ShaderNodeNormalMap')
            destination.node_tree.links.new(node.outputs['Color'], normal_node.inputs['Color'])
            destination.node_tree.links.new(normal_node.outputs['Normal'], bsdf.inputs['Normal'])
    assert fingerprint(target) == before, 'Appearance bake changed geometry/source IDs/FOUR fields'
    assert rest == [(o.name, [(b.name, list(b.head_local), list(b.tail_local), [list(r) for r in b.matrix_local]) for b in o.data.bones])
                    for o in bpy.data.objects if o.type == 'ARMATURE'], 'Appearance bake changed original rest'
    uv_array = np.asarray([tuple(d.uv) for d in target.data.uv_layers.active.data])
    np.savez_compressed(out/'actual-coherent-uv-and-ray-witnesses.npz', cornerUV=uv_array, sourceRays=np.asarray(rays))
    bpy.data.objects.remove(appearance, do_unlink=True); bpy.data.objects.remove(cage, do_unlink=True)
    native = out/'actual-dense-detail.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(native))
    receipt = {'accepted': False, 'kind': 'Intended-final coherent compact atlas and fitted original dense detail derivative',
        'manifestSHA256': sha(manifest_path), 'recipeSHA256': sha(__file__), 'transportCoreSHA256': sha(HERE/'transport_core.py'),
        'native': {'path': str(native), 'sha256': sha(native)}, 'originalInputs': specification,
        'originalGeometrySourceIDsFOURAndRestExactlyUnchanged': True, 'maximumReferenceSupportDistanceM': float(distances.max()),
        'solverToActualNativeFloat32MaximumDeltaM': float(np.max(abs(input_current-current))),
        'maximumTransportedDenseResidualM': maximum_residual, 'minimumTransportedOrientationDot': minimum_orientation,
        'fittedDenseTriangles': len(original_face_ids), 'removedOriginalSourceFaceRows': len(removed),
        'explicitlyExcludedOriginalDenseFaceRows': int(len(dense['faces'])-len(selected_rows)),
        'actualRayWitnessCount': len(rays), 'coverage': coverage, 'maps': receipts, 'liningPolicy': lining,
        'lineageSHA256': sha(out/'dense-fitted-lineage.npz'), 'UVAndRayWitnessSHA256': sha(out/'actual-coherent-uv-and-ray-witnesses.npz'),
        'originalCompactUVLineageSHA256': sha(out/'original-compact-uv-lineage.npz'),
        'limits': ['Static fitted appearance derivative only; parent judges complete played outfit.',
                   'Finite ray witnesses and atlas-pixel support are not all-pose glove contact or self-intersection proof.',
                   'Original 4K masters stay intact; runtime derivatives/whole-scene 96 MiB and physical phone remain open.']}
    (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n'); print(json.dumps(receipt))

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 2
    main(Path(args[0]).resolve(), Path(args[1]).resolve())
