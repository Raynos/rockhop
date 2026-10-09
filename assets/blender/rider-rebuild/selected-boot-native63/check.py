"""CPU checks for exact actual62 admission and frozen native expansion; no Blender."""
import ast
import copy
import json
from pathlib import Path
import tempfile

import numpy as np

import admission
import author

out = admission.OUTPUT_BASE/'cpu-fixture-no-native-output'
result = admission.admit(admission.RECEIPT, admission.RECEIPT_SHA, out)
assert not out.exists(), 'CPU admission created native output'
checks = ['Exact actual62 receipt: both immutable candidate packages and complete protected source fans admitted']


def reject(fn, message=''):
    try: fn()
    except AssertionError as error: assert message in str(error), (message, repr(error))
    else: raise AssertionError('Mutation accepted: '+message)


source_text, author57, _, _ = author.adapted_source(); ast.parse(source_text)
for path in Path(__file__).parent.glob('*.py'): ast.parse(path.read_text())
orientation = author.load(author.ORIENTATION57, 'native63_orientation_check')
proof = orientation.verify_proof(author.PROOF57, author.PROOF57_SHA)
assert proof['sha256'] == author.PROOF57_SHA
for token in ["spec['full'] == 8000 and spec['maximumSurfaceErrorM'] == 0.001",
              "'minimumNormalDot': 0.25, 'maximumSkinWeightL1': 0.3",
              "'maximumInfluences': 4, 'maximumRemovedMass': 0.001",
              "'maximumAdditionalAdjacentWeightL1': 0.002, 'supportEpsilon': 1e-05",
              'ORIENTATION57.install(engine, out, PROOF57)',
              'assert np.array_equal(p, sp[original])',
              'assert np.array_equal(fields, sw[original])',
              "assert before == witness.retained(sources, rig)",
              'assert np.array_equal(engine.triangles(target), f)',
              "surface_checks(engine, source, target, spec['maximumSurfaceErrorM']",
              "'sceneBudgetPassed': False", 'ADMITTED63_SHA',
              "receipt['candidateAttempts'] == 2", "receipt['fixedPoint']['complete'] is True"]:
    assert token in source_text, token
for token in ['ADMITTED61', 'nativeAdmission61', "receipt['topology']", 'Exact candidate46 required',
              "receipt['candidateAttempts'] == 1", 'UNACCEPTED_CONSTRUCTOR59']:
    assert token not in source_text, token
assert source_text.index("out/'admission63.json'") < source_text.index('bpy.ops.wm.save_as_mainfile')
assert source_text.index('bpy.ops.wm.save_as_mainfile') < source_text.index("report['objects'][name]['transfer'] = engine.transfer")
assert source_text.index('engine.transfer(source, target') < source_text.index('surface_checks(engine, source, target, spec')
assert source_text.index('surface_checks(engine, source, target, spec') < source_text.index('engine.unwrap_family([target])')
# Expanding pinned37 reproduces this function byte for byte through46/56/57/63.
def function_text(text, name):
    tree = ast.parse(text)
    return ast.get_source_segment(text, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name))
frozen37 = admission.ROOT/'assets/blender/rider-rebuild/selected-production-constructor37/author.py'
assert function_text(source_text, 'surface_checks') == function_text(frozen37.read_text(), 'surface_checks')
checks.append('Frozen37 surface function exact; frozen56/57 transfer and actual57 proof retained; raw save precedes all native qualifiers')

with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
    file = Path(temporary)/'receipt-fixture.json'; file.write_text('{}\n')
    digest = admission.sha(file); admission.pin(file, digest)
    reject(lambda: admission.pin(file, '0'*64), 'Pinned input changed')
    file.write_text('{"mutated":true}\n')
    reject(lambda: admission.pin(file, digest), 'Pinned input changed')
    reject(lambda: admission.admit(file, admission.sha(file), out), 'Exact reviewed actual62 receipt required')
    reject(lambda: admission.admit(admission.RECEIPT, '0'*64, out), 'Exact reviewed actual62 receipt required')
    reject(lambda: admission.admit(admission.RECEIPT, admission.RECEIPT_SHA, file), 'Fresh native63 output required')
checks.append('Wrong or changed reviewed bytes, alternate receipts, wrong reviewed SHA and existing/out-of-scope outputs reject')

census, seed, policy_receipt = admission.frozen_inputs()
receipt = json.loads(admission.RECEIPT.read_text())
for keys, value in [(('recipeSHA256',), 'changed'), (('closureRecipeSHA256',), 'changed'),
                    (('sceneBudgetPassed',), True), (('candidateAttempts',), 1),
                    (('fanConstructorAncestry', 'sha256'), 'changed'),
                    (('initialFanCensus', 'sha256'), 'changed'),
                    (('fanRetention', 'passed'), False), (('fanRetention', 'missingCount'), 1),
                    (('sourceInputBytesUnchanged',), False), (('policy', 'minimumNormalDot'), .1),
                    (('originalTopology', 'components'), -1), (('fixedPoint', 'complete'), False),
                    (('fixedPoint', 'minimumNormalDot'), .1), (('finalFanProtection', 'sha256'), 'changed'),
                    (('fixedPoint', 'iterations', 0, 'vertexNormalCensus', 'threshold'), .01),
                    (('fixedPoint', 'iterations', 0, 'addedOriginalFanCenters'), []),
                    (('fixedPoint', 'iterations', 0, 'vertexNormalCensus', 'failures', 0, 'normalDot'), float('nan')),
                    (('fixedPoint', 'iterations', 1, 'vertexNormalCensus', 'passed'), False)]:
    mutation = copy.deepcopy(receipt); row = mutation
    for key in keys[:-1]: row = row[key]
    row[keys[-1]] = value
    reject(lambda: admission.receipt_metadata(mutation, census, seed, policy_receipt))
# Mutate the final duplicate consistently, proving it is gated beyond mere equality.
mutation = copy.deepcopy(receipt)
for row in [mutation['vertexNormalCensus'], mutation['fixedPoint']['iterations'][-1]['vertexNormalCensus']]:
    row['minimumNormalDot'] = .249
reject(lambda: admission.receipt_metadata(mutation, census, seed, policy_receipt))
checks.append('Actual62 schema, recipe, ancestry, incomplete closure, failure census, .25 threshold and unaccepted budget mutations reject')

source = admission.array_package(receipt['sourceArrayPackage'])
candidate = admission.array_package(receipt['candidate'])
returned = admission.array_package(receipt['returnedOriginalIndices'])
protection = admission.array_package(receipt['finalFanProtection'])
original = candidate['originalVertexIds']; triangles = candidate['triangles'].reshape(-1, 3)
center_set = set(protection['centerOriginalVertexIds'].tolist())
face_id = next(i for i, face in enumerate(original[triangles]) if any(int(v) in center_set for v in face))
for kind, message in [('position', 'Original positions'), ('field', 'Original named fields'),
                      ('winding', 'Exact oriented source fan'), ('material', 'Protected source material'),
                      ('edge', 'Required protected edge'), ('indices', 'Returned index ancestry')]:
    mutation = dict(candidate); changed_returned = returned
    if kind == 'position':
        mutation['positions'] = candidate['positions'].copy(); mutation['positions'][0] += np.float32(1e-5)
    elif kind == 'field':
        mutation['namedWeights'] = candidate['namedWeights'].copy(); mutation['namedWeights'][0] += np.float32(.01)
    elif kind == 'winding':
        mutation['triangles'] = candidate['triangles'].copy()
        row = mutation['triangles'].reshape(-1, 3)[face_id]; row[0], row[1] = row[1], row[0]
        changed_returned = {'triangles': original[mutation['triangles']]}
    elif kind == 'material':
        mutation['faceMaterialIds'] = candidate['faceMaterialIds'].copy(); mutation['faceMaterialIds'][face_id] += 1
    elif kind == 'edge':
        remove = tuple(protection['requiredEdgesOriginal'][:2]); rows = candidate['requiredEdgesOriginal'].reshape(-1, 2)
        mutation['requiredEdgesOriginal'] = rows[~np.all(rows == remove, axis=1)].ravel()
    else:
        changed_returned = {'triangles': returned['triangles'].copy()}; changed_returned['triangles'][0] ^= 1
    reject(lambda: admission.verify_arrays(source, mutation, changed_returned, protection, receipt), message)
checks.append('Actual candidate position/field/winding/material/edge/returned-index mutations reject before raw save')


first, last = receipt['fixedPoint']['iterations']
previous = admission.array_package(first['protection'])
protected = admission.array_package(last['protection'])
admission.verify_growth(previous, protected, first)
for changed in [previous['centerOriginalVertexIds'], np.union1d(protected['centerOriginalVertexIds'], [0])]:
    mutation = dict(protected, centerOriginalVertexIds=changed)
    reject(lambda: admission.verify_growth(previous, mutation, first), 'Closure did not add every and only failing fan')
mutation = dict(protection, requiredSourceFaceIds=protection['requiredSourceFaceIds'][1:])
reject(lambda: admission.verify_arrays(source, candidate, returned, mutation, receipt), 'Incomplete source center-fan certificate')
mutation = dict(protection, requiredEdgesOriginal=protection['requiredEdgesOriginal'][2:])
reject(lambda: admission.verify_arrays(source, candidate, returned, mutation, receipt), 'Incomplete source fan-edge certificate')
mutation = copy.deepcopy(last); mutation['fanProtection']['addedLocks'] = 0
reject(lambda: admission.verify_round(source, mutation, receipt['groupNames'], previous))
checks.append('Actual59 failure120878 enters exact monotone fan closure; omitted/extra centers, incomplete source fans/edges and false added-lock counts reject')

evidence = admission.ROOT/'docs/evidence/rider-rebuild/selected-boot-native63'
evidence.mkdir(parents=True, exist_ok=True)
(evidence/'cpu-admission.json').write_text(json.dumps(result, indent=2)+'\n')
(evidence/'fixtures.json').write_text(json.dumps({'status': 'CPU_ACTUAL62_ADMISSION_FIXTURES_PASSED_NATIVE_PENDING',
    'constructor': result['constructor'], 'checks': checks,
    'limits': 'No native output, Blender invocation, atlas/budget/art acceptance or production mutation.'}, indent=2)+'\n')
print('\n'.join('PASS: '+check for check in checks))
