"""Virtual precision attribution only; no original construction changes."""
from pathlib import Path
import json,sys,numpy as np
from scipy.spatial import cKDTree
from collections import defaultdict,Counter
HERE=Path(__file__).resolve().parent;LANE=HERE.parent;sys.path.insert(0,str(LANE));from chart_labels import ROOT
SRC=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan');EVID=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan');f=np.load(HERE/'shell178-authored-copy.npz');P=f['p'];T=f['f'];panel=f['panel'];lit=json.loads((EVID/'literal-audit.json').read_text());pairs=lit['crossingWitnessFacePairs']+[[131,165],[281,315],[556,590],[706,740]]
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def overlap(tri,clip):
 origin=tri.mean(0);out=[p-origin for p in tri];clip=clip-origin;orientation=np.sign(cross(clip[1]-clip[0],clip[2]-clip[0]))
 for a,b in zip(clip,np.roll(clip,-1,axis=0)):
  incoming=out;out=[]
  if not incoming:break
  for p,q in zip(incoming,incoming[1:]+incoming[:1]):
   dp=orientation*cross(b-a,p-a);dq=orientation*cross(b-a,q-a);ip=dp>=0;iq=dq>=0
   if ip:out.append(p)
   if ip!=iq:out.append(p+(q-p)*(dp/(dp-dq)))
 return np.array(out)+origin if len(out)else np.empty((0,2))
rows=[]
for a,b in pairs:
 A=P[T[a]];B=P[T[b]];d=np.linalg.norm(A[:,None]-B[None],axis=2);d[T[a][:,None]==T[b][None,:]]=np.inf;ix=np.unravel_index(d.argmin(),d.shape);poly=overlap(A[:,1:],B[:,1:]);area=0.;penetration=0.
 if len(poly)>=3:
  q=poly-poly.mean(0);area=abs(sum(cross(v,w)for v,w in zip(q,np.roll(q,-1,axis=0))))*.5
  for tri in [A[:,1:],B[:,1:]]:
   orient=np.sign(cross(tri[1]-tri[0],tri[2]-tri[0]));dist=np.array([[orient*cross(v-u,p-u)/np.linalg.norm(v-u)for u,v in zip(tri,np.roll(tri,-1,axis=0))]for p in np.r_[poly,poly.mean(0)[None],(poly+np.roll(poly,-1,axis=0))*.5]]);penetration=max(penetration,float(dist.min(1).max(initial=0)))
 rows.append({'authoredFaces':[a,b],'panels':[str(panel[a]),str(panel[b])],'parentEarIDs':[a//25,b//25],'rawSharedVertexIDs':np.intersect1d(T[a],T[b]).tolist(),'nearRepeatedVertexIDs':[int(T[a][ix[0]]),int(T[b][ix[1]])],'nearRepeated3DDistanceM':float(d[ix]),'nearRepeatedDeltaBlenderM':(B[ix[1]]-A[ix[0]]).tolist(),'projectedYZOverlapAreaM2':area,'projectedYZMaximumInteriorPenetrationM':penetration,'projectedOverlapPolygon':poly.tolist()})
# Virtual union of submicrometer duplicate construction points, and removal
# of the known25zero-area ear children, is diagnostic only. Actual build unchanged.
near=cKDTree(P).query_pairs(5e-7);parent=np.arange(len(P))
def find(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
for a,b in near:
 aa,bb=find(a),find(b)
 if aa!=bb:parent[max(aa,bb)]=min(aa,bb)
U=np.array([find(i)for i in range(len(P))]);Q=P[T];area=np.linalg.norm(np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]),axis=1);virtual=T[area>=1e-12];virtual=U[virtual];edges=defaultdict(int)
for t in virtual:
 for a,b in zip(t,np.roll(t,-1)):edges[tuple(sorted((int(a),int(b))))]+=1
boundary=[e for e,n in edges.items()if n==1];adj=defaultdict(set)
for a,b in boundary:adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for root in adj:
 if root in seen:continue
 stack=[root];seen.add(root);ids=[]
 while stack:
  u=stack.pop();ids.append(u)
  for v in adj[u]:
   if v not in seen:seen.add(v);stack.append(v)
 components.append({'nodes':len(ids),'allDegreeTwo':all(len(adj[i])==2 for i in ids),'minBlenderM':P[ids].min(0).tolist(),'maxBlenderM':P[ids].max(0).tolist()})
r={'status':'VIRTUAL ATTRIBUTION ONLY; shell01 unchanged and failed','crossingWitnesses':rows,'precisionCause':'Adjacent parent ears independently interpolate the same material edge using float32 mathutils.Vector arithmetic, producing repeated points about119nm apart. Globalround7 key splits these IDs. Eight strictpair witnesses straddle those intendedsamepanel seams, with zero rawsharedIDs and nanometer projectedoverlap. Currentliteral crossesremainreal in storedgeometry.','virtualDryRun':{'duplicatePairsUnder.5Micrometer':len(near),'mergedVertexCount':int(len(P)-len(np.unique(U))),'maximumVirtualPointMoveM':float(np.linalg.norm(P-P[U],axis=1).max()),'removedZeroEarChildren':int((area<1e-12).sum()),'boundaryEdges':len(boundary),'nonmanifoldEdges':sum(n>2 for n in edges.values()),'boundaryComponents':components},'repairForSoleBuilder':'Use explicit parent-edge IDs plus integer subdivision parameterk/n to create shared seam nodes once; reusedirectedcanonicaledgearrays acrosspanels. Do not rely on globalcoordinateprecision weld, and do not use0.5um proximity union as productionconstructionpolicy. Reject/removecollinearback-neckear before subdivision. VerifyactualnextGLB literalcontacts and intended4boundarycycles.','limits':'Virtualthreshold union isolatesnumericcause only; not a modifiedmesh/candidate or broadliteralproof. IndependentQA owns actualexport audit.'};(HERE/'continuous-shell178-seam-precision.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
