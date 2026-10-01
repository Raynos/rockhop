"""Actual held NEW hand with exact decoded rubber-grip geometry; appearance probe."""
from pathlib import Path
import bpy,json,hashlib,math
import numpy as np
from mathutils import Vector
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-grip03';RUN=BASE/'rig-adapter01/native-grip03';MASTER=BASE/'parent-assembly/donor-fit05/rider.blend';BUFFER=RUN/'native-held-shape.npz';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(MASTER);d=np.load(BUFFER);ids=d['sourceCompleteVertexIds'];source=d['sourcePositions'];wrapped=d['wrappedPositionsDQS'];bpy.ops.wm.open_mainfile(filepath=str(MASTER));scene=bpy.context.scene;body=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith('NEW protected'));mesh=body.data;original=np.array([v.co for v in mesh.vertices]);assert np.array_equal(original[ids],source);current=original.copy();current[ids]=wrapped;assert np.array_equal(current[np.setdiff1d(np.arange(len(current)),ids)],original[np.setdiff1d(np.arange(len(current)),ids)]);mesh.vertices.foreach_set('co',current.ravel());mesh.normals_split_custom_set([(0,0,0)]*len(mesh.loops));mesh.update()
for o in list(scene.objects):
 if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
rodmesh=bpy.data.meshes.new('Actual unchanged rubber grip44triangles');rodmesh.from_pydata(d['rodPoints'].tolist(),[],d['rodTriangleIndices'].tolist());handle=bpy.data.objects.new(rodmesh.name,rodmesh);scene.collection.objects.link(handle)
green=bpy.data.materials.new('Real grip surface diagnosticgreen');green.use_nodes=True;bs=green.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.025,.24,.07,1);bs.inputs['Roughness'].default_value=.65;handle.data.materials.append(green)
world=bpy.data.worlds.new('Actual held gripstudio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
 light=bpy.data.lights.new(name,'AREA');light.energy=power;light.size=size;o=bpy.data.objects.new(name,light);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(d['nativeFixtureCentre'])-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Actual held shape');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=.27;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';target=Vector(d['nativeFixtureCentre']);target.z+=.025;views=[]
originalMats={o.name:list(o.data.materials) for o in scene.objects if o.type=='MESH' and o!=handle};gray=bpy.data.materials.new('Actual neutral handshape');gray.use_nodes=True;gray.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.35,.35,.35,1);gray.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.7
for mode in ['PBR','gray']:
 if mode=='gray':
  for name,mats in originalMats.items():
   obj=bpy.data.objects[name]
   for i in range(len(mats)):obj.data.materials[i]=gray
 for label,yaw in [('front',0),('palm',180),('profile',90)]:
  a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),.04));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();path=OUT/f'actual-held-{mode}-{label}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);views.append({'mode':mode,'view':label,'file':str(path),'SHA256':sha(path)})
assert before==sha(MASTER);(OUT/'render-report.json').write_text(json.dumps({'sourceSHA256':before,'sourceUnchanged':True,'nativeBufferSHA256':sha(BUFFER),'views':views,'sourceUVsMaterialsUnchanged':True,'bodyPositionsOutsideNativePatchExact':True,'normalDisclosure':'Deformed body mesh geometry normals recomputed; material texture maps untouched','scope':'Static held-shape appearance diagnostic only, not played riding or closing-motion acceptance','CPUthreads':2,'GPUjob':False},indent=2)+'\n');print('ACTUAL_HELD_SHAPE_RENDER_COMPLETE',flush=True)
