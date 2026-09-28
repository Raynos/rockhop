"""Build the B tabletop's sculpted, UV-mapped terrain tray as a runtime GLB.

Run from repository root:
  blender --background --python prototypes/world-map-b/blender/build_terrain.py

This asset shares the viewer's land-height equation so the twelve towers and
road remain on the ground. All extra high-frequency sculpting falls away at
the route. The terrain, escarpments and quarry cuts are actual mesh surfaces.
"""
from pathlib import Path
import bpy
import math
from mathutils import Vector, noise

ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / 'textures'
OUT = ROOT / 'assets' / 'sculpted-terrain.glb'
OUT.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def gauss(x,z,cx,cz,sx,sz):
    return math.exp(-(((x-cx)/sx)**2+((z-cz)/sz)**2))

def terrain(x,z):
    fine=.07*math.sin(x*5.2-z*3.6)+.035*math.cos(z*8.2+x*3.8)
    waves=.11*math.sin(x*2.4+z*1.6)+fine
    coast=.48+max(0,x+6.9)*.04+.87*gauss(x,z,-5.4,-2.2,2,2.4)
    forest=1.44*gauss(x,z,-2.8,-2.5,2.1,1.25)+1.25*gauss(x,z,-1.7,2.65,1.25,1.1)+1.0*gauss(x,z,-4.15,2.4,1.2,1.3)
    qr=math.hypot((x-2.05)/2.35,(z+2.1)/1.9)
    quarry=(2.28*gauss(x,z,2.05,-2.1,3.35,2.65)-(.37*math.floor((1.08-qr)*5) if qr<1.08 else 0)) if -.2<x<4.7 else 0
    mountain=2.55*gauss(x,z,6.65,-2.55,1.4,1.2)+1.65*gauss(x,z,5.5,2.9,1.25,1.1)+1.5*gauss(x,z,8.0,1.5,1.0,1.25)
    front=(1.02*gauss(x,z,2.4,3.7,3.5,1.15) if -.3<x<5.2 else .8*gauss(x,z,7,3.7,2.4,1.2) if x>=5.2 else .48*gauss(x,z,-2.6,3.8,2.5,1.1) if x>-4.7 else 0)
    ravine=-1.17*gauss(x,z,4.35,1.8,.57,2.5)
    shelf=max(-.45,(x+6.5)*.25) if x<-6.5 else 0
    return max(.16,coast+forest+quarry+mountain+front+ravine+waves+shelf)

ROUTE=[(-7.95,2.0),(-7.15,1.1),(-6.5,-.15),(-5.65,-1.05),(-4.7,.45),(-3.85,1.38),(-2.8,2.22),(-1.65,1.78),(-.5,1.05),(.65,1.28),(1.75,2.03),(2.7,2.37),(3.75,2.06),(4.5,1.28),(5.25,.55),(6.1,-.4),(7.2,-.05),(7.8,1.0),(8.05,2.1)]
def road_distance(x,z):
    best=99.
    for (ax,az),(bx,bz) in zip(ROUTE,ROUTE[1:]):
        dx,dz=bx-ax,bz-az
        t=max(0.,min(1.,((x-ax)*dx+(z-az)*dz)/(dx*dx+dz*dz)))
        best=min(best,math.hypot(x-(ax+t*dx),z-(az+t*dz)))
    return best

def field(x,z,y=0):
    return noise.noise(Vector((x,z,y)))

def sculpt(x,z):
    large=.075*field(x*2.2,z*2.2,.37)+.039*field(x*6.5,z*6.5,1.71)+.012*field(x*19,z*19,2.4)
    if -.2<x<4.8: large+=.063*field(x*3.8,z*3.8,5.2)
    if x>4.8: large+=.08*field(x*2.7,z*2.7,7.6)
    corridor=min(1.,max(0.,(road_distance(x,z)-.48)/1.05))
    return large*(.11+.89*corridor)

def material(name,filename,roughness=1):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nodes=m.node_tree.nodes;links=m.node_tree.links
    bsdf=nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=roughness
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(TEXTURES/filename),check_existing=True)
    tex.extension='REPEAT';tex.interpolation='Linear'
    links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    return m

materials={
 'coast':material('Coast sandstone and shingle','coast_sand_rocks_02_diff_1k.jpg'),
 'forest':material('Mossy forest earth','forest_ground_04_diff_1k.jpg'),
 'quarry':material('Cut orange sandstone','sandstone_cracks_diff_1k.jpg'),
 'snow':material('Compact alpine snow','snow_02_diff_1k.jpg'),
 'warmrock':material('Warm fractured cliff','marble_cliff_03_diff_1k.jpg'),
 'coldrock':material('Cold fractured cliff','marble_cliff_05_diff_1k.jpg'),
 'quarrywall':material('Quarry bench strata','marble_cliff_03_diff_1k.jpg'),
}

def mesh_object(name,verts,faces,uvs,mat,smooth=False):
    me=bpy.data.meshes.new(name)
    me.from_pydata(verts,[],faces);me.update()
    uv_layer=me.uv_layers.new(name='UV0')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uv_layer.data[li].uv=uvs[me.loops[li].vertex_index]
        poly.use_smooth=smooth
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob

# Dense top mesh: this is sculpted in Blender coordinates (X, -Z, Y-up), then
# converted by the glTF exporter to Three's Y-up convention.
for left,right,key in [(-9.175,-5.25,'coast'),(-5.25,-.2,'forest'),(-.2,4.8,'quarry'),(4.8,9.175,'snow')]:
    nx=round((right-left)/.055);nz=174
    verts=[];uvs=[];faces=[]
    for j in range(nz+1):
        z=-4.625+9.25*j/nz
        for i in range(nx+1):
            x=left+(right-left)*i/nx
            y=terrain(x,z)+sculpt(x,z)
            verts.append((x,-z,y));uvs.append(((x-left)*1.14,(z+4.625)*1.14))
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i;b=a+1;d=a+nx+1;c=d+1
            faces.append((a,d,c,b))
    mesh_object('Sculpted '+key+' land',verts,faces,uvs,materials[key],True)

def cliff_strip(name,start,end,zfront,key,seed):
    nx=round((end-start)/.047);ny=19
    verts=[];uvs=[];faces=[]
    for i in range(nx+1):
        x=start+(end-start)*i/nx
        top=terrain(x,3.82)+sculpt(x,3.82)
        for j in range(ny+1):
            t=j/ny;y=.045+(top-.045)*(1-t)
            # Erosion and large vertical joints are real displaced geometry.
            groove=math.pow(abs(math.sin(x*2.75+seed)),11)*-.14
            rock=.19*field(x*3.1,y*3.1,seed)+.076*field(x*9.3,y*9.3,seed+4)
            bulge=.13*math.sin((1-t)*math.pi*2.4+x*1.18)
            z=3.78+(zfront-3.78)*t+rock+bulge+groove
            verts.append((x+rock*.28,-z,y));uvs.append(((x-start)*.94,y*.92))
    for i in range(nx):
        for j in range(ny):
            a=i*(ny+1)+j;b=(i+1)*(ny+1)+j
            faces.append((a,a+1,b+1,b))
    return mesh_object(name,verts,faces,uvs,materials[key],True)

cliff_strip('Forest ravine cliff',-4.7,-.3,4.68,'warmrock',1.8)
cliff_strip('Quarry escarpment',-.3,4.8,4.72,'warmrock',3.2)
cliff_strip('Alpine stone face',4.8,9.175,4.68,'coldrock',5.1)

# The quarry wall is a sequence of cut open arcs with stratified, rough faces.
# It is modeled as stone, not as a level marker or selectable arena.
for k in range(6):
    radius=.34+k*.16
    nx=74;ny=5;verts=[];uvs=[];faces=[]
    for i in range(nx+1):
        a=math.pi*i/nx
        irregular=1+.038*field(i*.27,k*.71,4.0)
        x=2.05+2.35*radius*math.cos(a)*irregular
        z=-1.92+1.9*radius*math.sin(a)*irregular
        top=terrain(x,z)+sculpt(x,z)+.22
        for j in range(ny+1):
            t=j/ny
            y=top-.6*t+.024*field(i*.53,j*.67,k*1.5)
            offset=.026*field(i*.36,j*.37,k+2)
            verts.append((x+math.cos(a)*offset,-z-math.sin(a)*offset,y))
            uvs.append((i/nx*4.4,y*1.5))
    for i in range(nx):
        for j in range(ny):
            a=i*(ny+1)+j;b=(i+1)*(ny+1)+j
            faces.append((a,b,b+1,a+1))
    mesh_object(f'Carved quarry bench {k+1}',verts,faces,uvs,materials['quarrywall'],False)

for ob in bpy.context.scene.objects:
    if ob.type=='MESH': ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT),export_format='GLB',export_yup=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_image_format='AUTO')
print('Exported',OUT,OUT.stat().st_size,'bytes',len([o for o in bpy.context.scene.objects if o.type=='MESH']),'meshes')
