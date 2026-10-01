"""Check literal physical sewing across explicit native/body/glove namespaces."""
from pathlib import Path
import json,numpy as np
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/wrist-local156');OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/wrist-local156');data=np.load(ROOT/'wrist-local156.npz');f={k:data[k] for k in data.files};keys={};positions=[];weights=[]
def id_(ns,index):
 p=f['native_positions'][index] if ns==0 else f[f'source{ns-1}_POSITION'][index];w=f['native_weights19'][index] if ns==0 else f[f'source{ns-1}_weights19'][index];key=(ns,tuple(p))
 if key not in keys:keys[key]=len(keys);positions.append(p);weights.append(w)
 else:assert np.array_equal(weights[keys[key]],w)
 return keys[key]
faces=[]
for triangle in f['native_triangles']:
 faces.append([id_(0,i) for i in triangle])
for ns,sourceTriangles in [(1,f['source0_triangles'][f['source0_shoe_patch_triangle_ids']]),(2,f['source1_triangles'])]:
 for t in sourceTriangles:faces.append([id_(ns,i) for i in t])
bridgeGlobal=[]
for t in f['bridge_triangles']:
 physical=[]
 for i in t:
  ns,index,_=f['bridge_endpoint_reference'][i];j=id_(ns,index);assert np.array_equal(f['bridge_positions'][i],positions[j]);assert np.array_equal(f['bridge_weights19'][i],weights[j]);physical.append(j)
 faces.append(physical);bridgeGlobal.append(physical)
faces=np.array(faces);edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);e,count=np.unique(edges,axis=0,return_counts=True);bc={tuple(edge):int(c) for edge,c in zip(e,count)};bridgeEdges=np.unique(np.sort(np.concatenate([np.array(bridgeGlobal)[:,[0,1]],np.array(bridgeGlobal)[:,[1,2]],np.array(bridgeGlobal)[:,[2,0]]]),axis=1),axis=0);assert all(bc[tuple(edge)]==2 for edge in bridgeEdges);assert (count>2).sum()==0;assert np.all(faces[:,0]!=faces[:,1]) and np.all(faces[:,0]!=faces[:,2]) and np.all(faces[:,1]!=faces[:,2]);boundary=e[count==1];assert len(boundary)==82
report={'kind':'Virtual physical sewing verification; exported UV/normal aliases must retain these physical equivalence classes','sourceNamespace':'0native,1source body shoe patches,2source protected gloves','triangles':len(faces),'virtualPhysicalVertices':len(keys),'bridgeTriangles':len(bridgeGlobal),'allBridgeEdgesIncidentExactlyTwice':True,'allSharedPhysicalWeightsExact':True,'nonManifoldEdges':int((count>2).sum()),'remainingBoundaryEdges':len(boundary),'remainingBoundaries':'82edges belong to native collar20,shirt hem26,and jeans waist36. Separate neck/waist closure remains parent responsibility.','limits':['No actual GLB exported, normal/texture seams, selfintersection or rendered quality acceptance.','Source hand/sole attributes preserved; new transition UV endpoints are aliases with identical physical skin fields.']};(OUT/'physical-sewing-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
