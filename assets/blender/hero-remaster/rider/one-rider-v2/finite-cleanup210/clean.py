"""One literal duplicate collapse; preserve all distinct positions and incidences."""
from pathlib import Path
import hashlib, json, struct, time, resource, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
R=Path('/Users/raynos/projects/games/rockhop')
E=R/'docs/evidence/hero-remaster/one-rider-v2/finite-cleanup210'
D=B/'finite-cleanup210'
def pin(p):
    return {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def glb_read(p):
    b=p.read_bytes(); magic,version,size=struct.unpack_from('<III',b)
    assert (magic,version,size)==(0x46546c67,2,len(b))
    n,typ=struct.unpack_from('<II',b,12); assert typ==0x4e4f534a
    j=json.loads(b[20:20+n]); off=20+n
    n,typ=struct.unpack_from('<II',b,off); assert typ==0x004e4942
    binary=b[off+8:off+8+n]
    def acc(i):
        a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]
        assert 'byteStride' not in bv
        shape={'SCALAR':1,'VEC3':3}[a['type']]
        return np.frombuffer(binary,dtype={5125:'<u4',5126:'<f4'}[a['componentType']],count=a['count']*shape,offset=bv.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,shape).copy()
    primitive=j['meshes'][0]['primitives'][0]
    assert primitive['attributes'].keys()=={'POSITION'}
    return j,acc(primitive['attributes']['POSITION']),acc(primitive['indices']).reshape(-1,3)
def topology(P,T):
    directed=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]])
    edges,count=np.unique(np.sort(directed,axis=1),axis=0,return_counts=True)
    _,inv=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True)
    winding=np.bincount(inv,weights=np.where(directed[:,0]<directed[:,1],1,-1),minlength=len(edges))
    cross=np.cross(P[T[:,1]].astype(np.float64)-P[T[:,0]],P[T[:,2]].astype(np.float64)-P[T[:,0]])
    areas=np.linalg.norm(cross,axis=1)/2
    nc,labels=connected_components(coo_matrix((np.ones(2*len(edges)),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(P),len(P))).tocsr())
    corners=np.concatenate([np.c_[T[:,0],T[:,1],T[:,2]],np.c_[T[:,1],T[:,2],T[:,0]],np.c_[T[:,2],T[:,0],T[:,1]]])
    corners=corners[np.argsort(corners[:,0],kind='stable')]
    splits=np.r_[0,np.flatnonzero(np.diff(corners[:,0]))+1,len(corners)]
    failures=[]
    for start,end in zip(splits[:-1],splits[1:]):
        v=int(corners[start,0]); links=corners[start:end,1:]
        nodes,degrees=np.unique(links,return_counts=True)
        if np.any(degrees!=2):
            failures.append({'vertex':v,'reason':'link degree not two'});continue
        adjacency={int(x):[] for x in nodes}
        for a,b in links:
            adjacency[int(a)].append(int(b));adjacency[int(b)].append(int(a))
        seen={int(nodes[0])};todo=list(seen)
        while todo:
            for a in adjacency[todo.pop()]:
                if a not in seen:seen.add(a);todo.append(a)
        if len(seen)!=len(nodes):failures.append({'vertex':v,'reason':'disconnected link'})
    components=[]
    for i in range(nc):
        ids=np.flatnonzero(labels==i); mask=labels[T[:,0]]==i
        f=T[mask]; volume=np.einsum('ij,ij->i',P[f[:,0]].astype(np.float64),np.cross(P[f[:,1]].astype(np.float64),P[f[:,2]].astype(np.float64))).sum()/6
        components.append({'vertices':len(ids),'faces':int(mask.sum()),'bounds':[P[ids].min(0).tolist(),P[ids].max(0).tolist()],'signedVolumeNativeUnitsCubed':float(volume)})
    return {'vertices':len(P),'faces':len(T),'edges':len(edges),'boundaryEdges':int((count==1).sum()),'nonmanifoldEdges':int((count>2).sum()),'windingConflictEdges':int((winding!=0).sum()),'vertexLinkFailures':failures,'zeroAreaFaces':int((areas==0).sum()),'minimumAreaNativeUnitsSquared':float(areas.min()),'duplicateUnorderedFaceIncidences':len(T)-len(np.unique(np.sort(T,axis=1),axis=0)),'components':components}
start=time.monotonic()
src=B/'finite-native208/ancestry.npz';display=B/'finite-native208/native-display.glb'
assert pin(src)['sha256']=='48907fbbbcf1b787c07363006c86d2262e463b4f9f456c52191a7b73d4b288bb'
assert pin(display)['sha256']=='57eef332e00089296a5078d44c8e2c6963c8214aa55257aadcee5c818048923e'
z=np.load(src);P,F=z['positions'],z['faces']
j,displayP,displayF=glb_read(display)
assert np.array_equal(P,displayP) and np.array_equal(F[:,::-1],displayF)
assert np.isfinite(P).all() and P.dtype==np.float32
unique,first,inv=np.unique(P,axis=0,return_index=True,return_inverse=True)
# Source order retained. The earlier row is the duplicate pair representative.
order=np.argsort(first);representatives=first[order];uniqueToOutput=np.empty(len(order),dtype=np.int64);uniqueToOutput[order]=np.arange(len(order))
sourceRowToOutput=uniqueToOutput[inv];Q=P[representatives].copy();mapped=sourceRowToOutput[F]
areas=np.linalg.norm(np.cross(P[F[:,1]].astype(np.float64)-P[F[:,0]],P[F[:,2]].astype(np.float64)-P[F[:,0]]),axis=1)/2
removed=np.flatnonzero(areas==0);kept=np.flatnonzero(areas>0);T=mapped[kept]
assert len(P)-len(Q)==1 and removed.tolist()==[68199,68209]
assert np.array_equal(np.unique(Q,axis=0),np.unique(P,axis=0))
assert np.array_equal(Q[T],P[F[kept]])
assert np.array_equal(Q[sourceRowToOutput],P)
audit=topology(Q,T)
okay=all(audit[k]==0 for k in ('boundaryEdges','nonmanifoldEdges','windingConflictEdges','zeroAreaFaces')) and not audit['vertexLinkFailures']
report={'status':'UNACCEPTED_LITERAL_TOPOLOGY_CLEANUP' if okay else 'STOPPED_TOPOLOGY_COLLAPSE_FAILED','sourceRows':len(P),'sourceFaces':len(F),'removedFaceRows':removed.tolist(),'removedNativeFaceIDs':z['sourceFaceIDs'][removed].tolist(),'mergedRows':[34564,34565],'mergedNativeVertexIDs':z['sourceVertexIDs'][[34564,34565]].tolist(),'mergedRepresentativeRow':34564,'allDistinctPositionsExact':True,'allNondegenerateIncidencesAndMultiplicityExact':True,'allSourceFields':['POSITION only; no UV, texture, NORMAL, skin or morph field exists in source GLB'],'displayOnlyWindingReversal':True,'audit':audit,'limits':['This remains the finite diagnostic subset of a partly nonfinite decoded mesh.','The six-vertex native component is retained exactly; no semantic provenance justifies deletion.','No smoothing, remeshing, decimation, sculpt, texture, field reconstruction, rig, collision or visual acceptance.','Self-intersections and anatomically meaningful topology are not established by manifold tests.','Coordinates retain native orientation and arbitrary native units; no body/head alignment is performed.']}
if okay:
    assert not (D/'clean-native.glb').exists()
    np.savez_compressed(D/'ancestry.npz',positions=Q,faces=T,sourceRowToOutput=sourceRowToOutput,representativeSourceRows=representatives,sourceFaceRows=kept,sourceNativeVertexIDs=z['sourceVertexIDs'],sourceNativeFaceIDs=z['sourceFaceIDs'][kept],removedSourceFaceRows=removed,removedNativeFaceIDs=z['sourceFaceIDs'][removed])
    # The source has POSITION and indices only: write the same two fields directly.
    indexBytes=T[:,::-1].astype('<u4').tobytes();positionBytes=Q.astype('<f4').tobytes();binary=indexBytes+positionBytes
    j['asset']['generator']='Rockhop literal duplicate cleanup210';j['bufferViews'][0]['byteLength']=len(indexBytes);j['bufferViews'][1]['byteOffset']=len(indexBytes);j['bufferViews'][1]['byteLength']=len(positionBytes);j['buffers'][0]['byteLength']=len(binary)
    j['accessors'][0].update(count=T.size,min=[int(T.min())],max=[int(T.max())]);j['accessors'][1].update(count=len(Q),min=Q.min(0).tolist(),max=Q.max(0).tolist())
    js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
    out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    (D/'clean-native.glb').write_bytes(out)
    _,checkP,checkF=glb_read(D/'clean-native.glb')
    assert np.array_equal(checkP,Q) and np.array_equal(checkF,T[:,::-1])
    assert checkP.tobytes()==Q.astype('<f4').tobytes()
    report['exportedGLBPositionsIndicesExact']=True
report['elapsedSeconds']=time.monotonic()-start
report['peakRSSBytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
report['python']=sys.version
report['outputs']={str(p):pin(p) for p in D.iterdir() if p.is_file()}
assert pin(src)['sha256']=='48907fbbbcf1b787c07363006c86d2262e463b4f9f456c52191a7b73d4b288bb'
(E/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
