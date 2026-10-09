"""Reattach selected glove component in a separate process before sleeve38.

Reuse frozen38's mesh-only transplant and frozen04's independent full-master
qualifier. Actual recipe41 remains explicit; the old strict04 lineage is intact.
"""
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
component = runpy.run_path(str(HERE/'component.py'))
ROOT, pin, checked = (component[name] for name in ('ROOT', 'pin', 'checked'))
GLOVES, REFERENCE = component['GLOVES'], component['REFERENCE']
TRANSPLANT = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/integrate.py',
              'sha256': 'dd7e3373b43325149505ad89ce1a5ff5eb74d61776d5fc96df73c62d10d8ab49'}
LINEAGE = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/lineage.py',
           'sha256': 'cc1157bf315622e598c2c9051d80d9e707b1082e0275030d2c694f63557c9997'}
CHECKPOINT04 = {'path': 'assets/blender/rider-rebuild/selected-sleeve-tailoring27/checkpoint04.py',
                'sha256': 'd9e1c4f0b8fee05cae085482490fa4650c994c1dfc6213c234b3988ae3011406'}


def transplant_source():
    source = checked(TRANSPLANT).read_text()
    substitutions = {
        "h.pin(__file__)": "h.pin(WRAPPER)",
        "h.ROOT/'harness/out/rider-rebuild/selected-wardrobe-integration38'":
            "h.ROOT/'harness/out/rider-rebuild/selected-glove-component41'",
        "UNACCEPTED-selected-dressed-wardrobe38.blend": "UNACCEPTED-selected-gloves-attached41.blend"}
    for old, new in substitutions.items():
        assert source.count(old) == (2 if old == 'h.pin(__file__)' else 1), old
        source = source.replace(old, new)
    return source


def transplant_namespace():
    checked(LINEAGE)
    namespace = {'__name__': 'component41_exact_transplant38',
                 '__file__': str(checked(TRANSPLANT)), 'WRAPPER': __file__}
    exec(compile(transplant_source(), namespace['__file__'], 'exec'), namespace)
    return namespace


def component_gate(receipt):
    assert receipt['status'] == component['QUALIFIED'] and receipt['acceptedArt'] is False
    assert receipt['sourceRecipe'] == pin(HERE/'component.py')
    assert receipt['methodAncestry'] == component['FROZEN04']
    assert receipt['sourceInput'] == component['INPUT10']
    assert set(receipt['objects']) == set(GLOVES)
    assert receipt['protectedValidationPassed'] is receipt['exact75RestUnchanged'] is True
    assert receipt['constructedGloveGeometryAndNamedFieldsExactAfterReopen'] is True
    assert receipt['protectedValidationStage'] == 'SEPARATE_REOPENED_COMPONENT_NATIVE'
    assert receipt['nativeStorage'] == {'compressed': False, 'reopenVerified': True}
    for row in receipt['objects'].values():
        assert row['allSourcePrefixNamedFieldsExact'] is True
        assert row['allNewSourceParentNamedFieldsExactAfterFloat32Storage'] is True


def witness_gate(original, receipt):
    prior = component['read'](receipt['priorInput'])
    assert original['sourceMaster'] == receipt['sourceMaster'] == prior['master']
    assert original['sourceRecipe'] == pin(__file__)
    assert original['sourceInput'] == receipt['priorInput']
    assert original['geometryHelper'] == prior['geometryHelper'] and original['restHelper'] == prior['restHelper']
    visible = {'RiderBody', 'RiderHoodie', 'RiderJeans', *GLOVES, 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}
    assert set(original['visibleMeshes']) == visible and len(original['visibleMeshes']) == 7
    assert set(original['protectedNames']) == (visible-set(GLOVES))|{REFERENCE}
    assert set(original['expectedProtectedGeometry']) == set(original['protectedNames'])
    assert len(original['expectedRest']) == len(original['restForTransplant']) == 75


def witness(out_path, bpy):
    out_path = Path(out_path).resolve()
    assert out_path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-glove-component41')
    engine, config, base, source = component['methods']()
    author = runpy.run_path(str(checked(source['restHelper'])))
    geometry = runpy.run_path(str(checked(source['geometryHelper'])))['geometry']
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(source['master'])), use_scripts=False) == {'FINISHED'}
    names = sorted((engine.B.VISIBLE-set(GLOVES))|{REFERENCE})
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    actual_visible = sorted(obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.hide_render)
    assert actual_visible == sorted(engine.B.VISIBLE)
    # This expensive original scan runs without any live glove construction.
    row = {'sourceMaster': source['master'], 'sourceRecipe': pin(__file__),
           'sourceInput': base['priorInputs'], 'geometryHelper': source['geometryHelper'],
           'restHelper': source['restHelper'], 'protectedNames': names,
           'expectedProtectedGeometry': {name: geometry(bpy.data.objects[name]) for name in names},
           'expectedRest': author['rest'](rig), 'visibleMeshes': actual_visible,
           'restForTransplant': transplant_namespace()['rest'](rig)}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    component['write'](out_path, row)


def freeze(component_path, witness_path, out_path):
    receipt = json.loads(Path(component_path).read_text()); component_gate(receipt)
    original = json.loads(Path(witness_path).read_text())
    witness_gate(original, receipt)
    pins = {'componentReceipt': pin(component_path), 'sleeveNative': receipt['native'],
            'targetNative': original['sourceMaster'], 'sourceWitness': pin(witness_path),
            'integrationRecipe': pin(__file__), 'lineageHelper': LINEAGE}
    for row in pins.values(): checked(row)
    component['write'](Path(out_path).resolve(), {'acceptedArt': False, 'pins': pins})


def intake(input_path):
    config = json.loads(Path(input_path).read_text()); assert config['acceptedArt'] is False
    pins = config['pins']
    assert set(pins) == {'componentReceipt', 'sleeveNative', 'targetNative', 'sourceWitness',
                         'integrationRecipe', 'lineageHelper'}
    assert pins['integrationRecipe'] == pin(__file__) and pins['lineageHelper'] == LINEAGE
    for row in pins.values(): checked(row)
    receipt = component['read'](pins['componentReceipt']); component_gate(receipt)
    original = component['read'](pins['sourceWitness'])
    witness_gate(original, receipt)
    assert pins['targetNative'] == original['sourceMaster'] == receipt['sourceMaster']
    assert pins['sleeveNative'] == receipt['native']
    return config, {'visibleMeshes': original['visibleMeshes']}, receipt, {'nativeRest': {'bones': original['restForTransplant']}}


def assemble(input_path, out, bpy):
    input_path, out = Path(input_path).resolve(), Path(out).resolve()
    config, target, receipt, contract = intake(input_path)
    namespace = transplant_namespace()
    # This is an explicit new intake adapter. Original lineage38's strict04
    # gate remains unchanged; no receipt is relabeled as the frozen04 recipe.
    namespace['h'].WARDROBE = GLOVES
    namespace['h'].read_input = intake
    namespace['integrate'](input_path, out, bpy)
    raw = json.loads((out/'pending.json').read_text())
    checkpoint = runpy.run_path(str(checked(CHECKPOINT04)))
    original = component['read'](config['pins']['sourceWitness'])
    expected = {**original, 'status': 'EXPECTED_PRE_GLOVE_WITNESS_ONLY',
                'protectedValidationPassed': False, 'sourceRecipe': pin(__file__),
                'exact75RestUnchangedBeforeSave': True}
    witness_path = out/'protected-before-gloves.json'; component['write'](witness_path, expected)
    # Native already exists. Reuse the exact04 separately-reopened protected
    # comparison schema with truthful actual41/method04 provenance.
    glove_objects = {name: {**row['ancestry'], 'vertices': row['vertices'], 'polygons': row['triangles']}
                     for name, row in receipt['objects'].items()}
    pending = {'status': checkpoint['PENDING'], 'acceptedArt': False, 'sourceMaster': receipt['sourceMaster'],
               'sourceRecipe': pin(__file__), 'methodAncestry': component['FROZEN04'],
               'componentRecipe': receipt['sourceRecipe'], 'componentReceipt': config['pins']['componentReceipt'],
               'transplantMethod': TRANSPLANT, 'assemblyInput': pin(input_path),
               'protectedValidationPassed': False, 'geometryGatesPassed': False, 'movingReviewPassed': False,
               'native': raw['native'], 'gloveObjects': glove_objects,
               'expectedWitness': pin(witness_path), 'exact75RestUnchangedBeforeSave': True,
               'nativeStorage': {'compressed': False, 'reopenVerified': False}}
    component['write'](out/'gloves-only-pending.json', pending)


def qualify(pending_path, bpy):
    pending_path = Path(pending_path).resolve()
    pending = json.loads(pending_path.read_text())
    assert pending['sourceRecipe'] == pin(__file__) and pending['methodAncestry'] == component['FROZEN04']
    receipt = component['read'](pending['componentReceipt']); component_gate(receipt)
    assert pending['componentRecipe'] == receipt['sourceRecipe'] and pending['transplantMethod'] == TRANSPLANT
    intake(checked(pending['assemblyInput']))
    checkpoint = runpy.run_path(str(checked(CHECKPOINT04)))
    original = component['read'](pending['expectedWitness'])
    geometry = runpy.run_path(str(checked(original['geometryHelper'])))['geometry']
    def load_helper(path):
        namespace = runpy.run_path(path)
        if Path(path).resolve() == checked(original['restHelper']):
            exact_rest = namespace['rest']
            def rest_with_component_check(rig):
                # The unchanged qualifier calls rest only after open_mainfile.
                for name in GLOVES:
                    assert geometry(bpy.data.objects[name]) == receipt['expectedConstructedGeometry'][name], (
                        'Selected component changed during full-master transplant', name)
                return exact_rest(rig)
            namespace['rest'] = rest_with_component_check
        return namespace
    checkpoint['qualify'](pending_path, bpy, load_helper)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]
    if args[0] == 'freeze':
        assert len(args) == 4
        freeze(*args[1:])
    else:
        import bpy
        if args[0] == 'assemble':
            assert len(args) == 3
            assemble(*args[1:], bpy)
        else:
            assert len(args) == 2 and args[0] in {'witness', 'qualify'}
            {'witness': witness, 'qualify': qualify}[args[0]](args[1], bpy)
