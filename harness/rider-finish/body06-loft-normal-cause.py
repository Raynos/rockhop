"""Prepared array-only cause study of the frozen six-face loft neighborhood.

No native evaluation, pose generation, source mutation or normal rewriting.
Execute only after the parent checkpoints the preceding finding. All matrix
products use explicit finite einsum; no whole-head BLAS matmul is needed.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', required=True)
a = p.parse_args()
out = Path(a.out).resolve()
assert not out.exists()
root = Path(__file__).resolve().parents[2]
base = root / 'harness/out/rider-finish'
rt = root / 'docs/evidence/hero-remaster/finish-2026-10-05/runtime'
native_path = base / 'body06-intake01/report.json'
rest_path = base / 'body05-intake01/rest.json.gz'
sample_path = base / 'body06-intake01/sample-0244.json.gz'
fields_path = root / 'assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body06/authored-neck-fields.npz'
builder_path = root / 'assets/blender/hero-remaster/rider/finish-2026-10-05/construction/build_planar_neck.py'
metadata_path = rt / 'body06-normal-witness-metadata01.json'
sha = lambda x: hashlib.sha256(Path(x).read_bytes()).hexdigest()
pins = {str(x.relative_to(root)): sha(x) for x in (native_path, rest_path, sample_path, fields_path, builder_path, metadata_path)}
assert sha(fields_path) == 'ec307c63651b1b76cda75758572cce236987a0dc5c6d2543fd3e23492f9f626a'
assert sha(native_path) == '1d19d3d4abbaf27258b296ca0f4307d705f3c4ed4a0c1d4cc479020c5d6a39d4'
native = json.loads(native_path.read_text())
assert next(x for x in native['samples'] if x['path'] == sample_path.name)['sha256'] == sha(sample_path)
assert native['sourcePins'][str(rest_path)] == sha(rest_path)
rest = json.loads(gzip.decompress(rest_path.read_bytes()))
sample = json.loads(gzip.decompress(sample_path.read_bytes()))
f = np.load(fields_path)
target = 45084
corner = 196454
faces = f['headTriangles'].astype(int)
assert np.array_equal(faces, np.array(sample['parts']['head']['four']['faces']))
corner_ids = np.array(rest['parts']['head']['cornerVertices'], int)
assert np.array_equal(corner_ids.reshape(-1, 3), faces)
assert corner_ids[corner] == target
incidents = np.flatnonzero(np.any(faces == target, axis=1))
assert incidents.tolist() == [65484, 65485, 65486, 66317, 66318, 66319]
neighbors = np.unique(faces[incidents])
world = np.array(rest['parts']['head']['objectWorld'])
rig_world = np.array(rest['rigWorldRows'])
skin = np.array(sample['skinNativeRows'])

def finite(x):
    assert np.isfinite(x).all()
    return x

def product(*matrices):
    result = matrices[0]
    for matrix in matrices[1:]:
        result = finite(np.einsum('ab,bc->ac', result, matrix, optimize=False))
    return result

def point_transform(matrix, points):
    homogeneous = np.column_stack((points, np.ones(len(points))))
    return finite(np.einsum('ab,vb->va', matrix, homogeneous, optimize=False))[:, :3]

def unit(vector):
    length = np.linalg.norm(vector)
    assert np.isfinite(length) and length > 0
    return vector / length

def crosses(points):
    return finite(np.cross(points[1] - points[0], points[2] - points[0]))

rest_xyz = point_transform(world, f['headRestXYZ'][neighbors].astype(float))
actual_xyz = finite(np.array(sample['parts']['head']['four']['xyzWorld'])[neighbors])
rest_lookup = {int(v): rest_xyz[i] for i, v in enumerate(neighbors)}
actual_lookup = {int(v): actual_xyz[i] for i, v in enumerate(neighbors)}
world_skin = np.array([product(rig_world, matrix, np.linalg.inv(rig_world)) for matrix in skin])
raw = f['headFourWeights'][neighbors].astype(float)
weights = raw / raw.sum(axis=1)[:, None]
weight_lookup = {int(v): weights[i] for i, v in enumerate(neighbors)}
raw_lookup = {int(v): raw[i] for i, v in enumerate(neighbors)}
names = rest['jointOrder']
all_triangles = []
rest_angle_sum = np.zeros(3)
actual_angle_sum = np.zeros(3)
for tid in incidents:
    ids = faces[tid]
    points = np.array([rest_lookup[int(v)] for v in ids])
    actual = np.array([actual_lookup[int(v)] for v in ids])
    w = np.array([weight_lookup[int(v)] for v in ids])
    homogeneous = np.column_stack((points, np.ones(3)))
    transformed_by_joint = finite(np.einsum('jab,vb->vja', world_skin, homogeneous, optimize=False))[:, :, :3]
    predicted = finite(np.einsum('vj,vjk->vk', w, transformed_by_joint, optimize=False))
    mean = w.mean(axis=0)
    mean_affine = finite(np.einsum('j,jab->ab', mean, world_skin, optimize=False))
    frozen_edges = finite(np.einsum('ab,kb->ka', mean_affine[:3, :3], points[1:] - points[0], optimize=False))
    deviations = finite(np.einsum('vj,vjk->vk', w - mean, transformed_by_joint, optimize=False))
    gradient_edges = deviations[1:] - deviations[0]
    exact_edges = predicted[1:] - predicted[0]
    reconstructed_edges = frozen_edges + gradient_edges
    constant_cross = np.cross(frozen_edges[0], frozen_edges[1])
    mixed_cross = np.cross(frozen_edges[0], gradient_edges[1]) + np.cross(gradient_edges[0], frozen_edges[1])
    gradient_cross = np.cross(gradient_edges[0], gradient_edges[1])
    manual_cross, native_cross, rest_cross = crosses(predicted), crosses(actual), crosses(points)
    reconstructed_cross = constant_cross + mixed_cross + gradient_cross
    determinant = float(np.linalg.det(mean_affine[:3, :3]))
    which = int(np.flatnonzero(ids == target)[0])
    def angle_at(points):
        u = unit(points[(which + 1) % 3] - points[which])
        v = unit(points[(which + 2) % 3] - points[which])
        return float(np.arccos(np.clip(np.dot(u, v), -1, 1)))
    rest_angle_sum += angle_at(points) * unit(rest_cross)
    actual_angle_sum += angle_at(actual) * unit(native_cross)
    all_triangles.append({'triangle': int(tid), 'nativeVertexIDs': ids.tolist(),
        'restWorldXYZ': points.tolist(), 'actualWorldXYZ': actual.tolist(),
        'normalizedSkinRows': [{names[j]: float(value) for j, value in enumerate(row) if value} for row in w],
        'perJointVertexWeightRange': {names[j]: float(value) for j, value in enumerate(np.ptp(w, axis=0)) if value},
        'meanAffineLinearDeterminant': determinant,
        'restTrueCross': rest_cross.tolist(), 'actualTrueCross': native_cross.tolist(),
        'restArea2M2': float(np.linalg.norm(rest_cross)), 'actualArea2M2': float(np.linalg.norm(native_cross)),
        'constantMeanFieldEdges': frozen_edges.tolist(), 'weightGradientEdges': gradient_edges.tolist(),
        'actualManualEdges': exact_edges.tolist(),
        'edgeDecompositionMaximumResidualM': float(np.max(np.abs(exact_edges - reconstructed_edges))),
        'nativeManualVertexMaximumResidualM': float(np.linalg.norm(actual - predicted, axis=1).max()),
        'constantMeanFieldCross': constant_cross.tolist(), 'mixedGradientCross': mixed_cross.tolist(),
        'pureGradientCross': gradient_cross.tolist(),
        'crossDecompositionMaximumResidualM2': float(np.max(np.abs(manual_cross - reconstructed_cross))),
        'actualNativeToManualTrueNormalError': float(np.linalg.norm(unit(native_cross) - unit(manual_cross))),
        'actualNativeToFrozenMeanFieldTrueNormalDot': float(np.dot(unit(native_cross), unit(constant_cross))),
        'gradientCrossRelativeToConstantCross': float(np.linalg.norm(mixed_cross + gradient_cross) / np.linalg.norm(constant_cross))})

corner_rows = np.flatnonzero(corner_ids == target)
rest_decoded = np.array(rest['parts']['head']['cornerNormals'])[corner_rows]
actual_decoded = np.array(sample['parts']['head']['four']['normalWorldCorners'])[corner_rows]
rest_geometric_proxy = unit(rest_angle_sum)
actual_geometric_proxy = unit(actual_angle_sum)
actual_witness = np.array(sample['parts']['head']['four']['normalWorldCorners'])[corner]
scope = f['headCapRigid320NativeIDs']
result = {'status': 'UNACCEPTED_ARRAY_ONLY_VARIABLE_FIELD_GEOMETRY_AND_CORNER_NORMAL_CAUSE_STUDY',
          'recipeSHA256': sha(__file__), 'inputPins': pins, 'index': 244, 'nativeVertex': target, 'corner': corner,
          'allSixGeometricIncidentTriangles': all_triangles,
          'neighborPointLineageAndFields': [{'vertex': int(v), 'pointReference': f['headAttributeEdgeSources'][v].tolist(),
              'inRigid320': bool(np.isin(v, scope)), 'rawSemanticWeights': {names[j]: float(value) for j, value in enumerate(raw_lookup[int(v)]) if value}} for v in neighbors],
          'cornerProvenance': [{'corner': int(c), 'sourceReference': f['headCornerAttributeEdgeSources'][c].tolist(),
              'restDecodedLocalVector': rest_decoded[i].tolist(), 'actualDecodedWorldVector': actual_decoded[i].tolist()} for i, c in enumerate(corner_rows)],
          'allSixFaceGeometricAngleWeightedProxy': {'restWorld': rest_geometric_proxy.tolist(), 'actualWorld': actual_geometric_proxy.tolist(),
              'actualProxyToNativeWitnessVectorError': float(np.linalg.norm(actual_geometric_proxy - actual_witness)),
              'nativeFanPartitionVerified': False},
          'sourceEncodingProvenance': {'builder': str(builder_path.relative_to(root)),
              'builderMeaning': 'Generated loft source references−1. Desired decoded normals initially read from new geometric mesh before normals_split_custom_set. Protected source corners alone restore original INT16_2D data.',
              'actualPackedWitnessRowsCaptured': False, 'actualSharpEdgeAndSmoothFanPartitionCaptured': False,
              'exactCustomFanDecodeReconstruction': 'UNMEASURED; missing packed rows and actual partition'},
          'appropriateReference': 'Native oriented true triangle crosses are the actual current surface. Frozen mean per-triangle affine field is only an algebraic control used to isolate the exact weight-gradient contribution; head-rigid transport is not the reference for diagnosing a mixed chest/neck/head material fold.',
          'loftFoldCertificate': {'status': 'UNMEASURED', 'reason': 'Area and orientation at one pose plus constant-field controls do not prove a continuous-time orientation reversal. A negative dot against an arbitrary transported rigid normal is insufficient.'},
          'limits': ['No native job, new pose, save, shader, renderer, source rewrite, normal exclusion or tolerance relaxation.',
                     'Exact triangle edge decomposition uses normalized raw semantic fields and captured own51 skin matrices; actual native float32 geometry remains the numerical authority.',
                     'Six-face angle-weighted proxy is explicitly not a reconstructed native fan; even a small residual does not establish missing packed data.',
                     'Custom normal packing and post-set sharp-edge/fan partition are not available in this capture. Their exact interpretation remains open.',
                     'The previously captured whole-head moving-normal vector error remains a failure; this study cannot accept geometry, shading, art or release.']}
assert pins == {name: sha(root / name) for name in pins}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('BODY06_LOFT_CAUSE_READY', flush=True)
