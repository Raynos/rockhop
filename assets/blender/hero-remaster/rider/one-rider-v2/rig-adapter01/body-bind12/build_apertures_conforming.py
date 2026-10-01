"""One CPU-only two-sheet aperture trial; no asset appearance acceptance.

Convex 64-sided ellipse subtraction retains source attributes barycentrically.
Each clipped source triangle partitions polygon edges before center-fan
triangulation, avoiding T junctions between subtraction fragments. Existing
source binary bytes, original vertices, cheek, body, rig and atlas are retained.
"""
from pathlib import Path
from collections import Counter, defaultdict
import copy, hashlib, io, json, struct, time
import numpy as np
from PIL import Image

ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
REPO=Path('/Users/raynos/projects/games/rockhop')
OUT=ROOT/'rig-adapter01/body-bind12/construction01'
EVIDENCE=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind12/construction01'
OUT.mkdir(parents=True,exist_ok=True); EVIDENCE.mkdir(parents=True,exist_ok=True)
assert not (OUT/'rider.glb').exists(), 'Frozen trials are never overwritten'
start=time.monotonic()
def load(path):
    raw=path.read_bytes(); length=struct.unpack_from('<I',raw,12)[0]
    return raw,json.loads(raw[20:20+length]),raw[28+length:]
source=ROOT/'rig-adapter01/body-bind11/guarded-correction01/rider.glb'
donor=ROOT/'eye-donor01/guarded01/eyes.glb'
raw,doc,original=load(source); draw,ddoc,dbin=load(donor)
assert hashlib.sha256(raw).hexdigest()=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
assert hashlib.sha256(draw).hexdigest()=='c11e5273b7e8d82a94a46d46c853e0ad42e7caeb2328716bc4a5c4090170d0fb'
def array(document,binary,index):
    a=document['accessors'][index]; v=document['bufferViews'][a['bufferView']]
    lanes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    width=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],lanes),dtype=dtype,buffer=binary,
        offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',lanes*width),width)).copy()
p=doc['meshes'][1]['primitives'][0]
assert not p.get('targets'), 'Head morphs require an explicit extension'
attrs={k:array(doc,original,i) for k,i in p['attributes'].items()}
v=attrs['POSITION'].astype(float); tri=array(doc,original,p['indices']).reshape(-1,3).astype(int)
assert len(v)==61099 and len(tri)==99485
expanded={k:list(a) for k,a in attrs.items()}
new_cache={}; point_cache={}; edge_points=defaultdict(dict); vertex_edge={}
_,source_weld=np.unique(v,axis=0,return_inverse=True)
for row in v: point_cache.setdefault(tuple(np.round(row,7)),row.copy())
def vertex(face,bary):
    nearest=int(np.argmax(bary))
    if bary[nearest]>1-1e-10:return int(face[nearest])
    point=bary@v[face]; key=tuple(np.round(point,7))
    point=point_cache.setdefault(key,point.astype('<f4').astype(float))
    uv=bary@attrs['TEXCOORD_0'][face]
    normal=bary@attrs['NORMAL'][face];normal/=np.linalg.norm(normal)
    akey=(key,tuple(np.round(uv,7)),tuple(np.round(normal,4)))
    zeros=np.flatnonzero(abs(bary)<1e-9)
    edge=None
    if len(zeros)==1:
        ends=[int(source_weld[face[q]]) for q in range(3) if q!=zeros[0]]
        edge=tuple(sorted(ends));edge_points[edge][key]=point
    if akey in new_cache:
        if edge:vertex_edge[new_cache[akey]]=edge
        return new_cache[akey]
    index=len(expanded['POSITION']);new_cache[akey]=index
    if edge:vertex_edge[index]=edge
    for k in expanded:
        if k=='POSITION': value=point
        elif k=='NORMAL':value=normal
        elif k=='TEXCOORD_0':value=uv
        elif k=='JOINTS_0':value=np.array([4,0,0,0])
        elif k=='WEIGHTS_0':value=np.array([1.,0,0,0])
        else:raise AssertionError(k)
        expanded[k].append(value)
    return index

def clip(poly,values,inside):
    result=[]
    for a,b,da,db in zip(poly,poly[1:]+poly[:1],values,values[1:]+values[:1]):
        ia=da<=1e-12 if inside else da>=-1e-12
        ib=db<=1e-12 if inside else db>=-1e-12
        if ia:result.append(a)
        if ia!=ib:result.append(a+(b-a)*(da/(da-db)))
    clean=[]
    for a in result:
        if not clean or np.linalg.norm(a-clean[-1])>1e-10:clean.append(a)
    if len(clean)>1 and np.linalg.norm(clean[0]-clean[-1])<1e-10:clean.pop()
    return clean

SEEDS=[('positiveZ',1.6965,.032,.7469700990846553),('negativeZ',1.6970,-.0332,.747949309)]
output=[];changed=[];cut_reports=[]
for fi,face in enumerate(tri):
    points=v[face]
    match=None
    if points[:,0].min()>.72:
        for eye,cy,cz,apex in SEEDS:
            if points[:,1].min()<=cy+.00425 and points[:,1].max()>=cy-.00425 and points[:,2].min()<=cz+.013 and points[:,2].max()>=cz-.013:
                match=(eye,cy,cz);break
    if match is None:output.append(face.tolist());continue
    eye,cy,cz=match
    theta=np.arange(64)*2*np.pi/64
    # Halfspace normal includes exact polygon apothem, not a true-cylinder cut.
    normals=np.c_[np.sin(theta+np.pi/64)/.00425,np.cos(theta+np.pi/64)/.013]
    normalized=points[:,1:]-np.array([cy,cz])
    current=list(np.eye(3));pieces=[]
    for n in normals:
        values=[float((b@normalized)@n-np.cos(np.pi/64)) for b in current]
        outside=clip(current,values,False)
        if len(outside)>=3:pieces.append(outside)
        current=clip(current,values,True)
        if len(current)<3:break
    if len(current)<3:output.append(face.tolist());continue
    projected=np.array(current)@points
    area=sum(np.linalg.norm(np.cross(projected[j]-projected[0],projected[j+1]-projected[0]))/2 for j in range(1,len(projected)-1))
    if area<1e-14:output.append(face.tolist());continue
    changed.append(fi)
    # All fragment points are inserted into every collinear fragment edge.
    allpoints=np.array([b for poly in pieces for b in poly])
    for poly in pieces:
        boundary=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            delta=b-a;den=float(delta@delta)
            if den<1e-20:continue
            f=((allpoints-a)@delta)/den
            residual=np.linalg.norm(allpoints-(a+f[:,None]*delta),axis=1)
            candidates=allpoints[(f>=-1e-10)&(f<1-1e-10)&(residual<1e-9)]
            order=np.argsort(((candidates-a)@delta)/den)
            for value in candidates[order]:
                vi=vertex(face,value)
                if not boundary or vi!=boundary[-1]:boundary.append(vi)
        if len(boundary)>1 and boundary[0]==boundary[-1]:boundary.pop()
        if len(boundary)<3:continue
        center=vertex(face,np.mean(poly,axis=0))
        for a,b in zip(boundary,boundary[1:]+boundary[:1]):
            if len({center,a,b})<3:continue
            pp=np.array([expanded['POSITION'][q] for q in [center,a,b]])
            if np.linalg.norm(np.cross(pp[1]-pp[0],pp[2]-pp[0]))/2>1e-14:output.append([center,a,b])

# Source-edge intersections generated by subtracting planes can extend outside
# the final aperture. Split adjacent untouched faces at the same physical points.
conforming=[]
original_count=len(v)
def common_edge(a,b):
    if a<original_count and b<original_count:return tuple(sorted((int(source_weld[a]),int(source_weld[b]))))
    if a>=original_count and b>=original_count:
        return vertex_edge.get(a) if vertex_edge.get(a)==vertex_edge.get(b) else None
    new,old=(a,b) if a>=original_count else (b,a)
    edge=vertex_edge.get(new)
    return edge if edge and int(source_weld[old]) in edge else None
def interpolate_edge(a,b,point,t):
    index=len(expanded['POSITION'])
    for k in expanded:
        if k=='POSITION':value=point
        elif k=='JOINTS_0':value=np.array([4,0,0,0])
        elif k=='WEIGHTS_0':value=np.array([1.,0,0,0])
        else:
            value=(1-t)*np.array(expanded[k][a])+t*np.array(expanded[k][b])
            if k=='NORMAL':value/=np.linalg.norm(value)
        expanded[k].append(value)
    return index
for face in output:
    ring=[];modified=False
    for a,b in zip(face,face[1:]+face[:1]):
        ring.append(a);edge=common_edge(a,b)
        if not edge or edge not in edge_points:continue
        pa,pb=np.array(expanded['POSITION'][a]),np.array(expanded['POSITION'][b]);delta=pb-pa;den=delta@delta
        inserted=[]
        for point in edge_points[edge].values():
            t=float((point-pa)@delta/den)
            if 1e-5<t<1-1e-5 and np.linalg.norm(point-(pa+t*delta))<2e-7:
                inserted.append((t,point))
        for t,point in sorted(inserted,key=lambda row:row[0]):
            ring.append(interpolate_edge(a,b,point,t));modified=True
    if not modified:conforming.append(face);continue
    center=len(expanded['POSITION'])
    for k in expanded:
        if k=='JOINTS_0':value=np.array([4,0,0,0])
        elif k=='WEIGHTS_0':value=np.array([1.,0,0,0])
        else:
            value=np.mean(np.array([expanded[k][q] for q in face]),axis=0)
            if k=='NORMAL':value/=np.linalg.norm(value)
        expanded[k].append(value)
    for a,b in zip(ring,ring[1:]+ring[:1]):
        pp=np.array([expanded['POSITION'][q] for q in [center,a,b]],dtype='<f4')
        if np.linalg.norm(np.cross(pp[1]-pp[0],pp[2]-pp[0]))/2>1e-14:conforming.append([center,a,b])
positions=np.array(expanded['POSITION'],dtype='<f4'); output=np.array(conforming,dtype=np.int64)
def topology(points,faces):
    _,weld=np.unique(points,axis=0,return_inverse=True); wt=weld[faces]
    oriented=np.concatenate([wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]])
    edges,counts=np.unique(np.sort(oriented,axis=1),axis=0,return_counts=True)
    boundary=edges[counts==1];adj=defaultdict(list)
    for a,b in boundary:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
    assert all(len(n)==2 for n in adj.values()), 'Non-simple boundary'
    unseen=set(adj);loops=[]
    while unseen:
        first=min(unseen);loop=[first];previous=None;cur=first
        while True:
            nxt=next(x for x in adj[cur] if x!=previous)
            if nxt==first:break
            assert nxt not in loop
            loop.append(nxt);previous,cur=cur,nxt
        unseen-=set(loop);loops.append(loop)
    canonical=np.unique(points,axis=0)
    mapping={int(w):int(np.flatnonzero(weld==w)[0]) for loop in loops for w in loop}
    return dict(boundaryEdges=len(boundary),boundaryLoops=len(loops),nonmanifoldEdges=int(np.sum(counts>2))), [[mapping[a] for a in l] for l in loops],oriented,weld

before,_,_,_=topology(v,tri)
after,loops,directed,weld=topology(positions,output)
assert before==dict(boundaryEdges=151,boundaryLoops=4,nonmanifoldEdges=0)
if after['boundaryLoops']!=8 or after['nonmanifoldEdges']!=0:
    detail=[dict(vertices=len(l),bounds=[positions[l].min(0).tolist(),positions[l].max(0).tolist()]) for l in loops]
    (EVIDENCE/'conforming-failure.json').write_text(json.dumps(dict(status='REJECTED before export',attempt=2,topology=after,loops=detail),indent=2)+'\n')
    np.savez(OUT/'conforming-failure.npz',positions=positions,triangles=output)
assert after['boundaryLoops']==8 and after['nonmanifoldEdges']==0,after
bridge=[]
for eye,cy,cz,apex in SEEDS:
    rings=[l for l in loops if np.max(np.abs(positions[l,1]-cy))<.0044 and np.max(np.abs(positions[l,2]-cz))<.0131]
    assert len(rings)==2,(eye,len(rings))
    rings.sort(key=lambda l:float(positions[l,0].mean()),reverse=True)
    ordered=[]
    for l in rings:
        angles=np.mod(np.arctan2((positions[l,1]-cy)/.00425,(positions[l,2]-cz)/.013),2*np.pi)
        order=np.argsort(angles);ordered.append((np.array(l)[order],angles[order]))
    a,aa=ordered[0];b,bb=ordered[1];i=j=0;local=[]
    # Advance the earliest next event around the two rings, closing at 2pi.
    while i<len(a) or j<len(b):
        na=aa[(i+1)%len(a)]+(2*np.pi if i+1>=len(a) else 0) if i<len(a) else np.inf
        nb=bb[(j+1)%len(b)]+(2*np.pi if j+1>=len(b) else 0) if j<len(b) else np.inf
        if na<=nb:local.append([int(a[i%len(a)]),int(b[j%len(b)]),int(a[(i+1)%len(a)])]);i+=1
        else:local.append([int(a[i%len(a)]),int(b[j%len(b)]),int(b[(j+1)%len(b)])]);j+=1
    # Existing directed outer boundary must be traversed oppositely by tube.
    directed_set=set(map(tuple,directed.tolist()))
    same=sum((int(weld[t[2]]),int(weld[t[0]])) in directed_set for t in local if t[0] in set(a) and t[2] in set(a))
    if same:local=[t[::-1] for t in local]
    bridge.extend(local)
    cut_reports.append(dict(eye=eye,seedYZM=[cy,cz],outerVertices=len(a),innerVertices=len(b),outerXRange=positions[a,0].astype(float).tolist(),innerXRange=positions[b,0].astype(float).tolist(),tubeTriangles=len(local)))
joined=np.concatenate([output,np.array(bridge)])
final,_,finaldirected,_=topology(positions,joined)
assert final==before,(before,after,final)
area=np.linalg.norm(np.cross(positions[joined[:,1]]-positions[joined[:,0]],positions[joined[:,2]]-positions[joined[:,0]]),axis=1)/2
assert np.min(area)>1e-14,'Degenerate surface'
directed_counts=Counter(map(tuple,finaldirected.tolist()))
assert max(directed_counts.values())==1, 'Inconsistent winding'

binary=bytearray(original); result=copy.deepcopy(doc)
def append(data,target=None):
    binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(data)
    view=dict(buffer=0,byteOffset=offset,byteLength=len(data))
    if target:view['target']=target
    result['bufferViews'].append(view);return len(result['bufferViews'])-1
def put(a,kind,ctype,target=34962):
    a=np.ascontiguousarray(a); view=append(a.tobytes(),target)
    entry=dict(bufferView=view,componentType=ctype,count=len(a),type=kind)
    if kind=='VEC3':entry.update(min=a.min(0).tolist(),max=a.max(0).tolist())
    result['accessors'].append(entry);return len(result['accessors'])-1
head=result['meshes'][1]['primitives'][0]
for k,old in attrs.items():
    a=np.array(expanded[k],dtype=old.dtype)
    assert np.array_equal(a[:len(old)],old)
    oldspec=doc['accessors'][p['attributes'][k]]
    head['attributes'][k]=put(a,oldspec['type'],oldspec['componentType'])
head['indices']=put(output.astype('<u4').ravel(),'SCALAR',5125,34963)
skin=image=doc['images'][5];view=doc['bufferViews'][skin['bufferView']]
bitmap=np.array(Image.open(io.BytesIO(original[view['byteOffset']:view['byteOffset']+view['byteLength']])).convert('RGB'))
sample_points=[]
for _,cy,cz,_ in SEEDS:
    candidate=np.flatnonzero((v[:,0]>.72)&(abs(v[:,1]-cy)>.005)&(abs(v[:,1]-cy)<.008)&(abs(v[:,2]-cz)<.012))
    sample_points.extend(candidate.tolist())
uv=attrs['TEXCOORD_0'][sample_points];h,w=bitmap.shape[:2]
color=np.median(bitmap[np.clip((uv[:,1]*h).astype(int),0,h-1),np.clip((uv[:,0]*w).astype(int),0,w-1)],axis=0)/255
result['materials'].append(dict(name='New continuous eyelid tunnel skin',pbrMetallicRoughness=dict(baseColorFactor=[*color.tolist(),1],roughnessFactor=.62,metallicFactor=0),doubleSided=False))
material=len(result['materials'])-1
tube=np.array(bridge,dtype=np.int64);used=np.unique(tube);local={int(q):i for i,q in enumerate(used)}
norm=np.zeros((len(positions),3))
for t in tube:
    n=np.cross(positions[t[1]]-positions[t[0]],positions[t[2]]-positions[t[0]])
    for q in t:norm[q]+=n
norm=norm[used];norm/=np.linalg.norm(norm,axis=1)[:,None]
headweights=np.zeros((len(used),4),dtype='<f4');headweights[:,0]=1
headjoints=np.zeros((len(used),4),dtype='<u2');headjoints[:,0]=4
result['meshes'][1]['primitives'].append(dict(attributes=dict(POSITION=put(positions[used],'VEC3',5126),NORMAL=put(norm.astype('<f4'),'VEC3',5126),TEXCOORD_0=put(np.full((len(used),2),.5,dtype='<f4'),'VEC2',5126),JOINTS_0=put(headjoints,'VEC4',5123),WEIGHTS_0=put(headweights,'VEC4',5126)),indices=put(np.array([[local[int(q)] for q in t] for t in tube],dtype='<u4').ravel(),'SCALAR',5125,34963),material=material,mode=4))

# Append exact donor PNG, sampler, materials, and translated actual geometry.
image_offset=len(result['images']);texture_offset=len(result['textures']);sampler_offset=len(result['samplers']);material_offset=len(result['materials'])
for im in ddoc['images']:
    im=copy.deepcopy(im);view=ddoc['bufferViews'][im['bufferView']]
    im['bufferView']=append(dbin[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);result['images'].append(im)
result['samplers'].extend(copy.deepcopy(ddoc['samplers']))
for tex in ddoc['textures']:
    tex=copy.deepcopy(tex);tex['source']+=image_offset;tex['sampler']+=sampler_offset;result['textures'].append(tex)
for mat in ddoc['materials']:
    mat=copy.deepcopy(mat)
    if 'baseColorTexture' in mat['pbrMetallicRoughness']:mat['pbrMetallicRoughness']['baseColorTexture']['index']+=texture_offset
    result['materials'].append(mat)
eye_points=[];eye_faces=[]
for mi,mesh in enumerate(ddoc['meshes']):
    donorprim=mesh['primitives'][0]; a={k:array(ddoc,dbin,index) for k,index in donorprim['attributes'].items()}
    name=mesh['name']; seed=SEEDS[1] if name.startswith('R') else SEEDS[0]
    _,cy,cz,apex=seed
    offset=np.array([apex-.0152355616,cy,cz-(-.033 if name.startswith('R') else .033)])
    a['POSITION']=(a['POSITION']+offset).astype('<f4')
    count=len(a['POSITION']);a['JOINTS_0']=np.tile(np.array([4,0,0,0],dtype='<u2'),(count,1));a['WEIGHTS_0']=np.tile(np.array([1,0,0,0],dtype='<f4'),(count,1))
    new=copy.deepcopy(donorprim);new['attributes']={k:put(value,'VEC'+str(value.shape[1]),5123 if k=='JOINTS_0' else 5126) for k,value in a.items()}
    indices=array(ddoc,dbin,donorprim['indices']);new['indices']=put(indices.ravel(),'SCALAR',ddoc['accessors'][donorprim['indices']]['componentType'],34963);new['material']+=material_offset
    result['meshes'][1]['primitives'].append(new)
    if mi%2:eye_points.append(a['POSITION'].astype(float));eye_faces.append(indices.reshape(-1,3))
assert bytes(binary[:len(original)])==original
for field in ['nodes','skins','animations','scenes']:
    assert result[field]==doc[field],field
assert result['meshes'][0]==doc['meshes'][0] and result['meshes'][1]['primitives'][1]==doc['meshes'][1]['primitives'][1]
result['buffers'][0]['byteLength']=len(binary)
encoded=json.dumps(result,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\0')+binary
(OUT/'rider.glb').write_bytes(glb)
report=dict(status='UNACCEPTED bounded source aperture + actual CC0 donor trial; parent rendering pending',sourceSHA256=hashlib.sha256(raw).hexdigest(),donorSHA256=hashlib.sha256(draw).hexdigest(),outputSHA256=hashlib.sha256(glb).hexdigest(),output=str(OUT/'rider.glb'),elapsedSeconds=time.monotonic()-start,polygonSides=64,maxEllipseSagM=.013*(1-np.cos(np.pi/64)),changedSourceTriangles=len(changed),newHeadVertices=len(positions)-len(v),retainedOriginalVertexAttributesExact=True,originalBinaryPrefixExact=True,bodyCheekRigNodesSkinAnimationsExact=True,sourceTopology=before,cutTopology=after,joinedTopology=final,minJoinedTriangleAreaM2=float(area.min()),eyes=cut_reports,tunnelColorSRGB=color.tolist(),limits=['Manual seed placement and initial apex-aligned donor translation are feasibility only.','Tube uses sampled constant local skin; source texture outside aperture is untouched.','No rendered appearance, actual gameplay contact, neck motion or checkpoint pass claimed.'])
(EVIDENCE/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'changed-source-triangles.json').write_text(json.dumps(changed)+'\n')
print(json.dumps({k:report[k] for k in ['output','outputSHA256','elapsedSeconds','changedSourceTriangles','newHeadVertices','joinedTopology']}))
