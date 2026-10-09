"""All receiver vertices against exact source under recorded production poses."""
import numpy as np,json,struct,sys,time,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[4]
intake,atlas,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
source=root/'harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb'
with source.open('rb') as f:
 h=f.read(20);j=json.loads(f.read(struct.unpack_from('<I',h,12)[0]));binstart=28+struct.unpack_from('<I',h,12)[0]
 ac=j['accessors'][j['skins'][0]['inverseBindMatrices']];v=j['bufferViews'][ac['bufferView']];f.seek(binstart+v.get('byteOffset',0));ib=np.frombuffer(f.read(v['byteLength']),'<f4').reshape(-1,4,4).transpose(0,2,1).astype(float)
names=[j['nodes'][n]['name'] for n in j['skins'][0]['joints']];assert len(names)==75
sp=np.fromfile(intake/'POSITION.bin','<f4').reshape(-1,3);sj=np.fromfile(intake/'JOINTS_0.bin',np.uint8).reshape(-1,4);sw=np.fromfile(intake/'WEIGHTS_0.bin','<f4').reshape(-1,4);si=np.fromfile(intake/'indices.bin','<u4').reshape(-1,3)
lp=np.fromfile(atlas/'POSITION.bin','<f4').reshape(-1,3);lj=np.fromfile(atlas/'JOINTS_0.bin',np.uint8).reshape(-1,4);lw=np.fromfile(atlas/'WEIGHTS_0.bin','<f4').reshape(-1,4)
faces=np.fromfile(atlas/'source-face.u32','<u4');bc=np.fromfile(atlas/'source-bary.f32','<f4').reshape(-1,3);srcrows=si[faces];n=len(lp);assert len(faces)==n and lj.max()<75
rows=np.arange(n);expected=np.zeros((n,75,4),np.float64);p=np.column_stack([sp,np.ones(len(sp))]);lowp=np.column_stack([lp,np.ones(n)])
for corner in range(3):
 sourceverts=srcrows[:,corner]
 for slot in range(4):np.add.at(expected,(rows,sj[sourceverts,slot]),p[sourceverts]*(sw[sourceverts,slot]*bc[:,corner])[:,None])
nearestrows=srcrows[rows,bc.argmax(1)];nj=sj[nearestrows];nw=sw[nearestrows]
def delta(joints,weights):
 a=-expected.copy()
 for slot in range(4):np.add.at(a,(rows,joints[:,slot]),lowp*weights[:,slot,None])
 return a.reshape(n,300)
top=delta(lj,lw);del expected
results=[];vertexMax={k:np.zeros(n) for k in ('collapseNativeTop4',)}
for bike in ('rookie','pro'):
 path=root/f'harness/out/rider-rebuild/selected-ankle-field42/gameplay-{bike}01/report.json';r=json.loads(path.read_text());assert r['source']['source']['sha256']=='127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649'
 samples=r['played']['motionSamples'];poseMax={k:[] for k in vertexMax};worst={};palmDiff=0
 for sample in samples:
  byId={b['id']:b for b in sample['joints']};world=np.array([byId[name]['worldMatrix'] for name in names]).reshape(75,4,4).transpose(0,2,1);mat=world@ib
  # Node82 root and mesh80 bind transforms are identity in source. Attached
  # skinning cancels mesh.matrixWorld; rendered world position is sum(J*IBM*p).
  # Compare in world metres, then prove skeletonWorld is a rigid basis.
  skeleton=np.array(sample['skeletonWorld']).reshape(4,4).T;assert np.max(np.abs(skeleton[:3,:3].T@skeleton[:3,:3]-np.eye(3)))<1e-6
  for side in ('L','R'):
   hand=names.index('DEF-hand.'+side)
   for palm in range(1,5):palmDiff=max(palmDiff,float(np.max(np.abs(mat[names.index(f'DEF-palm.0{palm}.'+side)]-mat[hand]))))
  flat=mat[:,:3,:].transpose(0,2,1).reshape(300,3)
  for key,data in [('collapseNativeTop4',top)]:
   error=np.linalg.norm(data@flat,axis=1);vertexMax[key]=np.maximum(vertexMax[key],error);poseMax[key].append(float(error.max()))
   if key not in worst or error.max()>worst[key]['meters']:
    v=int(error.argmax());worst[key]={'meters':float(error[v]),'vertex':v,'sourceFace':int(faces[v]),'tick':sample['tick'],'phase':sample['phase'],'localPosition':lp[v].tolist()}
 results.append({'bike':bike,'reportSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'recordedPoses':len(samples),'worst':worst,'poseMaximumMeters':{k:{'mean':float(np.mean(v)),'max':max(v)} for k,v in poseMax.items()},'maxPalmHandSkinMatrixComponentDifference':palmDiff})
 print(bike,results[-1]['worst'],flush=True)
report={'accepted':False,'sourceSHA256':'127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649','method':'Every final seam vertex; exact original source face barycentric weighted skinned positions versus collapse-propagated native top4 receiver skinned positions under every recorded actual gameplay pose. Native inverse binds and original75jointorder. Identity native mesh/root bind; attached-mode world cancellation; rigid skeletonWorld verified.','vertices':n,'bikes':results,'allPoseVertexErrorMeters':{k:{'mean':float(v.mean()),'p95':float(np.quantile(v,.95)),'p99':float(np.quantile(v,.99)),'max':float(v.max()),'verticesAbove1mm':int((v>.001).sum()),'verticesAbove2mm':int((v>.002).sum())} for k,v in vertexMax.items()},'elapsedSeconds':time.monotonic()-start,'limitations':'Recorded neutral/forward/back gameplay only. Source face correspondence follows exact nearest rest surface; no future or unsampled crash/ragdoll guarantee.'}
(out/'motion.json').write_text(json.dumps(report,indent=2)+'\n');np.savez(out/'vertex-errors.npz',**vertexMax);print(json.dumps(report['allPoseVertexErrorMeters']))
