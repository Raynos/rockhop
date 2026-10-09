"""CPU-only source/gate/failure fixtures. Fake bytes are never native proof."""
import ast
import contextlib
import io
import json
import runpy
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'component.py'))
w = runpy.run_path(str(HERE/'sleeve47.py'))
source = w['transformed_source']()
original = h['checked'](w['ORIGINAL']).read_text()
start = "    wearer = bpy.data.objects['RiderBody__FullAnatomyReference']\n"
end = '    hp, hf, ancestry = surgery.finish(out)\n'
assert source[source.index(start):source.index(end)+len(end)] == original[original.index(start):original.index(end)+len(end)]
ast.parse(source)
assert "== helper47['MESHES']" in source and "n in helper47['PROTECTED']" in source
assert '== B.VISIBLE' not in source
assert 'compress=True' not in source
assert source.index('gc.collect()') < source.index("helper47['save_pending']")
assert "helper47['pin'](WRAPPER)" in source and "checkpoint['save_pending']" not in source
assert h['PROTECTED'] == {*h['GLOVES'], h['REFERENCE']}
assert h['OBJECTS'] == h['PROTECTED']|{'RiderHoodie', 'RiderSkeleton'}
fixtures = ['Exact original28 complete reference, continuous fit, cuff, cleanup and finish block unchanged',
            'Only present component meshes protected; lifetime38 releases scratch before raw save; explicit helper47 avoids local receipt shadowing']

# Exercise the real source-gate against existing independently qualified41.
actual = json.loads((h['ROOT']/'harness/out/rider-rebuild/selected-glove-component41/component01/component-qualified.json').read_text())
h['component41_gate'](actual)
for key, value in [('sourceRecipe', {'path':'wrong.py','sha256':'0'*64}),
                   ('protectedValidationPassed', False), ('status', h['INTAKE_QUALIFIED'])]:
    bad = {**actual, key:value}
    try: h['component41_gate'](bad)
    except AssertionError: pass
    else: raise AssertionError(('Accepted false component source gate', key))
fixtures.append('Real qualified41 accepted; false source recipe, validation and relabeled status rejected')
for pins in ({'component47':{'path':'wrong','sha256':'0'*64}},
             {'component47':h['pin'](HERE/'component.py'), 'constructor47':{'path':'wrong','sha256':'0'*64}}):
    try: h['source_identity']({'pins':pins}, {})
    except AssertionError: pass
    else: raise AssertionError('Accepted recipe identity mutation')
fixtures.append('Actual47 helper and constructor identity mutations rejected before intake/source reopening')
dense = runpy.run_path(str(HERE/'dense47.py'))
dense_source = dense['transformed_source'](); ast.parse(dense_source)
dense_original = h['checked'](dense['ORIGINAL']).read_text()
a = "    arrays = {key:"; b = "    row = {'acceptedArt'"
assert dense_source[dense_source.index(a):dense_source.index(b)] == dense_original[dense_original.index(a):dense_original.index(b)]
fixtures.append('All six dense28 full-triangle relation calculations unchanged; only output scope/provenance adapted')

with tempfile.TemporaryDirectory(prefix='sleeve47-fixtures-') as tmp, contextlib.redirect_stdout(io.StringIO()):
    root = Path(tmp).resolve()
    def file(name, data):
        p = root/name; p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes): p.write_bytes(data)
        else: p.write_text(json.dumps(data))
        return h['pin'](p)
    # Restrict mocks to source-pins/intake helpers; run actual save/reopen logic.
    for f in h.values():
        if callable(f) and hasattr(f, '__globals__'):
            f.__globals__.update(ROOT=root, OUT=root/'out')
    recipe = file('recipe.py', 'fixture-only')
    out_base = root/'out'; out_base.mkdir()
    expected = {'geometry': {n:n+'-exact' for n in h['PROTECTED']}, 'rest': ['native75']}
    meta = {'fields':'original-materials-groups-world-and-packed-maps'}
    initial_native = file('intake.blend', b'BLENDER fixture-only')
    intake_receipt = file('intake.json', {'expectedHoodieMetadata':meta})
    prior = file('prior.json', {'fixture':True})
    config = {'pins':{'gloveNative':initial_native, 'gloveReceipt':intake_receipt, 'priorInputs':prior}}
    config_pin = file('config.json', config)
    objects = {n:NS(name=n) for n in h['OBJECTS']}
    events, mismatch = [], [None]
    def geometry(obj):
        assert events[-1] in ('save', 'reopen'), 'Expensive scan before raw native save'
        if mismatch[0] == obj.name: return 'WRONG'
        return expected['geometry'].get(obj.name, 'rebuilt-hoodie-exact')
    def rest(rig): return ['WRONG'] if mismatch[0] == 'rest' else expected['rest']
    def save(**kwargs):
        assert kwargs['compress'] is False
        Path(kwargs['filepath']).write_bytes(b'BLENDER fake-fixture-only')
        events.append('save'); return {'FINISHED'}
    def reopen(**kwargs):
        assert kwargs['use_scripts'] is False
        events.append('reopen'); return {'FINISHED'}
    bpy = NS(data=NS(filepath=str(root/initial_native['path']), objects=objects),
             ops=NS(wm=NS(save_as_mainfile=save, open_mainfile=reopen)))
    bindings = {'source_identity':lambda c,r:None, 'scoped':lambda bpy:objects['RiderSkeleton'],
                'helpers':lambda prior:({'rest':rest,'packed_maps':None},geometry),
                'metadata':lambda obj,packed:meta}
    for f in h.values():
        if callable(f) and hasattr(f, '__globals__'): f.__globals__.update(bindings)
    def pending(name):
        out = out_base/name; out.mkdir()
        report = {'acceptedArt':False, 'ancestry':{'ancestry':file(name+'-ancestry.npz', b'fixture'),
                  'allSourcePrefixNamedFieldsExact':True, 'allNewSourceParentNamedFieldsExactAfterFloat32Storage':True},
                  'field':file(name+'-field.npz', b'fixture')}
        h['save_pending'](out, root/config_pin['path'], config, expected, report, bpy)
        return out
    out = pending('good')
    assert events == ['save'] and (out/'construction-raw.json').is_file()
    assert not (out/'construction.json').exists()
    h['qualify'](out/'construction-pending.json', bpy)
    result = json.loads((out/'construction.json').read_text())
    assert result['status'] == h['QUALIFIED'] and result['nativeStorage']['reopenVerified'] is True
    assert set(result['protectedGeometryUnchanged']) == h['PROTECTED']
    assert not any(result[k] for k in ('acceptedArt','geometryGatesPassed','poseEnclosurePassed','movingReviewPassed'))
    fixtures.append('Raw save precedes every completed-hoodie fingerprint; separate reopen alone issues component qualification; dense/art/motion remain false')
    for kind in ('rest', *sorted(h['PROTECTED']), 'RiderHoodie', 'bytes'):
        out = pending('bad-'+kind.replace('.','-'))
        if kind == 'bytes':
            row = json.loads((out/'construction-pending.json').read_text())
            (root/row['native']['path']).write_bytes(b'changed')
        else: mismatch[0] = kind
        try: h['qualify'](out/'construction-pending.json', bpy)
        except AssertionError: pass
        else: raise AssertionError(('Accepted mismatch',kind))
        assert not (out/'construction.json').exists() and (out/'construction-raw.json').exists()
        mismatch[0] = None
    fixtures.append('Reopened rest, each glove, full reference, rebuilt hoodie and native byte mismatch rejected without losing raw checkpoint')

print(json.dumps({'passed':True, 'nativeRunExecuted':False, 'fixtureBytesAreNotNativeBlenderData':True,
                  'fixtures':fixtures},indent=2))
