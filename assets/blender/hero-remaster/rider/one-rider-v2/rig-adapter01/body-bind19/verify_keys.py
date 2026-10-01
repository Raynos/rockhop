from pathlib import Path
import json, hashlib
import numpy as np
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind19')
private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind19')
a=json.loads((base/'arap-cpu/pose-manifest.json').read_text());b=json.loads((base/'morph01/cpu02/pose-manifest.json').read_text());rows=[]
def read(root,r):
 p=root/r['file']; p=p if p.exists() else private/'morph01/cpu02'/r['file']; assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];return np.fromfile(p,dtype='<f8').reshape(-1,3)
for x,y in zip(a['rows'],b['rows']):
 assert x['i']==y['i']; errors=[]
 for original,actual in zip(x['dump'],y['dump']): errors.append(float(np.linalg.norm(read(private/'arap-cpu',original['positions'])-read(base/'morph01/cpu02',actual['positions']),axis=1).max()))
 rows.append({'sample':x['i'],'maximumMorphVsAuthoredTargetErrorM':max(errors),'driver':y['hipCorrective'],'maximumContactVsRetainedPlayedM':max(c['maximumCPUvsActualPlayedSurfaceM'] for c in y['contacts'])})
assert max(x['maximumMorphVsAuthoredTargetErrorM'] for x in rows)<1e-7
(base/'morph01/cpu02/key-reproduction.json').write_text(json.dumps({'rows':rows,'passed':True,'limits':'Six authored poses only; interpolation and silhouette not yet judged.'},indent=2)+'\n');print(json.dumps(rows))
