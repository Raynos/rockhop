"""Static gates on the single frozen actual196 dump; no geometry tuning."""
from common import *
import heapq
C,a,F,U,q,c,alias,graph,star,path,sep=source();dumpPath=S/'construction.npz';pin(dumpPath);z=np.load(dumpPath);pr=json.loads(pin(S/'construction-provenance.json'));attrs={s:z['attribute_'+s] for s in a};indices=z['indices'];rows=z['clonedSourceRows'];newRows=z['clonedNewRows'];changed=z['changedSourceFaceIDs'];physical=z['physicalPositions'];rowPID=z['attributeRowPhysicalIDs'];interior=c['exactReleasedInteriorPhysicalIDs'];boundary=star['orientedFillBoundaryPhysicalIDs'];changedSet=set(map(int,changed));reasons=[]
same=lambda x,y:x.shape==y.shape and x.dtype==y.dtype and x.tobytes()==y.tobytes()
conservation={s:same(v,attrs[s][:len(v)]) for s,v in a.items()};morphs=[]
for i,target in enumerate(C.d['meshes'][0]['primitives'][0].get('targets',[])):
 morphs.append({s:z['morph_'+str(i)+'_'+s] for s in target})
 for s,ai in target.items():conservation['morph_'+str(i)+'_'+s]=same(C.acc(ai),morphs[i][s][:len(a['POSITION'])])
outside=np.array([i for i in range(len(F)) if i not in changedSet]);conservation['outsideFaceIndicesExact']=np.array_equal(indices[outside],F[outside]);conservation['originalFaceOrderAndCount']=indices.shape==F.shape;conservation['exact168FaceMask']=np.array_equal(changed,star['removedSourceFaceIDs']);conservation['exactSourcePhysicalPositions']=same(U,z['sourcePhysicalPositions']);conservation['boundaryXYZExact']=same(U[boundary],physical[boundary]);conservation['outsidePhysicalXYZExact']=same(U[~np.isin(np.arange(len(U)),interior)],physical[~np.isin(np.arange(len(U)),interior)])
expectedRows=np.flatnonzero(np.isin(q,interior));conservation['oneCloneEachInteriorSourceRow']=np.array_equal(rows,expectedRows) and np.array_equal(newRows,np.arange(len(a['POSITION']),len(a['POSITION'])+len(rows)));conservation['rowPhysicalMappingExact']=np.array_equal(rowPID,np.concatenate([q,q[rows]]));cloneMap=dict(zip(map(int,rows),map(int,newRows)));expected=F.astype(np.int64).copy()
for fi in changed:
 for lane,row in enumerate(F[fi]):
  if int(row) in cloneMap:expected[fi,lane]=cloneMap[int(row)]
conservation['onlyInteriorCornersRemapped']=np.array_equal(expected,indices);conservation['physicalIncidenceExact']=np.array_equal(rowPID[indices],q[F]);fieldFailures=[]
for s,v in a.items():
 if s not in ['POSITION','NORMAL'] and not same(v[rows],attrs[s][newRows]):fieldFailures.append(s)
for i,target in enumerate(C.d['meshes'][0]['primitives'][0].get('targets',[])):
 for s,ai in target.items():
  if not same(C.acc(ai)[rows],morphs[i][s][newRows]):fieldFailures.append('morph_'+str(i)+'_'+s)
# Independent exact station reduction and once-cast actual positions.
cum=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(U[path].astype(np.float64),axis=0),axis=1),dtype=np.float64)];us=cum/cum[-1];station={int(pid):float(v) for pid,v in zip(path,us)};station[4041]=float(np.mean(np.array([station[i] for i in [3674,3717,4279,4393]],np.float64)))
expectPhysical=U.copy();expectPhysical[interior]=z['finalFreeXYZFloat64'].astype(np.float32)
expectedTarget=np.array([float(U[1488,1])+station[int(pid)]*(float(U[13448,1])-float(U[1488,1])) for pid in interior],np.float64)
conservation['finalOneCastFloat32Exact']=same(physical,expectPhysical) and same(attrs['POSITION'][newRows],expectPhysical[q[rows]])
conservation['targetAndSourceStationsExact']=same(expectedTarget,z['targetYFloat64']) and same(us,z['pathStationsFloat64']) and same(cum,z['pathCumulativeFloat64'])
conservation['pathEndpointStationsExact']=us[0]==0 and us[-1]==1
maxTargetError=float(np.max(abs(physical[interior,1].astype(float)-expectedTarget)))
targetProxy=maxTargetError<=.002
if not targetProxy:reasons.append('Maximum actual Float32 soft targetY error exceeds2mm')
# Independent normal-group recomputation, byte-exact duplicate aliases.
t=attrs['POSITION'][indices].astype(float);faceV=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normalChecks=[];normalFailures=[];normalTurns=[];groups=defaultdict(list)
for row in rows:groups[(int(q[row]),tuple(a['NORMAL'][row].view(np.uint32)))].append(int(row))
for (pid,bits),sr in sorted(groups.items()):
 fs=sorted({int(fi) for fi in changed for row in F[fi] if q[row]==pid and tuple(a['NORMAL'][row].view(np.uint32))==bits});total=np.zeros(3,np.float64)
 for fi in fs:total+=faceV[fi]
 length=np.linalg.norm(total);n=np.zeros(3,np.float32) if length==0 else (total/length).astype(np.float32);new=[cloneMap[r] for r in sr];ok=all(same(attrs['NORMAL'][r],n) for r in new);oldDot=float(n.astype(float)@a['NORMAL'][sr[0]].astype(float))
 if not ok or length==0:normalFailures.append({'physicalID':pid,'sourceRows':sr,'exact':ok,'sumLength':float(length),'newDotOriginal':oldDot})
 if oldDot<=0:normalTurns.append({'physicalID':pid,'sourceRows':sr,'newDotOriginal':oldDot})
 normalChecks.append({'physicalID':pid,'sourceRows':sr,'newRows':new,'faceIDs':fs,'exact':ok,'sourceNormalBits':list(map(int,bits)),'newDotOriginal':oldDot})
# Attribute legality is measured, preserving known source skin problems literally.
finite=all(np.isfinite(v).all() for v in attrs.values()) and all(np.isfinite(v).all() for tg in morphs for v in tg.values());counts=all(len(v)==len(attrs['POSITION']) for v in attrs.values()) and all(len(v)==len(attrs['POSITION']) for tg in morphs for v in tg.values());indexLegal=bool(indices.min()>=0 and indices.max()<len(attrs['POSITION']));skin={'jointRangeLegal':bool(np.all(attrs['JOINTS_0']<19)),'nonnegativeWeights':bool(np.all(attrs['WEIGHTS_0']>=0)),'maximumCloneWeightSumError':float(np.max(abs(np.sum(attrs['WEIGHTS_0'][newRows],axis=1,dtype=np.float32)-1))),'sourceWeightsLiteral':same(a['WEIGHTS_0'][rows],attrs['WEIGHTS_0'][newRows]),'qualification':'source weights known bad; no motion/skin acceptance'}
# All five actual referenced primitive geometries, including both head pieces.
def assemble(candidate):
 ps=[];fs=[];origins=[];offset=0;changedGlobal=[];receipts=[]
 for mi,m in enumerate(C.d['meshes']):
  for pi,p in enumerate(m['primitives']):
   aa,ff=C.primitive(mi,pi);originalA,originalF=aa,ff
   if candidate and (mi,pi)==(0,0):aa,ff=attrs,indices
   ps.append(aa['POSITION']);fs.append(ff.astype(np.int64)+offset);receipts.append({'mesh':mi,'primitive':pi,'faces':len(ff),'sourceFieldsPreserved':(mi,pi)==(0,0) or all(same(aa[s],originalA[s]) for s in aa),'sourceIndicesPreserved':(mi,pi)==(0,0) or same(ff,originalF)})
   for j in range(len(ff)):
    origins.append({'mesh':mi,'primitive':pi,'sourceFace':j})
    if candidate and (mi,pi)==(0,0) and j in changedSet:changedGlobal.append(len(origins)-1)
   offset+=len(aa['POSITION'])
 return np.concatenate(ps),np.concatenate(fs),origins,changedGlobal,receipts
srcPos,srcFaces,_,_,srcPrimitives=assemble(False);pos,fs,origins,changedGlobal,primitives=assemble(True);assert len(primitives)==5
sourceTopo,_=topology(srcPos,srcFaces);topo,globalPF=topology(pos,fs);boundaryExact=sourceTopo['boundaryPositionKeys']==topo['boundaryPositionKeys'];componentsExact=sourceTopo['components']==topo['components'];physicalUnique,countsUnique=np.unique(physical,axis=0,return_counts=True);collisions=np.flatnonzero(countsUnique>1);collisionWitness=[{'positionM':physicalUnique[i].tolist(),'originalPhysicalIDs':np.flatnonzero(np.all(physical==physicalUnique[i],axis=1)).tolist()} for i in collisions]
save(S/'topology.json',{'source':sourceTopo,'candidate':topo,'boundaryExact':boundaryExact,'componentsExact':componentsExact,'physicalCollisions':collisionWitness,'primitives':primitives})
for k in ['zeroSliverFaces','nonmanifoldEdges','windingEdges','duplicatePhysicalFaces','vertexLinkPinches']:
 if topo[k]:reasons.append('Actual whole Float32 topology: '+k)
if not boundaryExact or not componentsExact:reasons.append('Original whole boundary/components changed')
if len(collisions):reasons.append('Distinct original physical IDs collapsed')
# Exact boundary incidence and source corner donors remain unsplit.
ee=edges(rowPID[indices]);boundaryReceipts=[]
for i,j in zip(boundary,boundary[1:]+boundary[:1]):
 owners=ee[tuple(sorted((i,j)))];boundaryReceipts.append({'originalEdge':[i,j],'owners':[int(fi) for fi,_ in owners],'opposed':len(owners)==2 and owners[0][1]!=owners[1][1]})
if not all(x['opposed'] for x in boundaryReceipts):reasons.append('Fixed78 perimeter incidence failed')
# Shared0/1/2 predicate fixtures: crossings, overlaps and legal adjacent contacts.
fa=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
fixtures=[('strict_cross',[[.25,.25,-1.],[.25,.25,1.],[.75,.25,0.]],True,False),('coplanar_shared0',[[.1,.1,0.],[.4,.1,0.],[.1,.4,0.]],False,True),('coplanar_shared1',[[0.,0.,0.],[.8,.1,0.],[.1,.8,0.]],False,True),('legal_shared2',[[0.,0.,0.],[1.,0.,0.],[0.,-1.,0.]],False,False),('legal_shared1',[[0.,0.,0.],[-1.,0.,0.],[0.,-1.,0.]],False,False),('coplanar_shared2',[[0.,0.,0.],[1.,0.,0.],[.2,.2,0.]],False,True)]
fixtureResults=[]
for name,fb,es,ep in fixtures:
 fb=np.array(fb);ss=bool(strict(fa[None],fb[None])[0]);cl=projected(fa,fb);fixtureResults.append({'name':name,'pass':ss==es and cl['positiveOverlap']==ep,'strict':ss,**cl})
assert all(f['pass'] for f in fixtureResults)
# Changed local versus allfive; unchanged pairs inherited by byte-exact geometry.
tri=pos[fs].astype(float);cent=tri.mean(1);rad=np.linalg.norm(tri-cent[:,None],axis=2).max(1);lo=tri.min(1);hi=tri.max(1);tree=cKDTree(cent);rmax=float(rad.max());pairs=set()
for begin in range(0,len(changedGlobal),128):
 ids=np.array(changedGlobal[begin:begin+128]);neighbors=tree.query_ball_point(cent[ids],rad[ids]+rmax+1e-12,workers=2)
 for i,ns in zip(ids,neighbors):
  js=np.array([j for j in ns if j!=i],int);js=js[(hi[i]>=lo[js]-1e-12).all(1)&(lo[i]<=hi[js]+1e-12).all(1)]
  for j in js:pairs.add(tuple(sorted((int(i),int(j)))))
 check()
pairs=sorted(pairs);strictHits=[];coplanar=[];categories=Counter();badPredicate=[]
for begin in range(0,len(pairs),4096):
 batch=pairs[begin:begin+4096];ia=np.array([i for i,j in batch]);ib=np.array([j for i,j in batch]);hit=strict(tri[ia],tri[ib]);na=np.cross(tri[ia,1]-tri[ia,0],tri[ia,2]-tri[ia,0]);nb=np.cross(tri[ib,1]-tri[ib,0],tri[ib,2]-tri[ib,0]);la=np.linalg.norm(na,axis=1);lb=np.linalg.norm(nb,axis=1);valid=(la>1e-12)&(lb>1e-12);ua=na/np.where(la>0,la,1)[:,None];ub=nb/np.where(lb>0,lb,1)[:,None];near=valid&(np.linalg.norm(np.cross(ua,ub),axis=1)<1e-8)&(abs(np.einsum('ij,ij->i',tri[ib,0]-tri[ia,0],ua))<1e-8)
 for k,(i,j) in enumerate(batch):
  shared=len(set(globalPF[i])&set(globalPF[j]));categories[str(shared)]+=1
  witness={'globalFaces':[i,j],'physicalSharedCorners':shared,'ancestry':[origins[i],origins[j]],'trianglesM':tri[[i,j]].tolist()}
  if not valid[k]:badPredicate.append([i,j])
  if hit[k]:strictHits.append(witness)
  if near[k]:coplanar.append({**witness,**projected(tri[i],tri[j])})
 check()
positiveCop=[v for v in coplanar if v['positiveOverlap']];save(S/'rest-crossing-evidence.json',{'candidatePairCount':len(pairs),'changedSourceFaces':len(changedGlobal),'againstAll5Primitives':True,'primitiveReceipts':primitives,'allPairs':pairs,'sharedCornerCategoryCounts':dict(categories),'strictCrossings':strictHits,'nearCoplanarClassifications':coplanar,'degeneratePredicatePairs':badPredicate,'fixtures':fixtureResults,'predicatePins':pins})
if strictHits:reasons.append('Changed source168 versus all5 strict crossings')
if positiveCop:reasons.append('Changed source168 exact/near coplanar overlaps')
# Full p0 referenced physical graph, rooted by frozen independent source labels.
g=defaultdict(set)
for t in rowPID[indices]:
 for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);g[i].add(j);g[j].add(i)
roots=sep['roots'];central=roots['central_Z0_straddling'];lateral=roots['positiveZ_lateral'];d={int(i):float(physical[i,1]) for i in central};previous={};heap=[(v,i) for i,v in d.items()];heapq.heapify(heap)
while heap:
 h,i=heapq.heappop(heap)
 if h!=d[i]:continue
 for j in sorted(g[i]):
  nh=max(h,float(physical[j,1]))
  if nh<d.get(j,float('inf')):d[j]=nh;previous[j]=i;heapq.heappush(heap,(nh,j))
target=min(lateral,key=lambda i:(d.get(i,float('inf')),i));attachment=d.get(target,float('inf'));minimaxPath=[target]
while minimaxPath[-1] in previous:minimaxPath.append(previous[minimaxPath[-1]])
separated=not any(d.get(i,float('inf'))<1.30 for i in lateral)
if not separated or not 1.30<=attachment<=1.32:reasons.append('Rooted low routes or high attachment failed')
save(S/'rooted-routes.json',{'roots':roots,'lowRoutesAbsentBelow1_30':separated,'firstAttachmentY_M':attachment,'minimaxPathOriginalPhysicalIDs':minimaxPath[::-1],'allFiniteMinimaxLabels':{str(i):v for i,v in d.items()},'candidateReferencedP0Graph':True})
# Actual source-to-sculpt strain: descriptive only, no invented stretch gate.
sourceTri=U[q[F[changed]]].astype(float);newTri=physical[q[F[changed]]].astype(float);oldV=np.cross(sourceTri[:,1]-sourceTri[:,0],sourceTri[:,2]-sourceTri[:,0]);newV=np.cross(newTri[:,1]-newTri[:,0],newTri[:,2]-newTri[:,0]);oldArea=np.linalg.norm(oldV,axis=1)/2;newArea=np.linalg.norm(newV,axis=1)/2
edgeList=sorted(edges(q[F[changed]]));oldLength=np.array([np.linalg.norm(U[i].astype(float)-U[j].astype(float)) for i,j in edgeList]);newLength=np.array([np.linalg.norm(physical[i].astype(float)-physical[j].astype(float)) for i,j in edgeList]);ratios=newLength/oldLength
angles=lambda t:np.array([np.arccos(np.clip(np.einsum('ij,ij->i',t[:,(j+1)%3]-t[:,j],t[:,(j+2)%3]-t[:,j])/(np.linalg.norm(t[:,(j+1)%3]-t[:,j],axis=1)*np.linalg.norm(t[:,(j+2)%3]-t[:,j],axis=1)),-1,1)) for j in range(3)]).T
oldAng=angles(sourceTri);newAng=angles(newTri);turn=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',oldV,newV)/(2*oldArea*2*newArea),-1,1)))
strain={'measurementOnlyNoStretchGate':True,'edgeRatioRange':[float(ratios.min()),float(ratios.max())],'areaRatioRange':[float((newArea/oldArea).min()),float((newArea/oldArea).max())],'maximumAngleChangeDegrees':float(np.degrees(abs(newAng-oldAng)).max()),'minimumCandidateTriangleAngleDegrees':float(np.degrees(newAng).min()),'faceNormalTurnDegreesRange':[float(turn.min()),float(turn.max())],'facesTurningOver90Degrees':changed[turn>90].tolist(),'edges':[{'physicalEdge':list(e),'sourceM':float(o),'candidateM':float(n),'ratio':float(r)} for e,o,n,r in zip(edgeList,oldLength,newLength,ratios)],'faces':[{'sourceFace':int(fi),'sourceAreaM2':float(o),'candidateAreaM2':float(n),'areaRatio':float(n/o),'sourceAnglesDegrees':np.degrees(oa).tolist(),'candidateAnglesDegrees':np.degrees(na).tolist(),'normalTurnDegrees':float(t)} for fi,o,n,oa,na,t in zip(changed,oldArea,newArea,oldAng,newAng,turn)]};save(S/'strain.json',strain)
if not all(conservation.values()):reasons.append('Literal source/provenance conservation failure')
if not finite or not counts or not indexLegal:reasons.append('Accessor legality failed')
if fieldFailures:reasons.append('Cloned source fields or morphs changed')
if normalFailures or pr['constructionFailures']:reasons.append('Interior source-normal group zero or consistency failures')
report={'status':'FROZEN_STATIC_REJECTION_NO_GLB' if reasons else 'STATIC_CLEAR_UNACCEPTED_PENDING_PARENT','attemptCount':1,'geometryGenerated':True,'GLBExported':False,'accepted':False,'sourceSHA256':SHA,'dumpSHA256':pins[str(dumpPath)]['sha256'],'sourceFaces':len(changed),'newAccessorRows':len(rows),'interiorPhysicalIDs':len(interior),'allOriginalRowsUnchanged':all(conservation[s] for s in a),'conservation':conservation,'finite':finite,'countsLegal':counts,'indicesLegal':indexLegal,'skin':skin,'fieldFailures':fieldFailures,'normalGroupCount':len(groups),'normalGroupFailures':normalFailures,'sourceNormalTurnGroupsNotInversionCertificate':normalTurns,'maximumTargetErrorM':maxTargetError,'targetProxyWithin2mm':targetProxy,'sourceTopology':{k:v for k,v in sourceTopo.items() if k not in ['boundaryPositionKeys','vertexLinkPinches']},'candidateTopology':{k:v for k,v in topo.items() if k not in ['boundaryPositionKeys','vertexLinkPinches']},'original237OpeningEdgesExpected':sourceTopo['boundaryEdgeCount']==237,'all5PrimitiveCount':len(primitives),'boundaryExact':boundaryExact,'componentsExact':componentsExact,'physicalFloat32Collisions':len(collisions),'strictCrossings':len(strictHits),'positiveCoplanarOverlaps':len(positiveCop),'broadphasePairs':len(pairs),'sharedClasses':dict(categories),'rootedLowRoutesSeparated':separated,'firstAttachmentY_M':attachment,'strainSummary':{k:v for k,v in strain.items() if k not in ['edges','faces']},'rejectionReasons':reasons,'elapsedSeconds':time.monotonic()-start,'CPUThreads':2,'GPU':False,'anonymousGBSamples':mem,'inputPins':pins,'limits':['Static final Float32 construction only; no art, skin, rig, played motion or mobile acceptance','Source weights preserved literally and known bad','FreeXYZ shell solve; contact is native triangle CCD/barrier, no heightfield guarantee or anatomy/skin acceptance','Unchanged triangle pairs inherited from byte-exact protected geometry; actual changed local168 checked against allfive, including shared0/1/2']}
save(E/'field-provenance-checks.json',{'conservation':conservation,'normalGroups':normalChecks,'fieldFailures':fieldFailures,'boundaryEdges':boundaryReceipts});save(E/'report.json',report)
save(E/'actual-crossing-witnesses.json',{'dumpSHA256':report['dumpSHA256'],'strictCrossings':strictHits,'positiveCoplanarOverlaps':positiveCop,'sharedClasses':dict(categories),'all5PrimitiveCount':len(primitives)})
save(E/'attempt.json',{'status':report['status'],'attemptCount':1,'geometryGenerated':True,'GLBExported':False,'dumpSHA256':report['dumpSHA256'],'rejectionReasons':reasons})
if reasons:
 assert not (S/'rider.glb').exists()
else:
 # Append-only GLB: original BIN bytes and every protected original JSON object retained.
 d=copy.deepcopy(C.d);binchunk=bytearray(C.bin);oldAccessors=copy.deepcopy(d['accessors']);oldViews=copy.deepcopy(d['bufferViews']);originalPrimitive=copy.deepcopy(d['meshes'][0]['primitives'][0]);p=d['meshes'][0]['primitives'][0]
 def append(v,template,index=False):
  binchunk.extend(b'\0'*((-len(binchunk))%4));offset=len(binchunk);v=np.ascontiguousarray(v);binchunk.extend(v.tobytes());vi=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':v.nbytes,'target':34963 if index else 34962});acc=copy.deepcopy(template);acc.pop('sparse',None);acc['bufferView']=vi;acc['byteOffset']=0;acc['count']=len(v);acc.pop('min',None);acc.pop('max',None)
  if not index and acc['type']=='VEC3':acc['min']=v.min(0).tolist();acc['max']=v.max(0).tolist()
  ai=len(d['accessors']);d['accessors'].append(acc);return ai
 for s,v in attrs.items():p['attributes'][s]=append(v,C.d['accessors'][originalPrimitive['attributes'][s]])
 for i,tg in enumerate(morphs):
  for s,v in tg.items():p['targets'][i][s]=append(v,C.d['accessors'][originalPrimitive['targets'][i][s]])
 ix=indices.astype(np.uint32).reshape(-1,1);template=copy.deepcopy(C.d['accessors'][originalPrimitive['indices']]);template['componentType']=5125;p['indices']=append(ix,template,True)
 assert d['accessors'][:len(oldAccessors)]==oldAccessors and d['bufferViews'][:len(oldViews)]==oldViews and bytes(binchunk[:len(C.bin)])==C.bin
 d['buffers'][0]['byteLength']=len(binchunk);binchunk.extend(b'\0'*((-len(binchunk))%4));js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);out=struct.pack('<III',0x46546c67,2,28+len(js)+len(binchunk))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binchunk),0x004e4942)+binchunk;(S/'rider.glb').write_bytes(out);report['GLBExported']=True;report['GLBSHA256']=sha(out);save(E/'report.json',report)
print(json.dumps({k:report[k] for k in ['status','newAccessorRows','normalGroupCount','strictCrossings','positiveCoplanarOverlaps','firstAttachmentY_M','maximumTargetErrorM','targetProxyWithin2mm','rejectionReasons','GLBExported','elapsedSeconds']}),flush=True)
