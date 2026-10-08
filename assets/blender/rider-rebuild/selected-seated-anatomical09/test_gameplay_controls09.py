"""CPU-only intake rejection tests. Synthetic records never qualify a rider."""
import copy
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PATH = Path(__file__).with_name('integrate-gameplay-controls09.py')
SPEC = importlib.util.spec_from_file_location('full_live_controls09', PATH)
SOURCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCE)


def fixture():
    pin = lambda name: {'path': name, 'sha256': name}
    config = {'accepted': False, 'pins': {name: pin(name) for name in SOURCE.PIN_NAMES}}
    pins = config['pins']
    full_config = {'pins': {'gameplayReceipt': pin('actual-converter-receipt')}}
    captured = [{'name': 'RiderGameplayLean'+bike.title(), 'bike': bike, 'fps': 24,
                 'sourceTicks': list(range(0, 1201, 5)), 'nativeWorldMatrices': 'Synthetic; never executed'}
                for bike in ('rookie', 'pro')]
    package = {'accepted': False, 'shapeActivation': 0, 'actions': captured,
               'source': {'recipes': {'gameplayControls': pins['gameplayControlsRecipe'],
                    'controls': pins['controlsRecipe'], 'commonBuild': pins['commonBuildRecipe']}}}
    records = [{key: value for key, value in action.items() if key != 'nativeWorldMatrices'} for action in captured]
    full = {'accepted': False, 'status': 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING',
        'native': pins['fullNative'], 'recipeSHA256': pins['fullRecipe']['sha256'],
        'inputSHA256': pins['fullInput']['sha256'], 'sourcePins': full_config['pins'],
        'shapeActivation': 0, 'actions': records,
        'checks': {key: True for key in ('allOriginalProtectedFieldsExact', 'allVertexGroupNamesAndFieldsExact',
            'originalActionsExact', 'originalKeyCoordinatesExact', 'native75RestExact',
            'visibleMeshesExact', 'checksUseReopenedNative')}}
    full['checks']['matrixReplay'] = [{'action': row['name'], 'frames': 241,
        'maximumAffineBoundWithin2mM': .000001} for row in records]
    control = {'accepted': False, 'status': 'NATIVE_MEASURED_GAMEPLAY_ACTIONS_UNACCEPTED',
        'sourceReceipt': full_config['pins']['gameplayReceipt'], 'recipe': pins['gameplayControlsRecipe'],
        'controlsRecipe': pins['controlsRecipe'], 'commonBuildRecipe': pins['commonBuildRecipe'],
        'nativeRestExactlyPreserved': True, 'shapeActivation': 0, 'actions': copy.deepcopy(records)}
    for row in control['actions']:
        row.update(controlAction='Author.'+row['name'], savedControlReplayMaximumAffineBoundWithin2mM=.000001,
                   bakeMaximumAffineBoundWithin2mM=.000001,
                   nativeWitnesses=[{'frame': frame, 'sourceTick': (frame-1)*5,
                       'capturedPoseBoundM': .000001, 'regionalOperatorBoundM': .000001}
                       for frame in range(1, 242)])
    return config, full, control, package, full_config


class Intake(unittest.TestCase):
    def test_actual_source_pin_rejects_changed_bytes_and_outside_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root/'source.py'
            data = b'original selected source\n'
            source.write_bytes(data)
            pin = {'path': 'source.py', 'sha256': hashlib.sha256(data).hexdigest()}
            with patch.object(SOURCE, 'ROOT', root):
                self.assertEqual(SOURCE.first_pin(pin), source)
                source.write_bytes(data+b'changed\n')
                with self.assertRaises(AssertionError):
                    SOURCE.first_pin(pin)
                with self.assertRaises(AssertionError):
                    SOURCE.first_pin({**pin, 'path': '../source.py'})

    def test_both_passed_prerequisites_match(self):
        SOURCE.validate_lineage(*fixture())

    def test_saved_checkpoint_is_not_successful_reopen(self):
        args = fixture()
        args[1]['status'] = 'SELECTED_FULL_GAMEPLAY_SAVED_REPLAY_AND_ART_PENDING'
        with self.assertRaises(AssertionError):
            SOURCE.validate_lineage(*args)
        args = fixture()
        args[1]['checks']['checksUseReopenedNative'] = False
        with self.assertRaises(AssertionError):
            SOURCE.validate_lineage(*args)

    def test_different_capture_and_missing_bike_are_rejected(self):
        args = fixture()
        args[2]['sourceReceipt'] = {'path': 'other-capture', 'sha256': 'different'}
        with self.assertRaises(AssertionError):
            SOURCE.validate_lineage(*args)
        args = fixture()
        args[2]['actions'].pop()
        with self.assertRaises(AssertionError):
            SOURCE.validate_lineage(*args)

    def test_precision_gate_is_not_relaxed_by_receipt(self):
        for field in ('savedControlReplayMaximumAffineBoundWithin2mM', 'bakeMaximumAffineBoundWithin2mM'):
            for value in (.0001, float('nan'), -1):
                args = fixture()
                args[2]['actions'][0][field] = value
                with self.assertRaises(AssertionError):
                    SOURCE.validate_lineage(*args)
        args = fixture()
        args[2]['actions'][1]['nativeWitnesses'][49]['capturedPoseBoundM'] = .00010001
        with self.assertRaises(AssertionError):
            SOURCE.validate_lineage(*args)

    def test_partial_actions_and_changed_recipes_are_rejected(self):
        args = fixture()
        args[2]['actions'][1]['nativeWitnesses'].pop()
        with self.assertRaises(AssertionError):
            SOURCE.validate_lineage(*args)
        args = fixture()
        args[2]['controlsRecipe'] = {'path': 'other-rig', 'sha256': 'different'}
        with self.assertRaises(AssertionError):
            SOURCE.validate_lineage(*args)


if __name__ == '__main__':
    unittest.main()
