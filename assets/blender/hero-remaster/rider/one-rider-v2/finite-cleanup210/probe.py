"""Read-only source topology inspection before the one literal cleanup trial."""
import json, hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/finite-cleanup210')
z = np.load(B/'finite-native208/ancestry.npz')
P,F = z['positions'],z['faces']
_,first,inverse,count = np.unique(P,axis=0,return_index=True,return_inverse=True,return_counts=True)
aliases = [np.flatnonzero(inverse==i).tolist() for i in np.flatnonzero(count>1)]
areas = np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)/2
zero = np.flatnonzero(areas==0)
edges = np.unique(np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1),axis=0)
nc,labels = connected_components(coo_matrix((np.ones(2*len(edges)),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(P),len(P))).tocsr())
components=[]
for i in range(nc):
    ids=np.flatnonzero(labels==i); faceids=np.flatnonzero(labels[F[:,0]]==i)
    rec={'vertices':len(ids),'faces':len(faceids),'bounds':[P[ids].min(0).tolist(),P[ids].max(0).tolist()]}
    if len(ids)<100:
        rec.update(vertexRows=ids.tolist(),nativeVertexIDs=z['sourceVertexIDs'][ids].tolist(),positions=P[ids].tolist(),faceRows=faceids.tolist(),nativeFaceIDs=z['sourceFaceIDs'][faceids].tolist(),faceIndices=F[faceids].tolist())
    components.append(rec)
report={'sourceSHA256':hashlib.sha256((B/'finite-native208/ancestry.npz').read_bytes()).hexdigest(),'aliasGroups':[{'rows':g,'nativeVertexIDs':z['sourceVertexIDs'][g].tolist(),'position':P[g[0]].tolist()} for g in aliases],'zeroAreaFaces':[{'row':int(i),'nativeFaceID':int(z['sourceFaceIDs'][i]),'indices':F[i].tolist(),'nativeVertexIDs':z['sourceVertexIDs'][F[i]].tolist(),'positions':P[F[i]].tolist(),'physicalIndices':inverse[F[i]].tolist()} for i in zero],'components':components,'policy':'Retain the tiny component exactly. Only merge literal equal positions and remove proven zero-area incidences. No field or anatomy inference.'}
(E/'source-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
