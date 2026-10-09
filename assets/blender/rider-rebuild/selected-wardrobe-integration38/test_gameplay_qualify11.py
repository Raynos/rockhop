"""Weak-reference lifetime and failure fixtures; no actual Blender/native I/O."""
import contextlib
import copy
import gc
import importlib.util
import io
import json
import tempfile
import weakref
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+'.py'))
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


q = module('gameplay_qualify11')
intake = module('intake_qualifier11')
actual10 = q.frozen10()
real_json = q.json
fixtures = []


class TrackedDict(dict): pass
class TrackedList(list): pass


def run_case(kind):
    with tempfile.TemporaryDirectory(prefix='qualifier11-fixture-') as tmp:
        folder = Path(tmp)
        paths = {name: folder/name for name in ('pending.json', 'source.json', 'saved.json', 'native.blend')}
        for name, path in paths.items(): path.write_text(name)
        out = folder/'result'; events, refs = [], {}
        pin = lambda path: {'path': Path(path).name, 'sha256': 'fixture-'+Path(path).name}
        original = {'pins': {'native': pin('original.blend')}}
        actions = [{'name': 'RiderGameplayLean'+bike, 'frameRange': [1, 241]} for bike in ('Rookie', 'Pro')]
        pending = {'accepted': False, 'status': 'SELECTED_FULL_GAMEPLAY_SAVED_PROTECTED_AND_REPLAY_PENDING',
                   'native': pin(paths['native.blend']), 'input': pin('actual10.input.json'),
                   'recipe': q.GENERATION10, 'actions': actions, 'shapeZeroActions': ['RiderJeans'],
                   'sourceInput': pin('actual08.input.json'), 'sourceRecipe': pin('actual08.py'),
                   'sourcePins': original['pins']}
        before = {'accepted': False, 'kind': 'source', 'native': original['pins']['native'],
                  'pending': pin(paths['pending.json']), 'protected': {'RiderJeans': 'PBR+UV+geometry'},
                  'fields': {'RiderJeans': 'exact'}, 'keys': {'RiderBody': 'exact'}, 'rest': ['native75'],
                  'visibleMeshes': ['selected'], 'recipe': q.GENERATION10,
                  'actions': {'OriginalGeneric': {'curves': [1, 2, 3]}}}
        after = copy.deepcopy(before); after.update(kind='saved', native=pending['native'])
        after['actions']['RiderGameplayLeanPro'] = {'curves': [4, 5]}
        if kind.startswith('snapshot-'): after[kind[9:]] = 'changed'
        if kind == 'wrong-generation': before['recipe'] = after['recipe'] = pin('wrong-generation.py')
        def parsed(text):
            value = copy.deepcopy(before if text == 'source.json' else after)
            tracked = TrackedDict(value)
            refs[text] = weakref.ref(tracked)
            return tracked
        def pending_at(path):
            assert path == paths['pending.json']
            package = TrackedDict(boneNames=['fixture75'], actions=[])
            refs['package'] = weakref.ref(package)
            for index, action in enumerate(actions):
                matrices = TrackedList([[index+1., 0.], [0., index+2.]])
                refs['matrices'+str(index)] = weakref.ref(matrices)
                package['actions'].append({**action, 'nativeWorldMatrices': matrices})
            return copy.deepcopy(pending), original, package
        def released(include_package):
            gc.collect()
            names = ['source.json', 'saved.json']
            if include_package: names += ['package', 'matrices0', 'matrices1']
            assert all(refs[name]() is None for name in names), ('Retained input tree', names)
        def asarray(values, dtype):
            released(False)
            assert dtype == 'float64' and refs['package']() is not None
            result = TrackedList(copy.deepcopy(list(values)))
            refs['array'+str(len([key for key in refs if key.startswith('array')]))] = weakref.ref(result)
            events.append('convert')
            return result
        np = NS(asarray=asarray, float64='float64')
        def helpers(config):
            released(True); events.append('helpers')
            return NS(bpy=bpy)
        def reopen(**kwargs):
            released(True)
            assert kwargs['use_scripts'] is False
            events.append('open')
            return {'FINISHED'}
        bpy = NS(ops=NS(wm=NS(open_mainfile=reopen)))
        def replay(bpy_arg, np_arg, rig, got_actions, names, poses, objects, shapes):
            released(True); events.append('replay')
            assert got_actions == actions and names == ['fixture75'] and shapes == ['RiderJeans']
            assert poses == [[[1., 0.], [0., 2.]], [[2., 0.], [0., 3.]]]
            if kind == 'shape-zero': raise AssertionError('Rejected seated shape activated')
            return [{'action': action['name'], 'frames': 241,
                     'maximumAffineBoundWithin2mM': .001 if kind == 'replay-bound' else .00001}
                    for action in actions]
        def surfaces(*args):
            assert all(refs[key]() is None for key in ('array0', 'array1')), 'Converted replay arrays retained into surfaces'
            events.append('surfaces')
            if kind == 'surface-failure': raise AssertionError('Actual surface extraction failed')
            return pin('actual-surfaces.npz'), [{'actual': 'fixture-only'}]
        source = NS(pin_file=pin, pinned=lambda row: folder/row['path'], replay_actions=replay,
                    AFFINE_BOUND_M=.0001, save_body_surfaces=surfaces,
                    write_json=lambda path, value: path.write_text(json.dumps(value)))
        frozen = NS(source=source, fresh=lambda path: None, pending_at=pending_at,
                    records=actual10.records, compare_snapshots=actual10.compare_snapshots,
                    helpers=helpers, rig_and_objects=lambda *args: ('rig', ['complete-selected'], 'contract'))
        q.json = NS(loads=parsed)
        try:
            q.qualify(paths['pending.json'], paths['source.json'], paths['saved.json'], out, frozen, np)
        except AssertionError:
            assert not (out/'receipt.json').exists(), 'Failure emitted a successful receipt'
            if kind.startswith('snapshot-') or kind == 'wrong-generation': assert events == []
            if kind == 'replay-bound':
                assert (out/'checks.json').exists() and 'surfaces' not in events
            raise
        finally:
            q.json = real_json
        result = json.loads((out/'receipt.json').read_text())
        assert result['recipe'] == q.GENERATION10 and result['recipeSHA256'] == q.GENERATION10['sha256']
        assert result['qualificationRecipe'] == pin(HERE/'gameplay_qualify11.py')
        assert result['qualificationRecipe'] != result['recipe']
        assert events == ['convert', 'convert', 'helpers', 'open', 'replay', 'surfaces']
        intake.explicit_qualifier(result, result['qualificationRecipe'], pin(paths['pending.json']))
        return result, out


with contextlib.redirect_stdout(io.StringIO()):
    result, _ = run_case('success')
    fixtures.append('Weak references prove both snapshot trees, package and matrix lists are gone before helpers/native open; copied replay arrays are gone before surfaces')
    fixtures.append('Actual frozen10 compare_snapshots and records functions execute unchanged in the fixture')
    fixtures.append('Both copied matrix payloads and shape-zero list reach replay unchanged; original0.0001m gate retained')
    fixtures.append('Receipt preserves saved generation10 recipe and exposes distinct actual qualificationRecipe11')
    for kind in ('snapshot-protected', 'snapshot-fields', 'snapshot-keys', 'snapshot-rest',
                 'snapshot-actions', 'wrong-generation', 'replay-bound', 'shape-zero', 'surface-failure'):
        try: run_case(kind)
        except AssertionError: fixtures.append(kind+' cannot return a successful receipt')
        else: raise AssertionError('Accepted '+kind)
    for key in ('qualificationRecipe', 'recipe', 'qualifiedPending'):
        bad = copy.deepcopy(result); bad[key] = {'path': 'wrong', 'sha256': 'wrong'}
        try: intake.explicit_qualifier(bad, result['qualificationRecipe'], result['qualifiedPending'])
        except AssertionError: fixtures.append('Intake rejects changed '+key+' pin')
        else: raise AssertionError('Intake accepted '+key)
    with tempfile.TemporaryDirectory(prefix='intake11-fixture-') as tmp:
        folder = Path(tmp); pending_path = folder/'pending.json'
        pending = {**result, 'status': 'SELECTED_FULL_GAMEPLAY_SAVED_PROTECTED_AND_REPLAY_PENDING'}
        pending_path.write_text(json.dumps(pending))
        pin = lambda path: {'path': Path(path).name, 'sha256': 'fixture-'+Path(path).name}
        calls = []
        def original_read(path):
            calls.append('all-original38-input-gates')
            return {'config': 'fixture'}, result, {}, {}
        merger = NS(h=NS(read_input=original_read, pin=pin,
                         checked=lambda row: pending_path if row['path'] == 'pending.json' else HERE/row['path']))
        intake.install_gate(merger)
        assert merger.h.read_input('fixture')[1] is result
        assert calls == ['all-original38-input-gates']
        old = result['qualificationRecipe']; result['qualificationRecipe'] = pin('wrong.py')
        try: merger.h.read_input('fixture')
        except AssertionError: pass
        else: raise AssertionError('Installed input wrapper admitted wrong qualifier')
        result['qualificationRecipe'] = old
        fixtures.append('Installed intake wrapper retains all original38 input gates and rejects wrong qualifier provenance before returning inputs to the merger')

print(json.dumps({'passed': True, 'nativeRunExecuted': False, 'fixtureRecordsAreNotActualEvidence': True,
                  'fixtures': fixtures}, indent=2))
