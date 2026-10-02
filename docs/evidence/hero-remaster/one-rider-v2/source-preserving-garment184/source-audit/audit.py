"""Read-only original C19 rest quotient topology and conservative strict crossings."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,json,struct,hashlib,time,subprocess,re,numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment184/source-audit';S=B/'source-preserving-garment184/source-audit';start=time.monotonic();pins={};sha=lambda b:hashlib.sha256(b).hexdigest();attempt=json.loads((O/'attempt.json').read_text());assert attempt['status']=='REGISTERED_READ_ONLY_BEFORE_RUN'
def pin(p):
 p=Path(p);b=p.read_bytes();pins[str(p)]={'path':str(p),'SHA256':sha(b),'bytes':len(b)};return b
mem=[]
def memory():
 text=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',text).group(1));n=int(re.search(r'Anonymous pages:\s+(\d+)',text).group(1));gb=page*n/1e9;mem.append({'elapsedSeconds':time.monotonic()-start,'anonymousGB':gb});assert gb<70,'Own CPU job stops when shared anonymous memory exceeds70GB';return gb
memory();reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py';tree=ast.parse(pin(reader).decode());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='GLB');env={'Path':Path,'json':json,'struct':struct,'np':np,'Rotation':Rotation,'sha':sha};exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),env);GLB=env['GLB'];source=Path(attempt['source']);C=GLB(source,attempt['sourceSHA256']);pin(source);pin(R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-boundaries181/report.json');pin(R/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/hoodie-repair02/qa-lane/uv-lower01/inherited-neck-rest-crossings.json');pin(R/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/hoodie-repair02/shape-lane/volume-lane/source-embedding23/continuous-shell-handoff.json')
parts=[];attrs=[];offset=0;fo=0;pp=[];ff=[];primitive=[];local=[]
for pi in range(3):
 a,f=C.primitive(0,pi);attrs.append(a);pp.append(a['POSITION']);ff.append(f+offset);offset+=len(a['POSITION']);primitive.extend([pi]*len(f));local.extend(range(len(f)));parts.append((a['POSITION'],f));fo+=len(f)
P=np.concatenate(pp);F=np.concatenate(ff);primitive=np.array(primitive);local=np.array(local);ref=np.unique(F);U,rv=np.unique(P[ref],axis=0,return_inverse=True);maprow=np.full(len(P),-1,dtype=int);maprow[ref]=rv;phys=maprow[F];T=P[F].astype(float);centre=T.mean(1);radius=np.linalg.norm(T-centre[:,None,:],axis=2).max(1);lo=T.min(1);hi=T.max(1);cross=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);area=np.linalg.norm(cross,axis=1)/2
edge=defaultdict(list);uf=np.arange(len(U))
def root(i):
 while uf[i]!=i:uf[i]=uf[uf[i]];i=uf[i]
 return i
for fi,t in enumerate(phys):
 for k in range(3):
  a,b=map(int,[t[k],t[(k+1)%3]]);edge[tuple(sorted([a,b]))].append((fi,a<b));ra,rb=root(a),root(b);uf[rb]=ra
components=Counter(root(i)for i in range(len(U)));bad=[e for e,v in edge.items()if len(v)>2];wrong=[e for e,v in edge.items()if len(v)==2 and v[0][1]==v[1][1]];boundary=[e for e,v in edge.items()if len(v)==1];deg=np.flatnonzero(area<1e-12)
# Geometric witness bands are diagnostic labels, not semantic garment ownership.
def region(fi):
 pi=int(primitive[fi]);x,y,z=centre[fi];z=abs(z)
 if pi==1:return 'source_glove'
 if pi==2:return 'source_hood'
 if .69<y<1.08 and z<.245:return 'lower_hip_upper_leg_window'
 if 1.10<y<1.40 and .16<z<.31:return 'lateral_underarm_window'
 if 1.28<y<1.50 and z<.24:return 'shoulder_upper_chest_window'
 if 1.00<y<1.37 and z<=.18:return 'central_torso_window'
 if .7<y<1.28 and z>=.245:return 'arm_distal_window'
 return 'other_source_body'
def face(fi):
 pi=int(primitive[fi]);li=int(local[fi]);return {'sourceMesh':0,'sourcePrimitive':pi,'sourceFace':li,'sourceVertexIDs':parts[pi][1][li].tolist(),'exactPositionPhysicalIDs':phys[fi].tolist(),'sourceFloat32Positions':T[fi].tolist(),'geometricRegion':region(fi),'areaM2':float(area[fi])}
# Fixed strict interior test identical in purpose but independently evaluated on original source only.
EPS=1e-7;DET=1e-12

def strict(A,B):
 hit=np.zeros(len(A),bool);first=[None]*len(A)
 for rev in [False,True]:
  aa,bb=(B,A)if rev else(A,B);e1=bb[:,1]-bb[:,0];e2=bb[:,2]-bb[:,0]
  for k in range(3):
   d=aa[:,(k+1)%3]-aa[:,k];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);valid=abs(det)>DET;den=np.where(valid,det,1);s=aa[:,k]-bb[:,0];u=np.einsum('ij,ij->i',s,h)/den;q=np.cross(s,e1);v=np.einsum('ij,ij->i',d,q)/den;t=np.einsum('ij,ij->i',e2,q)/den;now=valid&(u>EPS)&(v>EPS)&(u+v<1-EPS)&(t>EPS)&(t<1-EPS)
   for i in np.flatnonzero(now&~hit):first[i]={'edgeOwner':'B'if rev else'A','edgeVertexLanes':[k,(k+1)%3],'edgeParameter':float(t[i]),'oppositeTriangleBarycentric':[float(1-u[i]-v[i]),float(u[i]),float(v[i])],'intersectionPositionM':(aa[i,k]+t[i]*d[i]).tolist(),'determinantM3':float(det[i])}
   hit|=now
 return hit,first
# Unit-positive transverse witness and disjoint witness, independent of source claim.
a=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]]);b=np.array([[[.2,.2,-1],[.2,.2,1],[.8,.2,0.]]]);assert strict(a,b)[0][0]and not strict(a,b+[2,0,0])[0][0]
tree=cKDTree(centre);rmax=float(radius.max());counts=Counter();classCounts=Counter();regions=Counter();witnesses=[];pairRows=[];coplanar=0;lastCheck=0
for begin in range(0,len(T),256):
 assert time.monotonic()-start<11.5*60,'Own12minute job bound'
 if time.monotonic()-lastCheck>15:memory();lastCheck=time.monotonic()
 neigh=tree.query_ball_point(centre[begin:begin+256],radius[begin:begin+256]+rmax+1e-12,workers=2)
 ii=[];jj=[];shared=[]
 for off,neighbors in enumerate(neigh):
  i=begin+off;js=np.array([j for j in neighbors if j>i],dtype=int)
  if not len(js):continue
  # Scope body-self/body-vs-glove/body-vs-hood plus separate inherited hood-self.
  scope=((primitive[i]==0)&np.isin(primitive[js],[0,1,2]))|((primitive[i]==2)&(primitive[js]==2));js=js[scope]
  if not len(js):continue
  close=np.linalg.norm(centre[js]-centre[i],axis=1)<=radius[js]+radius[i]+1e-12;js=js[close];box=(hi[i]>=lo[js]-1e-12).all(1)&(lo[i]<=hi[js]+1e-12).all(1);js=js[box]
  for j in js:
   s=len(set(phys[i])&set(phys[j]));label=f'{primitive[i]}:{primitive[j]}';counts[label+' AABB_allShared']+=1
   if s<2:ii.append(i);jj.append(int(j));shared.append(s)
   else:counts[label+' excluded2plusShared']+=1
 if not ii:continue
 ii=np.array(ii);jj=np.array(jj);shared=np.array(shared);A=T[ii];BB=T[jj];h,fir=strict(A,BB)
 n1=cross[ii];n2=cross[jj];l1=np.linalg.norm(n1,axis=1);l2=np.linalg.norm(n2,axis=1);u1=np.divide(n1,l1[:,None],out=np.zeros_like(n1),where=l1[:,None]>1e-14);u2=np.divide(n2,l2[:,None],out=np.zeros_like(n2),where=l2[:,None]>1e-14);cop=(np.linalg.norm(np.cross(u1,u2),axis=1)<1e-8)&(abs(np.einsum('ij,ij->i',BB[:,0]-A[:,0],u1))<1e-8);coplanar+=int(cop.sum())
 for i,j,s in zip(ii,jj,shared):counts[f'{primitive[i]}:{primitive[j]} strictCandidates']+=1
 for index in np.flatnonzero(h):
  i,j=int(ii[index]),int(jj[index]);s=int(shared[index]);label=f'{primitive[i]}:{primitive[j]}';classCounts[label+f' shared{s}']+=1;regions[' / '.join(sorted([region(i),region(j)]))]+=1;pairRows.append([i,j,s]);witnesses.append({'pairID':len(witnesses),'physicalSharedVertices':s,'A':face(i),'B':face(j),'strictInteriorWitness':fir[index]})
memory();np.savez_compressed(S/'strict-source-rest-pairs.npz',globalSourceFacePairs=np.array(pairRows,dtype=int).reshape(-1,3),sourcePrimitivePerGlobalFace=primitive,sourceLocalFaceIDs=local);(S/'all-strict-witnesses.json').write_text(json.dumps(witnesses,separators=(',',':'))+'\n')
# Compact literal geometric/topological evidence with full witnesses in private immutable namespace.
result={'status':'COMPLETED_READ_ONLY_ORIGINAL_C19_REST_DIAGNOSTIC_UNACCEPTED_ART','sourceSHA256':C.h,'seconds':time.monotonic()-start,'sourceOnlyEvidence':'All tested faces come directly from raw original C19 mesh0 p0/p1/p2. No V7/tube/cage/inserted candidate faces were loaded. C19 assembly history is not reconstructed; user-described4shoulder inserts cannot be assigned to original source without literal matching evidence.','scope':'Original bodyp0self, bodyp0vsoriginalglovesp1 andhoodp2; separate hoodp2self also reported. Head/cheek/gloveself/glovehood contacts not exhaustively tested.','physicalReferencedVertices':len(U),'facesByPrimitive':Counter(primitive.tolist()),'topology':{'sourceAreaBelow1e12Faces':len(deg),'sourceDegenerateWitnesses':[face(int(i))for i in deg[:10]],'combinedPhysicalNonmanifoldEdges':len(bad),'combinedPhysicalWrongWindingEdges':len(wrong),'combinedPhysicalBoundaryEdges':len(boundary),'componentPhysicalVertexCountsDescending':sorted(components.values(),reverse=True),'nonmanifoldWitnesses':[{'physicalEdge':list(e),'positions':U[list(e)].tolist(),'incidentSourceFaces':[face(i)for i,d in edge[e]]}for e in bad[:6]],'wrongWindingWitnesses':[{'physicalEdge':list(e),'positions':U[list(e)].tolist(),'incidentSourceFaces':[face(i)for i,d in edge[e]]}for e in wrong[:6]]},'strictCrossings':{'conservativeBroadphase':'Triangle centre-radius sphere test from cKDTree radius_i+maxradius, then exact radius_i+radius_j and all3AABB axes with1e-12margin. Every retained pair tested; no selfBVH overlap inference.','fixedNarrowPhase':{'determinantM3':DET,'strictBarycentricAndSegmentParameter':EPS},'candidateCounts':dict(counts),'strictCountsPrimitiveSharedClass':dict(classCounts),'regionPairCounts':dict(regions),'totalStrictPairs':len(witnesses),'coplanarCandidatesUnclassified':coplanar,'literalWitnesses':witnesses[:25],'firstWitnessByRegionPair':[next(w for w in witnesses if ' / '.join(sorted([w['A']['geometricRegion'],w['B']['geometricRegion']]))==label)for label in regions]},'memory':mem,'inputHashes':list(pins.values()),'privateOutputs':[{'path':str(p),'SHA256':sha(p.read_bytes()),'bytes':p.stat().st_size}for p in S.glob('*')],'recipeSHA256':sha(Path(__file__).read_bytes()),'limits':['Geometric region windows are explicitly diagnostic, not certified garment ownership/anatomy. All original indices, sourcefloat32positions/UV/PBR/head/neck/hood/gloves/lower stay untouched.','Strict tests exclude coplanar overlap and endpoint/tangent-only contacts; >=2shared physical vertices are excluded. Source folds and thickness can still be wrong without counted strict pairs.','No render or moving pose; strict rest crossing is not perceived damage severity, anatomical acceptance, motion clearance, physical support, weights or rig readiness.','No repair, source reshaping, new export, GPU, nativeBlender, browser or other model workload.']}
for p,x in pins.items():assert sha(Path(p).read_bytes())==x['SHA256']
(O/'report.json').write_text(json.dumps(result,indent=2)+'\n');attempt.update(status='COMPLETED_READ_ONLY_DIAGNOSTIC',seconds=result['seconds'],diagnosticFamilyTrialFailure=False,reportSHA256=sha((O/'report.json').read_bytes()));(O/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n');print(json.dumps({'seconds':result['seconds'],'topology':{k:v for k,v in result['topology'].items()if 'Witnesses'not in k},'strict':dict(classCounts),'regionPairs':dict(regions),'coplanar':coplanar,'maxAnonymousGB':max(x['anonymousGB']for x in mem)}))
