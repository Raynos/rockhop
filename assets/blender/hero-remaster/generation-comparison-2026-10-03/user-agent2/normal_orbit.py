"""One derived orientation/smooth-normal comparison and geometric sections."""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from donor_orbit import material, mesh_object, sha


def main():
    parser = argparse.ArgumentParser()
    for name in ['native', 'native-sha256', 'preparation', 'preparation-sha256', 'out']:
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    for name in ['native', 'preparation']:
        if sha(getattr(args, name)) != getattr(args, name + '_sha256'):
            raise ValueError('Frozen bytes changed: ' + name)
    previous = json.loads(Path(args.preparation).read_text())
    if previous['nativeSHA256'] != args.native_sha256: raise ValueError('Different native mesh')
    derived = Path(args.preparation).parent / 'derived-normals.npz'
    if sha(derived) != previous['derivedArchiveSHA256']: raise ValueError('Derived normals changed')
    output = Path(args.out)
    if output.exists(): raise FileExistsError('Fresh diagnostic directory required')
    with np.load(args.native, allow_pickle=False) as raw:
        vertices, faces = raw['vertices'].copy(), raw['faces'].copy()
    with np.load(derived, allow_pickle=False) as d:
        corrected_faces, normals = d['faces'].copy(), d['normals'].copy()
    if not np.array_equal(np.sort(faces, axis=1), np.sort(corrected_faces, axis=1)):
        raise ValueError('Triangle geometry changed')
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    neutral = mesh_object('Current raw smooth', vertices.tolist(), faces[:, ::-1].tolist(), material('Current grey', (.55, .55, .55)))
    flat = mesh_object('Same geometry flat', vertices.tolist(), faces[:, ::-1].tolist(), material('Flat grey', (.55, .55, .55)))
    for polygon in flat.data.polygons: polygon.use_smooth = False
    corrected = mesh_object('Derived orientation and smooth normals', vertices.tolist(), corrected_faces.tolist(), material('Recomputed grey', (.55, .55, .55)))
    corrected.data.normals_split_custom_set_from_vertices(normals.tolist())
    matrix = Matrix(previous['previewRawToBlenderMatrixRows'])
    neutral.matrix_world = matrix; flat.matrix_world = matrix; corrected.matrix_world = matrix
    target = Vector(previous['camera']['targetM'])
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 8
    scene.render.resolution_x = 320; scene.render.resolution_y = 320; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.film_transparent = False
    scene.world.color = (.2, .2, .2); scene.view_settings.view_transform = 'Standard'
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 4; scene.render.use_persistent_data = True
    for name, location, watts in [('Key', (3, -3, 4), 450), ('Fill', (2, 4, 3), 350), ('Rim', (-3, 0, 4), 400)]:
        light = bpy.data.lights.new(name, 'AREA'); light.energy = watts; light.size = 4
        obj = bpy.data.objects.new(name, light); bpy.context.collection.objects.link(obj); obj.location = location
        obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Same geometric orbit'); data.type = 'ORTHO'; data.ortho_scale = previous['camera']['orthoScaleM']
    camera = bpy.data.objects.new('Same geometric orbit', data); bpy.context.collection.objects.link(camera); scene.camera = camera
    sections = Path(args.preparation).parent / 'cross-sections.npz'
    if sha(sections) != previous['sectionsArchiveSHA256']: raise ValueError('Section bytes changed')
    plot_objects = []
    def emission(name, colour):
        mat = bpy.data.materials.new(name); mat.use_nodes = True
        mat.node_tree.nodes.clear()
        node = mat.node_tree.nodes.new('ShaderNodeEmission'); node.inputs['Color'].default_value = (*colour, 1)
        end = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(node.outputs[0], end.inputs['Surface'])
        return mat
    ink = emission('Exact geometry section blue', (.2, .65, 1))
    letters = emission('Section annotation white', (.85, .85, .85))
    def label(text, x, y, size=.044):
        curve = bpy.data.curves.new(text, 'FONT'); curve.body = text; curve.size = size
        obj = bpy.data.objects.new(text, curve); bpy.context.collection.objects.link(obj)
        obj.location = (x, y, .01); curve.materials.append(letters); plot_objects.append(obj)
    for obj in [neutral, flat, corrected]: obj.hide_render = True
    with np.load(sections, allow_pickle=False) as cuts:
        for index, plane in enumerate(previous['sectionPlanes']):
            offset = ((-.76, .34), (.76, .34), (-.76, -.42), (.76, -.42))[index]
            lines = cuts[plane['name']]
            curve = bpy.data.curves.new(plane['name'], 'CURVE'); curve.dimensions = '3D'; curve.bevel_depth = .001
            for line in lines:
                spline = curve.splines.new('POLY'); spline.points.add(1)
                for point, world in zip(spline.points, line):
                    point.co = (float(world[1])+offset[0], float(world[0])+offset[1], 0, 1)
            obj = bpy.data.objects.new(plane['name'], curve); bpy.context.collection.objects.link(obj)
            curve.materials.append(ink); plot_objects.append(obj)
            label(f"Z={plane['worldZ']:.3f} m; {plane['segments']} segments", offset[0]-.61, offset[1]-.25)
    label('Raw hoodie: four exact horizontal geometry cuts', -1.4, .87, .065)
    label('Horizontal: world Y (width). Vertical: world X (depth). Same metre scale.', -1.4, -.86, .045)
    label('Layout offsets only; no curve fitting, cleanup or vertex movement.', -1.4, -.94, .04)
    camera.location = (0, 0, 5); camera.rotation_euler = (0, 0, 0); data.ortho_scale = 3.05
    scene.render.resolution_x = 1024; scene.render.resolution_y = 680
    section_png = Path(args.preparation).parent / 'cross-sections.png'
    scene.render.filepath = str(section_png); bpy.ops.render.render(write_still=True)
    for obj in plot_objects: obj.hide_render = True
    data.ortho_scale = previous['camera']['orthoScaleM']
    scene.render.resolution_x = 320; scene.render.resolution_y = 320
    output.mkdir(parents=True); rows = []
    for family, selected in [('canonical', neutral), ('donor', flat), ('corrected', corrected)]:
        directory = output / family; directory.mkdir()
        for obj in [neutral, flat, corrected]: obj.hide_render = obj != selected
        for frame in range(48):
            yaw = frame * 2 * math.pi / 48
            camera.location = target + Vector((5 * math.cos(yaw), 5 * math.sin(yaw), .12))
            camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
            path = directory / f'{frame:03d}.png'; scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            rows.append({'family': family, 'frame': frame, 'yawDegrees': frame * 7.5, 'path': str(path), 'sha256': sha(path)})
    result = {'accepted': False, 'kind': 'ONE derived current smooth/flat/recomputed smooth normal follow-up',
              'nativeSHA256': sha(args.native), 'preparationSHA256': sha(args.preparation),
              'recipeSHA256': sha(__file__), 'helperSHA256': sha(Path(__file__).with_name('donor_orbit.py')),
              'crossSectionsPNG': str(section_png), 'crossSectionsSHA256': sha(section_png),
              'crossSectionDiagram': 'Exact plane intersections projected world Y/X in metres; four layout offsets',
              'sameVerticesAndTriangleSets': True, 'normalModes': ['current smooth', 'current flat', 'derived orientation control with area-weighted smooth'],
              'remainingDerivedWindingWitnesses': previous['derivedAudit']['equalDirectionTwoFaceEdges'],
              'framesPerFamily': 48, 'fps': 8, 'resolution': [320, 320], 'rows': rows,
              'limits': ['Derived display only; raw archive unchanged', 'Orientation control can leave nonmanifold conflicts; no cleanup/remesh', 'No inference, art/fit/rig or generator-family judgment']}
    (output / 'orbit.json').write_text(json.dumps(result, indent=2) + '\n')
    if sha(args.native) != args.native_sha256: raise ValueError('Native changed')


if __name__ == '__main__': main()
