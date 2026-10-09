"""Small CPU fixtures; no bpy, numpy, native open or heavy numeric job."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as S

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ankle45', HERE/'apply.py')
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

# Exercise CPU comparator using independent witness fixtures and corruptions.
real_read, real_pin, real_write, real_pending = m.read, m.pin, m.write, m.pending_at
path = HERE/'fixture-pending.json'
pins = {'native10': {'path': 'source', 'sha256': 'a'}}
pending = {'acceptedArt': False, 'native': {'path': 'saved', 'sha256': 'b'}}
qualified = {'visibleMeshes': ['RiderJeans', 'RiderBody']}
parts = {name: {'protected': 'PBR+geometry+bind', 'keys': 'exact', 'fields': 'old'}
         for name in ['RiderJeans', 'RiderBody', 'RiderBody__FullAnatomyReference']}
source = {'acceptedArt': False, 'mode': 'source', 'native': pins['native10'], 'pending': 'pending',
          'recipe': 'recipe', 'parts': parts, 'selectedNamedRowsExact': 3318,
          'expectedJeansFields': 'new', 'actions': {'original': 'exact'}, 'rig': {'rest': 'exact'},
          'visibleMeshes': ['RiderBody', 'RiderJeans'], 'sharedSource': {'rows': 2638}}
saved = copy.deepcopy(source); saved.update(mode='saved', native=pending['native'], expectedJeansFields=None)
saved['parts']['RiderJeans']['fields'] = 'new'
result = []
m.pending_at = lambda _: (pending, {'pins': pins}, qualified, {}, rows)
m.pin = lambda p: 'recipe' if str(p).endswith('apply.py') else 'pending'
m.write = lambda p, value: result.append(value)


def comparison(candidate):
    m.read = lambda p: source if p.name == 'source-witness.json' else candidate
    m.compare(path)


comparison(saved)
assert result[-1]['protectedValidationPassed'] is True and result[-1]['acceptedArt'] is False
passed.append('Independent source/saved CPU witness comparison accepts exact initializer')
for label, mutate in [
    ('Protected geometry/PBR mismatch rejected', lambda r: r['parts']['RiderJeans'].update(protected='changed')),
    ('Key coordinate/state mismatch rejected', lambda r: r['parts']['RiderBody'].update(keys='changed')),
    ('Patched field mismatch rejected', lambda r: r['parts']['RiderJeans'].update(fields='changed')),
    ('Unrelated field mismatch rejected', lambda r: r['parts']['RiderBody'].update(fields='changed')),
    ('Action mismatch rejected', lambda r: r['actions'].update(original='changed')),
    ('Native rest mismatch rejected', lambda r: r['rig'].update(rest='changed')),
    ('Shared canonical source mismatch rejected', lambda r: r['sharedSource'].update(rows=2637))]:
    bad = copy.deepcopy(saved); mutate(bad)
    reject(lambda: comparison(bad), label)
print(json.dumps({'passed': True, 'fixtures': passed, 'blenderExecuted': False}, indent=2))
