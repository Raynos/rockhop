"""Persist clean elbow and actual source34 matrices without inventing game states."""
from data import *
from source34 import *
import hashlib
f=np.load(HERE/'input/v7-bind.npz');pp=[f[f'p{i}']for i in range(5)];ws=[f[f'W{i}']for i in range(5)];tri=[f[f'tr{i}']for i in range(5)]
base=np.concatenate([pp[0],pp[2]]);src=np.concatenate([POS[0],POS[2]]);tr=np.concatenate([tri[0],tri[2]+len(pp[0])]);roi=((src[tr][:,:,1]>1.08)&(src[tr][:,:,1]<1.49)&(abs(src[tr][:,:,2])<.405)).all(1);tr=tr[roi]
ed=np.unique(np.sort(np.concatenate([tr[:,[0,1]],tr[:,[1,2]],tr[:,[0,2]]]),axis=1),axis=0);l0=np.linalg.norm(base[ed[:,0]]-base[ed[:,1]],axis=1);a0=np.linalg.norm(np.cross(base[tr[:,1]]-base[tr[:,0]],base[tr[:,2]]-base[tr[:,0]]),axis=1)
folder=HERE/'isolation-poses';folder.mkdir(exist_ok=True)
def emit(label,D,metadata):
 pts=deform(pp,ws,D);q=np.concatenate([pts[0],pts[2]]);rat=np.linalg.norm(q[ed[:,0]]-q[ed[:,1]],axis=1)/np.maximum(l0,1e-15);ar=np.linalg.norm(np.cross(q[tr[:,1]]-q[tr[:,0]],q[tr[:,2]]-q[tr[:,0]]),axis=1)/np.maximum(a0,1e-15)
 path=folder/(label+'.npz');np.savez(path,matrices=D,**{f'p{i}':p for i,p in enumerate(pts)},**{f'tr{i}':t for i,t in enumerate(tri)})
 return dict(metadata,id=label,path=str(path),worldMatricesSHA256=hashlib.sha256(D.tobytes()).hexdigest(),upperClothMaxEdge2mm=float(rat[l0>=.002].max()),upperClothP99Edge2mm=float(np.quantile(rat[l0>=.002],.99)),upperClothCompressedBelowQuarter=int((ar<.25).sum()))
rows=[]
for side in ['both','L','R']:
 for angle in [0,15,30,45,60,75,90,105,120]:
  D=neutral_elbow(angle,side);rows.append(emit(f'neutral-elbow-{side}-{angle}',D,{'probe':'neutral_elbow','side':side,'degrees':angle,'holdout':angle in [15,45,75,105],'headTorsoMatricesIdentity':bool(np.array_equal(D[:5],np.repeat(np.eye(4)[None],5,axis=0))),'correctiveMorphsActive':False}))
actual=[];doc=json.loads(DEFAULT_MANIFEST.read_text())
for row in doc['rows']:
 i=row['i'];D,meta=source34_world_matrices(i);diff=max(float(np.abs(source34_world_matrices(i,primitive=j)[0]-D).max())for j in range(len(doc['primitives'])));meta['maxAcrossPrimitiveMatrixDifference']=diff
 source=emit(f'source34-{i}',D,dict(meta,probe='source34_actual',variant='source'))
 # Actual recorded morph weights are unavailable in the CPUdump; frozen V7
 # geometry replay deliberately holds all morphs zero for the motion ablation.
 E,audit=rigid_arm_control(D);candidate=emit(f'source34-rigid-arms-{i}',E,dict(meta,probe='source34_actual',variant='rigid_arms',armAudit=audit,nonArmSourceMatricesExact=bool(np.array_equal(E[[0,1,2,3,4,5,9,13,14,15,16,17,18]],D[[0,1,2,3,4,5,9,13,14,15,16,17,18]]))))
 actual.extend([source,candidate])
(HERE/'neutral-elbow-manifest.json').write_text(json.dumps({'rows':rows,'frozenBindSHA256':hashlib.sha256((HERE/'input/v7-bind.npz').read_bytes()).hexdigest(),'limits':'Finite clean elbow-only fixtures, not game envelope or continuous selfcollision acceptance.'},indent=2))
(HERE/'source34-manifest.json').write_text(json.dumps({'rows':actual,'sourceManifestPath':str(DEFAULT_MANIFEST),'sourceRawPath':str(DEFAULT_RAW),'correctiveMorphsActive':False,'limits':['Four actual recorded-state source34 frames only; not stand/Garage/landing envelope coverage.','All frozen V7 morphs held zero for matched motion ablation. Source34 contacts describe recorded source geometry, not new V7 contact qualification.','Rigid arm candidate preserves source end effectors; no collision/contact/visual pass claimed.']},indent=2))
print(json.dumps({'neutralRows':len(rows),'actualRows':len(actual),'elbowBothEndpoints':[{k:r[k]for k in ['degrees','upperClothMaxEdge2mm','upperClothCompressedBelowQuarter']}for r in rows if r['side']=='both'and r['degrees']in[30,60,90,120]],'actual':[{k:r[k]for k in ['id','upperClothMaxEdge2mm','upperClothCompressedBelowQuarter']}for r in actual]},indent=2))
