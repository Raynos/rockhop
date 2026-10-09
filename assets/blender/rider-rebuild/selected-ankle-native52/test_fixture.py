"""Small CPU fixtures; no bpy, numpy, native open or heavy numeric job."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as S

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ankle52', HERE/'apply.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows = json.loads((HERE.parent/'selected-ankle-field42/field-rows.json').read_text())
m.validate_rows(rows)
passed = ['Actual shared 3318 named rows pass strict support/finite/normalization/ID checks']


def reject(call, label):
    try: call()
    except AssertionError: passed.append(label)
    else: raise AssertionError('Fixture unexpectedly passed: '+label)


for label, change in [
    ('Duplicate native ID rejected', lambda r: r[1].update(nativeID=r[0]['nativeID'])),
    ('Pruned support rejected', lambda r: r[0]['after'].pop('DEF-foot.L')),
    ('Wrong side rejected', lambda r: r[0]['before'].update({'DEF-shin.R.001': 1})),
    ('Nonfinite weight rejected', lambda r: r[0]['after'].update({'DEF-foot.L': float('nan')}))]:
    bad = copy.deepcopy(rows); change(bad)
    reject(lambda: m.validate_rows(bad), label)


def obj(values):
    return S(vertex_groups=[S(index=i, name=n) for i, n in enumerate(('shin', 'foot', 'selection'))],
             data=S(vertices=[S(index=i, groups=[S(group=g, weight=w) for g, w in row]) for i, row in enumerate(values)]))


before = obj([[(0, 1), (2, .5)], [(0, 1), (2, 0)]])
after = obj([[(2, .5), (1, .75), (0, .25)], [(0, 1), (2, 0)]])
expected = m.canonical_digest(before, {0: {'shin': .25, 'foot': .75}}, {'shin', 'foot'})
assert expected == m.canonical_digest(after)
passed.append('Predicted complete fields equal reordered saved memberships without pruning')
for label, values in [
    ('Selected nondeform field change detected', [[(0, .25), (1, .75), (2, .6)], [(0, 1), (2, 0)]]),
    ('Unselected upper field change detected', [[(0, .25), (1, .75), (2, .5)], [(0, .9), (2, 0)]]),
    ('Unselected zero membership deletion detected', [[(0, .25), (1, .75), (2, .5)], [(0, 1)]])]:
    assert expected != m.canonical_digest(obj(values)); passed.append(label)

tree = ast.parse((HERE/'apply.py').read_text())
save = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'save')
calls = [n for n in ast.walk(save) if isinstance(n, ast.Call)]
raw = next(n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'save_as_mainfile')
assert any(k.arg == 'compress' and isinstance(k.value, ast.Constant) and k.value.value is False for k in raw.keywords)
assert not any(isinstance(n.func, ast.Name) and n.func.id in ('canonical_digest', 'witness', 'shared_source', 'fingerprint') for n in calls)
assert not any(isinstance(n.func, ast.Attribute) and n.func.attr in ('action_state', 'exact_group_digest', 'protected_signature') for n in calls)
passed.append('Save stage contains RAW save and no protected/full-field/action witness scans')

# Missing canonical groups are appended without changing an existing index.
inventory = [{'index': i, 'name': n} for i, n in enumerate(['DEF-shin.L.001', 'DEF-shin.R.001', 'selection'])]
bones = {'DEF-shin.L.001', 'DEF-shin.R.001', 'DEF-foot.L', 'DEF-foot.R'}
plan = m.group_plan(inventory, bones, rows)
assert plan['appended'] == [{'index': 3, 'name': 'DEF-foot.L'}, {'index': 4, 'name': 'DEF-foot.R'}]
m.validate_inventory(plan, rows)
passed.append('Only two missing canonical foot groups append after exact original indices')
assert m.group_plan(plan['after'], bones, rows)['appended'] == []
passed.append('Existing canonical foot groups are retained without duplicate additions')
reject(lambda: m.group_plan(inventory, bones-{'DEF-foot.R'}, rows), 'Destination group must be a canonical rig bone')
for label, mutate in [
    ('Original group index change rejected', lambda p: p['after'][0].update(index=1)),
    ('Original group name change rejected', lambda p: p['after'][0].update(name='renamed')),
    ('Append noncanonical bone rejected', lambda p: p['appended'][0].update(name='DEF-toe.L')),
    ('Extra empty group rejected', lambda p: p['after'].append({'index': 5, 'name': 'new-selection'}))]:
    bad = copy.deepcopy(plan); mutate(bad)
    reject(lambda: m.validate_inventory(bad, rows), label)

# Full canonical field prediction includes virtual appended groups and exact
# non-target/zero/nondeform fields; tiny representable weights are not pruned.
def named_obj(names, values):
    return S(vertex_groups=[S(index=i, name=n) for i, n in enumerate(names)],
             data=S(vertices=[S(index=i, groups=[S(group=g, weight=w) for g, w in row]) for i, row in enumerate(values)]))
old_names = [g['name'] for g in inventory]; new_names = [g['name'] for g in plan['after']]
small_before = named_obj(old_names, [[(0,1), (2,.5)], [(1,1), (2,0)], [(0,.75)]])
patch = {0: {'DEF-shin.L.001': .25, 'DEF-foot.L': .75}, 1: {'DEF-shin.R.001': 1-2**-20, 'DEF-foot.R': 2**-20}}
small_after = named_obj(new_names, [[(2,.5), (3,.75), (0,.25)], [(2,0), (4,2**-20), (1,1-2**-20)], [(0,.75)]])
expected_fields = m.canonical_digest(small_before, patch, bones, plan['after'])
assert expected_fields == m.canonical_digest(small_after)
passed.append('Virtual post-append fields match exact replacements and preserve tiny positive support')
bad = copy.deepcopy(small_after); bad.data.vertices[2].groups[0].weight = .5
assert expected_fields != m.canonical_digest(bad)
passed.append('Changed non-target named field detected with appended destination groups')
bad = copy.deepcopy(small_after); bad.data.vertices[0].groups[0].weight = .6
assert expected_fields != m.canonical_digest(bad)
passed.append('Changed selected nondeform field detected with appended groups')
bad = copy.deepcopy(small_after); bad.vertex_groups[0].name = 'renamed'
assert expected_fields != m.canonical_digest(bad)
passed.append('Canonical field digest detects original group rename')

# Audit the exact pinned helper transform without bpy or numerical execution.
original_path = HERE.parent/'selected-complete-engine01/export-private.py'
original_ast = ast.parse(original_path.read_text())
function = next(n for n in original_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'part_fingerprint')
original_source = ast.get_source_segment(original_path.read_text(), function)+'\n'
transformed = m.field_free_fingerprint_source(original_source)
assert 'vertex.groups' not in transformed and 'obj.vertex_groups' not in transformed
for marker in ["array('positions'", "'edgeVertices'", "mesh.attributes", "mesh.uv_layers", "'evaluatedCornerNormals'", "materials = []", "'parentInverse'", "'modifiers'"]:
    assert marker in transformed, marker
passed.append('Jeans fingerprint transformation retains positions/topology/attributes/UV/normals/PBR/bind')
reject(lambda: m.field_free_fingerprint_source(original_source.replace('for vertex in mesh.vertices:', 'for vertex in modified.vertices:')), 'Drift in exact field block rejected')

# Independent CPU witness comparison, exercised through downstream helper.
source_native = {'path': 'source-native', 'sha256': 'source-sha'}
pending = {'acceptedArt': False, 'status': m.STATUS, 'native': {'path': 'saved-native', 'sha256': 'saved-sha'},
           'groupInventory': plan, 'changedNativeVertices': 3318, 'rankPruning': False}
qualified = {'visibleMeshes': ['RiderJeans', 'RiderBody']}
parts = {name: {'protected': 'PBR+geometry+bind', 'keys': 'exact', 'fields': 'old'}
         for name in ['RiderJeans', 'RiderBody', 'RiderBody__FullAnatomyReference']}
source = {'acceptedArt': False, 'mode': 'source', 'native': source_native, 'pending': 'pending',
          'recipe': 'recipe', 'parts': parts, 'selectedNamedRowsExact': 3318,
          'expectedJeansFields': expected_fields, 'actions': {'original': 'exact'}, 'rig': {'rest': 'exact'},
          'visibleMeshes': ['RiderBody', 'RiderJeans'], 'sharedSource': {'rows': 2638},
          'jeansGroupInventory': plan['before'], 'groupInventory': plan,
          'protectedJeansDefinition': 'Pinned original geometry/PBR/bind fingerprint minus exact group block; inventory and all memberships qualified separately'}
saved = copy.deepcopy(source); saved.update(mode='saved', native=pending['native'], expectedJeansFields=None, jeansGroupInventory=plan['after'])
saved['parts']['RiderJeans']['fields'] = expected_fields

def comparison(candidate):
    m.validate_witness_pair(pending, source, candidate, qualified, 'pending', 'recipe', source_native, rows)

comparison(saved)
passed.append('Independent witness pair accepts declared append plus exact42 complete fields')
for label, mutate in [
    ('Unrelated geometry/PBR mismatch rejected', lambda r: r['parts']['RiderBody'].update(protected='changed')),
    ('Jeans geometry/PBR mismatch rejected', lambda r: r['parts']['RiderJeans'].update(protected='changed')),
    ('Key coordinate/state mismatch rejected', lambda r: r['parts']['RiderBody'].update(keys='changed')),
    ('Patched field mismatch rejected', lambda r: r['parts']['RiderJeans'].update(fields='changed')),
    ('Unrelated complete named field mismatch rejected', lambda r: r['parts']['RiderBody'].update(fields='changed')),
    ('Action mismatch rejected', lambda r: r['actions'].update(original='changed')),
    ('Native rest mismatch rejected', lambda r: r['rig'].update(rest='changed')),
    ('Shared canonical source mismatch rejected', lambda r: r['sharedSource'].update(rows=2637)),
    ('Saved original group index mismatch rejected', lambda r: r['jeansGroupInventory'][0].update(index=9)),
    ('Saved original group name mismatch rejected', lambda r: r['jeansGroupInventory'][0].update(name='renamed')),
    ('Saved noncanonical appended group rejected', lambda r: r['jeansGroupInventory'][-1].update(name='DEF-toe.R'))]:
    bad = copy.deepcopy(saved); mutate(bad)
    reject(lambda: comparison(bad), label)
# Downstream receipt API checks pinned witness identity before accepting fields.
real_read, real_checked, real_pin, real_pending = m.read, m.checked, m.pin, m.pending_at
receipt_path = m.ROOT/'harness/out/rider-rebuild/selected-ankle-native52/fixture/receipt.json'
pending.update(recipe='recipe', input='input', sourcePins={'native10': source_native})
receipt = {**pending, 'status': 'ANKLE52_EXACT_REOPENED_FIELDS_PROTECTED_PASS_ART_PENDING',
           'nativeReopened': True, 'protectedValidationPassed': True,
           'witnesses': {'source': 'source-pin', 'saved': 'saved-pin'}}
m.pending_at = lambda p: (pending, {'pins': pending['sourcePins']}, qualified, {}, rows)
m.pin = lambda p: 'recipe' if Path(p).name == 'apply.py' else 'input' if Path(p).name == 'input.json' else 'pending' if Path(p).name == 'pending.json' else 'source-pin' if Path(p).name == 'source-witness.json' else 'saved-pin'
m.checked = lambda value: Path('source-witness.json') if value == 'source-pin' else Path('saved-witness.json')
def intake(candidate):
    m.read = lambda p: candidate if p.name == 'receipt.json' else source if p.name == 'source-witness.json' else saved
    return m.qualify_receipt(receipt_path)
assert intake(receipt) == receipt
passed.append('CPU-only downstream receipt intake returns exact qualified receipt dict')
bad = copy.deepcopy(receipt); bad['witnesses']['saved'] = 'wrong-pin'
reject(lambda: intake(bad), 'Downstream changed witness file pin rejected')
bad = copy.deepcopy(receipt); bad['nativeReopened'] = False
reject(lambda: intake(bad), 'Downstream unreopened native claim rejected')
bad = copy.deepcopy(receipt); bad['sourcePins']['native10'] = {'path':'other', 'sha256':'other'}
reject(lambda: intake(bad), 'Downstream changed source ancestry rejected')
m.read, m.checked, m.pin, m.pending_at = real_read, real_checked, real_pin, real_pending
print(json.dumps({'passed': True, 'fixtureCount': len(passed), 'fixtures': passed, 'blenderExecuted': False}, indent=2))
