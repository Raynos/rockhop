"""Read-only parent check of the frozen native50 capture, not a new trial."""
import gc
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[6]
leaf = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
unpack = lambda p: json.loads(gzip.decompress(Path(p).read_bytes()))
execution = read(leaf / 'capture50-execution.json')
manifest = read(leaf / 'manifest-bound50.json')
directory = root / execution['nativeOutputDirectory']
report = read(directory / 'report.json')
assert execution['actualOuterProcessExitCode'] == execution['actualWorkerExitCode'] == 0
assert execution['sourcePinsRemainExact']
for key in ['command', 'manifest', 'recipe', 'guardRecipe', 'nativeCandidate',
            'fields', 'native49ScopeReceipt']:
    pin = execution[key]
    assert sha(root / pin['path']) == pin['sha256'], key
for filename, digest in execution['frozenCopies'].items():
    assert sha(leaf / filename) == digest, filename
assert sha(directory / 'report.json') == sha(leaf / 'capture50-native-report.json')
for filename, digest in report['sourcePins'].items():
    assert sha(filename) == digest, filename
for pin in [execution['rest'], *execution['samples']]:
    assert sha(directory / pin['path']) == pin['sha256'], pin['path']
assert execution['samples'] == report['samples']
assert execution['rest'] == report['rest']
fields = np.load(root / manifest['fields']['path'])
predictions_path = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body07/array-preflight04/saved-pose-predictions.npz'
assert sha(predictions_path) == '49940363592871f4148055917a0444c240d748b44f433f484757d84586252770'
predictions = np.load(predictions_path)
rest = unpack(directory / report['rest']['path'])
assert list(fields['boneNames']) == rest['jointOrder']
checks = {}
for region in ['body', 'head']:
    actual = rest['parts'][region]
    rows = {}
    for actual_key, field_key in [('xyz', 'RestXYZ'), ('faces', 'Triangles'),
                                  ('fullRawWeights', 'FullWeights'), ('fourRawWeights', 'FourWeights')]:
        expected = fields[region + field_key]
        observed = np.asarray(actual[actual_key])
        assert np.array_equal(observed, expected), (region, actual_key)
        rows[actual_key + 'Exact'] = True
    checks[region] = rows
changed = fields['bodyShoulderHarmonicChanged330NativeIDs']
outside = np.ones(len(fields['bodyRestXYZ']), dtype=bool)
outside[changed] = False
assert len(changed) == 330
for kind in ['Full', 'Four']:
    assert np.array_equal(fields['body' + kind + 'Weights'][outside],
                          fields['bodyBody06RawReference' + kind + 'Weights'][outside])
checks['bodyOutsideChanged330RawFullFourExactToBody06'] = True
old_dir = (root / manifest['poseAuthorityReport']['path']).parent
old_report = read(old_dir / 'report.json')
old_rest = unpack(old_dir / old_report['rest']['path'])
for region in ['boxer', 'cheek']:
    exact = {}
    for key in ['xyz', 'faces', 'objectWorld', 'fullWeights', 'fourWeights',
                'fullRawWeights', 'fourRawWeights', 'cornerVertices', 'cornerNormals']:
        assert np.array_equal(np.asarray(rest['parts'][region][key]),
                              np.asarray(old_rest['parts'][region][key])), (region, key)
        exact[key] = True
    checks[region + 'UnchangedToPoseAuthorityRest'] = exact
del rest, old_rest
gc.collect()
old_samples = {pin['path']: pin for pin in old_report['samples']}
records = []
for pin in report['samples']:
    old_pin = old_samples[pin['path']]
    assert sha(old_dir / old_pin['path']) == old_pin['sha256']
    sample = unpack(directory / pin['path'])
    old = unpack(old_dir / pin['path'])
    for key in ['index', 'case', 'phase', 'timeS', 'poseBasisBlender',
                'skinNativeRows', 'boneWorldNativeRows']:
        assert sample[key] == old[key], (pin['path'], key)
    residuals = {}
    for kind in ['full', 'four']:
        observed = np.asarray(sample['parts']['body'][kind]['xyzWorld'])
        predicted = predictions['sample%04d_%s_candidateXYZ' % (sample['index'], kind)]
        maximum = float(np.linalg.norm(observed - predicted, axis=1).max())
        assert maximum < 2e-6, (sample['index'], kind, maximum)
        residuals[kind + 'MaximumPredictionNativeM'] = maximum
    records.append({'index': sample['index'], 'saved51PayloadSkinAndBoneWorldExact': True,
                    **residuals})
    del sample, old
    gc.collect()
    print('PARENT_CAPTURE_READBACK', records[-1]['index'], flush=True)
f0 = read(leaf / 'capture50-f0-preservation.json')
for key in ['originalObjectsExact', 'original51RigRestWorldScaleExact',
            'copied51RigRestWorldScaleExact', 'originalSavedPoseBasisExact',
            'originalMaterialsExact', 'originalPackedImagesExact']:
    assert f0[key], key
for head in f0['heads'].values():
    assert head['protectedXYZExact'] and head['everySourceProtectedCornerOccursExactlyOnce']
    assert head['rawProtectedPackedNormalCornersExact'] and head['changedProtectedNormalCorners'] == 0
    assert all(layer['protectedExact'] for layer in head['protectedUVLayers'])
result = {'status': 'ROOT_CAPTURE50_READBACK_PASS_UNACCEPTED_PAUSE_CHECKPOINT',
    'round': 50, 'recipeSHA256': sha(__file__),
    'executionReceiptSHA256': sha(leaf / 'capture50-execution.json'),
    'nativeReportSHA256': sha(directory / 'report.json'),
    'sourceNativeSHA256': manifest['candidate']['sha256'],
    'sourceFieldsSHA256': manifest['fields']['sha256'], 'checks': checks, 'records': records,
    'boxerTriangulationFailureIndices': [302],
    'next': 'Complete geometry-check on actual captured triangles plus ordinary game gate51; then played body07 anatomy review before any correction or promotion.',
    'limits': ['Parent independently checks frozen capture and authored raw arrays; no new Blender execution, authoring or source rewrite.',
        'Historical manifest/proposal pending-admission wording is retained unchanged. Actual execution50 is recorded separately; prior parent admission is preserved in the session handoff.',
        'Boxer evaluated triangulation/corner triples fail at302 in FULL/FOUR; body/head/cheek stable. This is a failure, not an accepted topology exception.',
        'Ten frozen poses and submicrometre agreement do not prove anatomy, continuous motion, normals, contacts, clothes, engine, phone or shipping acceptance.']}
target = leaf / 'parent-readback50.json'
assert not target.exists()
target.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'records': records}))
