"""Resume verification of frozen actual192dump, without generating another mesh."""
from pathlib import Path
from collections import defaultdict,Counter,deque
from fractions import Fraction as Q
import ast,copy,hashlib,json,os,re,struct,subprocess,time
import numpy as np
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/panel-surgery192';S=B/'panel-surgery192';start=time.monotonic();pins={};mem=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def pin(p,h=None):
 p=Path(p);b=p.read_bytes();d=sha(b);assert h is None or d==h;pins[str(p)]={'sha256':d,'bytes':len(b)};return b
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
def check():
 assert time.monotonic()-start<890
 v=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',v).group(1));gb=int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1))*page/1e9;assert gb<70;mem.append(gb);return gb
check();attempt=json.loads(pin(E/'attempt.json'));source=B/'source-preserving-garment185/operator/rider.glb';raw=pin(source,attempt['source185SHA256']);op=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py';tree=ast.parse(pin(op));names={'GLB','strict','projected','edges'};exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))and x.name in names],type_ignores=[]),str(op),'exec'),globals());copPath=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment185/coplanar-source/audit.py';tree=ast.parse(pin(copPath));names={'sub','c2','c3','dot','rational_triangle','clip_exact'};exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in names],type_ignores=[]),str(copPath),'exec'),globals());C=GLB(source,attempt['source185SHA256']);a,F=C.primitive(0,0);P=a['POSITION'];originalU,q=np.unique(P,axis=0,return_inverse=True);PF=q[F];dumpPath=S/'construction.npz';dumpBefore=pin(dumpPath);z=np.load(dumpPath);U=z['physicalPositions'];newPF=z['newPhysicalTriangles'];kept=z['sourceKeptFaceIDs'];ribbon=set(z['removedSourceFaceIDs'].tolist());attrs={k:z['attribute_'+k] for k in a};finalF=z['indices'];targets=[]
for ti,target in enumerate(C.d['meshes'][0]['primitives'][0].get('targets',[])):targets.append({k:z['morph_'+str(ti)+'_'+k] for k in target})
pr=json.loads(pin(S/'construction-provenance.json'));cornerProvenance=pr['newCornerProvenance'];chartFailures=pr['chartFailures'];geometryReasons=pr['geometryReasons'];cycles=pr['excisedHoleCycles'];polygons=[x['orderedPhysicalBoundary'] for x in pr['polygons']];movedRows=np.array(pr['movedSourceRows']);scope=set(pr['sourceScopeFaceIDs']);contract=json.loads(pin(B/'source-seam191/next-construction-contract.json'));pin(R/'docs/evidence/hero-remaster/one-rider-v2/source-seam191/freeze.json');pin(R/'docs/evidence/hero-remaster/one-rider-v2/source-seam191/parent-review.json');A,Bnode=1571,13219
sourceEdges=edges(PF);retainedEdges=edges(PF[kept]);cut=[];out=defaultdict(list);ind=Counter()
for e,v in retainedEdges.items():
 if len(v)==1 and len(sourceEdges[e])==2:
  fi=v[0][0];t=PF[kept[fi]]
  for k in range(3):
   i,j=map(int,[t[k],t[(k+1)%3]])
   if tuple(sorted((i,j)))==e:cut.append({'fillDirectedPhysicalEdge':[j,i],'retainedSourceFace':int(kept[fi]),'sourceIncidentFaces':[int(vv[0]) for vv in sourceEdges[e]],'endpointPositionsM':U[[j,i]].tolist()});out[j].append(i);ind[i]+=1;break
invalid=[{'physicalID':i,'positionM':U[i].tolist(),'outDegree':len(out[i]),'inDegree':ind[i],'sourceRowAliases':np.flatnonzero(q==i).tolist(),'incidentCutHalfedges':[e for e in cut if i in e['fillDirectedPhysicalEdge']]} for i in sorted(set(out)|set(ind)) if len(out[i])!=1 or ind[i]!=1];save(S/'literal-boundary-rejection.json',{'cutHalfedges':cut,'invalidDirectedBoundaryNodes':invalid,'fullCutEdgeCount':len(cut),'generatedGeometryDumpSHA256':sha(dumpBefore),'noSecondGeometryGenerated':True});print(json.dumps({'phase':'VERIFY_RETAINED_ACTUAL_DUMP','cutEdges':len(cut),'invalidNodes':[{'id':x['physicalID'],'out':x['outDegree'],'in':x['inDegree']} for x in invalid]}),flush=True)
# Whole exported-style physical topology including original hood/gloves.
parts=[];fullPositions=[];fullF=[];partLabels=[];offset=0;faceOrigin=[];changed=[]
for mi,m in enumerate(C.d['meshes']):
 for pi,p in enumerate(m['primitives']):
  aa,ff=C.primitive(mi,pi)
  if(mi,pi)==(0,0):aa=attrs;ff=finalF
  fullPositions.append(aa['POSITION']);fullF.append(ff.astype(np.int64)+offset);partLabels.extend([(mi,pi)]*len(ff));offset+=len(aa['POSITION'])
  for j in range(len(ff)):
   original=int(kept[j]) if(mi,pi)==(0,0) and j<len(kept) else j if(mi,pi)!=(0,0) else None
   faceOrigin.append({'mesh':mi,'primitive':pi,'sourceFace':original,'newTriangle':j-len(kept) if(mi,pi)==(0,0) and j>=len(kept) else None})
   if(mi,pi)==(0,0) and(j>=len(kept) or 1571 in PF[int(kept[j])]):changed.append(len(faceOrigin)-1)
fullPositions=np.concatenate(fullPositions);fullF=np.concatenate(fullF);_,quotient=np.unique(fullPositions,axis=0,return_inverse=True);globalPF=quotient[fullF];tri=fullPositions[fullF].astype(float)

def topo(pos,fs):
 _,qq=np.unique(pos,axis=0,return_inverse=True);pp=qq[fs];ee=edges(pp);tt=pos[fs].astype(float);area=np.linalg.norm(np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]),axis=1)/2;g=defaultdict(set)
 for x,y in ee:g[x].add(y);g[y].add(x)
 seen=set();components=0
 for root in g:
  if root in seen:continue
  components+=1;stack=[root]
  while stack:
   i=stack.pop()
   if i in seen:continue
   seen.add(i);stack.extend(g[i]-seen)
 coords=np.unique(pos,axis=0);boundary=[tuple(sorted((tuple(coords[a]),tuple(coords[b])))) for(a,b),own in ee.items() if len(own)==1]
 return {'faces':len(fs),'physicalVertices':len(g),'edges':len(ee),'components':components,'degenerateFaces':np.flatnonzero(area<=1e-12).tolist(),'nonmanifoldEdges':[list(e) for e,v in ee.items() if len(v)>2],'windingEdges':[list(e) for e,v in ee.items() if len(v)==2 and v[0][1]==v[1][1]],'duplicateFaceCount':len(pp)-len({tuple(sorted(t)) for t in pp}),'boundaryEdgesPositionKeys':sorted(boundary),'minimumAreaM2':float(area.min())}
sourcePs=[];sourceFs=[];offset=0
for mi,m in enumerate(C.d['meshes']):
 for pi,p in enumerate(m['primitives']):
  aa,ff=C.primitive(mi,pi);sourcePs.append(aa['POSITION']);sourceFs.append(ff.astype(np.int64)+offset);offset+=len(aa['POSITION'])
sourcePs=np.concatenate(sourcePs);sourceFs=np.concatenate(sourceFs);sourceTopology=topo(sourcePs,sourceFs);candidateTopology=topo(fullPositions,fullF);topologyReasons=[]
for key in ['degenerateFaces','nonmanifoldEdges','windingEdges','duplicateFaceCount']:
 if candidateTopology[key]:topologyReasons.append('Candidate whole topology failure '+key)
if candidateTopology['components']!=sourceTopology['components']:topologyReasons.append('Changed whole physical component count')
if candidateTopology['boundaryEdgesPositionKeys']!=sourceTopology['boundaryEdgesPositionKeys']:topologyReasons.append('Changed actual whole hood/cuff/openboundary positions')
# Synthetic fixtures exercise strict crossing and exact/near coplanar projected classes.
fa=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
fixtures=[('strict_cross',np.array([[.25,.25,-1.],[.25,.25,1.],[.75,.25,0.]]),True,False),('coplanar_overlap',np.array([[.1,.1,0.],[.4,.1,0.],[.1,.4,0.]]),False,True),('legal_shared_edge',np.array([[0.,0.,0.],[1.,0.,0.],[0.,-1.,0.]]),False,False),('legal_one_corner',np.array([[0.,0.,0.],[-1.,0.,0.],[0.,-1.,0.]]),False,False)]
fixtureResults=[]
for name,fb,expectedStrict,expectedOverlap in fixtures:
 ss=bool(strict(fa[None],fb[None])[0]);cl=projected(fa,fb);ok=ss==expectedStrict and cl['positiveOverlap']==expectedOverlap;fixtureResults.append({'name':name,'pass':ok,'strict':ss,**cl})
assert all(f['pass'] for f in fixtureResults)
# Complete changed-local versus whole AABB broadphase with all shared classes.
cent=tri.mean(1);rad=np.linalg.norm(tri-cent[:,None],axis=2).max(1);lo=tri.min(1);hi=tri.max(1);tree=cKDTree(cent);rmax=float(rad.max());pairSet=set()
for begin in range(0,len(changed),128):
 ids=np.array(changed[begin:begin+128]);ns=tree.query_ball_point(cent[ids],rad[ids]+rmax+1e-12,workers=2)
 for i,cands in zip(ids,ns):
  js=np.array([j for j in cands if j!=i],dtype=int);js=js[(hi[i]>=lo[js]-1e-12).all(1)&(lo[i]<=hi[js]+1e-12).all(1)]
  for j in js:pairSet.add(tuple(sorted((int(i),int(j)))))
 check()
pairList=sorted(pairSet);crossings=[];coplanar=[];categoryCounts=Counter();predicateNearDegenerate=[]
for begin in range(0,len(pairList),8192):
 batch=pairList[begin:begin+8192];ia=np.array([a for a,b in batch]);ib=np.array([b for a,b in batch]);hit=strict(tri[ia],tri[ib]);na=np.cross(tri[ia,1]-tri[ia,0],tri[ia,2]-tri[ia,0]);nb=np.cross(tri[ib,1]-tri[ib,0],tri[ib,2]-tri[ib,0]);la=np.linalg.norm(na,axis=1);lb=np.linalg.norm(nb,axis=1);validN=(la>1e-12)&(lb>1e-12);ua=na/np.where(la>0,la,1)[:,None];ub=nb/np.where(lb>0,lb,1)[:,None];near=validN&(np.linalg.norm(np.cross(ua,ub),axis=1)<1e-8)&(abs(np.einsum('ij,ij->i',tri[ib,0]-tri[ia,0],ua))<1e-8)
 for k,(i,j) in enumerate(batch):
  shared=len(set(globalPF[i])&set(globalPF[j]));categoryCounts[str(shared)]+=1
  if not validN[k]:predicateNearDegenerate.append([i,j]);continue
  if hit[k]:crossings.append({'globalFaces':[i,j],'physicalSharedCorners':shared,'ancestry':[faceOrigin[i],faceOrigin[j]],'trianglesM':tri[[i,j]].tolist()})
  if near[k]:
   cl=projected(tri[i],tri[j]);coplanar.append({'globalFaces':[i,j],'physicalSharedCorners':shared,'ancestry':[faceOrigin[i],faceOrigin[j]],**cl})
 check()
# Literal left sublevel attachment on generated p0 graph; source roots frozen at1.13.
import heapq
bodyQ=np.concatenate([q,np.array([x['physicalSourceID'] for x in cornerProvenance],dtype=int)]);finalPF=bodyQ[finalF];gg=defaultdict(set)
for t in finalPF:
 for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);gg[i].add(j);gg[j].add(i)
sec=json.loads(pin(B/'source-axilla189/section-fixed-03.json'));roots={}
for loop in sec['loops']:
 if loop['geometricClass'] in ['central_Z0_straddling','positiveZ_lateral']:roots[loop['geometricClass']]={i for seg in loop['segments'] for ep in seg['endpoints'] for i in ep.get('sourcePhysicalEdge',[]) if originalU[i,1]<1.13}
distance={i:float(U[i,1]) for i in roots['central_Z0_straddling']};prev={};heap=[(v,i) for i,v in distance.items()];heapq.heapify(heap)
while heap:
 height,i=heapq.heappop(heap)
 if height!=distance[i]:continue
 for j in sorted(gg[i]):
  nh=max(height,float(U[j,1]))
  if nh<distance.get(j,float('inf')):distance[j]=nh;prev[j]=i;heapq.heappush(heap,(nh,j))
target=min(roots['positiveZ_lateral'],key=lambda i:(distance.get(i,float('inf')),i));attachmentY=distance.get(target,float('inf'));path=[target]
while path[-1] in prev:path.append(prev[path[-1]])
sectionResults=[]
for y in [.94,1.00,1.08,1.13,1.18,1.25,1.299,1.30,1.31,1.32]:
 graph=defaultdict(set);touch=0;cop=0
 for t in finalPF[(U[finalPF][:,:,1].min(1)<=y)&(U[finalPF][:,:,1].max(1)>=y)]:
  hits=set()
  for k in range(3):
   i,j=map(int,[t[k],t[(k+1)%3]]);yi,yj=U[i,1],U[j,1]
   if yi==y and yj==y:cop+=1;hits.add(('v',i));hits.add(('v',j))
   elif yi==y:hits.add(('v',i))
   elif yj==y:hits.add(('v',j))
   elif min(yi,yj)<y<max(yi,yj):hits.add(('e',*sorted((i,j))))
  if len(hits)==2:
   i,j=hits;graph[i].add(j);graph[j].add(i)
  elif len(hits)==1:touch+=1
 components=[];seen=set()
 for root in graph:
  if root in seen:continue
  stack=[root];nodes=set()
  while stack:
   i=stack.pop()
   if i in nodes:continue
   nodes.add(i);seen.add(i);stack.extend(graph[i]-nodes)
  components.append({'nodes':len(nodes),'closed':all(len(graph[i])==2 for i in nodes)})
 sectionResults.append({'Y_M':y,'contours':components,'pointTouches':touch,'coplanarEdges':cop})
# Conservation and finite/morph/accessor legality on the constructed arrays.
protectedRows=sorted({int(row) for fi in range(len(F)) if fi not in scope for row in F[fi]});conservation={k:bool(np.array_equal(a[k][protectedRows],attrs[k][protectedRows])) for k in a};conservation['outsideSourceFacesIndicesExact']=all(np.array_equal(F[fi],finalF[np.searchsorted(kept,fi)]) for fi in range(len(F)) if fi not in scope);conservation['sourceRigJSONUnchanged']=True;finite=all(np.isfinite(v).all() for v in attrs.values()) and all(np.isfinite(v).all() for t in targets for v in t.values());countsLegal=all(len(v)==len(attrs['POSITION']) for v in attrs.values()) and all(len(v)==len(attrs['POSITION']) for t in targets for v in t.values());positiveCop=[x for x in coplanar if x['positiveOverlap']];reasons=geometryReasons+topologyReasons
if chartFailures:reasons.append('New triangles cannot use one continuous source UV chart')
if crossings:reasons.append('Strict changed-local versus whole triangle crossings')
if positiveCop:reasons.append('Positive exact/near coplanar surface overlaps')
if not(1.30<=attachmentY<=1.32):reasons.append('Literal left attachment outside target1.30--1.32')
if not all(conservation.values()):reasons.append('Protected source arrays changed')
if not finite or not countsLegal:reasons.append('Illegal nonfinite/count/morph arrays')
save(S/'rest-crossing-evidence.json',{'candidatePairCount':len(pairList),'sharedCornerCategoryCounts':dict(categoryCounts),'strictCrossings':crossings,'allNearCoplanarClassifications':coplanar,'degeneratePredicatePairs':predicateNearDegenerate,'fixtures':fixtureResults,'predicatePins':{str(op):pins[str(op)],str(copPath):pins[str(copPath)]}})
# GLB export is deliberately gated by every construction check.
exported=False
if not reasons:
 d=copy.deepcopy(C.d);pp=d['meshes'][0]['primitives'][0];binchunk=bytearray(C.bin)
 def append(arr,oldAccessor,target=None,componentType=None):
  old=copy.deepcopy(d['accessors'][oldAccessor]);old['componentType']=componentType or old['componentType'];dtype={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[old['componentType']];arr=np.asarray(arr,dtype=dtype);binchunk.extend(b'\0'*((-len(binchunk))%4));offset=len(binchunk);buf=arr.tobytes();binchunk.extend(buf);vi=len(d['bufferViews']);view={'buffer':0,'byteOffset':offset,'byteLength':len(buf)}
  if target:view['target']=target
  d['bufferViews'].append(view);old.pop('sparse',None);old['bufferView']=vi;old['byteOffset']=0;old['count']=len(arr);old['min']=arr.min(0).tolist();old['max']=arr.max(0).tolist();ai=len(d['accessors']);d['accessors'].append(old);return ai
 for k,v in attrs.items():pp['attributes'][k]=append(v,pp['attributes'][k],34962)
 pp['indices']=append(finalF.astype('<u4').reshape(-1,1),pp['indices'],34963,5125);d['accessors'][pp['indices']]['componentType']=5125
 for ti,t in enumerate(targets):
  for k,v in t.items():pp['targets'][ti][k]=append(v,pp['targets'][ti][k],34962)
 d['buffers'][0]['byteLength']=len(binchunk);binchunk.extend(b'\0'*((-len(binchunk))%4));js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);out=struct.pack('<III',0x46546c67,2,28+len(js)+len(binchunk))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binchunk),0x004e4942)+binchunk;(S/'rider.glb').write_bytes(out);exported=True
assert source.read_bytes()==raw
assert dumpPath.read_bytes()==dumpBefore
report={'status':'FROZEN_CONSTRUCTION_REJECTED_BEFORE_MOTION' if reasons else'FROZEN_STATIC_PREFLIGHT_CLEAR_PENDING_PARENT','attemptCount':1,'sourceSHA256':sha(raw),'recipeSHA256':sha(Path(__file__).read_bytes()),'inputs':pins,'operator':'One source-panel hole split by high chord1571--13219 and separate deterministic ear reseals','generatedActualGeometry':True,'removedSourceFaces':69,'newFaceCount':len(newPF),'newCornerRows':len(cornerProvenance),'movedPhysicalID':1571,'maximumDisplacementM':float(np.linalg.norm(U[1571]-originalU[1571])),'excisedBoundaryCycleLengths':[len(c) for c in cycles],'polygonBoundaryLengths':[len(c) for c in polygons],'sourceTopology':sourceTopology,'candidateTopology':candidateTopology,'protectedSourceConservation':conservation,'finite':bool(finite),'attributeAndMorphCountsLegal':bool(countsLegal),'singleChartFailedTriangles':len(chartFailures),'crossingPairCount':len(pairList),'crossingCategoryCounts':dict(categoryCounts),'strictCrossings':len(crossings),'positiveCoplanarOverlaps':len(positiveCop),'predicateFixtures':fixtureResults,'leftFirstAttachmentY_M':attachmentY if np.isfinite(attachmentY) else None,'leftMinimaxPathPhysicalIDs':path[::-1],'sections':sectionResults,'rejectionReasons':reasons,'GLBExported':exported,'seconds':time.monotonic()-start,'anonymousGBSamples':mem,'limits':['Clinical local construction only, no art/PBR/motion pass.','Originalbelow-scope weight witness2030/2172/hips unchanged; stage2 required.','Projected coplanar overlap is classified using pinned exact dyadic rational source185 predicate, not threshold retuning.','All unchanged face pairs preserved through exactsource arrays; complete changed-local versus whole broadphase checked.']};save(E/'report.json',report);attempt.update(status=report['status'],geometryGenerated=True,GLBExported=exported,attemptCount=1,rejectionReasons=reasons);save(E/'attempt.json',attempt);print(json.dumps({k:report[k] for k in ['status','attemptCount','newFaceCount','newCornerRows','singleChartFailedTriangles','strictCrossings','positiveCoplanarOverlaps','leftFirstAttachmentY_M','rejectionReasons','seconds','GLBExported']}),flush=True)
