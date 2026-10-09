"""Narrow provenance gate around the unchanged selected wardrobe38 merger.

The selected target was saved by recipe10 and qualified by recipe11. Both
pins must remain explicit. No frozen38 source or existing input is rewritten.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import gameplay_qualify11 as qualifier

INTEGRATE38 = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/integrate.py',
               'sha256': 'dd7e3373b43325149505ad89ce1a5ff5eb74d61776d5fc96df73c62d10d8ab49'}
LINEAGE38 = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/lineage.py',
             'sha256': 'cc1157bf315622e598c2c9051d80d9e707b1082e0275030d2c694f63557c9997'}


def explicit_qualifier(receipt, expected, pending_pin):
    assert receipt['accepted'] is False and receipt['status'] == 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING'
    assert receipt['recipe'] == qualifier.GENERATION10
    assert receipt['recipeSHA256'] == qualifier.GENERATION10['sha256']
    assert receipt['qualificationRecipe'] == expected and receipt['qualificationRecipe'] != receipt['recipe']
    assert receipt['qualifiedPending'] == pending_pin


def install_gate(merger):
    original_read = merger.h.read_input
    def read_input(path):
        result = original_read(path)
        config, target, sleeve, contract = result
        expected = merger.h.pin(HERE/'gameplay_qualify11.py')
        merger.h.checked(target['qualificationRecipe'])
        # Read only the small pending witness here. Frozen38 already compared
        # both native-specific snapshot documents and all original08 gates.
        pending_path = merger.h.checked(target['qualifiedPending'])
        pending = json.loads(pending_path.read_text())
        explicit_qualifier(target, expected, merger.h.pin(pending_path))
        for key in ('native', 'input', 'recipe', 'sourceInput', 'sourceRecipe', 'sourcePins', 'actions'):
            assert pending[key] == target[key], key
        assert pending['status'] == 'SELECTED_FULL_GAMEPLAY_SAVED_PROTECTED_AND_REPLAY_PENDING'
        return result
    merger.h.read_input = read_input


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(args) == 2, 'Use ACTUAL_INTEGRATION38_INPUT FRESH_OUTPUT'
    for row in (INTEGRATE38, LINEAGE38):
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest() == row['sha256']
    spec = importlib.util.spec_from_file_location('qualified11_unchanged_merger38', ROOT/INTEGRATE38['path'])
    merger = importlib.util.module_from_spec(spec); spec.loader.exec_module(merger)
    install_gate(merger)
    import bpy
    input_path, out = [Path(value).resolve() for value in args]
    merger.integrate(input_path, out, bpy)
    path = out/'pending.json'
    pending = json.loads(path.read_text())
    pending.update(intakeRecipe=merger.h.pin(__file__),
                   targetQualificationRecipe=merger.h.pin(HERE/'gameplay_qualify11.py'))
    path.write_text(json.dumps(pending, indent=2)+'\n')


if __name__ == '__main__': main()
