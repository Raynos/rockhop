"""CPU matched gray turntables of source34 and incomplete clean-clothing fixture."""
import bpy,bmesh,json,math,time,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
repo=Path('/Users/raynos/projects/games/rockhop');run=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01');out=repo/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/silhouette02/gray';out.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
source=run.parent/'rig-adapter01/body-bind34/rider.glb';raw=source.read_bytes();bpy.ops.import_scene.gltf(filepath=str(source))
body=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith('Protected body'));head=next(o for o in scene.objects if o.type=='MESH' and o.name=='textured');assert sum(p.material_index==0 for p in body.data.polygons)==33968
for o in bpy.data.objects:
 if o.type=='ARMATURE':o.data.pose_position='REST';o.animation_data_clear()
 if o.type=='MESH' and o not in [body,head]:o.hide_render=True
for o in [body,head]:o.animation_data_clear()
mat=bpy.data.materials.new('Matched neutral-gray diagnostic');mat.use_nodes=True;n=mat.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(.34,.34,.34,1);n.inputs['Roughness'].default_value=.72
# Keep original material slots for exact source component selection, then grayoverride.
hoodVertices={v for p in body.data.polygons if p.material_index==2 for v in p.vertices};hoodKeys={tuple(body.data.vertices[i].co) for i in hoodVertices};bodyVertices={v for p in body.data.polygons if p.material_index==0 for v in p.vertices};shared={i for i in bodyVertices if tuple(body.data.vertices[i].co) in hoodKeys};assert len(shared)>100
fixtureBody=body.copy();fixtureBody.data=body.data.copy();fixtureBody.name='Protected_source_hood_gloves_shoes_PATCH_UNSTITCHED';scene.collection.objects.link(fixtureBody)
bm=bmesh.new();bm.from_mesh(fixtureBody.data);bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table();discard=[];keptMain=0
for f in bm.faces:
 keep=f.material_index!=0 or all(v.co.z<.2 for v in f.verts) or any(v.index in shared for v in f.verts)
 if not keep:discard.append(f)
 elif f.material_index==0:keptMain+=1
bmesh.ops.delete(bm,geom=discard,context='FACES_ONLY');bm.to_mesh(fixtureBody.data);bm.free()
fixtureHead=head.copy();fixtureHead.data=head.data.copy();fixtureHead.name='Protected_source_head_UNCHANGED';scene.collection.objects.link(fixtureHead)
f=np.load(run/'silhouette02/fit02.npz');P=f['positions'];quad=f['quads'];mesh=bpy.data.meshes.new('Clean_garment_gray_geometry');mesh.from_pydata([(p[0],-p[2],p[1]) for p in P],[],quad.tolist());mesh.update();garment=bpy.data.objects.new('Clean_native02_fit_UNSTITCHED_UNTEXTURED',mesh);scene.collection.objects.link(garment)
for p in garment.data.polygons:p.use_smooth=True
for o in [body,head,fixtureBody,fixtureHead,garment]:
 for i in range(max(1,len(o.data.materials))):
  if i<len(o.data.materials):o.data.materials[i]=mat
  else:o.data.materials.append(mat)
sourceObjects=[body,head];fixtureObjects=[fixtureBody,fixtureHead,garment]
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=384;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Shared neutral background');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.12,.12,.12,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4
def light(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((.64,0,.92))-o.location).to_track_quat('-Z','Y').to_euler()
light('Shared soft key',(3,-2,3),450,3);light('Shared soft fill',(-2,-2,2),250,3);light('Shared rear rim',(0,3,3),300,2)
d=bpy.data.cameras.new('Matched shape inspection camera');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=2.0;target=Vector((.64,0,.90));rows=[];start=time.monotonic()
for label,active in [('fit02',fixtureObjects)]:
 folder=out/label;folder.mkdir(exist_ok=True)
 for o in sourceObjects+fixtureObjects:o.hide_render=o not in active
 for i in range(73):
  if time.monotonic()-start>1600:raise RuntimeError('Own CPUrender batch stopped before30minutes')
  yaw=math.radians(i*5 if i<72 else 0);elevation=.12 if i<72 else .65;cam.location=target+Vector((4*math.cos(yaw),4*math.sin(yaw),elevation));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();path=folder/f'{i:04d}.png';assert not path.exists();scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'label':label,'frame':i,'yawDegrees':i*5 if i<72 else 0,'camera':list(cam.location),'cameraRotation':list(cam.rotation_euler),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()});print('GRAY_PROGRESS',label,i,flush=True)
assert source.read_bytes()==raw
(out/'render-report.json').write_text(json.dumps({'kind':'Matched CPU gray geometry turntable; temporary fixture incomplete/unaccepted','sourceSHA256':hashlib.sha256(raw).hexdigest(),'sourceUnchanged':True,'renderDevice':'CPU','threads':2,'seconds':time.monotonic()-start,'framesPerFilm':72,'extraElevatedFront':72,'resolution':[384,512],'sharedSourceBodyHoodVertices':len(shared),'retainedOriginalBodyPatchTriangles':keptMain,'fixtures':['Original complete34neutral rest','Source-fitted native02garment with source head,hood,gloves,shoe/neckpatches:NOTstitched or textured'],'rows':rows,'limits':['No new complete asset, exact seam/contacts/rig or appearance pass.','Rest turntable only; not sitting/Garage/gameplay motion.','Neutral materials replace allsource textures identically; no face/fullbody mockup score from this diagnostic.']},indent=2)+'\n')
