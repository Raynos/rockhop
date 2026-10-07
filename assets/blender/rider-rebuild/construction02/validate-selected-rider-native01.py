"""Independent read-only complete source check; never art acceptance or rendering."""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
FROZEN = ROOT / 'harness/out/rider-rebuild/construction01/rig04/anatomical-rig.blend'
FROZEN_SHA = 'e348548d974150cf089e5440b6d6b34846c7b6fbecd71b208df7b5fce81a0629'
DONOR = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb')
DONOR_SHA = 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
EXPECTED = {'RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L',
            'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
args = sys.argv[sys.argv.index('--') + 1:]
assert len(args) == 2
directory, output = [Path(p).resolve() for p in args]
assert not output.exists(), 'Preserve previous independent receipts'
assert sha(FROZEN) == FROZEN_SHA and sha(DONOR) == DONOR_SHA
bpy.ops.wm.open_mainfile(filepath=str(FROZEN))
original = bpy.data.objects['RiderBody']
original_body_points = [tuple(vertex.co) for vertex in original.data.vertices]
names = {group.index: group.name for group in original.vertex_groups}
lower = {i: (tuple(vertex.co), {names[g.group]: g.weight for g in vertex.groups if g.weight > 0})
         for i, vertex in enumerate(original.data.vertices) if vertex.co.z < 1.505 - 1e-5}
assert len(original.data.vertices) == 10582

bpy.ops.wm.open_mainfile(filepath=str(directory / 'rider-assembled.blend'))
rig = bpy.data.objects['RiderSkeleton']; body = bpy.data.objects['RiderBody']
meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj.parent == rig]
assert {obj.name for obj in meshes} == EXPECTED
assert rig.matrix_world.is_identity and len(rig.data.bones) == 75
assert not rig.constraints and all(not bone.constraints for bone in rig.pose.bones)
contract = json.loads((directory / 'rider-contract.json').read_text())
baseline = json.loads((ROOT / 'harness/out/rider-rebuild/construction01/combined04/rider-contract.json').read_text())
old = {bone['name']: bone for bone in baseline['nativeRest']['bones']}
for bone in contract['nativeRest']['bones']:
    if not bone['name'].startswith('SoleSocket.'):
        assert bone == old[bone['name']], ('Changed frozen rest', bone['name'])
    actual = rig.data.bones[bone['name']]
    assert tuple(actual.head_local) == tuple(bone['head']) and tuple(actual.tail_local) == tuple(bone['tail'])
    assert (actual.parent.name if actual.parent else None) == bone['parent']
    assert [list(row) for row in actual.matrix_local] == bone['matrix']

assembly = json.loads((directory / 'report.json').read_text())
canonical = assembly['wardrobe']['metrics']['canonicalFinalFields']
field_source_path = Path(canonical['preCanonicalFields']['path'])
assert sha(field_source_path) == canonical['preCanonicalFields']['sha256']
field_source = json.loads(field_source_path.read_text())
assert field_source['cutoff'] == .0001 and field_source['gridDenominator'] == 1 << 24
assert set(field_source['objects']) == EXPECTED
grid = field_source['gridDenominator']; minimum = math.floor(.0001 * grid) + 1
assert field_source['minimumRetainedGridCount'] == minimum
def expected_field(row):
    retained = sorted((name, weight) for name, weight in row if weight > .0001)
    total = sum(weight for _, weight in retained)
    exact = [weight / total * grid for _, weight in retained]
    counts = [max(minimum, math.floor(value)) for value in exact]
    residual = grid - sum(counts)
    if residual > 0:
        ranks = sorted(range(len(counts)), key=lambda i: (-(exact[i] - counts[i]), retained[i][0]))
        for index in ranks[:residual]: counts[index] += 1
    elif residual < 0:
        index = max(range(len(counts)), key=lambda i: (counts[i], retained[i][0]))
        counts[index] += residual
    assert sum(counts) == grid and all(value >= minimum for value in counts)
    return {name: count / grid for (name, _), count in zip(retained, counts)}
def geometry_sha(obj):
    result = hashlib.sha256()
    for vertex in obj.data.vertices: result.update(struct.pack('<3f', *vertex.co))
    for polygon in obj.data.polygons:
        result.update(struct.pack('<2I', len(polygon.vertices), polygon.material_index))
        result.update(struct.pack('<' + 'I' * len(polygon.vertices), *polygon.vertices))
    for normal in obj.data.corner_normals: result.update(struct.pack('<3f', *normal.vector))
    for layer in obj.data.uv_layers:
        for value in layer.data: result.update(struct.pack('<2f', *value.uv))
    source = obj.data.attributes.get('_SOURCE_VERTEX_ID')
    if source:
        for value in source.data: result.update(struct.pack('<i', value.value))
    return result.hexdigest()

field_errors, image_inventory, material_inventory, field_hashes = {}, {}, {}, {}
for obj in meshes:
    assert obj.matrix_world.is_identity and obj.matrix_parent_inverse.is_identity
    assert not obj.hide_render and not obj.hide_viewport and not obj.hide_get()
    armatures = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']
    assert len(armatures) == len(obj.modifiers) == 1 and armatures[0].object == rig
    assert not armatures[0].use_deform_preserve_volume
    names = {group.index: group.name for group in obj.vertex_groups}
    original_rows = field_source['objects'][obj.name]['preCanonicalNamedFields']
    assert len(original_rows) == len(obj.data.vertices)
    assert geometry_sha(obj) == field_source['objects'][obj.name]['geometryAndSourceIDSHA256']
    assert [value.value for value in obj.data.attributes['_NATIVE_ID'].data] == list(range(len(obj.data.vertices)))
    error = 0.; final_rows = []
    for index, vertex in enumerate(obj.data.vertices):
        fields = [(names[g.group], g.weight) for g in vertex.groups if g.weight > 0]
        assert 1 <= len(fields) <= 4 and all(name in rig.data.bones for name, _ in fields)
        assert all(weight > .0001 and weight * grid == int(weight * grid) for _, weight in fields)
        assert dict(fields) == expected_field(original_rows[index]), ('Wrong canonical operator', obj.name, index)
        error = max(error, abs(sum(weight for _, weight in fields) - 1))
        assert all(math.isfinite(value) for value in vertex.co)
        final_rows.append(sorted(fields))
    assert error == 0, (obj.name, error)
    field_errors[obj.name] = error
    field_hashes[obj.name] = hashlib.sha256(json.dumps(final_rows, separators=(',', ':')).encode()).hexdigest()
    assert obj.data.uv_layers.active is not None
    used = sorted({polygon.material_index for polygon in obj.data.polygons})
    material_inventory[obj.name] = []
    for index in used:
        mat = obj.data.materials[index]
        assert mat is not None and mat.use_nodes
        material_inventory[obj.name].append(mat.name)
        for node in mat.node_tree.nodes:
            if node.type != 'TEX_IMAGE' or node.image is None: continue
            image = node.image
            assert image.packed_file is not None, ('Unpacked selected map', obj.name, image.name)
            assert min(image.size) > 0
            image_inventory[image.name] = {'size': list(image.size), 'colorSpace': image.colorspace_settings.name,
                                          'packedSHA256': hashlib.sha256(image.packed_file.data).hexdigest()}
    if obj.name != 'RiderBody':
        assert any(node.type == 'TEX_IMAGE' and node.image for mat in obj.data.materials
                   for node in mat.node_tree.nodes), ('Missing selected PBR', obj.name)

source_ids = [item.value for item in body.data.attributes['_SOURCE_VERTEX_ID'].data]
native_ids = [item.value for item in body.data.attributes['_NATIVE_ID'].data]
assert native_ids == list(range(len(body.data.vertices)))
body_source_id_sha = hashlib.sha256(b''.join(struct.pack('<i', identity) for identity in source_ids)).hexdigest()
body_gltf_position_sha = hashlib.sha256(b''.join(struct.pack('<3f', vertex.co.x, vertex.co.z, -vertex.co.y)
                                               for vertex in body.data.vertices)).hexdigest()
names = {group.index: group.name for group in body.vertex_groups}
retained = {}
for identity, vertex in zip(source_ids, body.data.vertices):
    if vertex.co.z < 1.505 - 1e-5:
        assert identity in lower and identity not in retained
        original_fields = dict(field_source['objects']['RiderBody']['preCanonicalNamedFields'][vertex.index])
        assert (tuple(vertex.co), original_fields) == lower[identity], ('Changed original wearer before canonicalization', identity)
        retained[identity] = True
assert set(retained) == set(lower)
body.data.calc_loop_triangles()
edges, adjacent = {}, [set() for _ in body.data.vertices]
for polygon in body.data.polygons:
    vertices = list(polygon.vertices)
    for a, b in zip(vertices, vertices[1:] + vertices[:1]):
        edges.setdefault(tuple(sorted((a, b))), []).append((a, b))
        adjacent[a].add(b); adjacent[b].add(a)
assert all(len(rows) == 2 and rows[0] == rows[1][::-1] for rows in edges.values())
seen = {0}; pending = [0]
while pending:
    for vertex in adjacent[pending.pop()] - seen:
        seen.add(vertex); pending.append(vertex)
assert len(seen) == len(body.data.vertices)

# Verify protected actual donor corners against original raw arrays, not its report.
raw = DONOR.read_bytes(); size = struct.unpack_from('<I', raw, 12)[0]
gltf = json.loads(raw[20:20 + size]); binary = raw[28 + size:]
def accessor(index):
    item = gltf['accessors'][index]; view = gltf['bufferViews'][item['bufferView']]
    dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[item['componentType']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[item['type']]
    return np.ndarray((item['count'], width), dtype=dtype, buffer=binary,
                      offset=view.get('byteOffset', 0) + item.get('byteOffset', 0),
                      strides=(view.get('byteStride', np.dtype(dtype).itemsize * width), np.dtype(dtype).itemsize))
node = next(node for node in gltf['nodes'] if node.get('name') == 'textured')
face_ids = body.data.attributes['SelectedSourceFace']
faces = {identity.value: polygon for identity, polygon in zip(face_ids.data, body.data.polygons)
         if identity.value >= 0}
uv = body.data.uv_layers.active.data; normals = body.data.corner_normals
scale = 1.78 / 1.8225715160369873
maximum_position = maximum_uv = maximum_normal = 0.; protected = 0
source_point_ids = {}
for part, primitive in enumerate(gltf['meshes'][node['mesh']]['primitives']):
    for index, point in enumerate(accessor(primitive['attributes']['POSITION'])):
        source_point_ids.setdefault(tuple(float(value) for value in point), 1000000 + part * 100000 + index)
donor_points_by_id = {identity: Vector((-point[2] * scale, -(point[0] - .65) * scale, point[1] * scale))
                      for point, identity in source_point_ids.items()}
positive_ids = [identity for identity in source_ids if identity >= 0]
assert len(positive_ids) == len(set(positive_ids)), 'Derived points must not inherit duplicate original identities'
source_point_error = 0.
for identity, vertex in zip(source_ids, body.data.vertices):
    if identity == -1: continue
    expected = Vector(original_body_points[identity]) if 0 <= identity < 10582 else donor_points_by_id[identity]
    source_point_error = max(source_point_error, (vertex.co - expected).length)
assert source_point_error < 2e-7, 'Derived points must not masquerade as original source points'
for part, primitive in enumerate(gltf['meshes'][node['mesh']]['primitives']):
    xyz = accessor(primitive['attributes']['POSITION']); original_uv = accessor(primitive['attributes']['TEXCOORD_0'])
    original_normals = accessor(primitive['attributes']['NORMAL'])
    for index, triangle in enumerate(accessor(primitive['indices']).reshape(-1, 3)):
        if not all(xyz[int(i)][1] > 1.56 + 1e-5 for i in triangle): continue
        if len({tuple(xyz[int(i)]) for i in triangle}) < 3: continue
        polygon = faces[part * 1000000 + index]
        assert len(polygon.vertices) == 3
        for loop, original_index in zip(polygon.loop_indices, triangle):
            i = int(original_index); point = xyz[i]
            expected = Vector((-point[2] * scale, -(point[0] - .65) * scale, point[1] * scale))
            assert source_ids[body.data.loops[loop].vertex_index] == source_point_ids[tuple(float(value) for value in point)]
            expected_uv = Vector((float(original_uv[i][0]), 1 - float(original_uv[i][1])))
            normal = original_normals[i]; expected_normal = Vector((-normal[2], -normal[0], normal[1])).normalized()
            maximum_position = max(maximum_position, (body.data.vertices[body.data.loops[loop].vertex_index].co - expected).length)
            maximum_uv = max(maximum_uv, (uv[loop].uv - expected_uv).length)
            maximum_normal = max(maximum_normal, (normals[loop].vector - expected_normal).length)
        protected += 1
assert protected == 66364
assert maximum_position < 2e-7 and maximum_uv < 2e-7 and maximum_normal < 2e-6
face_report = assembly['wardrobe']['metrics']['selectedFace']
assert face_report['protectedSourcePointIDChanges'] == 0 and face_report['derivedCutSourceID'] == -1
cut_ids = [identity for identity, vertex in zip(source_ids, body.data.vertices)
           if abs(vertex.co.z - face_report['bodyCutNativeZ']) < 3e-6
           or abs(vertex.co.z - face_report['donorCutNativeZ']) < 3e-6]
assert sum(identity == -1 for identity in cut_ids) >= face_report['derivedCutVertexCount']
sole_errors = {}
for side in ('L', 'R'):
    boot = bpy.data.objects['ActualSelectedBoot.' + side]
    error = abs(rig.data.bones['SoleSocket.' + side].head_local.z - min(vertex.co.z for vertex in boot.data.vertices))
    assert error == 0
    sole_errors[side] = error
report = {'accepted': False, 'kind': 'independent complete selected native source readback',
          'native': {'path': str(directory / 'rider-assembled.blend'), 'sha256': sha(directory / 'rider-assembled.blend')},
          'validatorSHA256': sha(__file__), 'originalWearerSHA256': FROZEN_SHA, 'likedFaceSHA256': DONOR_SHA,
          'authorObjects': sorted(EXPECTED), 'jointCount': 75, 'nonSoleRestExactlyEqualToFrozen': True,
          'originalBelowNeckCutPositionsSourceIDsAndPreCanonicalFieldsExactlyRetained': len(retained),
          'nativeIDIsCurrentInventory': True,
          'bodySourceIDByNativeIDSHA256': body_source_id_sha, 'bodyGLTFPositionByNativeIDSHA256': body_gltf_position_sha,
          'bodyClosedOppositeWindingComponentCount': 1, 'protectedLikedFaceTriangles': protected,
          'protectedPositionMaximumErrorM': maximum_position, 'protectedUVMaximumError': maximum_uv,
          'protectedCornerNormalMaximumError': maximum_normal, 'normalizedFOURMaximumErrors': field_errors,
          'protectedLikedFacePointIDsExactlyRetained': True,
          'allPositiveSourcePointIDsUniqueAndAtOriginalCoordinates': True,
          'originalSourcePointMaximumPositionErrorM': source_point_error,
          'derivedCutVertexCount': face_report['derivedCutVertexCount'],
          'canonicalNamedFieldsByNativeIDSHA256': field_hashes,
          'canonicalOperatorMatchesPreFieldsExactly': True, 'skinFinishGeometryAndSourceIDsByteIdentical': True,
          'canonicalFinalFields': canonical,
          'materialsByAuthorObject': material_inventory, 'packedImages': image_inventory, 'soleUndersideSocketErrorM': sole_errors,
          'limits': ['Source transport only; parent must judge actual played outfit and calibrated contact.',
                     'Native closure and packed maps do not certify garment coverage, glove cavity or moving shading.']}
output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items() if key not in ('packedImages', 'materialsByAuthorObject')}))
