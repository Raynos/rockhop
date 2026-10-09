"""Actual receipt gates for selected sleeve/gloves onto the repaired rider.

No native filename or preparation marker substitutes for reopened comparisons.
The destination may be any explicitly pinned generation retaining the complete
original08 replay/check schema and the selected repaired master ancestry.
"""
import json
import importlib.util
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
io = runpy.run_path(str(HERE/'sleeve_checkpoint.py'))
ROOT, pin, checked = io['ROOT'], io['pin'], io['checked']
WARDROBE = ('RiderHoodie', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R')
REFERENCE = 'RiderBody__FullAnatomyReference'
RELATIONS = ('hoodie-full-wearer', 'hoodie-self', 'hoodie-glove-L', 'hoodie-glove-R',
             'glove-L-full-wearer', 'glove-R-full-wearer')
REPAIRED = {'path': 'harness/out/rider-rebuild/selected-seated-anatomical09/authored02/selected-anatomical09-weight-only.blend',
            'sha256': '4a330ae8a5e93c00a1492dbfd28923ff29796650bbae1dacfadc5fcf00a627a0'}
ORIGINAL_MASTER = {'path': 'harness/out/rider-rebuild/selected-complete-engine01/engine05/rider-private-masked.blend',
                   'sha256': '95a4f14e06fb52cc055df6d1446a035d8cd3d35180d565ad52f3a70b3b05664b'}
GLOVE04_SHA = 'c1a98001b74ad0ad445f856a2f423d320bf98ec1b9e315126eba218bb55ce002'
QUALIFY28_SHA = 'd4e261170c8d754ca97eec329d2958ad88e059a5f87903fc862207d87087710c'
GAMEPLAY08 = {'path': 'assets/blender/rider-rebuild/selected-seated-anatomical09/append-measured-gameplay08.py',
              'sha256': '2399678e7c7fff60f2bc7a3aa609dc439e869a5dc6d6287d8b94f1c98180d1a5'}
TARGET_CHECKS = ('allOriginalProtectedFieldsExact', 'allVertexGroupNamesAndFieldsExact',
                 'originalActionsExact', 'originalKeyCoordinatesExact', 'native75RestExact',
                 'visibleMeshesExact', 'checksUseReopenedNative')
PIN_NAMES = {'targetReceipt', 'targetNative', 'targetInput', 'targetRecipe', 'sleeveReceipt',
             'sleeveNative', 'sleeveInput', 'sleeveRecipe', 'denseSummary', 'integrationRecipe',
             'lineageHelper', 'checkpointHelper'}


def target_gate(receipt, pins):
    assert receipt['accepted'] is False
    assert receipt['status'] == 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING'
    assert receipt['native'] == pins['targetNative']
    assert receipt['recipeSHA256'] == pins['targetRecipe']['sha256']
    assert receipt['inputSHA256'] == pins['targetInput']['sha256']
    assert receipt['sourcePins']['native'] == REPAIRED
    assert receipt['shapeActivation'] == 0 and receipt['nativeFileCompressed'] is False
    assert all(receipt['checks'][key] is True for key in TARGET_CHECKS)
    assert len(receipt['visibleMeshes']) == len(set(receipt['visibleMeshes'])) == 7
    assert set(WARDROBE)|{'RiderBody', 'RiderJeans'} <= set(receipt['visibleMeshes'])
    assert len(receipt['checks']['matrixReplay']) == 2
    assert [row['action'] for row in receipt['checks']['matrixReplay']] == [
        'RiderGameplayLeanRookie', 'RiderGameplayLeanPro']
    assert all(row['frames'] == 241 and 0 <= row['maximumAffineBoundWithin2mM'] < .0001
               for row in receipt['checks']['matrixReplay'])


def target_ancestry(receipt, config, original, pins, before=None, after=None, pending=None):
    assert config['accepted'] is original['accepted'] is False
    assert receipt['sourcePins'] == original['pins']
    assert original['pins']['native'] == REPAIRED
    if set(config['pins']) == {'sourceInput', 'sourceRecipe'}:
        assert receipt['input'] == pins['targetInput'] and receipt['recipe'] == pins['targetRecipe']
        assert receipt['sourceInput'] == config['pins']['sourceInput']
        assert receipt['sourceRecipe'] == config['pins']['sourceRecipe'] == GAMEPLAY08
        assert pending['status'] == 'SELECTED_FULL_GAMEPLAY_SAVED_PROTECTED_AND_REPLAY_PENDING'
        assert pending['accepted'] is False
        for key in ('native', 'input', 'recipe', 'sourceInput', 'sourceRecipe', 'sourcePins', 'actions'):
            assert pending[key] == receipt[key], key
        assert before['accepted'] is after['accepted'] is False
        assert before['kind'] == 'source' and after['kind'] == 'saved'
        assert before['native'] == REPAIRED and after['native'] == pins['targetNative']
        assert before['pending'] == after['pending']
        assert before['recipe'] == after['recipe'] == pins['targetRecipe']
        for key in ('protected', 'fields', 'keys', 'rest', 'visibleMeshes'):
            assert before[key] == after[key], key
        required = set(receipt['visibleMeshes'])|{REFERENCE}
        assert set(before['protected']) == set(before['fields']) == required
        assert before['actions'] and all(after['actions'].get(name) == value for name, value in before['actions'].items())
    else:
        assert config == original and pins['targetRecipe'] == GAMEPLAY08


def sleeve_gate(sleeve, glove, dense, relations, config, pins):
    assert sleeve['acceptedArt'] is glove['acceptedArt'] is False
    assert sleeve['status'] == 'UNACCEPTED_CONSTRUCTION_DENSE_AND_MOTION_PENDING'
    assert sleeve['native'] == pins['sleeveNative']
    assert sleeve['recipeSHA256'] == pins['sleeveRecipe']['sha256']
    assert sleeve['inputSHA256'] == pins['sleeveInput']['sha256']
    assert sleeve['sourcePins'] == config['pins']
    assert config['pins']['constructor38'] == pins['sleeveRecipe']
    assert config['pins']['checkpointHelper38'] == pins['checkpointHelper']
    for report in (sleeve, glove):
        assert report['protectedValidationPassed'] is True and report['exact75RestUnchanged'] is True
        assert report['protectedValidationStage'] == 'SEPARATE_REOPENED_NATIVE'
        assert report['nativeStorage']['reopenVerified'] is True and report['nativeStorage']['compressed'] is False
    assert sleeve['actualFullReferenceExactToSavedBasisAndTriangles'] is True
    assert sleeve['ancestry']['allSourcePrefixNamedFieldsExact'] is True
    assert sleeve['ancestry']['allNewSourceParentNamedFieldsExactAfterFloat32Storage'] is True
    assert glove['status'] == 'UNACCEPTED_GLOVES_CONSTRUCTED_SLEEVE_NOT_AUTHORED'
    assert glove['sourceRecipe']['sha256'] == GLOVE04_SHA
    assert glove['sourceMaster'] == ORIGINAL_MASTER and glove['native'] == config['pins']['gloveNative']
    assert dense['acceptedArt'] is False and dense['sourceNative'] == sleeve['native']
    assert dense['completeStaticRelations'] is dense['staticTriangleRelationsPassed'] is True
    assert set(dense['relations']) == set(relations) == set(RELATIONS)
    for name, row in relations.items():
        assert row['relation'] == name and row['sourceNative'] == sleeve['native']
        assert row['recipeSHA256'] == QUALIFY28_SHA and row['fullTrianglesNoRadialCrop'] is True
        assert row['status'] == 'PASS_SINGLE_STATIC_RELATION' and row['result']['passed'] is True
        assert row['acceptedArt'] is False


def read_input(path):
    config = json.loads(Path(path).read_text())
    assert config['acceptedArt'] is False and set(config['pins']) == PIN_NAMES
    pins = config['pins']
    for row in pins.values(): checked(row)
    for key, name in (('integrationRecipe', 'integrate.py'), ('lineageHelper', 'lineage.py'),
                      ('checkpointHelper', 'sleeve_checkpoint.py'), ('sleeveRecipe', 'sleeve38.py')):
        assert pins[key] == pin(HERE/name)
    read = lambda row: json.loads(checked(row).read_text())
    target = read(pins['targetReceipt']); target_gate(target, pins)
    target_config = read(pins['targetInput'])
    if set(target_config['pins']) == {'sourceInput', 'sourceRecipe'}:
        for row in target_config['pins'].values(): checked(row)
        original = read(target_config['pins']['sourceInput'])
        assert set(target['preservationSnapshots']) == {'source', 'saved'}
        before, after = [read(target['preservationSnapshots'][name]) for name in ('source', 'saved')]
        pending = read(before['pending']); checked(after['pending'])
        target_ancestry(target, target_config, original, pins, before, after, pending)
        original_input = target_config['pins']['sourceInput']
    else:
        original = target_config
        target_ancestry(target, target_config, original, pins)
        original_input = pins['targetInput']
    # Resolve the exact original08 source/capture validation through either
    # the flat08 input or an explicitly pinned save-first generation wrapper.
    spec = importlib.util.spec_from_file_location('wardrobe38_original08_input', checked(GAMEPLAY08))
    original_helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(original_helper)
    checked_original, package = original_helper.read_input(checked(original_input))
    assert checked_original == original
    assert target['actions'] == [{key: value for key, value in action.items() if key != 'nativeWorldMatrices'}
                                 for action in package['actions']]
    for row in target['sourcePins'].values(): checked(row)
    checked(target['bodySurfaceArrays'])
    sleeve = read(pins['sleeveReceipt']); sleeve_config = read(pins['sleeveInput'])
    for row in sleeve_config['pins'].values(): checked(row)
    glove = read(sleeve_config['pins']['gloveReceipt'])
    dense = read(pins['denseSummary'])
    relations = {name: read(row) for name, row in dense['relations'].items()}
    sleeve_gate(sleeve, glove, dense, relations, sleeve_config, pins)
    for report in (glove, sleeve):
        for key in ('native', 'pendingReceipt', 'expectedWitness'): checked(report[key])
    for row in glove['gloveObjects'].values(): checked({key: row[key] for key in ('path', 'sha256')})
    checked(sleeve['ancestry']['ancestry']); checked(sleeve['field'])
    contract = read(target['sourcePins']['contract'])
    assert contract['nativeRest']['bones'] and len(contract['nativeRest']['bones']) == 75
    assert sorted(contract['specification']['meshNames'].values()) == sorted(target['visibleMeshes'])
    return config, target, sleeve, contract
