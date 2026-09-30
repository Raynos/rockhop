"""Bounded head-only adult facial rebuild over V6. Blender's donor is grafted
into the immutable source skin/animation; no torso, wrist or contact edits.
"""
import bpy,sys,argparse,json,math,hashlib,random
from pathlib import Path
from mathutils import Vector,Matrix
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(a.input).resolve()))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
body=bpy.data.objects['Street_remaster_neural_full_body'];bone=arm.data.bones['head'];origin=bone.head_local;up=(bone.tail_local-bone.head_local).normalized();right=Vector((0,1,0));front=right.cross(up).normalized()
def loc(p):
 d=p-origin;return Vector((d.dot(front),d.dot(right),d.dot(up)))
def world(p):return origin+front*p[0]+right*p[1]+up*p[2]
def gltf(p):return [p.x,p.z,-p.y]
# Only triangles fully driven by head above the retained neck band are replaced.
space=[loc(v.co) for v in body.data.vertices];head=[sum(g.weight for g in v.groups if body.vertex_groups[g.group].name=='head')>.95 and space[v.index].z>.048 for v in body.data.vertices]
remove=[f.index for f in body.data.polygons if all(head[i] for i in f.vertices)]
keep=[f for f in body.data.polygons if f.index not in set(remove)]
# Existing outer boundary stays as a neck overlap band. A 6 mm overlap prevents
# new head attachment opening; it shares 100% head weights with that band.
verts=[];faces=[];colors=[]
def vertex(p,c):
 verts.append(tuple(world(p)));colors.append(tuple(c)+(1,));return len(verts)-1
def gauss(v,c,s):return math.exp(-.5*((v-c)/s)**2)
profile=[(.041,.044,.084,-.064),(.053,.066,.100,-.079),(.065,.077,.099,-.090),(.080,.083,.088,-.100),(.098,.086,.082,-.103),(.115,.086,.079,-.104),(.138,.084,.073,-.103),(.160,.080,.059,-.099),(.185,.070,.041,-.090),(.207,.049,.015,-.067),(.223,.009,-.020,-.031)]
def interp(z,k):
 for p,q in zip(profile,profile[1:]):
  if z<=q[0]:t=max(0,(z-p[0])/(q[0]-p[0]));return p[k]*(1-t)+q[k]*t
 return profile[-1][k]
def surface(theta,z):
 co=math.cos(theta);si=math.sin(theta);width=interp(z,1);xf=interp(z,2);xb=interp(z,3);x=(xf+xb)*.5+(xf-xb)*.5*co;y=width*si
 frontness=max(0,co)**10
 # Continuous nose ridge/tip, brow shelf, malar cheek planes, eye sockets,
 # lip volumes, philtrum and chin are part of the skin surface itself.
 x+=frontness*(.030*gauss(z,.094,.012)*gauss(y,0,.014)+.012*gauss(z,.116,.019)*gauss(y,0,.010))
 x+=frontness*(.008*gauss(z,.112,.006)*(gauss(y,.034,.019)+gauss(y,-.034,.019))-.009*gauss(z,.101,.0048)*(gauss(y,.034,.013)+gauss(y,-.034,.013)))
 x+=frontness*.009*gauss(z,.087,.010)*(gauss(y,.047,.021)+gauss(y,-.047,.021))
 x+=frontness*(.006*gauss(z,.069,.0025)+.006*gauss(z,.064,.0028)-.0035*gauss(z,.0668,.0009))*gauss(y,0,.030)
 x+=frontness*.010*gauss(z,.053,.009)*gauss(y,0,.040)
 shade=1-.08*gauss(z,.077,.029)*max(0,abs(y)/.08)
 c=[.57*shade,.35*shade,.24*shade]
 # Beard/stubble follows lower facial planes, without a separate shell.
 stubble=frontness*max(0,1-z/.092)*2.5*max(0,min(1,(z-.045)/.014))
 c=[v*(1-.36*stubble) for v in c]
 lip=frontness*gauss(y,0,.028)*gauss(z,.0665,.0035)
 c=[c[0]*(1-.1*lip),c[1]*(1-.20*lip),c[2]*(1-.12*lip)]
 mouth=frontness*gauss(y,0,.025)*gauss(z,.0668,.0009)
 c=[v*(1-.65*mouth)for v in c]
 brow=frontness*gauss(z,.112,.0019)*(gauss(y,.034,.017)+gauss(y,-.034,.017))
 c=[v*(1-.65*min(1,brow))for v in c]
 return (x,y,z),c
# Concentrate facial vertical samples on lids/nose/lips instead of uniform rings.
levels=[.041,.048,.053,.059,.062,.064,.0668,.069,.072,.079,.087,.092,.097,.101,.105,.108,.112,.116,.123,.135,.150,.166,.182,.197,.210,.220,.223]
if a.lod:levels=[.041,.053,.064,.0668,.072,.087,.097,.101,.108,.116,.135,.160,.185,.207,.223]
segments=56 if not a.lod else 22
for z in levels:
 for j in range(segments):p,c=surface(j*math.tau/segments,z);vertex(p,c)
for r in range(len(levels)-1):
 for j in range(segments):
  k=(j+1)%segments;x=r*segments+j;y=r*segments+k;faces.extend([(x,y,y+segments),(x,y+segments,x+segments)])
faces.append(tuple(range((len(levels)-1)*segments,len(levels)*segments)))
# Recessed almond eye surfaces and integrated skin lids. Eye aperture is only
# 23 mm wide and 6 mm high: small adult eyes rather than eyeball accessories.
for side in [-1,1]:
 cy=side*.034;cz=.101
 rings=10 if not a.lod else 6
 center=vertex((.080,cy,cz),(.035,.029,.019));perimeter=[]
 for j in range(rings):
  t=j*math.tau/rings;yy=cy+math.cos(t)*.012;zz=cz+math.sin(t)*.0028;p,_=surface(math.asin(yy/interp(zz,1)),zz);xx=p[0]+.0018
  perimeter.append(vertex((xx,yy,zz),(.43,.41,.36)))
 for j in range(rings):faces.append((center,perimeter[j],perimeter[(j+1)%rings]))
 # Small iris with muted sclera and no separate spherical eyeball.
 iris=[]
 for j in range(rings):t=j*math.tau/rings;iris.append(vertex((.0845,cy+math.cos(t)*.0025,cz+math.sin(t)*.0026),(.045,.030,.014)))
 c=vertex((.0848,cy,cz),(.008,.007,.006))
 for j in range(rings):faces.append((c,iris[j],iris[(j+1)%rings]))
# Low opaque sculpted ear relief occupies the same adult side profile.
def ellipsoid(center,scale,color,rows=4,cols=8,rotation=0):
 start=len(verts)
 for r in range(rows+1):
  ph=math.pi*r/rows
  for j in range(cols):
   th=math.tau*j/cols;d=(scale[0]*math.sin(ph)*math.cos(th),scale[1]*math.sin(ph)*math.sin(th),scale[2]*math.cos(ph))
   vertex(tuple(center[k]+d[k] for k in range(3)),tuple(c*(.91+.09*math.cos(th))for c in color))
 for r in range(rows):
  for j in range(cols):
   k=(j+1)%cols;x=start+r*cols+j;y=start+r*cols+k
   if r>0:faces.append((x,y,x+cols))
   if r<rows-1:faces.append((y,y+cols,x+cols))
for side in [-1,1]:ellipsoid((-.004,side*.086,.104),(.015,.008,.026),(.48,.275,.185),3 if a.lod else 6,5 if a.lod else 10)
# Compact closed curl masses overlap a fitted scalp cap. No sparse tube hairs.
# Same seeded silhouette at both detail tiers, with larger LOD clumps.
start=len(verts);hairlevels=[.130,.154,.181,.205,.226,.234];hs=12 if a.lod else 32
for r,z in enumerate(hairlevels):
 for j in range(hs):
  theta=j*math.tau/hs;p,_=surface(theta,min(z,.223));p=list(p)
  if r==0:p[2]=.130+.018*max(0,math.cos(theta))+.007*math.sin(theta*3)
  p[0]-=.008;p[1]*=1.04;p[2]+=.004
  vertex(p,(.034,.018,.010))
for r in range(len(hairlevels)-1):
 for j in range(hs):k=(j+1)%hs;x=start+r*hs+j;y=start+r*hs+k;faces.extend([(x,y,y+hs),(x,y+hs,x+hs)])
faces.append(tuple(range(start+(len(hairlevels)-1)*hs,start+len(hairlevels)*hs)))
rng=random.Random(43009)
for i in range(8 if a.lod else 28):
 theta=i*2.399963;z=.156+(i%5)*.014;p,_=surface(theta,min(z,.216));p=list(p);p[0]-=.006;p[1]*=1.03;p[2]+=.010
 ellipsoid(tuple(p),(.023,.020,.018),(.042+rng.random()*.007,.021,.011),2 if a.lod else 4,5 if a.lod else 8)
me=bpy.data.meshes.new('Authored adult face and closed curls');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Street_face_v7',me);bpy.context.scene.collection.objects.link(ob)
color=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(colors):color.data[i].color=c
for f in me.polygons:f.use_smooth=True
mat=bpy.data.materials.new('Street adult skin hair and facial detail');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.65;bs.inputs['Metallic'].default_value=0;n=mat.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name='Color';mat.node_tree.links.new(n.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
for b in arm.data.bones:ob.vertex_groups.new(name=b.name)
ob.vertex_groups['head'].add(list(range(len(verts))),1,'REPLACE');ob.parent=arm;ob.matrix_parent_inverse=Matrix.Identity(4);mod=ob.modifiers.new('Immutable head rig','ARMATURE');mod.object=arm
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str(Path(a.out).resolve()),export_format='GLB',use_selection=True,export_yup=True,export_skins=True,export_animations=False,export_leaf_bone=False,export_influence_nb=4,export_all_influences=False,export_def_bones=False)
# Graft identifies original removed triangles by original glTF coordinate keys,
# independently of Blender's UV split vertex ordering.
triangles=[]
for f in body.data.polygons:
 if f.index in set(remove):triangles.append([gltf(body.data.vertices[i].co)for i in f.vertices])
report={'source':a.input,'sourceSHA256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'removedHeadTriangles':triangles,'removedHeadTriangleCount':len(triangles),'removedOldHairNode':'Street_head_strands_and_brows','newTriangles':sum(len(f.vertices)-2 for f in me.polygons),'newVertices':len(verts),'lod':a.lod,'method':'adult anatomical facial surface with continuous nose brow sockets lips jaw; recessed almond eyes; low ear relief; closed scalp and overlapping curl masses','retainedNeckBandMetres':.048,'outsideHeadByteChanges':0}
Path(a.out).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='removedHeadTriangles'}))
