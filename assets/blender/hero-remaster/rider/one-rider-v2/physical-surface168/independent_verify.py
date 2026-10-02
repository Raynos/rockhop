"""Independent literal witness verifier. No contact extraction or clipping imports."""
from pathlib import Path
import hashlib,json,struct,datetime,subprocess,os,numpy as np
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=R/'docs/evidence/hero-remaster/one-rider-v2/physical-surface168';owned=O/'independent-verification.json';records={}
def read(p,expected=None,role='input'):
 p=Path(p);b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected is not None:assert h==expected,(str(p),h,expected)
 records[str(p)]={'path':str(p),'SHA256':h,'bytes':len(b),'role':role};return b
contact=json.loads(read(O/'contact-report.json',role='frozen contact claims'));assert len(contact['rows'])==16
# Fixed numerical verification tolerances, independent of the extraction's physical gap classification.
INCLUSION=1e-9;METRIC=1e-12

def glb_indices(p,expected,meshID=None,nodeName=None):
 b=read(p,expected,'source GLB topology');n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);binary=b[28+n:]
 if nodeName is not None:meshID=next(x['mesh']for x in d['nodes']if x.get('name')==nodeName)
 prim=d['meshes'][meshID]['primitives'][0];a=d['accessors'][prim['indices']];assert a['type']=='SCALAR' and 'sparse'not in a;v=d['bufferViews'][a['bufferView']]
 if 'EXT_meshopt_compression'in v.get('extensions',{}):
  assert nodeName=='bodywork','Explicit compressed bike node only'
  read(R/'src/render/hero/gltfTestUtils.ts',role='compressed topology decoder helper');read(R/'pnpm-lock.yaml',role='decoder dependency lock')
  code="import {loadRigAt} from './src/render/hero/gltfTestUtils'; import {pathToFileURL} from 'node:url'; loadRigAt(pathToFileURL("+json.dumps(str(p))+"),true).then(g=>{const o=g.scene.getObjectByName('bodywork') as any; console.log(JSON.stringify(Array.from(o.geometry.index.array)));});"
  env=dict(os.environ,UV_THREADPOOL_SIZE='2',OMP_NUM_THREADS='2');values=subprocess.check_output(['pnpm','exec','tsx','-e',code],cwd=R,env=env,text=True);return np.array(json.loads(values),dtype=int).reshape(-1,3)
 dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4'}[a['componentType']]);arr=np.ndarray((a['count'],),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize),)).copy();return arr.reshape(-1,3)

def array(base,rec,width):
 b=read(base/rec['file'],rec['sha256'],'private literal snapshot/index array');assert len(b)==rec['bytes'];return np.frombuffer(b,dtype='<f8').reshape(-1,width)

def bary2(tri,p):
 xz=tri[:,[0,2]];A=(xz[1:]-xz[0]).T;uv=np.linalg.solve(A,np.asarray(p)-xz[0]);return np.r_[1-uv.sum(),uv]

def bary3(tri,p):
 E=(tri[1:]-tri[0]).T;uv=np.linalg.solve(E.T@E,E.T@(p-tri[0]));w=np.r_[1-uv.sum(),uv];return w,float(np.linalg.norm(w@tri-p))

def plane_coeff(tri):
 # Y = ax + bz + c, solved directly. This avoids extractor cross-product height formula.
 return np.linalg.solve(np.c_[tri[:,0],tri[:,2],np.ones(3)],tri[:,1])

def inside(tri,p):
 w=bary2(tri,p);return bool(w.min()>=-INCLUSION and w.max()<=1+INCLUSION)

def unique_points(points):
 out=[]
 for p in points:
  if not any(np.linalg.norm(p-q)<METRIC for q in out):out.append(p)
 return out

def independent_overlap(A,B):
 # Intersection vertices from enclosed triangle vertices and nine edge intersections.
 # This is not the extraction's sequential clipping algorithm.
 aa=A[:,[0,2]];bb=B[:,[0,2]];points=[p.copy()for p in aa if inside(B,p)]+[p.copy()for p in bb if inside(A,p)]
 for i in range(3):
  p=aa[i];u=aa[(i+1)%3]-p
  for j in range(3):
   q=bb[j];v=bb[(j+1)%3]-q;M=np.c_[u,-v]
   if abs(np.linalg.det(M))<1e-18:continue
   t,s=np.linalg.solve(M,q-p)
   if -INCLUSION<=t<=1+INCLUSION and -INCLUSION<=s<=1+INCLUSION:points.append(p+t*u)
 points=unique_points(points);assert len(points)>=3
 pts=np.array(points);centre=pts.mean(0);return pts[np.argsort(np.arctan2(pts[:,1]-centre[1],pts[:,0]-centre[0]))]

def pointset_error(a,b):
 return float(max(max(min(np.linalg.norm(x-y)for y in b)for x in a),max(min(np.linalg.norm(x-y)for y in a)for x in b)))

def direct_triangle_plane_segment(A,B):
 # Direct 3D triangle/triangle intersection: each triangle edge with the other's plane.
 pts=[]
 for tri,other in [(A,B),(B,A)]:
  normal=np.cross(other[1]-other[0],other[2]-other[0]);d=(tri-other[0])@normal
  for i in range(3):
   k=(i+1)%3
   if d[i]*d[k]>=0:continue
   t=d[i]/(d[i]-d[k]);p=tri[i]+t*(tri[k]-tri[i]);weights,residual=bary3(other,p)
   if weights.min()>=-INCLUSION and weights.max()<=1+INCLUSION:pts.append(p)
 pts=unique_points(pts);assert len(pts)==2,pts;return pts

variants={}
bikePath=R/'public/models/bike-rookie.glb';bikeRaw=glb_indices(bikePath,'e55919d60267849358ef5e97f4731f42fac6eb2835b9998e1d146d056c0f10f7',nodeName='bodywork')
for name,relative in [('source34','rig-adapter01/body-bind34/rider.glb'),('physicalV5','garment-rebuild01/physical-v5-control157/rider.glb')]:
 expected=next(p['reportSHA256']for p in contact['proofs']if p['variant']==name);ex=json.loads(read(O/name/'report.json',expected,'frozen surface extraction report'));base=Path(ex['matricesPrivateDirectory']);bodyT=array(base,ex['bodyTriangles'],3).astype(int);bikeT=array(base,ex['bikeTriangles'],3).astype(int);assert np.array_equal(bodyT,glb_indices(B/relative,ex['sourceSHA256'],meshID=0));assert np.array_equal(bikeT,bikeRaw);assert ex['sourceSHA256']==contact['sources'][name]['sourceSHA256'];variants[name]=(ex,base,bodyT,bikeT)
rows=[];crossings=[];allBary=[];maxGapError=0;maxMinError=0;maxHeightError=0;maxPolygonError=0
for row in contact['rows']:
 name=row['variant'];ex,base,bodyT,bikeT=variants[name];snap=next(s for s in ex['snapshots']if s['i']==row['frame']);body=array(base,snap['positions'],3);bike=array(base,snap['bikePositions'],3);assert row['snapshotSource']==snap['positions']
 def verify_witness(w,label):
  A=body[bodyT[w['riderTriangleID']]];C=bike[bikeT[w['seatTriangleID']]];assert bodyT[w['riderTriangleID']].tolist()==w['riderVertexIDs'];assert np.array_equal(A,np.array(w['riderTriangleM'])) and np.array_equal(C,np.array(w['seatTriangleM']));poly=np.array(w['overlapPolygonXZ']);ownpoly=independent_overlap(A,C);pErr=pointset_error(poly,ownpoly);assert pErr<METRIC;coeffA=plane_coeff(A);coeffC=plane_coeff(C);points=[]
  for i,p in enumerate(poly):
   wa=bary2(A,p);wc=bary2(C,p);allBary.extend(wa.tolist()+wc.tolist());assert wa.min()>=-INCLUSION and wc.min()>=-INCLUSION and wa.max()<=1+INCLUSION and wc.max()<=1+INCLUSION
   ya=float(wa@A[:,1]);yc=float(wc@C[:,1]);pa=float(np.r_[p,1]@coeffA);pc=float(np.r_[p,1]@coeffC);gap=ya-yc;assert abs(gap-w['gapAtVerticesM'][i])<METRIC;assert max(abs(ya-pa),abs(yc-pc))<METRIC
   points.append({'polygonVertex':i,'XZ':p.tolist(),'riderBarycentric':wa.tolist(),'seatBarycentric':wc.tolist(),'riderHeightM':ya,'seatHeightM':yc,'independentGapM':gap,'recordedGapM':w['gapAtVerticesM'][i],'gapResidualM':gap-w['gapAtVerticesM'][i],'riderHeightPlaneResidualM':ya-pa,'seatHeightPlaneResidualM':yc-pc,'riderXZReconstructionResidualM':float(np.linalg.norm(wa@A[:,[0,2]]-p)),'seatXZReconstructionResidualM':float(np.linalg.norm(wc@C[:,[0,2]]-p))})
  gaps=np.array([p['independentGapM']for p in points]);return A,C,poly,gaps,{'label':label,'riderTriangleID':w['riderTriangleID'],'riderVertexIDs':w['riderVertexIDs'],'seatTriangleID':w['seatTriangleID'],'seatVertexIDs':bikeT[w['seatTriangleID']].tolist(),'points':points,'independentlyDerivedOverlapPolygonXZ':ownpoly.tolist(),'maximumPolygonPointsetDifferenceM':pErr,'independentMinimumGapM':float(gaps.min()),'minimumPolygonVertexID':int(gaps.argmin()),'recordedMinimumGapM':min(w['gapAtVerticesM']),'minRecordedVertexResidualM':float(gaps.min()-min(w['gapAtVerticesM'])),'projectedRiderTriangleConditionNumber':float(np.linalg.cond((A[1:,[0,2]]-A[0,[0,2]]).T)),'projectedSeatTriangleConditionNumber':float(np.linalg.cond((C[1:,[0,2]]-C[0,[0,2]]).T))}
 A,C,poly,gaps,w=verify_witness(row['minimumWitness'],'minimumWitness');minerror=w['independentMinimumGapM']-row['minimumBikeFrameYGapMm']/1000;assert abs(minerror)<METRIC;w.update({'variant':name,'frame':row['frame'],'recordedRowMinimumGapMm':row['minimumBikeFrameYGapMm'],'rowMinimumResidualM':minerror});rows.append(w)
 if row['frame']==186:
  A,C,poly,gaps,c=verify_witness(row['crossingWitness'],'crossingWitness');assert gaps.min()<0<gaps.max();ends=[]
  for i in range(len(poly)):
   k=(i+1)%len(poly)
   if gaps[i]*gaps[k]>=0:continue
   t=float(gaps[i]/(gaps[i]-gaps[k]));p=poly[i]+t*(poly[k]-poly[i]);wa=bary2(A,p);wc=bary2(C,p);ya=float(wa@A[:,1]);yc=float(wc@C[:,1]);position=np.array([p[0],ya,p[1]]);assert wa.min()>=-INCLUSION and wc.min()>=-INCLUSION;assert abs(ya-yc)<METRIC;ends.append({'overlapEdgePolygonVertexIDs':[i,k],'edgeParameter':t,'positionM':position.tolist(),'riderBarycentric':wa.tolist(),'seatBarycentric':wc.tolist(),'riderHeightM':ya,'seatHeightM':yc,'zeroGapResidualM':ya-yc})
  assert len(ends)==2;direct=direct_triangle_plane_segment(A,C);derror=pointset_error(np.array([e['positionM']for e in ends]),np.array(direct));assert derror<METRIC;c.update({'variant':name,'frame':186,'independentZeroGapEndpoints':ends,'direct3DTrianglePlaneIntersectionEndpointsM':[p.tolist()for p in direct],'maximumTwoMethodEndpointDifferenceM':derror});crossings.append(c)
for w in rows+crossings:
 maxPolygonError=max(maxPolygonError,w['maximumPolygonPointsetDifferenceM']);maxMinError=max(maxMinError,abs(w.get('rowMinimumResidualM',0)));maxGapError=max(maxGapError,max(abs(p['gapResidualM'])for p in w['points']));maxHeightError=max(maxHeightError,max(max(abs(p['riderHeightPlaneResidualM']),abs(p['seatHeightPlaneResidualM']))for p in w['points']))
assert len(crossings)==2
for p,rec in records.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==rec['SHA256']
result={'status':'INDEPENDENT_FINITE_NUMERICAL_WITNESSES_VERIFIED_UNACCEPTED_ART','frozenUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'recipe':{'path':str(Path(__file__).resolve()),'SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'method':'Literal exported source triangle topology equals extracted indices (compressed bike indices independently CPU-decoded with stock GLTFLoader/MeshoptDecoder); witness coordinates equal hashed private snapshot positions. Independent XZ barycentric solves + direct affine plane solves; separate overlap reconstruction by triangle vertex containment and 9 edge intersections. Crossing segment checked with direct 3D triangle-edge/other-plane intersection. No extractor clip/height code imported.','inputHashes':list(records.values()),'fixedNumericalVerificationTolerances':{'barycentricInclusion':INCLUSION,'metreResidual':METRIC,'note':'Fixed numerical tolerances only; scalar residuals retained and no contact/overlap thresholds changed or fitted.'},'summary':{'minimumWitnesses':len(rows),'minimumWitnessPolygonVertices':sum(len(w['points'])for w in rows),'crossingWitnessesAtFrame186':len(crossings),'minimumBarycentricScalarIncludingRounding':float(min(allBary)),'maximumBarycentricScalarIncludingRounding':float(max(allBary)),'maximumIndependentRecordedGapResidualM':maxGapError,'maximumIndependentRecordedRowMinimumResidualM':maxMinError,'maximumBarycentricVsDirectPlaneHeightResidualM':maxHeightError,'maximumIndependentOverlapPointsetDifferenceM':maxPolygonError,'maximumZeroGapEndpointResidualM':max(abs(e['zeroGapResidualM'])for c in crossings for e in c['independentZeroGapEndpoints']),'maximumIndependentEndpointTwoMethodDifferenceM':max(c['maximumTwoMethodEndpointDifferenceM']for c in crossings)},'minimumWitnesses':rows,'frame186Crossings':crossings,'limits':['This verifies all16 nominated minimumWitness polygons and their recorded row minima; it does not independently exhaust all triangle pairs to prove global-minimum search completeness.','Snapshot source extraction/played state mapping is authenticated via hashes, not re-executed by this verifier. No new playback, render or GPU surface calculation.','XZ-projected gap and transverse triangle intersection are finite geometric statements; no force/physical collision solver, continuous-time, butt-only anatomy, visible quality or contact acceptance.','Positive gaps may be legitimate riding stance clearance. No threshold fitting or source changes.']}
owned.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
