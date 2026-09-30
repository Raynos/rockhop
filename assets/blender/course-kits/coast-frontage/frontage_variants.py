"""Two ground-pivot 28 x 12 m harbor halls for the existing Coast bank.

Executed by build.py before its recipe table. Geometry and compact shared PBR
atlas are original. Front is Blender -Y / game near side. Neither prototype
extends into the near riding strip or changes a collider.
"""

# Distinct facade atlas: 4 x 4 regions at 256 px. Both halls share this one
# material and three 256² maps; the seven existing prototypes retain theirs.
FRONT_COLORS = [
    (.36,.135,.085), (.49,.31,.19), (.18,.22,.22), (.72,.69,.58),
    (.19,.27,.28), (.105,.155,.18), (.15,.255,.29), (.29,.105,.06),
    (.24,.26,.24), (.59,.42,.14), (.11,.135,.13), (.67,.61,.48),
    (.21,.29,.27), (.13,.18,.21), (.40,.37,.30), (.17,.23,.24),
]
front_images = []
FN = 256
for kind in ('albedo','normal','arm'):
    image = bpy.data.images.new('frontage-'+kind+'.phone', width=FN, height=FN)
    if kind != 'albedo': image.colorspace_settings.name = 'Non-Color'
    pixels = [0.] * (FN*FN*4)
    for py in range(FN):
        for px in range(FN):
            slot = (py//64)*4 + px//64
            u,v = (px%64)/64, (py%64)/64
            stripe = math.sin(u*math.pi*46)
            brick = slot in (0,1)
            row = int(v*10)
            bond = ((u*8 + (row%2)*.5) % 1)
            joint = min(bond,1-bond) < .035 or (v*10)%1 < .07
            salt = math.sin(u*67+v*13)*.028 + math.sin(u*193-v*81)*.009
            drip = max(0.,v-.25)*sum(math.exp(-((u-c)/.018)**2) for c in (.17,.62,.87))
            if kind == 'albedo':
                rgb = list(FRONT_COLORS[slot])
                if brick:
                    mott = math.sin((int(u*8)+row*7)*13.7)*.045
                    rgb = [max(0,c+mott+salt) for c in rgb]
                    if joint: rgb = [c*.48 for c in rgb]
                    rgb = [c*(1-.20*drip) for c in rgb]
                elif slot in (4,5,12,15):
                    rgb = [c*(.94+.06*stripe) for c in rgb]
                elif slot in (2,8,14): rgb = [c+salt for c in rgb]
                if slot in (3,11) and .46 < u < .49: rgb = [c*.72 for c in rgb]
            elif kind == 'normal':
                nx = (-.23 if joint else .03*math.cos(u*140)) if brick else (.13*math.cos(u*math.pi*46) if slot in (4,5,12,15) else .012*math.sin(u*60))
                ny = -.18 if brick and (v*10)%1 < .07 else .015*math.cos(v*70)
                rgb = (.5+nx,.5+ny,.5+.5*math.sqrt(max(0,1-4*nx*nx-4*ny*ny)))
            else:
                metal = slot in (3,4,5,7,9,12,15)
                rough = .84 if brick else (.48 if metal else .71)
                rgb = (1.,min(.95,rough+.11*drip),.58 if metal else 0.)
            i=(py*FN+px)*4
            pixels[i:i+4]=(*[max(0.,min(1.,c)) for c in rgb],1.)
    image.pixels.foreach_set(pixels)
    image.filepath_raw=str(out/f'frontage-{kind}.phone.png')
    image.file_format='PNG'; image.save(); image.pack(); front_images.append(image)

frontage = material('frontage brick/steel PBR atlas',(1,1,1))
fb=frontage.node_tree.nodes['Principled BSDF']; fn=frontage.node_tree.nodes; fl=frontage.node_tree.links
for kind,image in zip(('albedo','normal','arm'),front_images):
    tex=fn.new('ShaderNodeTexImage');tex.image=image
    if kind=='albedo': fl.new(tex.outputs['Color'],fb.inputs['Base Color'])
    elif kind=='normal':
        normal=fn.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.64
        fl.new(tex.outputs['Color'],normal.inputs['Color']);fl.new(normal.outputs['Normal'],fb.inputs['Normal'])
    else:
        split=fn.new('ShaderNodeSeparateColor');fl.new(tex.outputs['Color'],split.inputs['Color'])
        fl.new(split.outputs['Green'],fb.inputs['Roughness']);fl.new(split.outputs['Blue'],fb.inputs['Metallic'])

def fbox(name,loc,dims,region=0,edge=0):
    return box(name,loc,dims,region,edge,frontage)

def fcylinder(name,loc,r,h,region=3,axis=None):
    return cylinder(name,loc,r,h,region,axis,frontage)

def fmesh(name,verts,faces,region):
    m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
    o=bpy.data.objects.new(name,m);collection.objects.link(o);o['region']=region;m.materials.append(frontage)
    return o

def front_window(cx,y,z,w,h,mullions=2):
    fbox('recessed smoked shop glazing',(cx,y+.13,z),(w,.09,h),13)
    for xx in (-w/2,w/2): fbox('steel glazing jamb',(cx+xx,y,z),(.13,.20,h+.14),3)
    for zz in (-h/2,h/2): fbox('steel glazing rail',(cx,y,z+zz),(w+.18,.19,.12),3)
    for i in range(1,mullions):
        fbox('glazing mullion',(cx-w/2+w*i/mullions,y-.02,z),(.075,.17,h),3)
    if not low: fbox('salt-stained stone sill',(cx,y+.02,z-h/2-.14),(w+.33,.25,.17),11)

def brick_repair_shed():
    # Ground-pivot replacement for a 28 x 12 m open warehouse. Front y=-6.
    fbox('old tide repair masonry plinth',(0,0,.20),(28.0,12.45,.4),2)
    fbox('oil-dark workshop floor',(0,0,.43),(27.2,11.5,.09),10)
    fbox('bonded rear brick wall',(0,5.87,3.65),(27.8,.42,6.55),0)
    for x in (-13.75,13.75):
        fbox('load-bearing brick end wall',(x,0,3.65),(.48,11.7,6.55),0)
        fbox('end wall brick pilaster',(x,0,4.0),(.62,.72,7.1),1)
        front_window(x + (.28 if x<0 else -.28),1.4,4.5,.36,2.1,1)
    # Shopfront contains three very different bays, not three copied dark gaps.
    for x in (-13.55,-6.7,.2,6.8,13.55):
        fbox('projecting brick pier',(x,-6.10,3.65),(.61,.64,7.1),0)
        fbox('cast stone pier foot',(x,-6.21,.49),(.78,.81,.40),11)
        fbox('weathered pier capital',(x,-6.16,7.05),(.75,.82,.28),11)
    fbox('deep brick spandrel',(0,-5.99,6.38),(27.6,.48,1.50),0)
    for x,w in [(-10.1,6.7),(-3.25,6.8),(3.5,6.8),(10.2,6.5)]:
        fbox('riveted lintel over dock bay',(x,-6.22,5.38),(w,.33,.38),3)
    fbox('closed roller door inset',(-10.15,-5.82,2.87),(6.35,.17,4.85),5)
    fbox('half-open shutter',(10.2,-5.80,4.64),(6.08,.17,1.28),5)
    for cx in (-10.15,10.2):
        if not low:
            for z in [1.0+i*.49 for i in range(8 if cx<0 else 3)]:
                fbox('pressed shutter blade',(cx,-5.96,z),(6.13,.045,.035),3)
        for dx in (-3.05,3.05):fbox('roll door steel runner',(cx+dx,-5.99,2.92),(.13,.23,5.0),3)
    # The open bay has unmistakable physical depth and occupied interior.
    fbox('open bay dark receding partition',(-3.22,4.95,3.0),(6.2,.13,5.0),10)
    for cx in (-4.55,-2.2,2.6,4.8):
        fbox('stacked tide repair stock',(cx,2.7,.95),(1.45,1.1,.9),11,.035)
        fbox('strapped machined crate',(cx,2.7,1.57),(1.2,1,.35),6)
    fbox('overhead travelling hoist rail',(-1,-1.1,5.72),(15,.20,.22),3)
    for xx in (-7,4):fcylinder('trolley chain block',(xx,-1.1,5.13),.24,.8,7)
    # Paired glazed clerestories define the age/material contrast at phone size.
    for x in (-9.7,-3,3.7,10.1):front_window(x,-6.23,6.24,4.2,.72,3 if not low else 2)
    for y in (-5.72,5.72):
        fbox('masonry eave cornice',(0,y,7.35),(28,.48,.38),11)
        fbox('continuous dentil shadow',(0,y,7.16),(28,.16,.12),2)
    # Old shallow gable, heavier zinc sheets and triangular profile.
    fmesh('two slope standing-seam roof',[(-14,-6.5,7.38),(14,-6.5,7.38),(-14,0,9.05),(14,0,9.05),(-14,6.5,7.38),(14,6.5,7.38)],[(0,1,3,2),(2,3,5,4)],4)
    for x in range(-14,15,2 if not low else 4):
        for y0,y1 in [(-6.4,0),(0,6.4)]:
            beam('continuous zinc standing seam',(x,y0,7.40),(x,y1,9.07 if y1==0 else 7.40),.035,3)
    for x in (-13.5,13.5):
        fmesh('gable brick masonry',[(x,-6.1,7.27),(x,6.1,7.27),(x,0,8.92)],[(0,1,2)],0)
        front_window(x + (-.22 if x<0 else .22),0,7.52,.30,.7,1)
    for x in (-12.4,12.4):
        fcylinder('cast iron rain downpipe',(x,6.16,3.55),.11,7.0,7)
        fbox('iron hopper collector',(x,6.12,7.2),(.4,.42,.37),7)
    # Show believable repair activity without placing a new hazard near track.
    for x in (-8,6.8):
        fbox('bay lamp visor',(x,-6.46,5.75),(.84,.48,.20),9)
    if not low:
        for x in range(-12,14,3):
            fbox('salt-rubbed lower brick repair patch',(x,5.58,.92),(1.3,.08,.48),1)
        for x in (-12.9,0,12.9):
            fcylinder('roof low exhaust cowl',(x,2.2,8.65),.33,1.4,7)
            fcylinder('rain hood',(x,2.2,9.42),.51,.12,4)

def sawtooth_maintenance_hall():
    # Ground-pivot replacement; tallest point 9.95 m, exact dry footprint.
    fbox('maintenance hall poured pad',(0,0,.22),(28,12.45,.44),2)
    fbox('shop floor with trench',(0,0,.49),(27.3,11.65,.08),8)
    fbox('insulated rear workshop wall',(0,5.9,3.76),(27.75,.32,6.85),12)
    for x in (-13.8,13.8):fbox('profiled end wall',(x,0,3.85),(.34,11.8,6.9),12)
    # Dark working bays to left, entirely different front rhythm from brick shed.
    for x in (-13.55,-7.2,-.85,5.55,13.55):
        fbox('exposed H column',(x,-6.08,3.71),(.24,.42,7.0),3)
        fbox('bolted base socket',(x,-6.11,.64),(.51,.54,.40),9)
    fbox('front standing seam upper fascia',(-.1,-6.03,6.34),(27.5,.32,1.65),4)
    for x in (-10.4,-4.1,2.3):
        fbox('dark recessed service bay',(x,-5.76,2.96),(5.76,.10,4.55),10)
        fbox('deep overhead rolled door hood',(x,-6.25,5.36),(5.88,.51,.44),3)
    fbox('yellow service door',(2.3,-6.08,2.58),(5.49,.14,4.45),9)
    for zz in (1.22,2.2,3.18,4.16):
        if not low:fbox('segmented service door seam',(2.3,-6.18,zz),(5.47,.04,.045),7)
    front_window(2.3,-6.20,4.32,1.7,.64,2)
    # The right bay is a true office volume, inset yet proud of the shopfront.
    fbox('loading office foundation',(9.3,-3.55,2.0),(8.1,5.9,3.65),11)
    fbox('office cream cladding',(9.3,-6.25,4.55),(8.15,.27,4.65),11)
    fbox('office flat rain roof',(9.3,-3.62,7.0),(8.55,5.75,.28),4)
    for x in (7.0,10.3,12.7):front_window(x,-6.42,5.32,2.36,1.62,2)
    front_window(9.5,-6.43,2.55,2.34,1.65,2)
    fbox('office entry door',(12.55,-6.42,1.85),(1.04,.15,2.5),5)
    fbox('office stair platform',(12.55,-6.35,.49),(2.05,.35,.19),9)
    # Four sawtooth modules run along travel X. The glazed vertical face is
    # offset from the pitched zinc sheet, creating actual roof silhouette.
    for j in range(4):
        x0=-13.9+7*j;x1=x0+7
        fmesh('sloped serrated zinc roof',[(x0,-6.45,7.18),(x1,-6.45,9.42),(x1,6.45,9.42),(x0,6.45,7.18)],[(0,1,2,3)],4)
        fmesh('closed saw bay front gable',[(x0,-6.36,7.17),(x1,-6.36,7.17),(x1,-6.36,9.31)],[(0,1,2)],12)
        fmesh('closed saw bay rear gable',[(x0,6.36,7.17),(x1,6.36,9.31),(x1,6.36,7.17)],[(0,1,2)],12)
        fmesh('tall sawtooth clerestory',[(x1-.03,-6.25,7.34),(x1-.03,-6.25,9.31),(x1-.03,6.25,9.31),(x1-.03,6.25,7.34)],[(0,1,2,3)],6)
        for yy in (-6.0,-2,2,6.0):
            fbox('sawtooth glass vertical mullion',(x1-.08,yy,8.32),(.18,.12,1.92),3)
        fbox('sawtooth glass sill',(x1-.09,0,7.32),(.15,12.5,.16),3)
        if not low:
            for yy in (-4.2,0,4.2):
                beam('standing seam over maintenance bay',(x0,yy,7.2),(x1,yy,9.43),.035,3)
    for x in (-13.65,13.65):
        fbox('gutter downpipe bracket',(x,6.15,6.84),(.32,.45,.32),7)
        fcylinder('service rainwater leader',(x,6.2,3.55),.095,7.1,7)
    # Roof plant becomes a second clear silhouette at varied camera angles.
    for x,y,z,r in [(-10,2.6,8.35,.46),(-3.3,1.4,9.75,.40),(11,3.2,9.48,.43)]:
        fcylinder('extraction riser',(x,y,z),r,1.25,3)
        fcylinder('curved weather cap',(x,y,z+.71),r*1.42,.17,7)
    for z in (2.0,4.0,5.8):
        fbox('rear exposed service manifold',(0,6.12,z),(24,.18,.14),7)
    for x in (-11,-2,5,11):
        fcylinder('rear air duct elbow',(x,6.0,5.7),.18,.7,7,(math.pi/2,0,0))
        if not low:fbox('service access hatch',(x,6.15,2.7),(1.45,.12,1.75),3)
    if not low:
        for x in range(-13,14,2):
            fbox('profiled sheet rib',(x,5.72,3.3),(.045,.06,5.9),3)
        for x in (-10,-4):
            fbox('forklift warning stripe',(x,-6.23,.74),(1.65,.025,.16),9)
