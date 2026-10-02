"""ONE immutable194 ruled construction. Exact parameter clipping; CPU only."""
from common import *
C,a,F,U,q,c,charts,comparison,sep,refs=source();assert not(S/'construction.npz').exists();attempt=json.loads((E/'attempt.json').read_text());assert attempt['status'] in ['PREREGISTERED_ONE_CONSTRUCTION_TRIAL','RUNNING_ONE_CONSTRUCTION'] and not attempt['geometryGenerated']
attempt.update(status='RUNNING_ONE_CONSTRUCTION',pid=os.getpid());save(E/'attempt.json',attempt)
PF=q[F];removed=c['exactRemovedSourceFaceIDs'];kept=np.array([i for i in range(len(F)) if i not in set(removed)],np.int64);boundary=set(c['fixedOrientedBoundaryPhysicalIDs']);endpoints=c['highSeamEndpointPhysicalIDs'];worldQ=[tuple(Q(float(v)) for v in p) for p in U];referenceToPhysical={refs[fi][j]:int(PF[fi,j]) for fi in removed for j in range(3)};physWorld=list(worldQ);physParam={pid:p for p,pid in referenceToPhysical.items()};physicalByParam=dict(referenceToPhysical);baseTriangles=[];baseRecords=[];fragmentRecords=[];contactRecords=[];failures=[]
union=sorted(set(Q(u) for x in c['arcCorrespondence'].values() for u in x['normalizedSourceArcLengthStations']))

def ring(name,r,stations):
 arc=c['arcCorrespondence'][name];us=[Q(u) for u in arc['normalizedSourceArcLengthStations']];ids=arc['physicalIDs'];rp=[];wp=[]
 for u in stations:
  j=min(np.searchsorted(us,u,side='right')-1,len(us)-2);j=max(j,0);t=(u-us[j])/(us[j+1]-us[j])
  refBoundary=tuple((1-t)*physParam[ids[j]][k]+t*physParam[ids[j+1]][k] for k in range(2));wb=tuple((1-t)*worldQ[ids[j]][k]+t*worldQ[ids[j+1]][k] for k in range(3));ch=tuple((1-u)*worldQ[endpoints[0]][k]+u*worldQ[endpoints[1]][k] for k in range(3));rp.append((u,(1-r)*refBoundary[1]));wp.append(tuple((1-r)*wb[k]+r*ch[k] for k in range(3)))
 return rp,wp

# Deterministic zipper with common endpoints collapsed before unequal stations.
def zipper(rp,wp,sp,xp):
 out=[];i=j=0;collapsed=0
 while i<len(rp)-1 or j<len(sp)-1:
  if i==j==0:outer=True
  elif i==len(rp)-2 and j<len(sp)-1:outer=False
  else:outer=(i<len(rp)-1) and (j==len(sp)-1 or rp[i+1][0]<sp[j+1][0])
  pts=[rp[i],rp[i+1],sp[j]] if outer else [rp[i],sp[j+1],sp[j]];ws=[wp[i],wp[i+1],xp[j]] if outer else [wp[i],xp[j+1],xp[j]]
  if outer:i+=1
  else:j+=1
  if len(set(pts))<3:
   assert all(p[0] in [Q(0),Q(1)] for p in pts if pts.count(p)>1);collapsed+=1;continue
  signed=c2(sub(pts[1],pts[0]),sub(pts[2],pts[0]));assert signed!=0,'Exact zipper degeneracy'
  if signed<0:pts[1],pts[2]=pts[2],pts[1];ws[1],ws[2]=ws[2],ws[1]
  out.append((tuple(pts),tuple(ws)))
 return out,collapsed

# A straight seam with early extra stations must keep its complete edge boundary.
toyOuter=[(Q(0),Q(0)),(Q(1,3),Q(-1)),(Q(3,4),Q(-1)),(Q(1),Q(0))]
toyInner=[(Q(u),Q(0)) for u in [0,Q(1,8),Q(1,4),Q(1,3),Q(1,2),Q(3,4),Q(7,8),1]]
toy,collapsed=zipper(toyOuter,toyOuter,toyInner,toyInner);te=Counter(tuple(sorted((t[k],t[(k+1)%3]))) for t,w in toy for k in range(3));toyBoundary={e for e,n in te.items() if n==1};expected={tuple(sorted(e)) for curve in [toyOuter,toyInner] for e in zip(curve,curve[1:])};assert toyBoundary==expected and collapsed==2 and all(n<=2 for n in te.values());save(S/'zipper-fixtures.json',{'unequalStationsCommonEndpointCollapse':True,'collapsedEndpoints':collapsed,'exactBoundaryConserved':toyBoundary==expected,'triangles':len(toy),'geometryAttempt':False})
for name in ['central','lateral']:
 us=[Q(u) for u in c['arcCorrespondence'][name]['normalizedSourceArcLengthStations']];levels=[Q(0),Q(1,3),Q(2,3),Q(1)];rings=[ring(name,r,union if r==1 else us) for r in levels]
 for ri in range(3):
  rp,wp=rings[ri];sp,xp=rings[ri+1];zs,collapsed=zipper(rp,wp,sp,xp);assert collapsed==2
  for pts,ws in zs:
   baseTriangles.append((pts,ws));baseRecords.append({'panel':name,'radialBand':ri,'parameterCorners':[encode(p) for p in pts]})

# Convex fragment triangulation keeps every exact clipping vertex. Never delete slivers.
def triangulate(poly):
 live=list(range(len(poly)));out=[]
 while len(live)>3:
  candidates=[]
  for k,i in enumerate(live):
   aa,bb,cc=live[k-1],i,live[(k+1)%len(live)]
   if c2(sub(poly[bb],poly[aa]),sub(poly[cc],poly[bb]))>0:candidates.append((i,k,aa,bb,cc))
  assert candidates,'No nonzero exact convex ear'
  _,k,aa,bb,cc=min(candidates);out.append([poly[aa],poly[bb],poly[cc]]);live.pop(k)
 if len(live)==3:out.append([poly[i] for i in live])
 return out

for bi,(bt,bw) in enumerate(baseTriangles):
 for fi,st in sorted(refs.items()):
  poly=clip_exact(list(bt),list(st));area=sum(c2(poly[k],poly[(k+1)%len(poly)]) for k in range(len(poly)))/2 if len(poly)>=3 else Q(0)
  if area==0:
   if poly:contactRecords.append({'baseTriangle':bi,'sourceFace':fi,'pointCount':len(poly)})
   continue
  assert area>0
  for pt in triangulate(poly):
   pids=[]
   for p in pt:
    w=bary(p,bt);wp=blend(bw,w)
    if p not in physicalByParam:
     pid=len(physWorld);physicalByParam[p]=pid;physParam[pid]=p;physWorld.append(wp)
    else:
     pid=physicalByParam[p]
     if physWorld[pid]!=wp:failures.append({'type':'exact_world_alias_mismatch','physicalID':pid,'baseTriangle':bi})
    pids.append(pid)
   fragmentRecords.append({'baseTriangle':bi,'panel':baseRecords[bi]['panel'],'sourceFace':fi,'sourceChart':charts[fi],'physicalCorners':pids,'referenceCorners':[encode(p) for p in pt],'sourceBarycentrics':[[float(x) for x in bary(p,st)] for p in pt]})
 check()
positions=np.array([[float(v) for v in p] for p in physWorld],dtype=np.float32);newPF=np.array([x['physicalCorners'] for x in fragmentRecords],np.int64);used=sorted(set(newPF.ravel().tolist()));fields={};morphSource=[{s:C.acc(ai) for s,ai in t.items()} for t in C.d['meshes'][0]['primitives'][0].get('targets',[])];loss=[];canonicalRecords=[]
for pid in used:
 p=physParam[pid];choices=[(fi,bary(p,t)) for fi,t in sorted(refs.items()) if min(bary(p,t))>=0];assert choices;fi,bw=choices[0];w=np.array([float(v) for v in bw]);rows=F[fi];dense=np.zeros(19,float)
 for lane in range(3):
  for ji,wi in zip(a['JOINTS_0'][rows[lane]],a['WEIGHTS_0'][rows[lane]]):dense[int(ji)]+=w[lane]*float(wi)
 lanes=sorted([i for i in range(19) if dense[i]>0],key=lambda i:(-dense[i],i))[:4];discarded=float(sum(dense[i] for i in range(19) if i not in lanes));joints=np.zeros(4,a['JOINTS_0'].dtype);weights=np.zeros(4,np.float32);joints[:len(lanes)]=lanes;weights[:len(lanes)]=dense[lanes].astype(np.float32);weights=(weights/np.sum(abs(weights),dtype=np.float32)).astype(np.float32)
 morph=[{s:(w@v[rows].astype(float)).astype(v.dtype) for s,v in t.items()} for t in morphSource];sourcePos=w@a['POSITION'][rows].astype(float);displacement=float(np.linalg.norm(positions[pid].astype(float)-sourcePos));fields[pid]=(joints,weights,morph,dense,discarded,fi,w,displacement);canonicalRecords.append({'physicalID':pid,'sourceFace':fi,'barycentric':w.tolist(),'sourceBarycentricPositionM':sourcePos.tolist(),'candidateDisplacementM':displacement,'dense19':dense.tolist(),'discardedPositiveMass':discarded,'joints4':joints.tolist(),'weights4':weights.tolist()})
# Physical area-weighted normals over the candidate cap, identical chart aliases.
tri=positions[newPF].astype(float);areaNormals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normalSum=defaultdict(lambda:np.zeros(3))
for t,n in zip(newPF,areaNormals):
 for pid in t:normalSum[int(pid)]+=n
normalByPhysical={}
for pid,n in normalSum.items():
 length=np.linalg.norm(n)
 if length==0:failures.append({'type':'zero_area_weighted_normal','physicalID':pid});normalByPhysical[pid]=np.zeros(3,np.float32)
 else:normalByPhysical[pid]=(n/length).astype(np.float32)
incident=defaultdict(list)
for fi in kept:
 for pid in PF[fi]:incident[int(pid)].append(int(fi))
newAttributes={s:[] for s in a};newMorphs=[{s:[] for s in t} for t in morphSource];cornerRecords=[];newRows=[];hardNormalAliases=[]
for ti,fr in enumerate(fragmentRecords):
 rows=[];fi=fr['sourceFace'];srcRows=F[fi]
 for lane,pid in enumerate(fr['physicalCorners']):
  w=np.array(fr['sourceBarycentrics'][lane]);row=len(a['POSITION'])+len(cornerRecords);rows.append(row);joints,weights,morph,dense,discarded,cfi,cw,disp=fields[pid];normal=normalByPhysical[pid];normalSource=None
  if pid in boundary:
   candidates=[(int(F[sfi][np.flatnonzero(PF[sfi]==pid)[0]]),sfi) for sfi in incident[pid] if charts.get(sfi)==fr['sourceChart']]
   # Match literal removed chart corner's hard normal, when multiple exist.
   refrow=int(srcRows[np.flatnonzero(PF[fi]==pid)[0]]) if pid in PF[fi] else None
   exact=[x for x in candidates if refrow is not None and np.array_equal(a['NORMAL'][x[0]],a['NORMAL'][refrow])];chosen=min(exact or candidates) if candidates else None
   if chosen is None:
    failures.append({'type':'missing_retained_boundary_chart_normal','physicalID':pid,'sourceFace':fi,'chart':fr['sourceChart']});normal=a['NORMAL'][refrow] if refrow is not None else normal
   else:normalSource={'sourceRow':chosen[0],'sourceFace':chosen[1]};normal=a['NORMAL'][chosen[0]]
   normals={tuple(a['NORMAL'][rr]) for rr,sfi in candidates}
   if len(normals)>1:hardNormalAliases.append({'physicalID':pid,'sourceChart':fr['sourceChart'],'sourceRows':[rr for rr,sfi in candidates],'chosen':normalSource,'distinctNormals':len(normals)})
  for semantic,v in a.items():
   value=positions[pid] if semantic=='POSITION' else normal if semantic=='NORMAL' else joints if semantic=='JOINTS_0' else weights if semantic=='WEIGHTS_0' else (w@v[srcRows].astype(float)).astype(v.dtype)
   newAttributes[semantic].append(value)
  for mi,t in enumerate(newMorphs):
   for semantic in t:t[semantic].append(morph[mi][semantic])
  cornerRecords.append({'newAccessorRow':row,'newTriangle':ti,'lane':lane,'physicalID':pid,'sourceFace':fi,'sourceChart':fr['sourceChart'],'sourceCornerRows':srcRows.tolist(),'barycentric':w.tolist(),'canonicalSourceFace':cfi,'canonicalBarycentric':cw.tolist(),'normalSource':normalSource,'normalRule':'retained_matched_chart' if pid in boundary else 'candidate_physical_area_weighted','discardedPositiveWeightMass':discarded,'sourceDisplacementM':disp})
 newRows.append(rows)
attrs={s:np.concatenate([v,np.array(newAttributes[s],dtype=v.dtype).reshape(-1,v.shape[1])]) for s,v in a.items()};morphs=[{s:np.concatenate([morphSource[i][s],np.array(vals,dtype=morphSource[i][s].dtype).reshape(-1,3)]) for s,vals in t.items()} for i,t in enumerate(newMorphs)];indices=np.concatenate([F[kept].astype(np.int64),np.array(newRows,np.int64)])
newPIDs=np.array([r['physicalID'] for r in cornerRecords],np.int64);dump={'positions':attrs['POSITION'],'indices':indices,'sourceKeptFaceIDs':kept,'removedSourceFaceIDs':np.array(removed,np.int64),'newPhysicalTriangles':newPF,'physicalPositions':positions,'sourcePhysicalPositions':U,'attributeRowPhysicalIDs':np.concatenate([q,newPIDs]),'newReferenceParameters':np.array([[float(v) for v in physParam[int(pid)]] for pid in newPIDs]),'newCanonicalSourceFaceIDs':np.array([fields[int(pid)][5] for pid in newPIDs]),'newCanonicalBarycentrics':np.array([fields[int(pid)][6] for pid in newPIDs]),'newDense19Weights':np.array([fields[int(pid)][3] for pid in newPIDs]),'newDiscardedWeightMass':np.array([fields[int(pid)][4] for pid in newPIDs])}
for s,v in attrs.items():dump['attribute_'+s]=v
for i,t in enumerate(morphs):
 for s,v in t.items():dump['morph_'+str(i)+'_'+s]=v
np.savez_compressed(S/'construction.npz',**dump)
save(S/'construction-provenance.json',{'sourceSHA256':SHA,'contractSHA256':attempt['contractSHA256'],'originalPositionsMoved':0,'baseTriangles':baseRecords,'fragments':fragmentRecords,'zeroAreaReferenceContacts':contactRecords,'physicalReferenceParameters':{str(pid):encode(p) for pid,p in physParam.items() if pid in used},'canonicalPhysicalFields':canonicalRecords,'newCornerProvenance':cornerRecords,'hardNormalAliases':hardNormalAliases,'constructionFailures':failures,'inputs':pins,'recipeSHA256':sha(Path(__file__).read_bytes()),'commonSHA256':sha(Path(__file__).with_name('common.py').read_bytes())})
attempt.update(status='ONE_CONSTRUCTION_DUMPED_PENDING_STATIC_VERIFICATION',geometryGenerated=True,dumpSHA256=sha((S/'construction.npz').read_bytes()),generatedTriangles=len(newPF),newAccessorRows=len(cornerRecords));save(E/'attempt.json',attempt)
save(S/'build-process.json',{'pid':os.getpid(),'elapsedSeconds':time.monotonic()-start,'anonymousGBSamples':mem,'CPUThreads':2,'GPU':False,'inputs':pins,'constructionFailures':failures,'baseTriangles':len(baseTriangles),'fragmentTriangles':len(newPF)})
print(json.dumps({'phase':'ONE194_DUMPED','baseTriangles':len(baseTriangles),'newTriangles':len(newPF),'newAccessorRows':len(cornerRecords),'constructionFailures':len(failures),'elapsedSeconds':time.monotonic()-start,'dumpSHA256':attempt['dumpSHA256']}),flush=True)
