"""Independent fresh-rig adaptation metrics on four retained actual game states."""
from pathlib import Path
import json,hashlib
import numpy as np
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01');out=base/'body-bind36';private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
a=json.loads((base/'body-bind25/morph01/baseline-normal01/pose-manifest.json').read_text());b=json.loads((out/'candidate-cpu/pose-manifest.json').read_text())
def read(root,rec,lanes):
 f=root/rec['file']
 if not f.exists() and root==out/'candidate-cpu':f=private/'body-bind36/candidate-cpu'/rec['file']
 raw=f.read_bytes();assert hashlib.sha256(raw).hexdigest()==rec['sha256'];return np.frombuffer(raw,dtype='<f8').reshape(-1,lanes).copy()
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-30)
rest=read(out/'candidate-cpu',b['primitives'][0]['attributes']['position'],3);tri=read(out/'candidate-cpu',b['primitives'][0]['index'],3).astype(int);n=read(out/'candidate-cpu',b['primitives'][0]['attributes']['normal'],3)
for mi in range(2):
 for key in ['position','normal','uv']:
  assert b['primitives'][mi]['attributes'][key]['sha256']==a['primitives'][mi]['attributes'][key]['sha256']
 assert b['primitives'][mi]['index']['sha256']==a['primitives'][mi]['index']['sha256']
q=rest[tri];cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);sourceDot=np.einsum('ti,ti->t',unit(cross),unit(n[tri].mean(1)));sourceEdge=np.linalg.norm(q-np.roll(q,-1,axis=1),axis=2)
arm=(q[:,:,1].mean(1)>.95)&(np.abs(q[:,:,2]).mean(1)>.13)
hip=(q[:,:,1].mean(1)>.70)&(q[:,:,1].mean(1)<1.06)&(np.abs(q[:,:,2]).mean(1)<.24)
hoodRest=read(out/'candidate-cpu',b['primitives'][1]['attributes']['position'],3);lookup={tuple(p):i for i,p in enumerate(rest)};aliases=[(lookup[tuple(p)],i) for i,p in enumerate(hoodRest) if tuple(p) in lookup]
rows=[]
for old,new in zip(a['rows'],b['rows']):
 assert old['i']==new['i'];assert old['bodyworkBikeFrame']['sha256']==new['bodyworkBikeFrame']['sha256']
 assert new['debug']['bones']==19 and new['debug']['physicalPose'] is True
 ap=read(private/'body-bind25/morph01/baseline-normal01',old['dump'][0]['positions'],3);an=read(private/'body-bind25/morph01/baseline-normal01',old['dump'][0]['gpuRuleSkinnedNormals'],3)
 bp=read(out/'candidate-cpu',new['dump'][0]['positions'],3);bn=read(out/'candidate-cpu',new['dump'][0]['gpuRuleSkinnedNormals'],3);hood=read(out/'candidate-cpu',new['dump'][1]['positions'],3)
 oldhood=read(private/'body-bind25/morph01/baseline-normal01',old['dump'][1]['positions'],3)
 aliasBefore=max(np.linalg.norm(ap[v]-oldhood[h]) for v,h in aliases);aliasAfter=max(np.linalg.norm(bp[v]-hood[h]) for v,h in aliases)
 row={'sample':new['i'],'maximumBodyPointChangeM':float(np.linalg.norm(bp-ap,axis=1).max()),'hoodSharedAliases':len(aliases),'maximumHoodBodySharedPositionGapBeforeAfterM':[float(aliasBefore),float(aliasAfter)],'debug':new['debug'],'contactsVsSource11ActualPlayed':new['contacts'],'scopes':{}}
 for label,roi in [('armGeometry',arm),('hipGeometry',hip)]:
  for name,P,N in [('baseline',ap,an),('fresh36',bp,bn)]:
   Q=P[tri];cross=np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]);dots=np.einsum('ti,ti->t',unit(cross),unit(N[tri].mean(1)));stretch=(np.linalg.norm(Q-np.roll(Q,-1,axis=1),axis=2)/np.maximum(sourceEdge,1e-30)).max(1)
   row['scopes'].setdefault(label,{})[name]={'triangles':int(roi.sum()),'normalOppositionFlags':int((roi&(sourceDot>.2)&(dots<-.2)).sum()),'maximumEdgeStretch':float(stretch[roi].max()),'edgeStretchP90P99':np.quantile(stretch[roi],[.90,.99]).tolist(),'elbow3789':{'normalDot':float(dots[3789]),'maximumEdgeStretch':float(stretch[3789])}}
 rows.append(row)
report={'status':'Read-only actualThree freshC19adapter measurements; art/Garage acceptance unproven','sourceSHA256':b['sourceSHA256'],'restGeometryNormalsUVIndicesExactTo11':True,'fourActualInputStates':4,'rows':rows,'maximumContactSurfaceDifferenceVsActual11M':max(c['maximumCPUvsActualPlayedSurfaceM'] for r in rows for c in r['contactsVsSource11ActualPlayed']),'limits':['Newbinds/weights mean body surfaces/bone positions are intentionally different; preserve COM/lean/contacts and input behavior, not local rotations.','Flags are normal opposition and strain, not rendered quality or collisions.','Fourpoints do not prove allmotion/Garage/bench/head-neck joins; head primitive not inspected in this regional dump.']}
(out/'cpu-adaptation-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
