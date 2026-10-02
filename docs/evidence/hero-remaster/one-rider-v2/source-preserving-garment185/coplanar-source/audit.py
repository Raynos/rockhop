"""Exact source near-coplanar registry and rational projected overlap, no repair."""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter,defaultdict
import ast,json,struct,hashlib,time,re,subprocess,numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment185/coplanar-source';S=B/'source-preserving-garment185/coplanar-source';sha=lambda b:hashlib.sha256(b).hexdigest();pins={};start=time.monotonic()
def pin(p):
 p=Path(p);b=p.read_bytes();pins[str(p)]={'path':str(p),'SHA256':sha(b),'bytes':len(b)};return b

def memory():
 txt=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',txt).group(1));n=int(re.search(r'Anonymous pages:\s+(\d+)',txt).group(1));gb=page*n/1e9;assert gb<70;return gb
mem=[memory()];source=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb');reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py';tree=ast.parse(pin(reader).decode());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='GLB');env={'Path':Path,'json':json,'struct':struct,'np':np,'Rotation':Rotation,'sha':sha};exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),env);C=env['GLB'](source,'186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e');pin(source);originalReportPath=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment184/source-audit/report.json';old=json.loads(pin(originalReportPath));pin(R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment184/source-audit/audit.py');proposalPath=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment184/operator-proposal/hood185-candidates.json';proposal=json.loads(pin(proposalPath));assert proposal['sourceSHA256']==C.h;slots=set(proposal['allowedSourceFaceSlots']);assert len(slots)==28
attrs=[];Fs=[];Ps=[];pi=[];li=[];offset=0
for k in range(3):
 a,f=C.primitive(0,k);attrs.append(a);Ps.append(a['POSITION']);Fs.append(f+offset);offset+=len(a['POSITION']);pi.extend([k]*len(f));li.extend(range(len(f)))
P=np.concatenate(Ps);F=np.concatenate(Fs);U,iv=np.unique(P,axis=0,return_inverse=True);pf=iv[F];T=P[F].astype(float);pi=np.array(pi);li=np.array(li);cent=T.mean(1);rad=np.linalg.norm(T-cent[:,None,:],axis=2).max(1);lo=T.min(1);hi=T.max(1);N=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);LN=np.linalg.norm(N,axis=1);UN=np.divide(N,LN[:,None],out=np.zeros_like(N),where=LN[:,None]>1e-14);tree=cKDTree(cent);rmax=float(rad.max());near=[];last=0
for begin in range(0,len(T),256):
 assert time.monotonic()-start<7.5*60
 if time.monotonic()-last>15:mem.append(memory());last=time.monotonic()
 ns=tree.query_ball_point(cent[begin:begin+256],rad[begin:begin+256]+rmax+1e-12,workers=2)
 for off,neighbors in enumerate(ns):
  i=begin+off;js=np.array([j for j in neighbors if j>i],dtype=int)
  if not len(js):continue
  scope=((pi[i]==0)&np.isin(pi[js],[0,1,2]))|((pi[i]==2)&(pi[js]==2));js=js[scope]
  if not len(js):continue
  js=js[np.linalg.norm(cent[js]-cent[i],axis=1)<=rad[js]+rad[i]+1e-12];js=js[(hi[i]>=lo[js]-1e-12).all(1)&(lo[i]<=hi[js]+1e-12).all(1)]
  if not len(js):continue
  cp=(np.linalg.norm(np.cross(UN[i],UN[js]),axis=1)<1e-8)&(abs(np.einsum('ij,ij->i',T[js,0]-T[i,0],np.broadcast_to(UN[i],(len(js),3))))<1e-8)
  for j in js[cp]:
   shared=len(set(pf[i])&set(pf[j]))
   if shared<2:near.append((i,int(j),shared))
assert len(near)==old['strictCrossings']['coplanarCandidatesUnclassified']==3
# Rational arithmetic acts on exact original float32 dyadic coordinates. No epsilon-adjusted clipping.
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def c2(a,b):return a[0]*b[1]-a[1]*b[0]
def c3(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def rational_triangle(tri):return [tuple(Q(float(x))for x in p)for p in tri]
def clip_exact(A,B):
 if c2(sub(B[1],B[0]),sub(B[2],B[0]))<0:B=[B[0],B[2],B[1]]
 poly=A[:]
 for k in range(3):
  if not poly:break
  a,b=B[k],B[(k+1)%3];v=sub(b,a);out=[]
  for p,q in zip(poly,poly[1:]+poly[:1]):
   dp,dq=c2(v,sub(p,a)),c2(v,sub(q,a));ip,iq=dp>=0,dq>=0
   if ip:out.append(p)
   if ip!=iq:
    t=dp/(dp-dq);out.append(tuple(p[z]+t*(q[z]-p[z])for z in range(2)))
  poly=[]
  for p in out:
   if p not in poly:poly.append(p)
 return poly

def face(i):return {'sourceMesh':0,'sourcePrimitive':int(pi[i]),'sourceFace':int(li[i]),'sourceVertexRows':(Fs[int(pi[i])][int(li[i])]-sum(len(p)for p in Ps[:int(pi[i])])).tolist(),'physicalIDs':pf[i].tolist(),'sourceFloat32Positions':T[i].tolist()}
def classify(i,j,shared,label):
 A,Bt=rational_triangle(T[i]),rational_triangle(T[j]);n=c3(sub(A[1],A[0]),sub(A[2],A[0]));exactResidual=[dot(n,sub(p,A[0]))for p in Bt];exact=all(v==0 for v in exactResidual);axis=int(np.argmax(abs(N[i])));keep=[k for k in range(3)if k!=axis];AA=[tuple(p[k]for k in keep)for p in A];BB=[tuple(p[k]for k in keep)for p in Bt];poly=clip_exact(AA,BB);area=abs(sum(c2(poly[k],poly[(k+1)%len(poly)])for k in range(len(poly))))/2 if len(poly)>=3 else Q(0);crossNorm=float(np.linalg.norm(np.cross(UN[i],UN[j])));signedNormal=float(UN[i]@UN[j]);plane=abs(float((T[j,0]-T[i,0])@UN[i]));allPlane=float(abs((T[j]-T[i,0])@UN[i]).max());width=float(max((np.linalg.norm(np.array([float(v)for v in p])-np.array([float(v)for v in q]))for p in poly for q in poly),default=0));classification='positive_projected_area_overlap'if area>0 else'edge_or_segment_only'if width>0 else'point_only'if poly else'disjoint_projection';sameSides=None
 if shared==2:
  common=list(set(pf[i])&set(pf[j]));a,b=U[common].astype(float);oa=next(p for p,id in zip(T[i],pf[i])if id not in common);ob=next(p for p,id in zip(T[j],pf[j])if id not in common);aa=a[keep];bb=b[keep];da=c2(tuple(bb-aa),tuple(oa[keep]-aa));db=c2(tuple(bb-aa),tuple(ob[keep]-aa));sameSides=bool(da*db>0)
 return {'registryID':label,'A':face(i),'B':face(j),'sharedPhysicalVertices':shared,'source184NearPlanePredicate':{'unitNormalCrossMagnitude':crossNorm,'absoluteB0ToAPlaneM':plane,'thresholds':{'normalCross':1e-8,'planeDistanceM':1e-8},'predicate':crossNorm<1e-8 and plane<1e-8},'planeGeometry':{'unitNormalDot':signedNormal,'maxAllBVerticesDistanceToAPlaneM':allPlane,'exactRationalCoplanar':exact,'exactTripleProductsNumeratorDenominator':[[str(v.numerator),str(v.denominator)]for v in exactResidual]},'projection':{'droppedAxis':axis,'keptAxes':keep,'intersectionPolygonExactRational':[[[str(x.numerator),str(x.denominator)]for x in p]for p in poly],'intersectionPolygonApproxMetres':[[float(x)for x in p]for p in poly],'projectedOverlapAreaM2':float(area),'projectedOverlapAreaExactNumeratorDenominator':[str(area.numerator),str(area.denominator)],'classification':classification,'sharedEdgeOppositeCornersSameProjectedSide':sameSides,'metricLimit':'For nonexact planes, projected area is not actual coplanar surface area or a new strict3D crossing certificate.'}}
registry=[classify(i,j,s,f'original-near-coplanar-{k}')for k,(i,j,s)in enumerate(sorted(near))];hoodBase=len(Fs[0])+len(Fs[1]);localEdges=defaultdict(list)
for localFace in slots:
 i=hoodBase+localFace
 for k in range(3):localEdges[tuple(sorted([int(pf[i,k]),int(pf[i,(k+1)%3])]))].append(i)
adj=[]
for e,faces in localEdges.items():
 if len(faces)==2:
  i,j=sorted(faces);adj.append(classify(i,j,2,f'local-original-adjacent-{int(li[i])}-{int(li[j])}'))
mem.append(memory());report={'status':'FROZEN_ORIGINAL_C19_COPLANAR_PREREQUISITE_NO_EDITS','sourceSHA256':C.h,'source184ReportedNearCandidates':3,'exactPredicateRegistry':registry,'operatorAllowedOriginalHoodFaces':sorted(slots),'localOriginalTwoSharedAdjacentPairs':adj,'summary':{'originalRegistryPairs':len(registry),'originalExactCoplanarPairs':sum(x['planeGeometry']['exactRationalCoplanar']for x in registry),'originalProjectedAreaOverlapPairs':sum(x['projection']['projectedOverlapAreaM2']>0 for x in registry),'localAdjacentPairs':len(adj),'localAdjacentNearPlanePairs':sum(x['source184NearPlanePredicate']['predicate']for x in adj),'localAdjacentExactCoplanarAreaOverlapPairs':sum(x['planeGeometry']['exactRationalCoplanar']and x['projection']['projectedOverlapAreaM2']>0 for x in adj),'localAdjacentPositiveProjectedAreaPairsRegardlessPlane':sum(x['projection']['projectedOverlapAreaM2']>0 for x in adj),'localAdjacentSameProjectedSidePairs':sum(x['projection']['sharedEdgeOppositeCornersSameProjectedSide']is True for x in adj)},'method':'Same original184 source/scope and conservative centre-radius/AABB candidates, same1e-8normalcross/B0plane predicate. Exactrational Sutherland-Hodgman2D intersection on dyadicfloat32sourcecoords; zeroarea means no strictlypositive projected interior overlap without tolerances. Exactrational tripleproducts distinguish sameplane from approximateplane. Original28faceoperatorhalo only, never expanded.','sampledAnonymousGB':mem,'seconds':time.monotonic()-start,'inputHashes':list(pins.values()),'recipeSHA256':sha(Path(__file__).read_bytes()),'knownStrictSourcePairsRemain':11,'limits':['No changedindices/positions/UV/weights, no removal/rejection ofpairs tofakezero, no newexport/render/GPU/rigging orshader acceptance.','Projectedoverlap for distinctplanes is a geometricreference, not physicalpenetration itself; tangent/adjacent folds needseparate local geometry/moving review.','This freezes onlyoriginal3near-coplanar0/1shared registry plusoriginal28facehood2sharedadjacency, not globalcoplanar pairs with2+shared vertices.','All original strict11pairs remain source defects; this diagnostic doesnotclear or repairthem.']}
np.savez_compressed(S/'original-pair-registry.npz',nearGlobalPairs=np.array(near,dtype=int),sourcePrimitivePerFace=pi,sourceLocalFaceIDs=li,nearTriangles=np.array([[T[i],T[j]]for i,j,s in near]));report['privateOutputs']=[{'path':str(p),'SHA256':sha(p.read_bytes())}for p in S.glob('*')]
for p,x in pins.items():assert sha(Path(p).read_bytes())==x['SHA256']
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'summary':report['summary'],'registry':[(x['A']['sourcePrimitive'],x['A']['sourceFace'],x['B']['sourcePrimitive'],x['B']['sourceFace'],x['planeGeometry']['exactRationalCoplanar'],x['projection']['classification'],x['projection']['projectedOverlapAreaM2'])for x in registry],'adjacentPositive':[(x['A']['sourceFace'],x['B']['sourceFace'],x['planeGeometry']['exactRationalCoplanar'],x['projection']['projectedOverlapAreaM2'],x['source184NearPlanePredicate']['predicate'])for x in adj if x['projection']['projectedOverlapAreaM2']>0]}))
