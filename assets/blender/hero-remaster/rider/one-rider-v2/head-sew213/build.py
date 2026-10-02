"""ONE bounded selective neck sew. All sources immutable; private unaccepted asset."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
import copy,hashlib,importlib.util,json,math,struct,time,traceback
from pathlib import Path
import numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');R=B/'head-sew213';E=ROOT/'docs/evidence/hero-remaster/one-rider-v2/head-sew213';A=ROOT/'assets/blender/hero-remaster/rider/one-rider-v2/head-sew213'
spec=importlib.util.spec_from_file_location('reader',ROOT/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();save=lambda p,x:Path(p).write_text(json.dumps(x,indent=2)+'\n')
inputs=[B/'finite-cleanup210/clean-native.glb',B/'finite-cleanup210/ancestry.npz',B/'source-preserving-garment185/operator/rider.glb',B/'head-join211/literal-cut211.npz',B/'head-join211/alignment211.npz',ROOT/'docs/evidence/hero-remaster/one-rider-v2/head-join211/join-contract.json',ROOT/'docs/evidence/hero-remaster/one-rider-v2/head-join211/parent-admission211.json'];pins={str(p):sha(p) for p in inputs};assert not (R/'construction.npz').exists(),'ONE trial output already exists'
started=time.monotonic();contract=json.loads(inputs[-2].read_text());admission=json.loads(inputs[-1].read_text());cap=admission['authorizedBoundaryDisplacementCapM'];assert cap==.025
c=np.load(inputs[3]);alignment=np.load(inputs[4]);M=alignment['bodyMatrix'];gbody=reader.GLB(inputs[0]);ghead=reader.GLB(inputs[2]);ancestry=np.load(inputs[1]);p=gbody.j['meshes'][0]['primitives'][0];P=gbody.array(p['attributes']['POSITION']).astype(float);F=gbody.array(p['indices']).reshape(-1,3);assert np.array_equal(F,ancestry['faces'][:,::-1]);source_faces=ancestry['sourceFaceRows'];remap=np.full(294506,-1,int);remap[source_faces]=np.arange(len(source_faces));remove=remap[c['nativeHeadRemovedFaceIDs']];split=remap[c['nativeNeckSplitFaceIDs']];assert np.all(remove>=0) and np.all(split>=0);source_row_map=ancestry['sourceRowToOutput'];edge_native=source_row_map[c['nativeOrderedBoundaryEdges']];assert np.array_equal(P[edge_native],gbody.array(p['attributes']['POSITION'])[edge_native])
N=alignment['nativeRingCanonical'];D=c['donorOuterBoundaryPositions'];I=c['donorInnerBoundaryPositions'];centre=D.mean(0);cxz=centre[[0,2]]

def cross2(a,b):return a[0]*b[1]-a[1]*b[0]
def theta(p):return float(math.atan2(p[2]-centre[2],p[0]-centre[0])%(2*math.pi))
def ray_point(poly,angle):
 xy=poly[:,[0,2]]-cxz;d=np.array([math.cos(angle),math.sin(angle)]);hit=[]
 for j in range(len(xy)):
  a=xy[j];e=xy[(j+1)%len(xy)]-a;det=cross2(d,e)
  if abs(det)<1e-14:continue
  t=cross2(a,e)/det;u=cross2(a,d)/det
  if t>0 and -1e-8<=u<=1+1e-8:hit.append((t,j,min(1,max(0,u))))
 # A ray through a literal polygon vertex touches two consecutive edges; same point.
 assert hit,'No positive radial hit';hit.sort();assert max(x[0] for x in hit)-min(x[0] for x in hit)<1e-8,'Non-star-shaped ring'
 t,j,u=hit[0];out=np.array([cxz[0]+t*d[0],centre[1],cxz[1]+t*d[1]]);return out,j,u

angles=sorted(set(theta(p) for p in np.r_[N,D]));station=[];sourceD=[];sourceN=[];station_displacement=[]
for a in angles:
 n,ni,nu=ray_point(N,a);d,di,du=ray_point(D,a);station.append(n);sourceD.append(d);sourceN.append(n);station_displacement.append(np.linalg.norm(n-d))
station=np.asarray(station);sourceD=np.asarray(sourceD);angles=np.asarray(angles);assert max(station_displacement)<=cap
# Exact existing ring coordinates at their angular station remove arithmetic seam drift.
for poly in [N]:
 for v in poly:
  k=int(np.argmin(np.abs(np.angle(np.exp(1j*(angles-theta(v)))))));assert abs(np.angle(np.exp(1j*(angles[k]-theta(v)))))<1e-10;station[k]=v

# Output attribute rows. Physical seam welding is verified from exact coordinates,
# with UV discontinuities retained as attribute aliases in a single GLTF mesh.
V=[];Normals=[];UV=[];provenance=[];faces=[];materials=[];origins=[];roles=[]
def add(v,n=None,uv=None,prov=None):
 V.append(np.asarray(v,float));Normals.append(np.asarray(n if n is not None else [0,0,0],float));UV.append(np.asarray(uv if uv is not None else [0,0],float));provenance.append(prov);return len(V)-1

def stations_between(a,b):
 aa=theta(a);bb=theta(b);delta=float(np.angle(np.exp(1j*(bb-aa))));assert abs(delta)<math.pi-.001
 t=np.angle(np.exp(1j*(angles-aa)));valid=(t/delta>1e-9)&(t/delta<1-1e-9);ids=np.flatnonzero(valid);return ids[np.argsort(t[ids]/delta)]
def nearest_station(point):
 k=int(np.argmin(np.abs(np.angle(np.exp(1j*(angles-theta(point)))))));assert np.linalg.norm(station[k][[0,2]]-point[[0,2]])<.03;return k

body_base=[]
for i,v in enumerate(P):body_base.append(add((M[:3,:3]@v+M[:3,3]),prov={'kind':'native210','row':i,'representative208row':int(ancestry['representativeSourceRows'][i])}))
body_cut_cache={};body_station_cache={}
def body_cut(a,b):
 key=tuple(sorted((int(a),int(b))))
 if key not in body_cut_cache:
  a,b=key;t=(.76-P[a,1])/(P[b,1]-P[a,1]);native=P[a]+t*(P[b]-P[a]);v=M[:3,:3]@native+M[:3,3];k=nearest_station(v);v=station[k];body_cut_cache[key]=add(v,prov={'kind':'native210-cut','edge':list(key),'alpha':float(t),'station':k})
 return body_cut_cache[key]
def body_extra(k,a,b):
 if k not in body_station_cache:body_station_cache[k]=add(station[k],prov={'kind':'native210-boundary-subdivision','station':int(k),'edgeOfClippedFace':list(map(int,[a,b]))})
 return body_station_cache[k]

# Oriented polygon clipping against height; add exact edge-interpolated rows.
def clip_triangle(indices,source_positions,above,cutfun,base):
 result=[];h=1.55 if above else .76
 for j in range(3):
  a=int(indices[j]);b=int(indices[(j+1)%3]);ina=source_positions[a,1]>h if above else source_positions[a,1]<h;inb=source_positions[b,1]>h if above else source_positions[b,1]<h
  if ina:result.append(base[a])
  if ina!=inb:result.append(cutfun(a,b))
 assert len(result) in [3,4];return result

def emit_clipped(poly,mat,origin,role,extra,outer_condition):
 # Subdivide the one cut-plane polygon edge, preserving the polygon winding.
 expanded=[]
 for j,a in enumerate(poly):
  b=poly[(j+1)%len(poly)];expanded.append(a)
  if abs(V[a][1]-1.55)<1e-9 and abs(V[b][1]-1.55)<1e-9 and outer_condition(a,b):
   for k in stations_between(V[a],V[b]):expanded.append(extra(int(k),a,b))
 # Choose an untouched above/below-plane corner, keeping nonzero fan triangles.
 off=next(j for j,x in enumerate(expanded) if abs(V[x][1]-1.55)>1e-9);expanded=expanded[off:]+expanded[:off]
 for j in range(1,len(expanded)-1):faces.append([expanded[0],expanded[j],expanded[j+1]]);materials.append(mat);origins.append(origin);roles.append(role)

remove_set=set(map(int,remove));split_set=set(map(int,split))
for ti,t in enumerate(F):
 if ti in remove_set:continue
 if ti in split_set:emit_clipped(clip_triangle(t,P,False,body_cut,body_base),0,int(source_faces[ti]),'body-cut',body_extra,lambda a,b:True)
 else:faces.append([body_base[int(x)] for x in t]);materials.append(0);origins.append(int(source_faces[ti]));roles.append('body-retained')
body_face_count=len(faces)

hp=ghead.j['meshes'][1]['primitives'][0];attrs={k:ghead.array(i) for k,i in hp['attributes'].items()};H=attrs['POSITION'].astype(float);HT=ghead.array(hp['indices']).reshape(-1,3);hbase=[];ringclass={}
# Literal physical edges classify outer/inner while preserving original UV aliases.
for label,key in [('outer','donorOuterBoundaryEdges'),('inner','donorInnerBoundaryEdges')]:
 for a,b in c[key]:ringclass[tuple(sorted((tuple(H[a]),tuple(H[b]))))]=label

def neck_field(v):
 if v[1]>=1.58:return v.copy()
 assert v[1]>=1.55-1e-9
 a=theta(v);don,_,_=ray_point(D,a);nat,_,_=ray_point(N,a);dr=np.linalg.norm(don[[0,2]]-cxz);nr=np.linalg.norm(nat[[0,2]]-cxz);q=min(1,max(0,(1.58-v[1])/.03));fade=q*q*(3-2*q);ratio=1+fade*(nr/dr-1);out=v.copy();out[[0,2]]=cxz+(v[[0,2]]-cxz)*ratio;return out
for i,v in enumerate(H):
 out=neck_field(v) if v[1]>=1.55 else v.copy();hbase.append(add(out,attrs['NORMAL'][i],attrs['TEXCOORD_0'][i],{'kind':'donor185-original','row':i,'protected':bool(v[1]>=1.58)}))
head_cut_cache={};head_cut_label={};head_station_cache={};inner_nodes={}
def head_cut(a,b):
 key=tuple(sorted((int(a),int(b))))
 if key not in head_cut_cache:
  a,b=key;t=(1.55-H[a,1])/(H[b,1]-H[a,1]);old=H[a]+t*(H[b]-H[a]);old[1]=1.55;lab=ringclass[tuple(sorted((tuple(H[a]),tuple(H[b]))))];v=neck_field(old);k=nearest_station(old)
  if lab=='outer':v=station[k]
  n=attrs['NORMAL'][a]*(1-t)+attrs['NORMAL'][b]*t;n=n/max(np.linalg.norm(n),1e-30);uv=attrs['TEXCOORD_0'][a]*(1-t)+attrs['TEXCOORD_0'][b]*t;idx=add(v,n,uv,{'kind':'donor185-cut','edge':list(key),'alpha':float(t),'sheet':lab,'sourcePosition':old.tolist(),'station':int(k) if lab=='outer' else None});head_cut_cache[key]=idx;head_cut_label[idx]=lab
  if lab=='inner':inner_nodes[tuple(old)]=idx
 return head_cut_cache[key]
def head_extra(k,a,b):
 # Interpolate original per-edge corner UVs at the angular source station.
 key=(k,a,b)
 if key not in head_station_cache:
  pa=np.asarray(provenance[a]['sourcePosition']);pb=np.asarray(provenance[b]['sourcePosition']);d,_,_=ray_point(D,float(angles[k]));t=np.dot(d-pa,pb-pa)/np.dot(pb-pa,pb-pa);assert -1e-8<=t<=1+1e-8;n=(1-t)*Normals[a]+t*Normals[b];n/=max(np.linalg.norm(n),1e-30);uv=(1-t)*UV[a]+t*UV[b];head_station_cache[key]=add(station[k],n,uv,{'kind':'donor185-boundary-subdivision','station':k,'sourceBoundaryRows':[a,b],'alpha':float(t),'sourcePosition':d.tolist()});head_cut_label[head_station_cache[key]]='outer'
 return head_station_cache[key]
for ti,t in enumerate(HT):
 lo=H[t,1].min();hi=H[t,1].max()
 if hi<1.55:continue
 if lo>1.55:faces.append([hbase[int(x)] for x in t]);materials.append(1);origins.append(ti);roles.append('head-retained' if lo>=1.58 else 'head-neck-field')
 else:emit_clipped(clip_triangle(t,H,True,head_cut,hbase),1,ti,'head-cut',head_extra,lambda a,b:head_cut_label.get(a)==head_cut_label.get(b)=='outer')
# Complete repaired mouth primitive preserved exact.
p1=ghead.j['meshes'][1]['primitives'][1];p1a={k:ghead.array(i) for k,i in p1['attributes'].items()};p1t=ghead.array(p1['indices']).reshape(-1,3);p1base=[]
for i,v in enumerate(p1a['POSITION']):p1base.append(add(v,p1a['NORMAL'][i],p1a['TEXCOORD_0'][i],{'kind':'donor185-mouth','row':i,'protected':True}))
for ti,t in enumerate(p1t):faces.append([p1base[int(x)] for x in t]);materials.append(2);origins.append(ti);roles.append('mouth-exact')
# Actual cap follows the retained inner sheet boundary winding in reverse.
PV=np.asarray(V);FT=np.asarray(faces,int);U,first,inv=np.unique(PV,axis=0,return_index=True,return_inverse=True);Q=inv[FT];ed=np.concatenate([Q[:,[0,1]],Q[:,[1,2]],Q[:,[2,0]]]);ued,ec=np.unique(np.sort(ed,axis=1),axis=0,return_counts=True);bs={tuple(x) for x in ued[ec==1]};direct=[tuple(map(int,x)) for x in ed if tuple(sorted(x)) in bs];nxt={a:b for a,b in direct};assert len(nxt)==len(direct),'Branched open boundary';loops=[];seen=set()
for start in nxt:
 if start in seen:continue
 seq=[];cur=start
 while cur not in seen:seen.add(cur);seq.append(cur);cur=nxt[cur]
 assert cur==start;loops.append(seq)
np.savez(R/'precap-partial.npz',attributePositions=np.asarray(V),attributeFaces=np.asarray(faces,np.int32),materials=np.asarray(materials,np.int8),roles=np.asarray(roles),sourceFaceOrigins=np.asarray(origins,np.int32),normals=np.asarray(Normals),uv=np.asarray(UV),physicalPositions=U,physicalFaces=Q,bodyTransform=M)
save(E/'precap-diagnostic.json',{'status':'ACTUAL_PRECAP_PREFIX_SAVED','boundaryLoopLengths':list(map(len,loops)),'boundaryEdges':len(direct),'physicalFloat64Vertices':len(U),'sourcePins':pins,'prefixReplay':'Identical geometry recipe rerun only to serialize before assertion after first process stopped; no geometry rule changes','limits':['No cap, final GLB or acceptance yet']})
print('PRECAP',json.dumps({'boundaryLoopLengths':list(map(len,loops)),'boundaryEdges':len(direct)}),flush=True)
assert len(loops)==1,('Sewn outer surface must leave ONLY inner cavity boundary',list(map(len,loops)));loop=loops[0][::-1];assert len(loop)==306,('innerBoundaryExpected306',len(loop))
# Ear clipping of the simple planar inner ring, never a centre fan.
poly=U[loop][:,[0,2]];signed=sum(cross2(poly[j],poly[(j+1)%len(poly)]) for j in range(len(poly)))/2;orientation=1 if signed>0 else -1;pending=list(range(len(loop)));cap_faces=[]
while len(pending)>3:
 found=False
 for jj,k in enumerate(pending):
  before=pending[jj-1];after=pending[(jj+1)%len(pending)];a,b,d=poly[[before,k,after]];ar=orientation*cross2(b-a,d-a)
  if ar<=1e-16:continue
  other=[x for x in pending if x not in [before,k,after]];p=poly[other];ab=b-a;bd=d-b;da=a-d;inside=(orientation*np.cross(ab,p-a)>=-1e-14)&(orientation*np.cross(bd,p-b)>=-1e-14)&(orientation*np.cross(da,p-d)>=-1e-14)
  if np.any(inside):continue
  cap_faces.append([int(first[loop[x]]) for x in [before,k,after]]);pending.pop(jj);found=True;break
 assert found,'No noncrossing positive ear exists; preserve failed prefix'
cap_faces.append([int(first[loop[x]]) for x in pending])
for t in cap_faces:faces.append(t);materials.append(1);origins.append(-1);roles.append('internal-cap')
V=np.asarray(V,np.float32);Normals=np.asarray(Normals,np.float32);UV=np.asarray(UV,np.float32);Fout=np.asarray(faces,np.int32);mat=np.asarray(materials,np.int8);origin=np.asarray(origins,np.int32);roles=np.asarray(roles)
# Physical quotient is the actual welded topology independent of UV aliases.
used=np.unique(Fout);PV,pinv=np.unique(V[used],axis=0,return_inverse=True);index=np.full(len(V),-1,np.int32);index[used]=pinv;PF=index[Fout];np.savez(R/'construction.npz',positions=PV,faces=PF,attributePositions=V,attributeNormals=Normals,attributeUV=UV,attributeFaces=Fout,attributeToPhysical=index,materials=mat,sourceFaceOrigins=origin,roles=roles,bodyTransform=M,headTransform=np.eye(4),stationAngles=angles,stationPositions=station,sourceDonorStations=sourceD,native210RemovedFaceIDs=remove,native210SplitFaceIDs=split)
(R/'attribute-provenance.json').write_text(json.dumps(provenance,separators=(',',':'))+'\n')
# Source BIN and embedded image bytes retained as exact prefix. Unrigged mesh only.
g=ghead;j=copy.deepcopy(g.j);binary=bytearray(g.bin)
def accessor(arr,ctype,typ):
 arr=np.ascontiguousarray(arr);offset=len(binary);binary.extend(arr.tobytes());binary.extend(b'\0'*((-len(binary))%4));vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':arr.nbytes});ai=len(j['accessors']);row={'bufferView':vi,'componentType':ctype,'count':len(arr),'type':typ}
 if typ=='VEC3':row['min']=arr.min(0).tolist();row['max']=arr.max(0).tolist()
 j['accessors'].append(row);return ai
# Body generated flat normals are calculated separately; approved face normals retain exact source values.
T=V[Fout[mat==0]].astype(float);vn=np.zeros_like(V,float);nn=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);np.add.at(vn,Fout[mat==0].ravel(),np.repeat(nn,3,0));lens=np.linalg.norm(vn,axis=1);body_rows=np.flatnonzero(lens>0);Normals[body_rows]=(vn[body_rows]/lens[body_rows,None]).astype(np.float32)
position_id=accessor(V,5126,'VEC3');normal_id=accessor(Normals,5126,'VEC3');uv_id=accessor(UV,5126,'VEC2');gray=len(j['materials']);j['materials'].append({'name':'UNPAINTED new body diagnostic gray','pbrMetallicRoughness':{'baseColorFactor':[.45,.45,.45,1],'metallicFactor':0,'roughnessFactor':.8}});prims=[]
for mi,material in [(0,gray),(1,hp['material']),(2,p1['material'])]:
 ids=accessor(Fout[mat==mi].astype('<u4').ravel(),5125,'SCALAR');prims.append({'attributes':{'POSITION':position_id,'NORMAL':normal_id,'TEXCOORD_0':uv_id},'indices':ids,'material':material,'mode':4})
j['meshes']=[{'name':'UNACCEPTED selective neck sew213','primitives':prims}];j['nodes']=[{'mesh':0,'name':'UNRIGGED NEW body + approved NEW head','extras':{'privateUnacceptedHeadSew213':True,'bodyUntextured':True}}];j['scenes']=[{'nodes':[0]}];j['scene']=0;j.pop('skins',None);j.pop('animations',None);j['buffers'][0]['byteLength']=len(binary);j['asset']['generator']='Rockhop bounded selective neck sew213';encoded=json.dumps(j,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);raw=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary;(R/'rider.glb').write_bytes(raw)
# Conservation checks over actual source row provenance and source-corner indices.
protected=[i for i,pv in enumerate(provenance) if pv.get('kind')=='donor185-original' and pv.get('protected')];assert all(np.array_equal(V[i],attrs['POSITION'][provenance[i]['row']]) and np.array_equal(UV[i],attrs['TEXCOORD_0'][provenance[i]['row']]) for i in protected);assert bytes(binary[:len(g.bin)])==g.bin
for path,h in pins.items():assert sha(path)==h
report={'status':'BUILT_PRIVATE_UNACCEPTED_PENDING_REST_AUDIT','inputs':pins,'bodyCanonicalTransform':M.tolist(),'donorHeadTransform':'IDENTITY','capM':cap,'observedStationDisplacementM':float(max(station_displacement)),'native208To210AncestryUsed':True,'removedNative210HeadFaces':len(remove),'splitNative210NeckFaces':len(split),'stationCount':len(station),'physicalVertices':len(PV),'faces':len(PF),'internalEarClippedCapFaces':len(cap_faces),'protectedHeadRowsExact':len(protected),'protectedMouthPrimitiveFacesExact':len(p1t),'sourceEmbeddedBINPrefixExact':True,'headGeometryUVAbove1_58Exact':True,'sourcesUnchanged':True,'seconds':time.monotonic()-started,'CPUThreads':2,'GPUJob':False,'outputs':{str(p):sha(p) for p in R.glob('*') if p.is_file()},'limits':['Body entirely unpainted gray; only liked head PBR retained','No rig, weights, game asset, appearance acceptance, deformation or contact gate','Finite-subset source qualification unchanged; short native arms remain unresolved','Rest intersections and coplanar adjacent fold audit pending; do not render as passed']};save(E/'build-report.json',report);print(json.dumps(report,indent=2))
