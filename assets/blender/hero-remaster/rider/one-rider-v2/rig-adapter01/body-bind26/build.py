"""One geometry-selected anatomical arm weight field, preserving source surfaces."""
import json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from common import SOURCE,RUN,OUT,load,accessor,sha
np.seterr(all='raise');raw,j,b,p,start=load();RUN.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
rest,_,_=accessor(j,b,p['attributes']['POSITION']);tri=accessor(j,b,p['indices'])[0].reshape(-1,3);si,siat,sistride=accessor(j,b,p['attributes']['JOINTS_0']);sw,swat,swstride=accessor(j,b,p['attributes']['WEIGHTS_0']);assert j['accessors'][p['attributes']['JOINTS_0']]['componentType']==5121;assert j['accessors'][p['attributes']['WEIGHTS_0']]['componentType']==5126
names=[j['nodes'][i]['name'] for i in j['skins'][0]['joints']];idx={n:i for i,n in enumerate(names)};ib=accessor(j,b,j['skins'][0]['inverseBindMatrices'])[0].astype(float);origins=np.linalg.inv(ib.reshape(-1,4,4).transpose(0,2,1))[:,:3,3]
W=np.zeros((len(rest),19))
for lane in range(4):np.add.at(W,(np.arange(len(rest)),si[:,lane]),sw[:,lane])
u,first,inv=np.unique(rest.astype(float),axis=0,return_index=True,return_inverse=True);UW=W[first];assert np.max(abs(W-UW[inv]))<1e-7;ut=inv[tri];edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),1),axis=0);edges=edges[edges[:,0]!=edges[:,1]];adj=coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(u),len(u))).tocsr()
shared=np.zeros(len(u),bool);lookup={tuple(q):i for i,q in enumerate(u)};provenance=[]
for mi,mesh in enumerate(j['meshes']):
 for pi,other in enumerate(mesh['primitives']):
  if other is p:continue
  positions=accessor(j,b,other['attributes']['POSITION'])[0];matches=[]
  for q in positions:
   if tuple(q) in lookup:shared[lookup[tuple(q)]]=True;matches.append(lookup[tuple(q)])
  provenance.append({'mesh':mi,'primitive':pi,'material':other['material'],'materialName':j['materials'][other['material']].get('name'),'sourcePositionCount':len(positions),'sourceBoundsM':[positions.min(0).tolist(),positions.max(0).tolist()],'bodyPhysicalAliases':len(set(matches)),'allSourceAccessorBytesRemainExact':True})
assert j['meshes'][0]['primitives'][2]['material']==2
C=UW.copy();selectedAll=np.zeros(len(u),bool);boundaryAll=np.zeros(len(u),bool);alphaAll=np.zeros(len(u));targets=np.zeros_like(C);regions=[]
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
for side,sign in [('L',1),('R',-1)]:
 upper,fore,chest=idx['upperArm.'+side],idx['forearm.'+side],idx['chest'];shoulder,elbow,wrist=[origins[idx[n+'.'+side]] for n in ['upperArm','forearm','hand']]
 def distance(a,b):
  d=b-a;t=np.clip(np.einsum('vi,i->v',u-a,d)/np.dot(d,d),0,1);return np.linalg.norm(u-a-t[:,None]*d,axis=1)
 shaft=np.minimum(distance(shoulder,elbow),distance(elbow,wrist));geometric=(u[:,1]>.95)&(u[:,1]<1.51)&(sign*u[:,2]>.18)&(shaft<.14);selected=geometric&~shared;ids=np.flatnonzero(selected);components,labels=connected_components(adj[ids][:,ids]);assert components==1,'Disconnected source sleeve selection'
 boundary=selected&((adj@(~selected).astype(float))>0);distanceRing=np.full(len(u),-1,int);distanceRing[boundary]=0;front=boundary.copy()
 for level in range(1,5):
  front=selected&(distanceRing<0)&((adj@front.astype(float))>0);distanceRing[front]=level
 depth=np.where(distanceRing<0,5,distanceRing);alpha=smooth(depth/4)*smooth((u[:,1]-.95)/.06)*smooth((sign*u[:,2]-.18)/.04);alpha[~selected]=0
 # Distal shoulder axis progress governs deliberate proximal chest blend.
 a=elbow-shoulder;progress=np.einsum('vi,i->v',u-shoulder,a)/np.dot(a,a);chestFraction=1-smooth(progress/.4)
 direction=(a/np.linalg.norm(a)+(wrist-elbow)/np.linalg.norm(wrist-elbow));direction/=np.linalg.norm(direction);long=np.einsum('vi,i->v',u-elbow,direction);foreFraction=smooth((long+.065)/.13)
 target=np.zeros_like(UW);total=UW.sum(1);target[:,chest]=chestFraction*total;target[:,upper]=(1-chestFraction)*(1-foreFraction)*total;target[:,fore]=(1-chestFraction)*foreFraction*total
 targets[selected]=target[selected];C[selected]=UW[selected]+alpha[selected,None]*(target[selected]-UW[selected]);selectedAll|=selected;boundaryAll|=boundary;alphaAll+=alpha
 regions.append({'side':side,'connectedComponents':components,'selectedPhysicalVertices':len(ids),'sharedProtectedWithinGeometricSelection':int((shared&geometric).sum()),'pinnedBoundaryPhysicalVertices':int(boundary.sum()),'bindShoulder':shoulder.tolist(),'bindElbow':elbow.tolist(),'bindWrist':wrist.tolist(),'longitudinalBlendDirection':direction.tolist(),'sourceBoundsM':[u[ids].min(0).tolist(),u[ids].max(0).tolist()]})
assert np.max(abs(C.sum(1)-UW.sum(1)))<1e-12;assert np.all(C>=0);assert np.array_equal(C[shared|boundaryAll|~selectedAll],UW[shared|boundaryAll|~selectedAll]);assert not np.any(alphaAll[np.abs(u[:,2])<=.18]);assert max(np.count_nonzero(row>0) for row in C)<=4,'Source/target union exceeds four influences; no automatic pruning permitted'
changedPhysical=np.flatnonzero(np.max(abs(C-UW),axis=1)>1e-7);candidate=C[inv];changed=np.flatnonzero(np.max(abs(candidate-W),axis=1)>1e-7);assert len(changed)>0;assert all(alphaAll[inv[v]]>0 for v in tri[3789]);patched=bytearray(raw);allowed=set()
for v in changed:
 entries=sorted([(int(i),float(w)) for i,w in enumerate(candidate[v]) if w>0],key=lambda pair:-pair[1]);assert len(entries)<=4;entries += [(0,0)]*(4-len(entries))
 for lane,(bone,weight) in enumerate(entries):
  at=start+siat+v*sistride+lane;patched[at]=bone;allowed.add(at);at=start+swat+v*swstride+lane*4;patched[at:at+4]=np.float32(weight).tobytes();allowed.update(range(at,at+4))
result=bytes(patched);actual=[i for i,(a,c) in enumerate(zip(raw,result)) if a!=c];assert len(result)==len(raw);assert result[:start]==raw[:start];assert all(i in allowed for i in actual);assert SOURCE.read_bytes()==raw
path=RUN/'rider.glb'
if path.exists():assert path.read_bytes()==result,'Frozen candidate cannot be overwritten'
else:path.write_bytes(result)
np.savez_compressed(RUN/'weight-field.npz',rest=rest,triangles=tri,original=W,candidate=candidate,unique=u,inverse=inv,selected=selectedAll,boundary=boundaryAll,shared=shared,alpha=alphaAll,target=targets,changed=changed)
witnesses=[]
for t in [3789,26534,26090]:
 witnesses.append({'triangle':t,'vertices':[{'exportVertex':int(v),'physicalVertex':int(inv[v]),'sourcePosition':rest[v].tolist(),'sharedProtected':bool(shared[inv[v]]),'graphBoundaryProtected':bool(boundaryAll[inv[v]]),'alpha':float(alphaAll[inv[v]]),'sourceWeights':{n:float(w) for n,w in zip(names,W[v]) if w>0},'candidatePreFloat32Weights':{n:float(w) for n,w in zip(names,candidate[v]) if w>0}} for v in tri[t]]})
settings={'singleConstruction':True,'noParameterSweep':True,'selectionUsesOriginalWeights':False,'geometrySourceM':{'yOpen':[.95,1.51],'signedLateralZAbove':.18,'shaftDistanceBelow':.14},'coreProtected':'Every physical vertex with absZ<=.18 m; all outside geometry selection exact','hoodProtection':'Entire donor hood/glove/head primitives byte-exact; every exact shared body position and first source graph boundary ring pinned','blend':'four graph rings smoothstep,60mm cuff taper,40mm lateral taper','anatomicalTarget':'chestFraction=1-smoothstep(shoulder-to-elbow projection/0.4); distal mass split upperArm/forearm using averaged shaft direction and +/-65mm elbow smoothstep; preserve each source weight sum','unionInfluencesAtMost':4,'noPruning':True,'provenance':provenance,'sides':regions}
report={'source':str(SOURCE),'sourceSHA256':sha(raw),'candidate':str(path),'candidateSHA256':sha(result),'candidateBytes':len(result),'allNonSkinBytesExact':True,'originalJSONNodesBonesBindsTexturesMaterialsTopologyUVNormalsMorphsExact':True,'protectedSharedAliasesExact':True,'sourceUnchanged':True,'changedExportVertices':len(changed),'changedPhysicalVertices':len(changedPhysical),'changedBytes':len(actual),'weightFieldSHA256':sha((RUN/'weight-field.npz').read_bytes()),'settings':settings,'limits':['CPU-only unaccepted anatomical skin experiment; no appearance, motion or collision verdict.','Some extreme shoulder triangles touch hood-join aliases. Their pinned neighborhood intentionally remains unchanged, so this experiment does not solve all shoulder defects.','Full geometric sleeve selection is not a semantic body segmentation certificate; explicit core/hood/cuff protections define the permitted region.']}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'settings.json').write_text(json.dumps(settings,indent=2)+'\n');(OUT/'source-witnesses.json').write_text(json.dumps(witnesses,indent=2)+'\n');print(json.dumps({'candidateSHA256':sha(result),'changedExportVertices':len(changed),'changedPhysicalVertices':len(changedPhysical),'changedBytes':len(actual)}))
