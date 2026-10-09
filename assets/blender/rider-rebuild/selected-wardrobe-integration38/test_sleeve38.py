"""CPU-light failure fixtures only; fake bytes are not a native Blender run."""
import ast
import contextlib
import io
import json
import runpy
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'sleeve_checkpoint.py'))
wrapper = runpy.run_path(str(HERE/'sleeve38.py'))
changed = wrapper['transformed_source']()
original = wrapper['checkpoint']['checked'](wrapper['ORIGINAL']).read_text()
stop = '    assert before == {o.name: geometry(o) for o in protected}\n'
assert changed[:original.index(stop)] == original[:original.index(stop)]
assert "compress=True" not in changed and 'protectedGeometryUnchanged' not in changed
assert changed.index('del hp, hf, surgery') < changed.index("checkpoint['save_pending']")
assert 'gc.collect()' in changed
ast.parse(changed)
fixtures = ['Exact original28 geometry prefix unchanged; scratch release precedes raw save; no after-scan or compressed save remains']

with tempfile.TemporaryDirectory(prefix='sleeve38-fixture-') as tmp, contextlib.redirect_stdout(io.StringIO()):
    root = Path(tmp).resolve()
    for value in h.values():
        if callable(value) and hasattr(value, '__globals__'):
            value.__globals__['ROOT'] = root
    def file(name, value='fixture-only'):
        path = root/name
        path.write_text(json.dumps(value) if not isinstance(value, str) else value)
        return h['pin'](path)
    constructor = file('sleeve38.py')
    checkpoint_helper = file('sleeve_checkpoint.py')
    file('qualify-sleeve38.py')
    original_recipe = file('original28.py')
    for value in h.values():
        if callable(value) and hasattr(value, '__globals__'):
            value.__globals__.update(HERE=root, ORIGINAL=original_recipe)
    prior = {'master': file('original.blend'), 'geometryHelper': file('geometry.py'), 'restHelper': file('rest.py')}
    native = file('gloves.blend')
    glove = {'native': native, 'status': 'UNACCEPTED_GLOVES_CONSTRUCTED_SLEEVE_NOT_AUTHORED',
             'protectedValidationPassed': True, 'protectedValidationStage': 'SEPARATE_REOPENED_NATIVE',
             'sourceMaster': prior['master']}
    config = {'acceptedArt': False, 'pins': {'gloveNative': native, 'gloveReceipt': file('glove.json', glove),
                'priorInputs': file('prior.json', prior), 'constructor38': constructor,
                'checkpointHelper38': checkpoint_helper}}
    config_path = root/'input.json'; config_path.write_text(json.dumps(config))
    names = ('ActualSelectedGlove.L', 'ActualSelectedGlove.R', 'RiderBody__FullAnatomyReference', 'RiderJeans')
    expected = {'geometry': {n: n+'-original' for n in names}, 'rest': [['bone', 75]]}
    objects = {n: NS(type='MESH', name=n) for n in names}
    objects['RiderSkeleton'] = NS(data=NS(bones=range(75)))
    events = []
    def save(**kwargs):
        assert kwargs['compress'] is False
        path = Path(kwargs['filepath'])
        assert (path.parent/'protected-before-sleeve.json').is_file()
        path.write_bytes(b'BLENDER fake fixture')
        events.append('save')
        return {'FINISHED'}
    def reopen(**kwargs):
        assert kwargs['use_scripts'] is False
        events.append('reopen')
        return {'FINISHED'}
    bpy = NS(data=NS(filepath=str(root/'gloves.blend'), objects=objects),
             ops=NS(wm=NS(save_as_mainfile=save, open_mainfile=reopen)))
    def load(path):
        def geometry(obj):
            assert events[-1] == 'reopen', 'Geometry scan before checkpoint reopen'
            return expected['geometry'][obj.name]
        return {'geometry': geometry} if path.endswith('geometry.py') else {'rest': lambda rig: expected['rest']}
    def pending(name):
        out = root/'harness/out/rider-rebuild/selected-sleeve-rebuild28'/name; out.mkdir(parents=True)
        report = {'acceptedArt': False, 'ancestry': {'ancestry': file(name+'-ancestry.npz')},
                  'field': file(name+'-field.npz'), 'recipeSHA256': constructor['sha256'],
                  'originalConstructor': original_recipe}
        return out, h['save_pending'](out, config_path, config, expected, report, bpy)
    out, result = pending('good')
    assert events == ['save'] and result['protectedValidationPassed'] is False
    assert not (out/'construction.json').exists()
    qualified = h['qualify'](out/'construction-pending.json', bpy, load)
    assert qualified['protectedValidationPassed'] is True and qualified['nativeStorage']['reopenVerified'] is True
    assert not any(qualified[k] for k in ('acceptedArt', 'geometryGatesPassed', 'poseEnclosurePassed', 'movingReviewPassed'))
    assert json.loads((out/'construction-pending.json').read_text())['protectedValidationPassed'] is False
    fixtures.append('Only separate reopened comparison issues construction.json; all six dense and motion gates stay false')
    for kind in ('geometry', 'rest'):
        out, result = pending(kind)
        def bad_load(path):
            result = load(path)
            if kind in result:
                result[kind] = lambda obj: 'MISMATCH'
            return result
        try: h['qualify'](out/'construction-pending.json', bpy, bad_load)
        except AssertionError: pass
        else: raise AssertionError('Accepted mismatch '+kind)
        assert not (out/'construction.json').exists() and (out/'construction-pending.json').exists()
        fixtures.append('Reopened '+kind+' mismatch preserves pending checkpoint and emits no qualified receipt')
    out, _ = pending('changed-native')
    saved = root/result['native']['path']
    actual = json.loads((out/'construction-pending.json').read_text())
    (root/actual['native']['path']).write_bytes(b'changed native bytes')
    try: h['qualify'](out/'construction-pending.json', bpy, load)
    except AssertionError: pass
    else: raise AssertionError('Accepted changed native bytes')
    assert not (out/'construction.json').exists()
    fixtures.append('Same-path native byte mutation is rejected before a qualified receipt')
    out, _ = pending('wrong-recipe')
    path = out/'construction-pending.json'; actual = json.loads(path.read_text())
    actual['recipeSHA256'] = '0'*64; path.write_text(json.dumps(actual))
    try: h['qualify'](path, bpy, load)
    except AssertionError: pass
    else: raise AssertionError('Accepted pending result with different actual recipe identity')
    assert not (out/'construction.json').exists()
    fixtures.append('Result recipe SHA must equal the pinned current constructor38 source; filenames alone cannot qualify')
    out, _ = pending('changed-master')
    (root/prior['master']['path']).write_bytes(b'changed original source')
    try: h['qualify'](out/'construction-pending.json', bpy, load)
    except AssertionError: pass
    else: raise AssertionError('Accepted changed source bytes')
    assert not (out/'construction.json').exists()
    fixtures.append('Same-path original source byte mutation is rejected before reopening the saved candidate')

print(json.dumps({'passed': True, 'nativeRunExecuted': False, 'fixtures': fixtures,
                  'fixtureBytesAreNotNativeBlenderData': True}, indent=2))
