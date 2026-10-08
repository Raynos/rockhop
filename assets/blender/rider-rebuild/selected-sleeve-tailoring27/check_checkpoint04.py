"""Behavior-only fake I/O: pending saves cannot become protected success."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import runpy
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'checkpoint04.py')); fixtures = []
with tempfile.TemporaryDirectory(prefix='checkpoint04-fixture-') as tmp, contextlib.redirect_stdout(io.StringIO()):
    root = Path(tmp).resolve(); h['pin'].__globals__['ROOT'] = root
    def file(name):
        path = root/name; path.write_text('fixture only'); return h['pin'](path)
    inputs = {'master': file('master.blend'), 'geometryHelper': file('geometry.py'), 'restHelper': file('rest.py')}
    recipe = file('recipe.py'); input_path = root/'input.json'
    input_path.write_text(json.dumps(inputs)); input_pin = h['pin'](input_path)
    names = ['RiderHoodie', 'RiderBody__FullAnatomyReference']
    objects = {n: NS(name=n, type='MESH') for n in names}
    rig = NS(data=NS(bones=range(75))); objects['RiderSkeleton'] = rig
    for side in ('L', 'R'):
        name = 'ActualSelectedGlove.'+side
        objects[name] = NS(name=name, type='MESH', vertex_groups=['native'], data=NS(vertices=range(3), polygons=range(1)))
    rest = [('bone'+str(i), None, [0., 0., 0.]) for i in range(75)]
    def forbidden_geometry(obj): raise AssertionError('Full protected scan ran before save')
    state = {'names': names, 'fingerprints': {n: n+'-expected' for n in names},
             'rig': rest, 'rest': lambda obj: rest, 'geometry': forbidden_geometry}
    events = []
    def save(**kwargs):
        path = Path(kwargs['filepath']); assert kwargs['compress'] is False
        expected = json.loads((path.parent/'protected-before-gloves.json').read_text())
        assert expected['protectedValidationPassed'] is False and expected['expectedProtectedGeometry'] == state['fingerprints']
        events.append('save'); path.write_bytes(b'BLENDER fixture only'); return {'FINISHED'}
    def reopen(**kwargs):
        assert kwargs['use_scripts'] is False
        events.append('reopen'); return {'FINISHED'}
    bpy = NS(data=NS(filepath=str(root/'master.blend'), objects=objects), ops=NS(wm=NS(save_as_mainfile=save, open_mainfile=reopen)))
    def out(name):
        p = root/'harness/out/rider-rebuild'/name; p.mkdir(parents=True)
        for side in ('L', 'R'): (p/('ActualSelectedGlove.'+side+'-ancestry.npz')).write_bytes(b'fixture ancestry')
        return p
    p = out('success'); report = h['save_pending'](p, recipe, state, inputs, input_pin, bpy)
    assert report['status'] == h['PENDING'] and report['protectedValidationPassed'] is False
    assert 'protectedGeometryUnchanged' not in report and 'originalHoodieUnchangedBeforeSave' not in report
    assert not (p/'gloves-only-qualified.json').exists() and events == ['save']
    fixtures.append('Pending save never scans protected geometry and persists expected witness before raw native save')
    def load(path):
        def geometry(obj):
            assert events[-1] == 'reopen'; return state['fingerprints'][obj.name]
        return {'geometry': geometry} if path.endswith('geometry.py') else {'rest': lambda obj: rest}
    qualified = h['qualify'](p/'gloves-only-pending.json', bpy, load)
    assert qualified['protectedValidationPassed'] and qualified['exact75RestUnchanged']
    assert qualified['protectedValidationStage'] == 'SEPARATE_REOPENED_NATIVE'
    assert not qualified['geometryGatesPassed'] and not qualified['movingReviewPassed'] and not qualified['acceptedArt']
    assert json.loads((p/'gloves-only-pending.json').read_text())['protectedValidationPassed'] is False
    fixtures.append('Only reopened matching native issues separate qualified receipt; pending receipt stays unchanged')
    p = out('changed-master-before-qualifier'); h['save_pending'](p, recipe, state, inputs, input_pin, bpy)
    master_path = root/inputs['master']['path']; original_master = master_path.read_bytes()
    master_path.write_bytes(b'changed source under identical pathname')
    prior_events = list(events)
    try: h['qualify'](p/'gloves-only-pending.json', bpy, load)
    except AssertionError: pass
    else: raise AssertionError('Changed source master accepted by qualifier')
    assert events == prior_events and not (p/'gloves-only-qualified.json').exists()
    master_path.write_bytes(original_master)
    fixtures.append('Changed source master bytes at the same path stop qualification before reopen or success receipt')
    for kind in ('geometry', 'rest'):
        p = out(kind); h['save_pending'](p, recipe, state, inputs, input_pin, bpy)
        def bad_load(path):
            value = load(path)
            if path.endswith(kind+'.py'): value[kind] = lambda obj: 'mismatch'
            return value
        try: h['qualify'](p/'gloves-only-pending.json', bpy, bad_load)
        except AssertionError: pass
        else: raise AssertionError('Qualifier swallowed '+kind+' mismatch')
        assert not (p/'gloves-only-qualified.json').exists()
        fixtures.append('Reopened '+kind+' mismatch emits no qualified receipt and preserves pending native')
    for kind in ('source', 'master-bytes', 'ancestry', 'rig'):
        p = out('reject-'+kind); prior_events = list(events)
        if kind == 'source': bpy.data.filepath = str(root/'other.blend')
        if kind == 'master-bytes': master_path.write_bytes(b'changed source under identical pathname')
        if kind == 'ancestry': (p/'ActualSelectedGlove.R-ancestry.npz').unlink()
        if kind == 'rig': rig.data.bones = range(74)
        try: h['save_pending'](p, recipe, state, inputs, input_pin, bpy)
        except AssertionError: pass
        else: raise AssertionError('Missing cheap witness accepted: '+kind)
        assert events == prior_events and not (p/'gloves-only-pending.json').exists()
        bpy.data.filepath = str(root/'master.blend'); rig.data.bones = range(75)
        master_path.write_bytes(original_master)
        fixtures.append('Missing '+kind+' witness stops before native save')

    engine = NS(bpy=bpy); original = NS(prior=NS(engine=engine), protected_state=state)
    before_glove = lambda: None; wiring = []
    class Loader:
        def create_module(self, spec): return None
        def exec_module(self, module): module.prior = original; module.before_glove = before_glove
    def wrapper_spec(name, location):
        assert Path(location).resolve() == HERE/'gloves_only02.py'
        return importlib.machinery.ModuleSpec(name, Loader())
    def main():
        assert engine.full_cuff is before_glove and engine.sleeve.__name__ == 'stop_before_protected_scan'
        def pending(out, recipe, actual_state, inputs, input_pin, actual_bpy):
            assert actual_state is state and actual_bpy is bpy; wiring.append(True)
        engine.sleeve.__globals__['checkpoint']['save_pending'] = pending
        try: engine.sleeve()
        except SystemExit as exc: assert exc.code == 0
        else: raise AssertionError('Callback did not stop before original sleeve/after-scan')
    engine.main = main
    with patch.object(importlib.util, 'spec_from_file_location', wrapper_spec), patch.object(sys, 'argv', ['fixture', '--', str(root)]):
        runpy.run_path(str(HERE/'gloves_only04.py'), run_name='__main__')
    assert wiring == [True]
    fixtures.append('Actual04 wrapper retains memory02 construction and replaces the after-scan callback with pending save then exit')
print(json.dumps({'passed': True, 'actualNativeRun': False, 'fixtures': fixtures,
                  'fixtureFileBytesAreNotNativeBlenderData': True}))
