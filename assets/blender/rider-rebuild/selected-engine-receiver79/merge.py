"""Thin reviewed51/47/38 merger reuse for actual compact77 + unchanged52."""
import runpy
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = runpy.run_path(str(HERE/'component.py'))
BASE51 = {'path':'assets/blender/rider-rebuild/selected-distal-wardrobe51/merge51.py',
          'sha256':'e69052249c0e4317cc8a5f69dddeed4c7e605bba890e7136565f6b1b5a49aea0'}
STAGE = 'SOURCE_REOPEN_TARGET_AT_MERGE_ASSEMBLY_REOPEN'


def wrapper():
    source = c['checked'](BASE51).read_text()
    changes = {
        'selected-distal-wardrobe51/merge':'selected-engine-receiver79/merge',
        "HERE/'dense51.py'":"HERE/'dense.py'",
        'UNACCEPTED-selected-dressed-distal51.blend':'UNACCEPTED-selected-dressed-receiver79.blend',
        'UNACCEPTED_DISTAL51_TO_NATIVE52_SEPARATE_COMPARISON_PASS_REPLAY_ART_PENDING':
            'UNACCEPTED_RECEIVER79_TO_NATIVE52_SEPARATE_COMPARISON_PASS_REPLAY_ART_PENDING',
        'SINGLE_DISTAL51_MERGE_NATIVE_WITNESS_ONLY':'SINGLE_RECEIVER79_MERGE_NATIVE_WITNESS_ONLY',
        'UNACCEPTED_MERGED51_ORIGINAL08_MATRIX_REPLAY_PASS_ART_PENDING':
            'UNACCEPTED_MERGED79_ORIGINAL08_MATRIX_REPLAY_PASS_ART_PENDING'}
    for old,new in changes.items():
        assert source.count(old) >= 1,old
        source = source.replace(old,new)
    # Preserve actual10's shape-zero list in the exact52 derivative replay.
    source = source.replace("'actions':pending10['actions'],'gameplaySourcePending':pending10,",
        "'actions':pending10['actions'],'shapeZeroActions':pending10['shapeZeroActions'],'gameplaySourcePending':pending10,")
    source = source.replace('THREE_SEPARATE_REOPENED_COMPONENT_TARGET_MERGED_NATIVES',STAGE)
    # The reviewed51 factory retains exact47 code and its own scoped globals.
    # Its final donor verification resolves this owned component.py instead.
    namespace = {'__name__':'receiver79_reviewed51','__file__':__file__}
    exec(compile(source,str(c['checked'](BASE51)),'exec'),namespace)
    original_source = namespace['transformed_source']
    namespace['transformed_source'] = lambda: original_source().replace(
        'THREE_SEPARATE_REOPENED_COMPONENT_TARGET_MERGED_NATIVES',STAGE)
    original_factory = namespace['methods']
    def factory():
        m = original_factory()
        m['intake'] = intake
        m['write_intake_witnesses'] = write_intake_witnesses
        m['capture_target'] = lambda target,contract,bpy: runpy.run_path(str(HERE/'witness.py'))['capture']('target',target,contract,bpy,m)
        original_transplant = m['transplant_source']
        def transplant_source():
            src = original_transplant()
            old = 'selected_materials = list(obj.data.materials)'
            assert src.count(old) == 1
            src = src.replace(old,"selected_materials = list(donor.data.materials) if name == 'RiderHoodie' else list(obj.data.materials)")
            old_count = 'assert len(donor.data.materials) == len(obj.data.materials) > 0'
            assert src.count(old_count) == 1
            src = src.replace(old_count,"assert len(donor.data.materials) > 0 and (name == 'RiderHoodie' or len(donor.data.materials) == len(obj.data.materials))")
            anchor = "    originals = {obj.name:"
            assert src.count(anchor) == 1
            src = src.replace(anchor,"    target_witness = capture_target(target,contract,bpy)\n"+anchor)
            anchor = "    h.io['write'](out/'pending.json', result)"
            assert src.count(anchor) == 1
            return src.replace(anchor,anchor+"\n    write_intake_witnesses(out/'pending.json',target_witness)")
        m['transplant_source'] = transplant_source
        original_loader = m['transplant']
        def transplant():
            result = original_loader()
            result.update(capture_target=m['capture_target'],write_intake_witnesses=write_intake_witnesses)
            return result
        m['transplant'] = transplant
        return m
    namespace['methods'] = factory
    return namespace


def methods(): return wrapper()['methods']()


def eligibility(dense,sleeve,m):
    if dense is None:
        return {'mode':'PRIVATE_DIAGNOSTIC_CONTACT_PENDING','staticContactPassed':False,
                'productionQualified':False,'movingReviewPassed':False}
    if dense['sourceNative'] == sleeve['native']:
        m['dense_gate'](dense,sleeve)
    else:
        # Reuse only actual79 results with observed inputs on an independently
        # qualified texture-only bake of the same artist77 native.
        contact = runpy.run_path(str(HERE/'contact.py'))
        baked = c['authority'](sleeve,'bakeQualificationRecipe','bakeReceipt')
        relations = {'hoodie-full-wearer','hoodie-self','hoodie-glove-L','hoodie-glove-R',
                     'glove-L-full-wearer','glove-R-full-wearer'}
        assert dense['acceptedArt'] is False and dense['completeStaticRelations'] is dense['staticTriangleRelationsPassed'] is True
        assert set(dense['relations']) == relations
        helper = c['read'](c['read'](sleeve['sourcePins']['cuffInput'])['baseInput'])['intersectionHelper']
        original = runpy.run_path(str(HERE/'dense.py'))['ORIGINAL']
        for relation,pin in dense['relations'].items():
            row = c['read'](pin)
            assert row['acceptedArt'] is False and row['relation'] == relation
            assert row['status'] == 'PASS_SINGLE_STATIC_RELATION' and row['result']['passed'] is True
            assert row['sourceNative'] == dense['sourceNative'] and row['fullTrianglesNoRadialCrop'] is True
            assert row['recipeSHA256'] == c['pin'](HERE/'dense.py')['sha256'] and row['originalQualifier'] == original
            assert row['actualIntersectionHelper'] == helper
            c['checked'](helper);contact['reusable'](row,baked)
    return {'mode':'STATIC_CONTACT_QUALIFIED_MOTION_PENDING','staticContactPassed':True,
            'productionQualified':False,'movingReviewPassed':False}


def freeze(component_path,dense_path,target52_path,output):
    output = Path(output).resolve();assert output.is_relative_to(HERE) and not output.exists()
    w=wrapper();m=w['methods']();pin=c['pin'];read=m['read']
    sleeve=read(pin(component_path));c['donor_gate'](sleeve,read(sleeve['input']))
    dense_pin = None if dense_path == '-' else pin(dense_path)
    state=eligibility(read(dense_pin) if dense_pin else None,sleeve,m)
    target52=read(pin(target52_path));w['target52_gate'](target52,target52_path)
    pins={'componentReceipt':pin(component_path),'sleeveInput':sleeve['input'],'sleeveNative':sleeve['native'],
        'targetReceipt52':pin(target52_path),'targetNative':target52['native'],
        'targetPending':m['TARGET_PENDING10'],'targetAncestorQualified11':m['TARGET_QUALIFIED11'],
        'targetRecipe52':target52['recipe'],'targetInput52':target52['input'],
        'integrationRecipe':pin(__file__),'lineageHelper':m['LINEAGE38'],'transplantMethod':m['TRANSPLANT38'],
        'mergeMethodAncestry':w['MERGE47'],'componentRecipe':pin(HERE/'component.py'),
        'assemblyWitnessRecipe':pin(HERE/'witness.py')}
    if dense_pin:pins['denseSummary']=dense_pin
    c['write'](output,{'acceptedArt':False,'targetReplayInheritedByExactActions':True,'eligibility':state,'pins':pins})


def intake(path):
    config=json.loads(Path(path).read_text());pins=config['pins'];w=wrapper();m=w['methods']();pin=c['pin'];read=m['read']
    assert config['acceptedArt'] is False and config['targetReplayInheritedByExactActions'] is True
    assert set(pins)=={'componentReceipt','sleeveInput','sleeveNative','targetReceipt52','targetNative',
        'targetPending','targetAncestorQualified11','targetRecipe52','targetInput52','integrationRecipe','lineageHelper',
        'transplantMethod','mergeMethodAncestry','componentRecipe','assemblyWitnessRecipe'}|({'denseSummary'} if config['eligibility']['staticContactPassed'] else set())
    assert pins['integrationRecipe']==pin(__file__) and pins['componentRecipe']==pin(HERE/'component.py')
    assert pins['assemblyWitnessRecipe']==pin(HERE/'witness.py')
    assert pins['lineageHelper']==m['LINEAGE38'] and pins['transplantMethod']==m['TRANSPLANT38']
    assert pins['mergeMethodAncestry']==w['MERGE47'] and pins['targetPending']==m['TARGET_PENDING10']
    assert pins['targetAncestorQualified11']==m['TARGET_QUALIFIED11']
    for row in pins.values():c['checked'](row)
    sleeve=read(pins['componentReceipt']);c['donor_gate'](sleeve,read(pins['sleeveInput']))
    assert sleeve['input']==pins['sleeveInput'] and sleeve['native']==pins['sleeveNative']
    assert config['eligibility']==eligibility(read(pins['denseSummary']) if 'denseSummary' in pins else None,sleeve,m)
    receipt52=read(pins['targetReceipt52']);target,contract=w['target52_gate'](receipt52,c['checked'](pins['targetReceipt52']))
    assert pins['targetNative']==receipt52['native'] and pins['targetRecipe52']==receipt52['recipe']
    assert pins['targetInput52']==receipt52['input']
    return config,target,sleeve,contract


def write_intake_witnesses(pending_path,target_witness):
    m=methods();pending,config,target,sleeve,contract=m['pending_at'](pending_path)
    baked=c['authority'](sleeve,'bakeQualificationRecipe','bakeReceipt')
    assert baked['assemblyWitnessRecipe']==config['pins']['assemblyWitnessRecipe']
    for mode,payload in [('target',target_witness),('source',baked['assemblySourceWitness'])]:
        c['write'](pending_path.parent/(mode+'-witness.json'),{**payload,'acceptedArt':False,
            'status':'SINGLE_RECEIVER79_MERGE_NATIVE_WITNESS_ONLY','mode':mode,'recipe':c['pin'](__file__),
            'native':config['pins']['targetNative' if mode=='target' else 'sleeveNative'],
            'pending':c['pin'](pending_path),'input':pending['input'],
            'observedDuring':'EXACT52_MERGE_OPEN' if mode=='target' else 'INDEPENDENT_BAKE79_REOPEN'})


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    m = wrapper()
    if args[0] == 'freeze': freeze(*args[1:])
    elif args[0] == 'compare': m['methods']()['compare'](*args[1:])
    else:
        import bpy
        inner = m['methods']()
        if args[0] in ('merge','replay'): inner[args[0]](*args[1:],bpy)
        else:
            assert args[0] == 'merged', 'Source recorded at bake reopen; target recorded at merge open'
            inner['witness'](args[0],args[1],bpy)
