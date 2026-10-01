"""Actual source-geometry section witnesses; false-color diagnostic, not new asset."""
import bpy,numpy as np,json,hashlib,math,time
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/B-local-volume/trial03');O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();g=R/'trial02/character.glb';before=sha(g)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(g));s=bpy.context.scene;meshes=[o for o in s.objects if o.type=='MESH'];body=next(o for o in meshes if 'three-contour panel' in o.name);head=next(o for o in meshes if 'male head' in o.name)
def mat(name,color,emission=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.65
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=1
 return m
cloth=mat('Diagnostic actual retained cloth cyan',(.08,.43,.5));skin=mat('Diagnostic unchanged native skin magenta',(.46,.16,.30));red=mat('Actual nonplanar cloth seam red',(1,.15,.06),True);secskin=mat('Actual native skin section yellow',(1,.7,.05),True);seccloth=mat('Actual garment section blue',(.05,.3,1),True)
for o in meshes:
 for k in range(len(o.data.materials)):o.data.materials[k]=skin if o==head else cloth

def curve(name,lines,material,radius=.0008):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=0
 for line in lines:
  sp=c.splines.new('POLY');sp.points.add(len(line)-1)
  for p,x in zip(sp.points,line):p.co=(*x,1)
 obj=bpy.data.objects.new(name,c);s.collection.objects.link(obj);c.materials.append(material)
for l in json.loads((R/'trial02/exact-three-loops.json').read_text()):q=l['coordinatesMetres'];curve('Actual cloth '+str(l['length'])+' seam',[q+[q[0]]],red,.0012)
sections=[]
for o in [body,head]:
 v=np.array([o.matrix_world@x.co for x in o.data.vertices]);f=np.array([p.vertices[:] for p in o.data.polygons]);
 for z in [1.485,1.515,1.555]:
  lines=[]
  for tri in v[f]:
   if tri[:,2].min()>z or tri[:,2].max()<z:continue
   pts=[]
   for a,b in zip(tri,np.roll(tri,-1,axis=0)):
    if (a[2]<z)!=(b[2]<z):pts.append(a+(z-a[2])/(b[2]-a[2])*(b-a))
   if len(pts)==2:lines.append(pts)
  curve(o.name+' source planeZ'+str(z),lines,secskin if o==head else seccloth);sections.append(dict(mesh=o.name,z=z,actualTriangleSegments=len(lines)))
world=bpy.data.worlds.new('Matched studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;s.world=world
for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
c=bpy.data.cameras.new('Actual nonplanar source sections');cam=bpy.data.objects.new(c.name,c);s.collection.objects.link(cam);s.camera=cam;c.type='ORTHO';c.ortho_scale=.46;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';rows=[]
for label,yaw in [('front',0),('profile',90),('rear',180),('three-quarter',45)]:
 a=math.radians(yaw);target=Vector((0,.015,1.53));cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),.03));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();p=O/('actual-3d-sections-'+label+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);rows.append(dict(label=label,path=str(p),sha256=sha(p)))
assert before==sha(g);(O/'actual-3d-sections.json').write_text(json.dumps(dict(status='Read-only false-color source diagnosis; no reconstructed garment',inputGLB=str(g),inputSHA=before,sourceSHAfter=sha(g),legend={'cyan':'actual retained cloth','magenta':'unchanged native skin','red':'194/43/23 nonplanar cloth seam circuits','yellow':'native skin actual triangle intersections at Z1.485/1.515/1.555','blue':'cloth actual triangle intersections at same levels'},sections=sections,views=rows,threads=2,device='CPU',recipeSHA=sha(__file__)),indent=2)+'\n')
