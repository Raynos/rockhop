"""Read-only source ray and native-ID proof for the actual proximal cloth pair.

Chunked NumPy over the exact selected GLB; no Blender and no model mutation.
The arm-axis rays are evidence of paired sheets, not global wall ownership.
"""
import json
import mmap
import runpy
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'check_solid.py'))
checked, pin = h['checked'], h['pin']
prior = json.loads(checked(h['CONFIG']['pins']['priorInputs']).read_text())
opened = []


def glb(row):
    file = checked(row).open('rb')
    data = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ); opened.extend((file, data))
    size = struct.unpack_from('<I', data, 12)[0]; doc = json.loads(data[20:20+size])
    def accessor(index):
        r = doc['accessors'][index]; v = doc['bufferViews'][r['bufferView']]
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[r['componentType']]
        count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[r['type']]
        item = np.dtype(dtype).itemsize
        return np.ndarray((r['count'], count), dtype=dtype, buffer=data,
            offset=28+size+v.get('byteOffset', 0)+r.get('byteOffset', 0),
            strides=(v.get('byteStride', item*count), item))
    return doc, accessor


def intersections(vertices, faces, point, direction, omitted):
    hits = []
    for start in range(0, len(faces), 32768):
        triangles = vertices[faces[start:start+32768]]
        e1, e2 = triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]
        cross = np.cross(direction, e2); det = np.einsum('ij,ij->i', e1, cross)
        valid = abs(det) > 1e-14; inverse = 1/np.where(valid, det, 1.)
        offset = point-triangles[:, 0]; u = np.einsum('ij,ij->i', offset, cross)*inverse
        q = np.cross(offset, e1); v = q@direction*inverse
        distance = np.einsum('ij,ij->i', e2, q)*inverse
        ids = np.flatnonzero(valid & (u >= 0) & (v >= 0) & (u+v <= 1) & (distance > 1e-7))
        for i in ids[start+ids != omitted]:
            normal = np.cross(e1[i], e2[i]); normal /= np.linalg.norm(normal)
            hits.append({'sourceFaceId': int(start+i), 'distanceSourceUnits': float(distance[i]),
                'normalDotRay': float(normal@direction),
                'sourceBarycentric': [float(1-u[i]-v[i]), float(u[i]), float(v[i])]})
    return sorted(hits, key=lambda row: row['distanceSourceUnits'])


def main():
    assert len(sys.argv) == 2, 'check_source_pair.py OUTPUT_JSON'
    output = Path(sys.argv[1]).resolve()
    assert not output.exists() and output.is_relative_to(h['h']['ROOT'])
    diagnostic = json.loads(h['DIAGNOSTIC_PATH'].read_text()); witness = diagnostic['globalMinimum']
    source, sa = glb(prior['originalHoodie']); primitive = source['meshes'][0]['primitives'][0]
    vertices = sa(primitive['attributes']['POSITION'])[:, [0, 2, 1]].astype(float); vertices[:, 1] *= -1
    faces = sa(primitive['indices']).reshape(-1, 3); fid = witness['originalNativeFaceId']
    assert faces[fid].tolist() == witness['clothVertices']
    assert vertices[faces[fid]].tolist() == witness['sourcePoints']
    triangle = vertices[faces[fid]]; point = triangle.mean(0)
    normal = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0]); normal /= np.linalg.norm(normal)
    controls = json.loads(checked(prior['hoodieSourceFrames']).read_text())
    affine = controls['sourceDisplayAffine']; scale = np.asarray(affine['scale']); translation = np.asarray(affine['translation'])
    bone = next(b for b in controls['authoringBones'] if b['name'] == 'AUTHOR_UpperArm.L')
    head = (np.asarray(bone['sourceHead'])-translation)/scale
    tail = (np.asarray(bone['sourceTail'])-translation)/scale
    axis = tail-head; axis /= np.linalg.norm(axis)
    axis_point = head+np.dot(point-head, axis)*axis
    radial = point-axis_point; radial /= np.linalg.norm(radial)
    rays = {}
    for label, direction in (('normal', normal), ('opposedNormal', -normal),
                             ('awayArmAxis', radial), ('towardArmAxis', -radial)):
        hits = intersections(vertices, faces, point, direction, fid)
        rays[label] = {'sourceDirection': direction.tolist(), 'positiveHitCount': len(hits), 'firstHits': hits[:6]}
    paired = rays['awayArmAxis']['firstHits'][0]['sourceFaceId']
    assert rays['awayArmAxis']['firstHits'][0]['normalDotRay'] > 0 and normal@radial < 0
    engine, ea = glb(prior['sourceGLB'])
    node = next(n for n in engine['nodes'] if n.get('name') == 'RiderHoodie')
    assert not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale'))
    primitive = engine['meshes'][node['mesh']]['primitives'][0]
    ids = ea(primitive['attributes']['_NATIVE_ID']).ravel().astype(int)
    world = ea(primitive['attributes']['POSITION'])[:, [0, 2, 1]].astype(float); world[:, 1] *= -1
    body = np.load(checked(h['ACTUAL'])); key = 'RiderBody__FullAnatomyReference'; reports = []
    for face_id in (fid, paired):
        points = []
        for native_id in faces[face_id]:
            copies = world[ids == native_id]; assert len(copies) and np.all(copies == copies[0])
            points.append(copies[0])
        center = np.mean(points, axis=0)
        if face_id == fid: assert center.tolist() == witness['worldPoint']
        solid = h['solid_witness'](body[key+'_basis'].astype(float), body[key+'_triangles'], center,
                                   witness['nearestFullReference']['fullReferenceTriangleId'])
        assert abs(solid['solidAngleWinding']-1) < 1e-10
        reports.append({'sourceFaceId': face_id, 'nativeIds': faces[face_id].tolist(),
            'nativePoints': np.asarray(points).tolist(), 'centroid': center.tolist(),
            'solidAngleWinding': solid['solidAngleWinding'],
            'exhaustiveUnsignedBodyDistanceM': solid['exhaustiveUnsignedDistanceM'],
            'nearestFullReferenceFaceId': solid['exhaustiveNearestTriangleId']})
    result = {'status': 'BOTH_ACTUAL_PROXIMAL_SOURCE_SHEETS_INSIDE_WEARER', 'acceptedArt': False,
        'recipe': pin(__file__), 'solidHelper': pin(HERE/'check_solid.py'),
        'diagnostic': pin(h['DIAGNOSTIC_PATH']), 'sources': {k: prior[k] for k in
            ('originalHoodie', 'hoodieSourceFrames', 'sourceGLB')}, 'fullReference': h['ACTUAL'],
        'sourceFaceId': fid, 'sourceEdgeLengths': np.linalg.norm(triangle-np.roll(triangle, 1, axis=0), axis=1).tolist(),
        'sourceNormal': normal.tolist(), 'sourceNormalDotAwayArmAxis': float(normal@radial),
        'rays': rays, 'actualNativeSheetFaces': reports,
        'limits': ['Rays establish this local cavity/paired-sheet relationship, not global inner/outer face ownership.',
            'Both source sheets penetrate actual body; removing only the inward sheet cannot enclose the wearer.',
            'No geometry, source correspondence, target, tolerance or support changes.']}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': pin(output), 'status': result['status']}))


if __name__ == '__main__': main()
