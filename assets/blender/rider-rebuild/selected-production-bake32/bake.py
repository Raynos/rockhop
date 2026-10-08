"""Boot bake entry point with scoped donor/cage copied-mesh lifetime.

Parent only: blender -b -t 2 --python-exit-code 1 --python bake.py -- INPUT OUT
INPUT pins policy.json and an actual successful family31 geometry report.
Frozen25 still owns every bake operator, shader, cage, map and acceptance gate.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lifetime import OwnedMeshes, BpyProxy


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1048576): h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], row
    return path


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 2
    input_path = Path(args[0]).resolve(); out = Path(args[1]).resolve()
    manifest = json.loads(input_path.read_text())
    policy_path = pin(manifest['policy']); assert policy_path.resolve() == HERE/'policy.json'
    policy = json.loads(policy_path.read_text())
    for row in policy['pins'].values(): pin(row)
    geometry_path = pin(manifest['geometryReport']); geometry = json.loads(geometry_path.read_text())
    assert geometry['status'] == 'UNACCEPTED_PRODUCTION_GEOMETRY' and geometry['authoredFamilies'] == ['boots']
    assert geometry['native']['sha256'] and geometry['sourceIdentityAfterIsolation'] and geometry['sourceIdentityAfterProduction']
    assert set(geometry['objects']) == {'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-rider-production25') and not out.exists()
    spec = importlib.util.spec_from_file_location('bake32_frozen25', pin(policy['pins']['productionBake']))
    engine = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
    tracker = OwnedMeshes(lambda: bpy.data.objects, lambda: bpy.data.meshes)
    original_donor = engine.emission_source; original_cage = engine.cage

    def donor(source, socket):
        obj, materials = original_donor(source, socket)
        tracker.register(obj, source, 'donor')
        return obj, materials

    def cage(target, distance):
        obj = original_cage(target, distance)
        tracker.register(obj, target, 'cage')
        return obj

    # Replace only this imported recipe's module globals. Real bpy.data and
    # bpy.ops remain untouched; all unowned object removals delegate unchanged.
    engine.bpy = BpyProxy(bpy, tracker.remove)
    engine.emission_source = donor; engine.cage = cage
    original_argv = sys.argv
    sys.argv = [str(pin(policy['pins']['productionBake'])), '--', str(pin(policy['pins']['productionInput'])),
                str(geometry_path), str(out), 'boots']
    success = False
    try:
        engine.main()
        assert not tracker.pending and len(tracker.created) == len(tracker.released) == 16
        success = True
    finally:
        sys.argv = original_argv
        if out.exists():
            receipt = {'status': 'UNACCEPTED_BAKE_WITH_OWNED_MESH_RELEASE' if success else 'INCOMPLETE_BAKE',
                'acceptedArt': False, 'wrapperSHA256': sha(Path(__file__)), 'inputSHA256': sha(input_path),
                'sourcePins': {'policy': manifest['policy'], 'geometryReport': manifest['geometryReport'], **policy['pins']},
                'created': tracker.created, 'released': tracker.released,
                'unreleased': [row for _, row in tracker.pending.values()],
                'completedFrozenBake': success, 'limits': 'Scoped temporary allocation lifetime only. Actual maps, shading, moving complete rider, runtime memory/timing and devices remain unaccepted.'}
            (out/'owned-mesh-lifetime.json').write_text(json.dumps(receipt, indent=2) + '\n')
    report_path = out/'bake.json'; report = json.loads(report_path.read_text())
    report.update(baseRecipeSHA256=report['recipeSHA256'], recipeSHA256=sha(Path(__file__)),
                  wrapperInputSHA256=sha(input_path),
                  ownedMeshLifetime={'path': str((out/'owned-mesh-lifetime.json').relative_to(ROOT)),
                                     'sha256': sha(out/'owned-mesh-lifetime.json')})
    report_path.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__': main()
