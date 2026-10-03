"""Play immutable matched footwear streams with source materials and a shared orbit."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--comparison', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
folder = Path(a.comparison).resolve(); out = folder/'review'; out.mkdir(exist_ok=True)
if (out/'review.json').exists():
    raise RuntimeError('Frozen footwear review exists')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins = {n: sha(folder/n) for n in ['motion.json', 'streams.npz']}
d = json.loads((folder/'motion.json').read_text()); streams = np.load(folder/'streams.npz')
source = Path(next(p for p in d['pins'] if p.endswith('.blend')))
assert sha(source) == d['pins'][str(source)]
bpy.ops.wm.open_mainfile(filepath=str(source)); scene = bpy.context.scene
materials = {n: list(bpy.data.objects[r['object']].data.materials) for n,r in d['nativeRegions'].items()}
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)
world = bpy.data.worlds.new('Matched footwear neutral studio'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.08, .08, .08, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .7; scene.world = world
objects = []
for version in ['old', 'new']:
    for name in [version, 'bodyVisible', 'jeans']:
        r = d['nativeRegions'][name]; mesh = bpy.data.meshes.new(version+' '+name)
        mesh.from_pydata(streams[name][0].tolist(), [], r['faces']); mesh.update()
        for mat in materials[name]:
            mesh.materials.append(mat)
        for p,slot in zip(mesh.polygons,r['materialSlots']):
            p.material_index = slot; p.use_smooth = True
        for number, layer in enumerate(r['UVLayers']):
            uv = mesh.uv_layers.new(name='Source UV '+str(number))
            for p,values in zip(mesh.polygons,layer):
                for i,value in zip(p.loop_indices,values):
                    uv.data[i].uv = value
        o = bpy.data.objects.new(version+' '+name,mesh); bpy.context.collection.objects.link(o)
        objects.append((o,name,version))
camera_data = bpy.data.cameras.new('Matched moving footwear orbit'); camera_data.type = 'ORTHO'; camera_data.ortho_scale = 1.9
camera = bpy.data.objects.new(camera_data.name,camera_data); bpy.context.collection.objects.link(camera); scene.camera = camera
for name,pos in [('Key',(3,-3,4)),('Fill',(-3,3,4))]:
    light = bpy.data.lights.new(name,'AREA'); light.energy = 400; light.size = 4
    o = bpy.data.objects.new(name,light); bpy.context.collection.objects.link(o); o.location = pos
    o.rotation_euler = (Vector((.65,0,.15))-o.location).to_track_quat('-Z','Y').to_euler()
white = bpy.data.materials.new('White diagnostic legend'); white.use_nodes = True
nt = white.node_tree; nt.nodes.clear(); e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (1,1,1,1)
output = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0],output.inputs['Surface'])
font = bpy.data.curves.new('Footwear diagnostic legend','FONT'); font.size = .028
legend = bpy.data.objects.new(font.name,font); bpy.context.collection.objects.link(legend); legend.parent = camera
legend.location = (-.91,.465,-2); font.materials.append(white)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 4; scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
scene.render.resolution_x = 1280; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'
frames = []; minimum = 1.
for index, sample in enumerate(d['sampledFrames']):
    yaw = -math.pi/4 + index/(len(d['sampledFrames'])-1)*2*math.pi
    right = np.array([-math.sin(yaw),math.cos(yaw),0.])
    points = np.concatenate([streams[n][index] for n in ['old','new','bodyVisible','jeans']])
    target = Vector((points.min(0)+points.max(0))/2)
    camera.location = target + Vector((3*math.cos(yaw),3*math.sin(yaw),.65))
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
    for o,name,version in objects:
        shift = right * (-.40 if version == 'old' else .40)
        for v,p in zip(o.data.vertices,streams[name][index]):
            v.co = p+shift
        o.data.update()
    row = d['frames'][sample['measurementIndex']]; contacts = row['versions']['new']['parts']
    font.body = 'LEFT: OLD APPEARANCE05     /     RIGHT: COMPLETE FOOTWEAR08\n'+sample['phase'].upper()+'   t='+format(sample['timeS'],'.3f')+'s   source sample '+str(sample['measurementIndex'])+'\nNEW UPPER/BODY '+str(contacts[0]['bodyTriangleContactPairs'])+'  SOLE/BODY '+str(contacts[1]['bodyTriangleContactPairs'])+'  / BIKE-FREE DIAGNOSTIC; UNACCEPTED'
    bpy.context.view_layer.update(); border = 1.
    for o,name,version in objects:
        for v in o.data.vertices:
            q = world_to_camera_view(scene,camera,o.matrix_world@v.co)
            border = min(border,q.x,q.y,1-q.x,1-q.y)
    assert border >= .02, (index,border)
    minimum = min(minimum,border); p = out/f'{index:04d}.png'; scene.render.filepath = str(p)
    bpy.ops.render.render(write_still=True)
    frames.append({**sample,'PNG_SHA256':sha(p),'minimumNormalizedBorder':border,'cameraTargetM':list(target),'cameraYawRadians':yaw})
    if index%12 == 0:
        print('FOOTWEAR_PLAYED',index,flush=True)
assert pins == {n:sha(folder/n) for n in pins}; assert sha(source) == d['pins'][str(source)]
report = {'status':'UNACCEPTED matched native footwear movement; parent judges','pins':pins,'sourceSHA256':sha(source),
    'recipeSHA256':sha(__file__),'FPS':12,'resolution':[1280,720],'frames':frames,'minimumNormalizedBorder':minimum,
    'render':'CyclesCPU2threads4samples','orthoHorizontalM':1.9,
    'limits':['Source materials and UVs preserved; baked native geometry normals recomputed. No cosmetic recoloring.',
        'Every fourth48Hz measurement shown at12Hz; original529 FK followed by96 explicit ankle20deg/toe15deg samples.',
        'Footwear, feet, lower calves and jeans cuffs only. No bike, supported peg contact or actual game/live collision claim.',
        'New08 fails added ankle/toe motion despite rest and original FK passing; all garments remain unaccepted.']}
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
print('FOOTWEAR_REVIEW_READY',sha(out/'review.json'),flush=True)
