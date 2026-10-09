"""Independently query actual posed donor geometry at failing interior witnesses."""
import bpy,numpy as np,json,struct,sys,time,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
intake,atlas,interior,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True);start=time.monotonic();root=Path(__file__).resolve().parents[4]
source=root/'harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb'
with source.open('rb') as f:
 h=f.read(20);j=json.loads(f.read(struct.unpack_from('<I',h,12)[0]));binstart=28+struct.unpack_from('<I',h,12)[0];ac=j['accessors'][j['skins'][0]['inverseBindMatrices']];v=j['bufferViews'][ac['bufferView']];f.seek(binstart+v.get('byteOffset',0));ib=np.frombuffer(f.read(v['byteLength']),'<f4').reshape(-1,4,4).transpose(0,2,1).astype(float)
names=[j['nodes'][i]['name'] for i in j['skins'][0]['joints']]
def read(d,n,t,w):return np.fromfile(d/(n+'.bin'),t).reshape(-1,w)
sp=read(intake,'POSITION','<f4',3);sj=read(intake,'JOINTS_0','u1',4);sw=read(intake,'WEIGHTS_0','<f4',4);si=read(intake,'indices','<u4',3)
lp=read(atlas,'POSITION','<f4',3);lj=read(atlas,'JOINTS_0','u1',4);lw=read(atlas,'WEIGHTS_0','<f4',4);li=read(atlas,'indices','<u4',3)
witness=np.load(interior/'interior-witnesses.npz');selected=np.flatnonzero(witness['maximumMeters']>.001);faces=witness['sourceFaces'][selected];bc=witness['sourceBary'][selected];n=len(selected);assert n>0
sourcep=np.column_stack([sp,np.ones(len(sp))]);lowp=np.column_stack([lp,np.ones(len(lp))]);delta=np.zeros((n,75,4));rows=np.arange(n)
for corner in range(3):
 lv=li[selected,corner];sv=si[faces,corner]
 for slot in range(4):
  np.add.at(delta,(rows,lj[lv,slot]),lowp[lv]*(lw[lv,slot]/3)[:,None]);np.add.at(delta,(rows,sj[sv,slot]),-sourcep[sv]*(sw[sv,slot]*bc[:,corner])[:,None])
delta=delta.reshape(n,300);maximum=np.zeros(n);worst=[None]*n;pose_matrices={}
for bike in ('rookie','pro'):
 path=root/f'harness/out/rider-rebuild/selected-ankle-field42/gameplay-{bike}01/report.json';report=json.loads(path.read_text())
 for sample in report['played']['motionSamples']:
  byId={b['id']:b for b in sample['joints']};world=np.array([byId[name]['worldMatrix'] for name in names]).reshape(75,4,4).transpose(0,2,1);mat=world@ib;error=np.linalg.norm(delta@mat[:,:3,:].transpose(0,2,1).reshape(300,3),axis=1);key=(bike,sample['tick'])
  for at in np.flatnonzero(error>maximum):maximum[at]=error[at];worst[at]=key
  pose_matrices[key]=mat
unique=sorted(set(worst));results=[]
def skin(pos,ids,weights,mat):
 hom=np.column_stack([pos,np.ones(len(pos))]);result=np.zeros((len(pos),3))
 for slot in range(4):result+=np.einsum('nij,nj->ni',mat[ids[:,slot],:3,:],hom)*weights[:,slot,None]
 return result
for key in unique:
 mat=pose_matrices[key];posed=skin(sp,sj,sw,mat);tree=BVHTree.FromPolygons(posed.tolist(),si.tolist(),all_triangles=True)
 for at in [i for i,k in enumerate(worst) if k==key]:
  triangle=int(selected[at]);indices=li[triangle];low=skin(lp[indices],lj[indices],lw[indices],mat);p=low.mean(0);normal=np.cross(low[1]-low[0],low[2]-low[0]);normal/=np.linalg.norm(normal);hit,norm,face,d=tree.find_nearest(Vector(p));opposed=float(np.array(norm)@normal)<=0;missing=False
  if opposed:
   candidates=[q for q in tree.find_nearest_range(Vector(p),max(.0005,d*2+1e-7)) if np.array(q[1])@normal>0]
   if candidates:hit,norm,face,d=min(candidates,key=lambda q:q[3])
   else:missing=True
  results.append({'triangle':triangle,'bike':key[0],'tick':key[1],'restCorrespondencePoseErrorMeters':float(maximum[at]),'targetPosedCentroid':p.tolist(),'actualPosedSourceFace':face,'actualPosedDistanceMeters':d,'actualSourceNormalDot':float(np.array(norm)@normal),'originalPosedNearestOpposed':opposed,'facingSourceMissing':missing,'targetNativeCornerSupport':[[{'joint':names[int(jj)],'weight':float(ww)} for jj,ww in zip(lj[v],lw[v]) if ww>0] for v in indices]})
 del tree,posed
valid=[r['actualPosedDistanceMeters'] for r in results if not r['facingSourceMissing']];a=np.array(valid)
summary={'accepted':False,'sourceSHA256':'127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649','method':'Only recorded failing interior witnesses, each at its independently recovered worst recordedpose. CPU skin entire original donor using native75 and original4slots, build posed donorBVH, query actual receiver skinned-centroid nearest same-facing source geometry. No source joint/weight field enters query selection.','witnesses':len(results),'uniqueWorstRecordedPoses':len(unique),'sameFacingMeasured':len(valid),'sameFacingMissing':sum(r['facingSourceMissing'] for r in results),'actualPosedSurfaceDistanceMeters':{'mean':float(a.mean()),'p95':float(np.quantile(a,.95)),'p99':float(np.quantile(a,.99)),'max':float(a.max())},'witnessesAbove1mm':sum(d>.001 for d in valid),'witnessesAbove2mm':sum(d>.002 for d in valid),'elapsedSeconds':time.monotonic()-start,'limits':'Failing centroid witness geometric check only. Material/normal continuity and corrected grip/alltriangle future poses remain separate. No player asset changes.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(out/'witnesses.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(summary))
