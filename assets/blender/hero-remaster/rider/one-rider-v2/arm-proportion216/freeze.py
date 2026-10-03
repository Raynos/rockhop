"""Wrap-up freeze: no new render, rig, model job or anatomy experiment."""
from pathlib import Path
import json,hashlib
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');A=R/'assets/blender/hero-remaster/rider/one-rider-v2/arm-proportion216';E=R/'docs/evidence/hero-remaster/one-rider-v2/arm-proportion216';D=B/'arm-proportion216'
def pin(p):return {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
pre=json.loads((E/'preflight-freeze.json').read_text());inputs={p:pin(Path(p)) for p in pre['inputPins']};assert all(q==pre['inputPins'][p] for p,q in inputs.items())
for p in [R/'assets/blender/hero-remaster/rider/one-rider-v2/finite-cleanup210/clean.py',R/'docs/evidence/hero-remaster/one-rider-v2/finite-cleanup210/freeze.json',B/'source-preserving-garment185/operator/rider.glb']:
    inputs[str(p)]=pin(p)
reports={name:json.loads((E/name).read_text()) for name in ('construction-report.json','collision-report.json','coplanar-report.json')}
assert reports['construction-report.json']['status']=='STRUCTURAL_PREREQUISITES_CLEAR_COLLISION_PENDING';assert reports['collision-report.json']['status']=='NATIVE_COLLISION_PREREQUISITES_CLEAR';assert reports['coplanar-report.json']['status']=='COPLANAR_PREREQUISITES_CLEAR'
owned=sorted(p for directory in (A,E) for p in directory.iterdir() if p.is_file() and p.name!='freeze.json');outputs=sorted(p for p in D.iterdir() if p.is_file())
out={'status':'FROZEN_UNACCEPTED_ARM_PROPORTION_ONE_TRIAL_NUMERIC_PREREQUISITES_CLEAR_VISUAL_UNMEASURED','geometryAttempts':1,'gpuUsed':False,'cpuThreads':2,'inputPins':inputs,'ownedFiles':{str(p):pin(p) for p in owned},'privateOutputs':{str(p):pin(p) for p in outputs},'sourceUnchanged':True,'renderStatus':'NOT_LAUNCHED_USER_REQUESTED_WRAP_UP','activeOwnedJobs':[],'completedOwnHandles':[50961,83749],'limits':['No movinggray/PBR, restvisualscore, rig, weights, contacts, legrepair, likedheadintegration, gameplay/mobilegate or promotion.','Generatedhead remainsprovisional andexact; likedNEWdonor185preservedelsewhere.','No newjob/experiment/render launched afteruserwrap-upinstruction.']}
(E/'freeze.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'freezeSHA256':pin(E/'freeze.json')['sha256'],'inputPins':len(inputs),'ownedFiles':len(owned),'privateOutputs':len(outputs),'candidateSHA256':pin(D/'candidate-native.glb')['sha256'],'activeJobs':[]},indent=2))
