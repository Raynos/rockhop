"""Integration-owner read-only receipt and literal surface verification."""
from pathlib import Path
import hashlib,json
import numpy as np
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/basic-pose-seams163')
f=json.loads((OUT/'freeze.json').read_text());verified=[]
for category in ['recipeFiles','runtimeDependencies','evidenceFiles','privateMasters']:
 for row in f[category]:
  raw=Path(row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
  if 'bytes' in row:assert len(raw)==row['bytes']
  verified.append(row['path'])
masters={Path(r['path']).name:Path(r['path']) for r in f['privateMasters']}
x=json.loads(masters['raw-seam-input.json'].read_text());fixture=json.loads(masters['fixture-v4.json'].read_text())
actual=json.loads((OUT/'actual-three-seams.json').read_text());assert len(actual['rows'])==5404
for r in actual['rows']:
 assert r['maximumEndpointGapM']==r['maximumWithinPrimitiveAliasGapM']==r['maximumRenderedEdgeMidpointGapM']==0
 assert all(q['quarterAreaFaces']==0 for q in r['regions'])
edge=json.loads((OUT/'incident-edge-coverage.json').read_text());assert len(edge['rows'])==127
folds=0
for r in edge['rows']:
 p=[];norm=[];away=[]
 a,b=[np.array(x['groups'][i]['position']) for i in r['endpointGroups']];axis=b-a;axis/=np.linalg.norm(axis)
 for mi,kind in [(0,'body'),(1,'glove')]:
  P=np.array(x['meshes'][mi]['attrs']['POSITION']);ids=r[kind+'TriangleVertexIDs'];tri=P[ids];n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=np.linalg.norm(n);norm.append(n)
  direction=None
  for lane in range(3):
   u,v=tri[lane],tri[(lane+1)%3]
   if (np.array_equal(u,a) and np.array_equal(v,b)) or (np.array_equal(u,b) and np.array_equal(v,a)):
    direction=1 if np.array_equal(u,a) else -1
    d=tri[(lane+2)%3]-a;d-=np.dot(d,axis)*axis;d/=np.linalg.norm(d);away.append(d)
  assert direction is not None;p.append(direction)
 assert p[0]==-p[1] and r['oppositeBoundaryWinding']
 assert abs(np.dot(*norm)-r['adjacentFaceNormalDot'])<1e-12
 assert abs(np.dot(*away)-r['edgePerpendicularAwayDirectionDot'])<1e-12
 folds+=np.dot(*away)>0
M=np.fromfile(masters['independent-raw-deltas.f64'],dtype='<f8').reshape(5404,19,4,4);posed=[]
for mi,key in [(0,'bodyVertexIDs'),(1,'gloveVertexIDs')]:
 mesh=x['meshes'][mi];ids=np.array([g[key][0] for g in x['groups']]);P=np.array(mesh['attrs']['POSITION'])[ids];J=np.array(mesh['attrs']['JOINTS_0'])[ids];w=np.array(mesh['attrs']['WEIGHTS_0'])[ids];w=(w/abs(w).sum(1,keepdims=True)).astype('f4').astype(float);W=np.zeros((127,19))
 for lane in range(4):np.add.at(W,(np.arange(127),J[:,lane]),w[:,lane])
 points=np.broadcast_to(P,(5404,127,3)).copy()
 for i,name in enumerate(mesh['targetNames']):
  side=name[-1] if name.endswith(('.L','.R','_L','_R')) else None
  activation=np.array([r['closedGrip'] if 'grip' in name.lower() and (r.get('gripSide') is None or r.get('gripSide')==side) else 0 for r in fixture['frames']])
  points+=activation[:,None,None]*np.array(mesh['targets'][i]['POSITION'])[ids][None,:,:]
 posed.append(np.einsum('gj,fjab,fgb->fga',W,M[:,:,:3,:],np.concatenate([points,np.ones((5404,127,1))],axis=2),optimize=True))
gap=float(np.linalg.norm(posed[0]-posed[1],axis=2).max());assert gap==0
report={'kind':'Parent independent read-only integration verification','hashedFiles':len(verified),'frames':5404,'literalOppositeWindingEdges':127,'restFoldedIncidentPairs':int(folds),'independentRecomputedAliasGapM':gap,'actualReceiptMaximumAffineParityM':max(r['maximumActualVsRawAffineParityM'] for r in actual['rows']),'limits':'Reuses frozen raw matrices; independently recomputes morph/normalized skin surface equality and edge geometry. No rendered appearance, collision, normal-map continuity, thickness or contact acceptance.'}
assert folds==46
(OUT/'parent-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
