import numpy as np,json
from pathlib import Path
root=Path('/Users/raynos/projects/games/rockhop');base=root/'harness/out/rider-rebuild/selected-boot-wearer80';frames=json.loads((base/'inspect02/inspection.json').read_text());body=np.load(root/'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz');jeans=np.load(root/'assets/blender/rider-rebuild/selected-ankle-field42/field-patch.npz');s=json.loads((root/'harness/out/rider-rebuild/selected-boot-family75/cpu01/source.json').read_text());raw=(root/s['arrays']['path']).read_bytes()
def closest(q,tri):
 a=tri[:,0];ab=tri[:,1]-a;ac=tri[:,2]-a;n=np.cross(ab,ac);n/=np.linalg.norm(n,axis=1)[:,None];d=np.einsum('ij,ij->i',q-a,n);project=q-d[:,None]*n
 aa=(ab*ab).sum(1);bb=(ac*ac).sum(1);abac=(ab*ac).sum(1);v=project-a;av=(ab*v).sum(1);bv=(ac*v).sum(1);den=aa*bb-abac*abac;u=(av*bb-bv*abac)/den;w=(bv*aa-av*abac)/den
 good=(u>=0)&(w>=0)&(u+w<=1);best=np.where(good,d*d,np.inf);hit=project.copy()
 for i,j in ((0,1),(1,2),(2,0)):
  a=tri[:,i];e=tri[:,j]-a;t=np.clip(np.einsum('ij,ij->i',q-a,e)/(e*e).sum(1),0,1);p=a+t[:,None]*e;dd=((q-p)**2).sum(1);better=dd<best;best[better]=dd[better];hit[better]=p[better]
 i=int(np.argmin(best));return i,float(best[i]**.5),float((q-hit[i])@n[i])
for side in 'LR':
 def arr(k):
  d=s['arrays']['layout'][side+k];return np.frombuffer(raw,dtype=d['dtype'],offset=d['byteOffset'],count=np.prod(d['shape'])).reshape(d['shape'])
 orig=arr('Positions');f=arr('Triangles');origin=np.array(frames['sides'][side]['origin']);basis=np.array(frames['sides'][side]['basisColumns']).T;p=(orig.astype(float)-origin)@basis;recipe=np.load('/tmp/boot83-mouth-'+side+'.npz');loop=recipe['loopOriginalVertexIds'];retired=recipe['retiredOriginalFaceIds'];mask=np.ones(len(f),bool);mask[retired]=False
 # Three exact source edge neighborhoods attached to the authored inner edge.
 band=np.zeros(len(f),bool);verts=loop
 for i in range(3):
  band |= mask & np.any(np.isin(f,verts),axis=1);verts=np.unique(f[band])
 ids=np.flatnonzero(band);tri=orig[f[ids]].astype(float);findings={}
 for label,vertices in [('body',body['vertices']),('jeans3318',jeans['beforeLocal'])]:
  local=(vertices.astype(float)-origin)@basis;use=(vertices[:,0]*origin[0]>0)&(local[:,2]>.09)&(local[:,2]<.14);qids=np.flatnonzero(use);rows=[]
  for qid in qids:
   query=vertices[qid].astype(float);mindist=np.linalg.norm(np.maximum(np.maximum(tri.min(1)-query,query-tri.max(1)),0),axis=1);candidates=np.flatnonzero(mindist<.012)
   if not len(candidates):continue
   k,dot,signed=closest(query,tri[candidates]);rows.append((int(qid),int(ids[candidates[k]]),dot,signed,local[qid].tolist()))
  bad=[r for r in rows if r[3]<0];near=[r for r in rows if r[2]<.001];findings[label]={'queryVertices':len(qids),'within12mmOfEdgeBand':len(rows),'negativeNearestSide':len(bad),'minimumDistanceM':min([r[2] for r in rows],default=None),'negativeMinimumSignedM':min([r[3] for r in bad],default=None),'closestRows':sorted(rows,key=lambda r:r[2])[:5]}
 print(side,json.dumps(findings),flush=True)
 Path('/tmp/boot83-mouth-fit-'+side+'.json').write_text(json.dumps(findings,indent=2))
