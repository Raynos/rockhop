"""Read-only saved native70 qualifier. Parent original guard; no save or bake.

--python qualify.py -- ACTUAL_PRODUCTION70_SHA NEW_REOPEN_OUTPUT
"""
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import intake
import surface

ROOT=intake.ROOT
PRODUCTION=ROOT/'harness/out/rider-rebuild/selected-boot-native70/native01/production.json'
PRODUCTION_SHA='518fe4ce2f7da86adc176c45d3d3393f70d1b1a4daaae0701ff245baa2681465'
NATIVE=PRODUCTION.with_name('UNACCEPTED-selected-production-full.blend')
NATIVE_SHA='ffac10be163895d2ecb76d6552c9e357b86122d522543b7117974884be0ea52c'
ENGINE=intake.BASE/'selected-rider-production25/author.py'
ENGINE_SHA='bc9e03aa6d99eba0d4b5037ceff49424c34ddcde99f0f2aae0f84a5090cbc483'
WITNESS=intake.BASE/'selected-production-family31/witness.py'
WITNESS_SHA='95c7813b503c7d5539b2d7082e14229d484060bacefae294d28160e2c30755d5'
PINS={HERE.parent/'author.py':'e58c32bf6c4a68d41f64295c7e7c1e23e957ae6b2d057496e10db2d6441ce355',
      HERE.parent/'intake.py':'bc1262b93289e95da61d6961b9a3132d65d2ee93ce9b0ff65a992f06608eccd5',
      HERE.parent/'surface.py':'192b3676f97714a89d978db64cabab81363c464d406b9d0ad7d9008c87859d1e',
      ENGINE:ENGINE_SHA,WITNESS:WITNESS_SHA,intake.WITNESS68:intake.WITNESS68_SHA}


def dependencies():
    for path,pin in PINS.items():intake.pin(path,pin)
    author=intake.load(HERE.parent/'author.py','reopen70_author')
    _,previous,*_=author.adapted_source()
    orientation=intake.load(previous.ORIENTATION57,'reopen70_orientation57')
    orientation.verify_proof(previous.PROOF57,previous.PROOF57_SHA)
    witness68=intake.load(intake.WITNESS68,'reopen70_witness68')
    return orientation,witness68


def readonly_transfer_source(orientation):
    raw=orientation.adapted_transfer_source(ENGINE.read_bytes())
    stop='    target.vertex_groups.clear();groups=[target.vertex_groups.new(name=n) for n in names]'
    resume="    file=out/(target.name+'-source-transfer.npz')"
    assert raw.count(stop)==raw.count(resume)==1,'Frozen transfer read-only boundary drift'
    # Every original geometry/skin/FOUR gate precedes this first scene write.
    # Actual70 has no donor/target shape keys; verify that on reopen, separately.
    return raw[:raw.index(stop)]+"    copied=[]\n"+raw[raw.index(resume):]


def array_diff(actual,expected):
    changed=[]
    for key in sorted(set(actual)|set(expected)):
        if key not in actual or key not in expected:changed.append({'key':key,'reason':'missing array'});continue
        a=np.asarray(actual[key]);b=np.asarray(expected[key])
        if a.shape!=b.shape or a.dtype!=b.dtype:changed.append({'key':key,'reason':'shape or dtype'});continue
        if not np.array_equal(a,b,equal_nan=a.dtype.kind in 'fc'):
            changed.append({'key':key,'reason':'array values'})
    return changed


def metadata(receipt,reviewed_sha):
    assert reviewed_sha==PRODUCTION_SHA,'Exact actual70 production SHA required'
    intake.pin(PRODUCTION,reviewed_sha)
    assert receipt['native']=={'path':str(NATIVE.relative_to(ROOT)),'sha256':NATIVE_SHA}
    assert receipt['status']=='UNACCEPTED_SCENE_BUDGET_PENDING' and receipt['restGeometryPassed'] is True
    assert receipt['sourceIdentityAfterProduction'] and receipt['sourceInputBytesUnchanged']
    assert receipt['bakeEligibility']=='LEFT_BOOT_ONLY_NOT_A_BILATERAL_FAMILY32_INPUT'
    for key in ['acceptedArt','sceneBudgetPassed','allocationPassed','bakeCompleted','movingReviewPassed','denseGeometryPassed','devicePassed']:
        assert receipt[key] is False
    assert receipt['constructor']=={'path':str(intake.RECEIPT.relative_to(ROOT)),'sha256':intake.RECEIPT_SHA}
    assert receipt['objects']['ActualSelectedBoot.L']['transfer']['copiedShapeKeys']==[]


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    out=Path(args[1]).resolve()
    assert out.is_relative_to(intake.OUTPUT_BASE) and out!=intake.OUTPUT_BASE and not out.exists()
    out.mkdir(parents=True)
    report={'status':'PARTIAL_SAVED_NATIVE70_BEFORE_ADMISSION','acceptedArt':False,'recipeSHA256':intake.sha(__file__),
            'limits':'Saved left boot rest qualification only; no bilateral, allocation, atlas, posed/contact, moving art or device acceptance.'}
    def write():(out/'reopen.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    def compare(label,actual,expected):
        diff,actual,expected=whole.comparison(actual,expected)
        path=out/(label+'.json');path.write_text(json.dumps({'actual':actual,'expected':expected,'diff':diff},indent=2,allow_nan=False)+'\n')
        report[label]={'equal':diff['equal'],'valueDifferenceCount':diff['valueDifferenceCount'],
                       'evidence':intake.pin(path,intake.sha(path))};write()
        assert diff['equal'],('Saved-native readback changed',label,diff['valueDifferences'])
    def compare_npz(label,actual_pin,expected_pin):
        for pin in [actual_pin,expected_pin]:intake.pin(ROOT/pin['path'],pin['sha256'])
        with np.load(ROOT/actual_pin['path']) as a,np.load(ROOT/expected_pin['path']) as b:changes=array_diff(a,b)
        report[label]={'equal':not changes,'differences':changes,'actual':actual_pin,'expected':expected_pin};write()
        assert not changes,('Saved-native measurement changed',label,changes)
    write()
    try:
        previous=json.loads(PRODUCTION.read_text());metadata(previous,args[0])
        report['production']=intake.pin(PRODUCTION,PRODUCTION_SHA);report['native']=intake.pin(NATIVE,NATIVE_SHA)
        report['admission']=intake.admit(intake.RECEIPT,intake.RECEIPT_SHA,out/'unused-intake-output')
        orientation,whole=dependencies()
        import bpy
        from mathutils import Vector
        engine=intake.load(ENGINE,'reopen70_engine25');witness=intake.load(WITNESS,'reopen70_witness31')
        constructor=json.loads(intake.RECEIPT.read_text());config=json.loads(engine.pin(constructor['censusSourcePins']['productionInput']).read_text())
        report['sourceMaster']=intake.pin(ROOT/previous['sourceMaster']['path'],previous['sourceMaster']['sha256'])
        report['status']='PARTIAL_SAVED_NATIVE70_BEFORE_REOPEN';write()
        bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
        rig=bpy.data.objects[config['rig']];assert len(rig.data.bones)==75
        sources={name:bpy.data.objects[name] for name in previous['sourceWitness']['sources']}
        source=sources['ActualSelectedBoot.L'];target=bpy.data.objects['Production.full.ActualSelectedBoot.L']
        compare('source-before',witness.retained(sources,rig),previous['sourceWitness'])
        target_before=witness.source(target)
        dense=intake.arrays(constructor['sourceArrayPackage']);candidate=intake.arrays(constructor['candidate']);names=constructor['groupNames']
        for obj,arrays in [(source,dense),(target,candidate)]:
            assert np.array_equal(engine.points(obj).astype(np.float32).ravel(),arrays['positions'])
            assert np.array_equal(engine.triangles(obj).ravel(),arrays['triangles'])
            assert np.array_equal(engine.skin_rows(obj,names).astype(np.float32).ravel(),arrays['namedWeights'])
            assert [g.name for g in obj.vertex_groups]==names,'Full named group roster changed'
            assert np.array_equal(np.array([t.material_index for t in obj.data.loop_triangles]),arrays['faceMaterialIds'])
            assert obj.data.shape_keys is None,'Actual70 saved no shape keys'
        _,original=orientation.ancestry(source,target,engine.points(source),engine.points(target))
        assert np.array_equal(original,candidate['originalVertexIds'])
        assert list(target.data.materials)==list(source.data.materials)
        compare('target-pbr',witness.materials([target]),previous['sourceWitness']['materials'])
        assert target.parent==source.parent and target.matrix_world==source.matrix_world and target.matrix_parent_inverse==source.matrix_parent_inverse
        assert len(target.modifiers)==1
        arm=target.modifiers[0];assert arm.type=='ARMATURE' and arm.object==rig and not arm.use_deform_preserve_volume
        assert target.data.uv_layers.active.name=='SelectedProductionAtlas'
        report['savedOriginalArraysFieldsAncestryAndBindExact']=True;report['status']='PARTIAL_SAVED_NATIVE70_BEFORE_TRANSFER_CHECKS';write()
        audit=orientation.kernel.Audit();namespace=dict(vars(engine),correspondence56=audit,ancestry57=orientation.ancestry)
        exec(compile(readonly_transfer_source(orientation),'native70-readonly-transfer','exec'),namespace)
        current=namespace['transfer'](source,target,rig,config['objects']['ActualSelectedBoot.L'],'full',config,out)
        expected=previous['objects']['ActualSelectedBoot.L']['transfer']
        compare_npz('reference-arrays',current['sourceTransfer'],expected['sourceTransfer'])
        compare_npz('four-arrays',current['fourFieldDiagnostics']['arrays'],expected['fourFieldDiagnostics']['arrays'])
        current['sourceTransfer']=expected['sourceTransfer'];current['fourFieldDiagnostics']['arrays']=expected['fourFieldDiagnostics']['arrays']
        compare('transfer-measurements',current,{key:expected[key] for key in current})
        report['correspondence56']=audit.report();report['status']='PARTIAL_SAVED_NATIVE70_BEFORE_SURFACE_CHECKS';write()
        surface.install(namespace,report['admission']['actualProof68'])
        def save_surface(rows):report['sourceSurfaceSamples']=rows;write()
        rows=namespace['surface_checks'](engine,source,target,.001,.25,out,save_surface)
        for label,row in rows.items():
            saved=previous['sourceSurfaceSamples'][label]
            compare_npz(label+'-arrays',row['arrays'],saved['arrays'])
            compare(label+'-measurements',{k:v for k,v in row.items() if k!='arrays'},{k:v for k,v in saved.items() if k!='arrays'})
        compare('source-after',witness.retained(sources,rig),previous['sourceWitness'])
        compare('target-after',witness.source(target),target_before)
        intake.pin(NATIVE,NATIVE_SHA);intake.pin(ROOT/previous['sourceMaster']['path'],previous['sourceMaster']['sha256'])
        report.update(status='SAVED_NATIVE70_REST_READBACK_PASSED_UNACCEPTED',savedNativeBytesUnchanged=True,sourceMasterBytesUnchanged=True);write()
    except Exception as error:
        if 'audit' in locals():report['correspondence56']=audit.report()
        report.update(status='REJECTED_OR_INCOMPLETE_SAVED_NATIVE70_READBACK',failure=repr(error));write();raise


if __name__=='__main__':main()
