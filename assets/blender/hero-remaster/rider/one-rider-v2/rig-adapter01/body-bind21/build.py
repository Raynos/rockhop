"""One byte-conserving anatomical sleeve weight trial. CPU only; no sweep."""
import json
import numpy as np
from scipy.sparse import coo_matrix
from common import SOURCE,RUN,OUT,load,accessor,sha
np.seterr(all='raise');raw,j,b,p,start=load();OUT.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True)
rest,_,_=accessor(j,b,p['attributes']['POSITION']);tri=accessor(j,b,p['indices'])[0].reshape(-1,3);si,siat,sistride=accessor(j,b,p['attributes']['JOINTS_0']);sw,swat,swstride=accessor(j,b,p['attributes']['WEIGHTS_0']);bones=[j['nodes'][n]['name'] for n in j['skins'][0]['joints']];idx={name:i for i,name in enumerate(bones)};ib=accessor(j,b,j['skins'][0]['inverseBindMatrices'])[0];origins=np.linalg.inv(ib.reshape(-1,4,4).transpose(0,2,1))[:,:3,3]
W=np.zeros((len(rest),19))
for lane in range(4):np.add.at(W,(np.arange(len(rest)),si[:,lane]),sw[:,lane])
u,first,inv=np.unique(rest,axis=0,return_index=True,return_inverse=True);UW=W[first];assert np.max(np.abs(W-UW[inv]))<1e-7
ut=inv[tri];edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]];adj=coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(u),len(u))).tocsr()
# Exact shared-position aliases in hood/other material primitives remain pinned.
shared=np.zeros(len(u),bool);lookup={tuple(q):i for i,q in enumerate(u)}
for other in j['meshes'][0]['primitives'][1:]:
 for q in accessor(j,b,other['attributes']['POSITION'])[0]:
  if tuple(q) in lookup:shared[lookup[tuple(q)]]=True
C=UW.copy();allEligible=np.zeros(len(u),bool);boundaries=np.zeros(len(u),bool);records=[]
torso=[idx[n] for n in ['pelvis','spine','chest']];forbidden=[idx[n] for n in ['neck','head','hand.L','hand.R','thigh.L','thigh.R','shin.L','shin.R','foot.L','foot.R']]
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
for side,sign in [('L',1),('R',-1)]:
 upper,fore=[idx[n+'.'+side] for n in ['upperArm','forearm']];shoulder=origins[upper];elbow=origins[fore];wrist=origins[idx['hand.'+side]]
 a=elbow-shoulder;c=wrist-elbow;dir=(a/np.linalg.norm(a)+c/np.linalg.norm(c));dir/=np.linalg.norm(dir)
 def segment_distance(a0,a1):
  d=a1-a0;t=np.clip(np.einsum('vi,i->v',u-a0,d)/np.dot(d,d),0,1);return np.linalg.norm(u-(a0+t[:,None]*d),axis=1)
 shaft=np.minimum(segment_distance(shoulder,elbow),segment_distance(elbow,wrist));arm=UW[:,upper]+UW[:,fore]
 eligible=(u[:,1]>.95)&(u[:,1]<1.38)&(sign*u[:,2]>.18)&(shaft<.14)&(arm>.3)&(UW[:,forbidden].sum(1)<1e-7)&(~shared)
 # Original graph pinning preserves ROI exterior and its first physical ring.
 boundary=eligible&((adj@(~eligible).astype(float))>0);distance=np.full(len(u),-1,int);distance[boundary]=0;front=boundary.copy()
 for level in range(1,5):
  front=eligible&(distance<0)&((adj@front.astype(float))>0);distance[front]=level
 depth=np.where(distance<0,5,distance);alpha=smooth(depth/4)*smooth((u[:,1]-.95)/.06)*smooth((1.38-u[:,1])/.06)*smooth((sign*u[:,2]-.18)/.04);alpha[~eligible]=0
 contaminated=eligible&(UW[:,torso].sum(1)>1e-6)&(alpha>0)
 longitudinal=np.einsum('vi,i->v',u-elbow,dir);foreFraction=smooth((longitudinal+.085)/.17)
 for v in np.flatnonzero(contaminated):
  target=UW[v].copy();mass=target[torso].sum()+target[upper]+target[fore];target[torso]=0;target[upper]=mass*(1-foreFraction[v]);target[fore]=mass-target[upper];C[v]=UW[v]+alpha[v]*(target-UW[v]);C[v,fore]+=UW[v].sum()-C[v].sum()
 allEligible|=eligible;boundaries|=boundary;records.append({'side':side,'eligiblePhysicalVertices':int(eligible.sum()),'torsoContaminatedChangedPhysicalVertices':int(contaminated.sum()),'pinnedBoundaryPhysicalVertices':int(boundary.sum()),'bindShoulder':shoulder.tolist(),'bindElbow':elbow.tolist(),'bindWrist':wrist.tolist(),'blendDirection':dir.tolist()})
changedPhysical=np.flatnonzero(np.max(np.abs(C-UW),axis=1)>1e-7);candidate=C[inv];changed=np.flatnonzero(np.max(np.abs(candidate-W),axis=1)>1e-7);assert len(changed)>0;assert np.max(np.abs(C.sum(1)-UW.sum(1)))<1e-12;assert np.array_equal(C[boundaries|shared],UW[boundaries|shared]);assert np.array_equal(C[~allEligible],UW[~allEligible]);patched=bytearray(raw);allowed=set()
for v in changed:
 entries=sorted([(int(bone),float(weight)) for bone,weight in enumerate(candidate[v]) if weight>0],key=lambda pair:-pair[1]);assert len(entries)<=4
 entries += [(0,0)]*(4-len(entries))
 for lane,(bone,weight) in enumerate(entries):
  at=start+siat+v*sistride+lane;patched[at]=bone;allowed.add(at);at=start+swat+v*swstride+lane*4;patched[at:at+4]=np.float32(weight).tobytes();allowed.update(range(at,at+4))
result=bytes(patched);actual=[i for i,(a,c) in enumerate(zip(raw,result)) if a!=c];assert all(i in allowed for i in actual);assert result[:start]==raw[:start];assert SOURCE.read_bytes()==raw
path=RUN/'rider.glb'
if path.exists():assert path.read_bytes()==result,'A previous frozen trial must not be overwritten'
else:path.write_bytes(result)
settings={'singleConstruction':True,'parameterSweep':False,'sourceM':{'y':[.95,1.38],'lateralAbsZAbove':.18,'sourceArmShaftDistanceBelow':.14,'originalUpperForearmSumAbove':.3},'protection':'hood/other material exact-position aliases; hand/neck/head/leg influences excluded; first ROI graph ring pinned; outside ROI exact','redistribution':'torso mass removed only from contaminated eligible sleeves; native arm-chain longitudinal smooth upperArm/forearm transition +/-85mm around source elbow; preserve source weight sum','taper':'four source graph rings with cubic smoothstep; 60mm cuff/shoulder taper; 40mm lateral taper'}
report={'source':str(SOURCE),'sourceSHA256':sha(raw),'candidate':str(path),'candidateSHA256':sha(result),'changedExportVertices':len(changed),'changedPhysicalVertices':len(changedPhysical),'changedBytes':len(actual),'allNonSkinBytesExact':True,'JSONAndNodesExact':True,'protectedSharedAliasesExact':True,'protectedSharedPhysicalVertices':int(shared.sum()),'pinnedROIBoundaryExact':True,'outsideROIWeightsExact':True,'sourceWeightSumsPreservedBeforeFloat32':True,'sourceUnchanged':True,'sides':records,'settings':settings,'limits':'CPU-only unaccepted sleeve weight experiment; no rendered art score, rig or physics changes.'}
np.savez_compressed(RUN/'weight-field.npz',rest=rest,triangles=tri,original=W,candidate=candidate,unique=u,inverse=inv,changed=changed,eligible=allEligible,boundaries=boundaries,shared=shared);report['weightFieldSHA256']=sha((RUN/'weight-field.npz').read_bytes());(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'settings.json').write_text(json.dumps(settings,indent=2)+'\n');print(json.dumps(report))

# Preserve the original failed inner-elbow witness and exact mask membership.
witness=[]
for v in tri[3789]:
 uId=int(inv[v]);witness.append({"exportVertex":int(v),"physicalVertex":uId,"sourcePosition":rest[v].tolist(),"eligible":bool(allEligible[uId]),"pinnedBoundary":bool(boundaries[uId]),"sharedProtected":bool(shared[uId]),"sourceWeights":{name:float(w) for name,w in zip(bones,W[v]) if w>0},"candidatePreFloat32Weights":{name:float(w) for name,w in zip(bones,candidate[v]) if w>0}})
(OUT/"inner-elbow-witness.json").write_text(json.dumps({"triangle":3789,"rows":witness,"limits":"Source-space weights and mask membership only; no rendered quality claim."},indent=2)+"\n")
