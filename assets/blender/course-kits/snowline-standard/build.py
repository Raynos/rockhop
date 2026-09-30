"""Deterministic editable Snowline Standard master and modular GLB prototypes.

Blender units are metres. X is course travel, Y is depth, Z is up; glTF exports
Y-up for Three. Each prototype's pivot is its contact foot (z=0). Details are
modelled in the editable .blend, then material-batched for the runtime GLB.
No downloaded/generated third-party art is used.
"""
import argparse
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
out = Path(p.parse_args(argv).out).resolve()
out.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
random.seed(91723)


def mat(name, color, metal=0, rough=.7):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    return m


snow = mat('01 compacted blue-white snow', (.73, .83, .86), 0, .89)
snow_edge = mat('02 wind-packed cream crust', (.93, .92, .82), 0, .83)
ice = mat('03 glacier blue', (.22, .52, .62), .03, .34)
ice_dark = mat('04 deep crevasse ice', (.045, .18, .27), 0, .47)
ice_face = mat('05 fractured face', (.39, .67, .72), 0, .53)
stone = mat('06 entrained slate', (.11, .18, .23), 0, .92)
steel = mat('07 galvanized support steel', (.35, .43, .43), .57, .46)
steel_dark = mat('08 oil and exposed iron', (.08, .14, .16), .52, .67)
paint = mat('09 service yellow', (.83, .52, .12), .17, .61)
paint_red = mat('10 rescue orange', (.82, .23, .11), .12, .62)
rubber = mat('11 tracked rubber', (.045, .055, .057), 0, .91)
glass = mat('12 cold smoke glass', (.052, .16, .19), .1, .21)
lamp = mat('13 amber warning lamp', (.98, .69, .28), .05, .28)
rope = mat('14 cable and welded joints', (.13, .16, .17), .68, .5)

collection = bpy.data.collections.new('Rockhop Snowline Standard source')
bpy.context.scene.collection.children.link(collection)
current = 'gorge-wall'


def use(o, name, m):
    o.name = f'{current}::{name}'
    for c in list(o.users_collection): c.objects.unlink(o)
    collection.objects.link(o)
    o.data.materials.append(m)
    return o


def cube(name, loc, dimensions, m, edge=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    use(o, name, m)
    if edge:
        bevel = o.modifiers.new('soft machined edge', 'BEVEL')
        bevel.width = edge
        bevel.segments = 1
        o.modifiers.new('weighted face normals', 'WEIGHTED_NORMAL')
    return o


def cyl(name, loc, radius, depth, m, n=12, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    if rotation: o.rotation_euler = rotation
    return use(o, name, m)


def mesh(name, verts, faces, m, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    o = bpy.data.objects.new(f'{current}::{name}', data)
    collection.objects.link(o)
    data.materials.append(m)
    for f in data.polygons: f.use_smooth = smooth
    return o


def tube(name, points, radius, m, resolution=2):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = resolution
    line = curve.splines.new('POLY')
    line.points.add(len(points) - 1)
    for pt, xyz in zip(line.points, points): pt.co = (*xyz, 1)
    o = bpy.data.objects.new(f'{current}::{name}', curve)
    collection.objects.link(o)
    curve.materials.append(m)
    return o


def beam(name, a, b, width, m):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = cube(name, (a + b) / 2, (width, width, d.length), m)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return o


def glacier_wall(w=10.0, h=11.8, depth=2.0, variant=0):
    # Hand-segmented shelf: cap, blue transparent-looking bands, dark basal
    # overhang, trapped moraine and fracture tongues. The shape is not a box.
    levels = [(0, .40), (.14, .64), (.27, .84), (.46, 1), (.63, .92),
              (.77, .85), (.91, .95), (1, .75)] if variant==0 else [
              (0,.57),(.12,.71),(.30,.96),(.47,.79),(.62,1.04),
              (.76,.80),(.89,.94),(1,.71)]
    pockets = [(-2.8,.51),(.35,.38),(3.15,.70)] if variant==0 else [
               (-3.9,.34),(-1.15,.68),(2.1,.50),(4.2,.80)]
    for side in (-1, 1):
        verts = []
        for j, (t, bulge) in enumerate(levels):
            z = h*t
            for i in range(13):
                x = -w/2 + w*i/12
                # Three deeply scooped shear pockets break the rectangular
                # silhouette; coherent height modulation makes actual 3D ribs.
                pocket = sum((.48+.10*variant)*math.exp(-((x-c)/(.82+.1*variant))**2 - ((t-v)/.23)**2)
                             for c,v in pockets)
                ridge = .18*math.sin(i*1.47 + j*.93+variant*1.3) + .12*math.sin(i*4.1-j+variant*.8)
                y = side * (depth*.43*bulge + ridge - pocket)
                verts.append((x + .08*math.sin(j*1.6+i*.7), y,
                              z + .18*math.sin(i*.96+j+variant*1.6) + .10*math.sin(i*2.1+variant)))
        faces = [(j*13+i, j*13+i+1, (j+1)*13+i+1, (j+1)*13+i)
                 for j in range(len(levels)-1) for i in range(12)]
        o = mesh('stratified face', verts, faces, ice_face)
        for m in (ice, ice_dark, stone): o.data.materials.append(m)
        for poly in o.data.polygons:
            row = poly.index // 12
            poly.material_index = (2 if row in (0,1) else 3 if row==2 else 1 if row in (3,5) else 0)
    # The end returns and cliff shoulder close the wall as a volume rather
    # than a zero-thickness theatre flat when the camera swings in the S runs.
    for side in (-1,1):
        xs = side*w/2
        end=[(xs,-depth*.52,0),(xs,-depth*.75,h*.27),
             (xs,-depth*.67,h*.74),(xs,-depth*.35,h),
             (xs,depth*.35,h),(xs,depth*.67,h*.74),(xs,depth*.75,h*.27),(xs,depth*.52,0)]
        # Three angled strata close the volume without one theatrical black
        # sheet at an oblique camera angle; joints vanish when modules overlap.
        mesh('fractured basal return', [end[i] for i in (0,1,6,7)],[(0,1,2,3)],ice_dark)
        mesh('blue mid return',[end[i] for i in (1,2,5,6)],[(0,1,2,3)],ice)
        mesh('snow shoulder return',[end[i] for i in (2,3,4,5)],[(0,1,2,3)],ice_face)
    for i in range(11):
        x = -w/2 + i*w/10
        top = h*(.92+.035*math.sin(i*2.3))
        if i in ((2,6,9) if variant==0 else (1,4,8)):
            # Deep, tapered rift wedges replace the uniform hairline cracks.
            mesh('rift cavity',[(x-.26,-depth*.57,top*.34),(x-.38,-depth*.47,top*.72),
                 (x+.31,-depth*.49,top*.76),(x+.23,-depth*.59,top*.25),
                 (x-.12,-depth*.86,top*.58),(x+.09,-depth*.88,top*.52)],
                 [(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)],ice_dark)
            mesh('rift luminous lip',[(x-.41,-depth*.55,top*.72),(x-.30,-depth*.48,top*.74),
                 (x-.21,-depth*.57,top*.36),(x+.28,-depth*.55,top*.76),
                 (x+.35,-depth*.62,top*.74),(x+.22,-depth*.62,top*.30)],
                 [(0,1,2),(3,4,5)],ice_face)
        elif i % 3 == 0:
            beam('short frost seam', (x,-depth*.50,top*.54), (x+.12, -depth*.56, top*.78), .028, ice_dark)
        if i % 2 == 0:
            beam('buried vertical moraine', (x-.08,-depth*.54,top*.10), (x+.13,-depth*.58,top*.38), .045, stone)
    # Saw-toothed snow cornice rolls over the ice lip, with an irregular undercut.
    crown = [(-w/2+i*w/12, -depth*.52-.25*math.sin(i*1.3+variant),
              h+.27*math.sin(i*1.8+variant*1.7)-.12*variant*math.sin(i*.7)) for i in range(13)]
    tube('wind rolled cornice', crown, .31, snow_edge, 3)
    for i in range(8):
        x=-w/2 + (i+.4)*w/8
        length=.5 + .7*((i*7)%5)/4
        beam('blue hanging fracture', (x,-depth*.50,h-.18), (x+.18,-depth*.58,h-.18-length), .07, ice)
    shoulders=[(-3.9,1.5,.38),(-.9,1.15,.61),(2.3,1.8,.46),(4.1,.75,.26)] if variant==0 else [
        (-4.4,.9,.25),(-2.3,1.9,.71),(.8,1.4,.43),(3.9,1.3,.59)]
    for i,(x,width,protrude) in enumerate(shoulders):
        mesh('thick buttress shoulder',[(x-width/2,-depth*.41,h*.56),
             (x+width/2,-depth*.42,h*.56),(x+width*.72,-depth*.41,h*.9),
             (x-width*.6,-depth*.42,h*.94),(x-width*.42,-depth*.41-protrude,h*.60),
             (x+width*.44,-depth*.41-protrude,h*.64)],
             [(0,1,5,4),(0,4,3),(3,4,5,2),(2,5,1)],ice if i%2 else ice_face)
    # Broken wind slabs sit on the lip at different depths and cast their own
    # small contact shadows. They remain well behind the rideable ribbon.
    for i in range(7):
        x=-4.3+i*1.38
        mesh('overhanging snow slab',[(x-.67,-.58,h-.16),(x+.55,-.58,h-.09),
             (x+.78,-1.10,h+.02),(x-.54,-1.16,h+.10),
             (x-.54,-1.10,h-.21),(x+.69,-1.03,h-.22)],
             [(0,1,2,3),(3,2,5,4)],snow_edge if i%3 else snow)


current='gorge-wall-a'
glacier_wall()
current='gorge-wall-b'
glacier_wall(variant=1)

current='shelf-face'
# Under-contact bracket; local z=0 is its top, everything extends below.
verts=[]
for i in range(15):
    x=-4 + i*8/14
    top=.02*math.sin(i*2.2)
    verts.extend([(x,-.55,top),(x,-.85-.11*math.sin(i),-1.5),
                  (x,-.68-.12*math.sin(i*.9),-3.35-.42*math.sin(i*1.7))])
faces=[(i*3+j,(i+1)*3+j,(i+1)*3+j+1,i*3+j+1) for i in range(14) for j in range(2)]
o=mesh('carved hanging ice front',verts,faces,ice_face)
o.data.materials.append(ice_dark)
for poly in o.data.polygons: poly.material_index=0 if poly.index%2==0 else 1
for i in range(10):
    x=-3.6+i*.81
    beam('thin subglacial vein',(x,-.88,-.25),(x+.16,-.79,-2.0-.15*(i%3)),.025,ice_dark)
tube('rounded snow lip',[(x,-.43,.02+.06*math.sin(x*1.1)) for x in (-4,-3,-2,-1,0,1,2,3,4)],.19,snow_edge)

current='lift-tower'
for s in (-1,1):
    for d in (-1,1):
        beam('tapered latticed mast',(s*.82,d*.57,.16),(s*.34,d*.30,9.62),.11,steel)
    for j in range(5):
        z=.55+j*1.75
        k=(9.62-z)/9.46
        beam('cross bracing',(s*(.34+.48*k),-.30-.27*k,z),(s*(-.34-.48*k),.30+.27*k,z+1.72),.06,steel_dark)
for z in (1.6,3.35,5.1,6.85,8.6):
    cube('horizontal inspection brace',(0,0,z),(1.24,1.0,.075),steel_dark)
cube('cast-in base plate',(0,0,.12),(2.3,1.7,.23),steel_dark,.08)
for x in (-.88,.88):
    for y in (-.62,.62): cyl('anchor bolt',(x,y,.28),.07,.18,steel,8)
cube('sheave crossarm',(0,0,10.06),(7.1,.31,.38),steel,.055)
for s in (-1,1):
    for x in (s*2.3,s*3.12):
        cyl('machined cable sheave',(x,0,10.31),.44,.13,steel_dark,18,(math.pi/2,0,0))
        cyl('sheave axle',(x,0,10.31),.13,.20,steel,12,(math.pi/2,0,0))
    beam('arm triangular load path',(s*.42,0,8.92),(s*2.76,0,10.07),.12,steel)
for j in range(8):
    z=1.0+j*.92
    cube('service ladder rung',(0,-.67,z),(.52,.055,.055),paint)

current='lift-chair'
for s in (-1,1):
    tube('chair hoop',[(s*.95,0,1.35),(s*1.00,0,.63),(s*.90,-.42,.23)],.055,steel)
cube('slatted pair seat',(0,-.18,.57),(2.12,.72,.10),paint,.035)
cube('backrest',(0,.18,1.17),(2.10,.09,.78),steel_dark,.045)
tube('lap bar',[(-1.05,-.45,.98),(0,-.63,.95),(1.05,-.45,.98)],.045,paint)
beam('hanger',(0,0,1.36),(0,0,2.79),.07,steel_dark)
cyl('grip on running cable',(0,0,2.84),.21,.34,rope,12,(math.pi/2,0,0))

current='lift-station'
for x in (-7.0,7.0):
    for y in (-2.2,2.2):
        beam('station leg',(x,y,0),(x*.85,y*.82,5.2),.28,steel)
        beam('leg crossbracing',(x,y,.3),(x*.85,-y*.82,5.05),.10,steel_dark)
for x in (-7,0,7):
    beam('station roof truss',(x,-3.2,5.1),(x,0,7.0),.20,steel)
    beam('station roof truss',(x,0,7.0),(x,3.2,5.1),.20,steel)
for side in (-1,1):
    cube('snow-shedding zinc roof',(0,side*1.7,6.06),(16.5,3.7,.13),steel_dark,.04).rotation_euler[0]=side*.48
    cube('walkway safety rail',(0,side*2.23,1.36),(13.3,.08,.07),paint)
    for x in (-5,-3,-1,1,3,5): beam('walkway upright',(x,side*2.23,.1),(x,side*2.23,1.35),.065,steel)
cube('snow-dusted concrete station footing',(0,0,.15),(15.5,4.65,.30),snow,.08)
for x in (-6.0,6.0):
    cyl('large turnaround sheave',(x,0,4.58),1.17,.29,steel_dark,26,(math.pi/2,0,0))
    cyl('orange mechanical hub',(x,0,4.58),.34,.32,paint,16,(math.pi/2,0,0))
for i in range(9):
    x=-5.2+i*1.3
    cube('station deck drainage grate',(x,0,.34),(.045,3.0,.015),steel_dark)
cube('operator cabin',(4.8,1.5,2.9),(2.45,1.6,2.7),paint_red,.12)
for y in (.64,2.36):
    cube('cold glazed operator window',(4.8,y,3.45),(1.65,.02,.74),glass,.025)
for x in (-7.5,7.5):
    cyl('hazard lamp',(x,0,5.35),.18,.36,lamp,12)

current='snowcat'
# Tractor cab, articulated track bogies, pushing blade and winter tools.
for side in (-1,1):
    cube('track outer belt',(0,side*1.55,.66),(7.1,.58,1.16),rubber,.19)
    for x in (-2.75,-1.65,-.55,.55,1.65,2.75):
        cyl('visible bogie wheel',(x,side*1.89,.61),.39,.12,steel_dark,12,(math.pi/2,0,0))
    for i in range(15):
        x=-3.33+i*.47
        cube('individual track grouser',(x,side*1.9,.17),(.19,.15,.18),steel_dark,.015)
        cube('upper return grouser',(x,side*1.9,1.22),(.19,.15,.14),steel_dark,.015)
    tube('cast track frame rail',[(-3.31,side*1.69,.40),(-3.0,side*1.70,1.06),
         (2.95,side*1.70,1.06),(3.34,side*1.69,.42)],.105,steel_dark)
    for x in (-3.0,3.0):
        cyl('exposed end idler',(x,side*1.91,.60),.42,.15,steel,14,(math.pi/2,0,0))
cube('cab lower chassis',(.55,0,1.66),(5.0,2.72,.84),paint_red,.18)
mesh('wedge cab',[(.4,-1.28,2.08),(3,-1.15,2.08),(2.30,-1.15,4.18),
                  (.20,-1.28,4.18),(.4,1.28,2.08),(3,1.15,2.08),
                  (2.30,1.15,4.18),(.20,1.28,4.18)],
     [(0,1,2,3),(4,7,6,5),(3,2,6,7),(0,4,5,1)],paint_red)
for side in (-1,1):
    cube('raked panoramic side glass',(1.23,side*1.282,3.15),(1.68,.038,1.15),glass,.04)
    tube('windshield guard',[(.47,side*1.31,2.55),(.47,side*1.31,3.79),(2.1,side*1.20,3.79)],.034,steel)
    tube('weather-sealed side window frame',[(.25,side*1.31,2.58),(2.14,side*1.22,2.58),
         (2.14,side*1.22,3.78),(.25,side*1.31,3.78),(.25,side*1.31,2.58)],.075,steel_dark)
    beam('cab side door cut',(1.25,side*1.32,2.1),(1.20,side*1.33,2.58),.025,steel_dark)
    cyl('cab door handrail',(1.52,side*1.35,2.45),.065,.10,steel,8,(math.pi/2,0,0))
cube('front windscreen',(2.54,0,3.20),(.055,1.95,1.30),glass,.04)
tube('windscreen frame',[(2.57,-1.01,2.52),(2.57,1.01,2.52),(2.51,1.01,3.84),
     (2.51,-1.01,3.84),(2.57,-1.01,2.52)],.075,steel_dark)
beam('windscreen centre post',(2.56,0,2.54),(2.51,0,3.82),.04,steel_dark)
for side in (-1,1):
    beam('wiper arm',(2.57,side*.12,2.66),(2.59,side*.76,3.36),.025,steel_dark)
for x in (-3.25,-1.85):
    cube('vented hydraulic bay',(x,0,2.18),(1.2,2.38,1.25),paint,.11)
    for i in range(5): cube('cooling grille',(x-.41+i*.20,-1.22,2.32),(.065,.025,.76),steel_dark)
    cube('vent surround',(x,-1.24,2.31),(1.08,.035,.91),steel_dark,.025)
    cube('raised service hatch',(x,.25,2.85),(1.06,1.54,.07),paint,.035)
for i in range(5):
    x=-3.85+i*.47
    cube('engine-bay intake slot',(x,1.23,2.26),(.08,.018,.34),steel_dark)
for side in (-1,1):
    beam('blade hydraulic ram',(2.2,side*.75,1.4),(4.05,side*1.55,1.0),.13,steel)
    cyl('blade side lamp',(2.77,side*1.02,2.3),.16,.16,lamp,12,(math.pi/2,0,0))
blade_verts=[]
for j,z in enumerate((.1,.88,1.47,1.9)):
    for i in range(11):
        y=-2.65+i*.53
        sweep=.12*abs(y/2.65)**1.8
        blade_verts.append((4.05 + (.18,.31,.60,.82)[j] - sweep,y,z+.06*abs(y/2.65)))
blade_faces=[(j*11+i,j*11+i+1,(j+1)*11+i+1,(j+1)*11+i)
             for j in range(3) for i in range(10)]
mesh('rolled multi-segment mouldboard',blade_verts,blade_faces,steel)
tube('blade rolled rim',[(4.87-.12*abs(y/2.65)**1.8,y,1.95+.06*abs(y/2.65))
     for y in [-2.65,-2.12,-1.59,-1.06,-.53,0,.53,1.06,1.59,2.12,2.65]],.10,steel_dark)
cube('replaceable black cutting edge',(4.12,0,.19),(.20,5.07,.25),rubber,.03)
for side in (-1,1):
    mesh('snow blade end wing',[(4.0,side*2.63,.12),(4.28,side*2.63,1.1),
         (4.88,side*2.63,1.98),(4.38,side*2.78,1.74)],
         [(0,1,3),(1,2,3)],paint)
for side in (-1,1):
    cyl('warning beacon',(0.1,side*.65,4.40),.16,.28,lamp,10)
cube('roof searchlight gantry',(1.0,0,4.32),(1.65,.16,.13),steel_dark,.025)
for side in (-1,1):
    cyl('roof searchlight',(1.1,side*.71,4.43),.19,.30,steel,12,(math.pi/2,0,0))
    cyl('lamp optic',(1.1,side*.87,4.43),.135,.04,lamp,12,(math.pi/2,0,0))

current='summit-beacon'
for side in (-1,1):
    beam('summit gantry splayed leg',(side*3.1,0,0),(side*2.32,0,9.25),.24,steel)
    beam('gantry diagonal',(side*3.08,0,1.4),(-side*2.45,0,7.58),.10,steel_dark)
cube('wind exposed gantry crossbar',(0,0,9.4),(6.7,.28,.36),steel,.06)
cube('snow-catching course banner frame',(0,-.15,7.25),(4.88,.10,2.9),paint_red,.06)
for x in (-2.40,2.40):
    beam('banner cable',(x,-.22,8.65),(x,-.22,5.85),.035,rope)
    cyl('summit strobe',(x,0,9.92),.23,.36,lamp,14)
for x in (-3.35,3.35):
    cube('rock socket',(x,0,.14),(1.15,1.45,.28),stone,.03)
beam('flag mast',(0,0,9.60),(0,0,12.4),.075,steel_dark)
mesh('wind-torn summit pennant',[(0,0,12.4),(2.1,-.08,12.05),(.35,-.02,11.5)],[(0,1,2)],paint_red)

# Apply editable modifiers and curves in source, then save the complete master.
for o in list(collection.objects):
    if o.type not in ('MESH','CURVE'): continue
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active=o
    if o.type=='CURVE': bpy.ops.object.convert(target='MESH')
    for mod in list(bpy.context.object.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'snowline-standard.source.blend'))

# Material-batch each source archetype into one mesh with colour-at-corner.
# Ice and metal have different responses; each prototype is at most two draws.
groups={}
for o in list(collection.objects):
    if o.type=='MESH': groups.setdefault(o.name.split('::')[0],[]).append(o)

# Original, deterministic 256² authored microdetail. The map is neutral so
# the region-specific COLOR_0 palette controls the large-scale hue; the same
# grain acts as ice frost, scoured snow and worn paint rather than seven maps.
N=256
albedo=bpy.data.images.new('Snowline frost and weather grain',width=N,height=N)
normal=bpy.data.images.new('Snowline compressed ice fine normal',width=N,height=N)
albedo_pixels=[0.0]*(N*N*4)
normal_pixels=[0.0]*(N*N*4)
for py in range(N):
    v=py/N
    for px in range(N):
        u=px/N
        ridge=.030*math.sin(u*74+v*11)+.014*math.sin(u*169-v*23)
        frost=.012*math.sin(u*391+v*403)*math.sin(u*271-v*293)
        seed=(px*73856093 ^ py*19349663 ^ 0x51a7)&255
        scratch=.023 if seed<4 else -.016 if seed>252 else 0
        grey=max(.78,min(1.0,.925+ridge+frost+scratch))
        index=(py*N+px)*4
        albedo_pixels[index:index+4]=(grey,grey,grey*.99,1)
        nx=.5+.08*math.cos(u*74+v*11)+.045*math.cos(u*169-v*23)
        ny=.5+.025*math.sin(v*161+u*41)
        normal_pixels[index:index+4]=(nx,ny,.98,1)
albedo.pixels.foreach_set(albedo_pixels)
normal.pixels.foreach_set(normal_pixels)
for img,file in ((albedo,'snowline-grain.png'),(normal,'snowline-ice-normal.png')):
    img.filepath_raw=str(out/file);img.file_format='PNG';img.save();img.pack()
normal.colorspace_settings.name='Non-Color'

vertex_ice=mat('Snowline ice and snow vertex palette',(1,1,1),.015,.55)
vertex_metal=mat('Snowline working metal vertex palette',(1,1,1),.32,.59)
vertex_glass=mat('Snowline glass vertex palette',(1,1,1),.07,.19)
vertex_rubber=mat('Snowline rubber vertex palette',(1,1,1),0,.93)
for m in (vertex_ice,vertex_metal,vertex_glass,vertex_rubber):
    nt=m.node_tree
    n=m.node_tree.nodes.new('ShaderNodeVertexColor')
    n.layer_name='COLOR_0'
    if m in (vertex_ice,vertex_metal):
        tex=nt.nodes.new('ShaderNodeTexImage');tex.image=albedo;tex.extension='REPEAT'
        mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
        nt.links.new(n.outputs['Color'],mix.inputs[1]);nt.links.new(tex.outputs['Color'],mix.inputs[2])
        nt.links.new(mix.outputs[0],nt.nodes['Principled BSDF'].inputs['Base Color'])
        if m==vertex_ice:
            ntex=nt.nodes.new('ShaderNodeTexImage');ntex.image=normal;ntex.extension='REPEAT'
            nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.36
            nt.links.new(ntex.outputs['Color'],nm.inputs['Color'])
            nt.links.new(nm.outputs[0],nt.nodes['Principled BSDF'].inputs['Normal'])
    else: nt.links.new(n.outputs['Color'],nt.nodes['Principled BSDF'].inputs['Base Color'])
ice_family={snow,snow_edge,ice,ice_dark,ice_face,stone}
for name, objects in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects: o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    joined=bpy.context.object
    joined.name=f'snowline:{name}'
    original=list(joined.data.materials)
    attr=joined.data.color_attributes.new(name='COLOR_0',type='FLOAT_COLOR',domain='CORNER')
    joined.data.color_attributes.active_color=attr
    uv=joined.data.uv_layers.get('UVMap') or joined.data.uv_layers.new(name='UVMap')
    target=[]
    for poly in joined.data.polygons:
        source=original[poly.material_index]
        for li in poly.loop_indices:
            attr.data[li].color=tuple(source.diffuse_color)
            xyz=joined.data.vertices[joined.data.loops[li].vertex_index].co
            uv.data[li].uv=(xyz.x/3,xyz.z/3)
        target.append(0 if source in ice_family else 2 if source == glass else 3 if source == rubber else 1)
    joined.data.materials.clear()
    for palette in (vertex_ice,vertex_metal,vertex_glass,vertex_rubber): joined.data.materials.append(palette)
    for poly, index in zip(joined.data.polygons,target): poly.material_index=index
    # Remove unused shader slots, retaining exact palette-to-face mapping.
    for unused in (3,2,1,0):
        if unused not in target: joined.data.materials.pop(index=unused)

# Only batched prototypes are selected. The editable master above remains intact.
bpy.ops.object.select_all(action='DESELECT')
protos=[o for o in collection.objects if o.type=='MESH']
for o in protos: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'snowline-standard.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_materials='EXPORT',export_animations=False,
    export_yup=True)

# Nine-angle evidence covers the three primary hero families: each in profile,
# oblique, and end-on, with the same scale and light for honest silhouette review.
world=bpy.context.scene.world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.18,.29,.36,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.60
for name,loc,power,size in [('cold key',(9,-15,22),3000,10),('bounce',(-12,7,12),1400,9),('rim',(-2,14,17),2400,8)]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data)
    bpy.context.scene.collection.objects.link(o)
    o.location=loc
    o.rotation_euler=(Vector((0,0,4))-o.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('review camera')
cam=bpy.data.objects.new('review camera',camdata)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=17.5
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=640;scene.render.resolution_y=480
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
for i,(name,deg) in enumerate([(n,a) for n in ('gorge-wall-a','lift-tower','snowcat') for a in (0,45,100)],1):
    for o in protos: o.hide_render=o.name!=f'snowline:{name}'
    a=math.radians(deg)
    cam.location=(20*math.sin(a),-20*math.cos(a),13)
    cam.rotation_euler=(Vector((0,0,5))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/f'angle-{i:02d}-{name}-{deg:03d}.png')
    bpy.ops.render.render(write_still=True)
for name,scale in [('gorge-wall-b',17.5),('shelf-face',11.5),('lift-station',21.5),('summit-beacon',19.0)]:
    for o in protos: o.hide_render=o.name!=f'snowline:{name}'
    a=math.radians(38)
    cam.location=(20*math.sin(a),-20*math.cos(a),13)
    cam.rotation_euler=(Vector((0,0,-1.5 if name=='shelf-face' else 5))-cam.location).to_track_quat('-Z','Y').to_euler()
    camdata.ortho_scale=scale
    scene.render.filepath=str(out/f'family-{name}.png')
    bpy.ops.render.render(write_still=True)
for o in protos: o.hide_render=False
# A far-view geometric reduction is an independent export of the same source.
for o in protos:
    mod=o.modifiers.new('phone far LOD','DECIMATE')
    mod.ratio=.56 if o.name not in ('snowline:lift-chair','snowline:summit-beacon') else .78
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.object.select_all(action='DESELECT')
for o in protos:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'snowline-standard-lod.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_materials='EXPORT',export_animations=False,
    export_yup=True)
print('Snowline Standard:',out)
