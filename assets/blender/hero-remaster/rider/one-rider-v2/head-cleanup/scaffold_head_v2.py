"""ONE bounded scaffold correction: dense skin fit and sewn compact scalp.

CPU Blender only; original sources/trial1 stay frozen. No UV/PBR bake.
"""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--scaffold',required=True);ap.add_argument('--dense',required=True)
ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out)
out.mkdir(parents=True,exist_ok=True)
if (out/'head.glb').exists():raise RuntimeError('Frozen correction exists')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={p:sha(p) for p in [a.scaffold,a.dense]};start=time.monotonic()
def clip(v,f,d):
    inside=d<=0;counts=inside[f].sum(1);parts=[];cross=[]
    kept=[f[counts==3]]
    for n in (1,2):
        tri=f[counts==n];mask=inside[tri]
        pivot=np.argmax(mask if n==1 else ~mask,axis=1)
        tri=np.take_along_axis(tri,(pivot[:,None]+np.arange(3))%3,axis=1)
        cross.append(np.stack((tri[:,[0,1]],tri[:,[0,2]]),axis=1).reshape(-1,2))
        parts.append((n,tri))
    edges,inv=np.unique(np.sort(np.concatenate(cross),axis=1),axis=0,return_inverse=True)
    t=d[edges[:,0]]/(d[edges[:,0]]-d[edges[:,1]])
    vv=v[edges[:,0]]+t[:,None]*(v[edges[:,1]]-v[edges[:,0]])
    offset=0
    for n,tri in parts:
        idx=inv[offset:offset+2*len(tri)].reshape(-1,2)+len(v);offset+=2*len(tri)
        x,y=idx.T
        if n==1:kept.append(np.stack((tri[:,0],x,y),axis=1))
        else:
            kept.append(np.stack((x,tri[:,1],tri[:,2]),axis=1))
            kept.append(np.stack((x,tri[:,2],y),axis=1))
    vv=np.vstack((v,vv));ff=np.vstack(kept);used,mapping=np.unique(ff,return_inverse=True)
    return vv[used],mapping.reshape(-1,3)
def topology(v,f):
    directed=np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]))
    edges,first,inv,counts=np.unique(np.sort(directed,axis=1),axis=0,
        return_index=True,return_inverse=True,return_counts=True)
    return edges,counts,directed[first]
def loops_from_boundary(edges):
    neighbors={}
    for x,y in edges:
        neighbors.setdefault(int(x),[]).append(int(y));neighbors.setdefault(int(y),[]).append(int(x))
    if any(len(x)!=2 for x in neighbors.values()):raise RuntimeError('Boundary is not simple; stop correction')
    done=set();loops=[]
    for start in neighbors:
        if start in done:continue
        loop=[start];prev=None;cur=start
        while True:
            nxt=next(x for x in neighbors[cur] if x!=prev)
            if nxt==start:break
            if nxt in loop:raise RuntimeError('Invalid boundary cycle')
            loop.append(nxt);prev,cur=cur,nxt
        done.update(loop);loops.append(loop)
    return loops
bpy.ops.wm.read_factory_settings(use_empty=True)
p=np.load(a.scaffold);v=p['vertices'].astype(np.float64);f=p['faces']
theta=np.arctan2(v[:,0],v[:,2]+.025);cosine=np.cos(theta)
height=np.where(cosine>=0,.13+.06*cosine,.13+.275*cosine)
v,f=clip(v,f,v[:,1]-height)
v,f=clip(v,f,-.31-v[:,1])
e,c,directed=topology(v,f)
if np.any(c>2):raise RuntimeError('Scalp surgery produced nonmanifold edges')
loops=loops_from_boundary(e[c==1])
scalp_loops=[x for x in loops if np.mean(v[x,1])>-.25]
base_loops=[x for x in loops if np.mean(v[x,1])<=-.25]
if len(scalp_loops)!=1 or len(base_loops)!=1:
    (out/'failed-preflight.json').write_text(json.dumps(dict(scalpLoops=len(scalp_loops),baseLoops=len(base_loops),loopSizes=[len(x) for x in loops]),indent=2)+'\n')
    raise RuntimeError('Expected one actual scalp and one base contour; stop')
loop=scalp_loops[0];boundary_size=len(loop)
# Match orientation to source cut boundary; new cap shares the actual vertices.
lookup={tuple(sorted(x)):tuple(x) for x in directed[c==1]}
if lookup[tuple(sorted(loop[:2]))]!=tuple(loop[:2]):loop=list(reversed(loop))
angles=np.unwrap(np.arctan2(v[loop,0],v[loop,2]+.025))
direction=1 if angles[-1]-angles[0]>0 else -1
uniform=angles[0]+direction*np.arange(boundary_size)*2*math.pi/boundary_size
# Scalp follows a compact adult skull ellipse, not the source curly envelope.
cap_top=.345;cy=.035;ry=.31;rx=.218;rz=.245
def scalp_points(ang,y):
    factor=np.sqrt(np.maximum(0,1-((y-cy)/ry)**2))
    return np.stack((rx*factor*np.sin(ang),y,-.025+rz*factor*np.cos(ang)),axis=1)
old_boundary=v[loop].copy()
v[loop]=scalp_points(angles,old_boundary[:,1])
cap_vertices=[];cap_faces=[];previous=np.array(loop)
for ring in range(1,25):
    t=ring/25
    ring_angles=(1-t)*angles+t*uniform
    y=(1-t)*old_boundary[:,1]+t*cap_top
    vv=scalp_points(ring_angles,y)
    ids=np.arange(len(v)+len(cap_vertices),len(v)+len(cap_vertices)+boundary_size)
    cap_vertices.extend(vv)
    for j,x in enumerate(previous):
        k=(j+1)%boundary_size
        cap_faces.extend(((previous[k],x,ids[j]),(previous[k],ids[j],ids[k])))
    previous=ids
apex=len(v)+len(cap_vertices);cap_vertices.append([0,cap_top,-.025])
for j,x in enumerate(previous):cap_faces.append((previous[(j+1)%boundary_size],x,apex))
v=np.vstack((v,cap_vertices));f=np.vstack((f,cap_faces))
# Native -> canonical Blender conversion.
canon=v[:,[0,2,1]].copy();canon[:,1]*=-1
mesh=bpy.data.meshes.new('Scaffold surgical compact head')
mesh.from_pydata(canon.tolist(),[],f.tolist());mesh.update()
clean=bpy.data.objects.new('UNACCEPTED scaffold attempt2',mesh);bpy.context.collection.objects.link(clean)
bm=bmesh.new();bm.from_mesh(mesh)
def skin(co):
    x,y,z=co;front=-y
    return abs(x)<.185 and front>.085 and -.12<z<.205 and (z>-.025 or abs(x)<.095)
edges=[edge for edge in bm.edges if all(skin(x.co) for x in edge.verts)]
bmesh.ops.subdivide_edges(bm,edges=edges,cuts=2,use_grid_fill=True)
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bm.to_mesh(mesh);bm.free();mesh.update()
# Dense high-resolution target: retained before export processing.
p=np.load(a.dense);raw=p['vertices'];dense_faces=p['faces']
dense_v=raw[:,[0,2,1]].copy();dense_v[:,1]*=-1
target=bpy.data.meshes.new('Retained dense source target')
target.vertices.add(len(dense_v));target.vertices.foreach_set('co',dense_v.ravel())
target.loops.add(dense_faces.size);target.loops.foreach_set('vertex_index',dense_faces.ravel())
target.polygons.add(len(dense_faces));target.polygons.foreach_set('loop_start',np.arange(len(dense_faces),dtype=np.int32)*3)
target.polygons.foreach_set('loop_total',np.full(len(dense_faces),3,dtype=np.int32));target.update()
obj=bpy.data.objects.new('Dense fitting target ONLY',target);bpy.context.collection.objects.link(obj)
bpy.context.view_layer.update();bvh=BVHTree.FromObject(obj,bpy.context.evaluated_depsgraph_get())
projected=[];rejected=0
for vertex in mesh.vertices:
    if not skin(vertex.co):continue
    hit,normal,idx,distance=bvh.find_nearest(vertex.co,.006)
    if hit is None:rejected+=1;continue
    # Bounded fit avoids faraway curl/dust capture; source skin mask excludes beard.
    if distance>.004:rejected+=1;continue
    vertex.co=hit;projected.append(float(distance))
bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(target)
# Preserve source folded ears. Smooth beard only, holding lip and jaw silhouette.
bm=bmesh.new();bm.from_mesh(mesh)
beard=[x for x in bm.verts if -.14<x.co.z<-.03 and -x.co.y>.13
       and not (abs(x.co.x)<.10 and x.co.z>-.085)]
original={x:x.co.copy() for x in beard}
for _ in range(3):bmesh.ops.smooth_vert(bm,verts=beard,factor=.25,use_axis_x=True,use_axis_y=True,use_axis_z=True)
for vertex in beard:
    delta=vertex.co-original[vertex]
    if delta.length>.004:vertex.co=original[vertex]+delta.normalized()*.004
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
for poly in mesh.polygons:poly.use_smooth=True
mat=bpy.data.materials.new('Neutral gray geometry only');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.42,.42,.42,1)
bsdf.inputs['Roughness'].default_value=.65;mesh.materials.append(mat)
bpy.context.view_layer.objects.active=clean;clean.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'head.glb'),export_format='GLB',use_selection=True,export_yup=True)
verts=np.array([x.co[:] for x in mesh.vertices]);tri=np.array([x.vertices[:] for x in mesh.polygons],dtype=np.int32)
native=verts[:,[0,2,1]].copy();native[:,2]*=-1
np.savez(out/'head.npz',vertices=native.astype(np.float32),faces=tri)
e,c,_=topology(native,tri)
report=dict(status='UNACCEPTED second corrective scaffold trial; no bake',sources=sources,
            sourcesAfter={p:sha(p) for p in sources},scriptSHA256=sha(__file__),
            vertices=len(native),faces=len(tri),boundaryEdges=int(np.sum(c==1)),
            nonmanifoldEdges=int(np.sum(c>2)),scalpSeamVertices=boundary_size,
            selectiveSubdivision=dict(cuts=2,selectedEdges=len(edges)),
            boundedDenseFit=dict(projectedVertices=len(projected),rejectedVertices=rejected,
                maximumNativeDistance=max(projected,default=0),
                percentileNativeDistance=np.percentile(projected,[50,95,99]).tolist() if projected else []),
            compactSkull=dict(topNativeY=cap_top,xRadius=rx,zRadius=rz,yRadius=ry),
            beard=dict(smoothedVertices=len(beard),iterations=3,factor=.25,maxNativeDisplacement=.004),
            wallSeconds=time.monotonic()-start,
            limits=['Reduced mesh is only repaired topology scaffolding, not dense original.',
                    'Actual cap uses scaffold contour shared vertices, no overlap shell.',
                    'Folded ears retained from scaffold; visual review required after cleanup.',
                    'No UV/PBR bake, neck join, rig, contacts or game-readiness pass.'])
assert sources==report['sourcesAfter']
(out/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
