"""Narrow dependency-refresh adapter for frozen conditioned04.

No solver, pole, rest, skin, action, branch policy or tolerance changes.
Every explicit mode request tags the rig, updates its dependency graph, and
requires the actual evaluated IK influences to equal the requested modes.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE04 = {'path': 'assets/blender/rider-rebuild/selected-authoring-motion11/gameplay_conditioned04.py',
            'sha256': '308f7e988e18847e10fff3d24b60f73500977ddbabd3397d60a8bea2033d013b'}


def frozen():
    import hashlib
    path = ROOT/SOURCE04['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SOURCE04['sha256']
    spec = importlib.util.spec_from_file_location('frozen_conditioned04', path)
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    return source


def read_input(path, source):
    config = json.loads(path.read_text())
    assert config['accepted'] is False and set(config['pins']) == {'sourceInput', 'sourceRecipe', 'adapter', 'actualFailure'}
    pins = config['pins']
    for pin in pins.values():
        source.pinned(pin)
    assert pins['sourceRecipe'] == SOURCE04
    assert source.pinned(pins['adapter']) == Path(__file__).resolve()
    failure = json.loads(source.pinned(pins['actualFailure']).read_text())
    assert failure['accepted'] is False and failure['action'] == 'RiderGameplayLeanRookie'
    assert failure['frame'] == 51 and failure['sourceTick'] == 250
    assert failure['maximumFKBoundM'] == failure['maximumIKBoundM'] > source.LIMIT
    original, package, contract = source.read_input(source.pinned(pins['sourceInput']))
    return config, original, package, contract


def refresh_modes(original, bpy, rig, context, modes, emit):
    original(rig, context, modes)
    before = {limb['kind']+limb['side']: next(constraint.influence
        for constraint in rig.pose.bones[limb['mechanismLower']].constraints if constraint.type == 'IK')
        for limb in context['limbs']}
    # Direct RNA custom-property writes need an explicit object dependency tag.
    # A view-layer update alone need not reevaluate a driver on an untagged ID.
    rig.update_tag()
    bpy.context.view_layer.update()
    evaluated = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    rows = []
    for limb in context['limbs']:
        name = limb['kind']+limb['side']
        actual = next(constraint for constraint in evaluated.pose.bones[limb['mechanismLower']].constraints
                      if constraint.type == 'IK')
        requested = float(modes[name])
        row = {'limb': name, 'requestedIKMode': requested,
            'propertyValue': float(rig.pose.bones[limb['targetControl']][context['ikProperty']]),
            'sourceInfluenceBeforeTag': float(before[name]), 'evaluatedInfluenceAfterTag': float(actual.influence),
            'evaluatedMuted': actual.mute, 'evaluatedLiveMode': float(evaluated[context['liveProperty']])}
        rows.append(row)
    emit({'frame': bpy.context.scene.frame_current, 'limbs': rows})
    assert all(row['requestedIKMode'] == row['propertyValue'] == row['evaluatedInfluenceAfterTag']
               and row['evaluatedLiveMode'] == 1. and row['evaluatedMuted'] is False for row in rows), (
                   'Mode property did not reach the actual evaluated IK constraints', rows)


def run(mode, input_path, plan_path, out, source, config, original, package, contract):
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-authoring-motion11')
    pins = config['pins']
    input_pin = source.pin_file(input_path)
    runtime = source.runtime(original)
    bpy = runtime[0].bpy
    prior_set, prior_write = source.set_modes, source.write
    witness_path = out/'mode-influences.jsonl'
    count = 0
    def emit(value):
        nonlocal count
        count += 1
        with witness_path.open('a') as stream:
            stream.write(json.dumps({'request': count, **value}, separators=(',', ':'))+'\n')
    def set_modes(rig, context, modes):
        refresh_modes(prior_set, bpy, rig, context, modes, emit)
    def write(path, value):
        # Add truthful adapter provenance before each write, never repair an
        # already emitted success receipt after the fact.
        value = {**value, 'recipe': pins['adapter'], 'baseRecipe': pins['sourceRecipe'],
                 'input': input_pin, 'sourceInput': pins['sourceInput']}
        if witness_path.exists():
            value['modeInfluences'] = source.pin_file(witness_path)
            value['modeRequestsVerified'] = count
        if path.name == 'receipt.json':
            assert count == (964 if mode == '--analyze' else 482), count
            for pin in pins.values():
                source.pinned(pin)
        prior_write(path, value)
    source.set_modes, source.write = set_modes, write
    try:
        if mode == '--analyze':
            source.analyze(input_path, out, original, package, contract, runtime)
        else:
            plan = json.loads(plan_path.read_text())
            assert plan['recipe'] == pins['adapter'] and plan['baseRecipe'] == SOURCE04
            assert plan['sourceInput'] == pins['sourceInput'] and plan['input'] == input_pin
            assert plan['modeRequestsVerified'] == 964
            source.pinned(plan['modeInfluences'])
            source.build_actions(input_path, plan_path, out, original, package, contract, runtime)
        assert count == (964 if mode == '--analyze' else 482), count
        for pin in pins.values():
            source.pinned(pin)
    finally:
        source.set_modes, source.write = prior_set, prior_write


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert args and args[0] in ('--analyze', '--build', '--validate-input')
    mode = args[0]
    assert len(args) == {'--analyze': 3, '--build': 4, '--validate-input': 2}[mode]
    path = Path(args[1]).resolve()
    source = frozen()
    config, original, package, contract = read_input(path, source)
    if mode == '--validate-input':
        print(json.dumps({'accepted': False, 'status': 'CONDITIONED05_SOURCE_INPUT_VALID_NATIVE_PENDING',
                          'input': source.pin_file(path)}))
        return
    run(mode, path, Path(args[2]).resolve() if mode == '--build' else None,
        Path(args[-1]).resolve(), source, config, original, package, contract)


if __name__ == '__main__':
    main()
