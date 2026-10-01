"""Palm-anchored native IK; thumb opposition first; DQS versus LBS.

Native pivots and original weights are measured. Skin pad targets lie on the
literal cylinder. Every assigned angle comes from a geometric objective search.
"""
import bpy,hashlib,json,math,time
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-grip03/R';RUN=BASE/'rig-adapter01/native-grip03/R';LAND=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-landmarks';MASTER=BASE/'parent-assembly/donor-fit05/rider.blend';NATIVE=BASE/'glove-cleanup/mpfb-trial2/fresh-anatomical-source.blend';CAGE=BASE/'glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete/neutral-complete-R.npz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=[MASTER,NATIVE,CAGE,LAND/'report.json',LAND/'native-bones.json',LAND/'native-weight-transfer-map.json'];before={str(p):sha(p) for p in sources};start=time.perf_counter();h=json.loads((LAND/'report.json').read_text())['hands'][1];maprow=json.loads((LAND/'native-weight-transfer-map.json').read_text())['matches'][1];native=json.loads((LAND/'native-bones.json').read_text())['bones'];ids=np.array(maprow['completeVertexIds']);names=list(native);cols={n:i for i,n in enumerate(names)};weights=np.zeros((1668,len(names)))
for i,gs in enumerate(maprow['nativeWeights']):
 for n,w in gs:weights[i,cols[n]]=w
bpy.ops.wm.open_mainfile(filepath=str(MASTER));body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('NEW protected'));body.data.calc_loop_triangles();allpoints=np.array([body.matrix_world@v.co for v in body.data.vertices]);rest=allpoints[ids];local={int(v):i for i,v in enumerate(ids)};idset=set(ids);tris=np.array([[local[int(v)] for v in t.vertices] for t in body.data.loop_triangles if set(t.vertices)<=idset]);transform=np.array(h['sourceArmatureToBody']);bind={n:transform@np.array(b['matrixLocal']) for n,b in native.items()};heads={n:bind[n][:3,3] for n in names};tails={n:(transform@np.r_[native[n]['tailLocal'],1])[:3] for n in names};parents={n:native[n]['parent'] for n in names};normal=-np.array(h['sourceCanonicalNormalMapped']);length=np.array(h['palmLongAxisWristToMCP']);width=np.array(h['palmWidthIndexToLittle']);radius=.016576/1.015
for v in [normal,length,width]:v/=np.linalg.norm(v)
active=[f'finger{i}-{j}.R' for i in range(1,6) for j in range(1,4)];fw=weights[:,[cols[n] for n in active]].sum(1);fixed=fw<.02
wrist=np.array(h['wristJoint']);mcp=np.array(h['knuckleCentroid']);anchorInternal=wrist+.90*(mcp-wrist);bvh=BVHTree.FromPolygons([Vector(p) for p in rest],tris.tolist(),all_triangles=True);hit,n,ti,distance=bvh.ray_cast(Vector(anchorInternal),Vector(normal),.10)
assert hit is not None,'No measured distal palm surface ray';anchor=np.array(hit);centre=anchor+normal*radius
# Preserve static palm clearance while retaining the cylinder near the witness.
fixedtris=tris[np.all(fixed[tris],axis=1)]
def cylinderDistances(p,c):
 q=p-c;projected=np.stack([q@normal,q@length],1);t=projected[tris];a=t;b=np.roll(t,-1,axis=1);edge=b-a;cross=a[:,:,0]*b[:,:,1]-a[:,:,1]*b[:,:,0];inside=(cross.min(1)>=-1e-15)|(cross.max(1)<=1e-15);u=np.clip(-np.sum(a*edge,2)/np.maximum(np.sum(edge*edge,2),1e-18),0,1);dist=np.linalg.norm(a+u[:,:,None]*edge,axis=2).min(1);dist[inside]=0;return dist
fixedmask=np.all(fixed[tris],axis=1);placement=[]
for clearance in np.arange(0,.0201,.0005):
 trialcentre=anchor+normal*(radius+clearance);r=cylinderDistances(rest,trialcentre);minfixed=float(r[fixedmask].min());placement.append({'additionalNormalOffsetM':float(clearance),'minimumFixedPalmTriangleRadiusM':minfixed})
 if minfixed>=radius-.00005:centre=trialcentre;break
else:raise RuntimeError('Palm anchoring cannot clear fixed native skin within20mm')
# Actual unchanged runtime-R rubber-grip island, transported with a proper
# rotation and declared inverse1.015 scale into the native source fixture.
actualReport=LAND.parent/'bike-grip-surface02/report.json';sources.append(actualReport);before[str(actualReport)]=sha(actualReport)
g=next(g for g in json.loads(actualReport.read_text())['results'][0]['grips'] if g['side']=='L');surface=g['sourceMeshSurface'];vertexids=[v['sourceVertex'] for v in surface['vertices']];vmap={i:k for k,i in enumerate(vertexids)};worldpoints=np.array([v['point'] for v in surface['vertices']]);rodtris=np.array([[vmap[i] for i in t] for t in surface['triangles']]);wa=np.array(g['recipeAxis']['a']);wb=np.array(g['recipeAxis']['b']);wax=(wb-wa)/np.linalg.norm(wb-wa);marker=np.array(g['markerWorld']);worldCentre=wa+wax*np.dot(marker-wa,wax)
nn=normal-width*np.dot(normal,width);nn/=np.linalg.norm(nn);ll=np.cross(width,nn);nativeBasis=np.column_stack([width,nn,ll]);wn=np.array([0.,-1.,0.]);wn-=wax*np.dot(wn,wax);wn/=np.linalg.norm(wn)
if np.dot(np.cross(wax,wn),[1,0,0])*np.dot(ll,length)<0:wax=-wax
worldBasis=np.column_stack([wax,wn,np.cross(wax,wn)]);nativeToRuntime=worldBasis@nativeBasis.T;assert abs(np.linalg.det(nativeToRuntime)-1)<1e-10
rodpoints=centre+(worldpoints-worldCentre)@nativeToRuntime/1.015
# Outward triangle orientation checked against convex grip center, preserving
# exact decoded vertex surfaces. No authored replacement cylinder is rendered.
for t in rodtris:
 q=rodpoints[t];n=np.cross(q[1]-q[0],q[2]-q[0])
 if np.dot(n,q.mean(0)-centre)<0:t[1],t[2]=t[2],t[1]
rodBVH=BVHTree.FromPolygons([Vector(v) for v in rodpoints],rodtris.tolist(),all_triangles=True)
virtualMarker=centre+(marker-worldCentre)@nativeToRuntime/1.015
rod={'source':str(actualReport),'runtimeSide':'L','sourceTriangles':len(rodtris),'sourceVertices':len(rodpoints),'nativeToRuntimeProperRotation':nativeToRuntime.tolist(),'runtimeRodCentre':worldCentre.tolist(),'runtimePhysicalGripMarker':marker.tolist(),'nativeFixtureCentre':centre.tolist(),'nativeVirtualPhysicsMarker':virtualMarker.tolist(),'nativeRodPoints':rodpoints.tolist(),'nativeRodTriangles':rodtris.tolist(),'declaredCharacterScale':1.015,'sourceIslandSHA256':hashlib.sha256(json.dumps(surface,sort_keys=True).encode()).hexdigest()}
def rodSignedDistances(p):
 result=[]
 for v in p:
  closest,n,index,d=rodBVH.find_nearest(Vector(v));assert closest is not None
  result.append(float(d)*(-1 if (Vector(v)-closest).dot(n)<0 else 1))
 return np.array(result)
# Five thumb degrees of freedom, then three native hinges per other finger.
params=['thumb.base.width','thumb.base.length','thumb.base.normal','thumb.PIP','thumb.DIP']+[f'finger{i}-{j}.R' for i in range(2,6) for j in range(1,4)];bounds=[(-95,95),(-95,95),(-95,95),(0,105),(0,85)]+[(0,105),(0,110),(0,85)]*4;bounds=np.radians(bounds)
axes={}
for finger in range(1,6):
 for joint in range(1,4):
  name=f'finger{finger}-{joint}.R';axis=width.copy();direction=tails[name]-heads[name]
  if np.dot(np.cross(axis,direction),normal)<0:axis=-axis
  axes[name]=axis
# Palmar native pad witnesses, derived from rest surface and native influence.
pads={}
for name in active:
 mask=weights[:,cols[name]]>.45;v=tails[name]-heads[name];u=np.clip((rest-heads[name])@v/np.dot(v,v),0,1);side=(rest-(heads[name]+u[:,None]*v))@normal;pads[name]=np.flatnonzero(mask&(side>=np.quantile(side[mask],.55)))
def rotation(axis,a):
 x,y,z=axis;k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return np.eye(3)+math.sin(a)*k+(1-math.cos(a))*(k@k)
def boneDeltas(a):
 own={}
 own['finger1-1.R']=rotation(normal,a[2])@rotation(length,a[1])@rotation(width,a[0]);own['finger1-2.R']=rotation(axes['finger1-2.R'],a[3]);own['finger1-3.R']=rotation(axes['finger1-3.R'],a[4])
 for i,name in enumerate(params[5:],5):own[name]=rotation(axes[name],a[i])
 delta={}
 def solve(n):
  if n in delta:return delta[n]
  d=solve(parents[n]).copy() if parents[n] else np.eye(4)
  if n in own:
   r=own[n];q=np.eye(4);q[:3,:3]=r;q[:3,3]=heads[n]-r@heads[n];d=d@q
  delta[n]=d;return d
 return {n:solve(n) for n in active}
def qmul(a,b):
 return np.r_[a[0]*b[0]-np.dot(a[1:],b[1:]),a[0]*b[1:]+b[0]*a[1:]+np.cross(a[1:],b[1:])]
def deform(a,mode='DQS'):
 if not np.any(a):return rest.copy()
 delta=boneDeltas(a)
 if mode=='LBS':
  p=rest.copy()
  for n,d in delta.items():p+=weights[:,cols[n],None]*(rest@d[:3,:3].T+d[:3,3]-rest)
  return p
 quats=[];duals=[]
 for n in active:
  d=delta[n];q=np.array(Matrix(d[:3,:3]).to_quaternion());quats.append(q);duals.append(.5*qmul(np.r_[0,d[:3,3]],q))
 qs=np.vstack([np.array([1.,0,0,0]),quats]);ds=np.vstack([np.zeros(4),duals]);w=np.column_stack([1-fw,weights[:,[cols[n] for n in active]]]);refs=qs[np.argmax(w,axis=1)];sign=np.where(refs@qs.T<0,-1.,1.);qr=(w*sign)@qs;qd=(w*sign)@ds;norm=np.linalg.norm(qr,axis=1);qr/=norm[:,None];qd/=norm[:,None];qd-=qr*np.sum(qr*qd,axis=1)[:,None];v=qr[:,1:];p=rest+2*np.cross(v,np.cross(v,rest)+qr[:,0,None]*rest);translation=2*(-qd[:,0,None]*v+qr[:,0,None]*qd[:,1:]+np.cross(v,qd[:,1:]));return p+translation
# Surface targets run clockwise around the measured circle from each MCP.
targets={}
for finger in range(2,6):
 base=heads[f'finger{finger}-1.R'];v=base-centre;v-=width*np.dot(v,width);angle=math.atan2(np.dot(v,length),np.dot(v,normal));travel=0
 for joint in range(1,4):
  name=f'finger{finger}-{joint}.R';segment=float(np.linalg.norm(tails[name]-heads[name]));theta=angle-(travel+.5*segment)/.026;targets[name]=centre+width*np.dot(base-centre,width)+radius*(normal*math.cos(theta)+length*math.sin(theta));travel+=segment
thumbAxis=np.dot(heads['finger1-1.R']-centre,width);thumbTarget=centre+width*thumbAxis+radius*(normal*.90-length*math.sqrt(1-.90**2));targets['finger1-3.R']=thumbTarget
# Geometry-dependent circle seeds are projected onto the real polygon/taper surface.
for n,p in targets.items():
 hit,normalAt,index,d=rodBVH.find_nearest(Vector(p));assert hit is not None;targets[n]=np.array(hit)
basecross=np.cross(rest[tris[:,1]]-rest[tris[:,0]],rest[tris[:,2]]-rest[tris[:,0]]);basearea=np.linalg.norm(basecross,axis=1)
def overlapcount(p):
 b=BVHTree.FromPolygons([Vector(v) for v in p],tris.tolist(),all_triangles=True);return [(a,c) for a,c in b.overlap(b) if a<c and not(set(tris[a])&set(tris[c]))]
assert len(overlapcount(rest))==0
history=[]
def objective(a,thumbOnly=False,withOverlap=False):
 p=deform(a);score=0
 if thumbOnly:
  selected=['finger1-3.R'];mask=weights[:,[cols[f'finger1-{j}.R'] for j in range(1,4)]].sum(1)>.1;q=p[mask]-centre;q-=np.outer(q@width,width);penetration=np.maximum(radius-np.linalg.norm(q,axis=1),0);score+=1000*np.sum(np.maximum(-rodSignedDistances(p),0)**2)
 else:
  selected=list(targets);q=p-centre;q-=np.outer(q@width,width);penetration=np.maximum(radius-np.linalg.norm(q,axis=1),0);score+=1000*np.sum(np.maximum(-rodSignedDistances(p),0)**2)
 for name in selected:
  # Closest pad patch, rather than an imagined fingertip/socket target.
  ds=np.linalg.norm(p[pads[name]]-targets[name],axis=1);score+=float(np.mean(np.sort(ds)[:max(2,len(ds)//4)]**2))*6
 score+=float(np.sum(a*a))*.0000001
 if withOverlap:score+=.002*len(overlapcount(p))
 return float(score)
def search(a,indices,thumbOnly=False,withOverlap=False):
 for stepdeg in [40,20,10,5,2.5,1.25]:
  step=math.radians(stepdeg)
  for sweep in range(8):
   changed=False;score=objective(a,thumbOnly,withOverlap)
   for i in indices:
    original=a[i];bestscore=score;bestvalue=original
    for candidate in [np.clip(original-step,*bounds[i]),np.clip(original+step,*bounds[i])]:
     trial=a.copy();trial[i]=candidate;s=objective(trial,thumbOnly,withOverlap)
     if s+1e-12<bestscore:bestscore=s;bestvalue=candidate
    if bestvalue!=original:a[i]=bestvalue;score=bestscore;changed=True
   history.append({'thumbOnly':thumbOnly,'withOverlap':withOverlap,'stepDegrees':stepdeg,'sweep':sweep,'objective':score,'anglesDegrees':np.degrees(a).tolist()})
   if not changed:break
 return a
angles=search(np.zeros(len(params)),range(5),True,False)
# Cylinder-derived circle/tangent seeds for the fingers, then full native search.
for finger in range(2,6):
 block=list(range(5+(finger-2)*3,8+(finger-2)*3));best=(objective(angles),angles.copy())
 for flex in [25,55,85]:
  trial=angles.copy();trial[block]=np.radians([flex,60,35]);trial=search(trial,block,False,False);score=objective(trial)
  if score<best[0]:best=(score,trial.copy())
 angles=best[1]
angles=search(angles,range(len(params)),False,True)

# One held shape only. Do not repeat rejected closing/handle-entry animation.
wrapped=deform(angles,'DQS');wristids=np.array(np.load(CAGE)['wristLoop'],dtype=int);distances=rodSignedDistances(wrapped);overlaps=overlapcount(wrapped);checks={}
for finger in range(1,6):
 namesf=[f'finger{finger}-{j}.R' for j in range(1,4)];patch=np.unique(np.concatenate([pads[n] for n in namesf]));ds=distances[patch];checks[str(finger)]={'padVertices':len(patch),'nearestAbsoluteGapM':float(np.abs(ds).min()),'insideRodVertices':int((ds<0).sum()),'maximumPadPenetrationM':float(np.maximum(-ds,0).max())}
bodyBVH=BVHTree.FromPolygons([Vector(v) for v in wrapped],tris.tolist(),all_triangles=True);crosspairs=bodyBVH.overlap(rodBVH);cross=np.cross(wrapped[tris[:,1]]-wrapped[tris[:,0]],wrapped[tris[:,2]]-wrapped[tris[:,0]]);area=np.linalg.norm(cross,axis=1);wristdelta=float(np.linalg.norm(wrapped[wristids]-rest[wristids],axis=1).max())
np.savez(RUN/'native-held-shape.npz',sourceCompleteVertexIds=ids,sourcePositions=rest,wrappedPositionsDQS=wrapped,morphDeltaDQS=wrapped-rest,triangleIndices=tris,anglesRadians=angles,parameterNames=np.array(params),rodPoints=rodpoints,rodTriangleIndices=rodtris,nativeToRuntimeProperRotation=nativeToRuntime,runtimeRodCentre=worldCentre,nativeFixtureCentre=centre,nativeVirtualPhysicsMarker=virtualMarker,wristLoopLocalIds=wristids)
report={'status':'Unaccepted nativeR/runtimeL heldshape against actualunchanged rubbergrip; no closingsequence repeated','sourceHashesBefore':before,'sourceHashesAfter':{str(p):sha(p) for p in sources},'recipeSHA256':sha(Path(__file__)),'actualRod':rod,'wristMaximumDeltaM':wristdelta,'nonadjacentHandOverlapPairs':len(overlaps),'handOverlapExamples':overlaps[:30],'actualRodHandCrossingTrianglePairs':len(crosspairs),'rodCrossingExamples':crosspairs[:30],'maximumActualRodVertexPenetrationNativeM':float(np.maximum(-distances,0).max()),'minimumTriangleAreaRatio':float((area/np.maximum(basearea,1e-18)).min()),'fingerPadContacts':checks,'parameterAnglesDegrees':dict(zip(params,np.degrees(angles).tolist())),'searchHistory':history,'restUnchanged':True,'otherCompleteVerticesUnchangedByConstruction':True,'nativeNPZ':str(RUN/'native-held-shape.npz'),'nativeNPZSHA256':sha(RUN/'native-held-shape.npz'),'wallSeconds':time.perf_counter()-start,'limits':['Exact decoded realgrip triangles used for targetprojection, signedvertexpenalty and BVH crossingdiagnostic','Signedvertex penetration does not bound every intersectingtriangle; parent must inspect actualgeometry','Heldshape only; original rejected closingsequence notrerun','No full19rig/otherhand/playedphysics contactpass']}
assert wristdelta<1e-6;assert report['sourceHashesBefore']==report['sourceHashesAfter'];(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print('ACTUAL_ROD_NATIVE_HELD_SHAPE_FROZEN',flush=True)
