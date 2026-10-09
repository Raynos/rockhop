"""Qualify the actual saved10 native with bounded Python input lifetimes.

Frozen10 owns saving and snapshot comparison. This separate qualifier owns
only the replay/surface run; its receipt distinguishes both actual recipes.
"""
import gc
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
GENERATION10 = {'path': 'assets/blender/rider-rebuild/selected-seated-anatomical09/gameplay_checkpoint10.py',
                'sha256': 'a4da0f6719e9f43cb97e01d3139be2c279d2c0e3cd695d76f001ae444127fa61'}


def frozen10():
    path = ROOT/GENERATION10['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == GENERATION10['sha256']
    spec = importlib.util.spec_from_file_location('actual_saved_generation10', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def qualify(path, before_path, after_path, out, frozen=None, numpy=None):
    frozen = frozen if frozen is not None else frozen10()
    source = frozen.source
    frozen.fresh(out)
    pending, original, package = frozen.pending_at(path)
    assert pending['recipe'] == GENERATION10
    before, after = [json.loads(p.read_text()) for p in (before_path, after_path)]
    frozen.compare_snapshots(before, after, source.pin_file(path), original['pins']['native'], pending['native'])
    assert before['recipe'] == GENERATION10
    del before, after
    gc.collect()
    if numpy is None:
        import numpy as np
    else:
        np = numpy
    actions = frozen.records(package)
    names = list(package['boneNames'])
    poses = [np.asarray(action['nativeWorldMatrices'], dtype=np.float64) for action in package['actions']]
    del package
    gc.collect()
    print('QUALIFIER11_INPUT_TREES_RELEASED_BEFORE_NATIVE_OPEN', flush=True)
    helper = frozen.helpers(original)
    bpy = helper.bpy
    assert bpy.ops.wm.open_mainfile(filepath=str(source.pinned(pending['native'])), use_scripts=False) == {'FINISHED'}
    rig, objects, contract = frozen.rig_and_objects(helper, original)
    out.mkdir(parents=True)
    replay = source.replay_actions(bpy, np, rig, actions, names, poses, objects, pending['shapeZeroActions'])
    del poses
    gc.collect()
    checks = {'matrixReplay': replay, 'allOriginalProtectedFieldsExact': True,
        'allVertexGroupNamesAndFieldsExact': True, 'originalActionsExact': True,
        'originalKeyCoordinatesExact': True, 'native75RestExact': True,
        'visibleMeshesExact': True, 'shapeActivation': 0, 'checksUseReopenedNative': True}
    source.write_json(out/'checks.json', {'accepted': False, 'checks': checks})
    assert all(row['maximumAffineBoundWithin2mM'] < source.AFFINE_BOUND_M for row in replay), replay
    surfaces, samples = source.save_body_surfaces(helper, rig, actions, pending['shapeZeroActions'], out)
    source.pinned(pending['native'])
    source.write_json(out/'receipt.json', {**pending,
        'status': 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING',
        'recipeSHA256': pending['recipe']['sha256'], 'inputSHA256': pending['input']['sha256'],
        'qualificationRecipe': source.pin_file(Path(__file__)),
        'qualifiedPending': source.pin_file(path),
        'checks': checks, 'bodySurfaceArrays': surfaces, 'surfaceSamples': samples,
        'preservationSnapshots': {'source': source.pin_file(before_path), 'saved': source.pin_file(after_path)},
        'appearanceReview': 'Actual complete-outfit profile/rear film and finite contacts remain pending.'})


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(args) == 4, 'Use PENDING10 SOURCE_SNAPSHOT SAVED_SNAPSHOT FRESH_OUTPUT'
    qualify(*map(lambda value: Path(value).resolve(), args))
