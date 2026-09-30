"""Editable coastal cargo terminal, metres, X along quay, Blender Z up.
Adapted manufactured edge / hull-section / batching techniques from the C1 tug.
Phone maps are actual exported PBR; no runtime procedural textures or photo plates.
"""
import argparse, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser(); p.add_argument('--out', required=True); p.add_argument('--skip-render',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]); out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
random.seed(4107)
PALETTE=[(.06,.19,.20),(.26,.055,.025),(.61,.57,.44),(.19,.24,.23),(.72,.32,.045),(.12,.31,.28),(.23,.14,.065),(.34,.37,.34),(.20,.26,.24),(.075,.085,.076),(.42,.105,.04),(.075,.20,.26),(.58,.54,.41),(.13,.19,.16),(.29,.095,.03),(.41,.33,.17)]
# A shared 4x4 region atlas: seams, salt run-off, plate fasteners, corrugated
# metal, wood grain and wet tidal bands. Geometry carries primary silhouette.
N=512; tile=N//4; images=[]
for kind in ('albedo','normal','arm'):
    image=bpy.data.images.new('coast-'+kind+'.phone',width=N,height=N)
    if kind!='albedo': image.colorspace_settings.name='Non-Color'
    pixels=[0.]*(N*N*4)
    for y in range(N):
        for x in range(N):
            s=(y//tile)*4+x//tile; u=(x%tile)/tile; v=(y%tile)/tile
            seam=min(u,1-u,v,1-v)<.018
            fastener=(abs(u-.05)<.012 or abs(u-.95)<.012) and (abs(v-.09)<.012 or abs(v-.91)<.012)
            ripple=math.sin(u*math.pi*24); grain=math.sin(v*93+math.sin(u*13)*2)
            streak=sum(math.exp(-((u-c-.009*math.sin(v*21))/.016)**2)*max(0.,(v-.1)) for c in (.12,.32,.73,.88))
            wet=max(0.,1-v/.22)*(.15 if s in (0,1,3,6,7,13) else .05)
            salt=.035*math.sin(u*35+v*7)+.013*math.sin(u*177-v*93)
            if kind=='albedo':
                rgb=[c*(1-wet)+salt for c in PALETTE[s]]
                if s in (5,8,10,11,12): rgb=[c*(.9+.1*(ripple+1)/2) for c in rgb]
                if s in (6,15): rgb=[c*(.88+.12*grain) for c in rgb]
                rust=min(.6,streak*.35)+(0.20 if seam else 0)
                if s not in (1,6,7,15): rgb=[c*(1-rust)+r*rust for c,r in zip(rgb,(.27,.073,.026))]
                if fastener: rgb=[c*.42 for c in rgb]
            elif kind=='normal':
                nx=.16*math.cos(u*math.pi*24) if s in (5,8,10,11,12) else .025*math.cos(u*39+v*11)
                ny=.07*math.cos(v*93+math.sin(u*13)*2) if s in (6,15) else .015*math.cos(v*51)
                if seam: nx+=.16*math.sin(u*math.pi*2); ny+=.16*math.sin(v*math.pi*2)
                rgb=(.5+nx,.5+ny,math.sqrt(max(0.,1-nx*nx*4-ny*ny*4))*.5+.5)
            else:
                rough=.72 if s in (1,6,7,13,14,15) else .48
                rgb=(.65 if seam or fastener else 1.,max(.24,min(.95,rough-wet+streak*.15)),.0 if s in (6,7,15) else .46)
            i=(y*N+x)*4; pixels[i:i+4]=(*[max(0.,min(1.,c)) for c in rgb],1.)
    image.pixels.foreach_set(pixels); image.filepath_raw=str(out/f'coast-{kind}.phone.png'); image.file_format='PNG'; image.save(); image.pack(); images.append(image)

def material(name,color,metal=.3,rough=.65):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Metallic'].default_value=metal; bs.inputs['Roughness'].default_value=rough
    return m
atlas=material('coast manufactured PBR atlas',(1,1,1)); bs=atlas.node_tree.nodes['Principled BSDF']; nodes=atlas.node_tree.nodes; links=atlas.node_tree.links
for kind,image in zip(('albedo','normal','arm'),images):
    tex=nodes.new('ShaderNodeTexImage'); tex.image=image
    if kind=='albedo': links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    elif kind=='normal':
        n=nodes.new('ShaderNodeNormalMap'); n.inputs['Strength'].default_value=.65; links.new(tex.outputs['Color'],n.inputs['Color']); links.new(n.outputs['Normal'],bs.inputs['Normal'])
    else:
        sep=nodes.new('ShaderNodeSeparateColor'); links.new(tex.outputs['Color'],sep.inputs['Color']); links.new(sep.outputs['Green'],bs.inputs['Roughness']); links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
glass=material('coast opaque smoked glazing',(.035,.14,.16),.18,.17)
rubber=material('coast rubber fenders',(.021,.029,.026),0,.88)
collection=None; low=False

def own(o,slot=3,mat=None):
    for c in list(o.users_collection): c.objects.unlink(o)
    collection.objects.link(o); o['region']=slot; o.data.materials.append(mat or atlas)
    return o

def box(name,loc,dims,slot=3,edge=0,mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=dims; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); own(o,slot,mat)
    if edge and not low:
        m=o.modifiers.new('rolled edges','BEVEL'); m.width=edge; m.segments=1
    return o

def cylinder(name,loc,r,h,slot=3,axis=None,mat=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8 if low else 12,radius=r,depth=h,location=loc); o=bpy.context.object; o.name=name
    if axis: o.rotation_euler=axis
    return own(o,slot,mat)

def beam(name,p1,p2,r=.07,slot=3):
    d=Vector(p2)-Vector(p1); o=cylinder(name,(Vector(p1)+Vector(p2))/2,r,d.length,slot); o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); return o

def ring(name,loc,r=.45,minor=.13,slot=3,axis=None,mat=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=10 if low else 16,minor_segments=4 if low else 6,location=loc,major_radius=r,minor_radius=minor); o=bpy.context.object; o.name=name
    if axis: o.rotation_euler=axis
    return own(o,slot,mat)

def mesh(name,verts,faces,slot=3):
    m=bpy.data.meshes.new(name); m.from_pydata(verts,[],faces); m.update(); o=bpy.data.objects.new(name,m); collection.objects.link(o); o['region']=slot; m.materials.append(atlas); return o

def rails(x0,x1,y,z):
    for h in (.42,.95): beam('continuous guardrail',(x0,y,z+h),(x1,y,z+h),.045)
    for x in range(math.ceil(x0),math.floor(x1),4 if low else 2): beam('stanchion',(x,y,z),(x,y,z+1.02),.05)

def bollard(x,y,z):
    box('welded bollard shoe',(x,y,z+.1),(.65,.55,.2),9)
    cylinder('mooring bollard',(x,y,z+.4),.18,.6,9); cylinder('cross head',(x,y,z+.65),.12,.75,3,(math.pi/2,0,0))

def container(x,y,z,length=6,slot=10):
    box('corrugated cargo container',(x,y,z+1.22),(length,2.4,2.44),slot,.025)
    for yy in (-1.22,1.22):
        for xx in (-length/2,length/2): box('ISO corner posts',(x+xx,y+yy,z+1.24),(.16,.16,2.55),3)
        for zz in (.07,2.42): box('reinforced top and bottom rail',(x,y+yy,z+zz),(length,.09,.14),slot)
        if not low:
            for xx in range(int(length*3)): box('pressed side corrugation',(x-length/2+xx/3,y+yy,z+1.22),(.06,.06,2.21),slot)
    for yy in (-.58,.58):
        box('split cargo end doors',(x+length/2+.03,y+yy,z+1.24),(.08,1.12,2.25),slot)
        if not low: beam('door locking bar',(x+length/2+.10,y+yy,z+.2),(x+length/2+.10,y+yy,z+2.2),.035)

def pallet(x,y,z):
    for yy in (-.48,0,.48): box('pallet bearer',(x,y+yy,z+.10),(1.3,.13,.18),6)
    for i in range(3 if low else 6): box('individual pallet plank',(x-.56+i*(1.12/(2 if low else 5)),y,z+.23),(.16,1.12,.07),6)

def winch(x,y,z,s=1):
    box('winch foundation',(x,y,z+.22*s),(2.2*s,1.4*s,.44*s),9)
    cylinder('winding drum',(x,y,z+.8*s),.42*s,1.2*s,3,(math.pi/2,0,0))
    for yy in (-.65,.65): cylinder('spool flange',(x,y+yy*s,z+.8*s),.61*s,.10*s,4,(math.pi/2,0,0))
    if not low:
        for yy in (-.4,-.2,0,.2,.4): ring('wound cable',(x,y+yy*s,z+.8*s),.44*s,.035*s,9,(math.pi/2,0,0))
    cylinder('drive motor',(x+.9*s,y,z+.66*s),.3*s,.6*s,5,(0,math.pi/2,0))

def freighter():
    sections=[(-33,3.0,2.8),(-30,5.0,2.8),(-23,5.7,2.8),(-12,5.9,2.9),(0,5.9,3),(12,5.8,3.15),(22,5.1,3.6),(28,3.3,4.4),(33,.16,5.3)]
    vertices=[]
    for x,b,d in sections: vertices += [(x,-b,d),(x,-b,1.2),(x,-b*.94,0),(x,-b*.65,-2.2),(x,-b*.25,-3.1),(x,b*.25,-3.1),(x,b*.65,-2.2),(x,b*.94,0),(x,b,1.2),(x,b,d)]
    for j in range(9):
        o=mesh('fair steel shell waterline / chine',vertices,[(i*10+j,(i+1)*10+j,(i+1)*10+j+1,i*10+j+1) for i in range(8)],0 if j in (0,1,7,8) else 1)
    mesh('closed transom',vertices,[tuple(reversed(range(10)))],0)
    mesh('raised forecastle deck',[(x,y,d) for x,b,d in sections[6:] for y in (-b,b)],[(0,1,3,2),(2,3,5,4)],3)
    # Side gangways and two genuinely open hold cavities, not slab silhouettes.
    for yy in (-5,5): box('continuous side gangway',(-2,yy,2.84),(57,1.65,.28),3); rails(-29,24,yy+( -.7 if yy<0 else .7),3)
    for cx in (-10,10):
        box('dark recessed cargo hold floor',(cx,0,.65),(17,7.4,.25),9)
        for yy in (-4,4): box('raised hold coaming',(cx,yy,3.35),(18,.3,1),0)
        for xx in (cx-9,cx+9): box('hold end coaming',(xx,0,3.35),(.3,8,1),0)
        for xx,yy,zz,slot in [(-4,-1.3,1,10),(3,1.3,1,11),(-3,1.3,3.45,12)]: container(cx+xx,yy,zz,6,slot)
    box('stern working deck',(-26,0,2.9),(13,10.2,.3),3)
    for x in (-29,25):
        for y in (-4.4,4.4): bollard(x,y,3.1)
    winch(27,0,4.1,.9)
    # Raised aft bridge: hull-integrated foundation, framed glass belt, roof lips.
    for z,dims,slot in [(4.5,(9,8.7,3),2),(7.3,(8,7.8,2.6),2),(9.0,(9.6,8.6,.38),2)]: box('stepped bridge house',(-26,0,z),dims,slot,.06)
    for y in (-3.95,3.95):
        for x in (-28.8,-27,-25.2,-23.4): box('individual wheelhouse glazing', (x,y,7.55),(1.48,.05,1.2),mat=glass)
        box('window sun visor',(-26,y*1.06,8.28),(8.8,.75,.15),2)
    for y in (-2.7,-.9,.9,2.7): box('forward bridge windows',(-21.94,y,7.58),(.05,1.55,1.22),mat=glass)
    for y in (-3.5,3.5): rails(-30,-22,y,6.1)
    cylinder('exhaust funnel',(-29,0,10.15),.65,2.8,9)
    box('funnel raincap',(-29,0,11.6),(1.7,1.5,.12),9)
    beam('navigation mast',(-24,0,9.2),(-24,0,14),.09,2); beam('radar crossbar',(-24,-2,12.2),(-24,2,12.2),.07,2)
    box('radar scanner',(-24,0,13.8),(2.8,.32,.2),2)
    for x in (-1,21):
        beam('deck cargo derrick pedestal',(x,0,3.2),(x,0,11),.26,4)
        beam('cargo boom',(x,0,8),(x+6,-4.6,12.5),.2,4)
        for y in (-3,3): beam('mast standing rigging',(x,0,10.8),(x-4,y,3.1),.035,9)
        beam('derrick topping cable',(x,0,11),(x+6,-4.6,12.5),.035,9)
        beam('hanging cargo cable',(x+6,-4.6,12.5),(x+6,-4.6,4.3),.04,9)
        ring('cargo hook',(x+6,-4.6,4.1),.22,.08,3,(math.pi/2,0,0)); winch(x-1,0,3.2,.75)
    for yy in (-5.92,5.92):
        beam('continuous hull rubbing strake',(-29,yy,.8),(20,yy,.8),.11,9)
        for x in (-25,-17,-5,7,18):
            ring('hung rubber fender',(x,yy,1.3),.52,.16,axis=(math.pi/2,0,0),mat=rubber)
            beam('fender chain',(x,yy,1.75),(x,yy,3),.025,9)
            if not low: box('rust below scupper',(x+1,yy,.9),(.11,.025,1.5),14)
    for y in (-4.8,4.8):
        box('bow hawse reinforcement',(28,y,2.5),(.8,.20,.75),9)
        beam('anchor stock',(28,y,2.4),(28,y,.8),.1,9)
        beam('anchor flukes',(27.5,y,1),(28.5,y,1),.1,9)
    if not low:
        for x in (-31,-21,-11,1,11,21):
            for y in (-5.94,5.94): box('welded shell plate seam',(x,y,1),(.04,.028,2),3)
        for y in (-4.3,4.3):
            for z in (3.4,3.8,4.2,4.6,5,5.4,5.8): beam('bridge ladder rung',(-30,y,z),(-29.3,y,z),.035)
        for x in (-22,20): cylinder('vent cowling',(x,3,4.1),.25,1.5,2)

def crane():
    # Four-legged, deep truss portal, not a single flat triangle.
    for x in (-4.2,4.2):
        for y in (-3.2,3.2):
            box('crane travelling bogie',(x,y,.45),(2.2,1.1,.65),9,.03)
            for dx in (-.65,.65): cylinder('bogie wheel',(x+dx,y,.35),.35,.22,3,(math.pi/2,0,0))
            beam('splayed portal leg',(x,y,.7),(x*.72,y*.65,10),.24,4)
        for zz in (3,6,9): beam('leg transom',(x,-3.2,zz),(x,3.2,zz),.12,4)
        for i in range(3):
            zz=i*3+.7; beam('depth X brace',(x,-3.2,zz),(x,3.2,zz+3),.1,4); beam('depth X brace',(x,3.2,zz),(x,-3.2,zz+3),.1,4)
    box('machine deck',(0,0,10),(8,6,.5),3)
    box('drive shed',(0,1.9,11.3),(4,2,2.2),5,.08)
    box('operator cabin',(3.2,-1.9,11.2),(2.4,2.2,2),4,.05)
    box('operator glazing',(3.22,-3.01,11.45),(1.95,.04,1.1),mat=glass)
    box('operator side glazing',(4.43,-1.9,11.45),(.04,1.7,1.1),mat=glass)
    box('stacked counterweight',(-6.5,0,11),(4,4,2),7)
    for y in (-1.1,1.1):
        beam('boom lower chord',(-5,y,10.8),(18,y,15.8),.15,4)
        beam('boom upper chord',(-5,y,12.6),(18,y,17),.15,4)
        for i in range(8):
            x=-5+i*2.9; z=10.8+(x+5)*5/23
            beam('boom Warren lattice',(x,y,z),(x+2.9,y,z+2.35),.08,4)
            beam('boom lattice vertical',(x,y,z),(x,y,z+1.8),.07,4)
    for x in range(-5,18,3): beam('boom depth transverse',(x,-1.1,11.8+(x+5)*5/23),(x,1.1,11.8+(x+5)*5/23),.08,4)
    beam('kingpost',(0,0,11),(0,0,19),.22,4)
    for y in (-.8,.8): beam('boom suspension',(0,y,19),(17,y,16.6),.055,9); beam('counter suspension',(0,y,19),(-7,y,12),.055,9)
    for y in (-.4,.4): beam('hoist fall',(17,y,16.6),(17,y,4.5),.035,9)
    cylinder('head sheave',(17,0,16.7),.55,.9,9,(math.pi/2,0,0)); cylinder('hook block',(17,0,4.5),.45,.8,4,(math.pi/2,0,0)); ring('lifting hook',(17,0,3.8),.34,.1,axis=(math.pi/2,0,0))
    winch(-1,0,10.3)
    rails(-3.7,3.7,-3,10.3)
    if not low:
        for z in range(1,10): beam('access ladder',(4.15,2.6,z),(4.15,3.2,z),.035)
        beam('ladder stile',(4.15,2.6,.5),(4.15,2.6,10),.04); beam('ladder stile',(4.15,3.2,.5),(4.15,3.2,10),.04)

def pier():
    box('pile cap loading apron',(0,0,0),(32,17,.48),7,.05)
    box('narrow access causeway',(0,-22,0),(4.2,28,.35),7)
    for y in range(-34,-9,4):
        for x in (-1.7,1.7): cylinder('access trestle pile',(x,y,-2.4),.24,4.6,13)
        beam('access pile crosshead',(-2,y,-.45),(2,y,-.45),.16,9)
    for x in (-1.9,1.9): beam('access edge girder',(x,-36,-.5),(x,-8,-.5),.17,9)
    for x in range(-14,16,4):
        for y in (-7,0,7):
            cylinder('tidally stained piling',(x,y,-2.4),.3,4.6,13)
            box('pile crosshead',(x,y,-.48),(1.6,1.2,.4),3)
        beam('underdeck cross girder',(x,-8,-.75),(x,8,-.75),.18,9)
    for y in (-6,6): beam('deep longitudinal joist',(-15,y,-.7),(15,y,-.7),.21,9)
    for x in (-14,-7,0,7,14):
        for y in (-8.6,8.6):
            cylinder('fender timber',(x,y,-1.0),.24,3,6)
            ring('hung dock tire',(x,y,-.9),.6,.2,axis=(math.pi/2,0,0),mat=rubber)
        bollard(x,-7.8,.25)
    for y in (-3.2,3.2): box('crane rail',(0,y,.32),(31,.12,.12),3)
    if not low:
        for x in range(-15,16,2): box('apron expansion joint',(x,0,.245),(.028,16,.014),9)
        for x in (-13,13): box('drainage grate',(x,6,.26),(2,.7,.04),9)

def warehouse():
    box('loading plinth',(0,0,.18),(28,12,.36),7)
    box('weathered back cladding',(0,5.95,3.6),(28,.2,6.8),5)
    for x in (-14,14):
        box('gable side cladding',(x,0,3.6),(.18,12,6.8),5)
        mesh('gable ventilated infill',[(x,-6,7),(x,6,7),(x,0,9)],[(0,1,2)],5)
        box('gable ventilation louvre',(x+( -.10 if x<0 else .10),0,7.7),(.10,2.2,.62),9)
    # Front is fully open between posts. Interior stock and trusses remain visible.
    for x in range(-14,15,7):
        for y in (-5.8,5.8): box('structural steel I column',(x,y,3.7),(.25,.25,7.2),3)
        beam('roof diagonal',(x,-6,7),(x,0,9),.11,3); beam('roof diagonal',(x,0,9),(x,6,7),.11,3); beam('roof tie',(x,-6,7),(x,6,7),.095,3)
        if not low:
            for y in (-3,3): beam('roof web',(x,y,7),(x,0,9),.06,3)
    mesh('corrugated pitched roofing',[(-14,-6.6,7),(14,-6.6,7),(-14,0,9.2),(14,0,9.2),(-14,6.6,7),(14,6.6,7)],[(0,1,3,2),(2,3,5,4)],8)
    for y in (-6.5,6.5): beam('rain gutter',(-14,y,7),(14,y,7),.1,3)
    for x in (-13.5,13.5): beam('downpipe',(x,6.1,6.9),(x,6.1,.5),.07,14)
    for x in (-10.5,3.5): box('rolled-up loading shutter',(x,-5.96,6.8),(6.5,.4,.45),9)
    box('partially dropped door',(10.5,-5.96,5.8),(6.5,.16,2.5),5)
    for x in (-9,-3,4):
        for y in (2,4):
            pallet(x,y,.37); box('bound shipping crate',(x,y,1.2),(1.5,1.2,1.5),6,.025)
            for xx in (-.6,.6): box('crate steel binding',(x+xx,y,1.2),(.08,1.25,1.6),9)
    box('steel mezzanine',(-9,3,3.6),(7,4,.22),3); rails(-12,-6,.9,3.7)
    for y in (.5,4.7): box('mezzanine support',(-6,y,1.8),(.18,.18,3.6),3)
    if not low:
        for x in range(-13,14): box('pressed rear wall rib',(x,5.83,3.6),(.05,.05,6.7),5)
        for y in range(-5,6):
            for x in (-13.89,13.89): box('pressed gable wall rib',(x,y,3.6),(.05,.05,6.7),5)
        for x in range(-13,14,4): box('rust at cladding foot',(x,5.80,.65),(1.2,.04,.35),14)
        for x in (-10.5,-3.5,3.5,10.5): box('bay floodlight',(x,-5.85,6.3),(.48,.25,.2),2)
    pallet(-10,-7,.02); pallet(-8.5,-7,.02)
    winch(8,1,.35,.7)

def logistics():
    container(-4,0,0,6,10); container(3,2.8,0,6,11); container(3,2.8,2.55,6,12)
    for x,y in ((1,-2),(3,-2),(4.5,-1.5)):
        pallet(x,y,0); pallet(x+.05,y+.04,.3)
    for x,y in ((-1,-2),(-.2,-2),(-1,-1.2)):
        cylinder('steel cargo drum',(x,y,.45),.31,.9,11)
        if not low:
            for z in (.12,.75): ring('pressed drum hoops',(x,y,z),.32,.025,3)
    # Compact forklift: mast forks, open protective cage, separate wheels.
    box('forklift chassis',(-1,-5,.7),(2.8,1.35,.6),4,.08); box('rear counterweight',(-2,-5,1.1),(.75,1.45,.9),4,.05)
    for x in (-1.9,-.1):
        for y in (-5.75,-4.25): cylinder('forklift tire',(x,y,.48),.4,.3,axis=(math.pi/2,0,0),mat=rubber)
    for x in (-1.6,-.25):
        for y in (-5.5,-4.5): beam('overhead guard post',(x,y,1),(x,y,2.5),.045,9)
    box('forklift safety roof',(-.9,-5,2.55),(1.8,1.2,.1),9)
    box('forklift seat',(-1,-5,1.35),(.6,.55,.55),mat=rubber)
    for y in (-5.45,-4.55):
        box('mast rail',(.6,y,1.9),(.12,.12,3.2),9)
        box('fork on ground',(1.3,y,.18),(1.5,.13,.12),3)

def barge():
    vertices=[(-16,-4,-1.8),(16,-4,-1.8),(16,4,-1.8),(-16,4,-1.8),(-18,-5,1),(18,-5,1),(18,5,1),(-18,5,1)]
    mesh('flat cargo lighter hull',vertices,[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],1)
    box('barge deck',(0,0,1),(35,9.6,.28),3)
    for x in (-13,-5,3,11): container(x,-1,1.15,6,10 if x<0 else 11)
    container(-5,1.8,3.7,6,12)
    for y in (-4.5,4.5): rails(-16,16,y,1.2)
    for x in (-16,16):
        for y in (-3.9,3.9): bollard(x,y,1.2)
    box('lighter utility cabin',(14,2.2,2.3),(3.5,3,2.1),5)
    box('lighter glazed wheelhouse',(14,3.72,2.65),(2.5,.06,.8),mat=glass)

def station():
    winch(0,0,0); bollard(-2,0,0); bollard(2,0,0)
    for i in range(3): ring('hemp mooring coil',(2,-1,.1+i*.07),.5-i*.08,.055,15)
    for i in range(3): pallet(-2,-1.6,i*.3)
    ring('stored rubber fender',(0,-1.6,.23),.62,.23,mat=rubber)

recipes={'cargo-freighter':freighter,'harbor-crane':crane,'loading-pier':pier,'open-warehouse':warehouse,'logistics-yard':logistics,'cargo-barge':barge,'dock-station':station}
# Projection is made per separate manufactured part before join; all region UVs
# stay inside a gutter. Regions share one atlas/material so one surface draw/model.
def prepare(o):
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    for mod in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
    if o.type!='MESH': return
    uv=o.data.uv_layers.new(name='manufactured region UV') if not o.data.uv_layers else o.data.uv_layers[0]
    uv.name='manufactured region UV'
    slot=int(o.get('region',3)); tx=slot%4; ty=slot//4
    coords=[v.co for v in o.data.vertices]
    lo=[min(v[i] for v in coords) for i in range(3)]; hi=[max(v[i] for v in coords) for i in range(3)]
    for face in o.data.polygons:
        dominant=max(range(3),key=lambda i:abs(face.normal[i])); axes=[i for i in range(3) if i!=dominant]
        for li in face.loop_indices:
            v=coords[o.data.loops[li].vertex_index]; vals=[(v[i]-lo[i])/max(.001,hi[i]-lo[i]) for i in axes]
            uv.data[li].uv=((tx+.03+vals[0]*.94)/4,(ty+.03+vals[1]*.94)/4)
    o.select_set(False)

banks={}
for tier in ('full','lod'):
    low=tier=='lod'; bank=[]; groups=[]
    if low:
        for o in banks['full']: o.name='source:'+o.name
    for name,recipe in recipes.items():
        collection=bpy.data.collections.new(tier+':'+name); bpy.context.scene.collection.children.link(collection)
        recipe(); objects=list(collection.objects)
        for o in objects: prepare(o); o['prototype']=name
        groups.append((name,objects))
    if not low: bpy.ops.wm.save_as_mainfile(filepath=str(out/'coast-harbor.source.blend'))
    for name,objects in groups:
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects: o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]; bpy.ops.object.join(); joined=bpy.context.object; joined.name=name
        bpy.context.scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); bank.append(joined)
    banks[tier]=bank
    bpy.ops.object.select_all(action='DESELECT')
    for o in bank: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/('coast-harbor'+('-lod' if low else '')+'.raw.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_animations=False)
    for o in bank: o.hide_render=low; o.hide_set(low)
    if low:
        for o in bank: o.name='lod:'+o.name
        for o in banks['full']: o.name=o.name.removeprefix('source:')
# Save a reusable model bank; all prototypes share origin and are parked locally.
bpy.ops.wm.save_as_mainfile(filepath=str(out/'coast-harbor.batched.blend'))
# The separate-parts editable scene can be reproduced from this script; bank file
# remains useful for material tweaks and inspection without rebuilding.
if not a.skip_render:
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=12; scene.cycles.use_denoising=True
    scene.render.resolution_x=900; scene.render.resolution_y=600; scene.render.resolution_percentage=100
    scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.23,.31,.32,1); scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
    scene.view_settings.view_transform='AgX'
    sun=bpy.data.lights.new('coastal overcast key','SUN'); sun.energy=2.2; sun.angle=.35; sunlight=bpy.data.objects.new('coastal overcast key',sun); scene.collection.objects.link(sunlight); sunlight.rotation_euler=(.42,-.58,-.4)
    for name,loc,energy,size in [('key',(15,-25,60),16000,45),('fill',(-30,20,40),9000,35)]:
        d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.size=size; o=bpy.data.objects.new(name,d); scene.collection.objects.link(o); o.location=loc; o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
    d=bpy.data.cameras.new('source inspection'); cam=bpy.data.objects.new('source inspection',d); scene.collection.objects.link(cam); scene.camera=cam; d.type='ORTHO'
    def render(name,target,scale,angle,height):
        for o in banks['full']: o.hide_render=o.name!=name
        d.ortho_scale=scale; t=Vector(target); rad=math.radians(angle); cam.location=t+Vector((scale*math.sin(rad),-scale*math.cos(rad),height)); cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler(); scene.render.filepath=str(out/f'{name}-{angle:03d}.png'); bpy.ops.render.render(write_still=True)
    for name,target,scale,height in [('cargo-freighter',(0,0,3),76,27),('harbor-crane',(3,0,8),33,15),('open-warehouse',(0,0,4),36,12)]:
        for angle in ((0,40,80,120,160,200,240,280,320) if name=='cargo-freighter' else (0,40,120)): render(name,target,scale,angle,height)
    for name,target,scale,height in [('cargo-barge',(0,0,2),43,17),('loading-pier',(0,0,-1),39,16),('logistics-yard',(0,0,1),18,8),('dock-station',(0,0,.5),7,4)]: render(name,target,scale,40,height)
print('Coast authoring outputs',out)
