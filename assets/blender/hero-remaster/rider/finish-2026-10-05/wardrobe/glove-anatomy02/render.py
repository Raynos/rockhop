"""Silent moving source topology review; exact donor XYZ, no fit or skin."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    data = np.load(args.data)
    # Fixed proper source Y-up/Z-front to Blender Z-up/-Y-front transform.
    vertices = data['vertices'][:, [0, 2, 1]].copy()
    vertices[:, 1] *= -1
    labels = data['branchLabels']
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    mesh = bpy.data.meshes.new('Exact donor prototype')
    mesh.from_pydata(vertices.tolist(), [], data['faces'].tolist())
    mesh.update()
    obj = bpy.data.objects.new('Exact donor prototype', mesh)
    bpy.context.collection.objects.link(obj)
    colors = [(0.45, .45, .45), (.85, .25, .2), (.9, .55, .1), (.18, .72, .22), (.12, .4, .9), (.68, .22, .8)]
    names = ['Unclassified palm/web/cuff', 'Pinky', 'Ring', 'Middle', 'Index', 'Thumb']
    for name, color in zip(names, colors):
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
        material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .6
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        ids = labels[np.array(polygon.vertices)]
        # Only complete classified triangles; transition rows stay neutral.
        polygon.material_index = int(ids[0]) if (ids == ids[0]).all() else 0
        polygon.use_smooth = True
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 6
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.use_persistent_data = True
    scene.view_settings.view_transform = 'Standard'
    scene.world.color = (.12, .12, .12)
    for position, energy in [((2, -3, 4), 450), ((-3, -2, 1), 250), ((1, 3, 3), 450)]:
        light = bpy.data.lights.new('Silent area', 'AREA')
        light.energy = energy
        light.size = 4
        lamp = bpy.data.objects.new('Silent area', light)
        bpy.context.collection.objects.link(lamp)
        lamp.location = position
        lamp.rotation_euler = (Vector((0, 0, 0)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data = bpy.data.cameras.new('Source rotation review')
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 2.7
    camera = bpy.data.objects.new('Source rotation review', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    frames = out / 'frames'
    frames.mkdir()
    pins = []
    for index in range(36):
        angle = 2 * np.pi * index / 36
        camera.location = (3 * np.sin(angle), -3 * np.cos(angle), .5)
        camera.rotation_euler = (Vector((0, .15, -.02)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        target = frames / f'{index:03}.png'
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        pins.append({'index': index, 'sha256': sha(target)})
    (out / 'render.json').write_text(json.dumps({'accepted': False, 'recipeSHA256': sha(__file__),
        'source': {'path': args.data, 'sha256': sha(args.data)}, 'frames': pins, 'fps': 12,
        'colors': dict(zip(names, [list(c) for c in colors])), 'geometry': 'Source prototype XYZ/triangles unchanged under one proper review-coordinate rotation; camera moves.',
        'limits': 'Distal five-branch source topology review only. Palm/web remains neutral; no fit, skin, source joint anatomy, handedness, original PBR, native motion, engine or art pass.'}, indent=2) + '\n')


if __name__ == '__main__':
    main()
