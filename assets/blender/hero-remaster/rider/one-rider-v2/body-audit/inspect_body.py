"""Read-only CPU closeups and measured display-space topology of H21-4.

Run Blender -b -t 4 --python inspect_body.py. Never saves a modified model.
Landmark probes are visible-surface estimates, not discovered skeleton joints.
"""
import hashlib, json, math, time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

REPO = Path('/Users/raynos/projects/games/rockhop')
SOURCE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
RAW = SOURCE.with_name('raw-shape.npz')
OUT = REPO / 'docs/evidence/hero-remaster/one-rider-v2/body-audit'
RUNTIME = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/body-audit')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
start = time.perf_counter()
frozen = {str(p): sha(p) for p in (SOURCE, RAW)}
OUT.mkdir(parents=True, exist_ok=True); RUNTIME.mkdir(parents=True, exist_ok=True)
if (OUT/'inspection.json').exists(): raise RuntimeError('Frozen inspection exists')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.context.view_layer.update()
pts = np.array([o.matrix_world @ v.co for o in meshes for v in o.data.vertices])
lo, hi = pts.min(0), pts.max(0)
scale = 1.8 / (hi[2]-lo[2]); translation = np.array([-(lo[0]+hi[0])/2, -(lo[1]+hi[1])/2, -lo[2]])*scale
root = bpy.data.objects.new('Read-only display normalization', None)
bpy.context.scene.collection.objects.link(root)
for o in [o for o in bpy.context.scene.objects if o.parent is None and o != root]:
    m=o.matrix_world.copy(); o.parent=root; o.matrix_world=m
root.scale=(scale,)*3; root.location=translation
bpy.context.view_layer.update()
vertices=[]; faces=[]; offset=0
for o in meshes:
    vertices.extend(o.matrix_world @ v.co for v in o.data.vertices)
    o.data.calc_loop_triangles()
    faces.extend([offset+int(i) for i in t.vertices] for t in o.data.loop_triangles)
    offset += len(o.data.vertices)
vertices=np.array(vertices); faces=np.array(faces)
def topology(v,f):
    unique, inverse=np.unique(np.round(v,8),axis=0,return_inverse=True)
    wf=inverse[f]
    repeated=np.any(np.stack([wf[:,0]==wf[:,1],wf[:,1]==wf[:,2],wf[:,2]==wf[:,0]]),axis=0)
    edges=np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1)
    ue,counts=np.unique(edges,axis=0,return_counts=True)
    parent=np.arange(len(unique))
    def find(a):
        while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
        return a
    for a,b in ue:
        a,b=find(int(a)),find(int(b))
        if a!=b: parent[a]=b
    component=np.array([find(i) for i in range(len(unique))])
    ids,c=np.unique(component,return_counts=True)
    comps=[]
    for i,n in sorted(zip(ids,c),key=lambda r:-r[1]):
        sel=unique[component==i]
        comps.append({'vertices':int(n),'bounds': [sel.min(0).tolist(),sel.max(0).tolist()]})
    return {'verticesStored':len(v),'verticesPositionWeld8Digits':len(unique),'faces':len(f),'repeatIndexFacesAfterPositionWeld':int(repeated.sum()),'boundaryEdgesAfterPositionWeld':int((counts==1).sum()),'nonmanifoldEdgesAfterPositionWeld':int((counts>2).sum()),'componentsAfterPositionWeld':comps}

scene=bpy.context.scene
world=bpy.data.worlds.new('Neutral diagnostic studio'); world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65; scene.world=world
for name, pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size
    o=bpy.data.objects.new(name,d); scene.collection.objects.link(o); o.location=pos
    o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Matched detail camera'); camera=bpy.data.objects.new('Matched detail camera',cd)
scene.collection.objects.link(camera); scene.camera=camera; cd.type='ORTHO'
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.resolution_x=640; scene.render.resolution_y=640; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
gray=bpy.data.materials.new('Neutral geometry only'); gray.use_nodes=True
bs=gray.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(.42,.42,.42,1); bs.inputs['Roughness'].default_value=.65
original={o.name:list(o.data.materials) for o in meshes}
# Same camera/light per PBR/gray; both hands shown independently.
views=[('hand-positive-front',(.35,0,.84),.27,0),('hand-positive-profile',(.35,0,.84),.27,90),('hand-positive-back',(.35,0,.84),.27,180),
       ('hand-negative-front',(-.35,0,.84),.27,0),('hand-negative-profile',(-.35,0,.84),.27,270),('hand-negative-back',(-.35,0,.84),.27,180),
       ('knees-front',(0,0,.52),.63,0),('knees-profile',(0,0,.52),.63,90),('shoes-front',(0,0,.13),.65,0),('shoes-profile',(0,0,.13),.65,90),
       ('armpits-front',(0,0,1.24),.83,0),('armpits-quarter',(0,0,1.24),.83,45),('back-full',(0,0,.91),1.92,180),('back-quarter',(0,0,.91),1.92,225)]
records=[]
for mode in ['pbr','gray']:
    for o in meshes:
        o.data.materials.clear()
        for m in ([gray] if mode=='gray' else original[o.name]): o.data.materials.append(m)
    for name,target,ortho,yaw in views:
        target=Vector(target); cd.ortho_scale=ortho; angle=math.radians(yaw)
        camera.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),0))
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        file=RUNTIME/f'{name}-{mode}.png'; scene.render.filepath=str(file); bpy.ops.render.render(write_still=True)
        records.append({'view':name,'material':mode,'target':list(target),'orthoScale':ortho,'yaw':yaw,'file':str(file),'sha256':sha(file)})
native=np.load(RAW)
metrics={'status':'CPU-only read-only body inspection; not body or rig acceptance', 'blender':bpy.app.version_string,'renderCPUThreads':4,'samples':24,
         'sourceSHA256':frozen,'sourceSHA256After':{str(p):sha(p) for p in (SOURCE,RAW)},'recipeSHA256':sha(Path(__file__)),
         'coordinates':'Blender +Z up, front -Y, lateral X; no left/right anatomical side inferred from screen',
         'displayHeight':1.8,'scale':float(scale),'translation':translation.tolist(),'beforeBounds':[lo.tolist(),hi.tolist()],
         'displayBounds':[vertices.min(0).tolist(),vertices.max(0).tolist()], 'workingTopology':topology(vertices,faces),
         'rawTopology':topology(native['vertices'],native['faces']), 'rawCoordinates':'unaligned native decoder coordinates; not same frame as Blender display',
         'skins':len([o for o in scene.objects if o.type=='ARMATURE']),'views':records,'wallSeconds':time.perf_counter()-start,
         'limits':['No self-intersection solver run: watertightness does not prove no intersections.','All images static source diagnostics; no contact or deformation measured.','1.8m includes rejected old hair; final neck/head replacement must establish anatomical stature anew.']}
assert metrics['sourceSHA256']==metrics['sourceSHA256After']
(OUT/'inspection.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('READ_ONLY_AUDIT_DONE',flush=True)
