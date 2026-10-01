"""Bounded orbital retopology with actual source boundary order preserved.

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
OUT=ROOT/'rig-adapter01/body-bind18/construction01'
EVIDENCE=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind18/construction01'
OUT.mkdir(parents=True,exist_ok=True); EVIDENCE.mkdir(parents=True,exist_ok=True)
PROVENANCE_ONLY='--provenance-only' in __import__('sys').argv
assert PROVENANCE_ONLY or not (OUT/'rider.glb').exists(), 'Frozen trials are never overwritten'
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
    point=bary@v[face]
    distance=np.linalg.norm(v[face]-point,axis=1)
    if distance.min()<2e-7:return int(face[int(distance.argmin())])
    key=tuple(np.round(point,7))
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
WIDTH=.018;HEIGHT=.009;INNER_WIDTH=.022;INNER_HEIGHT=.017
output=[];origins=[];changed=[];cut_reports=[]
for fi,face in enumerate(tri):
    points=v[face]
    match=None
    inward=np.cross(points[1]-points[0],points[2]-points[0])[0]<0
    cut_width=INNER_WIDTH if inward else WIDTH
    cut_height=INNER_HEIGHT if inward else HEIGHT
    if points[:,0].min()>(.69 if inward else .72):
        for eye,cy,cz,apex in SEEDS:
            if points[:,1].min()<=cy+cut_height and points[:,1].max()>=cy-cut_height and points[:,2].min()<=cz+cut_width and points[:,2].max()>=cz-cut_width:
                match=(eye,cy,cz);break
    if match is None:output.append(face.tolist());origins.append(fi);continue
    eye,cy,cz=match
    theta=np.arange(64)*2*np.pi/64
    # Halfspace normal includes exact polygon apothem, not a true-cylinder cut.
    normals=np.c_[np.sin(theta+np.pi/64)/cut_height,np.cos(theta+np.pi/64)/cut_width]
    normalized=points[:,1:]-np.array([cy,cz])
    current=list(np.eye(3));pieces=[]
    for n in normals:
        values=[float((b@normalized)@n-np.cos(np.pi/64)) for b in current]
        outside=clip(current,values,False)
        if len(outside)>=3:pieces.append(outside)
        current=clip(current,values,True)
        if len(current)<3:break
    if len(current)<3:output.append(face.tolist());origins.append(fi);continue
    projected=np.array(current)@points
    area=sum(np.linalg.norm(np.cross(projected[j]-projected[0],projected[j+1]-projected[0]))/2 for j in range(1,len(projected)-1))
    if area<1e-14:output.append(face.tolist());origins.append(fi);continue
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
            if np.linalg.norm(np.cross(pp[1]-pp[0],pp[2]-pp[0]))/2>1e-14:output.append([center,a,b]);origins.append(fi)

# Source-edge intersections generated by subtracting planes can extend outside
# the final aperture. Split adjacent untouched faces at the same physical points.
conforming=[];conforming_origins=[]
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
for face,origin in zip(output,origins):
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
    if not modified:conforming.append(face);conforming_origins.append(origin);continue
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
        if np.linalg.norm(np.cross(pp[1]-pp[0],pp[2]-pp[0]))/2>1e-14:conforming.append([center,a,b]);conforming_origins.append(origin)
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

"""Actual native anatomical graft continuation of source-sheet clipping."""
from scipy.interpolate import RBFInterpolator
from geometry_checks import surface_clearance,topology as eye_topology,self_test
assert self_test()['pass']

NATIVE=ROOT/'rig-adapter01/anatomical-eye-donor01/standalone01'
bridge=[];graft_reports=[];rays=[]
def surface_hit(points,faces,y,z):
    xyz=points[faces];yz=xyz[:,:,1:];p=np.array([y,z])
    eligible=np.flatnonzero((yz.min(1)<=p+1e-10).all(1)&(yz.max(1)>=p-1e-10).all(1))
    a=yz[eligible,1]-yz[eligible,0];b=yz[eligible,2]-yz[eligible,0];d=p-yz[eligible,0]
    det=a[:,0]*b[:,1]-a[:,1]*b[:,0];keep=abs(det)>1e-15
    eligible=eligible[keep];a=a[keep];b=b[keep];d=d[keep];det=det[keep]
    u=(d[:,0]*b[:,1]-d[:,1]*b[:,0])/det;q=(a[:,0]*d[:,1]-a[:,1]*d[:,0])/det
    bary=np.c_[1-u-q,u,q];inside=(bary>=-1e-8).all(1)
    return None if not inside.any() else float(np.max(np.sum(bary[inside]*xyz[eligible[inside],:,0],axis=1)))

def ordered(loop,cy,cz,points):
    loop=np.array(loop);p=points[loop,1:]-[cy,cz]
    if np.sum(p[:,1]*np.roll(p[:,0],-1)-p[:,0]*np.roll(p[:,1],-1))<0:loop=loop[::-1]
    loop=np.roll(loop,-int(np.argmax(points[loop,2])))
    lengths=np.linalg.norm(np.roll(points[loop],-1,axis=0)-points[loop],axis=1)
    return loop,np.r_[0,np.cumsum(lengths[:-1])]/lengths.sum()*2*np.pi

def zipper(a,aa,b,bb):
    i=j=0;result=[]
    while i<len(a) or j<len(b):
        na=aa[(i+1)%len(a)]+(2*np.pi if i+1>=len(a) else 0) if i<len(a) else np.inf
        nb=bb[(j+1)%len(b)]+(2*np.pi if j+1>=len(b) else 0) if j<len(b) else np.inf
        if na<=nb:result.append([int(a[i%len(a)]),int(b[j%len(b)]),int(a[(i+1)%len(a)])]);i+=1
        else:result.append([int(a[i%len(a)]),int(b[j%len(b)]),int(b[(j+1)%len(b)])]);j+=1
    return np.array(result,dtype=int)

def orient_strip(strip,reference,reference_vertices):
    points=np.array(expanded['POSITION'],dtype='<f4')
    _,canonical=np.unique(points,axis=0,return_inverse=True)
    directed=set((int(a),int(b)) for f in canonical[reference] for a,b in zip(f,np.roll(f,-1)))
    physical_vertices=set(canonical[list(reference_vertices)])
    shared=[(int(a),int(b)) for f in canonical[strip] for a,b in zip(f,np.roll(f,-1)) if a in physical_vertices and b in physical_vertices]
    same=sum(edge in directed for edge in shared);opposite=sum(edge[::-1] in directed for edge in shared)
    assert same+opposite==len(shared) and (same==0 or opposite==0),'Consistent existing seam winding'
    return strip[:,::-1] if same else strip

def add_points(points,normals=None):
    indices=[]
    for i,point in enumerate(points):
        indices.append(len(expanded['POSITION']))
        for key in expanded:
            expanded[key].append({'POSITION':point,'NORMAL':normals[i] if normals is not None else [1.,0,0],
                'TEXCOORD_0':[.5,.5],'JOINTS_0':[4,0,0,0],'WEIGHTS_0':[1.,0,0,0]}[key])
    return np.array(indices)

def native_loops(quads):
    count=Counter(tuple(sorted((int(a),int(b)))) for f in quads for a,b in zip(f,np.roll(f,-1)))
    edges=[edge for edge,n in count.items() if n==1];adj=defaultdict(list)
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    assert all(len(n)==2 for n in adj.values());unseen=set(adj);result=[]
    while unseen:
        first=min(unseen);loop=[first];prev=None;cur=first
        while True:
            nxt=next(n for n in adj[cur] if n!=prev)
            if nxt==first:break
            assert nxt not in loop;loop.append(nxt);prev,cur=cur,nxt
        unseen-=set(loop);result.append(loop)
    return result

def eye_geometry(prefix,cy,cz,apex,shift=0):
    result=[]
    for suffix in ['cornea','sclera_iris']:
        mesh=next(m for m in ddoc['meshes'] if m['name']==prefix+'_'+suffix);p0=mesh['primitives'][0]
        points=array(ddoc,dbin,p0['attributes']['POSITION']).astype(float)
        offset=np.array([apex-.0152355616+shift,cy,cz-(-.033 if prefix=='R' else .033)])
        result.append((points+offset,array(ddoc,dbin,p0['indices']).reshape(-1,3)))
    return result

eye_shifts={}
for eye,cy,cz,apex in SEEDS:
    rings=[l for l in loops if np.max(abs(positions[l,1]-cy))<INNER_HEIGHT+.0001 and np.max(abs(positions[l,2]-cz))<INNER_WIDTH+.0001]
    assert len(rings)==2;rings.sort(key=lambda l:positions[l,0].mean(),reverse=True)
    front,fa=ordered(rings[0],cy,cz,positions);back,ba=ordered(rings[1],cy,cz,positions)
    native_side='R' if eye=='positiveZ' else 'L';prefix='L' if eye=='positiveZ' else 'R'
    nd=np.load(NATIVE/f'fitted-native-{native_side}-lids.npz')
    raw_native=nd['positions'].copy();np0=raw_native.copy();nq=nd['quads'];boundary=native_loops(nq)
    assert len(boundary)==2
    boundary.sort(key=lambda l:np.ptp(np0[l,1])*np.ptp(np0[l,2]),reverse=True)
    outer=boundary[0];inner=boundary[1]
    neighbors=defaultdict(set)
    for f in nq:
        for a,b in zip(f,np.roll(f,-1)):neighbors[int(a)].add(int(b));neighbors[int(b)].add(int(a))
    distances={i:0 for i in outer};fringe=set(outer)
    for depth in range(1,3):
        nxt={b for a in fringe for b in neighbors[a]}-set(distances)
        distances.update({i:depth for i in nxt});fringe=nxt
    shifts=[]
    for i in outer:
        angle=np.arctan2((np0[i,1]-cy)/HEIGHT,(np0[i,2]-cz)/WIDTH)
        yy=cy+.90*HEIGHT*np.sin(angle);zz=cz+.90*WIDTH*np.cos(angle)
        xx=surface_hit(v,tri,yy,zz);assert xx is not None
        shifts.append(np.array([xx,yy,zz])-np0[i])
    shifts=np.array(shifts)
    for i,depth in distances.items():
        if depth>=2:continue
        nearest=int(np.argmin(np.linalg.norm(raw_native[outer]-raw_native[i],axis=1)))
        np0[i]+=shifts[nearest]*(1. if depth==0 else .5)
    assert np.array_equal(np0[inner],raw_native[inner]),'Actual native anatomical aperture preserved'
    indices=add_points(np0,nd['normals']);nt=np.concatenate([nq[:,[0,1,2]],nq[:,[0,2,3]]])
    nt=indices[nt];current=np.array(expanded['POSITION'],dtype='<f4')
    outloop,oa=ordered(indices[outer],cy,cz,current);inloop,ia=ordered(indices[inner],cy,cz,current)
    join=orient_strip(zipper(front,fa,outloop,oa),output,set(front))
    wall=orient_strip(zipper(inloop,ia,back,ba),nt,set(inloop))
    local=np.concatenate([nt,join,wall]);bridge.extend(local.tolist())
    # Actual surfaces are open-backed; test their triangles rather than
    # demanding every inward wall be in front of a single corneal ray.
    candidates=[];selected=None
    tissue=current[local].astype(float)
    for depth_mm in np.arange(0.,8.0001,.25):
        shift=-float(depth_mm)/1000
        cornea,iris=eye_geometry(prefix,cy,cz,apex,shift)
        checks={}
        for category,faces in [('native_lid',nt),('front_join',join),('inward_wall',wall)]:
            for donor_category,(ep,ef) in [('cornea',cornea),('opaque_sclera_iris',iris)]:
                checks[category+'/'+donor_category]=surface_clearance(current[faces].astype(float),ep[ef],reach=.00025)
        safe=all(row['distanceLowerBoundM']>=.00010 for row in checks.values())
        visibility=[]
        for yy,zz in [(cy,cz),(cy-.002,cz),(cy+.002,cz),(cy,cz-.005),(cy,cz+.005)]:
            ix=surface_hit(*iris,yy,zz)
            gx=surface_hit(current,local,yy,zz);sx=surface_hit(positions,output,yy,zz)
            visible=ix is not None and (gx is None or ix>gx+.0001) and (sx is None or ix>sx+.0001)
            visibility.append({'y':yy,'z':zz,'irisFrontX':ix,'nativeGraftFrontX':gx,'retainedSkinFrontX':sx,'visible':visible})
        candidate={'depthShiftM':shift,'actualSurfaceChecks':checks,'apertureRays':visibility,'safe':safe,'allApertureRaysVisible':all(q['visible'] for q in visibility)}
        candidates.append(candidate)
        if safe and candidate['allApertureRaysVisible']:
            selected=candidate;break
    if selected is None:
        np.savez_compressed(OUT/'native-graft-failure.npz',positions=current,sourceTriangles=output,nativeTriangles=nt,
            frontJoinTriangles=join,inwardWallTriangles=wall,nativeSourcePositions=raw_native,nativeRegisteredPositions=np0,
            actualCorneaPositions=eye_geometry(prefix,cy,cz,apex)[0][0],actualCorneaTriangles=cornea[1],
            actualIrisPositions=eye_geometry(prefix,cy,cz,apex)[1][0],actualIrisTriangles=iris[1])
        failure={'status':'REJECTED before export; no measured surface-safe and visible fit within8mm','eye':eye,
            'sourceSHA256':hashlib.sha256(raw).hexdigest(),'candidateExported':False,'GPUWorkPerformed':False,
            'fitBoundM':.008,'clearanceRequiredM':.00010,'fitTrials':candidates,
            'donorTopology':{'cornea':eye_topology(*cornea),'opaque_sclera_iris':eye_topology(*iris)},
            'surgicalROI':{'outerHalfWidthM':WIDTH,'outerHalfHeightM':HEIGHT,'innerHalfWidthM':INNER_WIDTH,'innerHalfHeightM':INNER_HEIGHT,'innerFaceClassifier':'geometric face-normal X<0','outerMinimumXM':.72,'innerMinimumXM':.69},
            'nativeAperturePositionsExact':np.array_equal(np0[inner],raw_native[inner]),
            'limits':['Actual donor components remain open-backed; no closed sphere containment claimed.','Opaque iris and sclera are tested together as their actual shared mesh; no untested surface is dropped.','No source conservation or full export validation was reached.']}
        (EVIDENCE/'native-graft-failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        print(json.dumps({'status':failure['status'],'eye':eye,'trials':len(candidates)},indent=2));raise SystemExit(1)
    shift=selected['depthShiftM'];eye_shifts[prefix]=shift
    rays.extend([dict(eye=eye,**r) for r in selected['apertureRays']])
    graft_reports.append({'eye':eye,'selectedActualSurfaceCheck':selected,'fitTrials':candidates,
        'donorTopology':{'cornea':eye_topology(*cornea),'opaque_sclera_iris':eye_topology(*iris)}})
    graft_reports.append({'eye':eye,'nativeSide':native_side,'originalNativeQuads':len(nq),'nativeApertureVertices':len(inner),
        'nativeAperturePositionsExact':True,'outerRegistrationBandMaxGraphDepth':1,
        'maxOuterBoundaryRegistrationM':float(np.linalg.norm(shifts,axis=1).max()),
        'actualEyeDepthShiftM':shift,'exactTriangleSurfaceChecks':True,'clearanceRequiredM':.00010,
        'nativeTriangles':len(nt),'sourceJoinTriangles':len(join),'inwardWallTriangles':len(wall)})

positions=np.array(expanded['POSITION'],dtype='<f4');bridge=np.array(bridge,dtype=np.int64)
joined=np.concatenate([output,bridge]);final,_,finaldirected,_=topology(positions,joined)
assert final==before,(before,final)
oriented=Counter(map(tuple,finaldirected.tolist()));assert max(oriented.values())==1,'Joined surface winding consistent'
areas=np.linalg.norm(np.cross(positions[joined[:,1]]-positions[joined[:,0]],positions[joined[:,2]]-positions[joined[:,0]]),axis=1)/2
assert areas.min()>1e-14 and np.isfinite(positions).all()

# Freeze CPU geometry only; independent conservation and skin/normal gates
# precede any GLB export. This is the single construction, not a new model.
np.savez_compressed(OUT/'geometry-preexport.npz',positions=positions,sourceTriangles=output,graftTriangles=bridge,
    sourceTriangleProvenance=np.array(conforming_origins,dtype=np.int32),surgicallyChangedSourceFaces=np.array(changed,dtype=np.int32),
    **{'attribute_'+key:np.array(value,dtype=attrs[key].dtype) for key,value in expanded.items()})
report={'status':'UNACCEPTED CPU native graft geometry; not exported','sourceSHA256':hashlib.sha256(raw).hexdigest(),
    'body11Unchanged':source.read_bytes()==raw,'candidateExported':False,'GPUWorkPerformed':False,
    'surgicalROI':{'outerHalfWidthM':WIDTH,'outerHalfHeightM':HEIGHT,'innerHalfWidthM':INNER_WIDTH,'innerHalfHeightM':INNER_HEIGHT,
        'innerFaceClassifier':'geometric face-normal X<0','outerMinimumXM':.72,'innerMinimumXM':.69},
    'sourceTopology':before,'joinedTopology':final,'minimumJoinedTriangleAreaM2':float(areas.min()),
    'nativeGrafts':graft_reports,'apertureRays':rays,'elapsedSeconds':time.monotonic()-start,
    'limits':['Conservation, UV baking, physical normal continuity and parent appearance gates are pending before export.','No closed donor volume is assumed; actual open cornea and combined opaque sclera/iris surfaces were checked.']}
(EVIDENCE/'geometry-preexport.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['nativeGrafts','apertureRays']},indent=2))
