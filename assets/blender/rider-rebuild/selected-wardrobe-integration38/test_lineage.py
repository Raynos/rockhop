"""CPU-light rejection fixtures; these records are not native evidence."""
import ast
import copy
import json
from pathlib import Path
import lineage as h

pin = lambda name: {'path': 'fixture/'+name, 'sha256': 'a'*64}
pins = {name: pin(name) for name in h.PIN_NAMES}
target = {'accepted': False, 'status': 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING',
          'native': pins['targetNative'], 'recipeSHA256': pins['targetRecipe']['sha256'],
          'inputSHA256': pins['targetInput']['sha256'], 'sourcePins': {'native': h.REPAIRED},
          'shapeActivation': 0, 'nativeFileCompressed': False,
          'visibleMeshes': [*h.WARDROBE, 'RiderBody', 'RiderJeans', 'Boot.L', 'Boot.R'],
          'checks': {**{name: True for name in h.TARGET_CHECKS}, 'matrixReplay': [
              {'action': 'RiderGameplayLean'+bike, 'frames': 241, 'maximumAffineBoundWithin2mM': .00002}
              for bike in ('Rookie', 'Pro')]}}
config = {'pins': {'constructor38': pins['sleeveRecipe'], 'checkpointHelper38': pins['checkpointHelper'],
                   'gloveNative': pin('gloveNative')}}
common = {'acceptedArt': False, 'protectedValidationPassed': True, 'exact75RestUnchanged': True,
          'protectedValidationStage': 'SEPARATE_REOPENED_NATIVE',
          'nativeStorage': {'reopenVerified': True, 'compressed': False}}
glove = {**copy.deepcopy(common), 'status': 'UNACCEPTED_GLOVES_CONSTRUCTED_SLEEVE_NOT_AUTHORED',
         'sourceRecipe': {'path': 'fixture/gloves04.py', 'sha256': h.GLOVE04_SHA},
         'sourceMaster': h.ORIGINAL_MASTER, 'native': config['pins']['gloveNative']}
sleeve = {**copy.deepcopy(common), 'status': 'UNACCEPTED_CONSTRUCTION_DENSE_AND_MOTION_PENDING',
          'native': pins['sleeveNative'], 'recipeSHA256': pins['sleeveRecipe']['sha256'],
          'inputSHA256': pins['sleeveInput']['sha256'], 'sourcePins': config['pins'],
          'actualFullReferenceExactToSavedBasisAndTriangles': True,
          'ancestry': {'allSourcePrefixNamedFieldsExact': True, 'allNewSourceParentNamedFieldsExactAfterFloat32Storage': True}}
dense = {'acceptedArt': False, 'sourceNative': pins['sleeveNative'], 'completeStaticRelations': True,
         'staticTriangleRelationsPassed': True, 'relations': {name: pin(name) for name in h.RELATIONS}}
relations = {name: {'relation': name, 'sourceNative': pins['sleeveNative'], 'recipeSHA256': h.QUALIFY28_SHA,
                    'fullTrianglesNoRadialCrop': True, 'status': 'PASS_SINGLE_STATIC_RELATION',
                    'result': {'passed': True}, 'acceptedArt': False} for name in h.RELATIONS}
h.target_gate(target, pins)
h.sleeve_gate(sleeve, glove, dense, relations, config, pins)
fixtures = ['Actual qualified schema accepts an explicitly pinned target generation without inferring its native filename']

original = {'accepted': False, 'pins': copy.deepcopy(target['sourcePins'])}
nested = {'accepted': False, 'pins': {'sourceInput': pin('original08input'), 'sourceRecipe': h.GAMEPLAY08}}
qualified = {**copy.deepcopy(target), 'input': pins['targetInput'], 'recipe': pins['targetRecipe'],
             'sourceInput': nested['pins']['sourceInput'], 'sourceRecipe': h.GAMEPLAY08, 'actions': []}
pending = {**copy.deepcopy(qualified), 'status': 'SELECTED_FULL_GAMEPLAY_SAVED_PROTECTED_AND_REPLAY_PENDING'}
snapshot = {'accepted': False, 'kind': 'source', 'native': h.REPAIRED, 'pending': pin('actualPending'),
            'recipe': pins['targetRecipe'], 'protected': {name: 'field' for name in target['visibleMeshes']+[h.REFERENCE]},
            'fields': {name: 'field' for name in target['visibleMeshes']+[h.REFERENCE]}, 'keys': {},
            'rest': ['original75'], 'visibleMeshes': target['visibleMeshes'], 'actions': {'original': 'unchanged'}}
saved = {**copy.deepcopy(snapshot), 'kind': 'saved', 'native': pins['targetNative']}
h.target_ancestry(qualified, nested, original, pins, snapshot, saved, pending)
fixtures.append('Actual10 nested sourceInput/sourceRecipe resolves original08 pins and native-specific preservation snapshots')
for label, mutation in (
    ('Mismatched nested source input is rejected', lambda t, a: t.update(sourceInput=pin('wrong08input'))),
    ('Saved snapshot from a different native is rejected', lambda t, a: a.update(native=pin('wrongSavedNative'))),
    ('Saved snapshot field change is rejected', lambda t, a: a['fields'].update(RiderJeans='changed')),
    ('Missing original action in saved snapshot is rejected', lambda t, a: a['actions'].clear())):
    candidate, changed = copy.deepcopy(qualified), copy.deepcopy(saved)
    mutation(candidate, changed)
    try: h.target_ancestry(candidate, nested, original, pins, snapshot, changed, pending)
    except AssertionError: fixtures.append(label)
    else: raise AssertionError('Accepted '+label)


def reject(label, edit, check):
    value = copy.deepcopy((target, sleeve, glove, dense, relations))
    edit(*value)
    try: check(*value)
    except (AssertionError, KeyError): fixtures.append(label)
    else: raise AssertionError('Failed to reject: '+label)


target_check = lambda t, s, g, d, r: h.target_gate(t, pins)
sleeve_check = lambda t, s, g, d, r: h.sleeve_gate(s, g, d, r, config, pins)
reject('Target pending save cannot replace reopened complete gameplay qualification',
       lambda t, s, g, d, r: t.update(status='SELECTED_FULL_GAMEPLAY_SAVED_REPLAY_AND_ART_PENDING'), target_check)
reject('Wrong selected repaired master ancestry is rejected',
       lambda t, s, g, d, r: t['sourcePins'].update(native=h.ORIGINAL_MASTER), target_check)
reject('A missing original fullcheck is rejected',
       lambda t, s, g, d, r: t['checks'].update(originalActionsExact=False), target_check)
reject('An invalid second-bike replay is rejected',
       lambda t, s, g, d, r: t['checks']['matrixReplay'][1].update(maximumAffineBoundWithin2mM=.001), target_check)
reject('Pending glove04 cannot enter sleeve integration',
       lambda t, s, g, d, r: g.update(protectedValidationPassed=False), sleeve_check)
reject('Pending sleeve38 cannot enter integration',
       lambda t, s, g, d, r: s.update(status='UNACCEPTED_SLEEVE_SAVED_PROTECTED_VALIDATION_PENDING'), sleeve_check)
reject('A dense result from a different saved native is rejected',
       lambda t, s, g, d, r: r[h.RELATIONS[-1]].update(sourceNative=pin('wrongNative')), sleeve_check)
reject('Five dense relations cannot masquerade as six',
       lambda t, s, g, d, r: r.pop(h.RELATIONS[-1]), sleeve_check)
reject('A failed individual dense relation is rejected despite the aggregate marker',
       lambda t, s, g, d, r: r[h.RELATIONS[0]]['result'].update(passed=False), sleeve_check)

source = (h.HERE/'integrate.py').read_text()
tree = ast.parse(source)
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'integrate')
calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
assert not any(isinstance(call.func, ast.Name) and call.func.id in {'fingerprint', 'geometry', 'exact_group_digest'} for call in calls)
assert 'compress=False' in source and 'compress=True' not in source
assert 'objects = list(h.WARDROBE)' in source and 'obj.data = mesh' in source and 'orphans_purge' not in source
fixtures.append('Integration source appends only three named objects and uses a raw save before any full field comparison')
print(json.dumps({'passed': True, 'nativeRunExecuted': False, 'fixtures': fixtures,
                  'fixtureReceiptsAreNotActualEvidence': True}, indent=2))
