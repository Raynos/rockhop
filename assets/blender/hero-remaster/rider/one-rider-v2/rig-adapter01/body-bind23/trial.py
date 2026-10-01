"""One source-connected local elbow ARAP construction; CPU only, no asset export."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import splu
from scipy.sparse.csgraph import connected_components
sys.path.insert(0,str(Path(__file__).parent.parent/'body-bind21'))
from common import SOURCE,load,accessor
np.seterr(all='raise')
OUT=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind23')
RUN=SOURCE.parent.parent.parent/'body-bind23'
BASE=OUT.parent/'body-bind21/baseline-cpu'
PRIVATE=RUN.parent/'body-bind21/baseline-cpu'
OUT.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True)
m=json.loads((BASE/'pose-manifest.json').read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(rec,n):
 p=BASE/rec['file'];p=p if p.exists() else PRIVATE/rec['file'];raw=p.read_bytes();assert sha(raw)==rec['sha256'];return np.frombuffer(raw,dtype='<f8').reshape(-1,n).copy()
def save(name,a):
 raw=np.asarray(a,dtype='<f8').tobytes();p=RUN/(name+'.f64')
 if p.exists():assert p.read_bytes()==raw,'Frozen construction cannot be overwritten'
 else:p.write_bytes(raw)
 return {'file':p.name,'values':len(raw)//8,'bytes':len(raw),'sha256':sha(raw),'privatePath':str(p)}
def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-30)
raw,j,b,primitive,start=load();assert m['sourceSHA256']==sha(raw)
a=m['primitives'][0]['attributes'];rest=read(a['position'],3);normal=read(a['normal'],3);tri=read(m['primitives'][0]['index'],3).astype(int)
assert np.array_equal(rest,accessor(j,b,primitive['attributes']['POSITION'])[0]);assert np.array_equal(tri,accessor(j,b,primitive['indices'])[0].reshape(-1,3))
u,first,inv=np.unique(rest,axis=0,return_index=True,return_inverse=True);ut=inv[tri]
edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),1),axis=0);edges=edges[edges[:,0]!=edges[:,1]]
length=np.linalg.norm(u[edges[:,0]]-u[edges[:,1]],axis=1);ew=1/np.maximum(length,1e-6)
adj=coo_matrix((np.r_[ew,ew],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(u),len(u))).tocsr();degree=np.asarray(adj.sum(1)).ravel();L=diags(degree)-adj
shared=np.zeros(len(u),bool);lookup={tuple(v):i for i,v in enumerate(u)}
# All coincident other-material surfaces remain pinned, including donor hood.
for mesh in j['meshes']:
 for p in mesh['primitives']:
  if p is primitive:continue
  for v in accessor(j,b,p['attributes']['POSITION'])[0]:
   if tuple(v) in lookup:shared[lookup[tuple(v)]]=True
names=[j['nodes'][n]['name'] for n in j['skins'][0]['joints']];ib=accessor(j,b,j['skins'][0]['inverseBindMatrices'])[0].astype(float);origins=np.linalg.inv(ib.reshape(-1,4,4).transpose(0,2,1))[:,:3,3]
active=np.zeros(len(u),bool);regions=[]
for side,sign in [('L',1),('R',-1)]:
 sh,el,wr=[origins[names.index(n+'.'+side)] for n in ['upperArm','forearm','hand']]
 def distance(a,b):
  d=b-a;t=np.clip(np.einsum('vi,i->v',u-a,d)/np.dot(d,d),0,1);return np.linalg.norm(u-(a+t[:,None]*d),axis=1)
 shaft=np.minimum(distance(sh,el),distance(el,wr))
 selected=(u[:,1]>.95)&(u[:,1]<1.38)&(sign*u[:,2]>.18)&(shaft<.14)&(~shared)
 ids=np.flatnonzero(selected);components,labels=connected_components(adj[ids][:,ids]);assert components==1,'Geometry ROI is not one connected sleeve'
 regions.append({'side':side,'selectedPhysicalVertices':len(ids),'connectedComponents':components,'sourceBoundsM':[u[ids].min(0).tolist(),u[ids].max(0).tolist()],'sourceShoulder':sh.tolist(),'sourceElbow':el.tolist(),'sourceWrist':wr.tolist(),'sharedProtectedInsideGeometricMask':int(((u[:,1]>.95)&(u[:,1]<1.38)&(sign*u[:,2]>.18)&(shaft<.14)&shared).sum())})
 active|=selected
boundary=active&((adj@(~active).astype(float))>0);free=active&~boundary;f=np.flatnonzero(free);k=np.flatnonzero(~free)
assert np.all(free[inv[tri[3789]]]),'All original witness vertices must be free'
assert not np.any(free&shared)
# Selection and boundaries have no weight eligibility, contamination or arm-weight threshold.
maskReport={'weightIndependentSelection':True,'geometricSelection':{'sourceYOpen':[.95,1.38],'lateralSignedZAbove':.18,'distanceToSourceShoulderElbowWristSegmentsBelowM':.14},'sides':regions,'freePhysicalVertices':len(f),'pinnedBoundaryPhysicalVertices':int(boundary.sum()),'sharedProtectedPhysicalVertices':int(shared.sum()),'witness3789':[{'exportVertex':int(v),'physicalVertex':int(inv[v]),'free':bool(free[inv[v]]),'sourcePosition':rest[v].tolist()} for v in tri[3789]],'outsideROINeverChanged':True,'shoulderCuffPinnedBySourceGraphBoundary':True}
(OUT/'roi-proof.json').write_text(json.dumps(maskReport,indent=2)+'\n')
# Single fixed geometry construction, no source-weight threshold or parameter sweep.
t=np.clip((u[:,1]-.95)/.43,0,1);blend=np.sin(np.pi*t)**2;penalty=degree*(.005+.08*(1-blend)**2)
solve=splu((L[f][:,f]+diags(penalty[f])).tocsc()).solve
local=np.any(free[edges],axis=1);ei,ej=edges[local].T;weights=ew[local];re=u[ei]-u[ej]
sourceQ=rest[tri];sourceCross=np.cross(sourceQ[:,1]-sourceQ[:,0],sourceQ[:,2]-sourceQ[:,0]);sourceArea=np.linalg.norm(sourceCross,axis=1)/2;sourceDot=np.einsum('ti,ti->t',unit(sourceCross),unit(normal[tri].mean(1)));sourceEdge=np.linalg.norm(sourceQ-np.roll(sourceQ,-1,axis=1),axis=2)
# Geometric audit includes every triangle touching selected sleeves and the original
# historical audit mask, rather than redefining success from modified normals alone.
geometryTriangles=np.any(active[ut],axis=1)
si=read(a['skinIndex'],4).astype(int);sw=read(a['skinWeight'],4);bones=m['primitives'][0]['bones'];armIds=[i for i,n in enumerate(bones) if n.startswith(('upperArm','forearm'))];arm=np.where(np.isin(si,armIds),sw,0).sum(1);historicalTriangles=(arm[tri].mean(1)>.3)&(rest[tri,1].mean(1)>.9)&(np.abs(rest[tri,2]).mean(1)>.13)
def metrics(pos,norm,roi):
 Q=pos[tri];cross=np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]);dot=np.einsum('ti,ti->t',unit(cross),unit(norm[tri].mean(1)));ratio=np.linalg.norm(cross,axis=1)/np.maximum(2*sourceArea,1e-30);stretch=(np.linalg.norm(Q-np.roll(Q,-1,axis=1),axis=2)/np.maximum(sourceEdge,1e-30)).max(1);fold=roi&(sourceDot>.2)&(dot<-.2)
 return {'triangles':int(roi.sum()),'folds':int(fold.sum()),'areaBelowQuarter':int((roi&(ratio<.25)).sum()),'maximumEdgeStretch':float(stretch[roi].max()),'minimumNormalDot':float(dot[roi].min()),'triangle3789':{'normalDot':float(dot[3789]),'areaRatio':float(ratio[3789]),'maximumEdgeStretch':float(stretch[3789])}},fold
rows=[];manifestRows=[];archive=[]
for row in m['rows']:
 d=row['dump'][0];lbs=read(d['positions'],3);nLBS=read(d['gpuRuleSkinnedNormals'],3);P=lbs[first].copy();assert np.max(np.linalg.norm(lbs-P[inv],axis=1))<1e-7;target=P.copy();changes=[]
 for iteration in range(15):
  pe=P[ei]-P[ej];cov=np.zeros((len(u),3,3));outer=weights[:,None,None]*pe[:,:,None]*re[:,None,:];np.add.at(cov,ei,outer);np.add.at(cov,ej,outer)
  U,_,Vh=np.linalg.svd(cov);sign=np.linalg.det(U@Vh);U[:,:,2]*=np.where(sign<0,-1.,1.)[:,None];R=U@Vh
  rhsAll=np.zeros_like(P);term=.5*weights[:,None]*np.einsum('ekl,el->ek',R[ei]+R[ej],re);np.add.at(rhsAll,ei,term);np.add.at(rhsAll,ej,-term)
  rhs=rhsAll[f]-L[f][:,k]@target[k]+penalty[f,None]*target[f]
  q=P.copy();q[f]=solve(rhs);changes.append(float(np.linalg.norm(q-P,axis=1).max()));P=q
 assert np.array_equal(P[k],target[k]);candidate=lbs.copy();candidate[free[inv]]=P[inv[free[inv]]]
 # Normal frame transport is explicit; it is not itself a visual quality verdict.
 normals=nLBS.copy();selectedExports=free[inv];normals[selectedExports]=unit(np.einsum('vkl,vl->vk',R[inv[selectedExports]],normal[selectedExports]))
 F=read(d['skinMatrices'],16).reshape(-1,4,4).transpose(0,2,1);smallest=np.linalg.svd(F[selectedExports,:3,:3],compute_uv=False)[:,-1];assert smallest.min()>.1
 # Verify the retained actual Three.js Cartesian skinning map before inversion.
 predicted=np.einsum('vkl,vl->vk',F[:,:3,:3],rest)+F[:,:3,3];baselineError=float(np.linalg.norm(predicted-lbs,axis=1).max());assert baselineError<1e-10
 delta=np.zeros_like(rest);delta[selectedExports]=np.linalg.solve(F[selectedExports,:3,:3],(candidate[selectedExports]-lbs[selectedExports])[:,:,None])[:,:,0];roundtrip=lbs+np.einsum('vkl,vl->vk',F[:,:3,:3],delta);error=float(np.linalg.norm(roundtrip-candidate,axis=1).max());assert error<1e-12
 sourceNormals=normal.copy();sourceNormals[selectedExports]=unit(np.linalg.solve(F[selectedExports,:3,:3],normals[selectedExports,:,None])[:,:,0]);normalDelta=np.zeros_like(normal);normalDelta[selectedExports]=sourceNormals[selectedExports]-normal[selectedExports];reconstructed=unit(np.einsum('vkl,vl->vk',F[selectedExports,:3,:3],sourceNormals[selectedExports]));normalError=float(np.linalg.norm(reconstructed-normals[selectedExports],axis=1).max());assert normalError<1e-12
 assert np.array_equal(candidate[~selectedExports],lbs[~selectedExports]);assert np.array_equal(normals[~selectedExports],nLBS[~selectedExports]);assert np.array_equal(delta[~selectedExports],np.zeros_like(delta[~selectedExports]));assert np.max(np.abs(delta-delta[first][inv]))<1e-7
 r={'sample':row['i'],'iterations':15,'iterationMaximumDisplacementM':changes,'maximumPosedDisplacementM':float(np.linalg.norm(candidate-lbs,axis=1).max()),'maximumSourceCorrectiveDisplacementM':float(np.linalg.norm(delta,axis=1).max()),'minimumInverseSkinSingularValue':float(smallest.min()),'baselineActualCartesianSkinReproductionErrorM':baselineError,'sourceRoundtripErrorM':error,'sourceNormalRoundtripError':normalError,'outsideRegionPositionsNormalsExact':True,'aliasesSamePositionCorrective':True,'skinMatricesWeightsBonesBindPhysicsContactsUnchanged':True,'scopeMetrics':{}}
 for name,mask in [('geometricSleeves',geometryTriangles),('historicalAudit',historicalTriangles)]:
  bm,bf=metrics(lbs,nLBS,mask);cm,cf=metrics(candidate,normals,mask);r['scopeMetrics'][name]={'baseline':bm,'candidate':cm,'newFoldsNotPresentAtBaseline':int((cf&~bf).sum())}
 dump=dict(d)
 for key,name,array in [('positions','positions',candidate),('gpuRuleSkinnedNormals','normals',normals),('correctiveDelta','source-delta',delta),('normalCorrectiveDelta','source-normal-delta',normalDelta)]:
  rec=save(f"sample{row['i']}-mesh0-{name}",array);dump[key]=rec;archive.append(rec)
 nextRow=dict(row);nextRow['dump']=[dump,*row['dump'][1:]];manifestRows.append(nextRow);rows.append(r)
 assert sha(SOURCE.read_bytes())==m['sourceSHA256']
 for mi in range(1,len(row['dump'])):
  assert nextRow['dump'][mi]==row['dump'][mi]
settings={'singleFrozenConstruction':True,'noParameterSweep':True,'method':'Local/global ARAP on source triangle graph with exact-position physical aliases','iterations':15,'boundary':'Source-connected geometry ROI; first ring hard pinned; all other-material aliases pinned','softProximity':'.005+.08*(1-sin(pi*t)^2)^2 times graph degree, source t=(Y-.95)/.43','weightsUsedForSelection':False,'weightsUsedForHistoricalReportOnly':True,'originalGeometryWeightsBindsBonesPhysicsTexturesUntouched':True,'exportedGLB':False}
(OUT/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
report={'source':str(SOURCE),'sourceSHA256':m['sourceSHA256'],'sourceUnchanged':True,'rows':rows,'maximumCPUvsActualPlayedContactErrorM':max(c['maximumCPUvsActualPlayedSurfaceM'] for row in m['rows'] for c in row['contacts']),'protectedSourceScope':'All positions and normals outside the free physical sleeve region; other primitive buffers remain source-manifest references','limits':['Four actual recorded-state CPU targets only, no motion interpolation, rendering, visual score, collision proof or asset promotion.','Face-versus-normal fold counts depend on authored transported normals; independently measured area and stretch do not establish good clothing shape.','Finite 15-iteration residual recorded; no convergence claim.','Source-space inverse deltas are morph-ready numeric payloads only, no GLB or engine driver.']}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');nm=dict(m);nm['rows']=manifestRows;nm['settings']=settings;nm['limits']=report['limits'];(OUT/'pose-manifest.json').write_text(json.dumps(nm,indent=2)+'\n');(OUT/'buffer-archive.json').write_text(json.dumps({'count':len(archive),'buffers':archive},indent=2)+'\n')
print(json.dumps({'freePhysicalVertices':len(f),'samples':len(rows),'rows':[{'sample':r['sample'],'posedMax':r['maximumPosedDisplacementM'],'sourceMax':r['maximumSourceCorrectiveDisplacementM'],'metrics':r['scopeMetrics']} for r in rows]},indent=2))
