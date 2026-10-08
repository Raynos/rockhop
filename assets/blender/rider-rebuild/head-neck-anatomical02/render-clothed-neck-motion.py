"""One actual-PBR Eevee clothed neck movie; read-only native, parent lease only.

Known host route: prior render_grounded_motion.py rendered 344 Eevee PBR640²
frames headlessly in 84.465s, macOS Blender CPU-thread limit2, global model lock.
This renderer uses exactly one 3/4 view and 72 consecutive authored frames.
No native save, model/export/geometry/material mutation or renderer fallback.
"""
import hashlib
import json
import struct
import subprocess
import sys
import time
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[4]
ACTION='UnacceptedClothedNeckTurnNod72'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pin(row):
    p=(ROOT/row['path']).resolve();assert sha(p)==row['sha256'],('Changed source',str(p));return p

def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    specpath,out=(Path(p).resolve() for p in args);spec=json.loads(specpath.read_text())
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/head-neck-anatomical02') and not out.exists()
    assert spec['accepted'] is False and spec['actionName']==ACTION and spec['frameRange']==[1,72] and spec['fps']==24
    native=pin(spec['native']);motion_path=pin(spec['motionReport']);motion=json.loads(motion_path.read_text())
    assert motion['candidate']==spec['native'] and motion['action']==ACTION and motion['actionSlot']==spec['actionSlot']
    assert sorted(spec['objects'])==sorted(motion['visibleMeshes']) and len(spec['objects'])==7
    bpy.ops.wm.open_mainfile(filepath=str(native));scene=bpy.context.scene;rig=bpy.data.objects['RiderSkeleton']
    actual_visible=sorted(o.name for o in scene.objects if o.type=='MESH' and not o.hide_render)
    assert actual_visible==sorted(spec['objects']) and 'RiderBody' in actual_visible
    assert all(any(n.startswith(p) for n in actual_visible) for p in ('Boots__','Gloves__','Hoodie__','Jeans__'))
    assert all(layer.material_override is None for layer in scene.view_layers),'Actual PBR required'
    assert len(rig.data.bones)==75 and len(rig.data.bones)==motion['resetAndTRSKeyedJointsEveryFrame']
    action=bpy.data.actions.get(ACTION);assert action is not None and rig.animation_data is not None
    assert rig.animation_data.action==action
    slot=next((s for s in action.slots if s.identifier==spec['actionSlot']),None);assert slot is not None
    rig.animation_data.action_slot=slot
    # Explicit proven engine, no workbench/material/camera substitution fallback.
    scene.render.engine='BLENDER_EEVEE';scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.film_transparent=False;scene.render.use_compositing=False;scene.render.use_sequencer=False
    scene.render.fps=24;scene.render.fps_base=1;scene.view_settings.view_transform='AgX'
    world=bpy.data.worlds.new('Clothed neck actual PBR diagnostic world');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.24,.28,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.55;scene.world=world
    focus=Vector((0,-.025,1.51))
    for o in scene.objects:
        if o.type=='LIGHT':o.hide_render=True
    for name,loc,power,size in [('Key',(2,-3,4),650,3),('Fill',(-3,-2,2),450,3),('Rim',(0,3,3),700,2)]:
        data=bpy.data.lights.new('Neck review '+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        light=bpy.data.objects.new(data.name,data);scene.collection.objects.link(light);light.location=loc;aim(light,(0,0,1))
    camera=bpy.data.objects.new('One fixed clothed neck three-quarter camera',bpy.data.cameras.new('One fixed clothed neck three-quarter camera'))
    scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.72
    camera.location=(-4,-4,1.58);aim(camera,focus)
    out.mkdir(parents=True);frames=out/'frames';frames.mkdir();start=time.monotonic();outputs=[];pose_hashes=[]
    for index,frame in enumerate(range(1,73)):
        scene.frame_set(frame);bpy.context.view_layer.update()
        h=hashlib.sha256()
        for b in rig.pose.bones:
            h.update(b.name.encode());h.update(struct.pack('<16f',*(x for r in b.matrix_basis for x in r)))
        pose_hashes.append({'frame':frame,'actual75PoseBasisSHA256':h.hexdigest()})
        scene.render.filepath=str(frames/f'{index:04d}.png');bpy.ops.render.render(write_still=True)
        outputs.append({'frame':frame,'path':str((frames/f'{index:04d}.png').relative_to(ROOT)),
                        'sha256':sha(frames/f'{index:04d}.png')})
        if (index+1)%12==0:print('NECK_MOVIE_PROGRESS',index+1,72,round(time.monotonic()-start,3),flush=True)
    assert pose_hashes[0]['actual75PoseBasisSHA256']==pose_hashes[-1]['actual75PoseBasisSHA256'],'Actual action did not return to exact neutral75 basis'
    movie=out/'clothed-neck-threequarter72.mp4'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate','24','-i',str(frames/'%04d.png'),
       '-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-an',str(movie)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(movie)]))
    video=[s for s in probe['streams'] if s['codec_type']=='video'];audio=[s for s in probe['streams'] if s['codec_type']=='audio']
    assert len(video)==1 and int(video[0]['nb_read_frames'])==72 and not audio
    assert video[0]['width']==640 and video[0]['height']==640 and video[0]['avg_frame_rate']=='24/1'
    assert sha(native)==spec['native']['sha256'] and sha(motion_path)==spec['motionReport']['sha256']
    report={'accepted':False,'status':'UNACCEPTED_ACTUAL_PBR_CLOTHED_NECK_MOVIE_READY_FOR_PARENT_PLAYED_REVIEW',
      'sourceNative':spec['native'],'motionReport':spec['motionReport'],'nativeSourceUnchanged':True,
      'recipeSHA256':sha(__file__),'specSHA256':sha(specpath),'engine':'BLENDER_EEVEE','cpuThreadLimit':2,
      'renderDevice':'Eevee host graphics backend; globally serialized parent model lease','resolution':[640,640],
      'movie':{'path':str(movie.relative_to(ROOT)),'sha256':sha(movie),'decodedFrames':72,'fps':24,'audioStreams':0},
      'actualVisibleMeshesEveryFrame':actual_visible,'frameRange':[1,72],'stride':1,'continuousFrames':True,
      'action':ACTION,'actionSlot':slot.identifier,'camera':{'location':list(camera.location),'focus':list(focus),'orthoScale':.72},
      'actualPoseFrames':pose_hashes,'renderedFrames':outputs,'elapsedSeconds':time.monotonic()-start,
      'limits':['One head/neck turn/nod stress sample only; parent alone judges played result.','All actual working outfit meshes remain visible in scene; fixed head+hoodie close camera crops the lower garments. Full outfit context remains a separate still.',
        'No shoulder/clothing/grip/gait/bike movement qualification or universal envelope claim.',
        'Known rest-shape/PBR tells and saved-normal residual remain open; conditioned field has no played acceptance.',
        'No native save, rig rest edit, bake, export, player promotion, browser or audio.']}
    (out/'render.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'movie':report['movie'],'frames':72,'elapsedSeconds':report['elapsedSeconds']}))
if __name__=='__main__':main()
