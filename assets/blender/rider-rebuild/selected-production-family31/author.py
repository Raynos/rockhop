"""Scoped boots production using unchanged production25 geometry/field gates.

Parent-only bounded invocation: blender -b -t 2 --python-exit-code 1
  --python author.py -- input.json NEW_OUTPUT_DIRECTORY full|lod
The initial pinned master is opened normally; only this derivative is saved.
"""
import importlib.util
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dependencies as DEP
import witness as W


def label(identifier):
    return identifier.bl_rna.identifier + ':' + identifier.name_full


def isolate(roots):
    graph = DEP.dependencies(bpy.data.user_map())
    kept = DEP.closure(roots, graph)
    expected = {label(i): sorted(label(d) for d in graph.get(i, ())) for i in kept}
    inventory = {kind: len(getattr(bpy.data, kind)) for kind in ('objects', 'meshes', 'materials', 'images')}
    removed = {kind: [] for kind in inventory}
    for obj in list(bpy.data.objects):
        if obj not in kept:
            removed['objects'].append(obj.name_full)
            bpy.data.objects.remove(obj, do_unlink=True)
    # Only zero-user, nondependency IDs are removed. No global orphan purge,
    # user_clear(), fake-user reset, or destructive unlink of live data.
    for kind in ('meshes', 'materials', 'images'):
        collection = getattr(bpy.data, kind)
        for item in list(collection):
            if DEP.removable_unused(item, kept, item.users):
                removed[kind].append(item.name_full)
                collection.remove(item, do_unlink=False)
    actual_graph = DEP.dependencies(bpy.data.user_map())
    actual = {label(i): sorted(label(d) for d in actual_graph.get(i, ())) for i in kept}
    assert actual == expected, 'Retained source dependency graph changed'
    assert set(bpy.data.objects) == {i for i in kept if isinstance(i, bpy.types.Object)}
    bpy.context.view_layer.update()
    return {'beforeCounts': inventory, 'afterCounts': {kind: len(getattr(bpy.data, kind)) for kind in inventory},
            'removed': removed, 'retainedDependencies': actual,
            'remainingUnrequestedData': {kind: [{'name': item.name_full, 'users': item.users,
                'fakeUser': item.use_fake_user} for item in getattr(bpy.data, kind) if item not in kept]
                for kind in ('meshes', 'materials', 'images')}, 'dependencyGraphUnchanged': True}


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 3
    manifest_path = Path(args[0]).resolve(); out = Path(args[1]).resolve(); level = args[2]
    manifest = json.loads(manifest_path.read_text())
    assert manifest['family'] == 'boots' and manifest['sourceObjects'] == ['ActualSelectedBoot.L', 'ActualSelectedBoot.R']
    assert manifest['saveCompressed'] is False
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-production-family31') and not out.exists()
    # Loading this module does not execute its main entry point.
    spec = importlib.util.spec_from_file_location('family31_frozen25', ROOT/manifest['pins']['productionAuthor']['path'])
    engine = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
    for row in manifest['pins'].values(): engine.pin(row)
    config_path = ROOT/manifest['pins']['productionInput']['path']
    config = json.loads(config_path.read_text()); assert level in config['levels']
    config['objects'] = {n: r for n, r in config['objects'].items() if r['family'] == 'boots'}
    assert list(config['objects']) == manifest['sourceObjects']
    bpy.ops.wm.open_mainfile(filepath=str(engine.pin(config['sourceMaster'])))
    armature = bpy.data.objects[config['rig']]; assert len(armature.data.bones) == 75
    sources = {n: bpy.data.objects[n] for n in config['objects']}
    before = W.retained(sources, armature)
    out.mkdir(parents=True)
    isolation = isolate([*sources.values(), armature])
    assert before == W.retained(sources, armature), 'Source identity changed during family isolation'
    report = {'acceptedArt': False, 'status': 'UNACCEPTED_PRODUCTION_GEOMETRY',
        'sourceMaster': config['sourceMaster'], 'recipeSHA256': engine.sha(__file__),
        'baseRecipeSHA256': manifest['pins']['productionAuthor']['sha256'],
        'inputSHA256': engine.sha(config_path), 'wrapperInputSHA256': engine.sha(manifest_path),
        'level': level, 'authoredFamilies': ['boots'], 'objects': {}, 'isolation': isolation,
        'sourceWitness': before, 'sourceIdentityAfterIsolation': True, 'bakeCompleted': False,
        'movingReviewPassed': False, 'denseGeometryPassed': False, 'devicePassed': False,
        'savedCompression': False, 'limits': 'Independent bilateral boots geometry unit. Initial full-master open remains required. No measured memory, bake, complete rider, moving, runtime or device acceptance.'}
    write = lambda: (out/'production.json').write_text(json.dumps(report, indent=2) + '\n')
    write()
    # Identical frozen25 rest preparation; rest/binds and source fields stay exact.
    armature.animation_data_clear()
    for bone in armature.pose.bones: bone.matrix_basis.identity()
    for obj in sources.values():
        if obj.data.shape_keys:
            for key in obj.data.shape_keys.key_blocks: key.value = 0
        obj.hide_set(False)
    bpy.context.view_layer.update()
    targets = []
    for name, source_spec in config['objects'].items():
        print('COMPACT SCOPED ' + level + ' ' + name, flush=True)
        target, row = engine.simplify(sources[name], armature, source_spec, level, config)
        row['transfer'] = engine.transfer(sources[name], target, armature, source_spec, level, config, out)
        targets.append(target); report['objects'][name] = row; write()
    engine.unwrap_family(targets)
    assert before == W.retained(sources, armature), 'Original boot geometry/UV/fields/maps or native75 rest changed'
    count = sum(len(engine.triangles(obj)) for obj in targets)
    assert count <= config['levels'][level]['triangleBudget']
    for source in sources.values(): source.hide_render = True; source.hide_set(True)
    report.update(totalTriangles=count, sourceIdentityAfterProduction=True, realIndependentLOD=level == 'lod')
    native = out/('UNACCEPTED-selected-production-' + level + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False)
    report['native'] = {'path': str(native.relative_to(ROOT)), 'sha256': engine.sha(native)}
    write()
    print(json.dumps({'native': report['native'], 'triangles': count, 'acceptedArt': False}), flush=True)


if __name__ == '__main__': main()
