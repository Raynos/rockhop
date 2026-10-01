"""Measured native glove surface witnesses and literal neutral geometry overlays.

Both normal signs are reported. Markers are diagnostic, not grip sockets.
"""
import bpy,json,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-landmarks';MASTER=BASE/'parent-assembly/donor-fit05/rider.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(MASTER);d=json.loads((OUT/'report.json').read_text());mapping=json.loads((OUT/'native-weight-transfer-map.json').read_text());native=json.loads((OUT/'native-bones.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(MASTER));body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('NEW protected'));body.data.calc_loop_triangles();points=[body.matrix_world@v.co for v in body.data.vertices];surfaces=[]
for h in d['hands']:
 side=h['nativeAnatomicalSide'];ids=set(next(r['completeVertexIds'] for r in mapping['matches'] if r['nativeSide']==side));tris=[tuple(t.vertices) for t in body.data.loop_triangles if set(t.vertices)<=ids];bvh=BVHTree.FromPolygons(points,tris,all_triangles=True);origin=Vector(h['skeletalPalmCentre']);normal=Vector(h['sourceCanonicalNormalMapped']).normalized();hits=[]
 for sign in [1,-1]:
  direction=normal*sign;hit,n,index,distance=bvh.ray_cast(origin,direction,.10)
  assert hit is not None,'No actual native palm-plane surface intersection'
  hits.append({'canonicalNormalSign':sign,'point':list(hit),'normal':list(n),'distanceFromSkeletalCentreM':distance,'sourceTriangleVertices':list(tris[index]),'status':'Actual native glove surface ray witness; palm/dorsum assignment unverified; not runtime grip socket'})
 transform=Matrix(h['sourceArmatureToBody']);proximal={}
 for name in [f'clavicle.{side}',f'shoulder01.{side}',f'upperarm01.{side}',f'upperarm02.{side}',f'lowerarm01.{side}']:
  b=native['bones'][name];proximal[name]={'transportedHead':list(transform@Vector(b['headLocal'])),'transportedTail':list(transform@Vector(b['tailLocal'])),'status':'Actual native proximal bone transported with hand rigid transform; not a measured new-body joint'}
 surfaces.append({'side':side,'hits':hits,'nativeProximalTransportDiagnostic':proximal})
scene=bpy.context.scene
for o in list(scene.objects):
 if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
gray=bpy.data.materials.new('Diagnostic actual neutral geometry');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.36,.36,.36,1);bs.inputs['Roughness'].default_value=.7
for o in scene.objects:
 if o.type=='MESH':
  for i in range(len(o.data.materials)):o.data.materials[i]=gray
  if not o.data.materials:o.data.materials.append(gray)
def mat(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');s=n.new('ShaderNodeEmission');s.inputs[0].default_value=(*color,1);s.inputs[1].default_value=.8;m.node_tree.links.new(s.outputs[0],out.inputs[0]);return m
red=mat('Red +canonical normal surface',(1,.07,.04));blue=mat('Blue -canonical normal surface',(.03,.18,1));yellow=mat('Yellow actual wrist and MCP skeleton',(1,.8,.04));objects={}
def ball(p,r,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=r,location=p);o=bpy.context.object;o.data.materials.append(m);return o
def line(a,b,r,m):
 a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(m);return o
for h,s in zip(d['hands'],surfaces):
 side=h['nativeAnatomicalSide'];objs=[]
 for b in h['bones'].values():
  if b is h['bones'].get('lowerarm01.'+side) or b is h['bones'].get('lowerarm02.'+side):continue
  objs.append(line(b['bodyHead'],b['bodyTail'],.0012,yellow))
 objs.append(ball(h['wristJoint'],.005,yellow));objs.append(ball(h['skeletalPalmCentre'],.004,yellow))
 for hit in s['hits']:objs.append(ball(hit['point'],.0045,red if hit['canonicalNormalSign']==1 else blue))
 objects[side]=objs
world=bpy.data.worlds.new('Neutral diagnostic studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
 light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;o=bpy.data.objects.new(name,light);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Actual native landmarks');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';views=[]
for h in d['hands']:
 side=h['nativeAnatomicalSide'];target=Vector(h['skeletalPalmCentre']);cd.ortho_scale=.25
 for label,yaw in [('front',0),('rear',180)]:
  a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();p=OUT/f'actual-native-{side}-{label}.png';scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);views.append({'side':side,'view':label,'file':str(p),'sha256':sha(p),'status':'Actual neutral source geometry plus explicitly colored measured skeleton/surface markers'})
assert before==sha(MASTER)
(OUT/'surface-witness.json').write_text(json.dumps({'status':'Measured visible surface candidates, no contact/socket claim','selectedSource':str(MASTER),'sourceSHA256Before':before,'sourceSHA256After':sha(MASTER),'surfaces':surfaces,'views':views,'recipeSHA256':sha(Path(__file__)),'CPUThreads':2,'limits':['The original source palm normal sign is not certified anatomically here.','Markers overlay and may be occluded by geometry; no retouched surface renders.','Transported native proximal bones are anatomy references, not a new body fit.']},indent=2)+'\n');print('ACTUAL_NATIVE_SURFACE_WITNESSES_FROZEN',flush=True)
