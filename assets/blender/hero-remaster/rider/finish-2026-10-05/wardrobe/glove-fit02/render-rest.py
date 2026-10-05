"""Source/fitted rest rotation and canonical hand context; no skin/action."""
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


def mesh_object(name, vertices, faces, labels=None, gray=(.55, .55, .55)):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    colors = [gray, (.85, .25, .2), (.9, .55, .1), (.18, .72, .22), (.12, .4, .9), (.68, .22, .8)] if labels is not None else [gray]
    for index, color in enumerate(colors):
        material = bpy.data.materials.new(name + str(index))
        material.use_nodes = True
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
        material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .7
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        if labels is not None:
            ids = labels[np.array(polygon.vertices)]
            polygon.material_index = int(ids[0]) if (ids == ids[0]).all() else 0
        polygon.use_smooth = True
    return obj


def main():
    parser = argparse.ArgumentParser()
    for key in ['fit', 'source', 'foundation', 'out']:
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    fit = json.loads(Path(args.fit).read_text())
    source = np.load(args.source)
    glove = np.load(fit['candidates']['R']['path'])
    foundation = np.load(args.foundation)
    matrix = np.array(fit['properInitialMatrix'])
    inverse = np.linalg.inv(matrix)
    wrist_source = np.array(json.loads(Path('docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/semantic-registration.json').read_text())['gloves']['coarsePalmRegistration']['R']['sourceWristCentre'])
    names = foundation['boneNames'].tolist()
    wrist_target = foundation['boneRest'][names.index('hand.R'), :3, 3]
    def display(points, fitted=False, offset=0):
        if fitted:
            points = (points - wrist_target) @ inverse.T + wrist_source
        points = points[:, [0, 2, 1]].copy()
        points[:, 1] *= -1
        points[:, 0] += offset
        return points
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    mesh_object('Exact source left', display(source['vertices'], offset=-1.1), source['faces'], source['branchLabels'])
    mesh_object('Fitted rest right', display(glove['vertices'], fitted=True, offset=1.1), glove['faces'], source['branchLabels'])
    columns = [index for index, name in enumerate(names) if name == 'hand.R' or (name.endswith('.R') and any(name.startswith(digit + '_') for digit in ['pinky', 'ring', 'middle', 'index', 'thumb']))]
    active = foundation['canonicalWeights'][:, columns].sum(1) > .2
    hand_faces = foundation['canonicalTriangles'][active[foundation['canonicalTriangles']].any(1)]
    mesh_object('Canonical hand right', display(foundation['canonicalXYZ'], fitted=True, offset=1.1), hand_faces, gray=(.24, .24, .27))
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 6
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = 960
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.use_persistent_data = True
    scene.view_settings.view_transform = 'Standard'
    scene.world.color = (.12, .12, .12)
    for position, energy in [((2, -4, 4), 500), ((-3, -2, 1), 300), ((1, 3, 3), 500)]:
        light = bpy.data.lights.new('Silent area', 'AREA')
        light.energy = energy
        light.size = 4
        lamp = bpy.data.objects.new('Silent area', light)
        bpy.context.collection.objects.link(lamp)
        lamp.location = position
        lamp.rotation_euler = (Vector((0, 0, 0)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data = bpy.data.cameras.new('Paired rest review')
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 4.4
    camera = bpy.data.objects.new('Paired rest review', camera_data)
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
        'fitSHA256': sha(args.fit), 'sourceSHA256': sha(args.source), 'foundationSHA256': sha(args.foundation), 'frames': pins, 'fps': 12,
        'displayNormalization': 'Source left; fitted R and canonical hand right, both inverse initial proper affine then same source proper Y-up/Z-front to Blender Z-up/-Y-front basis. Camera rotates; geometry remains rest.',
        'limits': 'Rest fitting context only. Inverse affine normalizes scale for donor comparison, not a native asset transform. Canonical hand uses weight-selected context triangles. No skin/native/engine/PBR/art pass.'}, indent=2) + '\n')


if __name__ == '__main__':
    main()
