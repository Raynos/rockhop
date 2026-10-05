"""Check actual native body05 fields, canonical raw FULL ancestry and moving normals."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
for key in ('intake', 'fields', 'full-source', 'foundation', 'out'):
    parser.add_argument('--' + key, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
directory, fields_path, full_path, foundation_path, out = [Path(getattr(args, key.replace('-', '_'))).resolve()
                                                        for key in ('intake', 'fields', 'full-source', 'foundation', 'out')]
assert not out.exists()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
report_path = directory / 'report.json'
native = json.loads(report_path.read_text())
rest_path = directory / native['rest']['path']
assert sha(rest_path) == native['rest']['sha256']
rest = json.loads(gzip.decompress(rest_path.read_bytes()))
fields, full, foundation = [np.load(path) for path in (fields_path, full_path, foundation_path)]
assert sha(full_path) == 'deb04faa6a5ca85ca9617cb963d84d5e62074aee281507c5a755fcbe8387d91c'
assert rest['jointOrder'] == full['boneNames'].tolist() == fields['boneNames'].tolist()
source_weights = full['originalFullWeights']
source_xyz = full['originalFullXYZ']
source_ids = full['renderedBodySourceIDs'].astype(int)
assert len(source_ids) == 9037 and len(source_xyz) == 13380
assert np.array_equal(source_xyz, foundation['canonicalXYZ'])
part = rest['parts']['body']
actual_full = np.array(part['fullRawWeights'], np.float32)
actual_four = np.array(part['fourRawWeights'], np.float32)
actual_xyz = np.array(part['xyz'], np.float32)
refs = fields['bodyAttributeEdgeSources']
assert np.array_equal(refs[:9037, :2], np.repeat(source_ids[:, None], 2, axis=1))
identity = (refs[:, 0] >= 0) & (refs[:, 0] == refs[:, 1])
edge = (refs[:, 0] >= 0) & (refs[:, 0] != refs[:, 1])
expected_full = np.zeros_like(actual_full)
expected_four = np.zeros_like(actual_four)
strong_scalar_four = np.zeros_like(actual_four)
expected_xyz = np.zeros_like(actual_xyz)
for index in np.flatnonzero(identity | edge):
    a, b, t = refs[index]
    a, b = int(a), int(b)
    strong_scalar_four[index] = (1 - t) * foundation['canonicalWeights'][a] + t * foundation['canonicalWeights'][b]
    # The serialized interpolation scalar is binary64, but FOUR endpoints are
    # binary32. Preserve source scalar arithmetic instead of NumPy's array
    # scalar promotion; this is checked independently from raw FULL binary64.
    t = float(t)
    expected_full[index] = (1 - t) * source_weights[a] + t * source_weights[b]
    expected_four[index] = (1 - t) * foundation['canonicalWeights'][a] + t * foundation['canonicalWeights'][b]
    expected_xyz[index] = ((1 - t) * source_xyz[a].astype(float) + t * source_xyz[b].astype(float)).astype(np.float32)
display_canonical_different = np.any(expected_four[:9037] != foundation['displayBodyWeights'], axis=1)
expected_four[:9037] = foundation['displayBodyWeights']
raw_reference = fields['bodyCanonicalReferenceFullWeights']
four_reference = fields['bodyCanonicalReferenceFourWeights']
assert np.array_equal(raw_reference[identity | edge], expected_full[identity | edge])
assert np.array_equal(four_reference[identity | edge], expected_four[identity | edge])
provenance = {
    'originalBody52RigWorldExact': bool(np.array_equal(np.array(rest['rigWorldRows']), full['rigWorld'])),
    'originalBody52RigRestExact': bool(np.array_equal(np.array([rest['restBoneRows'][name] for name in rest['jointOrder']]), full['rigRest'])),
    'original9037ActualNativeRawFULLExact': bool(np.array_equal(actual_full[:9037], source_weights[source_ids])),
    'original9037ActualNativeFOURExact': bool(np.array_equal(actual_four[:9037], foundation['displayBodyWeights'])),
    'original9037FOURAuthority': 'F0 displayBodyWeights; independently compared to F0 canonical conditioned FOUR by source ID',
    'original9037CanonicalToDisplayFOURDifferentRows': int(display_canonical_different.sum()),
    'identityCanonicalRows': int(identity.sum()), 'edgeCanonicalRows': int(edge.sum()),
    'derivedUnassignedAncestryRows': int(np.count_nonzero(~(identity | edge))),
    'identityActualRawFULLExact': bool(np.array_equal(actual_full[identity], expected_full[identity])),
    'identityActualFOURExact': bool(np.array_equal(actual_four[identity], expected_four[identity])),
    'canonicalReferenceRawFULLEdgeAndIdentityExact': True,
    'canonicalReferenceFOUREdgeAndIdentityExact': True,
    'edgeFOURStrongScalarFloat64DifferentRows': int(np.any(strong_scalar_four[edge] != expected_four[edge], axis=1).sum()),
    'edgeFOURStrongScalarFloat64MaximumDelta': float(np.max(np.abs(strong_scalar_four[edge] - expected_four[edge]))),
    'authoredSemanticEdgeFULLFOURExact': bool(np.array_equal(actual_full[edge], actual_four[edge])),
    'authoredSemanticEdgeMaximumInfluenceCount': int((actual_four[edge] > 0).sum(axis=1).max()),
    'actualRawFULLMatchesDeliveredFieldExact': bool(np.array_equal(actual_full, fields['bodyFullWeights'])),
    'actualRawFOURMatchesDeliveredFieldExact': bool(np.array_equal(actual_four, fields['bodyFourWeights'])),
    'actualRestXYZMatchesDeliveredFieldExact': bool(np.array_equal(actual_xyz, fields['bodyRestXYZ'])),
    'canonicalIdentityPositionExact': bool(np.array_equal(actual_xyz[identity], expected_xyz[identity])),
    'bodyTrianglesMatchDeliveredExact': bool(np.array_equal(np.array(part['faces']), fields['bodyTriangles'])),
    'headTrianglesMatchDeliveredExact': bool(np.array_equal(np.array(rest['parts']['head']['faces']), fields['headTriangles'])),
    'headActualRawFULLFOURExact': bool(np.array_equal(np.array(rest['parts']['head']['fullRawWeights']), np.array(rest['parts']['head']['fourRawWeights'])))
}
assert all(provenance[key] for key in provenance if key.endswith('Exact'))

records = []
rig_world = np.array(rest['rigWorldRows'])
for pin in native['samples']:
    path = directory / pin['path']
    assert sha(path) == pin['sha256']
    sample = json.loads(gzip.decompress(path.read_bytes()))
    assert list(sample['poseBasisBlender']) == rest['jointOrder']
    skin = np.array(sample['skinNativeRows'])
    row = {'index': sample['index'], 'case': sample['case'], 'phase': sample['phase'], 'regions': {}}
    for region in ('body', 'head', 'boxer', 'cheek'):
        reference = rest['parts'][region]
        world = np.array(reference['objectWorld'])
        local_to_rig = np.linalg.inv(rig_world) @ world
        rig_to_local = np.linalg.inv(local_to_rig)
        corners = np.array(reference['cornerVertices'], int)
        normal = np.array(reference['cornerNormals'])
        region_row = {}
        for field in ('full', 'four'):
            weights = np.array(reference[field + 'Weights'])
            blended = np.einsum('vj,jab->vab', weights, skin)
            linear = np.einsum('ab,vbc,cd->vad', rig_to_local, blended, local_to_rig)[:, :3, :3]
            predicted = np.einsum('vab,vb->va', linear[corners], normal)
            predicted = predicted @ np.linalg.inv(world[:3, :3])
            lengths = np.linalg.norm(predicted, axis=1)
            predicted[lengths > 0] /= lengths[lengths > 0, None]
            actual = np.array(sample['parts'][region][field]['normalWorldCorners'])
            errors = np.linalg.norm(predicted - actual, axis=1)
            worst = int(errors.argmax())
            region_row[field] = {'evaluatedTrianglesExactlyRest': bool(np.array_equal(np.array(sample['parts'][region][field]['faces']), np.array(reference['faces']))),
                                 'maximumCPUFormulaNativeNormalVectorError': float(errors[worst]),
                                 'worstCorner': worst, 'worstNativeVertex': int(corners[worst]),
                                 'predictedWorldNormal': predicted[worst].tolist(), 'actualWorldNormal': actual[worst].tolist(),
                                 'zeroPredictedNormals': int(np.count_nonzero(lengths == 0))}
        row['regions'][region] = region_row
    records.append(row)
result = {'status': 'UNACCEPTED_BODY05_ACTUAL_FIELD_ANCESTRY_AND_NATIVE_NORMAL_DIAGNOSTIC',
          'sourcePins': native['sourcePins'], 'inputPins': {str(path): sha(path) for path in (report_path, rest_path, fields_path, full_path, foundation_path)},
          'recipeSHA256': sha(__file__), 'jointOrderExactlyOwn51': True, 'provenance': provenance,
          'records': records, 'limits': ['Canonical13380/body52 actual raw FULL independently read; conditioned F0 canonical fields are FOUR only.',
                                       'Original9037 FOUR authority is F0 displayBodyWeights; restored canonical and edge reference FOUR authority is F0 canonicalWeights, both explicitly conditioned.',
                                       'Authored plane edge104 fields are deliberate normalized semantic<=4; raw and FOUR ancestry controls retained separately.',
                                       'CPU linear blended normal formula compared to evaluated native corners; no GLB, GPU or parity acceptance.',
                                       'Finite listed FK samples only; no played, grounded-support, continuous-contact, art or device acceptance.']}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('BODY05_FIELDS_READY', json.dumps(provenance), flush=True)
