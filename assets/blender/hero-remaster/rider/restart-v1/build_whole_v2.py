"""Fresh adult Street rider in Blender. Existing rider geometry is never retained.

The rig-only import preserves runtime numbers; geometry comes from a freshly
instantiated MPFB base, shaped garment topology and newly authored accessories.
This first whole-body checkpoint is explicitly unaccepted art.
"""
import bpy,bmesh,json,math,sys,argparse,hashlib,random
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--lod',action='store_true');ap.add_argument('--output');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.output or P/('whole-rider-v2-lod.glb' if a.lod else 'whole-rider-v2.glb')).resolve()
bpy.ops.wm.open_mainfile(filepath=str(P/'fresh-base.blend'))
scene=bpy.context.scene;scene.render.fps=30
base=bpy.data.objects['Fresh_adult_MakeHuman_base'];native=next(o for o in scene.objects if o.type=='ARMATURE')
# Official CC0 native eyes fit through their MakeHuman helper correspondence.
addon=Path.home()/'Library/Application Support/Blender/5.1/extensions/user_default'
repo=bpy.context.preferences.extensions.repos.new(name='Restart MPFB read-only',module='restart_mpfb',custom_directory=str(addon))
import addon_utils
addon_utils.enable('bl_ext.restart_mpfb.mpfb',default_set=True,persistent=False)
from bl_ext.restart_mpfb.mpfb.services.humanservice import HumanService
eye_dir=Path.home()/'projects/weights/makehuman/system-cc0/eyes'
eye_asset=HumanService.add_mhclo_asset(str(eye_dir/'low-poly/low-poly.mhclo'),base,asset_type='Eyes',subdiv_levels=0,material_type='NONE',set_up_rigging=False)
bpy.context.view_layer.update()
eye_mesh=eye_asset.data
eye_source={'vertices':[eye_asset.matrix_world@v.co for v in eye_mesh.vertices],'faces':[list(f.vertices) for f in eye_mesh.polygons],'uv':[tuple(d.uv) for d in eye_mesh.uv_layers.active.data]}

# Source fingers are deliberately curled before the fresh mesh is baked. All
# their weights subsequently collapse into the runtime's rigid hand bones.
for pb in native.pose.bones:
 if pb.name.startswith('finger'):
  digit,segment=pb.name.split('.')[0].replace('finger','').split('-')
  pb.rotation_mode='XYZ';pb.rotation_euler.x=(.42 if digit=='1' else .75)+(int(segment)-1)*.18
scene.frame_set(0);bpy.context.view_layer.update()
evalbase=base.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh=bpy.data.meshes.new_from_object(evalbase,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
fresh=bpy.data.objects.new('Street_restart_complete_fresh_adult',mesh);scene.collection.objects.link(fresh)
for g in base.vertex_groups:fresh.vertex_groups.new(name=g.name)
sourcecoords=[v.co.copy() for v in mesh.vertices]
sourcenormals=[v.normal.copy() for v in mesh.vertices]
sourcebones={b.name:(b.head_local.copy(),b.tail_local.copy()) for b in native.data.bones}
# Discard all MPFB helper, source rig, and all original hero meshes after import.
for o in list(scene.objects):
 if o!=fresh:bpy.data.objects.remove(o,do_unlink=True)
rigsource=P/'rig-source-decoded.glb';bpy.ops.import_scene.gltf(filepath=str(rigsource))
arm=next(o for o in scene.objects if o.type=='ARMATURE')
imported_mesh_names=[o.name for o in scene.objects if o.type=='MESH' and o!=fresh]
for o in list(scene.objects):
 if o.type=='MESH' and o!=fresh:bpy.data.objects.remove(o,do_unlink=True)
arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
R=Matrix(((0,-1,0),(-1,0,0),(0,0,1))).to_4x4()
S={
 'pelvis':(sourcebones['spine05'][0],sourcebones['spine04'][0]),
 'spine':(sourcebones['spine04'][0],sourcebones['spine02'][0]),
 'chest':(sourcebones['spine02'][0],sourcebones['neck01'][0]),
 'neck':(sourcebones['neck01'][0],sourcebones['head'][0]),
 'head':sourcebones['head'],
}
for side in ('L','R'):
 S.update({
 f'shoulder.{side}':(sourcebones[f'clavicle.{side}'][0],sourcebones[f'upperarm01.{side}'][0]),
 f'upperArm.{side}':(sourcebones[f'upperarm01.{side}'][0],sourcebones[f'lowerarm01.{side}'][0]),
 f'forearm.{side}':(sourcebones[f'lowerarm01.{side}'][0],sourcebones[f'wrist.{side}'][0]),
 f'hand.{side}':(sourcebones[f'wrist.{side}'][0],sourcebones[f'wrist.{side}'][1]),
 f'thigh.{side}':(sourcebones[f'upperleg01.{side}'][0],sourcebones[f'lowerleg01.{side}'][0]),
 f'shin.{side}':(sourcebones[f'lowerleg01.{side}'][0],sourcebones[f'foot.{side}'][0]),
 f'foot.{side}':sourcebones[f'foot.{side}'],
 })
T={}
for name,(sh,st) in S.items():
 sh,st=R@sh,R@st;b=arm.data.bones[name];dh,dt=b.head_local,b.tail_local
 sd=st-sh;dd=dt-dh
 if name.startswith('hand'):
  side=name.split('.')[-1];dd=Vector((.92,(-1 if side=='L' else 1)*.33,.78))-dh
 if name.startswith('foot'):dd=Vector((1,0,0))
 q=sd.normalized().rotation_difference(dd.normalized()).to_matrix().to_4x4()
 ratio=(dt-dh).length/sd.length if name.startswith(('upperArm','forearm','thigh','shin','spine','chest')) else (.73 if name.startswith('hand') else 1)
 axis=sd.normalized();stretch=Matrix.Identity(4)
 for i in range(3):
  for j in range(3):stretch[i][j]+=(ratio-1)*axis[i]*axis[j]
 T[name]=Matrix.Translation(dh)@q@stretch@Matrix.Translation(-sh)@R
 if name.startswith('hand'):
  # Measured v2 CPU contact residual, transformed back through the retained
  # hand bind frame: inward/back shift of the fresh palm around the bar.
  sign=-1 if name.endswith('.L') else 1
  T[name]=Matrix.Translation(Vector((-.00770,-sign*.00924,.00012)))@T[name]

def mapbone(name):
 if name not in sourcebones:return None
 side=name.split('.')[-1] if '.' in name else None
 if name=='root' or name.startswith(('pelvis','spine05')):return 'pelvis'
 if name.startswith(('spine04','spine03')):return 'spine'
 if name.startswith(('spine02','spine01','breast')):return 'chest'
 if name.startswith('neck'):return 'neck'
 if name.startswith(('clavicle','shoulder01')):return 'shoulder.'+side
 if name.startswith('upperarm'):return 'upperArm.'+side
 if name.startswith('lowerarm'):return 'forearm.'+side
 if name.startswith(('wrist','finger','metacarpal')):return 'hand.'+side
 if name.startswith('upperleg'):return 'thigh.'+side
 if name.startswith('lowerleg'):return 'shin.'+side
 if name.startswith(('foot','toe')):return 'foot.'+side
 if name in sourcebones:return 'head'
 return None
oldgroups=list(fresh.vertex_groups.keys());weights=[]
for v in mesh.vertices:
 ws={}
 for g in v.groups:
  dest=mapbone(oldgroups[g.group])
  if dest:ws[dest]=ws.get(dest,0)+g.weight
 if not ws:ws={'pelvis':1}
 ws=sorted(ws.items(),key=lambda kv:-kv[1])[:4];total=sum(w for n,w in ws);weights.append({n:w/total for n,w in ws})
fresh.vertex_groups.clear()
for name in arm.data.bones.keys():fresh.vertex_groups.new(name=name)
# Seven physical material groups: skin, cotton, denim, gloves, footwear, hair,
# and eyes. Vertex pigments carry deliberate colours without source skin maps.
colors={'skin':(.49,.265,.155,1),'cotton':(.57,.335,.065,1),'denim':(.055,.105,.18,1),'gloves':(.023,.026,.027,1),'footwear':(.041,.046,.05,1),'hair':(.032,.019,.012,1),'eyes':(.62,.60,.54,1)}
roughness={'skin':.62,'cotton':.91,'denim':.90,'gloves':.82,'footwear':.86,'hair':.85,'eyes':.27}
materials={}
for name in colors:
 m=bpy.data.materials.new('Street_restart_'+name);m.use_nodes=True;bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(1,1,1,1);bs.inputs['Roughness'].default_value=roughness[name];bs.inputs['Metallic'].default_value=0
 vc=m.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Pigment';m.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);m.diffuse_color=colors[name];materials[name]=m;mesh.materials.append(m)
matindex={k:i for i,k in enumerate(colors)}

def source_region(p,ws):
 side='L' if p.x>=0 else 'R';dom=max(ws,key=ws.get)
 if dom.startswith('hand'):return 'gloves'
 if p.z<.125:return 'footwear'
 if p.z<.89 and dom.startswith(('thigh','shin','foot','pelvis')):return 'denim'
 if dom in ('head','neck') and p.z>1.37:return 'skin'
 if dom.startswith('forearm'):
  h,t=S[dom];u=(p-h).dot(t-h)/(t-h).length_squared
  if u>.63:return 'skin'
 if dom.startswith(('upperArm','forearm','shoulder')) or dom in ('pelvis','spine','chest','neck'):return 'cotton'
 return 'skin'

regions=[]
for v,p,ws,n in zip(mesh.vertices,sourcecoords,weights,sourcenormals):
 region=source_region(p,ws);regions.append(region);dom=max(ws,key=ws.get)
 # Loose continuous cloth shell is shaped on this newly generated surface,
 # rather than primitives grafted onto the rejected body.
 if region=='cotton':
  amount=.010 if dom.startswith(('upperArm','forearm','shoulder')) else .016
  if dom.startswith('forearm'):
   h,t=S[dom];u=(p-h).dot(t-h)/(t-h).length_squared
   amount*=min(1,max(0,(.64-u)/.12))
  # Quieter chest, heavier waist drape, sleeve bunching.
  amount+=.004*math.sin(p.z*53+p.x*11)*math.exp(-((p.z-.95)/.19)**2)
  p=p+n*amount
  torso_weight=sum(ws.get(b,0) for b in ('pelvis','spine','chest'))
  if torso_weight>.35 and .90<p.z<1.35:
   # Project the new cotton shell to an intentionally quiet cloth envelope.
   # Native chest muscles are not the visible garment surface.
   u=max(0,min(1,(p.z-.90)/.45));width=.172+.023*math.sin(u*math.pi*.65)
   px=p.x*1.025;profile=math.sqrt(max(.02,1-(px/width)**2))
   py=(-.153 if p.y<0 else .108)*profile-.004
   fold=.0035*math.sin((p.z-.90)*55+p.x*9)*math.exp(-((p.z-1.0)/.13)**2)
   blend=min(1,(torso_weight-.35)/.40)
   p.x=px;p.y=p.y*(1-blend)+(py+fold)*blend
 elif region=='denim':
  amount=.015+.003*math.sin(p.z*76+p.y*18)*math.exp(-((p.z-.48)/.13)**2)
  p=p+n*amount
 elif region=='gloves':p=p+n*.0015
 elif region=='footwear':
  p=p+n*.01
 for name,w in ws.items():fresh.vertex_groups[name].add([v.index],w,'REPLACE')
 v.co=sum(((T[name]@p)*w for name,w in ws.items()),Vector((0,0,0)))
# Pigment is per corner, preserving clean material boundaries and continuous
# geometry/weights across the hands and forearms.
pigment=mesh.color_attributes.new(name='Pigment',type='FLOAT_COLOR',domain='CORNER')
for poly in mesh.polygons:
 region=max(colors,key=lambda r:(sum(regions[i]==r for i in poly.vertices),-matindex[r]));poly.material_index=matindex[region];poly.use_smooth=True
 for li in poly.loop_indices:
  p=sourcecoords[mesh.loops[li].vertex_index];col=colors[region];variation=1
  if region=='skin':
   # New restrained adult stubble pigment on native jaw; not the disputed skin.
   stubble=p.z<1.493 and p.z>1.405 and p.y<-.073 and abs(p.x)<.07
   if stubble:variation=.70+.06*math.sin(p.x*951+p.z*1283)
   elif p.y<-.115 and p.z<1.56:variation=.98
  elif region=='cotton':variation=.98+.02*math.sin(p.z*210)*math.sin(p.x*173+p.y*141)
  elif region=='denim':variation=.95+.04*math.sin(p.z*147+p.x*128)
  pigment.data[li].color=tuple(c*variation for c in col[:3])+(1,)
fresh.parent=arm;mod=fresh.modifiers.new('Exact nineteen bone runtime rig','ARMATURE');mod.object=arm

# New authored accessories in source coordinates. They use the very same
# semantic fit matrices as the fresh anatomy, never copied hero geometry.
objects=[fresh]
def accessory(name,verts,faces,region,ws,vertexcols=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);me.materials.append(materials[region]);o.parent=arm
 for bn in arm.data.bones.keys():o.vertex_groups.new(name=bn)
 for v in me.vertices:
  for bn,w in ws.items():o.vertex_groups[bn].add([v.index],w,'REPLACE')
  v.co=sum(((T[bn]@v.co.copy())*w for bn,w in ws.items()),Vector((0,0,0)))
 col=me.color_attributes.new(name='Pigment',type='FLOAT_COLOR',domain='CORNER')
 for poly in me.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices:col.data[li].color=vertexcols[me.loops[li].vertex_index] if vertexcols else colors[region]
 mod=o.modifiers.new('Runtime nineteen bone skin','ARMATURE');mod.object=arm;objects.append(o);return o

def tube(name,points,radii,region,ws,sides=8):
 vv=[];ff=[]
 for k,p in enumerate(points):
  p=Vector(p);d=Vector(points[min(k+1,len(points)-1)])-Vector(points[max(0,k-1)])
  d.normalize();u=d.cross(Vector((1,0,0)))
  if u.length<.01:u=d.cross(Vector((0,0,1)))
  u.normalize();v=d.cross(u).normalized()
  radius=radii[k] if isinstance(radii,list) else radii
  for j in range(sides):vv.append(p+(u*math.cos(j/sides*math.tau)+v*math.sin(j/sides*math.tau))*radius)
 for k in range(len(points)-1):
  for j in range(sides):ff.append((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j))
 ff.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))]);return accessory(name,vv,ff,region,ws)

# Collapsed hood: a shaped crescent loft around the back of the fresh neck.
vv=[];ff=[];N=40;M=16
for i in range(N+1):
 ang=(-.83+i/N*1.66)*math.pi;cx=.104*math.sin(ang);cy=.029+.105*math.cos(ang);cz=1.335+.043*math.cos(ang)
 for j in range(M):
  ph=j/M*math.tau;r=.023*(.6+.4*math.sin(i/N*math.pi));vv.append((cx+math.sin(ang)*r*math.cos(ph),cy+math.cos(ang)*r*math.cos(ph),cz+r*.82*math.sin(ph)))
for i in range(N):
 for j in range(M):ff.append((i*M+j,i*M+(j+1)%M,(i+1)*M+(j+1)%M,(i+1)*M+j))
ff.extend([tuple(reversed(range(M))),tuple(N*M+j for j in range(M))]);accessory('New_sewn_collapsed_hood',vv,ff,'cotton',{'chest':.93,'neck':.07})
# Double rolled cuffs follow the native forearm section and retain the complete
# forearm influence to stay attached in every runtime pose.
for side in ('L','R'):
 h,t=S['forearm.'+side];axis=(t-h).normalized();u=axis.cross(Vector((0,0,1))).normalized();v=axis.cross(u).normalized();c=h.lerp(t,.60)
 points=[c+(u*math.cos(j/48*math.tau)+v*math.sin(j/48*math.tau))*.043 for j in range(49)]
 tube('New_rolled_cuff_'+side,points,.010,'cotton',{'forearm.'+side:1},sides=8)
# Front drawcords, collar seam, and shaped kangaroo pocket on the new garment.
for side,sgn in [('L',1),('R',-1)]:
 points=[(sgn*.025,-.092,1.354),(sgn*.031,-.159,1.29),(sgn*.03,-.159,1.22),(sgn*.033,-.14,1.16)]
 tube('New_drawcord_'+side,points,.0018,'cotton',{'chest':1},sides=6)
# Hoodie's pocket patch is a curved grid surface, following the fresh abdomen.
vv=[];ff=[];rows=8;cols=20
for iy in range(rows+1):
 z=.974+iy/rows*.112
 for ix in range(cols+1):
  x=-.104+ix/cols*.208;depth=-.131-.013*(1-(x/.12)**2)-.013*math.sin(iy/rows*math.pi)
  vv.append((x,depth,z))
for iy in range(rows):
 for ix in range(cols):k=iy*(cols+1)+ix;ff.append((k,k+1,k+cols+2,k+cols+1))
accessory('New_kangaroo_pocket',vv,ff,'cotton',{'spine':.7,'chest':.3})
# Each shoe is a shaped native foot shell, with an authored flat sole rim and
# curved lace set. No old glove/boot meshes are used.
for side,sgn in [('L',1),('R',-1)]:
 ankle=S['foot.'+side][0];points=[]
 for j in range(65):
  ph=j/64*math.tau;x=ankle.x+.047*math.cos(ph);y=ankle.y-.08+.145*math.sin(ph);points.append((x,y,.015))
 tube('New_sneaker_sole_rim_'+side,points,.010,'eyes',{'foot.'+side:1},sides=8)
 for j in range(5):
  z=.072-j*.003;y=ankle.y-.045-j*.018
  tube('New_sneaker_lace_'+side+str(j),[(ankle.x-.025,y,z),(ankle.x,y-.004,z+.008),(ankle.x+.025,y,z)],.0018,'eyes',{'foot.'+side:1},sides=5)
# Native face fit: eye surfaces follow the actual fresh face instead of
# putting independent white spheres in front of the lids.
from mathutils.bvhtree import BVHTree
face_tree=BVHTree.FromPolygons(sourcecoords,[list(p.vertices) for p in mesh.polygons])
def facepoint(x,z,lift=.0005):
 hit,n,idx,d=face_tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
 if hit is None:raise RuntimeError('Eye projection misses fresh native face')
 return hit+Vector((0,-lift,0))
def eye_patch(name,cx,cz,rx,rz,col,lift):
 vv=[facepoint(cx,cz,lift)];ff=[];N=24
 for j in range(N):
  ph=j/N*math.tau;vv.append(facepoint(cx+rx*math.cos(ph),cz+rz*math.sin(ph),lift))
 for j in range(N):ff.append((0,j+1,(j+1)%N+1))
 return accessory(name,vv,ff,'eyes',{'head':1},[col]*len(vv))
native_eyes=accessory('New_native_CC0_MakeHuman_eyes',eye_source['vertices'],eye_source['faces'],'eyes',{'head':1})
uv=native_eyes.data.uv_layers.new(name=fresh.data.uv_layers.active.name)
assert len(uv.data)==len(eye_source['uv'])
for d,source_uv in zip(uv.data,eye_source['uv']):d.uv=source_uv
eye_mat=bpy.data.materials.new('Street_restart_native_eyes');eye_mat.use_nodes=True
bs=eye_mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(1,1,1,1);bs.inputs['Roughness'].default_value=.28;bs.inputs['Metallic'].default_value=0
image=bpy.data.images.load(str(eye_dir/'materials/brown_eye.png'),check_existing=True)
if max(image.size)>1024:image.scale(1024,1024)
image.pack();texture=eye_mat.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image;eye_mat.node_tree.links.new(texture.outputs['Color'],bs.inputs['Base Color'])
native_eyes.data.materials.clear();native_eyes.data.materials.append(eye_mat)
for side in ('L','R'):
 e=sourcebones['eye.'+side][0]
 points=[facepoint(e.x-.014+j/12*.028,e.z+.011+.0025*math.sin(j/12*math.pi),.0010) for j in range(13)]
 tube('New_fitted_brow_'+side,points,.0018,'hair',{'head':1},sides=6)
# Opaque newly authored curl masses follow this base's actual scalp samples.
def sph(name,center,scale,region,ws,segments=12,rings=8,color=None):
 vv=[Vector(center)+Vector((0,0,scale[2]))];ff=[]
 for k in range(1,rings):
  th=k/rings*math.pi
  for j in range(segments):
   ph=j/segments*math.tau;lobes=1+.10*math.sin(ph*3+th*5)+.06*math.cos(ph*5-th*3)
   vv.append(Vector(center)+Vector((math.sin(th)*math.cos(ph)*scale[0],math.sin(th)*math.sin(ph)*scale[1],math.cos(th)*scale[2]))*lobes)
 bottom=len(vv);vv.append(Vector(center)-Vector((0,0,scale[2])))
 for j in range(segments):ff.append((0,1+j,1+(j+1)%segments))
 for k in range(rings-2):
  for j in range(segments):ff.append((1+k*segments+j,1+k*segments+(j+1)%segments,1+(k+1)*segments+(j+1)%segments,1+(k+1)*segments+j))
 for j in range(segments):ff.append((1+(rings-2)*segments+j,bottom,1+(rings-2)*segments+(j+1)%segments))
 return accessory(name,vv,ff,region,ws,[color]*len(vv) if color else None)
# A new coherent scalp shell comes from this fresh adult base, then grouped
# opaque curl masses break its silhouette. There are no old hair donors.
rng=random.Random(214)
eye_height=sourcebones['eye.L'][0].z
scalp_ids=[i for i,p in enumerate(sourcecoords) if weights[i].get('head',0)>.9 and (p.z>eye_height+.052 or (p.y>-.10 and p.z>eye_height-.004))]
scalp_set=set(scalp_ids)
scalp_faces=[list(poly.vertices) for poly in mesh.polygons if all(i in scalp_set for i in poly.vertices)]
if scalp_faces:
 selected=sorted(set(i for f in scalp_faces for i in f));remap={old:i for i,old in enumerate(selected)}
 verts=[sourcecoords[i]+sourcenormals[i]*.004 for i in selected];faces=[tuple(remap[i] for i in f) for f in scalp_faces]
 accessory('New_fitted_opaque_scalp',verts,faces,'hair',{'head':1})
# Farthest-point placement distributes irregular curl masses over the true
# scalp, without the first shape's bead rows or ellipsoid cap.
selected=[];available=list(scalp_ids)
if available:selected=[max(available,key=lambda i:sourcecoords[i].z)]
for k in range(70):
 if not available:break
 i=max(available,key=lambda i:min((sourcecoords[i]-sourcecoords[j]).length for j in selected))
 if i in selected:break
 selected.append(i);available.remove(i)
for k,i in enumerate(selected):
 c=sourcecoords[i]+sourcenormals[i]*(.007+rng.uniform(0,.004));radius=.019+rng.uniform(-.002,.004)
 sph('New_fitted_curl_'+str(k),c,(radius,radius*1.1,radius*.85),'hair',{'head':1},segments=12,rings=8)
# Join into one mesh: a single material primitive per semantic response.
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=fresh;bpy.ops.object.join()
# Material merging after join removes duplicate slots and bounds actual draws.
used=list(dict.fromkeys(m for m in fresh.data.materials));old=list(fresh.data.materials)
material_remap=[used.index(old[poly.material_index]) for poly in fresh.data.polygons]
fresh.data.materials.clear()
for m in used:fresh.data.materials.append(m)
for poly,mi in zip(fresh.data.polygons,material_remap):poly.material_index=mi
triangles=sum(len(p.vertices)-2 for p in fresh.data.polygons)
if a.lod:
 dec=fresh.modifiers.new('Bounded phone LOD','DECIMATE');dec.ratio=min(1,7800/triangles);bpy.ops.object.modifier_apply(modifier=dec.name)
 for v in fresh.data.vertices:
  ws=sorted([(g.group,g.weight) for g in v.groups if g.weight>0],key=lambda x:-x[1])[:4];total=sum(w for g,w in ws)
  for g in list(v.groups):fresh.vertex_groups[g.group].remove([v.index])
  for g,w in ws:fresh.vertex_groups[g].add([v.index],w/total,'REPLACE')
# Save an editable source scene, then export six existing clips through the
# exact skeleton. This candidate is not automatically promoted.
for tr in arm.animation_data.nla_tracks:tr.mute=False
arm.animation_data.action=None
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
for ac in bpy.data.actions:ac.use_fake_user=True
scene.frame_set(0)
scene['restartSource']='Fresh MPFB adult base, new garment/accessory geometry; only numeric rig/clips/sockets retained'
bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix('.blend')),compress=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_yup=True,export_animations=True,export_skins=True,export_animation_mode='ACTIONS',export_nla_strips=True,export_force_sampling=True,export_anim_slide_to_zero=False,export_rest_position_armature=True,export_influence_nb=4,export_all_influences=False,export_leaf_bone=False,export_morph=False,export_extras=True,export_vertex_color='MATERIAL')
report={'status':'UNACCEPTED complete fresh Blender rider candidate; parent must judge actual Garage/ride','source':'Fresh MPFB adult base plus new authored cloth/accessories','existingMeshGeometryRetained':False,'discardedImportedMeshes':imported_mesh_names,'rigSource':str(rigsource),'rigSourceSHA256':hashlib.sha256(rigsource.read_bytes()).hexdigest(),'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'triangles':sum(len(p.vertices)-2 for p in fresh.data.polygons),'materials':list(fresh.data.materials.keys()),'materialCount':len(fresh.data.materials),'bones':list(arm.data.bones.keys()),'clips':list(bpy.data.actions.keys()),'freshBaseProof':str(P/'fresh-base-probe.json'),'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'nativeEyeSource':{'mhclo':str(eye_dir/'low-poly/low-poly.mhclo'),'mhcloSHA256':hashlib.sha256((eye_dir/'low-poly/low-poly.mhclo').read_bytes()).hexdigest(),'objSHA256':hashlib.sha256((eye_dir/'low-poly/low-poly.obj').read_bytes()).hexdigest(),'license':'CC0 official MakeHuman system pack','fittedVertices':len(eye_source['vertices'])},'limits':['Whole-body fit iteration; UV/PBR cloth bake unfinished','Skin/garment fit, contacts and LOD require moving engine review','No AAA/mockup acceptance claimed']}
out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
