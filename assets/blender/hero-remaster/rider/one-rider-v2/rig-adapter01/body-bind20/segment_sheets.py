"""One read-only connectivity/depth-seed sheet preflight; never normal-sign labels."""
from pathlib import Path
from collections import defaultdict,Counter
import hashlib,json,struct
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components,maximum_flow,breadth_first_order

ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
OUT=ROOT/'body-bind20/sheet-preflight01';OUT.mkdir(parents=True,exist_ok=True)
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind20/sheet-preflight01');EVIDENCE.mkdir(parents=True,exist_ok=True)
source=ROOT/'body-bind11/guarded-correction01/rider.glb';raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest()
assert sha=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def array(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];item=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*item),item)).copy()
p=doc['meshes'][1]['primitives'][0];v=array(p['attributes']['POSITION']).astype(float);faces=array(p['indices']).reshape(-1,3);xyz=v[faces]
physical,weld=np.unique(v.astype('<f4'),axis=0,return_inverse=True);wf=weld[faces]
mask=(xyz[:,:,0].min(1)>.68)&(xyz[:,:,1].min(1)>1.670)&(xyz[:,:,1].max(1)<1.726)&(abs(xyz[:,:,2]).max(1)<.061)
roi=np.flatnonzero(mask);index={int(fid):i for i,fid in enumerate(roi)}
edge_faces=defaultdict(list)
for fid in roi:
    for a,b in zip(wf[fid],np.roll(wf[fid],-1)):edge_faces[tuple(sorted((int(a),int(b))))].append(int(fid))
rows=[];cols=[];weights=[]
for edge,fs in edge_faces.items():
    assert len(fs)<=2
    if len(fs)==2:
        a,b=map(index.get,fs);weight=max(1,int(round(np.linalg.norm(physical[edge[1]]-physical[edge[0]])*1e6)))
        rows.extend([a,b]);cols.extend([b,a]);weights.extend([weight,weight])
graph=coo_matrix((weights,(rows,cols)),shape=(len(roi),len(roi))).tocsr()
count,component=connected_components(graph,directed=False);sizes=np.bincount(component);chosen=int(sizes.argmax());keep=np.flatnonzero(component==chosen)
excluded=roi[component!=chosen];selected_faces=roi[keep];local={int(fi):i for i,fi in enumerate(selected_faces)}
base=graph[keep][:,keep]

def ray_hits(y,z):
    yz=xyz[:,:,1:];a=yz[:,1]-yz[:,0];b=yz[:,2]-yz[:,0];d=np.array([y,z])-yz[:,0]
    det=a[:,0]*b[:,1]-a[:,1]*b[:,0];ids=np.flatnonzero(abs(det)>1e-15)
    u=(d[ids,0]*b[ids,1]-d[ids,1]*b[ids,0])/det[ids];q=(a[ids,0]*d[ids,1]-a[ids,1]*d[ids,0])/det[ids]
    bc=np.c_[1-u-q,u,q];ok=(bc>=-1e-8).all(1);ids=ids[ok];bc=bc[ok]
    xs=(bc*xyz[ids,:,0]).sum(1);order=np.argsort(-xs)
    hits=[]
    for i in order:
        if xs[i]<=.68:continue
        if hits and abs(xs[i]-hits[-1]['xM'])<1e-7:continue
        hits.append({'xM':float(xs[i]),'sourceFace':int(ids[i]),'barycentric':bc[i].tolist()})
    return hits
landmarks=[];front=set();inside=set()
for eye,cy,cz in [('positiveZ',1.6965,.032),('negativeZ',1.697,-.0332)]:
    for dy in [-.012,-.006,0,.006,.012]:
        for dz in [-.014,-.007,0,.007,.014]:
            hits=ray_hits(cy+dy,cz+dz)
            accepted=len(hits)==2 and all(h['sourceFace'] in local for h in hits) and .001<hits[0]['xM']-hits[1]['xM']<.015
            landmarks.append({'eye':eye,'yM':cy+dy,'zM':cz+dz,'hits':hits,'acceptedDepthSeed':accepted})
            if accepted:front.add(hits[0]['sourceFace']);inside.add(hits[1]['sourceFace'])
assert front and inside and not (front&inside)
# One fixed minimum cut. Edge cost is physical shared-edge length. Seed labels
# derive only ordered ray depth and measured source landmarks. No normals used.
S=len(selected_faces);T=S+1;hard=int(base.sum())+1
r,c=base.nonzero();data=base.data.tolist();rr=r.tolist();cc=c.tolist()
for fi in sorted(front):rr.append(S);cc.append(local[fi]);data.append(hard)
for fi in sorted(inside):rr.append(local[fi]);cc.append(T);data.append(hard)
network=coo_matrix((np.array(data,dtype=np.int64),(rr,cc)),shape=(T+1,T+1)).tocsr()
flow=maximum_flow(network,S,T)
residual=network-flow.flow;residual.data=(residual.data>0).astype(np.int64);residual.eliminate_zeros()
reachable=breadth_first_order(residual,S,directed=True,return_predecessors=False)
outer=np.zeros(len(selected_faces),dtype=bool);outer[reachable[reachable<S]]=True
assert all(outer[local[fi]] for fi in front) and all(not outer[local[fi]] for fi in inside)

def selected_topology(ids):
    ff=wf[ids];edges=Counter(tuple(sorted((int(a),int(b)))) for f in ff for a,b in zip(f,np.roll(f,-1)))
    adj=defaultdict(list)
    for (a,b),number in edges.items():
        if number==1:adj[a].append(b);adj[b].append(a)
    branch=[int(i) for i,ne in adj.items() if len(ne)!=2]
    face_mask=np.array([local[int(fi)] for fi in ids]);components,_=connected_components(base[face_mask][:,face_mask],directed=False)
    loops=[]
    if not branch:
        unseen=set(adj)
        while unseen:
            first=min(unseen);loop=[first];previous=None;current=first
            while True:
                nxt=next(i for i in adj[current] if i!=previous)
                if nxt==first:break
                assert nxt not in loop;loop.append(nxt);previous,current=current,nxt
            unseen-=set(loop);loops.append(loop)
    return {'faces':len(ids),'connectedComponents':int(components),'boundaryEdges':sum(n==1 for n in edges.values()),
        'nonmanifoldEdges':sum(n>2 for n in edges.values()),'nonSimpleBoundaryVertexCount':len(branch),
        'nonSimpleBoundaryVertices':[{'physicalVertex':i,'positionM':physical[i].tolist(),'degree':len(adj[i])} for i in branch],
        'simpleBoundaryLoops':[{'vertexCount':len(q),'physicalVertexIDs':q,'boundsM':[physical[q].min(0).tolist(),physical[q].max(0).tolist()]} for q in loops]}
outer_ids=selected_faces[outer];inner_ids=selected_faces[~outer]
audit={'exterior':selected_topology(outer_ids),'inward':selected_topology(inner_ids)}
coherent=all(row['connectedComponents']==1 and row['nonmanifoldEdges']==0 and row['nonSimpleBoundaryVertexCount']==0 and row['simpleBoundaryLoops'] for row in audit.values())
np.savez_compressed(OUT/'sheet-selection.npz',sourcePositions=v.astype('<f4'),sourceTriangles=faces,physicalPositions=physical,
    physicalWeld=weld,roiSourceFaces=roi,selectedComponentSourceFaces=selected_faces,exteriorSourceFaces=outer_ids,inwardSourceFaces=inner_ids,
    exteriorDepthSeedFaces=np.array(sorted(front),dtype=np.int32),inwardDepthSeedFaces=np.array(sorted(inside),dtype=np.int32))
report={'status':'PASS coherent connected source-sheet preflight; no cut performed' if coherent else 'REJECTED sheet preflight before any cut',
    'sourceSHA256':sha,'sourceUnchanged':source.read_bytes()==raw,'CPUOnly':True,'GPUWorkPerformed':False,'candidateExported':False,
    'method':'Physical exact-position welded shared-edge connectivity; ordered front-depth ray landmarks; one length-weighted seeded minimum cut',
    'normalSignClassifierUsed':False,'clipPerformed':False,'fixedPreflightROI':{'minimumXM':.68,'minimumYM':1.670,'maximumYM':1.726,'maximumAbsZM':.061},
    'ROIComponents':int(count),'ROIComponentSizes':sizes.tolist(),'ignoredOtherComponentFaces':excluded.tolist(),
    'depthSeedRayCount':sum(q['acceptedDepthSeed'] for q in landmarks),'exteriorSeedCount':len(front),'inwardSeedCount':len(inside),
    'minimumCutCostMicrometres':int(flow.flow_value),'seedCapacity':hard,'sheetTopology':audit,'sourceLandmarks':landmarks,
    'limits':['One fixed preflight; no cut-size or segmentation-parameter sweep.','A connected minimum-cut selection does not itself prove correct anatomical sheet membership; topology and depth evidence must also hold.','No native graft, atlas, normals, triangle/eye, conservation, export or motion pass is claimed.']}
(EVIDENCE/'sheet-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['sourceLandmarks','sheetTopology']},indent=2))
for name,row in audit.items():print(name,json.dumps({k:v for k,v in row.items() if k!='simpleBoundaryLoops'},indent=2))
print('coherent',coherent)
