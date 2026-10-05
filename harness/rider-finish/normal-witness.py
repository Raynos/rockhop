"""Read one saved moving-normal witness without saving or exporting Blender data."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Matrix

parser = argparse.ArgumentParser(description=__doc__)
for key in ('source', 'manifest', 'sample', 'out'):
    parser.add_argument('--' + key, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
paths = {key: Path(getattr(args, key)).resolve() for key in ('source', 'manifest', 'sample')}
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
pins = {str(path): sha(path) for path in paths.values()}
manifest = json.loads(paths['manifest'].read_text())
sample = json.loads(gzip.open(paths['sample'], 'rt').read())
assert pins[str(paths['source'])] == manifest['sourceSHA256']
assert sample['index'] == 244
out = Path(args.out).resolve()
assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(paths['source']))
rig = bpy.data.objects[manifest['rigName']]
rig.animation_data_clear()
rig.hide_viewport = False
rig.hide_set(False)
names = [bone.name for bone in rig.data.bones]
assert len(names) == 51
for bone in rig.pose.bones:
    for constraint in bone.constraints:
        constraint.mute = True
    bone.rotation_mode = 'QUATERNION'
    bone.matrix_basis = Matrix.Identity(4)

def unit(vector):
    value = np.asarray(vector, dtype=np.float64)
    return value / np.linalg.norm(value)

def cross_report(xyz):
    cross = np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])
    edges = [np.linalg.norm(xyz[(i + 1) % 3] - xyz[i]) for i in range(3)]
    return {'cross': cross.tolist(), 'normal': unit(cross).tolist(),
            'twiceAreaM2': float(np.linalg.norm(cross)),
            'minimumAltitudeM': float(np.linalg.norm(cross) / max(edges))}

def read(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    triangle = mesh.loop_triangles[61196]
    assert list(triangle.vertices) == [26, 27, 28]
    assert list(triangle.loops) == [183498, 183499, 183500]
    polygon = mesh.polygons[triangle.polygon_index]
    xyz = np.array([mesh.vertices[v].co[:] for v in triangle.vertices])
    corner = np.array([mesh.corner_normals[i].vector[:] for i in triangle.loops])
    result = {'localXYZ': xyz.tolist(), 'localCrossFloat64': cross_report(xyz),
              'localCrossFloat32': cross_report(xyz.astype(np.float32)),
              'faceNormalLocal': list(mesh.polygon_normals[polygon.index].vector),
              'cornerNormalsLocal': corner.tolist(), 'triangleVertices': list(triangle.vertices),
              'triangleCorners': list(triangle.loops), 'polygon': polygon.index,
              'polygonCorners': list(polygon.loop_indices), 'smooth': polygon.use_smooth,
              'worldRows': np.array(evaluated.matrix_world).tolist()}
    attr = mesh.attributes.get('custom_normal')
    if attr:
        assert attr.data_type == 'INT16_2D' and attr.domain == 'CORNER'
        packed = np.empty(len(attr.data) * 2, dtype=np.int32)
        attr.data.foreach_get('value', packed)
        result['packedCustomNormals'] = packed.reshape(-1, 2)[list(triangle.loops)].tolist()
    else:
        result['packedCustomNormals'] = None
    evaluated.to_mesh_clear()
    return result

head = next(pair for pair in manifest['pairs'] if pair['region'] == 'head')
objects = [bpy.data.objects[head[field]] for field in ('full', 'four')]
for obj in objects:
    obj.hide_viewport = False
    obj.hide_set(False)
    obj.animation_data_clear()
bpy.context.view_layer.update()
rests = {obj.name: read(obj) for obj in objects}
for name, basis in sample['poseBasisBlender'].items():
    bone = rig.pose.bones[name]
    bone.location = basis['location']
    bone.rotation_quaternion = basis['quaternionWXYZ']
    bone.scale = basis['scale']
bpy.context.view_layer.update()
skin = np.array([rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted()
                 for name in names])
assert np.array_equal(skin, np.array(sample['skinNativeRows']))
records = {}
for field, obj in zip(('full', 'four'), objects):
    rest, moving = rests[obj.name], read(obj)
    xyz = np.array(rest['localXYZ'])
    weights = np.zeros((3, 51))
    memberships = []
    for row, vid in enumerate((26, 27, 28)):
        observed = {}
        for group in obj.data.vertices[vid].groups:
            name = obj.vertex_groups[group.group].name
            if name in names and group.weight > 0:
                weights[row, names.index(name)] = group.weight
                observed[name] = group.weight
        memberships.append(observed)
    weights /= weights.sum(axis=1)[:, None]
    local_to_rig = np.linalg.inv(np.array(rig.matrix_world)) @ np.array(obj.matrix_world)
    rig_to_local = np.linalg.inv(local_to_rig)
    homogeneous = np.column_stack((xyz, np.ones(3))) @ local_to_rig.T
    predicted = np.einsum('vj,jab,vb->va', weights, skin, homogeneous) @ rig_to_local.T
    predicted = predicted[:, :3]
    linear = (rig_to_local @ skin[names.index('head')] @ local_to_rig)[:3, :3]
    rest_normals = np.array(rest['cornerNormalsLocal'])
    linear_normals = np.array([unit(linear @ normal) for normal in rest_normals])
    inverse_normals = np.array([unit(np.linalg.inv(linear).T @ normal) for normal in rest_normals])
    actual_normals = np.array(moving['cornerNormalsLocal'])
    world = np.column_stack((np.array(moving['localXYZ']), np.ones(3))) @ np.array(moving['worldRows']).T
    saved_world = np.array(sample['parts']['head'][field]['xyzWorld'])[26:29]
    records[field] = {'object': obj.name, 'rest': rest, 'moving': moving,
                      'rawDeformMemberships': memberships, 'manualLocalXYZ': predicted.tolist(),
                      'manualCrossFloat64': cross_report(predicted),
                      'maximumManualNativeLocalPositionErrorM': float(np.linalg.norm(predicted - moving['localXYZ'], axis=1).max()),
                      'savedSnapshotWorldXYZMaximumErrorM': float(np.linalg.norm(world[:, :3] - saved_world, axis=1).max()),
                      'linearNormalsLocal': linear_normals.tolist(), 'inverseTransposeNormalsLocal': inverse_normals.tolist(),
                      'maximumLinearNormalVectorError': float(np.linalg.norm(linear_normals - actual_normals, axis=1).max()),
                      'maximumInverseTransposeNormalVectorError': float(np.linalg.norm(inverse_normals - actual_normals, axis=1).max()),
                      'movingFaceToCrossVectorError': float(np.linalg.norm(np.array(moving['faceNormalLocal']) - moving['localCrossFloat32']['normal'])),
                      'movingCornerToFaceMaximumVectorError': float(np.linalg.norm(actual_normals - moving['faceNormalLocal'], axis=1).max())}
assert pins == {path: sha(path) for path in pins}
report = {'status': 'UNACCEPTED_READ_ONLY_EXACT_TURN244_NORMAL_WITNESS',
          'sourcePins': pins, 'readerSHA256': sha(__file__), 'blender': bpy.app.version_string,
          'sampleIdentity': 244, 'case': sample['case'], 'phase': sample['phase'],
          'sourceNativeVertex': 26, 'sourceNativeCorner': 183498, 'originalSourceCorner': 183453,
          'exactSavedSkinRowsReplayed': True, 'sourceBytesUnchanged': True, 'records': records,
          'limits': ['One rigid head triangle witness only; maximum whole-head/body normal failures remain unresolved.',
                     'Local mesh evaluation and CPU algebra; no GPU, engine, contact, art or device acceptance.',
                     'No native save, GLB export, new motion generation, render or movie.']}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
print('EXACT_NORMAL_WITNESS_READY', out, flush=True)
