"""CPU-only model inspection. Render editable Blender masters without game build/GPU.

blender -b --python-exit-code 1 --python preview.py -- --in out/quarry-drill.source.blend --out out/quarry-drill-preview.png
"""
import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument('--in', dest='source', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--azimuth', type=float, default=43)
opt = parser.parse_args(args)
bpy.ops.wm.open_mainfile(filepath=str(Path(opt.source).resolve()))

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 20
scene.render.resolution_x = 720
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(Path(opt.out).resolve())
scene.render.film_transparent = False
scene.world.color = (0.18, 0.24, 0.27)

meshes = [o for o in scene.objects if o.type == 'MESH']
corners = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector(tuple(min(p[i] for p in corners) for i in range(3)))
hi = Vector(tuple(max(p[i] for p in corners) for i in range(3)))
center = (lo + hi) * 0.5
span = hi - lo
az = math.radians(opt.azimuth)

bpy.ops.object.camera_add(location=(center.x + math.cos(az) * 1.3 * span.length,
                                center.y - math.sin(az) * 1.3 * span.length,
                                center.z + 0.55 * span.length))
camera = bpy.context.object
direction = center - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = max(span.x * 1.45, span.y * 1.8, span.z * 1.48)
scene.camera = camera

for name, location, power, size in [
    ('warm key', (center.x - 10, center.y - 8, hi.z + 10), 2800, 12),
    ('cool fill', (center.x + 6, center.y + 10, hi.z + 5), 1900, 11),
]:
    bpy.ops.object.light_add(type='AREA', location=location)
    lamp = bpy.context.object
    lamp.name = name
    lamp.data.energy = power
    lamp.data.shape = 'DISK'
    lamp.data.size = size
    lamp.rotation_euler = (center - lamp.location).to_track_quat('-Z', 'Y').to_euler()

ground = bpy.data.materials.new('preview gray stage')
ground.diffuse_color = (0.15, 0.17, 0.17, 1)
ground.use_nodes = True
bpy.ops.mesh.primitive_plane_add(size=max(span.x, span.y) * 2.8, location=(center.x, center.y, lo.z - 0.05))
bpy.context.object.data.materials.append(ground)
scene.view_settings.view_transform = 'AgX'
bpy.ops.render.render(write_still=True)
