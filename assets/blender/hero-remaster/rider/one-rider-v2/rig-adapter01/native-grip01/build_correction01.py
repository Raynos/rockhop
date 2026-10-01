"""One native hand: geometry-dependent joint search against an 18mm cylinder.

No fixed curl angles. Measured native pivots/binds/weights drive linear skinning;
angle search minimizes cylinder gaps with explicit penetration penalties.
"""
import bpy,json,hashlib,math,time
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');SRC=Path(__file__).parent;OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-grip01';RUN=BASE/'rig-adapter01/native-grip01';LAND=OUT.parent/'native-landmarks'
MASTER=BASE/'parent-assembly/donor-fit05/rider.blend';NATIVE=BASE/'glove-cleanup/mpfb-trial2/fresh-anatomical-source.blend';CAGE=BASE/'glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete/neutral-complete-L.npz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=[MASTER,NATIVE,CAGE,LAND/'report.json',LAND/'native-weight-transfer-map.json',LAND/'native-bones.json'];before={str(p):sha(p) for p in sources};start=time.perf_counter()
hand=json.loads((LAND/'report.json').read_text())['hands'][0];mapping=json.loads((LAND/'native-weight-transfer-map.json').read_text())['matches'][0];native=json.loads((LAND/'native-bones.json').read_text())['bones'];ids=np.array(mapping['completeVertexIds']);bone_names=list(native);column={n:i for i,n in enumerate(bone_names)};weights=np.zeros((len(ids),len(bone_names)))
for vi,gs in enumerate(mapping['nativeWeights']):
 for n,w in gs:weights[vi,column[n]]=w
bpy.ops.wm.open_mainfile(filepath=str(MASTER));body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('NEW protected'));body.data.calc_loop_triangles();allpoints=np.array([body.matrix_world@v.co for v in body.data.vertices],dtype=np.float64);points=allpoints[ids];idset=set(ids);localmap={int(n):i for i,n in enumerate(ids)};triangles=np.array([[localmap[int(v)] for v in t.vertices] for t in body.data.loop_triangles if set(t.vertices)<=idset]);assert len(points)==1668
transform=np.array(hand['sourceArmatureToBody']);rest={n:transform@np.array(b['matrixLocal']) for n,b in native.items()};head={n:rest[n][:3,3] for n in native};tail={n:(transform@np.r_[b['tailLocal'],1])[:3] for n,b in native.items()};parents={n:b['parent'] for n,b in native.items()}
width=np.array(hand['palmWidthIndexToLittle']);length=np.array(hand['palmLongAxisWristToMCP']);normal=-np.array(hand['sourceCanonicalNormalMapped']);width/=np.linalg.norm(width);length/=np.linalg.norm(length);normal/=np.linalg.norm(normal);radius=.018
mcp=np.mean([head[f'finger{i}-1.L'] for i in range(2,6)],axis=0)
# Place an infinite circular cross-section just outside the actual open hand.
# Axis length is finite160mm for render; all tested finger points lie within it.
placement=[];best=None
for proximal in np.arange(-.040,.041,.002):
 for offset in np.arange(.018,.075,.001):
  centreTry=mcp+length*proximal+normal*offset;rad=points-centreTry;rad-=np.outer(rad@width,width);r=np.linalg.norm(rad,axis=1);minimum=float(r.min());mcpRad=[]
  for finger in range(2,6):
   v=head[f'finger{finger}-1.L']-centreTry;v-=width*np.dot(v,width);mcpRad.append(float(np.linalg.norm(v)))
  score=float(offset*offset+proximal*proximal+.5*np.mean((np.array(mcpRad)-.026)**2))
  placement.append({'longitudinalShiftM':float(proximal),'normalOffsetM':float(offset),'minimumOpenSkinRadiusM':minimum,'MCPRadialDistancesM':mcpRad,'score':score})
  if minimum>=radius+.0005 and min(mcpRad)>=radius+.004:
   if best is None or score<best[0]:best=(score,centreTry.copy(),proximal,offset,minimum)
if best is None:raise RuntimeError('No external2D18mmcylinderplacement found')
centre=best[1]
params=[f'finger{i}-{j}.L' for i in range(1,6) for j in range(1,4)];axes={};limits=[]
for n in params:
 finger=int(n[6]);joint=int(n[8]);direction=tail[n]-head[n]
 if finger==1:
  target=centre+width*np.dot(head[n]-centre,width);axis=np.cross(direction,target-head[n]);axis/=np.linalg.norm(axis)
 else:
  axis=width.copy()
  if np.dot(np.cross(axis,direction),normal)<0:axis=-axis
 axes[n]=axis;limits.append(math.radians([95,110,85][joint-1] if finger!=1 else [100,105,85][joint-1]))
padsets={}
for n in params:
 mask=weights[:,column[n]]>.45;direction=tail[n]-head[n];u=np.clip(((points-head[n])@direction)/np.dot(direction,direction),0,1);closest=head[n]+u[:,None]*direction;side=(points-closest)@normal
 candidates=np.flatnonzero(mask & (side>=np.quantile(side[mask],.55)))
 padsets[n]=candidates
 def finite():return None
assert all(len(i)>0 for i in padsets.values())
def rot(axis,angle):
 a=axis;x,y,z=a;s=math.sin(angle);c=math.cos(angle);k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return np.eye(3)+s*k+(1-c)*(k@k)
def deform(angles):
 delta={};values=dict(zip(params,angles))
 def solve(n):
  if n in delta:return delta[n]
  d=solve(parents[n]).copy() if parents[n] else np.eye(4)
  if n in values:
   r=rot(axes[n],values[n]);q=np.eye(4);q[:3,:3]=r;q[:3,3]=head[n]-r@head[n];d=d@q
  delta[n]=d;return d
 out=points.copy()
 for n in params:
  d=solve(n);moved=points@d[:3,:3].T+d[:3,3];out+=weights[:,column[n]][:,None]*(moved-points)
 return out,delta
# Skinning covers all15 changed native bones. Unchanged native influences are
# exactly identity; use rest+weightedDelta so open rest is byte-exact.
def metrics(angles):
 p,delta=deform(angles);q=p-centre;q-=np.outer(q@width,width);r=np.linalg.norm(q,axis=1);penetration=np.maximum(radius-r,0);contacts={}
 objective=1000*float(np.sum(penetration**2))
 for n,indices in padsets.items():
  # Skin pad witnesses seek the surface, rather than skeletal joints/caps.
  gap=r[indices]-radius;nearest=np.sort(np.maximum(gap,0))[:max(2,len(indices)//3)];objective+=float(np.mean((nearest-.0006)**2))*10
  contacts[n]={'nearestPadGapM':float(gap.min()),'medianPadGapM':float(np.median(gap)),'padVertices':len(indices)}
 objective+=float(np.sum(np.array(angles)**2))*.00000005
 return objective,p,{'maximumCylinderPenetrationM':float(penetration.max()),'penetratingVerticesOver1mm':int((penetration>.001).sum()),'contacts':contacts},delta
angles=np.zeros(len(params));history=[]
# Multi-resolution coordinate search, bounded native joint intervals. Trial
# angles are selected by measured skin/cylinder objective, never canned curls.
for stepdeg in [30,15,7.5,3.75,1.875,.9375]:
 step=math.radians(stepdeg)
 for sweep in range(8):
  changed=False;score=metrics(angles)[0]
  for i,n in enumerate(params):
   best=score;value=angles[i]
   for candidate in [max(0,value-step),min(limits[i],value+step)]:
    trial=angles.copy();trial[i]=candidate;s=metrics(trial)[0]
    if s+1e-12<best:best=s;value=candidate
   if value!=angles[i]:angles[i]=value;score=best;changed=True
  history.append({'stepDegrees':stepdeg,'sweep':sweep,'objective':score,'anglesDegrees':np.degrees(angles).tolist()})
  if not changed:break
score,wrapped,contact,delta=metrics(angles);basis=np.cross(points[triangles[:,1]]-points[triangles[:,0]],points[triangles[:,2]]-points[triangles[:,0]]);area=np.linalg.norm(basis,axis=1);frames=[];checks=[]
for index in range(33):
 phase=index/32;amount=math.sin(math.pi*phase)**2;p,_=deform(angles*amount);normal2=np.cross(p[triangles[:,1]]-p[triangles[:,0]],p[triangles[:,2]]-p[triangles[:,0]]);area2=np.linalg.norm(normal2,axis=1);cos=np.sum(basis*normal2,axis=1)/np.maximum(area*area2,1e-18)
 _,_,m,_=metrics(angles*amount);frames.append(p);checks.append({'frame':index,'wrapAmount':amount,'finite':bool(np.isfinite(p).all()),'minimumAreaRatio':float(np.min(area2/np.maximum(area,1e-18))),'normalAgainstRestBelowZeroTriangles':int((cos<0).sum()),'maximumCylinderPenetrationM':m['maximumCylinderPenetrationM'],'penetratingVerticesOver1mm':m['penetratingVerticesOver1mm']})
frames=np.array(frames);wrist=np.load(CAGE)['wristLoop'];wrist=np.array(wrist,dtype=int);wristdelta=np.linalg.norm(frames[:,wrist]-points[wrist],axis=2);assert np.array_equal(frames[0],points);assert np.max(wristdelta)<1e-6
np.savez(RUN/'native-hand-animation.npz',sourceCompleteVertexIds=ids,sourcePositions=points,wrappedPositions=wrapped,morphDelta=wrapped-points,framePositions=frames,triangleIndices=triangles,anglesRadians=angles,parameterNames=np.array(params),cylinderCentre=centre,cylinderAxis=width,cylinderRadius=radius,wristLoopLocalIds=wrist)
report={'status':'One geometry-driven native finger articulation; parent played judgment required; noacceptedgrip','sourceHashesBefore':before,'sourceHashesAfter':{str(p):sha(p) for p in sources},'recipeSHA256':sha(Path(__file__)),'nativeSide':'L','runtimeContractSide':'R','cylinder':{'radiusM':radius,'lengthM':.160,'centre':centre.tolist(),'axis':width.tolist(),'placementRule':'2Dactualopenhandclearance + measuredMCPdistance search inlongitudinal/palmnormalplane, minimum18.5mmradialskinclearance; literal18mmradius','selectedPlacement':{'longitudinalShiftM':float(best[2]),'normalOffsetM':float(best[3]),'minimumOpenSkinRadiusM':float(best[4])},'placementSearch':placement},'solver':'Bounded multi-resolution coordinate search on actual native rest pivots and native vertex skin weights; pad/cylinder gap objective plus1000xpenetrationpenalty; notfixedcurl','parameterAnglesDegrees':dict(zip(params,np.degrees(angles).tolist())),'axes':{n:a.tolist() for n,a in axes.items()},'wrappedContacts':contact,'objective':score,'searchHistory':history,'frameChecks':checks,'maximumWristRimDeltaM':float(wristdelta.max()),'staticCompleteOtherVerticesUnchangedByConstruction':True,'restPositionsByteExact':np.array_equal(frames[0],points),'NPZ':str(RUN/'native-hand-animation.npz'),'NPZSHA256':sha(RUN/'native-hand-animation.npz'),'wallSeconds':time.perf_counter()-start,'limits':['Contact witnesses are mesh vertices, not continuoussurfacecertification.','Normal change against rest is not automatically trianglefold because finger rotation changes normal; local inversion still requires shape/contactreview.','No runtime19rig or completebodyedit.','Thumbusesmeasuredtargetdependentaxes, fingersusemeasuredpalmlateralaxis with geometrysearchangles.','No selfintersection clearance certificate yet.','First1Dplacement failed beforearticulation;2Dcorrectionpreserves sourcebytesandliteralcylinder.']}
assert report['sourceHashesBefore']==report['sourceHashesAfter'];(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print('GEOMETRY_DEPENDENT_NATIVE_GRIP_FROZEN',contact,flush=True)
