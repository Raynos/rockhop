"""CPU-only hip/upper-leg geometry audit; no renderer, Blender or candidate edit."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
np.seterr(all='raise')
repo=Path('/Users/raynos/projects/games/rockhop');out=Path(sys.argv[1]) if len(sys.argv)>1 else repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind15/candidate-cpu';m=json.loads((out/'pose-manifest.json').read_text());archive=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind15')/out.name
def read(rec,n):
 p=out/rec['file'];p=p if p.exists() else archive/rec['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256'];return np.fromfile(p,dtype='<f8').reshape(-1,n)
def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-30)
def weights(p):
 a=p['attributes'];si=read(a['skinIndex'],4).astype(int);sw=read(a['skinWeight'],4);W=np.zeros((len(si),19))
 for lane in range(4):np.add.at(W,(np.arange(len(si)),si[:,lane]),sw[:,lane])
 return W,si,sw
p=m['primitives'][0];a=p['attributes'];rest=read(a['position'],3);normal=read(a['normal'],3);tri=read(p['index'],3).astype(int);W,si,sw=weights(p);bones=p['bones'];idx={b:i for i,b in enumerate(bones)};nativeZ=rest[:,1]/1.015;leg=W[:,[idx[b] for b in ['pelvis','thighL','thighR']]].sum(1)
# Native source height separates jeans/seat from hoodie sleeves. Each triangle
# requires ALL vertices inside the height band and mean pelvis/thigh support >.5.
vmasks={'upper-leg':(nativeZ>=.55)&(nativeZ<.80)&(leg>.5),'waist-repair-band':(nativeZ>=.78)&(nativeZ<.85)&(leg>.5),'hip-seat':(nativeZ>=.78)&(nativeZ<=1.00)&(leg>.5)}
vmasks['posterior-hip-seat']=vmasks['hip-seat']&(rest[:,0]<.634775)
rois={name:np.all(mask[tri],axis=1) for name,mask in vmasks.items()};r=rest[tri];rc=np.cross(r[:,1]-r[:,0],r[:,2]-r[:,0]);area=np.linalg.norm(rc,axis=1)/2;sourceDots=np.einsum('ti,ti->t',unit(rc),unit(normal[tri].mean(1)));edgesR=np.linalg.norm(r-np.roll(r,-1,axis=1),axis=2)
source=[];history=[]
for name,mask in vmasks.items():
 ids=np.flatnonzero(mask);ts=np.flatnonzero(rois[name]);source.append({'region':name,'vertices':len(ids),'triangles':len(ts),'restAgainstNormalTriangles':int((rois[name]&(sourceDots<-.2)).sum()),'restDegenerateTriangles':int((rois[name]&(area<1e-10)).sum()),'bounds':{'min':rest[ids].min(0).tolist(),'max':rest[ids].max(0).tolist()},'meanBoneWeights':{b:float(W[ids,idx[b]].mean()) for b in bones if W[ids,idx[b]].max()>1e-5},'maximumSpineWeight':float(W[ids,idx['spine']].max()),'oppositeSideThighVerticesOver1Percent':int(((rest[ids,2]>.02)&(W[ids,idx['thighR']]>.01)|((rest[ids,2]<-.02)&(W[ids,idx['thighL']]>.01))).sum())})
for h in m['history']:
 hr=read(h['attributes']['position'],3);HW,_,_=weights(h);assert hr.shape==rest.shape;assert h['bones']==bones;assert np.array_equal(hr,rest)
 history.append({'version':h['version'],'sourceSHA256':h['sha256'],'restPositionsExact':True,'rawSourceWeightsVsCurrent':[{'region':name,'changedVerticesOver1eMinus6':int((np.abs(HW[mask]-W[mask]).max(1)>1e-6).sum()),'maximumAbsoluteBoneWeightDifference':float(np.abs(HW[mask]-W[mask]).max())} for name,mask in vmasks.items()]})
# Exact exporter aliases, never normal/UV index duplicates mistaken for holes.
keys={}
for i,v in enumerate(rest):keys.setdefault(tuple(v),[]).append(i)
aliasGroups={name:[ids for ids in keys.values() if len(ids)>1 and mask[ids[0]]] for name,mask in vmasks.items()}
# Actual authored seat cover dimensions, from author_bike_hero.py, distinguish
# its top triangles from tail/tank: superellipse top .548..630, x .11..60.
bp=read(m['bodyworkSource']['positions'],3);bt=read(m['bodyworkSource']['triangles'],3).astype(int);bq=bp[bt];bc=bq.mean(1);bn=unit(np.cross(bq[:,1]-bq[:,0],bq[:,2]-bq[:,0]));seat=np.all((bq[:,:,0]>=.1095)&(bq[:,:,0]<=.6005)&(bq[:,:,1]>=.5405)&(bq[:,:,1]<=.631)&(np.abs(bq[:,:,2])<=.069),axis=1)&(bn[:,1]>.3)
seatIds=np.flatnonzero(seat);assert len(seatIds)>0
poses=[];contours=[]
for row in m['rows']:
 posed=read(row['dump'][0]['positions'],3);normalP=read(row['dump'][0]['gpuRuleSkinnedNormals'],3);q=posed[tri];pc=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);pa=np.linalg.norm(pc,axis=1)/2;dots=np.einsum('ti,ti->t',unit(pc),unit(normalP[tri].mean(1)));ratio=pa/np.maximum(area,1e-30);edge=np.linalg.norm(q-np.roll(q,-1,axis=1),axis=2);stretch=(edge/np.maximum(edgesR,1e-30)).max(1)
 for name,mask in vmasks.items():
  roi=rois[name];ids=np.flatnonzero(roi);worst=sorted(ids,key=lambda i:dots[i])[:12];separations=[float(np.linalg.norm(posed[g,None,:]-posed[None,g,:],axis=2).max()) for g in aliasGroups[name]]
  poses.append({'sample':row['i'],'region':name,'triangles':len(ids),'newFaceAgainstSkinnedNormalTriangles':int((roi&(sourceDots>.2)&(dots<-.2)).sum()),'areaBelowQuarterTriangles':int((roi&(ratio<.25)).sum()),'areaRatioPercentiles':np.percentile(ratio[roi],[0,1,5,50,95,99,100]).tolist(),'maximumEdgeStretch':float(stretch[roi].max()),'maximumEdgeStretchWitness':{'triangle':int(ids[np.argmax(stretch[ids])]),'sourcePositions':rest[tri[ids[np.argmax(stretch[ids])]]].tolist(),'posedBikeFramePositions':posed[tri[ids[np.argmax(stretch[ids])]]].tolist()},'edgeStretchPercentiles':np.percentile(stretch[roi],[50,95,99,100]).tolist(),'maximumCoincidentSeparationM':max(separations,default=0),'worst':[{'triangle':int(t),'indices':tri[t].tolist(),'sourceNormalDot':float(sourceDots[t]),'posedNormalDot':float(dots[t]),'areaRatio':float(ratio[t]),'edgeStretch':float(stretch[t]),'sourcePositions':rest[tri[t]].tolist(),'posedBikeFramePositions':posed[tri[t]].tolist(),'weights':[[{'bone':bones[b],'weight':float(w)} for b,w in zip(si[v],sw[v]) if w>1e-5] for v in tri[t]]} for t in worst]})
 bodywork=read(row['bodyworkBikeFrame'],3);seatQ=bodywork[bt[seatIds]];hipIds=np.flatnonzero(vmasks['hip-seat']);rear=hipIds[rest[hipIds,0]<=np.quantile(rest[hipIds,0],.35)];pelvis=np.array(next(b['bikeFramePosition'] for b in row['bonePoints'] if b['name']=='pelvis'))
 # Longitudinal/vertical contour bands of source posterior samples, tracked
 # through actual skinning; no convex hull or posed aesthetic verdict.
 bands=[]
 for lo,hi in [(.78,.84),(.84,.90),(.90,.96),(.96,1.00)]:
  v=rear[(nativeZ[rear]>=lo)&(nativeZ[rear]<hi)];bands.append({'nativeSourceHeightBand':[lo,hi],'vertices':len(v),'boundsRelativePelvis':({'min':(posed[v]-pelvis).min(0).tolist(),'max':(posed[v]-pelvis).max(0).tolist()} if len(v) else None)})
 # Barycentric projected vertical clearance against actual top triangles.
 # This is a vertex-to-upward-surface sample, NOT whole body collision.
 checks=[]
 for v in hipIds:
  x,y,z=posed[v];best=None
  for t,st in zip(seatIds,seatQ):
   M=np.array([[st[1,0]-st[0,0],st[2,0]-st[0,0]],[st[1,2]-st[0,2],st[2,2]-st[0,2]]]);det=float(np.linalg.det(M))
   if abs(det)<1e-12:continue
   uv=np.linalg.solve(M,np.array([x-st[0,0],z-st[0,2]]))
   if uv.min()>=-1e-6 and uv.sum()<=1.000001:
    sy=float(st[0,1]+uv[0]*(st[1,1]-st[0,1])+uv[1]*(st[2,1]-st[0,1]));gap=float(y-sy)
    if best is None or gap<best['verticalGapM']:best={'vertex':int(v),'seatTriangle':int(t),'verticalGapM':gap,'bikeFramePosition':posed[v].tolist(),'seatProjectedY':sy}
  if best:checks.append(best)
 contours.append({'sample':row['i'],'pelvisBikeFrame':pelvis.tolist(),'hipBoundsBikeFrame':{'min':posed[hipIds].min(0).tolist(),'max':posed[hipIds].max(0).tolist()},'posteriorTrackedBands':bands,'seatTriangleIds':seatIds.tolist(),'seatTopBoundsBikeFrame':{'min':seatQ.reshape(-1,3).min(0).tolist(),'max':seatQ.reshape(-1,3).max(0).tolist()},'projectedHipVertices':len(checks),'negativeVerticalGapVertices':sum(c['verticalGapM']<0 for c in checks),'minimumProjectedVerticalGapM':min((c['verticalGapM'] for c in checks),default=None),'lowestProjectedSamples':sorted(checks,key=lambda c:c['verticalGapM'])[:10]})
report={'sourceSHA256':m['sourceSHA256'],'sourceUnchanged':hashlib.sha256(Path(m['source']).read_bytes()).hexdigest()==m['sourceSHA256'],'maximumCPUvsRetainedPlayedContactErrorM':max(c['maximumCPUvsActualPlayedSurfaceM'] for row in m['rows'] for c in row['contacts']),'source':source,'sourceBindOrigins':p['inverseBindOriginPositions'],'waistBlendSourceYBandM':[.78*1.015,.85*1.015],'history':history,'poses':poses,'contours':contours,'limits':['Six reconstructed immutable candidate or baseline recorded states, physical pose verified by retained actual palm/sole points; no renderer, asset repair or appearance score.','ROIs use exact native source-height ranges plus pelvis/thigh support; hoodie, NEW head/neck and glove surfaces excluded.','Against-skinned-normal means local fold/normal disagreement, not necessarily watertight inside-out volume or proven self-intersection.','Historical raw decoded weights, not old rendered pose, are compared to current conditioned weights; source positions and bone names verified exact.','Seat top subset comes from actual exported bodywork geometry and authored seat dimensions; projected vertex samples cannot certify whole-body collision.']};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'source':source,'sourceBindOrigins':p['inverseBindOriginPositions'],'waistBlendSourceYBandM':[.78*1.015,.85*1.015],'history':history,'poses':[{k:v for k,v in x.items() if k!='worst'} for x in poses],'contours':[{k:v for k,v in x.items() if k not in ['posteriorTrackedBands','lowestProjectedSamples','seatTriangleIds']} for x in contours]}))
