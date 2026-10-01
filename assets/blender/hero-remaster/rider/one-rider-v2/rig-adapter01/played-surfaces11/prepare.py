"""Immutable body11/native-source correspondence and actual contact ROIs; CPU only."""
from pathlib import Path
import json, struct, hashlib
import numpy as np
from scipy.spatial import cKDTree
repo=Path('/Users/raynos/projects/games/rockhop')
base=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11'
source=base/'body-bind11/guarded-correction01/rider.glb'
raw=source.read_bytes(); n=struct.unpack_from('<I',raw,12)[0]; doc=json.loads(raw[20:20+n]); binary=raw[28+n:]
def attr(i):
 a=doc['accessors'][i]; dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]; lanes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]; width=np.dtype(dtype).itemsize
 result=np.zeros((a['count'],lanes),dtype=dtype)
 if 'bufferView' in a:
  v=doc['bufferViews'][a['bufferView']]; result=np.ndarray((a['count'],lanes),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*lanes),width)).copy()
 if 'sparse' in a:
  s=a['sparse'];iv=doc['bufferViews'][s['indices']['bufferView']];vv=doc['bufferViews'][s['values']['bufferView']];indexdtype={5121:'u1',5123:'<u2',5125:'<u4'}[s['indices']['componentType']];indices=np.frombuffer(binary,dtype=indexdtype,count=s['count'],offset=iv.get('byteOffset',0)+s['indices'].get('byteOffset',0));values=np.frombuffer(binary,dtype=dtype,count=s['count']*lanes,offset=vv.get('byteOffset',0)+s['values'].get('byteOffset',0)).reshape(-1,lanes);result[indices]=values
 return result
prims=doc['meshes'][0]['primitives']; positions=[attr(p['attributes']['POSITION']) for p in prims]; handpos=positions[1]; tree=cKDTree(handpos); weightmap=json.loads((out.parent/'native-landmarks/native-weight-transfer-map.json').read_text()); hands=[]
actualHandTriangles=attr(prims[1]['indices']).ravel().reshape(-1,3)
for native, runtime, suffix in [('L','R',''),('R','L','/R')]:
 p=base/('native-grip03'+suffix)/'native-held-shape.npz'; d=np.load(p); rest=d['sourcePositions']; target=np.stack([.65-rest[:,1]*1.015,rest[:,2]*1.015,-rest[:,0]*1.015],1); distances,ids=tree.query(target)
 assert distances.max()<5e-7 and len(set(ids))==1668
 aliasDistance,alias=cKDTree(handpos[ids]).query(handpos); valid=aliasDistance<1e-8
 # glTF can split coincident vertices at normal/UV seams. Any alias used for
 # actual triangles must have identical skin/morph data to the sampled vertex.
 for accessorIndex in [prims[1]['attributes']['JOINTS_0'],prims[1]['attributes']['WEIGHTS_0']]+[t['POSITION'] for t in prims[1].get('targets',[])]:
  a=attr(accessorIndex); assert np.max(np.abs(a[valid].astype(float)-a[ids[alias[valid]]].astype(float)))<1e-8
 exported=actualHandTriangles[np.all(valid[actualHandTriangles],axis=1)]; actualTriangles=alias[exported]
 assert len(actualTriangles)>3000
 row=next(x for x in weightmap['matches'] if x['nativeSide']==native)
 fingers={str(f):[i for i,gs in enumerate(row['nativeWeights']) if sum(w for name,w in gs if name.startswith(f'finger{f}-') and name.endswith('.'+native))>.5] for f in range(1,6)}
 # Finger surface groups use native skin influence, including dorsal/palmar faces;
 # they do not falsely call a dorsal nearest point a palmar pad contact.
 fingerweights=np.array([sum(w for name,w in gs if name.startswith('finger') and name.endswith('.'+native)) for gs in row['nativeWeights']]); fixed=np.flatnonzero(fingerweights<.02)
 landmarks=json.loads((out.parent/'native-landmarks/report.json').read_text())['hands']; landmark=next(h for h in landmarks if h['nativeAnatomicalSide']==native)
 bones=json.loads((out.parent/'native-landmarks/native-bones.json').read_text())['bones']; transform=np.array(landmark['sourceArmatureToBody']); normal=-np.array(landmark['sourceCanonicalNormalMapped']); normal/=np.linalg.norm(normal); pads={}
 for finger in range(1,6):
  patch=[]
  for joint in range(1,4):
   name=f'finger{finger}-{joint}.{native}'; weight=np.array([sum(w for n,w in gs if n==name) for gs in row['nativeWeights']]); mask=weight>.45
   head=np.einsum('ij,j->i',transform,np.r_[bones[name]['headLocal'],1])[:3]; tail=np.einsum('ij,j->i',transform,np.r_[bones[name]['tailLocal'],1])[:3]; axis=tail-head
   u=np.clip(np.einsum('vi,i->v',rest-head,axis)/np.dot(axis,axis),0,1); palmar=np.einsum('vi,i->v',rest-head-u[:,None]*axis,normal); patch.extend(np.flatnonzero(mask&(palmar>=np.quantile(palmar[mask],.55))).tolist())
  pads[str(finger)]=sorted(set(patch))
 hands.append({'side':runtime,'nativeSide':native,'meshName':'Protected_body_NEW_hood_joined_garment_1','sourceVertices':ids.tolist(),'nativeCompleteVertexIds':d['sourceCompleteVertexIds'].tolist(),'triangles':actualTriangles.tolist(),'actualExportedTriangleSourceVertices':exported.tolist(),'triangleProvenance':'Literal GLB primitive indices, coincident UV/normal vertex aliases require identical skin/morph buffers','fingerSurfaceGroups':fingers,'palmarPadGroups':pads,'fixedPalmAndWristSurface':fixed.tolist(),'maximumSourceCorrespondenceErrorM':float(distances.max()),'nativeNPZSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'bikeMeshName':'handlebar'})
feet=[]; p=positions[0]; tri=attr(prims[0]['indices']).ravel().reshape(-1,3)
for side,sign in [('L',1),('R',-1)]:
 ids=np.flatnonzero((p[:,1]<.0021*1.015)&(p[:,2]*sign>0)); assert len(ids)>30; idsset=set(ids); selected=np.array([t for t in tri if set(t)<=idsset]); index={int(v):i for i,v in enumerate(ids)}
 feet.append({'side':side,'meshName':'Protected_body_NEW_hood_joined_garment','sourceVertices':ids.tolist(),'triangles':[[index[int(v)] for v in t] for t in selected],'sourceBounds':{'min':p[ids].min(0).tolist(),'max':p[ids].max(0).tolist()},'bikeMeshName':'pegs'})
manifest={'source':str(source),'sourceSHA256':hashlib.sha256(raw).hexdigest(),'hands':hands,'feet':feet,'limits':['Whole finger surface groups are native influence selections, not anatomically certified palmar pads.','Feet use literal lowest 2.1mm source vertices and their complete triangles; low shoe walls excluded.','Closest vertex-to-triangle distances do not prove zero whole-triangle intersection.','No geometry, rig, materials or source buffers are modified.']}
(out/'source-roi.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'hands':[(h['side'],len(h['sourceVertices']),h['maximumSourceCorrespondenceErrorM']) for h in hands],'feet':[(f['side'],len(f['sourceVertices']),len(f['triangles'])) for f in feet],'sourceSHA256':manifest['sourceSHA256']}))
