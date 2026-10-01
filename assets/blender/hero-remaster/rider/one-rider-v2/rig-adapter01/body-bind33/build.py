"""One constrained harmonic garment field. No Euclidean sleeve selection or morph."""
import json
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import connected_components
from common import SOURCE,RUN,OUT,load,accessor,sha
raw,j,b,p,start=load();RUN.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
branch=RUN.parent/'body-bind32/branch-fields.npz';f=np.load(branch)
rest,_,_=accessor(j,b,p['attributes']['POSITION']);tri=accessor(j,b,p['indices'])[0].reshape(-1,3)
si,siat,sistride=accessor(j,b,p['attributes']['JOINTS_0']);sw,swat,swstride=accessor(j,b,p['attributes']['WEIGHTS_0'])
assert j['accessors'][p['attributes']['JOINTS_0']]['componentType']==5121
u,first,inv=np.unique(rest,axis=0,return_index=True,return_inverse=True);assert np.array_equal(u,f['source']) and np.array_equal(inv,f['inverse'])
W=np.zeros((len(rest),19))
for lane in range(4):np.add.at(W,(np.arange(len(rest)),si[:,lane]),sw[:,lane])
UW=W[first];assert np.max(abs(W-UW[inv]))<1e-7
ut=inv[tri];edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]]
length=np.linalg.norm(u[edges[:,0]]-u[edges[:,1]],axis=1);conductance=1/length
adj=coo_matrix((np.r_[conductance,conductance],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(u),len(u))).tocsr()
L=diags(np.asarray(adj.sum(1)).ravel())-adj
prior=np.load(RUN.parent/'body-bind26/weight-field.npz');assert np.array_equal(prior['unique'],u);shared=prior['shared']
names=[j['nodes'][i]['name'] for i in j['skins'][0]['joints']];ix={n:i for i,n in enumerate(names)}
C=UW.copy();selectedAll=np.zeros(len(u),bool);boundaryAll=np.zeros(len(u),bool);rows=[];maxPruned=0;residuals=[]
for side,sign in [('L',1),('R',-1)]:
 selected=f[side+'_region']&~shared&(np.abs(u[:,2])>.18)
 ids=np.flatnonzero(selected);components,_=connected_components(adj[ids][:,ids]);assert components==1
 boundary=selected&((adj@(~selected).astype(float))>0)
 # Explicit geometry landmarks within the surface-classified branch; no old-weight filter.
 upper=selected&~boundary&(u[:,1]>1.29)&(u[:,1]<1.37)&(sign*u[:,2]>.29)
 elbow=selected&~boundary&(u[:,1]>1.12)&(u[:,1]<1.17)&(sign*u[:,2]>.29)
 fore=selected&~boundary&(u[:,1]>1.00)&(u[:,1]<1.06)&(sign*u[:,2]>.315)
 assert upper.any() and elbow.any() and fore.any()
 fixed=boundary|upper|elbow|fore;free=selected&~fixed
 targets=UW.copy()/UW.sum(1,keepdims=True)
 targets[upper|elbow|fore]=0
 targets[upper,ix['upperArm.'+side]]=1
 targets[elbow,ix['upperArm.'+side]]=.5;targets[elbow,ix['forearm.'+side]]=.5
 targets[fore,ix['forearm.'+side]]=1
 freeIds=np.flatnonzero(free);fixedIds=np.flatnonzero(fixed)
 rhs=-(L[freeIds][:,fixedIds]@targets[fixedIds])
 solution=spsolve(L[freeIds][:,freeIds].tocsc(),rhs)
 assert np.min(solution)>-1e-9 and np.max(solution)<1+1e-9
 residuals.append(float(np.max(abs(L[freeIds][:,freeIds]@solution-rhs))))
 proposed=targets.copy();proposed[freeIds]=np.clip(solution,0,1)
 changedRegion=selected&~boundary
 for v in np.flatnonzero(changedRegion):
  value=proposed[v];top=np.argsort(-value,kind='stable')[:4];pruned=value.sum()-value[top].sum();maxPruned=max(maxPruned,float(pruned))
  keep=np.zeros(19);keep[top]=value[top];keep*=UW[v].sum()/keep.sum();C[v]=keep
 selectedAll|=selected;boundaryAll|=boundary
 rows.append({'side':side,'selectedPhysicalVertices':len(ids),'components':components,'boundaryPinned':int(boundary.sum()),'anchors':{'upperArm':int(upper.sum()),'elbow':int(elbow.sum()),'forearm':int(fore.sum())},'freeSolved':len(freeIds)})
landmarks=np.unique(ut[[6340,6403,27413,27805]]);assert np.array_equal(C[landmarks],UW[landmarks])
assert np.array_equal(C[shared|boundaryAll|~selectedAll],UW[shared|boundaryAll|~selectedAll]);assert np.max(abs(C.sum(1)-UW.sum(1)))<1e-12
candidate=C[inv];changed=np.flatnonzero(np.max(abs(candidate-W),axis=1)>1e-7);assert len(changed)>0
patched=bytearray(raw);allowed=set()
for v in changed:
 entries=sorted([(int(i),float(w)) for i,w in enumerate(candidate[v]) if w>0],key=lambda pair:(-pair[1],pair[0]));assert len(entries)<=4;entries += [(0,0)]*(4-len(entries))
 for lane,(bone,weight) in enumerate(entries):
  at=start+siat+v*sistride+lane;patched[at]=bone;allowed.add(at)
  at=start+swat+v*swstride+lane*4;patched[at:at+4]=np.float32(weight).tobytes();allowed.update(range(at,at+4))
result=bytes(patched);actual=[i for i,(a,c) in enumerate(zip(raw,result)) if a!=c];assert result[:start]==raw[:start] and len(result)==len(raw) and all(i in allowed for i in actual)
path=RUN/'rider.glb'
if path.exists():assert path.read_bytes()==result,'Frozen harmonic candidate cannot be overwritten'
else:path.write_bytes(result)
np.savez_compressed(RUN/'weight-field.npz',rest=rest,triangles=tri,original=W,candidate=candidate,unique=u,inverse=inv,selected=selectedAll,boundary=boundaryAll,shared=shared,changed=changed)
report={'source':str(SOURCE),'sourceSHA256':sha(raw),'candidate':str(path),'candidateSHA256':sha(result),'candidateBytes':len(result),'allNonSkinBytesExact':True,'originalJSONNodesBonesBindsTexturesMaterialsTopologyUVNormalsMorphsExact':True,'protectedSharedAliasesExact':True,'sourceUnchanged':True,'changedExportVertices':len(changed),'changedPhysicalVertices':int(np.count_nonzero(np.max(abs(C-UW),axis=1)>1e-7)),'changedBytes':len(actual),'weightFieldSHA256':sha((RUN/'weight-field.npz').read_bytes()),'branchFieldSHA256':sha(branch.read_bytes()),'settings':{'method':'Inverse source-edge-length harmonic Dirichlet skin field over explicit source-surface branch32; no direct shaft/lateral field or sparse corrective driver','coreProtection':'absZ<=.18 and outside selected sourcebranch byte exact','hoodProtection':'All exact shared primitive aliases and one graphboundary ring exact; all hood/head/glove non-skin bytes exact','anchors':'upper Y(1.29,1.37)/signedZ>.29,elbow Y(1.12,1.17)/signedZ>.29,fore Y(1.00,1.06)/signedZ>.315 inside branch; upper1,elbow upper.5 fore.5,fore1','pruning':'Stable largest4 influence selection per solved vertex, renormalized to original source weight mass; no pruning on pinned boundary/outside','maximumDiscardedProbability':maxPruned,'maximumLinearSolveResidual':max(residuals),'sides':rows,'oneConstructionNoSweep':True},'limits':['CPU construction only, no actual-pose or visual quality yet.','Top4 projection may introduce small influence discontinuities, requiring measured normals/stretch/contacts.','Fixed boundary protects original join but some historical shoulder defects remain.','No new joint positions, physics, geometry, atlas, optimized LOD or player asset promotion.']}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');assert SOURCE.read_bytes()==raw
print(json.dumps(report,indent=2))
