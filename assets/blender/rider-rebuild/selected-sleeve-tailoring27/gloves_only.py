"""Parent-guarded glove-only checkpoint using the unchanged actual cuff10 recipe.

This NEW wrapper has not run. It saves both finished glove meshes and exits
before any hoodie edit or sleeve recipe. Output remains explicitly unaccepted.
"""
import hashlib
import importlib.util
import json
import runpy
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
prior_path=ROOT/'assets/blender/rider-rebuild/selected-cuff-topology10/construct10.py'
assert hashlib.sha256(prior_path.read_bytes()).hexdigest()=='906c4df1c117d183b9b117fe03a27d2f96c82f65f1abc45ae9fd6e9e7e29aa0e'
spec=importlib.util.spec_from_file_location('unchanged_selected_cuff10',prior_path)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
checkpoint_path=HERE/'checkpoint.py'
assert hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()=='d45d46b46cc621fb6a116f6677bafaa642989e6664f6da6a919d46b70b4b2419'
checkpoint=runpy.run_path(str(checkpoint_path))
saved_full_cuff=prior.engine.full_cuff
protected_state={}


def remember_protected_before_gloves(*args,**kwargs):
    if not protected_state:
        engine=prior.engine
        inputs=json.loads((ROOT/'assets/blender/rider-rebuild/glove-over-sleeve08/input.json').read_text())
        geometry=runpy.run_path(str(engine.pin(inputs['geometryHelper'])))['geometry']
        rest=runpy.run_path(str(engine.pin(inputs['restHelper'])))['rest']
        names=(engine.B.VISIBLE-{'ActualSelectedGlove.L','ActualSelectedGlove.R'})|{'RiderBody__FullAnatomyReference'}
        protected_state.update(geometry=geometry,rest=rest,names=sorted(names),
            fingerprints={n:geometry(engine.bpy.data.objects[n]) for n in names},
            rig=rest(engine.bpy.data.objects['RiderSkeleton']))
    return saved_full_cuff(*args,**kwargs)


def stop_after_gloves(*args,**kwargs):
    assert protected_state, 'No pre-glove protected-state witness'
    state=protected_state;objects=prior.engine.bpy.data.objects
    assert state['fingerprints']=={n:state['geometry'](objects[n]) for n in state['names']}, 'Protected geometry, including original hoodie, changed before checkpoint'
    assert state['rig']==state['rest'](objects['RiderSkeleton']), 'Native75 rest changed before checkpoint'
    inputs=json.loads((ROOT/'assets/blender/rider-rebuild/glove-over-sleeve08/input.json').read_text())
    output=Path(sys.argv[sys.argv.index('--')+1]).resolve()
    recipe={'path':str(Path(__file__).relative_to(ROOT)),'sha256':checkpoint['sha'](__file__)}
    report=checkpoint['save'](output,inputs['master'],recipe)
    report.update(protectedGeometryUnchanged=state['fingerprints'],exact75RestUnchanged=True,
                  originalHoodieUnchangedBeforeSave=True)
    (output/'gloves-only-checkpoint.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0)


if __name__=='__main__':
    prior.engine.full_cuff=remember_protected_before_gloves
    prior.engine.sleeve=stop_after_gloves
    prior.engine.main()
