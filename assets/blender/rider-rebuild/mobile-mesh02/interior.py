"""Every receiver triangle centroid against its geometrically facing source sheet."""
import bpy,numpy as np,json,struct,sys,hashlib,time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
intake,atlas,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
root=Path(__file__).resolve().parents[4];source=root/'harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb'
with source.open('rb') as f:
 h=f.read(20);j=json.loads(f.read(struct.unpack_from('<I',h,12)[0]));binstart=28+struct.unpack_from('<I',h,12)[0]
 ac=j['accessors'][j['skins'][0]['inverseBindMatrices']];v=j['bufferViews'][ac['bufferView']];f.seek(binstart+v.get('byteOffset',0));ib=np.frombuffer(f.read(v['byteLength']),'<f4').reshape(-1,4,4).transpose(0,2,1).astype(float)
names=[j['nodes'][n]['name'] for n in j['skins'][0]['joints']];assert len(names)==75
sp=np.fromfile(intake/'POSITION.bin','<f4').reshape(-1,3);sj=np.fromfile(intake/'JOINTS_0.bin',np.uint8).reshape(-1,4);sw=np.fromfile(intake/'WEIGHTS_0.bin','<f4').reshape(-1,4);si=np.fromfile(intake/'indices.bin','<u4').reshape(-1,3)
lp=np.fromfile(atlas/'POSITION.bin','<f4').reshape(-1,3);lj=np.fromfile(atlas/'JOINTS_0.bin',np.uint8).reshape(-1,4);lw=np.fromfile(atlas/'WEIGHTS_0.bin','<f4').reshape(-1,4);li=np.fromfile(atlas/'indices.bin','<u4').reshape(-1,3)
tri=lp[li];centers=tri.mean(1);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normal,axis=1);assert np.all(length>1e-15);normal/=length[:,None]
tree=BVHTree.FromPolygons(sp.tolist(),si.tolist(),all_triangles=True);n=len(li);faces=np.zeros(n,np.uint32);bcs=np.zeros((n,3));distances=np.zeros(n);opposed=0;misses=[]
def bary(p,tri):
 a,b,c=tri;v0=b-a;v1=c-a;v2=p-a;d00=v0@v0;d01=v0@v1;d11=v1@v1;den=d00*d11-d01*d01
 if abs(den)<1e-30:return np.array([1,0,0])
 v=(d11*(v2@v0)-d01*(v2@v1))/den;w=(d00*(v2@v1)-d01*(v2@v0))/den;q=np.clip([1-v-w,v,w],0,1);return q/q.sum()
for row,p in enumerate(centers):
 hit,norm,face,distance=tree.find_nearest(Vector(p))
 if np.array(norm)@normal[row]<=0:
  opposed+=1;candidates=[q for q in tree.find_nearest_range(Vector(p),max(.0005,distance*2+1e-7)) if np.array(q[1])@normal[row]>0]
  if not candidates:misses.append(row)
  else:hit,norm,face,distance=min(candidates,key=lambda q:q[3])
 faces[row]=face;bcs[row]=bary(np.array(hit),sp[si[face]]);distances[row]=distance
covered=np.ones(n,bool);covered[misses]=False;assert covered.any()
rows=np.arange(n);delta=np.zeros((n,75,4));sourcep=np.column_stack([sp,np.ones(len(sp))]);lowp=np.column_stack([lp,np.ones(len(lp))])
for corner in range(3):
 lv=li[:,corner];sv=si[faces,corner]
 for slot in range(4):
  np.add.at(delta,(rows,lj[lv,slot]),lowp[lv]*(lw[lv,slot]/3)[:,None])
  np.add.at(delta,(rows,sj[sv,slot]),-sourcep[sv]*(sw[sv,slot]*bcs[:,corner])[:,None])
delta=delta.reshape(n,300);maximum=np.zeros(n);results=[]
for bike in ('rookie','pro'):
 path=root/f'harness/out/rider-rebuild/selected-ankle-field42/gameplay-{bike}01/report.json';r=json.loads(path.read_text());assert r['source']['source']['sha256']=='127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649';worst=None
 for sample in r['played']['motionSamples']:
  byId={b['id']:b for b in sample['joints']};world=np.array([byId[name]['worldMatrix'] for name in names]).reshape(75,4,4).transpose(0,2,1);mat=world@ib;flat=mat[:,:3,:].transpose(0,2,1).reshape(300,3)
  error=np.linalg.norm(delta@flat,axis=1);maximum=np.maximum(maximum,error);at=int(np.argmax(np.where(covered,error,-1)))
  if worst is None or error[at]>worst['meters']:worst={'meters':float(error[at]),'triangle':at,'sourceFace':int(faces[at]),'tick':sample['tick'],'phase':sample['phase'],'localPosition':centers[at].tolist()}
 results.append({'bike':bike,'recordedPoses':len(r['played']['motionSamples']),'reportSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'worst':worst})
def stats(a):return {k:float(v) for k,v in [('mean',a.mean()),('p95',np.quantile(a,.95)),('p99',np.quantile(a,.99)),('max',a.max())]}
report={'accepted':False,'method':'Every receiver triangle centroid. Independently choose nearest source geometric face in the same facing hemisphere; no native joint/weight field enters source-face selection. Original nearest opposed-sheet counts retained. Compare exact native75 LBS coefficient fields under all482historical played poses.','triangles':n,'originalNearestOpposedFaces':opposed,'facingSourceMisses':len(misses),'measuredFacingTriangles':int(covered.sum()),'missingFacingWitnesses':[{'triangle':int(v),'localPosition':centers[v].tolist(),'geometricNormal':normal[v].tolist(),'nearestSourceFace':int(faces[v]),'nearestDistanceMeters':float(distances[v]),'nativeCornerSupport':[[{'joint':names[int(jj)],'weight':float(ww)} for jj,ww in zip(lj[vertex],lw[vertex]) if ww>0] for vertex in li[v]],'unconstrainedNearestPoseErrorMeters':float(maximum[v]),'qualification':'No same-facing source within original0.5mmminimum search; nearest result retained as ambiguous, not counted as qualified coverage.'} for v in misses],'restSourceSurfaceMeters':stats(distances[covered]),'playedInteriorErrorMeters':stats(maximum[covered]),'trianglesAbove1mm':int((maximum[covered]>.001).sum()),'trianglesAbove2mm':int((maximum[covered]>.002).sum()),'bikes':results,'elapsedSeconds':time.monotonic()-start,'limits':'Centroids and recorded neutral/forward/back gameplay only; no exhaustive intra-triangle or future corrected-grip guarantee. Rest source is geometrically overlapping in some places, hemisphere correspondence is explicit and original nearest failures retained elsewhere.'}
(out/'interior.json').write_text(json.dumps(report,indent=2)+'\n');np.savez(out/'interior-witnesses.npz',sourceFaces=faces,sourceBary=bcs,centers=centers,maximumMeters=maximum);print(json.dumps(report))
