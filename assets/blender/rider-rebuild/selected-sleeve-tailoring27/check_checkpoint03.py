"""Execute the real save helper and wrapper with explicit fake Blender I/O."""
import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import runpy
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
fake_bpy = SimpleNamespace(data=SimpleNamespace(objects={}), ops=SimpleNamespace(wm=SimpleNamespace()))
for side in ('L', 'R'):
    fake_bpy.data.objects['ActualSelectedGlove.'+side] = SimpleNamespace(
        type='MESH', vertex_groups=['native_weight'],
        data=SimpleNamespace(vertices=range(3), polygons=range(1)))
fixtures = []
with patch.dict(sys.modules, {'bpy': fake_bpy}), contextlib.redirect_stdout(io.StringIO()):
    helper = runpy.run_path(str(HERE/'checkpoint03.py'))
    with tempfile.TemporaryDirectory(prefix='gloves-checkpoint03-fixture-') as tmp:
        root = Path(tmp).resolve()
        helper['save'].__globals__['ROOT'] = root
        master = {'path': 'fixture-master.blend', 'sha256': 'fixture-only'}
        recipe = {'path': 'fixture-recipe.py', 'sha256': 'fixture-only'}
        calls = []

        def output(name):
            out = root/'harness/out/rider-rebuild'/name; out.mkdir(parents=True)
            for side in ('L', 'R'):
                (out/('ActualSelectedGlove.'+side+'-ancestry.npz')).write_bytes(b'fixture ancestry '+side.encode())
            return out

        def operator(mode):
            def save(**kwargs):
                calls.append(kwargs)
                assert kwargs['compress'] is False
                path = Path(kwargs['filepath'])
                if mode == 'success': path.write_bytes(b'BLENDER17-01v0500 fixture only')
                elif mode == 'compressed': path.write_bytes(b'\x28\xb5\x2f\xfd fixture only')
                else: Path(str(path)+'@').write_bytes(b'incomplete fixture only')
                if mode == 'exception': raise RuntimeError('Fixture save failure')
                return {'CANCELLED'} if mode == 'cancelled' else {'FINISHED'}
            return save

        fake_bpy.ops.wm.save_as_mainfile = operator('success')
        out = output('success'); report = helper['save'](out, master, recipe)
        native = out/'UNACCEPTED-gloves-only-checkpoint.blend'
        assert report['sourceMaster'] is master and report['sourceRecipe'] is recipe
        assert report['native'] == {'path': str(native.relative_to(root)),
                                    'sha256': hashlib.sha256(native.read_bytes()).hexdigest()}
        assert json.loads((out/'gloves-only-checkpoint.json').read_text()) == report
        assert report['nativeStorage']['compressed'] is False and not report['nativeStorage']['reopenVerified']
        assert not any(report[k] for k in ('acceptedArt', 'geometryGatesPassed', 'movingReviewPassed'))
        for side in ('L', 'R'):
            name = 'ActualSelectedGlove.'+side
            assert report['gloveObjects'][name]['sha256'] == hashlib.sha256((out/(name+'-ancestry.npz')).read_bytes()).hexdigest()
        fixtures.append('Successful save explicitly disables compression and hashes final native plus both ancestry files')
        before = len(calls)
        try: helper['save'](out, master, recipe)
        except AssertionError: pass
        else: raise AssertionError('Existing native/receipt overwritten')
        assert len(calls) == before
        fixtures.append('Existing native/receipt rejected before save')
        for mode in ('cancelled', 'missing-final', 'compressed', 'exception'):
            out = output(mode); fake_bpy.ops.wm.save_as_mainfile = operator(mode)
            try: helper['save'](out, master, recipe)
            except (AssertionError, RuntimeError): pass
            else: raise AssertionError('Invalid save accepted: '+mode)
            assert not (out/'gloves-only-checkpoint.json').exists()
            fixtures.append(mode+' save preserves failure output and emits no success receipt')

    engine = SimpleNamespace()
    original = SimpleNamespace(checkpoint={'save': object(), 'sha': object()}, prior=SimpleNamespace(engine=engine))
    before_glove = lambda: None
    stop_after_gloves = lambda: None
    original.stop_after_gloves = stop_after_gloves
    old_sha = original.checkpoint['sha']; witnessed = []

    def main():
        assert engine.full_cuff is before_glove and engine.sleeve is stop_after_gloves
        assert Path(original.__file__).resolve() == HERE/'gloves_only03.py'
        assert Path(original.checkpoint['save'].__code__.co_filename).resolve() == HERE/'checkpoint03.py'
        assert original.checkpoint['sha'] is old_sha
        witnessed.append(True)

    engine.main = main
    class Loader:
        def create_module(self, spec): return None
        def exec_module(self, module):
            module.prior = original; module.before_glove = before_glove
    def wrapper_spec(name, location):
        assert Path(location).resolve() == HERE/'gloves_only02.py'
        return importlib.machinery.ModuleSpec(name, Loader())
    with patch.object(importlib.util, 'spec_from_file_location', wrapper_spec):
        runpy.run_path(str(HERE/'gloves_only03.py'), run_name='__main__')
    assert witnessed == [True]
    fixtures.append('Actual03 wrapper retains memory02 and protected callbacks, changes only save, records its own recipe')

print(json.dumps({'passed': True, 'actualNativeRun': False, 'fixtures': fixtures,
                  'fixtureFileBytesAreNotNativeBlenderData': True}))
