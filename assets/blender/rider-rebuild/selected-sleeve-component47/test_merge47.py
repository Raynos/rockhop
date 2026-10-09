"""CPU-only transplant/scope/source-fact/failure fixtures; no native execution."""
import ast
import copy
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
m = runpy.run_path(str(HERE/'merge47.py'))
source = m['transplant_source']()
original = m['checked'](m['TRANSPLANT38']).read_text()
a = "    assert bpy.ops.wm.open_mainfile("
b = "    native = out/'"
assert source[source.index(a):source.index(b)] == original[original.index(a):original.index(b)]
ast.parse(source)
assert "mesh.materials[index] = material" in source
assert 'selected_materials = list(obj.data.materials)' in source
assert source.index('original_actions ==') < source.index("bpy.ops.wm.save_as_mainfile")
fixtures = ['Entire frozen38 native-open, mesh/material transplant, scoped ID cleanup, rest/action/pointer checks and scratch release block unchanged']

# Actual source fact: compressed independently qualified11 receipt is byte pinned.
target = m['read'](m['TARGET_PENDING10'])
qualified = m['read'](m['TARGET_QUALIFIED11'])
m['qualifier_gate'](target,qualified)
assert len(qualified['checks']['matrixReplay']) == 2
assert max(r['maximumAffineBoundWithin2mM'] for r in qualified['checks']['matrixReplay']) < .0001
for key,value in [('qualificationRecipe',m['GENERATION10']),('qualifiedPending',{'path':'wrong','sha256':'0'*64})]:
    bad = {**qualified,key:value}
    try: m['qualifier_gate'](target,bad)
    except AssertionError: pass
    else: raise AssertionError(('Accepted qualifier provenance mutation',key))
fixtures.append('Actual compressed qualifier11 receipt and pending10 identity accepted; generation/qualifier conflation and wrong pending rejected')

wardrobe,reference = m['WARDROBE'],m['REFERENCE']
visible = ['RiderBody','RiderJeans','ActualSelectedBoot.L','ActualSelectedBoot.R',*wardrobe]
rest = [{'bone':'original75'}]
contract = {'nativeRest':{'bones':rest}}
def part(label):
    return {'geometryPBRBind':{'sha256':label+'-all-actual-fields'},'namedFieldsSHA256':label+'-skin',
            'keys':{'basis':label+'-key-coordinates'}}
target_report = {'parts':{name:part(name+'-target') for name in visible+[reference]},
                 'rig':{'rest':rest,'activeAction':'RiderGameplayLeanRookie','poseBasis':'exact','frame':[1,1,241]},
                 'actions':{'RiderGameplayLeanRookie':'exact-rookie','RiderGameplayLeanPro':'exact-pro'},
                 'visibleMeshes':sorted(visible),'referenceHidden':True,'maskReference':reference}
source_report = {'parts':{name:part(name+'-source') for name in wardrobe},
                 'rig':None,'actions':{},'visibleMeshes':sorted(wardrobe),'referenceHidden':True,'maskReference':None}
source_report['parts'][reference] = copy.deepcopy(target_report['parts'][reference])
merged_report = copy.deepcopy(target_report)
for name in wardrobe: merged_report['parts'][name] = copy.deepcopy(source_report['parts'][name])
m['compare_reports'](target_report,source_report,merged_report,visible,contract)
fixtures.append('Component donor has only wardrobe+fullref; complete target/merged retain native10 visibility, mask, actions, rest and keys')

cases = []
for name in visible+[reference]:
    bad = copy.deepcopy(merged_report); bad['parts'][name]['geometryPBRBind']['sha256'] = 'changed-PBR-normal-UV-bind-geometry'
    cases.append(('geometry/PBR '+name,target_report,source_report,bad))
for kind in ('namedFieldsSHA256','keys'):
    bad = copy.deepcopy(merged_report); bad['parts']['RiderHoodie'][kind] = 'changed'
    cases.append((kind,target_report,source_report,bad))
for key,value in [('actions',{'RiderGameplayLeanRookie':'changed'}),('maskReference','wrong'),
                  ('visibleMeshes',sorted(wardrobe)),('referenceHidden',False),('rig',{'rest':rest,'frame':[2,1,241]})]:
    bad = copy.deepcopy(merged_report);bad[key] = value
    cases.append((key,target_report,source_report,bad))
bad_source = copy.deepcopy(source_report);bad_source['parts']['RiderBody'] = part('absent')
cases.append(('false full-source scope',target_report,bad_source,merged_report))
bad_source = copy.deepcopy(source_report);bad_source['parts'][reference] = part('different-complete-wearer')
cases.append(('different complete wearer',target_report,bad_source,merged_report))
for label,t,s,g in cases:
    try: m['compare_reports'](t,s,g,visible,contract)
    except AssertionError: pass
    else: raise AssertionError(('Accepted mismatch',label))
fixtures.append(str(len(cases))+' separate donor/protected PBR/normal/UV/geometry, skin/key, action, mask, visibility, rig, scope and fullref mutations rejected')

print(json.dumps({'passed':True,'nativeRunExecuted':False,'actualQualifier11ReceiptSourceFactVerified':True,
                  'fixtures':fixtures,'fullFingerprintChecksRelaxed':False,'mergedReplayExecuted':False},indent=2))
