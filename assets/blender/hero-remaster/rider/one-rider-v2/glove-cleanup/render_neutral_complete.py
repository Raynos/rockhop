"""Complete neutral polygon export and display; no anatomy or posing changes."""
import hashlib,json,math
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SOURCE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy')
RUN=SOURCE/'display-complete'
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete')
RUN.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'report.json').exists():raise RuntimeError('Frozen neutral display exists')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources={str(SOURCE/f'neutral-hand-{s}.npz'):sha(SOURCE/f'neutral-hand-{s}.npz') for s in ['L','R']}
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'neutral-anatomical-hands.blend'))
complete={}
for side in ['L','R']:
    original=bpy.data.objects[f'NEW neutral anatomical hand {side}']
    old=np.load(SOURCE/f'neutral-hand-{side}.npz')
    vertices=np.array([v.co[:] for v in original.data.vertices])
    assert np.allclose(vertices,old['vertices'],atol=1e-8,rtol=0)
    faces=[list(p.vertices) for p in original.data.polygons]
    assert len(faces)==1656
    offsets=np.cumsum([0]+[len(f) for f in faces])
    payload={key:old[key] for key in old.files}
    payload['polygonIndices']=np.array([i for face in faces for i in face],dtype=np.int32)
    payload['polygonOffsets']=np.array(offsets,dtype=np.int32)
    path=RUN/f'neutral-complete-{side}.npz';np.savez(path,**payload)
    complete[side]={'path':str(path),'sha256':sha(path),'faces':faces,'vertices':vertices.tolist()}
for o in list(bpy.context.scene.objects):
    if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
mat=bpy.data.materials.get('Neutral MODEL anatomy gray')
objects=[];metrics=[]
for side in ['L','R']:
    data=np.load(complete[side]['path']);v=data['vertices'];f=complete[side]['faces']
    mesh=bpy.data.meshes.new(f'Frozen neutral {side} canonical cage');mesh.from_pydata(v.tolist(),[],f);mesh.update();mesh.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(mesh);topology={'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldBeyondWrist':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)};assert topology=={'boundaryEdges':22,'nonmanifoldBeyondWrist':0};bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    for p in mesh.polygons:p.use_smooth=True
    o=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(o)
    for col,name in enumerate(data['nativeBoneNames']):
        g=o.vertex_groups.new(name=str(name))
        for vi in np.flatnonzero(data['nativeBoneWeights'][:,col]>0):g.add([int(vi)],float(data['nativeBoneWeights'][vi,col]),'REPLACE')
    sub=o.modifiers.new('Non-destructive neutral display smoothing','SUBSURF');sub.levels=1;sub.render_levels=1
    objects.append((side,o));metrics.append({'side':side,'sourceNPZSHA256':sources[str(SOURCE/f'neutral-hand-{side}.npz')],'vertices':len(v),'faces':len(f),'shapeKeys':False,'topology':topology,'completeNPZ':{'path':complete[side]['path'],'sha256':complete[side]['sha256']},'nativeWeightSums':[float(data['nativeBoneWeights'].sum(1).min()),float(data['nativeBoneWeights'].sum(1).max())]})
scene=bpy.context.scene;cam=scene.camera;cam.data.ortho_scale=.29;scene.render.threads_mode='FIXED';scene.render.threads=4
views=[]
for (side,o),metric in zip(objects,metrics):
    for _,other in objects:other.hide_render=other!=o
    for label,yaw in [('front',0),('profile',90 if side=='L' else 270),('back',180)]:
        target=Vector((0,0,-.09));angle=math.radians(yaw);cam.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.view_layer.update();path=RUN/f'neutral-{side}-{label}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        views.append({'side':side,'view':label,'file':str(path),'sha256':sha(path)})
    evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());display=evaluated.to_mesh();display.calc_loop_triangles();vs=[v.co.copy() for v in display.vertices];tris=[list(t.vertices) for t in display.loop_triangles]
    bvh=BVHTree.FromPolygons(vs,tris,all_triangles=True)
    pairs=[(a,b) for a,b in bvh.overlap(bvh) if a<b and not(set(tris[a])&set(tris[b]))]
    metric['nonadjacentBVHOverlapPairs']=len(pairs);metric['displayBounds']=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]];evaluated.to_mesh_clear()
for _,o in objects:o.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'neutral-anatomical-cages.blend'))
assert sources=={p:sha(Path(p)) for p in sources}
(OUT/'report.json').write_text(json.dumps({'status':'NEUTRAL MODEL gray evidence, parent acceptance pending; no curl/contact pass','sourceNPZs':sources,'sourceNPZsAfter':{p:sha(Path(p)) for p in sources},'metrics':metrics,'views':views,'threads':4,'displayCorrection':'All1656 original polygons including2 wrist-cut ngons exported from unchanged canonical neutral master; positions/native weights match frozen partial NPZ; fresh render mesh removes inherited shape keys','recipeSHA256':sha(Path(__file__))},indent=2)+'\n')
print('NEUTRAL_COMPLETE_DISPLAY_VERIFIED',flush=True)
