"""Read exact local geometry and fan data for two pinned body05 normal extremes."""
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
for key in ('source', 'intake', 'fields', 'out', 'summary'):
    parser.add_argument('--' + key, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, directory, fields_path, out, summary = [Path(getattr(args, key)).resolve() for key in ('source', 'intake', 'fields', 'out', 'summary')]
assert not out.exists() and not summary.exists()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(source) == '58c59f6e8b3e1a3c792e628040a137714fcf62f9ff8989578e2429a038e59661'
pins = {str(path): sha(path) for path in (source, fields_path, directory / 'report.json')}
fields = np.load(fields_path)
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Finish rig']
rig.animation_data_clear()
rig.hide_viewport = False
rig.hide_set(False)
names = [bone.name for bone in rig.data.bones]
assert names == fields['boneNames'].tolist() and len(names) == 51
for bone in rig.pose.bones:
    bone.rotation_mode = 'QUATERNION'
    for constraint in bone.constraints:
        constraint.mute = True

def normalized(vector):
    vector = np.asarray(vector, dtype=np.float64)
    length = np.linalg.norm(vector)
    return vector / length if length else vector

def newell(points):
    points = np.array(points, np.float32)
    total = np.zeros(3, np.float32)
    terms = []
    for i in range(len(points)):
        previous, current = points[i - 1], points[i]
        term = np.array([(previous[k] - current[k]) * (previous[(k + 1) % 3] + current[(k + 1) % 3]) for k in (1, 2, 0)], np.float32)
        total += term
        terms.append(term.tolist())
    return {'terms': terms, 'sum': total.tolist(), 'normal': normalized(total).tolist()}

def read(obj, region, corner, vid):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    assert mesh.loops[corner].vertex_index == vid
    incident = [polygon for polygon in mesh.polygons if vid in polygon.vertices]
    incident_by_id = {polygon.index: polygon for polygon in incident}
    edge_faces = {}
    for polygon in mesh.polygons:
        for loop in polygon.loop_indices:
            edge = mesh.loops[loop].edge_index
            if vid in mesh.edges[edge].vertices:
                edge_faces.setdefault(edge, []).append(polygon.index)
    sharp = mesh.attributes.get('sharp_edge')
    is_sharp = lambda edge: bool(sharp.data[edge].value) if sharp else False
    adjacency = {polygon.index: set() for polygon in incident}
    for edge, faces in edge_faces.items():
        if len(faces) == 2 and not is_sharp(edge) and all(incident_by_id[face].use_smooth for face in faces):
            adjacency[faces[0]].add(faces[1]); adjacency[faces[1]].add(faces[0])
    target = next(polygon for polygon in incident if corner in polygon.loop_indices)
    fan, stack = set(), [target.index]
    while stack:
        face = stack.pop()
        if face in fan:
            continue
        fan.add(face); stack.extend(adjacency[face] - fan)
    attr = mesh.attributes.get('custom_normal')
    packed = None
    if attr:
        assert attr.data_type == 'INT16_2D'
        packed = np.empty(len(attr.data) * 2, np.int32)
        attr.data.foreach_get('value', packed)
        packed = packed.reshape(-1, 2)
    polygons, automatic, custom_rows = [], np.zeros(3), []
    for polygon in incident:
        loops, ids = list(polygon.loop_indices), list(polygon.vertices)
        points = np.array([mesh.vertices[index].co[:] for index in ids])
        at = ids.index(vid)
        incoming = normalized(points[(at - 1) % len(points)] - points[at])
        outgoing = normalized(points[(at + 1) % len(points)] - points[at])
        angle = float(np.arccos(np.clip(incoming @ outgoing, -1, 1)))
        face_normal = np.array(mesh.polygon_normals[polygon.index].vector[:])
        if polygon.index in fan:
            automatic += face_normal * angle
            if packed is not None:
                custom_rows.append(packed[loops[at]])
        cross = np.cross(points[1] - points[0], points[2] - points[0])
        n = newell(points)
        polygons.append({'polygon': polygon.index, 'inTargetFan': polygon.index in fan,
                         'vertices': ids, 'corners': loops, 'localXYZ': points.tolist(),
                         'smooth': polygon.use_smooth, 'cornerAngleRadiansAtTarget': angle,
                         'faceNormalLocal': face_normal.tolist(), 'localCrossNormalFloat64': normalized(cross).tolist(),
                         'twiceAreaFloat64M2': float(np.linalg.norm(cross)), 'newellFloat32': n,
                         'newellToFaceVectorError': float(np.linalg.norm(np.array(n['normal']) - face_normal)),
                         'decodedNormalsLocal': [list(mesh.corner_normals[loop].vector) for loop in loops],
                         'packedCustomNormals': packed[loops].tolist() if packed is not None else None})
    ids = sorted({index for polygon in incident for index in polygon.vertices})
    result = {'targetPolygon': target.index, 'targetLocalNormal': list(mesh.corner_normals[corner].vector),
              'targetPacked': packed[corner].tolist() if packed is not None else None,
              'automaticFanAngleWeightedNormalLocal': normalized(automatic).tolist(),
              'targetFanPolygons': sorted(fan), 'averageFanPackedTruncated': np.trunc(np.mean(custom_rows, axis=0)).astype(int).tolist() if custom_rows else None,
              'incidentPolygons': polygons, 'incidentEdges': [{'edge': edge, 'vertices': list(mesh.edges[edge].vertices), 'sharp': is_sharp(edge), 'faces': faces} for edge, faces in edge_faces.items()],
              'vertexIDs': ids, 'localXYZ': [list(mesh.vertices[index].co) for index in ids],
              'worldRows': np.array(evaluated.matrix_world).tolist()}
    evaluated.to_mesh_clear()
    return result

records, compact = [], []
for region, index, corner, vid in [('head', 244, 206973, 43732), ('body', 128, 26810, 4572)]:
    sample_path = directory / f'sample-{index:04d}.json.gz'
    sample = json.loads(gzip.decompress(sample_path.read_bytes()))
    pins[str(sample_path)] = sha(sample_path)
    assert list(sample['poseBasisBlender']) == names
    objects = [bpy.data.objects[f'Finish {region} {field.upper()}'] for field in ('full', 'four')]
    for obj in objects:
        obj.hide_viewport = False; obj.hide_set(False); obj.animation_data_clear()
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    rests = {obj.name: read(obj, region, corner, vid) for obj in objects}
    for name, basis in sample['poseBasisBlender'].items():
        bone = rig.pose.bones[name]
        bone.location, bone.rotation_quaternion, bone.scale = basis['location'], basis['quaternionWXYZ'], basis['scale']
    bpy.context.view_layer.update()
    skin = np.array([rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted() for name in names])
    assert np.array_equal(skin, sample['skinNativeRows'])
    for field, obj in zip(('full', 'four'), objects):
        rest, moving = rests[obj.name], read(obj, region, corner, vid)
        assert rest['vertexIDs'] == moving['vertexIDs']
        ids = rest['vertexIDs']
        weights = np.zeros((len(ids), 51))
        memberships = {}
        for row, vertex in enumerate(ids):
            observed = {}
            for group in obj.data.vertices[vertex].groups:
                name = obj.vertex_groups[group.group].name
                if name in names and group.weight > 0:
                    observed[name] = group.weight; weights[row, names.index(name)] = group.weight
            memberships[str(vertex)] = observed
        sums = weights.sum(axis=1); weights /= sums[:, None]
        local_to_rig = np.linalg.inv(np.array(rig.matrix_world)) @ np.array(obj.matrix_world)
        rig_to_local = np.linalg.inv(local_to_rig)
        homogeneous = np.column_stack((rest['localXYZ'], np.ones(len(ids)))) @ local_to_rig.T
        predicted = np.einsum('vj,jab,vb->va', weights, skin, homogeneous) @ rig_to_local.T
        linear = (rig_to_local @ np.einsum('j,jab->ab', weights[ids.index(vid)], skin) @ local_to_rig)[:3, :3]
        predicted_normal = normalized(linear @ rest['targetLocalNormal'])
        actual_normal = np.array(moving['targetLocalNormal'])
        target_row = ids.index(vid)
        point_refs = fields[region + 'AttributeEdgeSources'][vid].tolist()
        corner_refs = fields[region + 'CornerAttributeEdgeSources'][corner].tolist()
        result = {'region': region, 'field': field, 'sample': index, 'corner': corner, 'vertex': vid,
                  'pointAncestry': point_refs, 'cornerAncestry': corner_refs,
                  'rawDeformMemberships': memberships, 'rawSumRange': [float(sums.min()), float(sums.max())],
                  'rest': rest, 'moving': moving, 'manualLocalXYZ': predicted[:, :3].tolist(),
                  'manualNativeMaximumLocalXYZErrorM': float(np.linalg.norm(predicted[:, :3] - moving['localXYZ'], axis=1).max()),
                  'targetInfluenceCount': int(np.count_nonzero(weights[target_row])),
                  'targetRigidSingleBone': bool(np.count_nonzero(weights[target_row]) == 1),
                  'predictedTargetLinearNormalLocal': predicted_normal.tolist(),
                  'linearNativeTargetNormalVectorError': float(np.linalg.norm(predicted_normal - actual_normal)),
                  'automaticFanToActualTargetNormalVectorError': float(np.linalg.norm(np.array(moving['automaticFanAngleWeightedNormalLocal']) - actual_normal)),
                  'savedNativeTargetNormalWorldVectorError': float(np.linalg.norm(actual_normal - sample['parts'][region][field]['normalWorldCorners'][corner]))}
        records.append(result)
        compact.append({key: result[key] for key in ('region', 'field', 'sample', 'corner', 'vertex', 'pointAncestry', 'cornerAncestry', 'targetInfluenceCount', 'targetRigidSingleBone', 'manualNativeMaximumLocalXYZErrorM', 'linearNativeTargetNormalVectorError', 'automaticFanToActualTargetNormalVectorError', 'savedNativeTargetNormalWorldVectorError')}
                           | {'restTargetPacked': rest['targetPacked'], 'movingTargetPacked': moving['targetPacked'], 'restFanPolygons': rest['targetFanPolygons'], 'movingFanPolygons': moving['targetFanPolygons'], 'movingMaximumNewellFaceError': max(polygon['newellToFaceVectorError'] for polygon in moving['incidentPolygons'])})
assert pins == {path: sha(path) for path in pins}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'status': 'UNACCEPTED_READ_ONLY_BODY05_LOCAL_NORMAL_EXTREMES', 'sourcePins': pins, 'readerSHA256': sha(__file__), 'exactSavedOwn51SkinRows': True, 'records': records}, indent=2) + '\n')
summary.parent.mkdir(parents=True, exist_ok=True)
summary.write_text(json.dumps({'status': 'UNACCEPTED_READ_ONLY_BODY05_LOCAL_NORMAL_EXTREMES', 'sourcePins': pins, 'readerSHA256': sha(__file__), 'rawWitness': str(out), 'rawWitnessSHA256': sha(out), 'rawWitnessBytes': out.stat().st_size, 'exactSavedOwn51SkinRows': True, 'records': compact, 'limits': ['Two selected worst current native/CPU formula corners only; no tolerance relaxed or broad exclusion.', 'Fan membership reconstructed from actual incident smooth faces and sharp edges; angle weighting uses float64 acos, not Blender approximate acos.', 'Custom packed values and native decoded normals retained; custom fan-space decoding/normal transport is not silently approximated as a parity pass.', 'No save/export/geometry/normal/weight/rig mutation, new motion, film, GPU, contact or art acceptance.']}, indent=2) + '\n')
print('BODY05_LOCAL_NORMAL_EXTREMES_READY', flush=True)
