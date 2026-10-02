"""Finite actual-state surface contact with explicit Cartesian LBS prefix."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');O=R/'docs/evidence/hero-remaster/one-rider-v2/physical-surface168'
old=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/saddle-surface165/report.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def data(base,rec,width=None):
 p=base/rec['file'];assert sha(p)==rec['sha256'];a=np.frombuffer(p.read_bytes(),dtype='<f8');return a.reshape(-1,width)if width else a
def glb(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);buf=b[28+n:]
 def acc(i):
  a=j['accessors'][i];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  if 'bufferView' in a:
   v=j['bufferViews'][a['bufferView']];z=np.ndarray((a['count'],w),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*w),dt.itemsize)).copy()
  else:z=np.zeros((a['count'],w),dtype=dt)
  if 'sparse'in a:
   sp=a['sparse'];ix=sp['indices'];val=sp['values'];iv=j['bufferViews'][ix['bufferView']];vv=j['bufferViews'][val['bufferView']];idx=np.frombuffer(buf,dtype={5121:'u1',5123:'<u2',5125:'<u4'}[ix['componentType']],count=sp['count'],offset=iv.get('byteOffset',0)+ix.get('byteOffset',0));z[idx]=np.frombuffer(buf,dtype=dt,count=sp['count']*w,offset=vv.get('byteOffset',0)+val.get('byteOffset',0)).reshape(-1,w)
  return z
 return j,acc
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def clip(poly,t):
 if cross(t[1]-t[0],t[2]-t[0])<0:t=t[[0,2,1]]
 for i in range(3):
  if len(poly)==0:break
  a,b=t[i],t[(i+1)%3];edge=b-a;result=[]
  for p,q in zip(poly,np.roll(poly,-1,axis=0)):
   dp,dq=cross(edge,p-a),cross(edge,q-a);insideP,insideQ=dp>=-1e-10,dq>=-1e-10
   if insideP:result.append(p)
   if insideP!=insideQ and abs(dp-dq)>1e-14:result.append(p+(q-p)*dp/(dp-dq))
  poly=np.asarray(result,float).reshape(-1,2)
 return poly
def height(tri,xz):
 n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);assert abs(n[1])>1e-12
 return (np.dot(n,tri[0])-n[0]*xz[:,0]-n[2]*xz[:,1])/n[1]
def contact(body,tri,ids,seat,seatIDs):
 region=body[tri[ids]];xz=region[:,:,[0,2]];lo=xz.min(1);hi=xz.max(1);minimum=np.inf;witness=None;crossing=None;pairs=negative=both=0
 for si,s in enumerate(seat):
  square=s[:,[0,2]];candidates=np.flatnonzero((lo<=square.max(0)).all(1)&(hi>=square.min(0)).all(1))
  for fi in candidates:
   poly=clip(xz[fi].copy(),square)
   if len(poly)<3:continue
   area=.5*abs(sum(cross(poly[k],poly[(k+1)%len(poly)])for k in range(len(poly))))
   if area<=1e-16:continue
   # Same unchanged finite projected saddle scope as round166.
   g=height(region[fi],poly)-height(s,poly);pairs+=1;negative+=g.min()<-1e-9;isCross=g.min()<-1e-9 and g.max()>1e-9;both+=isCross
   common={'riderTriangleID':int(ids[fi]),'riderVertexIDs':tri[ids[fi]].tolist(),'seatTriangleID':int(seatIDs[si]),'riderTriangleM':region[fi].tolist(),'seatTriangleM':s.tolist(),'overlapPolygonXZ':poly.tolist(),'gapAtVerticesM':g.tolist()}
   if g.min()<minimum:minimum=float(g.min());witness=common
   if isCross and crossing is None:crossing=common
 return {'pairs':pairs,'negativePairs':int(negative),'crossingPairs':int(both),'minimumBikeFrameYGapMm':minimum*1000,'minimumWitness':witness,'crossingWitness':crossing}
allRows=[];proofs=[];sources={};seatIDs=np.array(old['seat_triangle_ids']);snapshotFiles=[]
for variant,dirname in [('source34','source34-run02'),('physicalV5','physicalV5-run01')]:
 p=O/variant/'report.json';report=json.loads(p.read_text());base=Path(report['matricesPrivateDirectory']);assert base.name==dirname;source=Path(report['source']);played=json.loads(source.read_text());assert sha(source)==report['playedReportSHA256'];assert len(played['samples'])==480
 model=Path(played['build'])/'model-catalog.json' if 'build' in played else None
 # Source GLB is identified by the played report and the immutable extraction arguments.
 glbPath=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')/('rig-adapter01/body-bind34/rider.glb'if variant=='source34'else'garment-rebuild01/physical-v5-control157/rider.glb')
 assert sha(glbPath)==report['sourceSHA256'];j,get=glb(glbPath);prim=j['meshes'][0]['primitives'][0]
 P=data(base,report['attrs']['position'],3);W=data(base,report['attrs']['skinWeight'],4);J=data(base,report['attrs']['skinIndex'],4).astype(int);tri=data(base,report['bodyTriangles'],3).astype(int);BT=data(base,report['bikeTriangles'],3).astype(int)
 assert np.array_equal(P,get(prim['attributes']['POSITION'])) and np.array_equal(tri,get(prim['indices']).reshape(-1,3)) and np.array_equal(J,get(prim['attributes']['JOINTS_0']))
 rawW=get(prim['attributes']['WEIGHTS_0']).astype(float);expectedW=(rawW/abs(rawW).sum(1,keepdims=True)).astype('f4').astype(float);assert np.array_equal(W,expectedW)
 ids=np.flatnonzero(((P[tri][:,:,1]>.69)&(P[tri][:,:,1]<1.08)&(abs(P[tri][:,:,2])<.245)).all(1));vertices=np.unique(tri[ids]);assert len(ids)==6776
 for target in prim.get('targets',[]):assert abs(get(target['POSITION'])[vertices]).max()==0
 bodyOutput=next(r for r in report['outputs']if r['file']=='body0-joint-matrices.f64');M=data(base,bodyOutput).reshape(480,19,4,4).transpose(0,1,3,2);prefix=data(base,report['prefixOutput']).reshape(480,4,4).transpose(0,2,1);P4=np.c_[P,np.ones(len(P))];sumW=W.sum(1);maxParity=0;maxNaive=0
 for snap in report['snapshots']:
  i=snap['i'];actual=data(base,snap['positions'],3);bike=data(base,snap['bikePositions'],3);assert np.array_equal(np.array(snap['bindMatrix']).reshape(4,4).T,np.eye(4))
  naive=np.zeros((len(P),3))
  for lane in range(4):naive+=W[:,lane,None]*np.einsum('vab,vb->va',M[i,J[:,lane],:3,:],P4)
  corrected=naive+(1-sumW)[:,None]*prefix[i,:3,3]
  error=float(abs(corrected[vertices]-actual[vertices]).max());naiveError=float(abs(naive[vertices]-actual[vertices]).max());assert error<1e-12;maxParity=max(maxParity,error);maxNaive=max(maxNaive,naiveError)
  row=contact(actual,tri,ids,bike[BT[seatIDs]],seatIDs);row.update({'variant':variant,'frame':i,'tick':snap['tick'],'phase':snap['phase'],'lean':snap['lean'],'grounded':snap['grounded'],'physicalPose':snap['debug']['physicalPose'],'stateSHA256':hashlib.sha256(json.dumps(played['samples'][i]['state'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'sourceReportSHA256':sha(p),'surfaceParityM':error,'naiveFinalMatrixErrorM':naiveError,'snapshotSource':snap['positions']});allRows.append(row);snapshotFiles.append({'path':str(base/snap['positions']['file']),'sha256':snap['positions']['sha256']})
  if i in [114,186,304,426]:
   prior=next(r for r in old['rows']if r['i']==i and r['variant']==('physical34'if variant=='source34'else'physicalV5'));assert row['crossingPairs']==prior['surface_crossing_pairs'];assert abs(row['minimumBikeFrameYGapMm']-prior['minimum_bike_frame_Y_gap_mm'])<1e-9
 proofs.append({'variant':variant,'snapshots':len(report['snapshots']),'oldLiteralAllVertexDifferenceM':report['maximumLiteralPositionDifferenceM'],'correctedHipSurfaceParityM':maxParity,'naiveFinalMatrixHipDifferenceM':maxNaive,'all480WorldBonePositionErrorM':report['maximumWorldPositionErrorM'],'all480WorldQuaternionError':report['maximumQuaternionComponentError'],'all480BikeBonePositionErrorM':report['maximumBikeFramePositionErrorM'],'rawPositionIndicesAndExplicitLoaderWeightsExact':True,'hipMorphDeltasExactlyZero':True,'hipRegionTriangles':len(ids),'reportSHA256':sha(p),'prefixFile':str(base/report['prefixOutput']['file']),'prefixSHA256':report['prefixOutput']['sha256']})
 sources[variant]={'sourceSHA256':report['sourceSHA256'],'playedReportSHA256':report['playedReportSHA256'],'compiledRuntimeSHA256':report['compiledRuntimeSHA256']}
for i in [35,114,186,304,426,445,446,447]:
 a,b=[next(r for r in allRows if r['frame']==i and r['variant']==v)for v in ['source34','physicalV5']];assert a['stateSHA256']==b['stateSHA256'] and a['minimumBikeFrameYGapMm']==b['minimumBikeFrameYGapMm'] and a['crossingPairs']==b['crossingPairs']
result={'status':'FINITE_ACTUAL_STATE_CPU_CONTACT_UNACCEPTED','sources':sources,'proofs':proofs,'rows':allRows,'snapshotFiles':snapshotFiles,'method':'Actual getVertexPosition on frozen riding states, compared with exact recorded bone transforms and old literal dumps. Independent Cartesian LBS includes explicit outer translation once; no fitted prefix. Projected saddle triangles unchanged from166.','limits':['No new browser pixels, GPU float-shader surface parity, continuous collision, force or anatomy/device pass.','Finite8surface snapshots each; all480bone/prefix frames verified, not all480contact surfaces.','Rest-defined region may include upper thighs/folded clothes; no butt-only claim.','Positive gaps can be valid stance clearance; do not require universal seat contact.']}
(O/'contact-report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'proofs':proofs,'rows':[{k:r[k]for k in ['variant','frame','lean','grounded','minimumBikeFrameYGapMm','crossingPairs']}for r in allRows]}))
