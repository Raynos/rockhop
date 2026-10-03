from motion import *
import hashlib
from data import POS,OFF,INV,U,deform
frozen=np.load(HERE/'input/v7-bind.npz');pp=[frozen[f'p{i}']for i in range(5)];ws=[frozen[f'W{i}']for i in range(5)];tris=[frozen[f'tr{i}']for i in range(5)]
base=np.concatenate([pp[0],pp[2]]);source=np.concatenate([POS[0],POS[2]]);tri=np.concatenate([tris[0],tris[2]+len(pp[0])])
roi=((source[tri][:,:,1]>1.08)&(source[tri][:,:,1]<1.49)&(abs(source[tri][:,:,2])<.405)).all(1);tr=tri[roi]
edges=np.unique(np.sort(np.concatenate([tr[:,[0,1]],tr[:,[1,2]],tr[:,[0,2]]]),axis=1),axis=0)
l0=np.linalg.norm(base[edges[:,0]]-base[edges[:,1]],axis=1);a0=np.linalg.norm(np.cross(base[tr[:,1]]-base[tr[:,0]],base[tr[:,2]]-base[tr[:,0]]),axis=1)
(HERE/'poses').mkdir(exist_ok=True)
rows=[]
protocol=[('neutral',0)]+[(kind,t)for kind in ['horizontal','overhead','functional_overhead','forward','elbow','legacy_elbow']for t in [.0,.125,.25,.375,.5,.625,.75,.875,1]]+[(kind,t)for kind in ['forearm_twist','legacy_distal_axial','wrist_flex','wrist_deviation']for t in [-1,-.5,0,.5,1]]
for kind,t in protocol:
 for variant in ['legacy','fixed_ik','girdle']:
  D,rec=arm_pose(kind,t,variant=variant);pts=deform(pp,ws,D,False);q=np.concatenate([pts[0],pts[2]])
  ratio=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/np.maximum(l0,1e-15);area=np.linalg.norm(np.cross(q[tr[:,1]]-q[tr[:,0]],q[tr[:,2]]-q[tr[:,0]]),axis=1)/np.maximum(a0,1e-15)
  good=l0>=.002;fn=f'{variant}-{kind}-{t:g}.npz';path=HERE/'poses'/fn
  np.savez(path,**{f'p{i}':p for i,p in enumerate(pts)},matrices=D,**{f'tr{i}':x for i,x in enumerate(tris)})
  Q=centres(D)
  # Exact all-primitive source aliases are frozen, including127cuffvertices.
  _,alias=np.unique(np.concatenate(POS),axis=0,return_inverse=True);cnt=np.bincount(alias);sumq=np.zeros((len(cnt),3));np.add.at(sumq,alias,np.concatenate(pts));sumq/=cnt[:,None]
  aliasgap=float(np.linalg.norm(np.concatenate(pts)-sumq[alias],axis=1).max())
  handerr=max([s['handTargetErrorM']for s in rec['sides']]or[0]);rotations=[s['handRotationErrorRad']for s in rec['sides']]
  rec.update({'path':str(path),'geometryRestPath':str(HERE/'input/v7-bind.npz'),'worldMatricesSHA256':hashlib.sha256(D.tobytes()).hexdigest(),'upperClothMaxEdge2mm':float(ratio[good].max()),'upperClothP99Edge2mm':float(np.quantile(ratio[good],.99)),'upperClothCompressedBelowQuarter':int((area<.25).sum()),'sourceExactAliasGapM':aliasgap,'headTorsoJointMatricesExact':bool(np.array_equal(D[[0,1,2,3,4]],np.repeat(np.eye(4)[None],5,axis=0))),'handTargetMaxErrorM':handerr,'handRotationMaxErrorRad':max(rotations or[0]),'holdoutSample':bool(t in [.125,.375,.625,.875])});rows.append(rec)
manifest={'frozenBindSHA256':hashlib.sha256((HERE/'input/v7-bind.npz').read_bytes()).hexdigest(),'rows':rows,'poseCount':len(rows),'api':str(HERE/'motion.py'),'geometryWeightsFixed':True,'correctiveMorphsActive':False,'protocol':'All variants apply same frozen V7bindandweights. Legacy directfixedglenoid; fixed_ik restgirdle withsame handtarget+orientation; girdle samehandtarget+orientation+existing shoulderproxy8elev/6retraction. Sourceoverhead174.29elevationstress separatefunctional140overhead. Arms0startsneutral; elbow/wrist0startsforward.7. Finite9samplemotioncurves, noCCD.','clinicalLimitClaim':False,'limits':'Single clavicleproxy is not separate scapulamodel. Axes estimatedfrommesh/jointcentres, no anatomy scan. Anatomicalwristaxes are transverse toforearm; hand90distalaxialstress clearlylegacy. No newbone or weightchange. Posed shape body/head unchanged except inevitable existinglineararmweightleakage.'}
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2))
summary=[]
for k in ['horizontal','overhead','functional_overhead','forward','elbow','legacy_elbow']:
 for row in rows:
  if row['kind']==k and row['fraction']==1:summary.append({x:row[x]for x in ['variant','kind','upperClothMaxEdge2mm','upperClothP99Edge2mm','upperClothCompressedBelowQuarter','handTargetMaxErrorM']})
(HERE/'quick-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({'poses':len(rows),'summary':summary},indent=2))
