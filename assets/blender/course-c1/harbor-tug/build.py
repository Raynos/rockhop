"""Rebuild the C1 working harbor tug and its nine-angle review board.

blender -b --python-exit-code 1 --python assets/blender/course-c1/harbor-tug/build.py -- --out assets/blender/course-c1/harbor-tug/out

The script owns only an isolated asset scene. It exports an editable .blend master,
an uncompressed glTF 2.0 GLB, and nine Eevee views. No runtime files are changed.
Units are metres; Blender X is the keel axis, Z is up. The glTF importer makes Z
the game's Y-up axis. The center origin is near the keel; red oxide meets the
painted hull at local +1.25 m, which is the intended waterline.
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

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
random.seed(7)


def mat(name, color, metallic=0.0, rough=0.7):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = rough
    return m


paint = mat('01 • weathered petrol blue enamel', (0.075, 0.23, 0.26), 0.48, 0.52)
paint_dark = mat('02 • shadowed hull blue', (0.036, 0.105, 0.12), 0.45, 0.68)
antifoul = mat('03 • red oxide antifoul', (0.30, 0.085, 0.052), 0.3, 0.83)
cream = mat('04 • aged ivory', (0.69, 0.65, 0.54), 0.1, 0.75)
cream_shadow = mat('05 • ivory shadow', (0.40, 0.40, 0.35), 0.1, 0.78)
steel = mat('06 • galvanized steel', (0.27, 0.32, 0.31), 0.78, 0.38)
steel_dark = mat('07 • oiled machinery', (0.065, 0.082, 0.081), 0.7, 0.57)
rubber = mat('08 • black harbor rubber', (0.025, 0.034, 0.035), 0.0, 0.91)
rust = mat('09 • bleeding oxide', (0.40, 0.145, 0.072), 0.08, 0.88)
rust_dark = mat('10 • old rust', (0.20, 0.065, 0.041), 0.08, 0.92)
wood = mat('11 • wet timber', (0.22, 0.15, 0.09), 0.0, 0.83)
glass = mat('12 • smoked bridge glass', (0.035, 0.12, 0.14), 0.1, 0.18)
glass_glint = mat('13 • reflected blue glass', (0.16, 0.29, 0.29), 0.0, 0.23)
yellow = mat('14 • working yellow', (0.83, 0.39, 0.08), 0.13, 0.54)
red = mat('15 • port light', (0.76, 0.08, 0.045), 0.0, 0.22)
green = mat('16 • starboard light', (0.05, 0.60, 0.27), 0.0, 0.22)
rope_mat = mat('17 • salt-stained hemp', (0.36, 0.29, 0.17), 0.0, 0.96)

# A small, deterministic hull albedo is authored here rather than depending on
# a Blender-only procedural shader. The broad salt fade and fine vertical rust
# streaks remain visible in the GLB; the file is also packed into the .blend.
def hull_albedo():
    w, h = 512, 256
    img = bpy.data.images.new('RH07 salt, scraped paint and oxide', width=w, height=h)
    pixels = [0.0] * (w*h*4)
    streaks = [(0.08,0.83),(0.17,0.57),(0.27,0.73),(0.66,0.61),(0.79,0.91),(0.86,0.75)]
    for yy in range(h):
        v = yy/(h-1)
        for xx in range(w):
            u = xx/(w-1)
            salt = 0.028*math.sin(u*44+math.sin(v*19)*0.5) + 0.014*math.sin(u*113+v*43)
            salt += 0.009*math.sin(u*273-v*127)
            wash = 0.055*math.exp(-((v-0.62)/0.10)**2)
            weather = max(-0.05,min(0.09,salt+wash))
            col = [0.070+weather*0.65, 0.205+weather, 0.232+weather]
            for sx, density in streaks:
                width = 0.0025 + (1-v)*0.0012
                d = abs(u-sx-0.002*math.sin(v*26+sx*50))
                if v < density and d < width*2.2:
                    fade = (1-d/(width*2.2)) * max(0, 1-(density-v)*0.31)
                    col = [col[i]*(1-fade*0.72)+c*fade*0.72 for i,c in enumerate((0.31,0.095,0.050))]
            k = (yy*w+xx)*4
            pixels[k:k+4] = (*col, 1)
    img.pixels.foreach_set(pixels)
    img.filepath_raw = str(out/'hull-albedo.png')
    img.file_format = 'PNG'
    img.save()
    img.pack()
    tex = paint.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Linear'
    paint.node_tree.links.new(tex.outputs['Color'], paint.node_tree.nodes['Principled BSDF'].inputs['Base Color'])


hull_albedo()

asset = bpy.data.collections.new('RH07 • C1 harbor tug')
bpy.context.scene.collection.children.link(asset)


def move_asset(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    asset.objects.link(o)
    return o


def assign(o, material):
    o.data.materials.append(material)
    return move_asset(o)


def bevel(o, width=0.06, segments=1):
    mod = o.modifiers.new('soft manufactured edges', 'BEVEL')
    mod.width, mod.segments = width, segments
    mod.affect = 'EDGES'
    normal = o.modifiers.new('weighted face normals', 'WEIGHTED_NORMAL')
    normal.keep_sharp = True
    return o


def cube(name, loc, scale, material, edge=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, material)
    if edge: bevel(o, edge)
    return o


def cyl(name, loc, radius, depth, material, vertices=16, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    if rotation: o.rotation_euler = rotation
    assign(o, material)
    bevel(o, min(0.035, radius * 0.15), 1)
    return o


def torus(name, loc, major, minor, material, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=18, minor_segments=7,
        location=loc, major_radius=major, minor_radius=minor)
    o = bpy.context.object
    o.name = name
    if rotation: o.rotation_euler = rotation
    assign(o, material)
    return o


def mesh(name, vertices, faces, material, smooth=False):
    m = bpy.data.meshes.new(name)
    m.from_pydata(vertices, [], faces)
    m.update()
    o = bpy.data.objects.new(name, m)
    asset.objects.link(o)
    o.data.materials.append(material)
    for p in m.polygons: p.use_smooth = smooth
    return o


def tube(name, pts, radius, material, resolution=4):
    c = bpy.data.curves.new(name, 'CURVE')
    c.dimensions = '3D'
    c.resolution_u = 2
    c.bevel_depth = radius
    c.bevel_resolution = resolution
    s = c.splines.new('POLY')
    s.points.add(len(pts) - 1)
    for p, xyz in zip(s.points, pts): p.co = (*xyz, 1)
    o = bpy.data.objects.new(name, c)
    asset.objects.link(o)
    c.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target='MESH')
    return o


# A fair curved hull, defined by actual waterline/chine/shear sections rather than
# a stretched box. The aft transom is full, the bow pinches and rises above the deck.
sections = [(-8.3, 0.33, 3.03), (-7.8, 0.75, 3.05), (-6.0, 0.96, 3.07),
            (-3.0, 1.00, 3.10), (0.0, 1.00, 3.12), (3.2, 0.96, 3.17),
            (5.4, 0.82, 3.32), (6.9, 0.51, 3.56), (8.2, 0.08, 3.72)]
verts, faces, face_mats = [], [], []
for x, breadth, sheer in sections:
    b = 2.78 * breadth
    verts.extend([(x, -b, sheer), (x, -b * 1.00, 2.55),
                  (x, -b * 0.93, 1.25), (x, -b * 0.68, 0.23),
                  (x, -b * 0.30, -0.38), (x, b * 0.30, -0.38),
                  (x, b * 0.68, 0.23), (x, b * 0.93, 1.25),
                  (x, b * 1.00, 2.55), (x, b, sheer)])
for i in range(len(sections) - 1):
    for j in range(9):
        faces.append((i * 10+j, (i+1)*10+j, (i+1)*10+j+1, i*10+j+1))
        face_mats.append(0 if j in (0, 8) else 1 if j in (1, 7) else 2)
faces.append(tuple(reversed(range(10))))
face_mats.append(1)
faces.append(tuple((len(sections)-1)*10+j for j in range(10)))
face_mats.append(0)
hull = mesh('hand-faired steel hull • keel / chine / sheer', verts, faces, paint, True)
for m in (paint_dark, antifoul): hull.data.materials.append(m)
for p, m in zip(hull.data.polygons, face_mats): p.material_index = m
uv = hull.data.uv_layers.new(name='longitudinal hull paint')
for p in hull.data.polygons:
    for li in p.loop_indices:
        co = hull.data.vertices[hull.data.loops[li].vertex_index].co
        uv.data[li].uv = ((co.x+8.3)/16.5, (co.z+0.38)/4.1)
bevel(hull, 0.045, 2)

# Deck and bulwark: curved sheer, alternating metal and timber walking areas.
outline = [(x, -2.72*b, h+0.015) for x,b,h in sections] + [(x, 2.72*b, h+0.015) for x,b,h in reversed(sections)]
mesh('recessed continuous deck', outline, [tuple(range(len(outline)))], steel_dark)
for side in (-1, 1):
    tube('continuous heavy rubbing strake', [(x, side*2.78*b, h-0.32) for x,b,h in sections], 0.13, rubber)
    tube('thin scarred cream boot stripe', [(x, side*2.81*b, 2.50) for x,b,h in sections], 0.045, cream)
    tube('lower weld/chine shadow', [(x, side*2.62*b, 1.25) for x,b,h in sections], 0.048, steel_dark)
    for x in (-7.2, -5.3, -3.4, 3.5, 5.0):
        torus('heavy side tyre fender', (x, side*2.82, 2.04), 0.58, 0.16, rubber,
              (math.pi/2, 0, 0))
        tube('fender fall', [(x,side*2.83,3.16),(x,side*2.86,2.58)], 0.024, rope_mat)

# A stepped aft deck with plank seams, winch drum, fairlead and non-fictional
# machinery connections. These are visible when the rider passes the vessel.
for i in range(8):
    cube('aft working deck timber', (-5.15+i*0.43, 0, 3.24), (0.36, 4.25, 0.11), wood, 0.018)
for side in (-1, 1):
    tube('aft bulwark cap', [(-7.8,side*1.9,3.25),(-6.1,side*2.7,3.20),(-3.3,side*2.7,3.27)],0.07,steel)
    for x in (-6.5, -5.2, -3.9):
        cyl('aft rail stanchion', (x,side*2.62,3.68),0.055,0.9,steel,8)
    tube('aft safety rail', [(-7.15,side*2.45,4.10),(-5.2,side*2.62,4.11),(-3.3,side*2.55,4.13)],0.035,steel)

for x in (-5.8, -3.8):
    cube('drum pedestal', (x,0,3.7), (0.18,1.5,0.84), steel,0.08)
cyl('towing/winch drum',(-4.8,0,4.05),0.51,2.1,steel_dark,20,(math.pi/2,0,0))
for side in (-1,1):
    cyl('drum side flange',(-4.8,side*1.08,4.05),0.68,0.12,steel,20,(math.pi/2,0,0))
for i in range(10):
    x = -4.8 + math.cos(i*0.63)*0.53
    z = 4.05 + math.sin(i*0.63)*0.53
    tube('visible tow rope turns', [(x,y,z) for y in (-0.90,0.90)],0.017,rope_mat,2)
cyl('deck capstan',(-6.8,0,3.53),0.39,0.5,steel,14)
for side in (-1,1):
    cube('tow bit upright',(-7.1,side*0.54,3.55),(0.23,0.22,0.76),steel,0.04)
tube('tow bit crossbar',[(-7.1,-1,3.94),(-7.1,1,3.94)],0.10,steel)

# A purposeful stepped wheelhouse, with six separate swept glazing panels and
# metal mullions. Dark recesses under the lip distinguish glass from painted box.
cube('deckhouse base', (0.55,0,4.20), (4.5,4.1,2.0), cream_shadow,0.16)
cube('deckhouse ivory upper', (0.65,0,5.09), (4.35,3.95,1.40), cream,0.10)
cube('dark window belt', (0.82,0,5.62), (4.12,4.08,0.98),steel_dark,0.06)
cube('cabin roof overhang', (0.75,0,6.37), (5.5,4.65,0.29),paint_dark,0.08)
cube('weather cap upper surface', (0.75,0,6.56), (5.2,4.35,0.09),cream,0.04)
for side in (-1,1):
    for x in (-0.68,0.27,1.22,2.17):
        cube('framed wheelhouse window', (x,side*2.052,5.67), (0.77,0.045,0.71),glass,0.035)
        cube('glass top daylight reflection', (x-0.21,side*2.085,5.87),(0.16,0.018,0.15),glass_glint,0.015)
    for x in (-1.15,-0.20,0.75,1.70,2.65):
        cube('visible metal mullion',(x,side*2.095,5.67),(0.07,0.07,0.92),cream,0.012)
    cube('weathered deckhouse door',(0.0,side*2.074,4.35),(0.86,0.06,1.26),paint_dark,0.04)
    cyl('door porthole',(0.0,side*2.13,4.65),0.20,0.045,glass,12,(math.pi/2,0,0))
    cyl('brass handle',(-0.29,side*2.15,4.13),0.045,0.08,yellow,10,(math.pi/2,0,0))
# Forward windshield; shallow angled center mullion and glass band.
cube('forward bridge glass',(2.91,0,5.68),(0.07,3.60,0.76),glass,0.03)
for y in (-1.25,0,1.25):
    cube('windshield mullion',(2.97,y,5.68),(0.065,0.065,0.88),cream,0.01)

# Foredeck raised coaming, paired anchors, mooring bits and rope bundle.
for side in (-1,1):
    tube('foredeck bulwark',[ (3.0,side*2.65,3.2),(5.4,side*2.22,3.42),(7.65,side*0.32,3.78)],0.10,cream)
    for x,y in ((3.8,2.58),(5.5,2.1),(6.65,1.35)):
        cyl('foredeck rail stanchion',(x,side*y,3.92),0.043,0.82,steel,8)
    tube('foredeck rail',[(3.0,side*2.65,4.42),(5.5,side*2.1,4.42),(6.65,side*1.35,4.44)],0.031,steel)
    cyl('anchor hawse rim',(5.55,side*2.03,2.54),0.25,0.08,steel_dark,12,(math.pi/2,0,0))
    cyl('anchor center',(5.55,side*2.08,2.54),0.17,0.08,rust_dark,12,(math.pi/2,0,0))
    for x in (4.0,6.1):
        cube('mooring bollard riser',(x,side*0.85,3.65),(0.32,0.30,0.67),steel_dark,0.05)
        cyl('mooring bollard horn',(x,side*0.85,4.0),0.20,0.50,steel,12,(math.pi/2,0,0))

# Mast/radar and asymmetric navigation light silhouettes.
cyl('radar mast',(0.85,0,7.44),0.075,1.74,steel,10)
cube('radar bar',(0.85,0,8.23),(0.40,1.25,0.14),cream,0.06)
cube('mast cross-arm',(0.85,0,7.52),(0.12,2.5,0.12),steel,0.03)
for side, material in ((-1,red),(1,green)):
    cyl('navigation lamp',(0.85,side*1.26,7.52),0.125,0.15,material,12)
    cyl('lamp metal cap',(0.85,side*1.26,7.67),0.17,0.09,steel_dark,12)
cyl('horn vent',(0.07,0.95,6.72),0.14,0.58,steel_dark,12)
cyl('exhaust stack',(-1.1,-1.05,7.12),0.27,1.23,paint_dark,16)
cyl('exhaust heat collar',(-1.1,-1.05,7.65),0.33,0.14,steel,16)

# Deliberate maintenance wear follows plausible causes: salt at the waterline,
# rust running below hawse openings and scuffs near tyres. It is modeled, so
# the color regions survive low mip levels and the nine-angle silhouette test.
for side in (-1,1):
    for x in (-7.1,-5.25,-3.6,3.52,5.0):
        y=side*2.805
        for i in range(3):
            xx=x + (i-1)*0.13
            zz=1.62 - 0.16*i
            cube('fender rust dribble',(xx,y+side*0.035,zz),(0.055,0.019,0.44+0.11*i),rust_dark,0.015)
    for x in (5.48,6.1):
        tube('hawse rust run',[(x,side*2.10,2.40),(x-0.09,side*2.18,1.80),(x-0.02,side*2.18,1.36)],0.04,rust,2)
    for i in range(18):
        x=random.uniform(-7.0,5.8)
        if x>4.9: continue
        b=next((bb for xx,bb,_ in sections if xx>=x),0.85)
        y=side*(2.78*b+0.02)
        z=random.uniform(1.65,2.75)
        cube('paint-edge chip',(x,y,z),(random.uniform(0.06,0.26),0.018,random.uniform(0.035,0.10)),
             rust if i%3 else cream_shadow,0.007)

# Hull-side identity in solid raised lettering; true geometry avoids a large
# decal texture and remains readable in the ten-to-twenty-pixel ride silhouette.
font = bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial Bold.ttf')
for side in (-1,1):
    curve=bpy.data.curves.new('RH07 hull name','FONT')
    curve.body='RH 07'
    curve.font=font
    curve.size=0.68
    curve.resolution_u=1
    o=bpy.data.objects.new('raised hull identity',curve)
    asset.objects.link(o)
    o.rotation_euler=(math.pi/2 if side<0 else -math.pi/2,0,0)
    o.location=(-1.62,side*2.87,2.72)
    curve.materials.append(cream)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.convert(target='MESH')

# Apply every authored modifier, convert curves, then merge by material. An
# exported mesh with a bounded number of material primitives is cheaper than
# hundreds of individual GLB draw nodes and retains editable source objects.
for o in list(asset.objects):
    if o.type!='MESH': continue
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active=o
    for mod in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if o.data.polygons:
        o.data.update()

bpy.ops.wm.save_as_mainfile(filepath=str(out/'harbor-tug.source.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in asset.objects:
    if o.type=='MESH': o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in asset.objects if o.type=='MESH')
bpy.ops.object.join()
joined=bpy.context.view_layer.objects.active
joined.name='RH07 • four-draw batched display mesh'
# Preserve all seventeen authored colours in per-corner COLOR_0, but keep
# actual separate shader programs only where the phone can see a different
# response: textured hull, glossy windows, rubber fenders, and painted metal.
# glTF emits one primitive per material, so this matters more than node count.
old_mats=list(joined.data.materials)
colors=joined.data.color_attributes.new(name='COLOR_0',type='FLOAT_COLOR',domain='CORNER')
joined.data.color_attributes.active_color=colors

def vertex_mat(name,metallic,rough):
    m=mat(name,(1,1,1),metallic,rough)
    attr=m.node_tree.nodes.new('ShaderNodeVertexColor')
    attr.layer_name='COLOR_0'
    m.node_tree.links.new(attr.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    return m

glass_vertex=vertex_mat('window glass • vertex tint',0.10,0.21)
metal_vertex=vertex_mat('painted metal • vertex palette',0.43,0.60)
target_mats=[paint,glass_vertex,rubber,metal_vertex]
face_targets=[]
for p in joined.data.polygons:
    old=old_mats[p.material_index]
    target=0 if old==paint else 1 if old in (glass,glass_glint) else 2 if old==rubber else 3
    rgba=(1,1,1,1) if target in (0,2) else tuple(old.diffuse_color)
    for li in p.loop_indices:
        colors.data[li].color=rgba
        if target!=0:
            for layer in joined.data.uv_layers: layer.data[li].uv=(0,0)
    face_targets.append(target)
joined.data.materials.clear()
for m in target_mats: joined.data.materials.append(m)
for p,target in zip(joined.data.polygons,face_targets): p.material_index=target
bpy.ops.export_scene.gltf(filepath=str(out/'harbor-tug.glb'), export_format='GLB',
    use_selection=True, export_apply=True, export_materials='EXPORT',
    export_animations=False, export_yup=True, export_image_format='AUTO')

# Nine orthographic studio views: 0° is the port broadside; other angles expose
# bow, stern, contact scale, railings and both cabin sides. The source and GLB
# are unaffected by studio-only lights, floor and camera.
world=bpy.context.scene.world
world.color=(0.21,0.28,0.32)
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.29,0.39,0.43,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.48
for name,loc,power,size in [('key',(5,-8,14),1900,8),('fill',(-8,5,10),1000,8),('rim',(-3,8,11),1600,6)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    light=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(light);light.location=loc
    direction=Vector((0,0,3))-light.location;light.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('nine-angle orthographic camera')
cam=bpy.data.objects.new('nine-angle orthographic camera',camdata)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=22.5
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.render.image_settings.color_mode='RGBA'
for index,deg in enumerate((0,40,80,120,160,200,240,280,320),1):
    a=math.radians(deg)
    cam.location=(18*math.sin(a),-18*math.cos(a),10.6)
    cam.rotation_euler=(Vector((0,0,3.4))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/f'angle-{index:02d}-{deg:03d}.png')
    bpy.ops.render.render(write_still=True)
# The full scene was saved before batching; this reduction affects only a
# separate far-view export. Keep the original object and its material regions.
lod=bpy.context.view_layer.objects.active
mod=lod.modifiers.new('far-view LOD', 'DECIMATE')
mod.ratio=0.54
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.export_scene.gltf(filepath=str(out/'harbor-tug-lod.glb'), export_format='GLB',
    use_selection=True, export_apply=True, export_materials='EXPORT',
    export_animations=False, export_yup=True, export_image_format='AUTO')
print('C1 tug output:',out)
