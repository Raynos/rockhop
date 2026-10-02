"""Static review of the frozen194 dump only. No geometry generation or retune."""
from common import *
import heapq
C,a,F,U,q,c,charts,comparison,sep,refs=source();dumpPath=S/'construction.npz';dumpRaw=pin(dumpPath);z=np.load(dumpPath);pr=json.loads(pin(S/'construction-provenance.json'));kept=z['sourceKeptFaceIDs'];attrs={s:z['attribute_'+s] for s in a};indices=z['indices'];newPF=z['newPhysicalTriangles'];pU=z['physicalPositions'];rowPID=z['attributeRowPhysicalIDs'];PF=q[F];morphs=[{s:z['morph_'+str(i)+'_'+s] for s in t} for i,t in enumerate(C.d['meshes'][0]['primitives'][0].get('targets',[]))];reasons=[];failures={}
assert sha(dumpRaw)==json.loads((E/'attempt.json').read_text())['dumpSHA256']
# Original buffers, rows, indices, all five primitive assemblies remain literal.
conservation={s:bool(np.array_equal(v,attrs[s][:len(v)])) for s,v in a.items()}
for i,t in enumerate(C.d['meshes'][0]['primitives'][0].get('targets',[])):
 for s,ai in t.items():conservation['morph_'+str(i)+'_'+s]=bool(np.array_equal(C.acc(ai),morphs[i][s][:len(a['POSITION'])]))
conservation['removedExact47']=bool(np.array_equal(z['removedSourceFaceIDs'],c['exactRemovedSourceFaceIDs']));conservation['retainedOriginalIndices']=bool(np.array_equal(indices[:len(kept)],F[kept]));conservation['retainedFaceIDs']=bool(np.array_equal(kept,[i for i in range(len(F)) if i not in c['exactRemovedSourceFaceIDs']]))
finite=all(np.isfinite(v).all() for v in attrs.values()) and all(np.isfinite(v).all() for t in morphs for v in t.values());counts=all(len(v)==len(attrs['POSITION']) for v in attrs.values()) and all(len(v)==len(attrs['POSITION']) for t in morphs for v in t.values());legalIndices=bool(indices.min()>=0 and indices.max()<len(attrs['POSITION']));legalSkin=bool(np.all(attrs['JOINTS_0']<19) and np.all(attrs['WEIGHTS_0']>=0));newWeights=attrs['WEIGHTS_0'][len(a['POSITION']):];skinSums=np.sum(abs(newWeights),axis=1,dtype=np.float32);legalSkin=legalSkin and bool(np.max(abs(skinSums-1))<=2e-7)
# Full Float32 geometry physical quotient decides topology, regardless parameter aliases.
def assemble(candidate):
 ps=[];fs=[];origins=[];offset=0;changed=[]
 for mi,m in enumerate(C.d['meshes']):
  for pi,p in enumerate(m['primitives']):
   aa,ff=C.primitive(mi,pi)
   if candidate and (mi,pi)==(0,0):aa=attrs;ff=indices
   ps.append(aa['POSITION']);fs.append(ff.astype(np.int64)+offset);offset+=len(aa['POSITION'])
   for j in range(len(ff)):
    isNew=candidate and (mi,pi)==(0,0) and j>=len(kept);origins.append({'mesh':mi,'primitive':pi,'sourceFace':int(kept[j]) if candidate and (mi,pi)==(0,0) and not isNew else j if not isNew else None,'newTriangle':j-len(kept) if isNew else None})
    if isNew:changed.append(len(origins)-1)
 return np.concatenate(ps),np.concatenate(fs),origins,changed

def topology(pos,fs):
 uq,qq=np.unique(pos,axis=0,return_inverse=True);pf=qq[fs];ee=edges(pf);tt=pos[fs].astype(float);ar=np.linalg.norm(np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]),axis=1)/2;edgeGraph=defaultdict(set);incident=defaultdict(set);link=defaultdict(lambda:defaultdict(set))
 for fi,t in enumerate(pf):
  for v in t:incident[int(v)].add(fi)
 for (i,j),owners in ee.items():
  edgeGraph[i].add(j);edgeGraph[j].add(i)
  if len(owners)==2:
   x,y=owners[0][0],owners[1][0]
   for v in (i,j):link[v][x].add(y);link[v][y].add(x)
 seen=set();components=[]
 for v in edgeGraph:
  if v in seen:continue
  stack=[v];nodes=set()
  while stack:
   i=stack.pop()
   if i in nodes:continue
   nodes.add(i);stack.extend(edgeGraph[i]-nodes)
  seen|=nodes;components.append(len(nodes))
 pinches=[]
 for v,faces in incident.items():
  remaining=set(faces);cc=[]
  while remaining:
   root=min(remaining);stack=[root];seen=set()
   while stack:
    i=stack.pop()
    if i in seen:continue
    seen.add(i);stack.extend(link[v][i]-seen)
   remaining-=seen;cc.append(sorted(seen))
  if len(cc)>1:pinches.append({'physicalID':v,'positionM':uq[v].tolist(),'faceLinkComponents':cc})
 boundary=sorted(tuple(sorted((tuple(uq[i]),tuple(uq[j])))) for(i,j),vv in ee.items() if len(vv)==1);dups=defaultdict(list)
 for fi,t in enumerate(pf):dups[tuple(sorted(map(int,t)))].append(fi)
 return {'components':sorted(components),'zeroSliverFaces':np.flatnonzero(ar<=1e-12).tolist(),'minimumAreaM2':float(ar.min()),'nonmanifoldEdges':[list(k) for k,v in ee.items() if len(v)>2],'windingEdges':[list(k) for k,v in ee.items() if len(v)==2 and v[0][1]==v[1][1]],'duplicatePhysicalFaces':[v for v in dups.values() if len(v)>1],'vertexLinkPinches':pinches,'boundaryPositionKeys':boundary,'boundaryEdgeCount':len(boundary)},pf
sourcePs,sourceFs,_,_=assemble(False);pos,fs,origins,changed=assemble(True);srcTopo,_=topology(sourcePs,sourceFs);topo,globalPF=topology(pos,fs);boundaryExact=srcTopo['boundaryPositionKeys']==topo['boundaryPositionKeys'];componentsExact=len(srcTopo['components'])==len(topo['components']);save(S/'topology.json',{'source':srcTopo,'candidate':topo,'boundaryExact':boundaryExact,'componentCountExact':componentsExact})
for key in ['zeroSliverFaces','nonmanifoldEdges','windingEdges','duplicatePhysicalFaces','vertexLinkPinches']:
 if topo[key]:reasons.append('Float32 whole topology: '+key)
if not boundaryExact:reasons.append('Original global openboundary changed')
if not componentsExact:reasons.append('Original whole component count changed')
floatPhysical=defaultdict(list)
for pid in sorted(set(newPF.ravel().tolist())):floatPhysical[tuple(pU[pid])].append(pid)
physicalCollisions=[ids for ids in floatPhysical.values() if len(ids)>1]
if physicalCollisions:reasons.append('Distinct exact parameter physicalIDs collapse in Float32')
# Named source triangle/chart provenance and canonical alias field checks.
fieldFailures=[];normalFailures=[];chartFailures=[];rowsByPID=defaultdict(list)
for co in pr['newCornerProvenance']:
 row=co['newAccessorRow'];pid=co['physicalID'];rowsByPID[pid].append(row);fi=co['sourceFace'];w=np.array(co['barycentric']);src=F[fi]
 if charts.get(fi)!=co['sourceChart'] or min(w)<-1e-12 or abs(w.sum()-1)>1e-12:chartFailures.append(row)
 for semantic in a:
  if semantic not in ['POSITION','NORMAL','JOINTS_0','WEIGHTS_0']:
   expect=(w@a[semantic][src].astype(float)).astype(a[semantic].dtype)
   if not np.array_equal(expect,attrs[semantic][row]):fieldFailures.append({'row':row,'semantic':semantic})
 if co['normalSource']:
  sr=co['normalSource']['sourceRow']
  if not np.array_equal(attrs['NORMAL'][row],a['NORMAL'][sr]):normalFailures.append(row)
 elif pid in set(c['fixedOrientedBoundaryPhysicalIDs']):normalFailures.append(row)
for fi,fr in enumerate(pr['fragments']):
 if any(co['sourceFace']!=fr['sourceFace'] or co['sourceChart']!=fr['sourceChart'] for co in pr['newCornerProvenance'][3*fi:3*fi+3]):chartFailures.append(fr['physicalCorners'])
for pid,rows in rowsByPID.items():
 for semantic in ['JOINTS_0','WEIGHTS_0']:
  if not np.all(attrs[semantic][rows]==attrs[semantic][rows[0]]):fieldFailures.append({'physicalID':pid,'semantic':semantic,'aliasMismatch':True})
 for mi,t in enumerate(morphs):
  for semantic,v in t.items():
   if not np.all(v[rows]==v[rows[0]]):fieldFailures.append({'physicalID':pid,'semantic':'morph_'+str(mi)+'_'+semantic,'aliasMismatch':True})
 if pid not in set(c['fixedOrientedBoundaryPhysicalIDs']) and not np.all(attrs['NORMAL'][rows]==attrs['NORMAL'][rows[0]]):normalFailures.append(pid)
# Independently recompute canonical lowest-face, dense19 reduction and morph fields.
canonicalChecks=[]
for rec in pr['canonicalPhysicalFields']:
 pid=rec['physicalID'];pp=tuple(Q(int(n),int(d)) for n,d in pr['physicalReferenceParameters'][str(pid)]);choices=[(fi,bary(pp,t)) for fi,t in sorted(refs.items()) if min(bary(pp,t))>=0];fi,bw=choices[0];w=np.array([float(v) for v in bw]);src=F[fi];dense=np.zeros(19,float)
 for lane in range(3):
  for joint,weight in zip(a['JOINTS_0'][src[lane]],a['WEIGHTS_0'][src[lane]]):dense[int(joint)]+=w[lane]*float(weight)
 lanes=sorted([j for j in range(19) if dense[j]>0],key=lambda j:(-dense[j],j))[:4];jj=np.zeros(4,a['JOINTS_0'].dtype);ww=np.zeros(4,np.float32);jj[:len(lanes)]=lanes;ww[:len(lanes)]=dense[lanes].astype(np.float32);ww=(ww/np.sum(abs(ww),dtype=np.float32)).astype(np.float32);discarded=float(sum(dense[j] for j in range(19) if j not in lanes));ok=(rec['sourceFace']==fi and np.array_equal(rec['barycentric'],w) and np.array_equal(rec['dense19'],dense) and rec['discardedPositiveMass']==discarded)
 for row in rowsByPID[pid]:
  ok=ok and np.array_equal(attrs['JOINTS_0'][row],jj) and np.array_equal(attrs['WEIGHTS_0'][row],ww)
  local=row-len(a['POSITION']);ok=ok and np.array_equal(z['newDense19Weights'][local],dense) and z['newDiscardedWeightMass'][local]==discarded
  for mi,target in enumerate(C.d['meshes'][0]['primitives'][0].get('targets',[])):
   for sem,ai in target.items():
    v=C.acc(ai);expected=(w@v[src].astype(float)).astype(v.dtype);ok=ok and np.array_equal(morphs[mi][sem][row],expected)
 if not ok:fieldFailures.append({'physicalID':pid,'canonicalDense19MorphReduction':False})
 canonicalChecks.append(ok)
from scipy.spatial import ConvexHull
hull=ConvexHull(U[sorted(set(PF[z['removedSourceFaceIDs']].ravel().tolist()))].astype(float));capPoints=pU[sorted(set(newPF.ravel().tolist()))].astype(float);maxHullResidual=float((np.sum(capPoints[:,None,:]*hull.equations[None,:,:3],axis=2)+hull.equations[None,:,3]).max());insideHull=maxHullResidual<=2e-7
if not insideHull:reasons.append('Candidate cap exceeds original47 convex hull')
normalLengths=np.linalg.norm(attrs['NORMAL'][len(a['POSITION']):].astype(float),axis=1)
if np.any(normalLengths<1e-8):normalFailures.append('zero normal')
maxDisp=max(x['candidateDisplacementM'] for x in pr['canonicalPhysicalFields']);limit=c['parentBoundaryDisplacementClarification']['maximumNewCornerCorrespondenceDistanceM']+2e-7
if maxDisp>limit:reasons.append('New barycentric correspondence displacement outside source diameter')
if fieldFailures or chartFailures or normalFailures:reasons.append('Source field/chart/normal provenance failure')
# Crossing fixture classes include shared0/1/2, no exemption for adjacency.
fa=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
fixtures=[('strict_cross',np.array([[.25,.25,-1.],[.25,.25,1.],[.75,.25,0.]]),True,False),('coplanar_overlap',np.array([[.1,.1,0.],[.4,.1,0.],[.1,.4,0.]]),False,True),('legal_shared_edge',np.array([[0.,0.,0.],[1.,0.,0.],[0.,-1.,0.]]),False,False),('legal_shared_corner',np.array([[0.,0.,0.],[-1.,0.,0.],[0.,-1.,0.]]),False,False),('illegal_shared_edge_overlap',np.array([[0.,0.,0.],[1.,0.,0.],[.2,.2,0.]]),False,True)]
fixtureResults=[]
for name,fb,es,ep in fixtures:
 ss=bool(strict(fa[None],fb[None])[0]);cl=projected(fa,fb);fixtureResults.append({'name':name,'pass':ss==es and cl['positiveOverlap']==ep,'strict':ss,**cl})
assert all(f['pass'] for f in fixtureResults)
tri=pos[fs].astype(float);cent=tri.mean(1);rad=np.linalg.norm(tri-cent[:,None],axis=2).max(1);lo=tri.min(1);hi=tri.max(1);tree=cKDTree(cent);rmax=float(rad.max());pairs=set()
for begin in range(0,len(changed),128):
 ids=np.array(changed[begin:begin+128]);neighbors=tree.query_ball_point(cent[ids],rad[ids]+rmax+1e-12,workers=2)
 for i,ns in zip(ids,neighbors):
  js=np.array([j for j in ns if j!=i],int);js=js[(hi[i]>=lo[js]-1e-12).all(1)&(lo[i]<=hi[js]+1e-12).all(1)]
  for j in js:pairs.add(tuple(sorted((int(i),int(j)))))
 check()
pairs=sorted(pairs);strictHits=[];coplanar=[];categories=Counter();badPredicate=[]
for begin in range(0,len(pairs),4096):
 batch=pairs[begin:begin+4096];ia=np.array([i for i,j in batch]);ib=np.array([j for i,j in batch]);hit=strict(tri[ia],tri[ib]);na=np.cross(tri[ia,1]-tri[ia,0],tri[ia,2]-tri[ia,0]);nb=np.cross(tri[ib,1]-tri[ib,0],tri[ib,2]-tri[ib,0]);la=np.linalg.norm(na,axis=1);lb=np.linalg.norm(nb,axis=1);valid=(la>1e-12)&(lb>1e-12);ua=na/np.where(la>0,la,1)[:,None];ub=nb/np.where(lb>0,lb,1)[:,None];near=valid&(np.linalg.norm(np.cross(ua,ub),axis=1)<1e-8)&(abs(np.einsum('ij,ij->i',tri[ib,0]-tri[ia,0],ua))<1e-8)
 for k,(i,j) in enumerate(batch):
  shared=len(set(globalPF[i])&set(globalPF[j]));categories[str(shared)]+=1
  if not valid[k]:badPredicate.append([i,j])
  if hit[k]:strictHits.append({'globalFaces':[i,j],'physicalSharedCorners':shared,'ancestry':[origins[i],origins[j]],'trianglesM':tri[[i,j]].tolist()})
  if near[k]:coplanar.append({'globalFaces':[i,j],'physicalSharedCorners':shared,'ancestry':[origins[i],origins[j]],**projected(tri[i],tri[j])})
 check()
positiveCop=[x for x in coplanar if x['positiveOverlap']];save(S/'rest-crossing-evidence.json',{'candidatePairCount':len(pairs),'changedLocalFaces':len(changed),'againstAll5Primitives':True,'sharedCornerCategoryCounts':dict(categories),'strictCrossings':strictHits,'nearCoplanarClassifications':coplanar,'degeneratePredicatePairs':badPredicate,'fixtures':fixtureResults,'predicatePins':pins})
if strictHits:reasons.append('New/changed versus all5 strict crossings')
if positiveCop:reasons.append('New/changed positive exact/near coplanar overlap')
# Whole remaining original p0 plus cap minimax paths, rooted by frozen literal labels.
g=defaultdict(set)
for t in rowPID[indices]:
 for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);g[i].add(j);g[j].add(i)
roots=sep['roots'];central=roots['central_Z0_straddling'];lateral=roots['positiveZ_lateral'];d={int(i):float(pU[i,1]) for i in central};previous={};heap=[(v,i) for i,v in d.items()];heapq.heapify(heap)
while heap:
 h,i=heapq.heappop(heap)
 if h!=d[i]:continue
 for j in sorted(g[i]):
  nh=max(h,float(pU[j,1]))
  if nh<d.get(j,float('inf')):d[j]=nh;previous[j]=i;heapq.heappush(heap,(nh,j))
target=min(lateral,key=lambda i:(d.get(i,float('inf')),i));attachment=d.get(target,float('inf'));path=[target]
while path[-1] in previous:path.append(previous[path[-1]])
separated=not any(d.get(i,float('inf'))<1.30 for i in lateral)
if not separated or not(1.30<=attachment<=1.32):reasons.append('Rooted low routes or high attachment failed')
# Literal crosssection segments retain geometry; no closed-volume claim.
sections=[]
for y in [1.13,1.18,1.25,1.299,1.30,1.31,1.32]:
 segs=[]
 for j,t in enumerate(pU[rowPID[indices]].astype(float)):
  if t[:,1].min()>y or t[:,1].max()<y:continue
  hits=[]
  for k in range(3):
   aa,bb=t[k],t[(k+1)%3]
   if (aa[1]<y<bb[1]) or(bb[1]<y<aa[1]):hits.append(aa+(y-aa[1])/(bb[1]-aa[1])*(bb-aa))
   elif aa[1]==y:hits.append(aa)
  if len(hits)==2:segs.append({'p0Triangle':j,'newCap':j>=len(kept),'endpointsM':np.array(hits).tolist()})
 sections.append({'heightY_M':y,'segments':segs})
save(S/'crosssections.json',{'sourceIsOpenAtHoodCuffs':True,'closedVolumeClaim':False,'sections':sections,'channelMetric':'Rooted graph connectivity and literal horizontal section segments; no material thickness or closedvolume pass'})
if pr['constructionFailures']:reasons.append('Exact parameter/world construction failures')
if not all(conservation.values()):reasons.append('Original source conservation failed')
if not finite or not counts or not legalIndices or not legalSkin:reasons.append('Float32 accessor/morph/skin legality failed')
report={'status':'STATIC_CLEAR_UNACCEPTED_PENDING_PARENT' if not reasons else 'FROZEN_STATIC_REJECTION_NO_GLB','attemptCount':1,'geometryGenerated':True,'GLBExported':False,'accepted':False,'source185SHA256':SHA,'dumpSHA256':sha(dumpRaw),'sourceRemovedFaces':47,'newTriangles':len(newPF),'newAccessorRows':len(attrs['POSITION'])-len(a['POSITION']),'originalPositionsMoved':0,'conservation':conservation,'finite':finite,'countsLegal':counts,'indicesLegal':legalIndices,'skinLegal':legalSkin,'sourceTopology':{k:v for k,v in srcTopo.items() if k not in ['boundaryPositionKeys','vertexLinkPinches']},'candidateTopology':{k:v for k,v in topo.items() if k not in ['boundaryPositionKeys','vertexLinkPinches']},'vertexLinkPinches':len(topo['vertexLinkPinches']),'boundaryExact':boundaryExact,'physicalFloat32Collisions':len(physicalCollisions),'sourceFieldFailures':len(fieldFailures),'chartFailures':len(chartFailures),'normalFailures':len(normalFailures),'strictCrossings':len(strictHits),'positiveCoplanarOverlaps':len(positiveCop),'broadphasePairs':len(pairs),'sharedClasses':dict(categories),'rootedLowRoutesSeparated':separated,'firstAttachmentY_M':attachment,'minimaxPathPhysicalIDs':path[::-1],'canonicalDense19MorphChecks':all(canonicalChecks),'candidateInsideOriginal47ConvexHull':insideHull,'maximumConvexHullResidualM':maxHullResidual,'maximumNewCornerBarycentricDisplacementM':maxDisp,'newCornerLimitM':limit,'discardedWeightMass':{'everyNewCornerReported':True,'count':len(z['newDiscardedWeightMass']),'max':float(z['newDiscardedWeightMass'].max()),'sum':float(z['newDiscardedWeightMass'].sum())},'rejectionReasons':reasons,'elapsedSeconds':time.monotonic()-start,'anonymousGBSamples':mem,'inputs':pins,'limits':['Static unaccepted construction only; no moving art or rig gate','Original broad reach/overhead/sit failures not cleared','Original19 joints preserved; explicit170 adapter remains parent work']}
# Check frozen inputs before intentional attempt/report status updates.
for p,v in pins.items():assert sha(Path(p).read_bytes())==v['sha256']
save(S/'field-failures.json',{'fieldFailures':fieldFailures,'chartFailures':chartFailures,'normalFailures':normalFailures,'physicalFloat32Collisions':physicalCollisions});save(E/'report.json',report)
attempt=json.loads((E/'attempt.json').read_text());attempt.update(status=report['status'],staticRejected=bool(reasons),rejectionReasons=reasons);save(E/'attempt.json',attempt)
# The sole geometry dump remains byte identical after verification.
assert sha(dumpPath.read_bytes())==sha(dumpRaw)
print(json.dumps({k:report[k] for k in ['status','attemptCount','newTriangles','newAccessorRows','strictCrossings','positiveCoplanarOverlaps','vertexLinkPinches','physicalFloat32Collisions','firstAttachmentY_M','rejectionReasons','elapsedSeconds']}),flush=True)
