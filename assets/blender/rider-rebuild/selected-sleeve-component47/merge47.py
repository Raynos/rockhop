"""Explicit47 component-to-gameplay10 merger and independent native witnesses.

Reuses exact transplant38 mesh loop. Actual qualifier11 qualifies target10;
merged actions still require a separate reopened original08 replay. No accepted art, export or player promotion.
"""
import gc
import gzip
import hashlib
import importlib.util
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = runpy.run_path(str(HERE/'component.py'))
ROOT, checked, pin, write = (c[k] for k in ('ROOT', 'checked', 'pin', 'write'))
OUT = ROOT/'harness/out/rider-rebuild/selected-wardrobe-component-merge47'
WARDROBE = ('RiderHoodie', *c['GLOVES'])
REFERENCE = c['REFERENCE']
TRANSPLANT38 = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/integrate.py',
                'sha256': 'dd7e3373b43325149505ad89ce1a5ff5eb74d61776d5fc96df73c62d10d8ab49'}
LINEAGE38 = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/lineage.py',
             'sha256': 'cc1157bf315622e598c2c9051d80d9e707b1082e0275030d2c694f63557c9997'}
GENERATION10 = {'path': 'assets/blender/rider-rebuild/selected-seated-anatomical09/gameplay_checkpoint10.py',
                'sha256': 'a4da0f6719e9f43cb97e01d3139be2c279d2c0e3cd695d76f001ae444127fa61'}
GAMEPLAY08 = {'path': 'assets/blender/rider-rebuild/selected-seated-anatomical09/append-measured-gameplay08.py',
              'sha256': '2399678e7c7fff60f2bc7a3aa609dc439e869a5dc6d6287d8b94f1c98180d1a5'}
TARGET_PENDING10 = {'path': 'harness/out/rider-rebuild/selected-seated-anatomical09/gameplay10/pending.json',
                    'sha256': '3c9492f9567d76c4be8bfebf53ba05f14e7bde22cc11721116d9b8bad6089c13'}
TARGET_NATIVE10 = {'path': 'harness/out/rider-rebuild/selected-seated-anatomical09/gameplay10/UNACCEPTED-selected-gameplay-checkpoint10.blend',
                   'sha256': '35815e62180aabc37588668f426d3709bad139b5f50d6b1f82ccfa60af848ce8'}
QUALIFIER11 = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/gameplay_qualify11.py',
               'sha256': 'aefc733547c24149221675c2992c9ce7904d0524a84a73311ba88b896f4f194f'}
TARGET_QUALIFIED11 = {'path': 'docs/evidence/rider-rebuild/selected-seated-anatomical09/gameplay11-qualified01/receipt.json.gz',
                      'sha256': 'ec8356a639ebbe78612b718d43bec1e89f235278655d3c09c2f972d604995820'}
PENDING = 'UNACCEPTED_WARDROBE_INTEGRATION_SAVED_COMPARISON_PENDING'
QUALIFIED = 'UNACCEPTED_COMPONENT47_TO_NATIVE10_SEPARATE_COMPARISON_PASS_REPLAY_ART_PENDING'


def read(row):
    path = checked(row)
    if path.suffix == '.gz':
        with gzip.open(path, 'rt') as stream: return json.load(stream)
    return json.loads(path.read_text())


def module(row, name):
    spec = importlib.util.spec_from_file_location(name, checked(row))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sleeve_gate(sleeve, config):
    assert sleeve['status'] == c['QUALIFIED'] and sleeve['acceptedArt'] is False
    assert sleeve['protectedValidationPassed'] is sleeve['exact75RestUnchanged'] is True
    assert sleeve['constructedHoodieGeometryAndNamedFieldsExactAfterReopen'] is True
    assert sleeve['protectedValidationStage'] == 'SEPARATE_REOPENED_COMPONENT_NATIVE'
    assert sleeve['nativeStorage'] == {'compressed': False, 'reopenVerified': True}
    assert set(sleeve['scope']) == c['OBJECTS']
    assert set(sleeve['protectedGeometryUnchanged']) == c['PROTECTED']
    assert sleeve['sourcePins'] == config['pins']
    c['source_identity'](config, sleeve)
    for name in ('native', 'pendingReceipt', 'expectedWitness', 'field'):
        checked(sleeve[name])
    checked(sleeve['ancestry']['ancestry'])


def dense_gate(summary, sleeve):
    dense = runpy.run_path(str(HERE/'dense47.py'))
    relations = ('hoodie-full-wearer', 'hoodie-self', 'hoodie-glove-L', 'hoodie-glove-R',
                 'glove-L-full-wearer', 'glove-R-full-wearer')
    assert summary['acceptedArt'] is False and summary['completeStaticRelations'] is True
    assert summary['staticTriangleRelationsPassed'] is True and summary['sourceNative'] == sleeve['native']
    assert set(summary['relations']) == set(relations)
    for relation, row_pin in summary['relations'].items():
        row = read(row_pin)
        assert row['acceptedArt'] is False and row['relation'] == relation
        assert row['status'] == 'PASS_SINGLE_STATIC_RELATION' and row['result']['passed'] is True
        assert row['fullTrianglesNoRadialCrop'] is True and row['sourceNative'] == sleeve['native']
        assert row['recipeSHA256'] == pin(HERE/'dense47.py')['sha256']
        assert row['originalQualifier'] == dense['ORIGINAL']
        cuff = read(sleeve['sourcePins']['cuffInput']); base = read(cuff['baseInput'])
        assert row['actualIntersectionHelper'] == base['intersectionHelper']
        checked(row['actualIntersectionHelper'])


def target_gate(target, qualified=None):
    assert target['accepted'] is False
    assert target['status'] == 'SELECTED_FULL_GAMEPLAY_SAVED_PROTECTED_AND_REPLAY_PENDING'
    assert target['native'] == TARGET_NATIVE10 and target['recipe'] == GENERATION10
    assert target['sourceRecipe'] == GAMEPLAY08
    assert target['nativeFileCompressed'] is False and target['shapeActivation'] == 0
    assert len(target['visibleMeshes']) == len(set(target['visibleMeshes'])) == 7
    assert set(WARDROBE)|{'RiderBody','RiderJeans'} <= set(target['visibleMeshes'])
    assert [a['name'] for a in target['actions']] == ['RiderGameplayLeanRookie','RiderGameplayLeanPro']
    assert all(a['frameRange'] == [1,241] for a in target['actions'])
    for name in ('input','sourceInput','sourceRecipe','recipe','native'):
        checked(target[name])
    for row in target['sourcePins'].values(): checked(row)
    qualified = read(TARGET_QUALIFIED11) if qualified is None else qualified
    qualifier_gate(target, qualified)
    for row in qualified['preservationSnapshots'].values(): checked(row)
    contract = read(target['sourcePins']['contract'])
    assert len(contract['nativeRest']['bones']) == 75
    assert set(contract['specification']['meshNames'].values()) == set(target['visibleMeshes'])
    return contract


def qualifier_gate(target, qualified):
    frozen = runpy.run_path(str(checked(LINEAGE38)))
    frozen['target_gate'](qualified, {'targetNative':TARGET_NATIVE10, 'targetRecipe':GENERATION10,
                                      'targetInput':target['input']})
    assert qualified['recipe'] == GENERATION10 and qualified['qualificationRecipe'] == QUALIFIER11
    checked(QUALIFIER11)
    assert qualified['qualifiedPending'] == TARGET_PENDING10
    for name in ('native','input','recipe','sourceInput','sourceRecipe','sourcePins','actions'):
        assert qualified[name] == target[name], ('Different qualified target generation',name)


def freeze(sleeve_path, dense_path, output):
    sleeve_path, dense_path, output = map(lambda p:Path(p).resolve(), (sleeve_path,dense_path,output))
    assert output.is_relative_to(HERE) and not output.exists()
    sleeve = json.loads(sleeve_path.read_text()); sleeve_gate(sleeve, read(sleeve['input']))
    dense_gate(json.loads(dense_path.read_text()), sleeve)
    target = read(TARGET_PENDING10); target_gate(target)
    write(output, {'acceptedArt':False, 'targetReplayPassed':True,
                   'pins':{'componentReceipt':pin(sleeve_path), 'sleeveInput':sleeve['input'],
                           'sleeveNative':sleeve['native'], 'denseSummary':pin(dense_path),
                           'targetPending':TARGET_PENDING10, 'targetNative':TARGET_NATIVE10,
                           'targetReceipt':TARGET_QUALIFIED11, 'targetQualificationRecipe':QUALIFIER11,
                           'integrationRecipe':pin(__file__), 'lineageHelper':LINEAGE38,
                           'transplantMethod':TRANSPLANT38, 'componentRecipe':pin(HERE/'component.py')}})
    print(json.dumps({'input':pin(output), 'nativeRunExecuted':False}))


def intake(path):
    config = json.loads(Path(path).read_text()); pins = config['pins']
    assert config['acceptedArt'] is False and config['targetReplayPassed'] is True
    assert set(pins) == {'componentReceipt','sleeveInput','sleeveNative','denseSummary','targetPending',
                         'targetNative','targetReceipt','targetQualificationRecipe','integrationRecipe','lineageHelper','transplantMethod','componentRecipe'}
    assert pins['integrationRecipe'] == pin(__file__) and pins['lineageHelper'] == LINEAGE38
    assert pins['transplantMethod'] == TRANSPLANT38 and pins['componentRecipe'] == pin(HERE/'component.py')
    assert pins['targetPending'] == TARGET_PENDING10 and pins['targetNative'] == TARGET_NATIVE10
    assert pins['targetReceipt'] == TARGET_QUALIFIED11 and pins['targetQualificationRecipe'] == QUALIFIER11
    for row in pins.values(): checked(row)
    sleeve = read(pins['componentReceipt']); sleeve_gate(sleeve, read(pins['sleeveInput']))
    assert sleeve['input'] == pins['sleeveInput'] and sleeve['native'] == pins['sleeveNative']
    dense_gate(read(pins['denseSummary']), sleeve)
    target = read(pins['targetPending']); contract = target_gate(target)
    return config, target, sleeve, contract


def transplant_source():
    source = checked(TRANSPLANT38).read_text()
    changes = {'h.pin(__file__)':'h.pin(WRAPPER)',
               "h.ROOT/'harness/out/rider-rebuild/selected-wardrobe-integration38'":
                   "h.ROOT/'harness/out/rider-rebuild/selected-wardrobe-component-merge47'",
               'UNACCEPTED-selected-dressed-wardrobe38.blend':'UNACCEPTED-selected-dressed-component47.blend'}
    for old, new in changes.items():
        assert source.count(old) == (2 if old == 'h.pin(__file__)' else 1)
        source = source.replace(old,new)
    return source


def transplant():
    checked(LINEAGE38)
    namespace = {'__name__':'merge47_exact_transplant38','__file__':str(checked(TRANSPLANT38)), 'WRAPPER':__file__}
    exec(compile(transplant_source(), namespace['__file__'], 'exec'), namespace)
    namespace['h'].read_input = intake
    return namespace


def merge(path, out, bpy):
    transplant()['integrate'](Path(path).resolve(), Path(out).resolve(), bpy)


def pending_at(path):
    path = Path(path).resolve(); assert path.is_relative_to(OUT)
    pending = json.loads(path.read_text())
    assert pending['status'] == PENDING and pending['protectedValidationPassed'] is False
    assert pending['recipe'] == pin(__file__)
    config,target,sleeve,contract = intake(checked(pending['input']))
    assert pending['sourcePins'] == config['pins']
    assert set(pending['changedMeshes']) == set(WARDROBE)
    assert pending['nativeStorage'] == {'compressed':False,'reopenVerified':False}
    checked(pending['native'])
    return pending,config,target,sleeve,contract


def witness(mode, pending_path, bpy):
    pending_path = Path(pending_path).resolve()
    pending,config,target,sleeve,contract = pending_at(pending_path)
    native = pending['native'] if mode == 'merged' else config['pins']['targetNative' if mode == 'target' else 'sleeveNative']
    helper = module(target['sourcePins']['inspectionHelper'],'merge47_inspection')
    assert pin(helper.sculpt.__file__) == target['sourcePins']['sculptRecipe']
    assert pin(helper.base.__file__) == target['sourcePins']['baseRecipe']
    full = module(GAMEPLAY08,'merge47_original08_fields')
    rest = transplant()['rest']
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(native)),use_scripts=False) == {'FINISHED'}
    rig = bpy.data.objects['RiderSkeleton']; assert len(rig.data.bones) == 75
    assert rest(rig) == contract['nativeRest']['bones']
    fingerprint,_ = helper.sculpt.protected_signature()
    names = list(WARDROBE)+[REFERENCE] if mode == 'source' else target['visibleMeshes']+[REFERENCE]
    parts = {}
    for name in names:
        obj = bpy.data.objects[name]
        print('MERGE47_WITNESS '+mode+' '+name,flush=True)
        parts[name] = {'geometryPBRBind':fingerprint(obj), 'namedFieldsSHA256':full.exact_group_digest(obj),
                       'keys':helper.keys_state(obj)}
    visible = sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render)
    assert visible == sorted(WARDROBE if mode == 'source' else target['visibleMeshes'])
    if mode == 'source':
        assert {o.name for o in bpy.data.objects} == c['OBJECTS']
        rig_state,actions,mask = None,{},None
    else:
        active = rig.animation_data; scene = bpy.context.scene
        rig_state = {'rest':rest(rig),'matrix':[list(r) for r in rig.matrix_world],
            'activeAction':active.action.name if active and active.action else None,
            'activeSlot':active.action_slot.identifier if active and active.action_slot else None,
            'poseBasis':{b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones},
            'frame':[scene.frame_current,scene.frame_start,scene.frame_end],
            'fps':[scene.render.fps,scene.render.fps_base]}
        actions = {a.name:digest(helper.action_state(a)) for a in bpy.data.actions}
        mask = bpy.data.objects['RiderBody']['outfitFullBodyReference']; assert mask == REFERENCE
    assert bpy.data.objects[REFERENCE].hide_render
    write(pending_path.parent/(mode+'-witness.json'), {'acceptedArt':False,'status':'SINGLE_COMPONENT47_MERGE_NATIVE_WITNESS_ONLY',
        'mode':mode,'recipe':pin(__file__),'native':native,'pending':pin(pending_path),'input':pending['input'],
        'parts':parts,'actions':actions,'rig':rig_state,'visibleMeshes':visible,
        'referenceHidden':True,'maskReference':mask})


def compare_reports(target, source, merged, visible, contract):
    assert set(target['parts']) == set(merged['parts']) == set(visible)|{REFERENCE}
    assert set(source['parts']) == set(WARDROBE)|{REFERENCE}
    for name in target['parts']:
        expected = source['parts'][name] if name in WARDROBE else target['parts'][name]
        assert merged['parts'][name] == expected, ('Saved field/PBR/normal/UV/bind/key mismatch',name)
    assert source['parts'][REFERENCE] == target['parts'][REFERENCE], 'Different source complete wearer'
    assert target['actions'] == merged['actions'] and target['rig'] == merged['rig']
    assert merged['rig']['rest'] == contract['nativeRest']['bones']
    assert source['rig'] is None and source['actions'] == {} and source['maskReference'] is None
    assert target['visibleMeshes'] == merged['visibleMeshes'] == sorted(visible)
    assert source['visibleMeshes'] == sorted(WARDROBE)
    assert all(r['referenceHidden'] is True for r in (target,source,merged))
    assert target['maskReference'] == merged['maskReference'] == REFERENCE


def compare(pending_path):
    pending_path = Path(pending_path).resolve()
    pending,config,target,sleeve,contract = pending_at(pending_path)
    reports,pins = {},{}
    expected = {'target':config['pins']['targetNative'],'source':config['pins']['sleeveNative'],'merged':pending['native']}
    for mode in expected:
        path = pending_path.parent/(mode+'-witness.json'); pins[mode] = pin(path)
        row = json.loads(path.read_text()); reports[mode] = row
        assert row['status'] == 'SINGLE_COMPONENT47_MERGE_NATIVE_WITNESS_ONLY' and row['acceptedArt'] is False
        assert row['mode'] == mode and row['recipe'] == pin(__file__) and row['native'] == expected[mode]
        assert row['pending'] == pin(pending_path) and row['input'] == pending['input']
        checked(row['native'])
    compare_reports(reports['target'],reports['source'],reports['merged'],target['visibleMeshes'],contract)
    result = {**pending,'status':QUALIFIED,'protectedValidationPassed':True,
              'protectedValidationStage':'THREE_SEPARATE_REOPENED_COMPONENT_TARGET_MERGED_NATIVES',
              'nativeStorage':{'compressed':False,'reopenVerified':True},'witnesses':pins,
              'targetReplayPassed':True,'mergedReplayPassed':False,
              'checks':{'donorWardrobeGeometryPBRUVNormalsNamedFieldsExact':True,
                        'targetUnrelatedMeshesKeysFieldsExact':True,'targetActionsRigRestExact':True,
                        'sameCompleteWearer':True},'pendingReceipt':pin(pending_path)}
    write(pending_path.parent/'receipt.json',result)


def replay(receipt_path, out, bpy):
    receipt_path,out = Path(receipt_path).resolve(),Path(out).resolve()
    assert out.is_relative_to(OUT) and not out.exists()
    receipt = json.loads(receipt_path.read_text()); assert receipt['status'] == QUALIFIED
    pending,config,target,sleeve,contract = pending_at(checked(receipt['pendingReceipt']))
    assert receipt['native'] == pending['native'] and receipt['protectedValidationPassed'] is True
    for row in receipt['witnesses'].values(): checked(row)
    generation = module(GENERATION10,'merge47_exact_saved10_replay_input')
    loaded,original,package = generation.pending_at(checked(config['pins']['targetPending']))
    assert loaded == target
    helper = generation.helpers(original); np = helper.np; full = generation.source
    actions,names = generation.records(package),list(package['boneNames'])
    poses = [np.asarray(a['nativeWorldMatrices'],dtype=np.float64) for a in package['actions']]
    del package; gc.collect()
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(receipt['native'])),use_scripts=False) == {'FINISHED'}
    rig,objects,actual_contract = generation.rig_and_objects(helper,original)
    assert actual_contract == contract
    checks = full.replay_actions(bpy,np,rig,actions,names,poses,objects,target['shapeZeroActions'])
    assert all(r['frames'] == 241 and r['maximumAffineBoundWithin2mM'] < full.AFFINE_BOUND_M for r in checks)
    del poses; gc.collect()
    out.mkdir(parents=True)
    write(out/'receipt.json', {'acceptedArt':False,'status':'UNACCEPTED_MERGED47_ORIGINAL08_MATRIX_REPLAY_PASS_ART_PENDING',
        'native':receipt['native'],'mergeReceipt':pin(receipt_path),'recipe':pin(__file__),
        'originalReplayMethod':GAMEPLAY08,'savedTargetGeneration':GENERATION10,
        'matrixReplay':checks,'shapeActivation':0,'mergedReplayPassed':True,
        'poseEnclosurePassed':False,'movingReviewPassed':False,
        'limits':['Original08 0.1mm affine replay bound unchanged; no garment enclosure or played-art acceptance.',
                  'Actual dressed game forward/back leans, finite contact, export and device review remain required.']})


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'freeze':
        assert len(args) == 4; freeze(*args[1:])
    elif args[0] == 'compare':
        assert len(args) == 2; compare(args[1])
    else:
        import bpy
        if args[0] in ('merge','replay'):
            assert len(args) == 3; {'merge':merge,'replay':replay}[args[0]](*args[1:],bpy)
        else:
            assert len(args) == 2 and args[0] in ('target','source','merged')
            witness(args[0],args[1],bpy)
