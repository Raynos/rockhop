"""Inspect the first failed native deformation witness without modifying meshes."""
import bpy,numpy as np,json,sys,struct,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
base,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
i=base/'intake01';b=base/'bake01';vertex=11107
sp=np.fromfile(i/'POSITION.bin','<f4').reshape(-1,3);sn=np.fromfile(i/'NORMAL.bin','<f4').reshape(-1,3);si=np.fromfile(i/'indices.bin','<u4').reshape(-1,3);sj=np.fromfile(i/'JOINTS_0.bin','u1').reshape(-1,4);sw=np.fromfile(i/'WEIGHTS_0.bin','<f4').reshape(-1,4)
lp=np.fromfile(b/'POSITION.bin','<f4').reshape(-1,3);lj=np.fromfile(b/'JOINTS_0.bin','u1').reshape(-1,4);lw=np.fromfile(b/'WEIGHTS_0.bin','<f4').reshape(-1,4);ln=np.fromfile(b/'NORMAL.bin','<f4').reshape(-1,3)
faces=np.fromfile(b/'source-face.u32','<u4');bc=np.fromfile(b/'source-bary.f32','<f4').reshape(-1,3);face=int(faces[vertex])
source=Path(json.loads((i/'intake.json').read_text())['source'])
with source.open('rb') as f:h=f.read(20);j=json.loads(f.read(struct.unpack_from('<I',h,12)[0]))
names=[j['nodes'][n]['name'] for n in j['skins'][0]['joints']]
def field(ids,weights):
 a=np.bincount(ids.ravel(),weights=weights.ravel(),minlength=75);return {names[k]:float(w) for k,w in enumerate(a) if w>1e-7}
def bary(p,tri):
 a,c,d=tri;v0=c-a;v1=d-a;v2=p-a;d00=v0@v0;d01=v0@v1;d11=v1@v1;den=d00*d11-d01*d01
 if abs(den)<1e-30:return np.array([1,0,0])
 v=(d11*(v2@v0)-d01*(v2@v1))/den;w=(d00*(v2@v1)-d01*(v2@v0))/den;q=np.clip([1-v-w,v,w],0,1);return q/q.sum()
rows=si[face];dst=np.bincount(lj[vertex],weights=lw[vertex],minlength=75)
tree=BVHTree.FromPolygons(sp.tolist(),si.tolist(),all_triangles=True);near=[]
for hit,n,f,d in tree.find_nearest_range(Vector(lp[vertex]),.0003):
 ids=si[f];w=bary(np.array(hit),sp[ids]);nf=np.bincount(sj[ids].ravel(),weights=(sw[ids]*w[:,None]).ravel(),minlength=75)
 nn=(sn[ids]*w[:,None]).sum(0);nn/=np.linalg.norm(nn)
 near.append({'sourceFace':f,'distanceMeters':d,'sourceField':field(sj[ids],sw[ids]*w[:,None]),'targetWeightL1':float(abs(nf-dst).sum()),'normalDotReceiver':float(nn@ln[vertex]),'bary':w.tolist()})
r={'accepted':False,'vertex':vertex,'targetPosition':lp[vertex].tolist(),'targetField':field(lj[vertex],lw[vertex]),'declaredNearestFace':face,'declaredSourceBary':bc[vertex].tolist(),'declaredSourceField':field(sj[rows],sw[rows]*bc[vertex,:,None]),'cornerFields':[field(sj[v],sw[v]) for v in rows],'cornerDistancesMeters':np.linalg.norm(sp[rows]-lp[vertex],axis=1).tolist(),'sourceNearbyFaces':sorted(near,key=lambda a:a['distanceMeters']),'limits':'Local forensic witness, not an alternative skin fit or played acceptance.'}
(out/'witness.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
