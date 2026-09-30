"""Deterministic Street head refinement; geometry-only graft preserves clips.
Blender --python refine_head.py -- --input candidate-v4.glb --out work/head-detail.glb [--lod]
No disputed groom/beard is imported. Hair, eye and brow additions bind to head.
"""
import bpy,json,math,argparse,sys,random,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(Path(a.input).resolve()))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
body=next(o for o in bpy.data.objects if o.type=='MESH' and 'neural' in o.name)
bone=arm.data.bones['head'];origin=bone.head_local;up=(bone.tail_local-bone.head_local).normalized();right=Vector((0,1,0));front=right.cross(up).normalized()
def local(p):
 d=p-origin;return Vector((d.dot(front),d.dot(right),d.dot(up)))
def world(p):return origin+front*p[0]+right*p[1]+up*p[2]
def gltf(p):return [p.x,p.z,-p.y]
coords=[v.co.copy() for v in body.data.vertices];spaces=[local(p) for p in coords]
head=[sum(g.weight for g in v.groups if body.vertex_groups[g.group].name=='head')>.95 for v in body.data.vertices]
# Identify the existing cap from its actual painted albedo; face and neck remain separate.
img=next(n.image for m in body.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
w,h=img.size;pixels=np.empty(w*h*4,dtype=np.float32);img.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4)
uv=body.data.uv_layers.active;dark=[False]*len(coords)
for f in body.data.polygons:
 for li in f.loop_indices:
  i=body.data.loops[li].vertex_index;p=spaces[i]
  if not head[i] or p.z<.09:continue
  t=uv.data[li].uv;c=pixels[min(h-1,max(0,int(t.y*h))),min(w-1,max(0,int(t.x*w))),:3]
  if float(c.mean())<.22:dark[i]=True
patches=[]
for i,v in enumerate(body.data.vertices):
 if not head[i]:continue
 p=spaces[i].copy()
 if dark[i]:
  p.x=.014+(p.x-.014)*.91;p.y*=.93;p.z=.12+(p.z-.12)*.92
 elif .024<p.z<.06 and p.x>.04:
  # A small, bounded jaw-width correction; no facial-hair geometry.
  p.y*=1.045
 new=world(p);body.data.vertices[i].co=new
 patches.append({'old':gltf(coords[i]),'position':gltf(new),'index':i})
# Average geometric normals across UV duplicates on the head, preserving body normals.
body.data.update();normal_sum={}
for f in body.data.polygons:
 vs=list(f.vertices);q0=body.data.vertices[vs[0]].co
 for j in range(1,len(vs)-1):
  q1=body.data.vertices[vs[j]].co;q2=body.data.vertices[vs[j+1]].co;n=(q1-q0).cross(q2-q0)
  for vi in [vs[0],vs[j],vs[j+1]]:
   if head[vi]:
    key=tuple(round(x,5) for x in coords[vi]);normal_sum[key]=normal_sum.get(key,Vector())+n
for patch in patches:
 n=normal_sum.get(tuple(round(x,5) for x in coords[patch['index']]),Vector((1,0,0)))
 if n.length:n.normalize()
 patch['normal']=gltf(n);del patch['index']
head_faces=[list(f.vertices) for f in body.data.polygons if all(head[i] for i in f.vertices)]
bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],head_faces,all_triangles=False)
center=world((.014,0,.12));rng=random.Random(43009)
def scalp(theta,phi):
 d=front*(math.cos(phi)*math.cos(theta))+right*(math.cos(phi)*math.sin(theta))+up*math.sin(phi)
 p,n,_,_=bvh.ray_cast(center+d*.45,-d,1)
 if p is None:p=center+d*.10;n=d
 return p,n.normalized()
verts=[];faces=[];colours=[]
def tube(points,normals,radius,color,sides=4):
 start=len(verts)
 for j,(p,n) in enumerate(zip(points,normals)):
  t=j/(len(points)-1);taper=max(.055,math.sin(math.pi*(.14+.86*t)))
  tangent=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized()
  side=tangent.cross(n).normalized()
  if side.length<.1:side=right
  for k in range(sides):
   angle=k*math.tau/sides
   co=p+side*(radius*taper*math.cos(angle))+n*(radius*.4*taper*math.sin(angle))
   verts.append(tuple(co));shade=.75+.25*math.sin(math.pi*t)
   colours.append(tuple(min(1,x*shade) for x in color)+(1,))
 for j in range(len(points)-1):
  for k in range(sides):
   x=start+j*sides+k;y=start+j*sides+(k+1)%sides;z=x+sides;q=y+sides
   faces.extend([(x,y,z),(y,q,z)])
 if sides>2:faces.extend([tuple(start+k for k in range(sides-1,-1,-1)),tuple(start+(len(points)-1)*sides+k for k in range(sides))])
count=64 if not a.lod else 9
for i in range(count):
 theta=i*2.399963229728653+(.15 if i%2 else 0)
 phi=.15+(i/max(1,count-1))*.99
 points=[];normals=[];phase=rng.uniform(-1,1);sweep=rng.uniform(.11,.32)
 rings=10 if not a.lod else 3
 for j in range(rings):
  t=j/(rings-1);th=theta+(sweep+.13)*t+.015*math.sin(math.pi*t+phase)
  ph=max(.05,phi-.28*t)
  p,n=scalp(th,ph)
  n=(p-center).normalized();p+=n*(.001+.0015*math.sin(math.pi*t))
  points.append(p);normals.append(n)
 # The generated scalp is lumpy; smooth the sweep instead of reproducing
 # every triangle in a raised zigzag. Fine strands retain only a small tip lift.
 for _ in range(4 if not a.lod else 1):
  points=[points[0]]+[points[j]*.5+(points[j-1]+points[j+1])*.25 for j in range(1,len(points)-1)]+[points[-1]]
 normals=[(p-center).normalized() for p in points]
 points[-1]+=normals[-1]*.002
 variation=rng.uniform(.85,1.2)
 tube(points,normals,.0014 if not a.lod else .0018,tuple(c*variation for c in (.025,.012,.005)),4 if not a.lod else 2)
# Fine swept eyebrows sit directly on the face surface; avoid separate floating balls.
for sign in [-1,1]:
 points=[];normals=[];rings=6 if not a.lod else 2
 for j in range(rings):
  t=j/(rings-1);side=sign*(.020+.034*t);height=.090+.004*math.sin(math.pi*t)
  target=world((0,side,height));p,n,_,_=bvh.ray_cast(target+front*.35,-front,.7)
  if p is None:continue
  points.append(p+n*.001);normals.append(n)
 if len(points)>1:tube(points,normals,.0015,(.030,.015,.008),4 if not a.lod else 2)
# Keep the eye paint; raised brows and smoother skin avoid inventing a different gaze.
me=bpy.data.meshes.new('Authored swept hair and brows');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Street_head_strands_and_brows',me);bpy.context.scene.collection.objects.link(ob)
colors=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(colours):colors.data[i].color=c
for f in me.polygons:f.use_smooth=True
mat=bpy.data.materials.new('Street dark brown hair detail');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.72;bs.inputs['Metallic'].default_value=0
node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='Color';mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
# Match donor joint order to the source at graft time. Only head has a nonzero weight.
for b in arm.data.bones:ob.vertex_groups.new(name=b.name)
ob.vertex_groups['head'].add(list(range(len(verts))),1,'REPLACE');ob.parent=arm;ob.matrix_parent_inverse=Matrix.Identity(4);mod=ob.modifiers.new('Head rig','ARMATURE');mod.object=arm
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str(Path(a.out).resolve()),export_format='GLB',use_selection=True,export_yup=True,export_skins=True,export_animations=False,export_leaf_bone=False,export_influence_nb=4,export_all_influences=False,export_def_bones=False,export_image_format='JPEG')
report={'source':str(Path(a.input).resolve()),'sourceSHA256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'headVertexPatches':patches,'extraTriangles':sum(len(f.vertices)-2 for f in me.polygons),'hairClumps':count,'capReduction':{'lateral':.93,'forward':.91,'height':.92},'method':'smoothed seeded fine swept strands + head-only welded smooth normals + 4.5% lower-jaw width','noNewNeuralBatch':True,'bodyContactVerticesUntouched':True}
Path(a.out).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='headVertexPatches'}))
