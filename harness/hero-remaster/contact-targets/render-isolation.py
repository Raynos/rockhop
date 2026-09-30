"""Read-only matched source grip isolation. Cycles CPU; no native Metal job/export."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
source, out = Path(args.input), Path(args.output)
assert not out.exists(), 'fresh evidence only'
out.mkdir(parents=True)
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
assert len(meshes) == 1
mesh = meshes[0]
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.resolution_x = 640
scene.render.resolution_y = 384
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('neutral studio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.12, .12, .12, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .7
scene.view_settings.view_transform = 'AgX'
target = Vector((.924, -.3425, .779))
camera = bpy.data.objects.new('matched camera', bpy.data.cameras.new('matched camera'))
scene.collection.objects.link(camera)
camera.location = target + Vector((.21, -.19, .11))
camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .235
scene.camera = camera
for i, (offset, energy, size) in enumerate([((.35, -.2, .35), .25, .4), ((-.15, -.35, .2), .15, .3), ((.0, .2, .25), .20, .3)]):
    lamp = bpy.data.objects.new('studio'+str(i), bpy.data.lights.new('studio'+str(i), 'AREA'))
    scene.collection.objects.link(lamp)
    lamp.location = target+Vector(offset)
    lamp.rotation_euler = (target-lamp.location).to_track_quat('-Z', 'Y').to_euler()
    lamp.data.energy = energy
    lamp.data.shape = 'DISK'
    lamp.data.size = size
source_materials = list(mesh.data.materials)
records = []
for mode in ['pbr', 'gray']:
    if mode == 'gray':
        neutral = bpy.data.materials.new('inspection gray')
        neutral.use_nodes = True
        shader = neutral.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (.45, .45, .45, 1)
        shader.inputs['Roughness'].default_value = .6
        mesh.data.materials.clear()
        mesh.data.materials.append(neutral)
    scene.render.filepath = str(out/(mode+'.png'))
    bpy.ops.render.render(write_still=True)
    data = Path(scene.render.filepath).read_bytes()
    records.append({'mode': mode, 'path': str(Path(scene.render.filepath)), 'sha256': hashlib.sha256(data).hexdigest()})
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
(out/'manifest.json').write_text(json.dumps({'scope': 'source grip PBR/neutral-gray isolation only; no rider or contact gate acceptance',
    'input': str(source), 'sourceSHA256': digest, 'sourceMeshTriangles': len(mesh.data.loop_triangles) or len(mesh.data.polygons),
    'sourceMaterialNames': [m.name for m in source_materials], 'blenderVersion': bpy.app.version_string,
    'engine': 'Cycles CPU', 'samples': 16, 'denoising': False, 'size': [640, 384], 'orthoScaleM': .235,
    'cameraLocation': list(camera.location), 'cameraEuler': list(camera.rotation_euler), 'target': list(target), 'renders': records}, indent=2)+'\n')
