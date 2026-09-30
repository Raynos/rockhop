"""Fit a closed neural A-pose body to the existing 19-bone runtime rig.

Blender headless --python fit_rider.py -- --input raw/MODEL/street-apose.glb
The authored rest rig, socket nodes and six existing clips survive unchanged.
Skin/pose fitting is a candidate, requiring moving contact and anatomy review.
"""
import bpy,bmesh,sys,json,math,argparse,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',default=str(P/'candidate.glb'));ap.add_argument('--lod',action='store_true');ap.add_argument('--contacts',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'work/baseline.glb'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
for o in list(bpy.data.objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
original=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(Path(a.input).resolve()))
new=set(bpy.data.objects)-original
mesh=next(o for o in new if o.type=='MESH')
verts=[mesh.matrix_world@v.co for v in mesh.data.vertices]
lo=Vector([min(v[i] for v in verts) for i in range(3)]);hi=Vector([max(v[i] for v in verts) for i in range(3)])
scale=1.75/(hi.z-lo.z)
# Imported glTF front +Z is Blender -Y; game front is Blender +X.
centre=(lo+hi)*.5
for v,p in zip(mesh.data.vertices,verts):v.co=Vector((-(p.y-centre.y)*scale,(p.x-centre.x)*scale,(p.z-lo.z)*scale))
mesh.matrix_world=Matrix.Identity(4);mesh.parent=None
for o in new:
 if o!=mesh:bpy.data.objects.remove(o,do_unlink=True)
mesh.name='Street_remaster_neural_full_body'
# Recipe landmarks measured from the clean generated A-pose reference.
S={
 'pelvis':((0,0,.91),(0,0,1.00)),
 'spine':((0,0,1.00),(0,0,1.19)),
 'chest':((0,0,1.19),(0,0,1.40)),
 'neck':((0,0,1.40),(0,0,1.52)),
 'head':((0,0,1.52),(0,0,1.68)),
}
for side,sgn in [('L',-1),('R',1)]:
 S.update({
 f'shoulder.{side}':((0,sgn*.04,1.39),(0,sgn*.20,1.39)),
 f'upperArm.{side}':((0,sgn*.20,1.39),(0,sgn*.36,1.17)),
 f'forearm.{side}':((0,sgn*.36,1.17),(0,sgn*.49,1.00)),
 f'hand.{side}':((0,sgn*.49,1.00),(0,sgn*.56,.86)),
 f'thigh.{side}':((0,sgn*.09,.91),(0,sgn*.13,.50)),
 f'shin.{side}':((0,sgn*.13,.50),(0,sgn*.17,.12)),
 f'foot.{side}':((0,sgn*.17,.12),(.16,sgn*.17,.065)),
 })
S={name:(Vector(h),Vector(t)) for name,(h,t) in S.items()}
transforms={}
for name,(h,t) in S.items():
 b=arm.data.bones[name]
 direction=b.tail_local-b.head_local
 rotation=direction.normalized().rotation_difference((t-h).normalized()).to_matrix().to_4x4()
 src=Matrix.Translation(h)@rotation@b.matrix_local.to_3x3().to_4x4()
 # Upper/lower limbs fit endpoint lengths; heads, gloves and shoes keep shape.
 ratio=direction.length/(t-h).length if name.startswith(('upperArm','forearm','thigh','shin')) else 1
 transforms[name]=b.matrix_local@Matrix.Diagonal((1,ratio,1,1))@src.inverted()
 mesh.vertex_groups.new(name=name)
def segment_distance(p,h,t):
 d=t-h;u=max(0,min(1,(p-h).dot(d)/d.length_squared));return (p-h-d*u).length
if a.contacts:
 bm=bmesh.new();bm.from_mesh(mesh.data)
 def crop(p):
  if p.z<.135:return True
  if abs(p.y)<.28 or p.z<.74:return False
  side='L' if p.y<0 else 'R';w,t=S[f'hand.{side}'];d=(t-w).normalized()
  return (p-w).dot(d)>.003
 drop=[f for f in bm.faces if crop(f.calc_center_median())]
 bmesh.ops.delete(bm,geom=drop,context='FACES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 bm.to_mesh(mesh.data);bm.free()
allweights=[]
for v in mesh.data.vertices:
 p=v.co.copy();side='L' if p.y<0 else 'R'
 if p.z>1.54 and abs(p.y)<.23:names=['head']
 elif abs(p.y)>.28 and p.z>.74:names=[f'{n}.{side}' for n in ['upperArm','forearm','hand']]
 elif p.z<.16:names=[f'foot.{side}',f'shin.{side}']
 elif p.z<.88:names=[f'thigh.{side}',f'shin.{side}',f'foot.{side}','pelvis']
 elif abs(p.y)>.25 and p.z>.86:names=[f'{n}.{side}' for n in ['upperArm','forearm','hand']]
 elif abs(p.y)>.16 and p.z>1.15:names=['chest',f'shoulder.{side}',f'upperArm.{side}']
 else:names=['pelvis','spine','chest','neck','head']
 ranked=sorted([(name,segment_distance(p,*S[name])) for name in names],key=lambda x:x[1])[:3]
 weights=[(name,1/(dist+.035)**6) for name,dist in ranked];total=sum(w for _,w in weights)
 weights=[(name,w/total) for name,w in weights if w/total>.005];total=sum(w for _,w in weights)
 weights=[(name,w/total) for name,w in weights]
 fitted=Vector((0,0,0))
 for name,w in weights:
  fitted+=(transforms[name]@p)*w;mesh.vertex_groups[name].add([v.index],w,'REPLACE')
 v.co=fitted;allweights.append(weights)
for f in mesh.data.polygons:f.use_smooth=True
mesh.parent=arm;mesh.matrix_parent_inverse=Matrix.Identity(4)
mod=mesh.modifiers.new('Runtime nineteen bone rig','ARMATURE');mod.object=arm
# All generated material is dielectric apparel/skin; never accept glTF default metallic=1.
for mat in mesh.data.materials:
 if mat and mat.use_nodes:
  for node in mat.node_tree.nodes:
   if node.type=='BSDF_PRINCIPLED':
    node.inputs['Metallic'].default_value=0
    if not node.inputs['Roughness'].is_linked:node.inputs['Roughness'].default_value=.72
contact=None
if a.contacts:
 with bpy.data.libraries.load(str(P/'work/authored-contacts.blend'),link=False) as (src,dst):dst.objects=['Authored_grips_and_soles']
 contact=dst.objects[0];scene.collection.objects.link(contact);contact.parent=arm;contact.matrix_parent_inverse=Matrix.Identity(4)
 cm=contact.modifiers.new('Unchanged runtime contact skin','ARMATURE');cm.object=arm
 # Blend the generated garment boundary into the retained contact shells.
 from mathutils.kdtree import KDTree
 kd=KDTree(len(contact.data.vertices))
 for v in contact.data.vertices:kd.insert(v.co,v.index)
 kd.balance()
 bm=bmesh.new();bm.from_mesh(mesh.data);boundary=set(v.index for e in bm.edges if len(e.link_faces)==1 for v in e.verts);bm.free()
 for i in boundary:
  v=mesh.data.vertices[i];co,idx,dist=kd.find(v.co)
  if dist<.085:
   v.co=co.copy()
   for g in list(v.groups):mesh.vertex_groups[g.group].remove([v.index])
   cv=contact.data.vertices[idx]
   for g in cv.groups:mesh.vertex_groups[contact.vertex_groups[g.group].name].add([v.index],g.weight,'REPLACE')
before=sum(len(p.vertices)-2 for p in mesh.data.polygons)
contact_tris=sum(len(p.vertices)-2 for p in contact.data.polygons) if contact else 0
if before+contact_tris>60000 and not a.lod:
 bpy.context.view_layer.objects.active=mesh;mesh.select_set(True)
 dec=mesh.modifiers.new('Whole rider sixty thousand budget','DECIMATE');dec.ratio=(59900-contact_tris)/before
 bpy.ops.object.modifier_apply(modifier=dec.name)
 before=sum(len(p.vertices)-2 for p in mesh.data.polygons)
if a.lod:
 bpy.context.view_layer.objects.active=mesh;mesh.select_set(True)
 dec=mesh.modifiers.new('Phone eight thousand triangles','DECIMATE');dec.ratio=(7900-(min(contact_tris,1600) if contact else 0))/before
 bpy.ops.object.modifier_apply(modifier=dec.name)
 # The simplified mesh keeps at most four influences with normalized weights.
 for v in mesh.data.vertices:
  ws=sorted([(g.group,g.weight) for g in v.groups if g.weight>0],key=lambda x:-x[1])[:4];s=sum(w for _,w in ws)
  for g in list(v.groups):mesh.vertex_groups[g.group].remove([v.index])
  for g,w in ws:mesh.vertex_groups[g].add([v.index],w/s,'REPLACE')
 if contact and contact_tris>1600:
  bpy.context.view_layer.objects.active=contact
  dec=contact.modifiers.new('Preserve weighted contact silhouette in LOD','DECIMATE');dec.ratio=1600/contact_tris
  bpy.ops.object.modifier_apply(modifier=dec.name)
 for img in bpy.data.images:
  if img.size[0]>1024 or img.size[1]>1024:img.scale(1024,1024)
# Restore muted tracks for export; exporter samples original retained actions.
for tr in arm.animation_data.nla_tracks:tr.mute=False
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
arm.animation_data.action=None
for ac in bpy.data.actions:ac.use_fake_user=True
scene.frame_set(0)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()),export_format='GLB',export_image_format='JPEG',export_jpeg_quality=95,export_yup=True,export_animations=True,export_skins=True,export_animation_mode='ACTIONS',export_nla_strips=True,export_force_sampling=True,export_anim_slide_to_zero=False,export_rest_position_armature=True,export_influence_nb=4,export_all_influences=False,export_leaf_bone=False,export_morph=False,export_extras=True)
bl=Path(a.output).with_suffix('.blend');bpy.ops.wm.save_as_mainfile(filepath=str(bl),compress=True)
report={'input':str(Path(a.input).resolve()),'inputSHA256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'output':str(Path(a.output).resolve()),'sha256':hashlib.sha256(Path(a.output).read_bytes()).hexdigest(),'bytes':Path(a.output).stat().st_size,'sourceHeightNormalizedMetres':1.75,'triangles':sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'materials':len(mesh.data.materials)+(len(contact.data.materials) if contact else 0),'authoredContacts':a.contacts,'bones':sorted(arm.data.bones.keys()),'clips':sorted(ac.name for ac in bpy.data.actions),'sourceBounds':[list(lo),list(hi)],'landmarks':{n:[list(h),list(t)] for n,(h,t) in S.items()},'candidateStatus':'requires moving anatomy and contact inspection; manually fitted skinning is not an acceptance claim'}
Path(a.output).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
