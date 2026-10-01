"""Independent retained-source and garment namespace verification."""
from pathlib import Path
import numpy as np,json,hashlib,struct
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');REPO=Path('/Users/raynos/projects/games/rockhop');RUN=ROOT/'garment-rebuild01/shoulder-transition155';OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/shoulder-transition155'
f=np.load(RUN/'transition.npz');raw=(ROOT/'rig-adapter01/body-bind34/rider.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def acc(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 assert 'byteStride' not in v and 'sparse' not in a
 return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],width)
p=doc['meshes'][0]['primitives'][2];a=p['attributes'];J=acc(a['JOINTS_0']);V=acc(a['WEIGHTS_0']);W=np.zeros((len(J),19))
for k in range(4):W[np.arange(len(J)),J[:,k]]+=V[:,k]
checks={}
for field,key in [('POSITION','protectedHoodPositions'),('NORMAL','protectedHoodNormals'),('TEXCOORD_0','protectedHoodUV')]:np.testing.assert_array_equal(acc(a[field]),f[key]);checks[key]=True
np.testing.assert_array_equal(W,f['protectedHoodWeights']);np.testing.assert_array_equal(acc(p['indices']).reshape(-1,3),f['protectedHoodTriangles']);checks['protectedHoodWeights']=True;checks['protectedHoodTriangles']=True
r=f['protectedRingIDs'];ids=f['protectedHoodVertexIDs'][r]
for key,source in [('positions','protectedHoodPositions'),('weights','protectedHoodWeights'),('normals','protectedHoodNormals')]:np.testing.assert_array_equal(f[key][r],f[source][ids]);checks['protectedBoundary'+key.title()]=True
c=np.load(ROOT/'garment-rebuild01/cage04/fit04.npz');keep=np.ones(len(c['quads']),bool);keep[f['removedNativeQuadIDs']]=False;Q=c['quads'][keep];UV=c['uvLoops'].reshape(-1,4,2)[keep]
expectedT=np.array([q[s] for q in Q for s in [[0,1,2],[0,2,3]]]);expectedUV=np.array([uv[s] for uv in UV for s in [[0,1,2],[0,2,3]]]);np.testing.assert_array_equal(expectedT,f['triangles'][f['triangleScope']==0]);np.testing.assert_array_equal(expectedUV,f['triangleUV'][f['triangleScope']==0]);np.testing.assert_array_equal(c['weights'],f['weights'][:len(c['positions'])]);checks['retainedNativeTopologyUVAndWeights']=True
head=[]
for i,p in enumerate(doc['meshes'][1]['primitives']):
 head.append({'sourceMesh':1,'primitive':i,'attributeHashes':{k:hashlib.sha256(acc(v).tobytes()).hexdigest() for k,v in p['attributes'].items()},'indicesSHA256':hashlib.sha256(acc(p['indices']).tobytes()).hexdigest()})
report={'status':'Source conservation only; does not approve flawed shoulder geometry','sourceGLBUnchangedSHA256':hashlib.sha256(raw).hexdigest(),'checks':checks,'protectedHeadPolicy':'Head geometry is referenced unchanged from original sourceGLB; it was not reconstructed or included in the new garment NPZ. Attribute hashes pin every original head primitive.','protectedHeadPrimitives':head,'nativeOriginalVertexNamespace':{'start':0,'count':2136,'removedQuadIDsStored':200},'newSourceBoundaryAndTransitionNamespace':{'start':2136,'count':1228,'sourceBoundaryVertexIDsField':'protectedHoodVertexIDs; -1 for new/non-source vertices'},'triangleUVContract':'Kept native triangles retain exact original per-corner UVs. New transition uses a new unbaked chart. Original hood UVs are separately exact; no new texture appearance claimed.'}
(OUT/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(checks))
