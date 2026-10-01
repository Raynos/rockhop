"""Matched four actual physics witnesses: C19 vs static V5 shape/weights."""
from pathlib import Path
import json, hashlib
import numpy as np
REPO=Path('/Users/raynos/projects/games/rockhop')
BASE=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/physical-v5-control157'
PRIVATE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
oldRoot=PRIVATE/'rig-adapter01/body-bind34/candidate-cpu'
newRoot=PRIVATE/'garment-rebuild01/physical-v5-control157/candidate-cpu'
a=json.loads((REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu/pose-manifest.json').read_text())
b=json.loads((newRoot/'pose-manifest.json').read_text())
(BASE/'candidate-cpu').mkdir(exist_ok=True)
(BASE/'candidate-cpu/pose-manifest.json').write_text(json.dumps(b,indent=2)+'\n')
def read(root,rec,width):
 raw=(root/rec['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rec['sha256']
 return np.frombuffer(raw,dtype='<f8').reshape(-1,width)
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-30)
sourceP=read(oldRoot,a['primitives'][0]['attributes']['position'],3)
tri=read(oldRoot,a['primitives'][0]['index'],3).astype(int)
newTri=read(newRoot,b['primitives'][0]['index'],3).astype(int)
assert tri.shape==newTri.shape
changedTopology=np.any(tri!=newTri,axis=1)
# Restrict paired regional scores to literal unchanged source triangle rows.
# Preserve intentional source topology edits rather than silently undoing them.
cent=sourceP[tri].mean(1)
scopes={'arms':(cent[:,1]>.95)&(np.abs(sourceP[tri][:,:,2]).mean(1)>.13),
        'hips':(cent[:,1]>.70)&(cent[:,1]<1.06)&(np.abs(sourceP[tri][:,:,2]).mean(1)<.24)}
scopes={k:mask&~changedTopology for k,mask in scopes.items()}
hood=read(oldRoot,a['primitives'][1]['attributes']['position'],3)
lookup={tuple(p):i for i,p in enumerate(sourceP)}
pairs=np.array([(lookup[tuple(p)],i) for i,p in enumerate(hood) if tuple(p) in lookup],int)
rows=[]
for old,new in zip(a['rows'],b['rows']):
 assert old['i']==new['i']
 row={'sample':new['i'],'lean':new['lean'],'variants':{},'contacts':new['contacts']}
 delta=max(np.linalg.norm(np.array(x['bikeFramePosition'])-y['bikeFramePosition']) for x,y in zip(old['bonePoints'],new['bonePoints']))
 assert delta<1e-12
 row['maximumBoneBikeFrameDifferenceM']=float(delta)
 for label,root,manifest,sample in [('C19',oldRoot,a,old),('V5static',newRoot,b,new)]:
  P=read(root,manifest['primitives'][0]['attributes']['position'],3)
  N=read(root,manifest['primitives'][0]['attributes']['normal'],3)
  X=read(root,sample['dump'][0]['positions'],3)
  normal=read(root,sample['dump'][0]['gpuRuleSkinnedNormals'],3)
  H=read(root,sample['dump'][1]['positions'],3)
  rest,posed=P[tri],X[tri]
  rc=np.cross(rest[:,1]-rest[:,0],rest[:,2]-rest[:,0]);pc=np.cross(posed[:,1]-posed[:,0],posed[:,2]-posed[:,0])
  stretch=np.linalg.norm(posed-np.roll(posed,-1,axis=1),axis=2)/np.maximum(np.linalg.norm(rest-np.roll(rest,-1,axis=1),axis=2),1e-30)
  area=np.linalg.norm(pc,axis=1)/np.maximum(np.linalg.norm(rc,axis=1),1e-30)
  rd=(unit(rc)*unit(N[tri].mean(1))).sum(1);pd=(unit(pc)*unit(normal[tri].mean(1))).sum(1)
  row['variants'][label]={'maximumHoodBodySharedPositionGapM':float(np.linalg.norm(X[pairs[:,0]]-H[pairs[:,1]],axis=1).max()),'aliasCount':len(pairs),'scopes':{name:{'triangles':int(mask.sum()),'maximumEdgeStretch':float(stretch[mask].max()),'edgeP99':float(np.quantile(stretch[mask],.99)),'minimumAreaRatio':float(area[mask].min()),'areaBelowQuarter':int((area[mask]<.25).sum()),'normalOppositionFlags':int(((rd>.2)&(pd<-.2)&mask).sum())} for name,mask in scopes.items()}}
 rows.append(row)
report={'kind':'Actual physical driver witnesses; no authored clip or compression driver',
 'sourceMapping':json.loads((BASE/'mapping-report.json').read_text())['candidateSHA256'],'rows':rows,
 'changedSourceBodyTriangleRowsExcludedFromPairedMetrics':np.flatnonzero(changedTopology).tolist(),
 'maximumContactDifferenceFromRetained11PlayedM':max(c['maximumCPUvsActualPlayedSurfaceM'] for r in rows for c in r['contacts']),
 'limits':['Four witnesses are not complete motion, collision or visible contact acceptance.',
 'Per-variant rest metrics are not interchangeable with authored105/111snapshot crossing gates.',
 'New hood/body base fields change; shared original aliases are specifically measured.']}
(BASE/'cpu-physical-control.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(rows,indent=2))
