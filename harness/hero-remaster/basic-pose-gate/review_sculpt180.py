"""Independent frozen export/donor audit and conservative triangle broadphase."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,struct
import numpy as np
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop')
E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/continuous-sculpt179'
M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/continuous-sculpt179')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((E/'manifest.json').read_text());verified=[]
for name,record in manifest['files'].items():
    p=Path(name);assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256'];verified.append(name)
def glb(p):
    b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
source=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb');j,b=glb(source);k,c=glb(M/'neutral-assembly01.glb')
assert c[:len(b)]==b and k['meshes'][1:len(j['meshes'])]==j['meshes'][1:]
assert k['meshes'][0]['primitives'][1:]==j['meshes'][0]['primitives'][1:]
for key in ['accessors','bufferViews','materials','images','textures','samplers']:assert k.get(key,[])[:len(j.get(key,[]))]==j.get(key,[])
assert not k.get('skins') and not k.get('animations') and all('skin' not in node for node in k['nodes'])
g,binary=glb(M/'shell01.glb')
def array(i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];n={'SCALAR':1,'VEC3':3}[a['type']];s=np.dtype(dt).itemsize
    return np.ndarray((a['count'],n),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',s*n),s)).copy()
q=g['meshes'][0]['primitives'][0];p=array(q['attributes']['POSITION']);p=np.column_stack((p[:,0],-p[:,2],p[:,1]));f=array(q['indices']).reshape(-1,3);p,inv=np.unique(p,axis=0,return_inverse=True);f=inv[f]
edges=Counter();directions=defaultdict(list)
for row in f:
    for a,z in zip(row,np.roll(row,-1)):
        edge=tuple(sorted((int(a),int(z))));edges[edge]+=1;directions[edge].append(a<z)
adj=defaultdict(set)
for (a,z),n in edges.items():
    if n==1:adj[a].add(z);adj[z].add(a)
seen=set();components=0
for a in adj:
    if a in seen:continue
    components+=1;todo=[a];seen.add(a)
    while todo:
        for z in adj[todo.pop()]:
            if z not in seen:seen.add(z);todo.append(z)
nonmanifold=sum(n>2 for n in edges.values());winding=sum(n==2 and directions[e][0]==directions[e][1] for e,n in edges.items())
t=p[f].astype(np.float64);area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)/2
centres=t.mean(1);radius=np.linalg.norm(t-centres[:,None,:],axis=2).max(1)
# Every overlapping triangle pair is inside its sum-of-radii sphere bound;
# global maximum radius is deliberately conservative, then exact AABBs filter.
pairs=cKDTree(centres).query_pairs(float(2*radius.max())+1e-12,output_type='ndarray');sphereCount=len(pairs)
lo=t.min(1);hi=t.max(1);mask=np.all(lo[pairs[:,0]]<=hi[pairs[:,1]]+1e-12,axis=1)&np.all(lo[pairs[:,1]]<=hi[pairs[:,0]]+1e-12,axis=1)
pairs=pairs[mask];boxCount=len(pairs);shared=(f[pairs[:,0],:,None]==f[pairs[:,1],None,:]).any(2).sum(1);pairs=pairs[shared<2];shared=shared[shared<2]
def intersects(a,z):
    result=np.zeros(len(a),dtype=bool)
    for A,B in [(a,z),(z,a)]:
        e1=B[:,1]-B[:,0];e2=B[:,2]-B[:,0]
        for edge in range(3):
            origin=A[:,edge];direction=A[:,(edge+1)%3]-origin;h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-12;safe=np.where(valid,det,1.)
            s=origin-B[:,0];u=np.einsum('ij,ij->i',s,h)/safe;q=np.cross(s,e1);v=np.einsum('ij,ij->i',direction,q)/safe;distance=np.einsum('ij,ij->i',e2,q)/safe
            result|=valid&(u>1e-7)&(u<1-1e-7)&(v>1e-7)&(v<1-1e-7)&(u+v<1-1e-7)&(distance>1e-7)&(distance<1-1e-7)
    return result
hits=[]
for start in range(0,len(pairs),50000):
    row=pairs[start:start+50000];h=intersects(t[row[:,0]],t[row[:,1]])
    hits.extend({'faces':x.tolist(),'sharedVertices':int(s)} for x,s in zip(row[h],shared[start:start+50000][h]))
counts={'vertices':len(p),'triangles':len(f),'nonmanifoldEdges':int(nonmanifold),'wrongWindingEdges':int(winding),'boundaryComponents':components,'degenerateFaces':int((area<1e-12).sum())}
assert counts=={'vertices':18996,'triangles':37604,'nonmanifoldEdges':8,'wrongWindingEdges':4,'boundaryComponents':6,'degenerateFaces':8}
(E/'parent-review.json').write_text(json.dumps({'status':'REJECTED_EXPORTED_TOPOLOGY_DONOR_JOIN_OPEN','builderFilesVerified':verified,'protectedOriginalBINHeadHoodGlovePBRPrefixesExact':True,'assemblyUnrigged':True,'actualExportExactPositionTopology':counts,'independentStrictCrossingAudit':{'method':'Conservative centre/radius cKDTree pairs, exact AABB filter, zero/one-shared strict transverse edge-triangle predicates','spherePairs':sphereCount,'aabbPairs':boxCount,'nonTwoSharedPairsTested':len(pairs),'witnesses':hits,'strictCrossings':len(hits),'limits':'Coplanar/endpoint contacts excluded; shell self-only, donor-shell/cuff sewing and anatomical shape not certified. Independent checker does not rely on Blender BVH zero-candidate result.'},'limits':'Neutral export and byte contracts only. New cuff correspondence precleanup IDs not final sewn topology. Hood/hem/glove-cuff joins, deliberate retopology, rig/weights/pose/game/contact/mobile all open.'},indent=2)+'\n')
print(json.dumps({'verifiedFiles':len(verified),'actualTopology':counts,'strictPairsTested':len(pairs),'strictCrossings':len(hits)}))
