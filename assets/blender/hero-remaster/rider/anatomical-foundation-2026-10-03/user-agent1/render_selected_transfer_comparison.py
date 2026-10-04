"""Matched played rest orbit of original donor, registration, and material test.

Four synchronized columns; same camera, lighting, source channels and scale.
The first donor has only uniform unit/frame placement. Second shows the
existing piecewise registration. Last two have byte-identical rest geometry.
No garment deformation or candidate acceptance is implied by this orbit.
"""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector, Matrix

ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','registration-recipe','transfer-recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source,recipe,transfer_recipe,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','registration-recipe','transfer-recipe','out']]
out.mkdir(parents=True,exist_ok=True);assert not (out/'review.json').exists(),'Keep frozen review'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,recipe,transfer_recipe]}
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only'];rig=bpy.data.objects['Independent anatomical foundation rig']
old=bpy.data.objects['Selected Hunyuan underarm fitted wearable, unrigged']
new=bpy.data.objects['Selected donor direct-UV transfer on unchanged source13, unaccepted']
assert len(old.data.vertices)==len(new.data.vertices)==6046
assert [v.co[:] for v in old.data.vertices]==[v.co[:] for v in new.data.vertices]
definition=transfer_recipe.read_text();definition=definition[definition.index('definition=recipe.read_text()'):definition.index('tree=BVHTree')]
exec(compile(definition,str(transfer_recipe),'exec'))
raw=high.copy();raw.data=high.data.copy();bpy.context.collection.objects.link(raw);raw.name='Exact donor, uniform frame placement only'
reg=high.copy();reg.data=high.data.copy();bpy.context.collection.objects.link(reg);reg.name='Exact donor, existing piecewise registration'
uniform=donor@display_to_native.T*height+[0,.007,up]
for obj,positions in [(raw,uniform),(reg,registered)]:
    obj.parent=None;obj.matrix_world=Matrix.Translation((.65,0,0))
    coords=np.asarray(positions,dtype=np.float32).ravel();obj.data.vertices.foreach_set('co',coords);obj.data.update()
    # Position changes transport authored geometric normals through the source
    # deformation; unchanged source object and both fitted normals stay frozen.
    if obj.data.has_custom_normals:obj.data.normals_split_custom_set([(0,0,0)]*len(obj.data.loops))
variants=[('donor','DONOR / UNIFORM FRAME',raw),('registered','DONOR / EXISTING REGISTRATION',reg),('baked','SOURCE13 / FROZEN RAY BAKE',old),('direct','SOURCE15 / DIRECT UV TEST',new)]
for o in scene.objects:
    if o.type in ['MESH','LIGHT','FONT']:o.hide_render=True
world=bpy.data.worlds.new('Matched selected donor neutral studio');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.075,.075,.075,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
target=Vector((.65,0,1.38))
for name,pos,energy in [('Key',(4,-4,5),700),('Fill',(-3,4,4),600),('Top',(.65,0,5),400)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=energy;light.size=4
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Identical matched rest orbit');cd.type='ORTHO';cd.ortho_scale=1.72
camera=bpy.data.objects.new(cd.name,cd);bpy.context.collection.objects.link(camera);scene.camera=camera
white=bpy.data.materials.new('Matched comparison legend');white.use_nodes=True;nt=white.node_tree;nt.nodes.clear();em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(1,1,1,1)
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(em.outputs[0],output.inputs['Surface'])
font=bpy.data.curves.new('Matched source legend','FONT');font.size=.031;font.materials.append(white)
legend=bpy.data.objects.new(font.name,font);bpy.context.collection.objects.link(legend);legend.parent=camera;legend.location=(-.80,.78,-2.)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='AgX'
for key,label,obj in variants:(out/key).mkdir(exist_ok=True)
frames=[];start=time.monotonic()
for index in range(48):
    yaw=2*math.pi*index/48;camera.location=target+Vector((4*math.cos(yaw),4*math.sin(yaw),.30));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    views=[]
    for key,label,obj in variants:
        obj.hide_render=False;obj.hide_set(False);font.body=label+'\nREST / SAME CAMERA+LIGHT / UNACCEPTED'
        scene.render.filepath=str(out/key/f'{index:04d}.png');bpy.ops.render.render(write_still=True)
        views.append({'variant':key,'PNG_SHA256':sha(scene.render.filepath),'object':obj.name})
        obj.hide_render=True
    frames.append({'frame':index,'timeS':index/6,'yawRadians':yaw,'cameraWorldRows':[list(r) for r in camera.matrix_world],'views':views})
    if index%6==0:print('MATCHED_TRANSFER_PLAYED',index,'seconds',round(time.monotonic()-start,1),flush=True)
parents=[v.value for v in old.data.attributes['source_parent_polygon'].data]
hoodIds={i for p in old.data.polygons if parents[p.index]>=1224 for i in p.vertices}
hood=np.array([old.data.vertices[i].co[:] for i in sorted(hoodIds)])
sourceHood=registered[donor[:,2]>.62]
report={'status':'UNACCEPTED matched actual donor/rest/material orbit, root sole art judge','pins':pins,'recipeSHA256':sha(__file__),'FPS':6,'frames':frames,'viewResolution':[640,640],
        'sourceGeometry':{'originalDonorVertices':len(donor),'registeredScalarSampleMaximumErrorM':registration_error,'fittedVertices':6046,'fittedOldVsNewMaximumChangeM':0,
                          'fittedHoodXYZBoundsM':[hood.min(0).tolist(),hood.max(0).tolist()],'donorUpperPartCriterion':'Original display Z >0.62; diagnostic bounds, not an authored semantic hood partition','registeredDonorUpperPartXYZBoundsM':[sourceHood.min(0).tolist(),sourceHood.max(0).tolist()]},
        'render':'Cycles CPU2threads8samples, AgX, actual selected donor PBR; synchronized continuous rest-camera orbit',
        'limits':['Orbit isolates actual material transfer and rest silhouette; no native wearing motion or visual acceptance claim.','Raw donor has uniform scale0.472222 and frame rotation/placement; registered donor uses frozen piecewise torso/arm mapping. Same native camera and lighting for all columns.','Donor display derivatives recompute geometric normals after coordinate mapping; original donor, source13/source14, protected body/head/bind are not modified.','Source15 geometry exactly source13; transfer test cannot recover lost hood volume or sleeve folds. AllM0-M5/mobile open; no normal-player promotion.']}
assert pins=={p:sha(p) for p in pins};(out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print('MATCHED_TRANSFER_READY',round(time.monotonic()-start,1),flush=True)
