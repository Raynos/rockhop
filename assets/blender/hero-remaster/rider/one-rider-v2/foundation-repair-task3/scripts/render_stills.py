from pathlib import Path
import bpy,json,math,numpy as np,sys
from mathutils import Vector,Matrix
import itertools
root=Path.cwd();out=root/'evidence'
sys.path.insert(0,str(root/'scripts'));from glb import GLB
g=GLB(root/'baseline/rider.glb');prims=[p for m in g.j['meshes']for p in m['primitives']];r=np.concatenate([g.array(p['attributes']['POSITION']) for p in prims])
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;bpy.ops.import_scene.gltf(filepath=str(root/'baseline/rider.glb'))
meshes=[o for o in sc.objects if o.type=='MESH' and o.name!='Icosphere'];rig=next(o for o in sc.objects if o.type=='ARMATURE')
lookup={}
for i,v in enumerate(r):lookup.setdefault(tuple(np.round(v*10000).astype(int)),[]).append(i)
maps=[]
for o in meshes:
 orig=np.array([list(o.matrix_world@v.co) for v in o.data.vertices]);world=orig[:,[0,2,1]];world[:,2]*=-1;ix=[];md=0
 for v in world:
  key=tuple(np.round(v*10000).astype(int));cand=lookup.get(key,[])
  if not cand:
   for dd in itertools.product([-1,0,1],repeat=3):cand+=lookup.get(tuple(key[i]+dd[i] for i in range(3)),[])
  assert cand,(o.name,key);best=min(cand,key=lambda j:np.linalg.norm(r[j]-v));md=max(md,float(np.linalg.norm(r[best]-v)));ix.append(best)
 assert md<1e-5,(o.name,md);maps.append(np.array(ix))
 o.shape_key_clear()
 for mod in list(o.modifiers):o.modifiers.remove(mod)
 o.parent=None;o.matrix_world=Matrix.Identity(4)
 for poly in o.data.polygons:poly.use_smooth=True
rig.hide_render=True
for o in list(sc.objects):
 if o.name=='Icosphere':bpy.data.objects.remove(o,do_unlink=True)
def mat(name,c):
 a=bpy.data.materials.new(name);a.diffuse_color=(*c,1);a.use_nodes=True;a.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*c,1);return a
before=set(sc.objects);bpy.ops.import_scene.gltf(filepath=str(root/'baseline/bike.glb'))
bikeobjects=set(sc.objects)-before;bikeparts={x['name']:x for x in json.loads((out/'bike.json').read_text())}
for ob in bikeobjects:
 if ob.type!='MESH':continue
 if 'blur' in ob.name or 'spokes' in ob.name:ob.hide_render=True
 key=ob.name.split('.')[0]
 if key not in bikeparts:continue
 pts=np.array(bikeparts[key]['positions']);pts=pts[:,[0,2,1]];pts[:,1]*=-1;assert len(pts)==len(ob.data.vertices),(key,len(pts),len(ob.data.vertices));ob.parent=None;ob.matrix_world=Matrix.Identity(4);ob.data.vertices.foreach_set('co',pts.astype('f4').ravel());ob.data.update()
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.34));bpy.context.object.data.materials.append(mat('floor',(.18,.18,.18)))
world=bpy.data.worlds.new('studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;sc.world=world
target=Vector((-.1,0,.7))
for pos,power in [((3,-4,4),700),((0,4,3),500),((-3,-1,3),600)]:
 d=bpy.data.lights.new('area','AREA');d.energy=power;d.size=4;o=bpy.data.objects.new('area',d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('camera');cam=bpy.data.objects.new('camera',d);sc.collection.objects.link(cam);sc.camera=cam;d.type='ORTHO'
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.view_settings.view_transform='AgX';sc.render.resolution_x=640;sc.render.resolution_y=640;sc.render.resolution_percentage=100

cases=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['A','B','C19','C']
sc.cycles.samples=8;sc.render.resolution_x=512;sc.render.resolution_y=512
for name in cases:
 for sample in [0,12,24]:
  dat=np.load(root/'experiments'/f'{name}-rigid_length_stand_to_sit-{sample:03d}.npz');posed=np.concatenate([dat[f'p{i}']for i in range(5)]);v=posed[:,[0,2,1]];v[:,1]*=-1
  for o,ix in zip(meshes,maps):
   o.data.vertices.foreach_set('co',v[ix].astype('f4').ravel());o.data.update();o.data.normals_split_custom_set_from_vertices([(0.,0.,0.)]*len(o.data.vertices))
  for angle,an in [(0,'front'),(90,'side'),(180,'back')]:
   tar=Vector((-.18,0,.82));cam.location=tar+Vector((4*math.cos(math.radians(angle)),4*math.sin(math.radians(angle)),.2));cam.rotation_euler=(tar-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=1.85
   sc.render.filepath=str(out/'renders'/f'{name}-{sample}-{an}.png');bpy.ops.render.render(write_still=True)
print('RENDER FINISHED')
