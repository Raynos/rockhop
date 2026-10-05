"""Interpret the already captured whole-head maximum; no native job or save."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[2]
runtime = root / 'docs/evidence/hero-remaster/finish-2026-10-05/runtime'
out = runtime / 'body06-normal-witness-metadata01.json'
assert not out.exists()
intake = root / 'harness/out/rider-finish/body06-intake01'
native_path = intake / 'report.json'
native = json.loads(native_path.read_text())
worst_sample = max(native['records'], key=lambda x: x['parts']['head']['four']['maximumCPUFormulaNativeCornerNormalError'])
row = worst_sample['parts']['head']['four']
pin = next(x for x in native['samples'] if x['path'] == 'sample-%04d.json.gz' % worst_sample['index'])
sample_path = intake / pin['path']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(sample_path) == pin['sha256']
sample = json.loads(gzip.decompress(sample_path.read_bytes()))
old_path = root / 'harness/out/rider-finish/body05-intake01/rest.json.gz'
rest = json.loads(gzip.decompress(old_path.read_bytes()))
fields_path = root / 'assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body06/authored-neck-fields.npz'
f0_path = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/foundation-source.npz'
f, f0 = np.load(fields_path), np.load(f0_path)
corner, vertex = row['worstCorner'], row['worstVertex']
faces = np.array(sample['parts']['head']['four']['faces'], int)
assert np.array_equal(faces, f['headTriangles'])
assert np.array_equal(np.array(rest['parts']['head']['cornerVertices']).reshape(-1, 3), faces)
triangle = corner // 3
assert faces[triangle, corner % 3] == vertex
xyz = np.array(sample['parts']['head']['four']['xyzWorld'])
normals = np.array(sample['parts']['head']['four']['normalWorldCorners'])
assert np.array_equal(normals[corner], np.array(row['actualWorldNormal']))
raw = f['headFourWeights'][vertex].astype(float)
weights = raw / raw.sum()
rig_world = np.array(rest['rigWorldRows'])
world = np.array(rest['parts']['head']['objectWorld'])
to_rig = np.linalg.inv(rig_world) @ world
skin = np.array(sample['skinNativeRows'])
linear = (np.linalg.inv(to_rig) @ np.einsum('j,jab->ab', weights, skin) @ to_rig)[:3, :3]
predicted = linear @ np.array(rest['parts']['head']['cornerNormals'][corner])
predicted = predicted @ np.linalg.inv(world[:3, :3])
predicted /= np.linalg.norm(predicted)
assert np.max(np.abs(predicted - row['predictedWorldNormal'])) < 2e-15
rest_world = (np.c_[f['headRestXYZ'], np.ones(len(f['headRestXYZ']))] @ world.T)[:, :3]
head = rest['jointOrder'].index('head')
head_world = rig_world @ skin[head] @ np.linalg.inv(rig_world)
incidents = np.flatnonzero(np.any(faces == vertex, axis=1))
fan = []
for tid in incidents:
    old, moved = rest_world[faces[tid]], xyz[faces[tid]]
    rest_cross = np.cross(old[1] - old[0], old[2] - old[0])
    moving_cross = np.cross(moved[1] - moved[0], moved[2] - moved[0])
    transported = rest_cross @ np.linalg.inv(head_world[:3, :3])
    fan.append({'triangle': int(tid), 'nativeVertexIDs': faces[tid].tolist(),
                'sourcePolygon': int(f['headTriangleSourcePolygonIDs'][tid]),
                'restWorldXYZ': old.tolist(), 'actualWorldXYZ': moved.tolist(),
                'restTrueWorldCross': rest_cross.tolist(), 'actualTrueWorldCross': moving_cross.tolist(),
                'restArea2M2': float(np.linalg.norm(rest_cross)), 'actualArea2M2': float(np.linalg.norm(moving_cross)),
                'dotToTransportedHeadReference': float(np.dot(moving_cross, transported) / (np.linalg.norm(moving_cross) * np.linalg.norm(transported)))})
cap_ids = np.arange(68704, 69005)
scope = f['headCapRigid320NativeIDs']
face_scope = np.isin(faces, scope)
lining_ids = np.flatnonzero(face_scope.any(axis=1) & ~face_scope.all(axis=1))
assert len(lining_ids) == 459
result = {'status': 'UNACCEPTED_SAME_CAPTURE_WHOLE_HEAD_NORMAL_MAXIMUM_METADATA',
          'recipeSHA256': sha(__file__), 'inputPins': {str(p.relative_to(root)): sha(p) for p in (native_path, sample_path, old_path, fields_path, f0_path)},
          'index': sample['index'], 'case': sample['case'], 'field': 'four; native head FULL fields identical',
          'corner': corner, 'nativeVertex': vertex, 'triangle': triangle,
          'sourcePointReference': f['headAttributeEdgeSources'][vertex].tolist(),
          'sourceCornerReference': f['headCornerAttributeEdgeSources'][corner].tolist(),
          'sourcePolygonReference': int(f['headTriangleSourcePolygonIDs'][triangle]),
          'originalSource43707Vertex': vertex < 43707, 'derivedLoftVertex': vertex >= 43707,
          'F0ProtectedOriginalVertex': bool(np.isin(vertex, f0['headProtectedIDs'])),
          'F0EditableOriginalVertex': bool(np.isin(vertex, f0['headEditableIDs'])),
          'vertexInRigid320': bool(np.isin(vertex, scope)),
          'triangleInCap301': bool(np.isin(triangle, cap_ids)), 'triangleInAffectedLining459': bool(np.isin(triangle, lining_ids)),
          'semanticRawSkinRow': {rest['jointOrder'][i]: float(w) for i, w in enumerate(raw) if w},
          'rawWeightSum': float(raw.sum()), 'head1': bool(raw[head] == 1 and np.count_nonzero(raw) == 1),
          'restLocalXYZ': f['headRestXYZ'][vertex].tolist(), 'actualWorldXYZ': xyz[vertex].tolist(),
          'predictedWorldNormal': predicted.tolist(), 'actualWorldNormal': normals[corner].tolist(),
          'normalVectorError': float(np.linalg.norm(predicted - normals[corner])),
          'allGeometricIncidentTriangles': fan,
          'stalePriorBody02Corner183498LabelRejected': {'currentBody06Corner': 183498, 'currentNativeVertex': int(np.array(rest['parts']['head']['cornerVertices'])[183498]),
              'meaning': 'Recorded actual vector is valid, but the prior protected vertex26 witness does not transfer through changed topology.'},
          'limits': ['Only existing captured arrays interpreted; no native job, pose, save, export, shader or tolerance change.',
                     'All six geometric incident triangle crosses are actual vertex geometry. They are not decoded custom corner-normal fan spaces or RNA polygon normals.',
                     'Head reference transport is a diagnostic direction for this mixed chest/neck/head loft row; its sign is not a general physical fold certificate.',
                     'Derived loft has source point/corner/polygon reference -1; F0 original protection/editability sets do not assign it an original-source identity.',
                     'Packed INT16_2D values for this new whole-head maximum were not captured; immutable rest packed data were independently preserved.',
                     'Whole-head moving-normal parity remains failed; cap and finite-contact progress do not accept the rider.']}
out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('BODY06_WHOLE_HEAD_WITNESS', vertex, corner, result['normalVectorError'], flush=True)
