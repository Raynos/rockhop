"""Play exact measured native pose sequence from two synchronized cameras."""
import argparse,hashlib,json,math,sys,time
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','driver','measurement','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,driver_path,measurement,out=[Path(getattr(a,k)).resolve() for k in ['source','driver','measurement','out']]
out.mkdir(parents=True,exist_ok=True);assert not (out/'review.json').exists(),'Preserve frozen review'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,driver_path,measurement]}
d=json.loads(driver_path.read_text());m=json.loads(measurement.read_text());assert m['pins'][str(source)]==pins[str(source)] and m['pins'][str(driver_path)]==pins[str(driver_path)]
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;rig=bpy.data.objects['Independent anatomical foundation rig']
visible=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
assert any(o.name=='Selected Hunyuan authored skin wearable, unaccepted' for o in visible)
world=bpy.data.worlds.new('Selected native wearing neutral studio');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.075,.075,.075,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for o in scene.objects:
    if o.type=='LIGHT':o.hide_render=True
for name,pos,energy in [('Key',(4,-4,5),700),('Fill',(-3,4,4),600),('Top',(.65,0,5),400)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=energy;light.size=4
    o=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.65,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Matched native front rear camera');cd.type='ORTHO';cd.ortho_scale=2.85
camera=bpy.data.objects.new(cd.name,cd);bpy.context.collection.objects.link(camera);scene.camera=camera
white=bpy.data.materials.new('Native diagnostic legend');white.use_nodes=True;nt=white.node_tree;nt.nodes.clear();emission=nt.nodes.new('ShaderNodeEmission');emission.inputs[0].default_value=(1,1,1,1)
output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(emission.outputs[0],output.inputs['Surface'])
font=bpy.data.curves.new('Unaccepted native wearing legend','FONT');font.size=.043;font.materials.append(white)
legend=bpy.data.objects.new(font.name,font);bpy.context.collection.objects.link(legend);legend.parent=camera;legend.location=(-1.34,1.30,-2.)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='AgX'
for view in ['front','rear']:(out/view).mkdir(exist_ok=True)
frames=[];start=time.monotonic()
for number,index in enumerate(m['playedDriverFrameIndices']):
    row=d['frames'][index]
    for name,trs in row['poseBasisBlender'].items():
        bone=rig.pose.bones[name];bone.rotation_mode='QUATERNION';bone.location=trs['location'];bone.rotation_quaternion=trs['quaternionWXYZ'];bone.scale=trs['scale']
    bpy.context.view_layer.update();record=m['frames'][index];views=[]
    for view,yaw in [('front',0.),('rear',math.pi)]:
        target=Vector((.65,0,1.04));camera.location=target+Vector((4*math.cos(yaw),4*math.sin(yaw),.22));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        font.body=view.upper()+' / SOURCE14 NATIVE FK / UNACCEPTED\n'+f't={row["timeS"]:.3f}s  body {record["bodyTrianglePairs"]}  self {record["nonAdjacentSelfTrianglePairs"]}'
        bpy.context.view_layer.update();border=1.
        for o in visible:
            evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
            for vertex in mesh.vertices:
                q=world_to_camera_view(scene,camera,evaluated.matrix_world@vertex.co);border=min(border,q.x,q.y,1-q.x,1-q.y)
            evaluated.to_mesh_clear()
        assert border>.02,(number,view,border)
        path=out/view/f'{number:04d}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        views.append({'view':view,'PNG_SHA256':sha(path),'minimumNormalizedBorder':border,'cameraWorldRows':[list(r) for r in camera.matrix_world]})
    frames.append({'displayFrame':number,'driverFrame':index,'timeS':row['timeS'],'bodyPairs':record['bodyTrianglePairs'],'selfPairs':record['nonAdjacentSelfTrianglePairs'],'views':views})
    if number%12==0:print('NATIVE_SELECTED_PLAYED',number,'driver',index,'elapsed',round(time.monotonic()-start,1),flush=True)
assert pins=={p:sha(p) for p in pins}
report={'status':'UNACCEPTED continuous authored native garment wearing; root judges played evidence',
        'pins':pins,'recipeSHA256':sha(__file__),'FPS':12,'viewResolution':[640,640],'frames':frames,'visibleNativeObjects':[o.name for o in visible],
        'render':'CyclesCPU2threads4samples, AgX, original actual selected PBR and protected native appearance',
        'limits':['Synchronized front/rear same native poses every fourth measured48Hzsample; all529samples mechanically measured separately.',
                  'Actual native rig/body/garment deformation, no simulated cloth/collision correction or cosmetic recoloring.',
                  'Native FK is not actual bike/engine/support or iOS qualification. Source14fails moving contacts; allM0-M5/rootsolejudge remain open.',
                  'Source13rest/source14native/export/selectedUV/PBR/body/head/51bind remain frozen; no player/Library promotion.']}
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print('NATIVE_SELECTED_REVIEW_READY',len(frames),round(time.monotonic()-start,1),flush=True)
