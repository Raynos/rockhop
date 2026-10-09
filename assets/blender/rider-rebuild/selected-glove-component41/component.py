"""Selected bilateral glove component: exact frozen04 math, selective native load.

Parent's unchanged serial CPU2/global memory guard only. No normal-player export.
blender -b -t 2 --python-exit-code 1 --python component.py -- build FRESH_OUT
blender -b -t 2 --python-exit-code 1 --python component.py -- qualify PENDING_JSON
"""
import gc
import importlib.util
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
io = runpy.run_path(str(ROOT/'assets/blender/rider-rebuild/selected-sleeve-tailoring27/checkpoint04.py'))
pin, checked = io['pin'], io['checked']
FROZEN04 = {'path': 'assets/blender/rider-rebuild/selected-sleeve-tailoring27/gloves_only04.py',
            'sha256': 'c1a98001b74ad0ad445f856a2f423d320bf98ec1b9e315126eba218bb55ce002'}
INPUT10 = {'path': 'assets/blender/rider-rebuild/selected-cuff-topology10/input09.json',
           'sha256': '076ce70b228895af9cd75ea9148abca85c57996938c19691fb6d3bdc9049d0f4'}
GLOVES = ('ActualSelectedGlove.L', 'ActualSelectedGlove.R')
REFERENCE = 'RiderBody__FullAnatomyReference'
REQUESTED = (*GLOVES, 'RiderSkeleton', REFERENCE)
PENDING = 'UNACCEPTED_SELECTED_GLOVE_COMPONENT_SAVED_REOPEN_PENDING'
QUALIFIED = 'UNACCEPTED_SELECTED_GLOVE_COMPONENT_REOPENED_DENSE_AND_MOTION_PENDING'


def read(row):
    return json.loads(checked(row).read_text())


def write(path, row):
    assert not path.exists(), ('Refuse overwrite', str(path))
    path.write_text(json.dumps(row, indent=2)+'\n')


def methods():
    # Import the actual frozen04 ancestry chain, including its constructor10
    # native topology proof. Its full-scene main/protected scan is never called.
    spec = importlib.util.spec_from_file_location('component41_frozen04', checked(FROZEN04))
    frozen = importlib.util.module_from_spec(spec); spec.loader.exec_module(frozen)
    engine = frozen.prior.prior.prior.engine
    config = read(INPUT10)
    engine.Q = runpy.run_path(str(checked(config['finiteBearingHelper'])))
    engine.G = runpy.run_path(str(checked(config['cuffReconstructionHelper'])))
    spec = importlib.util.spec_from_file_location('component41_exact_surgery', checked(config['baseConstructor']))
    engine.B = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine.B)
    B = engine.B
    base = read(config['baseInput']); source = read(base['priorInputs'])
    B.V = runpy.run_path(str(checked(base['volumeHelper'])))
    B.A = runpy.run_path(str(checked(base['intersectionHelper'])))
    B.hit_radius = engine.Q['hit_radius']
    frozen.prior.lifetime['install'](B, lambda row: print('COMPONENT41_LIFETIME '+json.dumps(row), flush=True))
    # The unchanged wrapper installed no fit override at import time. Reuse its
    # captured original function, not a copy of the reconstruction implementation.
    assert frozen.prior.prior.saved_full_cuff is engine.full_cuff
    return engine, config, base, source


def append_component(bpy, master):
    assert not list(bpy.data.objects), 'Use a new empty background process'
    with bpy.data.libraries.load(str(master), link=False) as (available, loaded):
        assert set(REQUESTED) <= set(available.objects)
        loaded.objects = list(REQUESTED)
    assert all(obj is not None for obj in loaded.objects)
    # Blender resolves native mesh, rig, material/node/image dependencies.
    # Fail explicitly if an object-level dependency expands beyond this scope.
    assert {obj.name for obj in bpy.data.objects} == set(REQUESTED), (
        'Unexpected selected component object dependency', sorted(obj.name for obj in bpy.data.objects))
    for obj in loaded.objects:
        bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()


def metadata(obj, packed_maps):
    return {'groups': [group.name for group in obj.vertex_groups],
            'materials': [material.name if material else None for material in obj.data.materials],
            'packedMaps': packed_maps(obj), 'matrixWorld': [list(row) for row in obj.matrix_world],
            'parent': obj.parent.name if obj.parent else None,
            'modifiers': [(mod.name, mod.type,
                           mod.object.name if hasattr(mod, 'object') and mod.object else None,
                           mod.show_viewport, mod.show_render) for mod in obj.modifiers]}


def build(out, bpy):
    out = Path(out).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-glove-component41') and not out.exists()
    engine, config, base, source = methods(); B = engine.B; np = B.np
    bpy.ops.wm.read_factory_settings(use_empty=True)
    append_component(bpy, checked(source['master']))
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    author = runpy.run_path(str(checked(source['restHelper'])))
    geometry = runpy.run_path(str(checked(source['geometryHelper'])))['geometry']
    protected = {'rest': author['rest'](rig), 'fullReference': geometry(bpy.data.objects[REFERENCE]),
                 'gloves': {name: metadata(bpy.data.objects[name], author['packed_maps']) for name in GLOVES}}
    assert all(protected['gloves'][name]['packedMaps'] for name in GLOVES)
    placement = read(source['placement'])
    settings = dict(base['settings']); settings.update(config['settings'])
    settings['sourceWrist'] = placement['sourceRest']['wrist']
    with np.load(checked(source['originalGloveDense'])) as dense:
        source_glove = dense['vertices']
    _, bp = B.A['points'](bpy.data.objects[REFERENCE]); bf = B.A['faces'](bpy.data.objects[REFERENCE])
    out.mkdir(parents=True)
    report = {'status': PENDING, 'acceptedArt': False, 'geometryGatesPassed': False,
              'movingReviewPassed': False, 'protectedValidationPassed': False,
              'sourceMaster': source['master'], 'sourceRecipe': pin(__file__), 'methodAncestry': FROZEN04,
              'sourceInput': INPUT10, 'baseInput': config['baseInput'], 'priorInput': base['priorInputs'],
              'protectedBefore': protected, 'objects': {}, 'hands': {},
              'scope': 'Two selected highres gloves, native75 rig and immutable full-body fit reference only. No full-outfit preservation or sleeve claim.'}
    for side, name in zip(('L', 'R'), GLOVES):
        print('COMPONENT41_CONSTRUCT '+name, flush=True)
        with np.load(checked(source['guideArrays'][side])) as dump:
            _, x, z = B.V['cuff_frame'](dump, placement['hands'][side])
            profile = B.V['BodyProfile'](bp, bf, dump['wristWorld'], dump['forearmAxisWorld'], x, z,
                                       {'bodyProfileStations': 49, 'bodyProfileAngles': 96})
            wearer = engine.body_tree(bp, bf, profile)
            obj = bpy.data.objects[name]
            surgery = B.Surgery(obj, source_glove)
            row = engine.full_cuff(surgery, dump, placement['hands'][side], profile, wearer, settings)
            cleanup = engine.remove_inherited_local_degenerates(surgery, {side: profile})
            gp, gf, ancestry = surgery.finish(out)
            report['objects'][name] = ancestry
            report['hands'][side] = {'glove': row, 'gloveDegenerates': cleanup}
            del gp, gf, surgery, wearer, profile
            gc.collect()
    # Save the useful native component immediately after both exact finish calls.
    # No completed-glove BVH, outfit fingerprint scan, sleeve load or solve.
    native = out/'UNACCEPTED-selected-gloves-component.blend'
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
    with native.open('rb') as stream: assert stream.read(7) == b'BLENDER'
    report['native'] = pin(native)
    report['nativeStorage'] = {'compressed': False, 'reopenVerified': False}
    write(out/'component-raw.json', report)
    # The native already exists before these full selected-glove fingerprints.
    # The exact reused finish assertions establish source/new named fields;
    # these fingerprints let the independent reopen verify serialization.
    report['expectedConstructedGeometry'] = {name: geometry(bpy.data.objects[name]) for name in GLOVES}
    report['conditionedRayQueries'] = engine.Q['receipts']
    write(out/'component-pending.json', report)
    print('COMPONENT41_SAVED '+json.dumps(report['native']), flush=True)


def qualify(pending_path, bpy):
    pending_path = Path(pending_path).resolve()
    assert pending_path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-glove-component41')
    report = json.loads(pending_path.read_text())
    assert report['status'] == PENDING and report['acceptedArt'] is False
    assert report['sourceRecipe'] == pin(__file__) and report['methodAncestry'] == FROZEN04
    assert report['sourceInput'] == INPUT10 and set(report['objects']) == set(GLOVES)
    engine, config, base, source = methods()
    assert report['sourceMaster'] == source['master']
    assert report['baseInput'] == config['baseInput'] and report['priorInput'] == base['priorInputs']
    checked(source['master'])
    bpy.ops.wm.open_mainfile(filepath=str(checked(report['native'])), use_scripts=False)
    assert {obj.name for obj in bpy.data.objects} == set(REQUESTED)
    author = runpy.run_path(str(checked(source['restHelper'])))
    geometry = runpy.run_path(str(checked(source['geometryHelper'])))['geometry']
    before = report['protectedBefore']; rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert json.loads(json.dumps(author['rest'](rig))) == before['rest']
    assert geometry(bpy.data.objects[REFERENCE]) == before['fullReference']
    for name, row in report['objects'].items():
        obj = bpy.data.objects[name]
        assert json.loads(json.dumps(metadata(obj, author['packed_maps']))) == before['gloves'][name]
        assert len(obj.data.vertices) == row['vertices'] and len(obj.data.polygons) == row['triangles']
        checked(row['ancestry'])
        assert row['allSourcePrefixNamedFieldsExact'] is True
        assert row['allNewSourceParentNamedFieldsExactAfterFloat32Storage'] is True
        assert geometry(obj) == report['expectedConstructedGeometry'][name], ('Reopened glove fingerprint mismatch', name)
    report.update(status=QUALIFIED, protectedValidationPassed=True,
                  protectedValidationStage='SEPARATE_REOPENED_COMPONENT_NATIVE',
                  exact75RestUnchanged=True, fullReferenceUnchanged=True,
                  sourcePrefixNamedFieldsExactAfterReopen=True,
                  constructedGloveGeometryAndNamedFieldsExactAfterReopen=True, pendingReceipt=pin(pending_path))
    report['nativeStorage']['reopenVerified'] = True
    write(pending_path.with_name('component-qualified.json'), report)


if __name__ == '__main__':
    import bpy
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 2 and args[0] in {'build', 'qualify'}
    {'build': build, 'qualify': qualify}[args[0]](args[1], bpy)
