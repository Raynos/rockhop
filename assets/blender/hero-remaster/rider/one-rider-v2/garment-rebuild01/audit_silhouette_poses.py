"""CPU actual34joint-pose probe of new quad garment, no appearance claim."""
from pathlib import Path
import json,hashlib,numpy as np
run=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01');root=Path('docs/evidence/hero-remaster/one-rider-v2');out=root/'garment-rebuild01/silhouette02';data=np.load(run/'silhouette02/fit02.npz');P=data['positions'];W=data['weights'];Q=data['quads'];tri=np.concatenate([Q[:,[0,1,2]],Q[:,[0,2,3]]]);rest=P[tri];cross=np.cross(rest[:,1]-rest[:,0],rest[:,2]-rest[:,0]);normals=np.zeros_like(P)
for i in range(3):np.add.at(normals,tri[:,i],cross)
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-20)
normals=unit(normals);edge=np.linalg.norm(rest-np.roll(rest,-1,axis=1),axis=2);sourceDots=np.einsum('ti,ti->t',unit(cross),unit(normals[tri].mean(1)))
topo=json.loads((out.parent/'native02-topology-audit.json').read_text());components=[]
for c in topo['components']:
 faces=np.array(c['sourceFaceIndices']);mask=np.zeros(len(tri),dtype=bool);mask[faces]=True;mask[faces+len(Q)]=True;components.append(('jeans' if c['vertices']==886 else 'shirt',mask))
m=json.loads((root/'rig-adapter01/body-bind34/candidate-cpu/pose-manifest.json').read_text());archive=run.parent/'rig-adapter01/body-bind34/candidate-cpu';rows=[];samples={}
for row in m['rows']:
 rec=row['dump'][0]['jointTransforms'];raw=(archive/rec['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rec['sha256'];M=np.frombuffer(raw,dtype='<f8').reshape(-1,4,4).transpose(0,2,1)
 posed=np.einsum('vj,jab,vb->va',W,M[:,:3,:],np.c_[P,np.ones(len(P))]);skinNorm=unit(np.einsum('vj,jab,vb->va',W,M[:,:3,:3],normals));q=posed[tri];cr=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);dots=np.einsum('ti,ti->t',unit(cr),unit(skinNorm[tri].mean(1)));stretch=(np.linalg.norm(q-np.roll(q,-1,axis=1),axis=2)/np.maximum(edge,1e-20)).max(1);area=np.linalg.norm(cr,axis=1)/np.maximum(np.linalg.norm(cross,axis=1),1e-20)
 r={'sample':row['i'],'scopes':{}}
 for name,mask in components:r['scopes'][name]={'triangles':int(mask.sum()),'normalOppositionFlags':int((mask&(sourceDots>.2)&(dots<-.2)).sum()),'maximumEdgeStretch':float(stretch[mask].max()),'edgeStretchP90P99':np.quantile(stretch[mask],[.9,.99]).tolist(),'areaCollapsedBelow25Percent':int((mask&(area<.25)).sum())}
 rows.append(r);samples[f'sample{row["i"]}Positions']=posed
np.savez_compressed(run/'silhouette02/fit02-posed.npz',**samples)
report={'status':'CPU regional feasibility of new clean garment only; no fullcharacter/engine appearance pass','sourceFitSHA256':hashlib.sha256((run/'silhouette02/fit02.npz').read_bytes()).hexdigest(),'sourceRigSHA256':m['sourceSHA256'],'sourceWeightsMaximumDiscardedProbability':json.loads((out.parent/'fit01/fit-report.json').read_text())['maximumDiscardedSkinProbability'],'rows':rows,'limits':['New topology means original triangle IDs/ROI counts are incomparable; separate native shirt/jeans components, no percentile equivalence claim.','No saddle support/selfintersection/contacts/hood join or continuous motion checked.','Original complete rider preserved; this garment has no head/hood/gloves/shoes or material bake yet.','Native weight TOP4drops up to1.97percent; full-field displacement probe remains required before acceptance.']}
(out/'pose-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
