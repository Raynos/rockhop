"""Independent source conservation; does not approve the failed yoke."""
from pathlib import Path
import numpy as np,json,struct,hashlib
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');REPO=Path('/Users/raynos/projects/games/rockhop');RUN=ROOT/'garment-rebuild01/routed-panels157';OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/routed-panels157';f=np.load(RUN/'routed-instrument.npz');raw=(ROOT/'rig-adapter01/body-bind34/rider.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def acc(i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];assert 'byteStride' not in v and 'sparse' not in a
 return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],width)
p=doc['meshes'][0]['primitives'][2];a=p['attributes'];checks={}
for field,key in [('POSITION','protectedHoodPositions'),('NORMAL','protectedHoodNormals'),('TEXCOORD_0','protectedHoodUV')]:np.testing.assert_array_equal(acc(a[field]),f[key]);checks[key]=True
np.testing.assert_array_equal(acc(p['indices']).reshape(-1,3),f['protectedHoodTriangles']);checks['protectedHoodTriangles']=True;J=acc(a['JOINTS_0']);V=acc(a['WEIGHTS_0']);W=np.zeros((len(J),19))
for k in range(4):W[np.arange(len(J)),J[:,k]]+=V[:,k]
np.testing.assert_array_equal(W,f['protectedHoodWeights']);checks['protectedHood19Weights']=True;c=np.load(ROOT/'garment-rebuild01/cage04/fit04.npz');outside=f['nativeOriginalVertexIDs'];np.testing.assert_array_equal(c['positions'][outside],f['positions'][outside]);np.testing.assert_array_equal(c['weights'][outside],f['weights'][outside]);checks['nativeOutsidePanelPositionsAndWeights']=True
keep=np.zeros(len(c['quads']),bool);keep[f['nativeRetainedQuadIDs']]=True;Q=c['quads'][keep];UV=c['uvLoops'].reshape(-1,4,2)[keep];T=np.array([q[k] for q in Q for k in [[0,1,2],[0,2,3]]]);U=np.array([uv[k] for uv in UV for k in [[0,1,2],[0,2,3]]]);np.testing.assert_array_equal(T,f['triangles'][:len(T)]);np.testing.assert_array_equal(U,f['triangleUV'][:len(T)]);checks['retainedNativeTopologyAndCornerUV']=True
head=[]
for i,p in enumerate(doc['meshes'][1]['primitives']):head.append({'primitive':i,'attributeHashes':{k:hashlib.sha256(acc(v).tobytes()).hexdigest() for k,v in p['attributes'].items()},'indicesSHA256':hashlib.sha256(acc(p['indices']).tobytes()).hexdigest()})
r={'status':'Source conservation only; rest geometry gate failed','sourceGLBSHA256':hashlib.sha256(raw).hexdigest(),'checks':checks,'headImmutableSourceReferencePrimitives':head,'namespace':'0..2135 all original native vertices, preserved as source namespace; only nativeRetainedQuadIDs are surfaced. New surface has parameterToOutputVertexIDs, newTriangleIDs and source protected307aliases mapped by protectedHoodAliases. No old native20collar participates in new surface.'}
(OUT/'source-verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(checks))
