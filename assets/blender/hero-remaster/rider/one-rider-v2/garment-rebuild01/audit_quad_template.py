"""Read-only native02 topology audit before fitting or appearance work."""
from pathlib import Path
import hashlib,json,numpy as np
p=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/source/male_casualsuit02.obj');out=Path('docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01')
v=[];f=[]
for line in p.read_text().splitlines():
 if line.startswith('v '):v.append([float(x) for x in line.split()[1:4]])
 if line.startswith('f '):f.append([int(x.split('/')[0])-1 for x in line.split()[1:]])
v=np.array(v);f=np.array(f);assert f.shape==(2060,4) and v.shape==(2136,3)
parent=np.arange(len(v))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for face in f:
 for b in face[1:]:parent[find(b)]=find(face[0])
labels=np.array([find(i) for i in range(len(v))]);rows=[]
for label in np.unique(labels):
 ids=np.flatnonzero(labels==label);mask=np.all(labels[f]==label,axis=1);faces=f[mask];edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,3]],faces[:,[3,0]]]),axis=1);ed,count=np.unique(edges,axis=0,return_counts=True);boundary=ed[count==1];degree=np.bincount(boundary.reshape(-1),minlength=len(v));q=v[faces];area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)/2+np.linalg.norm(np.cross(q[:,2]-q[:,0],q[:,3]-q[:,0]),axis=1)/2
 rows.append({'rootVertex':int(label),'vertices':len(ids),'quads':len(faces),'bounds':np.c_[v[ids].min(0),v[ids].max(0)].tolist(),'boundaryEdges':len(boundary),'nonManifoldEdges':int((count>2).sum()),'boundaryVerticesNotDegree2':int(((degree>0)&(degree!=2)).sum()),'zeroAreaQuads':int((area<1e-12).sum()),'sourceFaceIndices':np.flatnonzero(mask).tolist()})
assert all(r['nonManifoldEdges']==r['boundaryVerticesNotDegree2']==r['zeroAreaQuads']==0 for r in rows)
report={'status':'Native02 garment topology retained for fitting; not appearance/animation accepted','sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'vertices':len(v),'quads':len(f),'connectedComponents':len(rows),'components':rows,'mechanism':'Clean separately authored quad garment template, anatomically placed sleeve and hip/knee loops. Replace faulty deformation topology rather than keep regenerating scalar weights on fused H21surface. Keep generated mesh/detail as bake donor and protect approved head/hood/gloves/shoes.','limits':['No assertion that topology alone fixes anatomy or posing.','Native snapshot differs from selected rider; fitting, hood join, material bake and actual game motion remain gates.','No inherited base body, hair or face substituted; source templates are private, unaccepted construction evidence.']}
(out/'native02-topology-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k!='sourceFaceIndices'} for r in rows],indent=2))
