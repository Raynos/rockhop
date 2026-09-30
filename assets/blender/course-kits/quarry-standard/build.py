"""Author editable full/LOD quarry machines. No runtime/public files or GPU render.

blender -b --python-exit-code 1 --python assets/blender/course-kits/quarry-standard/build.py -- --out assets/blender/course-kits/quarry-standard/out

X is the course axis, Blender Z is world up. glTF conversion produces Y-up
assets. Each origin is the ground contact, and all models are cosmetic.
"""
import argparse
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument('--out', required=True)
out = Path(parser.parse_args(args).out).resolve()
out.mkdir(parents=True, exist_ok=True)
random.seed(3301)


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


clear()
asset_collection = None
LOW = False


def mat(name, color, metal=0, rough=0.7):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    return m


yellow = mat('01 quarry safety ochre / chipped enamel', (0.72, 0.42, 0.075), 0.34, 0.57)
oxide = mat('02 weathered red oxide structural steel', (0.35, 0.12, 0.063), 0.49, 0.69)
galv = mat('03 dusted galvanized steel', (0.39, 0.43, 0.41), 0.67, 0.48)
dark = mat('04 oiled machinery / shadow steel', (0.073, 0.081, 0.078), 0.68, 0.57)
rubber = mat('05 deep tire rubber', (0.026, 0.031, 0.032), 0, 0.91)
glass = mat('06 dirty blue cab glass', (0.075, 0.18, 0.21), 0.05, 0.25)
ore = mat('07 iron-rich crushed sandstone', (0.39, 0.29, 0.19), 0.03, 0.95)
cream = mat('08 pale worn identification panels', (0.68, 0.65, 0.53), 0.12, 0.74)


def paint_texture():
    w = h = 256
    img = bpy.data.images.new('RH quarry enamel salt/abrasion', width=w, height=h)
    pixels = [0.0] * (w * h * 4)
    for y in range(h):
        for x in range(w):
            u, v = x / w, y / h
            dust = 0.07 * math.exp(-((v - 0.16) / 0.23) ** 2)
            wear = 0.025 * math.sin(u * 72 + v * 19) + 0.012 * math.sin(u * 203 - v * 91)
            gouge = 0.0
            for sx in (0.1, 0.24, 0.68, 0.82):
                d = abs(u - sx - 0.002 * math.sin(v * 27))
                if d < 0.0025 and v > 0.18:
                    gouge = 0.09 * (1 - d / 0.0025)
            c = (max(0, 0.70 + dust - gouge + wear),
                 max(0, 0.385 + dust * 0.9 - gouge * 0.5 + wear),
                 max(0, 0.06 + dust * 0.8 - gouge * 0.25 + wear * 0.4))
            i = (y * w + x) * 4
            pixels[i:i+4] = (*c, 1)
    img.pixels.foreach_set(pixels)
    img.filepath_raw = str(out / 'quarry-enamel-albedo.png')
    img.file_format = 'PNG'
    img.save(); img.pack()
    p = yellow.node_tree.nodes.get('Principled BSDF')
    tex = yellow.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = img
    yellow.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])


paint_texture()


def move(o, material):
    for collection in list(o.users_collection):
        collection.objects.unlink(o)
    asset_collection.objects.link(o)
    if o.type == 'MESH':
        o.data.materials.append(material)
    else:
        o.data.materials.append(material)
    return o


def soft(o, width=0.05):
    bevel = o.modifiers.new('real manufactured bevel', 'BEVEL')
    bevel.width = width
    bevel.segments = 1 if LOW else 2
    bevel.affect = 'EDGES'
    normals = o.modifiers.new('weighted panel normals', 'WEIGHTED_NORMAL')
    normals.keep_sharp = True
    return o


def box(name, loc, size, material, edge=0.0, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    if rot: o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move(o, material)
    if edge: soft(o, edge)
    return o


def cyl(name, loc, radius, depth, material, vertices=None, rot=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices or (10 if LOW else 20), radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    if rot: o.rotation_euler = rot
    move(o, material)
    if radius > 0.1: soft(o, min(0.04, radius * 0.12))
    return o


def torus(name, loc, major, minor, material, rot=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=12 if LOW else 24, minor_segments=5 if LOW else 8,
                                    location=loc, major_radius=major, minor_radius=minor)
    o = bpy.context.object
    o.name = name
    if rot: o.rotation_euler = rot
    return move(o, material)


def mesh(name, vertices, faces, material, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    asset_collection.objects.link(o)
    o.data.materials.append(material)
    for p in data.polygons: p.use_smooth = smooth
    return o


def tube(name, points, radius, material):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 1 if LOW else 3
    line = curve.splines.new('POLY')
    line.points.add(len(points) - 1)
    for p, xyz in zip(line.points, points): p.co = (*xyz, 1)
    o = bpy.data.objects.new(name, curve)
    asset_collection.objects.link(o)
    curve.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target='MESH')
    return o


def beam(name, a, b, width, material):
    va, vb = Vector(a), Vector(b)
    o = box(name, (va + vb) * 0.5, (width, width, (vb - va).length), material)
    o.rotation_euler = (vb - va).to_track_quat('Z', 'Y').to_euler()
    return o


def bevel_mesh(name, rings, material):
    """Hand-faired shell from successive x sections of (x, outline y/z)."""
    vertices, faces = [], []
    sides = len(rings[0][1])
    for x, contour in rings:
        vertices += [(x, y, z) for y, z in contour]
    for i in range(len(rings) - 1):
        for j in range(sides - 1):
            faces.append((i * sides + j, (i + 1) * sides + j,
                          (i + 1) * sides + j + 1, i * sides + j + 1))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(rings) - 1) * sides + j for j in range(sides)))
    o = mesh(name, vertices, faces, material, True)
    soft(o, 0.04)
    return o


def track_unit(x, y, length=5.5):
    box('crawler heavy side frame', (x, y, 0.84), (length, 0.64, 0.58), dark, 0.12)
    for k in range(8 if not LOW else 5):
        xx = x - length * 0.39 + k * (length * 0.78 / (7 if not LOW else 4))
        cyl('crawler bogie wheel', (xx, y, 0.71), 0.37, 0.69, galv, rot=(math.pi / 2, 0, 0))
    # The track belt is an actual closed heavy loop, with thick visible grousers.
    tube('continuous crawler belt', [(x-length*0.48, y, 0.8), (x-length*0.36, y, 0.24),
         (x+length*0.35, y, 0.24), (x+length*0.48, y, 0.8),
         (x+length*0.3, y, 1.28), (x-length*0.33, y, 1.28),
         (x-length*0.48, y, 0.8)], 0.19, rubber)
    if not LOW:
        for k in range(11):
            xx = x - length*0.37 + k * length*0.074
            box('steel grouser tooth', (xx, y, 0.2), (0.13, 0.9, 0.1), galv, 0.015)


def drill():
    for y in (-1.63, 1.63): track_unit(0, y)
    box('rotating machine platform', (0, 0, 1.62), (6.2, 3.8, 0.56), galv, 0.12)
    cyl('heavy slew ring', (0, 0, 1.95), 1.27, 0.35, dark)
    box('engine and compressor bay', (-1.72, -0.12, 3.03), (2.9, 2.4, 1.6), yellow, 0.12)
    for i in range(5 if not LOW else 3):
        box('louvered engine intake', (-3.18, -0.96 + i * (0.46 if not LOW else 0.8), 3.02),
            (0.07, 0.26, 0.86), dark, 0.015)
    box('operator cab fairing', (1.05, 0.63, 3.30), (2.38, 1.62, 2.3), yellow, 0.11)
    box('angled front cab glass', (2.29, 0.62, 3.70), (0.07, 1.4, 1.12), glass, 0.015, rot=(0, -0.12, 0))
    box('large side window', (1.14, 1.48, 3.72), (1.75, 0.06, 1.12), glass, 0.015)
    box('cab roof / work light plinth', (1.0, 0.60, 4.55), (2.65, 1.92, 0.22), dark, 0.04)
    for side in (-1, 1):
        box('mast continuous box chord', (3.10, side * 0.85, 9.9), (0.34, 0.34, 14.2), oxide, 0.04)
        for k in range(5 if not LOW else 3):
            z = 4.2 + k * (2.75 if not LOW else 5.5)
            beam('mast diagonal structural brace', (3.10, -0.83, z), (3.10, 0.83, z + 2.3), 0.115, galv)
    for z in (4.15, 10.5, 16.55):
        box('mast transverse tie', (3.1, 0, z), (0.45, 2.05, 0.3), dark, 0.02)
    cyl('rotary drilling head', (3.1, 0, 10.8), 0.56, 1.35, yellow)
    cyl('steel drill string', (3.1, 0, 4.78), 0.13, 8.1, galv, 12)
    cyl('cutting bit', (3.1, 0, 0.65), 0.38, 0.62, dark)
    for side in (-1, 1):
        beam('hydraulic raise ram sleeve', (1.12, side*0.97, 2.03), (2.78, side*0.75, 7.8), 0.23, dark)
        beam('hydraulic chrome piston', (2.78, side*0.75, 7.8), (3.08, side*0.72, 9.2), 0.13, galv)
        tube('drill hydraulic hose', [(0.15,side*1.2,2.8),(1.4,side*1.45,3.6),
             (2.4,side*1.35,6.5),(3.12,side*1.0,9.4)],0.07,rubber)
    box('vertical identifying band', (3.34, 0, 13.5), (0.045, 1.15, 2.6), cream)


def crusher():
    for y in (-2.85, 2.85):
        box('crusher fabricated skid', (0, y, 0.56), (11, 0.68, 1.05), dark, 0.08)
        for x in (-4, 0, 4): box('skid cross sleeper', (x, y, 0.22), (0.5, 1.6, 0.44), galv, 0.04)
    box('jaw chamber armored cheeks', (-1.85, 0, 5.0), (6.4, 4.6, 7.0), oxide, 0.12)
    # Flared intake is a shaped funnel, not a tall rectangular stack.
    rings = []
    for z, sx, sy in [(7.2,3.4,2.5),(8.1,4.5,3.45),(10.5,5.8,4.2)]:
        rings.append((-1.9, [(-sy,-sx),(sy,-sx),(sy,sx),(-sy,sx)]))
    # Four sloping walls with an open top.
    bottom = [(-5.3,-2.5,7.2),(1.5,-2.5,7.2),(1.5,2.5,7.2),(-5.3,2.5,7.2)]
    top = [(-7.7,-4.2,10.5),(3.9,-4.2,10.5),(3.9,4.2,10.5),(-7.7,4.2,10.5)]
    verts = bottom + top
    mesh('open flared ore hopper', verts, [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], yellow)
    for y in (-4.2, 4.2):
        box('hopper heavy lip', (-1.9, y, 10.57), (11.8,0.23,0.22), dark, 0.04)
    for x in (-7.7,3.9): box('hopper end lip', (x,0,10.57),(0.23,8.6,0.22),dark,0.04)
    for i in range(8 if not LOW else 4):
        x=-6.6+i*(1.25 if not LOW else 2.55)
        box('grizzly sorting bar', (x,0,8.9),(0.17,6.3,0.22),galv,0.02)
    for side in (-1, 1):
        cyl('guarded jaw flywheel', (1.1, side*2.48, 5.17), 1.31, 0.28, dark,
            rot=(math.pi/2,0,0))
        torus('cast flywheel rim', (1.1, side*2.67, 5.17), 1.04, 0.14, yellow, rot=(math.pi/2,0,0))
        for k in range(4):
            a=k*math.pi/2
            beam('flywheel spoke', (1.1,side*2.7,5.17),
                 (1.1+0.87*math.cos(a),side*2.7,5.17+0.87*math.sin(a)),0.13,galv)
    # A real transfer belt with separated upper/lower chords, visible rollers,
    # splayed support trestle and guarded head pulley.
    a=(2.2,-1.4,3.0); b=(19.2,-1.4,7.6)
    for side in (-1,1):
        beam('conveyor truss upper', (a[0],side*1.55,a[2]),(b[0],side*1.55,b[2]),0.25,oxide)
        beam('conveyor truss lower', (a[0],side*1.55,a[2]-1.2),(b[0],side*1.55,b[2]-1.2),0.19,dark)
        for k in range(6 if not LOW else 3):
            t=k/(5 if not LOW else 2)
            x=a[0]+(b[0]-a[0])*t; z=a[2]+(b[2]-a[2])*t
            beam('conveyor diagonal', (x,side*1.55,z-1.2),(x+2.7,side*1.55,z+0.7),0.11,galv)
    beam('rubber conveyor upper belt',(2.2,0,3.2),(19.2,0,7.8),3.0,rubber)
    beam('conveyor support A', (13,-2.7,0.2),(12.4,-1.5,5.7),0.25,dark)
    beam('conveyor support B', (13,2.7,0.2),(12.4,1.5,5.7),0.25,dark)
    cyl('head pulley', (19.15,0,7.42),0.65,3.5,galv,rot=(math.pi/2,0,0))
    box('screen maintenance catwalk',(-1.9,4.8,6.8),(9.7,1.25,0.22),galv,0.03)
    for x in (-6.4,-2.3,2.1):
        box('catwalk vertical guard', (x,5.35,7.4), (0.09,0.09,1.28), yellow)
    tube('catwalk safety rail',[(-6.5,5.35,8.05),(-2.3,5.35,8.05),(2.2,5.35,8.05)],0.055,yellow)


def haul():
    box('heavy dump chassis', (0,0,1.66),(10.4,4.1,0.62),dark,0.13)
    for x in (-3.7,2.3):
        for side in (-1,1):
            y=side*2.24
            cyl('large earthmover tire', (x,y,1.43),1.36,0.84,rubber,
                vertices=12 if LOW else 28,rot=(math.pi/2,0,0))
            cyl('dished wheel center', (x,y+side*0.46,1.43),0.58,0.88,galv,
                vertices=10 if LOW else 18,rot=(math.pi/2,0,0))
            if not LOW:
                for k in range(14):
                    a=k*2*math.pi/14
                    box('real raised tire lug',(x+math.sin(a)*1.26,y,1.43+math.cos(a)*1.26),
                        (0.34,0.91,0.16),rubber,0.02,rot=(0,-a,0))
    box('truck engine hood', (-3.25,0,3.02),(3.9,3.75,1.55),yellow,0.18)
    box('front radiator grille',(-5.24,0,3.0),(0.1,3.1,1.26),dark,0.02)
    for i in range(7 if not LOW else 4):
        box('radiator vertical slat',(-5.3,-1.35+i*(0.45 if not LOW else 0.9),3.02),
            (0.08,0.1,1.14),galv)
    box('cab windshield fairing',(-2.9,1.08,4.52),(2.68,1.57,1.9),yellow,0.09)
    box('very large side glazing',(-2.92,1.92,4.75),(2.17,0.055,1.1),glass,0.02)
    box('front windshield',(-4.28,1.08,4.75),(0.06,1.45,1.1),glass,0.02)
    box('wide roof edge',(-2.9,1.02,5.54),(2.85,1.8,0.19),dark,0.04)
    # Open dump box with cut steel wall thickness and upward flared lip.
    bed = [(-0.8,-1.95,3.1),(5.6,-1.95,3.1),(5.6,1.95,3.1),(-0.8,1.95,3.1),
           (-1.2,-2.37,6.6),(6.0,-2.37,6.6),(6.0,2.37,6.6),(-1.2,2.37,6.6)]
    mesh('high-sided open dump vessel', bed,
         [(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],yellow)
    for side in (-1,1):
        for x in (0.1,1.5,3.0,4.5):
            beam('real bed side stiffener',(x,side*2.03,3.2),(x-0.3,side*2.33,6.6),0.16,oxide)
        beam('dump hydraulic cylinder',(1.3,side*0.78,1.9),(3.5,side*0.78,4.2),0.35,dark)
        beam('chrome lift piston',(3.5,side*0.78,4.2),(4.1,side*0.78,5.0),0.18,galv)
    box('rear tailgate weight', (6.04,0,4.91),(0.28,4.68,3.6),oxide)
    for z in (2.2,2.7,3.2,3.7,4.2):
        box('cab access ladder',(-1.64,2.15,z),(1.32,0.12,0.09),galv)


def gantry():
    # A mine-head ore hoist built as four braced load-bearing legs.
    for x in (-5.6,5.6):
        for y in (-3.5,3.5):
            beam('splayed steel headframe leg',(x*1.38,y*1.25,0),(x,y,17.0),0.36,oxide)
            box('bearing base plate',(x*1.38,y*1.25,0.18),(1.1,1.1,0.25),galv,0.03)
    for z in (3.8,8.2,12.6,17):
        for y in (-3.5,3.5):
            beam('headframe cross member',(-5.6,y,z),(5.6,y,z),0.2,galv)
        for x in (-5.6,5.6):
            beam('transverse girder',(x,-3.5,z),(x,3.5,z),0.2,galv)
    for side in (-1,1):
        for k in range(4 if not LOW else 2):
            z0=k*(4.3 if not LOW else 8.6)
            beam('diagonal lattice',(5.6*side,-3.5,z0),(5.6*side,3.5,z0+4.3),0.14,dark)
    cyl('huge rope sheave',(0,0,18.1),1.55,0.75,dark,rot=(math.pi/2,0,0))
    torus('yellow sheave rim',(0,0,18.1),1.4,0.13,yellow,rot=(math.pi/2,0,0))
    for k in range(6):
        a=k*2*math.pi/6
        beam('sheave spoke',(0,0,18.1),(1.2*math.cos(a),0,18.1+1.2*math.sin(a)),0.16,galv)
    tube('winding hoist rope',[(0,0,19.65),(0,0,9.7),(0.2,0,8.3)],0.045,dark)
    mesh('heavy ore skip', [(-1.25,-1.2,5.2),(1.25,-1.2,5.2),(1.25,1.2,5.2),(-1.25,1.2,5.2),
           (-1.5,-1.5,8.15),(1.5,-1.5,8.15),(1.5,1.5,8.15),(-1.5,1.5,8.15)],
         [(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],oxide)
    for x in (-5.6,5.6):
        box('maintenance platform',(x,0,13.0),(1.5,8.3,0.28),galv,0.04)
    tube('maintenance guard rail',[(-6.4,-4.3,14.2),(-6.4,4.3,14.2),
         (6.4,4.3,14.2),(6.4,-4.3,14.2)],0.07,yellow)


MODELS = {'drill': drill, 'crusher': crusher, 'haul': haul, 'gantry': gantry}


def material_join():
    """Apply bevels and merge same-material parts into a handful of draws."""
    objects = [o for o in asset_collection.objects if o.type == 'MESH']
    for o in objects:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for modifier in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    for m in (yellow, oxide, galv, dark, rubber, glass, ore, cream):
        same = [o for o in asset_collection.objects if o.type == 'MESH' and o.data.materials and o.data.materials[0] == m]
        if len(same) < 2: continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in same: o.select_set(True)
        bpy.context.view_layer.objects.active = same[0]
        bpy.ops.object.join()
        same[0].name = f'{m.name} • merged manufactured assembly'


for kind, build in MODELS.items():
    for lod in (False, True):
        clear()
        LOW = lod
        asset_collection = bpy.data.collections.new(f'ROCKHOP {kind} {"LOD" if lod else "full"}')
        bpy.context.scene.collection.children.link(asset_collection)
        build()
        material_join()
        bpy.ops.object.select_all(action='DESELECT')
        for o in asset_collection.objects: o.select_set(True)
        stem = f'quarry-{kind}{"-lod" if lod else ""}'
        bpy.ops.export_scene.gltf(filepath=str(out / f'{stem}.glb'), export_format='GLB',
                                  use_selection=True, export_apply=True, export_materials='EXPORT')
        if not lod:
            bpy.ops.wm.save_as_mainfile(filepath=str(out / f'{stem}.source.blend'))
        print(f'EXPORTED {stem}')
