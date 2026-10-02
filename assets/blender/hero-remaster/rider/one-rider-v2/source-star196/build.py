"""Exactly one append-only source-star scalar construction. CPU only, no tuning."""
from common import *
C,a,F,U,q,c,alias,graph,star,path,sep=source()
assert not (S/'construction.npz').exists(),'Candidate already exists; construction forbidden'
assert not (E/'attempt.json').exists(),'Attempt already registered'
removed=np.array(star['removedSourceFaceIDs'],np.int64);interior=np.array(c['exactReleasedInteriorPhysicalIDs'],np.int64);boundary=star['orientedFillBoundaryPhysicalIDs'];PF=q[F]
assert 3823 in removed and 3824 in removed
assert set(PF[removed].ravel())-set(boundary)==set(interior)
rows=np.flatnonzero(np.isin(q,interior));assert rows.tolist()==sorted(r for v in alias['sourceRowAliases'].values() for r in v['originalSourceAccessorRows'])
assert all(v['incidentRetainedSourceFaceIDs']==[] for v in alias['sourceRowAliases'].values())
recipeSHA=sha(Path(__file__).read_bytes());save(E/'attempt.json',{'status':'RUNNING_REGISTERED_SINGLE196_TRIAL','attemptCount':1,'geometryGenerated':False,'contractPath':str(CONTRACT),'contractSHA256':pins[str(CONTRACT)]['sha256'],'sourceSHA256':SHA,'recipeSHA256':recipeSHA})
lengths=np.linalg.norm(np.diff(U[path].astype(np.float64),axis=0),axis=1);cumulative=np.concatenate([np.zeros(1,np.float64),np.cumsum(lengths,dtype=np.float64)]);stations=cumulative/cumulative[-1];assert stations[0]==0 and stations[-1]==1
u={int(pid):float(t) for pid,t in zip(path,stations)};u[4041]=float(np.mean(np.array([u[i] for i in [3674,3717,4279,4393]],np.float64)))
physical=U.copy();y0=float(U[1488,1]);y1=float(U[13448,1])
for pid in interior:physical[pid,1]=np.float32(y0+u[int(pid)]*(y1-y0))
attrs={s:np.concatenate([v,v[rows].copy()]) for s,v in a.items()};attrs['POSITION'][len(a['POSITION']):]=physical[q[rows]]
clones={int(r):int(len(a['POSITION'])+i) for i,r in enumerate(rows)};indices=F.astype(np.int64).copy();cornerRecords=[]
for fi in removed:
 for lane,row in enumerate(F[fi]):
  if int(row) in clones:
   indices[fi,lane]=clones[int(row)];cornerRecords.append({'sourceFace':int(fi),'lane':lane,'sourceRow':int(row),'newRow':clones[int(row)],'physicalID':int(q[row])})
# Source normal crease charts: exact Float32 bits, independent of UV islands.
tri=attrs['POSITION'][indices].astype(np.float64);vectors=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normalGroups=defaultdict(list)
for row in rows:normalGroups[(int(q[row]),tuple(a['NORMAL'][row].view(np.uint32).tolist()))].append(int(row))
normalReceipts=[];failures=[]
for (pid,bits),sr in sorted(normalGroups.items()):
 faces=sorted({int(fi) for fi in removed for row in F[fi] if int(q[row])==pid and tuple(a['NORMAL'][row].view(np.uint32).tolist())==bits})
 total=np.zeros(3,np.float64)
 for fi in faces:total+=vectors[fi]
 length=float(np.linalg.norm(total));normal=np.zeros(3,np.float32) if length==0 else (total/length).astype(np.float32)
 dotOld=float(normal.astype(np.float64)@a['NORMAL'][sr[0]].astype(np.float64))
 if length==0:failures.append({'type':'zero_group_area_normal','physicalID':pid,'sourceRows':sr})
 if dotOld<=0:failures.append({'type':'source_normal_group_flip','physicalID':pid,'sourceRows':sr,'newDotOriginal':dotOld})
 for row in sr:attrs['NORMAL'][clones[row]]=normal
 normalReceipts.append({'physicalID':pid,'originalNormalBits':bits,'originalRows':sr,'newRows':[clones[r] for r in sr],'sourceFaceIDs':faces,'sumAreaVector':total.tolist(),'sumLength':length,'newNormal':normal.tolist(),'newDotOriginal':dotOld})
morphs=[]
for target in C.d['meshes'][0]['primitives'][0].get('targets',[]):
 morphs.append({s:np.concatenate([C.acc(ai),C.acc(ai)[rows]]) for s,ai in target.items()})
dump={'positions':attrs['POSITION'],'indices':indices,'sourceIndices':F,'sourcePhysicalPositions':U,'physicalPositions':physical,'attributeRowPhysicalIDs':np.concatenate([q,q[rows]]),'clonedSourceRows':rows,'clonedNewRows':np.arange(len(a['POSITION']),len(attrs['POSITION']),dtype=np.int64),'changedSourceFaceIDs':removed,'pathPhysicalIDs':np.array(path),'pathLengthsFloat64':lengths,'pathCumulativeFloat64':cumulative,'pathStationsFloat64':stations,'interiorPhysicalIDs':interior,'interiorStationsFloat64':np.array([u[int(i)] for i in interior]),'boundaryPhysicalIDs':np.array(boundary)}
for s,v in attrs.items():dump['attribute_'+s]=v
for i,target in enumerate(morphs):
 for s,v in target.items():dump['morph_'+str(i)+'_'+s]=v
np.savez_compressed(S/'construction.npz',**dump)
save(S/'construction-provenance.json',{'sourceSHA256':SHA,'contractSHA256':pins[str(CONTRACT)]['sha256'],'recipeSHA256':recipeSHA,'cornerProvenance':cornerRecords,'cloneRows':[{'sourceRow':r,'newRow':clones[r],'physicalID':int(q[r])} for r in rows.tolist()],'normalGroups':normalReceipts,'constructionFailures':failures,'boundaryNormals':'Literal original rows, no clone or edit','inputs':pins})
report={'status':'ONE196_DUMPED_PENDING_STATIC','attemptCount':1,'geometryGenerated':True,'GLBExported':False,'dumpSHA256':sha((S/'construction.npz').read_bytes()),'sourceFaces':len(removed),'newAccessorRows':len(rows),'interiorPhysicalIDs':len(interior),'constructionFailures':len(failures),'elapsedSeconds':time.monotonic()-start,'anonymousGBSamples':mem,'CPUThreads':2,'GPU':False,'inputPins':pins}
save(E/'build-report.json',report);save(E/'attempt.json',report);print(json.dumps(report),flush=True)
