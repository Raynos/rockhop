"""Bounded adapter integrity checks; no Blender, browser, native hashing or art."""
import ast
import importlib.util
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = runpy.run_path(str(HERE/'component.py'))
merge = runpy.run_path(str(HERE/'merge.py'))
m = merge['methods']()
dense = runpy.run_path(str(HERE/'dense.py'))
p = runpy.run_path(str(HERE/'proof.py'))
export = runpy.run_path(str(HERE/'export.py'))
groups = []


def code_function(source,name):
    return next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name==name)


def equal_function(a,b,name):
    assert ast.dump(code_function(a,name),include_attributes=False)==ast.dump(code_function(b,name),include_attributes=False),name


original28 = c['checked'](dense['ORIGINAL']).read_text()
changed28 = dense['transformed_source']()
a="    arrays = {key: (helper['points']"
b="    row = {'acceptedArt': False"
assert original28[original28.index(a):original28.index(b)]==changed28[changed28.index(a):changed28.index(b)]
assert 'fullTrianglesNoRadialCrop' in changed28
assert 'native_gate' in (HERE/'dense.py').read_text()
groups.append('same six full triangle relations and measurement-only native gate')

original38 = c['checked'](m['TRANSPLANT38']).read_text()
transplant = m['transplant_source']()
old='selected_materials = list(obj.data.materials)'
new="selected_materials = list(donor.data.materials) if name == 'RiderHoodie' else list(obj.data.materials)"
assert transplant.count(new)==1 and old not in transplant
normalized=transplant.replace(new,old).replace('h.pin(WRAPPER)','h.pin(__file__)').replace(
    "h.ROOT/'harness/out/rider-rebuild/selected-engine-receiver79/merge'",
    "h.ROOT/'harness/out/rider-rebuild/selected-wardrobe-integration38'").replace(
    'UNACCEPTED-selected-dressed-receiver79.blend','UNACCEPTED-selected-dressed-wardrobe38.blend')
assert normalized==original38
groups.append('exact38 mesh transplant except protected baked hoodie material retention')

original47 = c['checked'](m['MERGE47']).read_text() if 'MERGE47' in m else c['checked'](merge['wrapper']()['MERGE47']).read_text()
for name in ('compare_reports',):
    assert ast.dump(code_function(original47,name),include_attributes=False)==ast.dump(code_function(
        merge['wrapper']()['transformed_source'](),name),include_attributes=False)
assert m['WARDROBE']==('RiderHoodie',*c['GLOVES'])
assert set(m['c']['OBJECTS'])==c['OBJECTS']
assert 'ankle52' in p['assembly'].__code__.co_names or p['MERGE']==HERE/'merge.py'
groups.append('full wardrobe protected comparison, exact52 target and hidden dense donor scope')

original71 = c['checked'](export['BASE71']).read_text()
changed71 = export['transformed_source']()
for name in ('bone_fields','accessor','skin_rest','corner_table','corner_residual','canonical_triangles','decoded_transport'):
    equal_function(original71,changed71,name)
assert p['KIND']=='qualified-selected-receiver77-native52-fields'
assert 'PROXIMAL69' not in p['transformed_source']()
assert 'donor_gate' in p['transformed_source']()
assert p['OUT']==c['ROOT']/'harness/out/rider-rebuild/selected-engine-receiver79'
groups.append('exact71 decoded fields/corners/topology/rest; real77 replaces rejected C2 admission')

try:c['native_gate']({'acceptedArt':False},{'pins':{}})
except AssertionError as e:assert 'Missing actual artist77 independent qualifier' in str(e)
else:raise AssertionError('Admitted absent native qualification')
try:c['authority']({},'bakeQualificationRecipe','bakeReceipt')
except AssertionError as e:assert 'Missing actual' in str(e)
else:raise AssertionError('Admitted absent genuine bake')
groups.append('absent native or genuine bake authority explicitly rejected')

# Execute the actual donor assertions from native_gate with distinct renamed
# and original-name witnesses. This catches the name-bound hash regression
# without mocking a valid native receipt or hashing a native.
gate_node = code_function((HERE/'component.py').read_text(),'native_gate')
donor_assertions = [node for node in gate_node.body if isinstance(node,ast.Assert)
                    and 'donor' in ast.unparse(node)]
assert len(donor_assertions)==2
checks=compile(ast.fix_missing_locations(ast.Module(body=donor_assertions,type_ignores=[])),
               '<actual79-donor-assertions>','exec')
source={'expectedHoodieGeometry':'original-name-fingerprint','expectedHoodieMetadata':{'PBR':'selected'}}
expected={'donorGeometry':'renamed-donor-fingerprint',
          'donorOriginalNamedGeometry':'original-name-fingerprint','donorMetadata':{'PBR':'selected'}}
exec(checks,{'source':source,'expected':expected})
assert expected['donorGeometry']=='renamed-donor-fingerprint'
for key,value in [('donorOriginalNamedGeometry','wrong-original-name'),('donorMetadata',{'PBR':'wrong'})]:
    try:exec(checks,{'source':source,'expected':{**expected,key:value}})
    except AssertionError:pass
    else:raise AssertionError(('Changed selected donor witness admitted',key))
groups.append('distinct renamed donor hash retained; original-name geometry and selected PBR exact')
print(json.dumps({'status':'SOURCE_ADAPTER_CHECKS_ONLY','count':len(groups),'groups':groups,
                  'nativeExecuted':False,'browserExecuted':False,'candidateAdmitted':False}))
