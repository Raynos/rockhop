"""Fixed-world collar closeups; CPU only, no display rescaling of cut body."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--input', required=True)
p.add_argument('--out', required=True)
p.add_argument('--gray', action='store_true')
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
source, out = Path(a.input).resolve(), Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
if (out/'manifest.json').exists():
    raise RuntimeError('Frozen render exists')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
before = sha(source)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == 'MESH']
if a.gray:
    mat = bpy.data.materials.new('Neutral geometry diagnostic')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (.42, .42, .42, 1)
    bsdf.inputs['Roughness'].default_value = .65
    for o in meshes:
        o.data.materials.clear()
        o.data.materials.append(mat)
world = bpy.data.worlds.new('Matched studio')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.16, .16, .16, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .65
scene.world = world
target = Vector((0, 0, 1.50))
for name, location, energy, size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = energy, 'DISK', size
    o = bpy.data.objects.new(name, data)
    scene.collection.objects.link(o)
    o.location = location
    o.rotation_euler = (target-o.location).to_track_quat('-Z','Y').to_euler()
data = bpy.data.cameras.new('Fixed-world collar')
camera = bpy.data.objects.new('Fixed-world collar', data)
scene.collection.objects.link(camera)
scene.camera = camera
data.type, data.ortho_scale = 'ORTHO', .62
scene.render.engine, scene.cycles.device = 'CYCLES', 'CPU'
scene.cycles.samples, scene.cycles.use_denoising = 16, True
scene.render.threads_mode, scene.render.threads = 'FIXED', 4
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
rows = []
for i, yaw in enumerate([0,45,90,180]):
    angle = math.radians(yaw)
    camera.location = target+Vector((4*math.sin(angle),-4*math.cos(angle),.12))
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
    path = out/f'{i:04d}.png'
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    rows.append({'yaw':yaw,'file':path.name,'sha256':sha(path),'cameraMatrix':[list(row) for row in camera.matrix_world]})
assert before == sha(source)
(out/'manifest.json').write_text(json.dumps({'status':'Unaccepted static collar extraction diagnostic; no attachment or rig',
    'input':str(source),'inputSHA256':before,'inputSHA256After':sha(source),'rendererSHA256':sha(__file__),
    'materialMode':'neutral-gray' if a.gray else 'native-PBR','worldSpaceNormalization':'none; canonical metres preserved',
    'target':list(target),'orthoScale':.62,'backend':'Cycles CPU','threads':4,'samples':16,
    'blender':bpy.app.version_string,'views':rows},indent=2)+'\n')
