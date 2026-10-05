"""Distinguish actual geometric fans from Blender's mixed custom face normals."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
source, out = Path(args.input), Path(args.out)
assert not out.exists()
raw = json.loads(source.read_text())
length = lambda value: math.sqrt(sum(x * x for x in value))
distance = lambda a, b: length([x - y for x, y in zip(a, b)])
unit = lambda value: [x / length(value) for x in value] if length(value) else value
f32 = lambda value: struct.unpack('f', struct.pack('f', value))[0]

def independent_newell(points):
    total = [0.0, 0.0, 0.0]
    for index in range(len(points)):
        previous, current = points[index - 1], points[index]
        term = [f32(f32(previous[k] - current[k]) * f32(previous[(k + 1) % 3] + current[(k + 1) % 3])) for k in (1, 2, 0)]
        total = [f32(a + b) for a, b in zip(total, term)]
    return total

implementation = Path('.tmp/user-agent3-normal80-mesh_normals.cc')
rna = Path('harness/out/rider-finish/rna_mesh-v5.2.1-normal-extremes.cc')
implementation_text, rna_text = implementation.read_text(), rna.read_text()
face_method = implementation_text[implementation_text.index('Span<float3> Mesh::face_normals() const'):implementation_text.index('Span<float3> Mesh::face_normals_true() const')]
assert 'custom.varray.type().is<short2>()' in face_method and 'mesh::mix_normals_corner_to_face' in face_method
rna_method = rna_text[rna_text.index('static void rna_Mesh_poly_normals_begin'):rna_text.index('static int rna_Mesh_poly_normals_length')]
assert 'mesh->face_normals()' in rna_method
records = []
for record in raw['records']:
    row = {key: record[key] for key in ('region', 'field', 'sample', 'corner', 'vertex', 'pointAncestry', 'cornerAncestry', 'targetInfluenceCount', 'targetRigidSingleBone', 'manualNativeMaximumLocalXYZErrorM', 'linearNativeTargetNormalVectorError', 'savedNativeTargetNormalWorldVectorError')}
    row['rawTargetWeights'] = record['rawDeformMemberships'][str(record['vertex'])]
    row['packedUnchanged'] = record['rest']['targetPacked'] == record['moving']['targetPacked']
    row['packedTarget'] = record['rest']['targetPacked']
    row['fanTopologyUnchanged'] = record['rest']['targetFanPolygons'] == record['moving']['targetFanPolygons']
    row['states'] = {}
    for state in ('rest', 'moving'):
        data = record[state]
        fan = [polygon for polygon in data['incidentPolygons'] if polygon['inTargetFan']]
        geometric_sum = [sum(polygon['localCrossNormalFloat64'][k] * polygon['cornerAngleRadiansAtTarget'] for polygon in fan) for k in range(3)]
        newell_sum = [sum(polygon['newellFloat32']['normal'][k] * polygon['cornerAngleRadiansAtTarget'] for polygon in fan) for k in range(3)]
        mixed_errors = []
        for polygon in data['incidentPolygons']:
            assert independent_newell(polygon['localXYZ']) == polygon['newellFloat32']['sum']
            mixed = unit([sum(vector[k] for vector in polygon['decodedNormalsLocal']) for k in range(3)])
            mixed_errors.append(distance(mixed, polygon['faceNormalLocal']))
        row['states'][state] = {'nativeTargetDecodedNormalLocal': data['targetLocalNormal'],
                                'trueGeometryAngleWeightedFanNormalFloat64': unit(geometric_sum),
                                'newellGeometryAngleWeightedFanNormalFloat64': unit(newell_sum),
                                'mixedRNAFaceToNormalizedDecodedCornerMeanMaximumVectorError': max(mixed_errors),
                                'trueNewellToDirectCrossMaximumVectorError': max(distance(polygon['newellFloat32']['normal'], polygon['localCrossNormalFloat64']) for polygon in data['incidentPolygons']),
                                'fanPolygons': [{'polygon': polygon['polygon'], 'trueDirectCrossNormalLocal': polygon['localCrossNormalFloat64'], 'trueArea2M2': polygon['twiceAreaFloat64M2'], 'RNAFaceMixedNormalLocal': polygon['faceNormalLocal']} for polygon in fan]}
        assert max(mixed_errors) < 2e-7
    rest_target = next(polygon for polygon in record['rest']['incidentPolygons'] if polygon['polygon'] == record['rest']['targetPolygon'])
    moving_target = next(polygon for polygon in record['moving']['incidentPolygons'] if polygon['polygon'] == record['moving']['targetPolygon'])
    row['targetTrueFaceNormalRestMovingDot'] = sum(a * b for a, b in zip(rest_target['localCrossNormalFloat64'], moving_target['localCrossNormalFloat64']))
    row['trueNewellPrecisionDoesNotExplainNearlyTwoVectorError'] = max(row['states'][state]['trueNewellToDirectCrossMaximumVectorError'] for state in ('rest', 'moving')) < .002
    assert row['packedUnchanged'] and row['fanTopologyUnchanged']
    records.append(row)
report = {'status': 'UNACCEPTED_BODY05_CUSTOM_FAN_NORMAL_AND_GEOMETRIC_FOLD_DIAGNOSIS',
          'inputPins': {'rawWitness': str(source), 'rawWitnessSHA256': hashlib.sha256(source.read_bytes()).hexdigest(), 'rawReaderSHA256Executed': raw['readerSHA256']},
          'sourcePins': raw['sourcePins'], 'algebraRecipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'exactSavedOwn51SkinRows': raw['exactSavedOwn51SkinRows'], 'records': records,
          'primaryImplementation': [{'version': 'Blender5.2.1', 'url': 'https://raw.githubusercontent.com/blender/blender/v5.2.1/source/blender/blenkernel/intern/mesh_normals.cc', 'localPath': str(implementation), 'downloadSHA256': hashlib.sha256(implementation.read_bytes()).hexdigest(), 'functions': ['Mesh::face_normals', 'Mesh::face_normals_true', 'mix_normals_corner_to_face', 'corner_fan_space_define', 'corner_space_custom_data_to_normal'], 'claim': 'CORNER short2 custom_normal routes face_normals to normalized mixed decoded corner vectors; true geometric normals are a separate cache; custom decode uses a geometry fan frame.'}, {'version': 'Blender5.2.1', 'url': 'https://raw.githubusercontent.com/blender/blender/v5.2.1/source/blender/makesrna/intern/rna_mesh.cc', 'localPath': str(rna), 'downloadSHA256': hashlib.sha256(rna.read_bytes()).hexdigest(), 'functions': ['rna_Mesh_poly_normals_begin', 'rna_Mesh_poly_normals_lookup_int'], 'claim': 'polygon_normals RNA collection calls mesh->face_normals(), including custom mixing branch.'}],
          'independentFloat32NewellMethod': 'Every recorded face localXYZ uses exact polygon vertex order, closed previous-last/current-first cycle, explicit Float32 subtraction/addition/multiplication/accumulation via struct. Every sum equals the native reader NumPy Float32 sum exactly.',
          'finding': 'Both current extreme corners are nonrigid with nonzero unchanged packed custom normals and stable fan topology. Their geometry deforms and true face directions change substantially. New head target triangle68991 flips true orientation+Z to-Z under turn; the original body reach fan also changes. Native custom vectors are fan-relative evaluated outputs and do not follow the linear blended-vector hypothesis at these witnesses.',
          'readerSemanticCorrection': 'The raw reader faceNormalLocal is Blender polygon_normals, experimentally equal to normalized means of decoded custom corner normals. It is not the true geometric face normal with these packed values. Its automaticFanAngleWeightedNormalLocal and newellToFaceVectorError fields are invalid geometric-fan/cancellation comparisons and must not be used. This algebra derives geometric fans from recorded localXYZ direct crosses/Newell separately.',
          'limits': ['True geometric fan is reconstructed with float64 angle weighting; Blender approximate acos/custom fan-space basis decoding is not fully reproduced.',
                     'An observed face orientation change is a finite deformation witness, not a continuous self-contact or signed-volume certificate.',
                     'True float32 Newell/direct-cross error is small relative to near2 failure here; the prior rigid packedzero turn244 precision cause is not a general explanation.',
                     'No normal parity pass, exclusion, relaxed tolerance, source mutation, GLB/GPU, played-art, contact or device acceptance.']}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
print('BODY05_NORMAL_SEMANTICS_AND_GEOMETRIC_FOLD_READY')
