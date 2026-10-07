"""First unaccepted conventional anatomical rig; never replaces player assets."""
import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
args=sys.argv[sys.argv.index('--')+1:];bundle=Path(args[0]).resolve();out=Path(args[1]).resolve();out.mkdir(parents=True,exist_ok=False)
assert hashlib.sha256(bundle.read_bytes()).hexdigest()=='3c121505651140ceb4d69fd1d8923f7788ffadd81672f5be14845a5f2c75c137'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
names=['GEO-body_male_realistic','GEO-body_male_realistic.eye.L','GEO-body_male_realistic.eye.R']
with bpy.data.libraries.load(str(bundle),link=False) as (source,destination):destination.objects=names
for obj in destination.objects:scene.collection.objects.link(obj)
body=destination.objects[0];body.name='RiderBody'
raw=[v.co.copy() for v in body.data.vertices];floor=min(v.z for v in raw);scale=1.78/(max(v.z for v in raw)-floor)
convert=lambda p:Vector((p[0]*scale,p[1]*scale,(p[2]-floor)*scale))
source_body_inverse=body.matrix_world.inverted()
for obj in destination.objects:
 source_to_body=source_body_inverse @ obj.matrix_world
 converted=[convert(source_to_body @ v.co) for v in obj.data.vertices]
 obj.matrix_world=Matrix.Identity(4)
 for v,co in zip(obj.data.vertices,converted):v.co=co
 for m in list(obj.modifiers):obj.modifiers.remove(m)
 for p in obj.data.polygons:p.use_smooth=True
body.data.update()
bpy.ops.preferences.addon_enable(module='rigify')
from rigify.metarigs import human
bpy.ops.object.armature_add();meta=bpy.context.object;meta.name='RiderMetarig'
bpy.ops.object.mode_set(mode='EDIT')
for b in list(meta.data.edit_bones):meta.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT');human.create(meta)
edit=meta.data.edit_bones
face=edit.get('face');remove=[b.name for b in edit if b==face or face in b.parent_recursive]
for name in remove+['breast.L','breast.R']:edit.remove(edit[name])
# Body-joint proposals explicitly calibrated against selected source anatomy.
# Native axes stay X-lateral / -Y-forward / Z-up; named L is source +X.
spine=[(0,-.018,.90),(0,-.027,1.025),(0,-.025,1.16),(0,-.014,1.30),(0,-.004,1.395),(0,-.008,1.435),(0,-.011,1.475),(0,-.01,1.645)]
for i in range(7):
 b=edit['spine' if i==0 else 'spine.%03d'%i];b.head=convert(spine[i]);b.tail=convert(spine[i+1]);b.align_roll(Vector((0,1,0)))
for side,sign in [('L',1),('R',-1)]:
 def p(x,y,z):return (sign*x,y,z)
 points={'hip':p(.095,-.018,.875),'knee':p(.128,.004,.51),'ankle':p(.1694,.05835,.12),'ball':p(.23,-.065,.025),'toe':p(.235,-.127,.012),'shoulder':p(.194,.01,1.315),'elbow':p(.30865,-.00875,1.06),'wrist':p(.37027,-.05504,.90),'palm':p(.405,-.10,.82)}
 def bone(name,a,b,roll=(0,-1,0)):
  item=edit[name+'.'+side];item.head=convert(a);item.tail=convert(b);item.align_roll(Vector(roll))
 bone('pelvis',spine[0],p(.11,-.05,.96))
 bone('shoulder',p(.025,-.015,1.345),points['shoulder'])
 bone('upper_arm',points['shoulder'],points['elbow'],(0,-1,0))
 bone('forearm',points['elbow'],points['wrist'],(0,-1,0))
 bone('hand',points['wrist'],points['palm'],(-sign,0,0))
 bone('thigh',points['hip'],points['knee']);bone('shin',points['knee'],points['ankle'])
 bone('foot',points['ankle'],points['ball']);bone('toe',points['ball'],points['toe'])
 heel=edit['heel.02.'+side];heel.head=convert(p(.13,.085,0));heel.tail=convert(p(.20,.085,0))
 # MCP/PIP/DIP proposals follow measured five-digit source regions, unequal lengths.
 # Exact source IDs and final joints/inside-surface diagnostics are emitted below.
 digit_points={
  'f_index':[(.397,-.126,.825),(.413,-.151,.780),(.418,-.163,.754),(.4183,-.1643,.744)],
  'f_middle':[(.412,-.103,.823),(.427,-.130,.777),(.432,-.140,.739),(.4313,-.140,.721)],
  'f_ring':[(.411,-.078,.817),(.423,-.099,.772),(.429,-.108,.739),(.428,-.109,.719)],
  'f_pinky':[(.405,-.052,.807),(.417,-.062,.776),(.425,-.065,.745),(.425,-.064,.727)],
  'thumb':[(.359,-.103,.862),(.361,-.144,.834),(.369,-.169,.817),(.369,-.174,.808)]}
 for finger,rows in digit_points.items():
  for i in range(3):bone(finger+'.%02d'%(i+1),p(*rows[i]),p(*rows[i+1]),(-sign,0,0))
 for i,finger in enumerate(['f_index','f_middle','f_ring','f_pinky'],1):
  root=digit_points[finger][0];bone('palm.%02d'%i,p(.382,-.075,.868),p(*root),(-sign,0,0))
 # Match rigify connected endpoints after anatomical placement; roll remains explicit.
 for b in edit:
  if b.use_connect and b.parent:b.head=b.parent.tail
bpy.ops.object.mode_set(mode='OBJECT')
for side in ['L','R']:
 for stem in ['upper_arm','thigh']:
  par=meta.pose.bones[stem+'.'+side].rigify_parameters;par.segments=2;par.bbones=1
 for stem in ['f_index','f_middle','f_ring','f_pinky','thumb']:meta.pose.bones[stem+'.01.'+side].rigify_parameters.bbones=1
# Keep unaccepted inside-surface evidence. Near-joint distances are diagnostics,
# not anatomical approval; field and moving review must qualify this fit.
bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons],all_triangles=False)
inside=[]
for b in meta.data.bones:
 for endpoint,point in [('head',b.head_local),('tail',b.tail_local)]:
  near,normal,index,distance=bvh.find_nearest(point)
  inside.append({'bone':b.name,'endpoint':endpoint,'point':list(point),'nearestFace':index,'distanceMetres':distance,'signedNearestMetres':(point-near).dot(normal)})
(out/'metarig-fit.json').write_text(json.dumps({'accepted':False,'sourceNativeSHA256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'sourceScale':scale,'sourceFloor':floor,'nativeFrame':'X lateral named-left, -Y forward, Z up; gallery translation removed once','heightMetres':1.78,'bones':[{ 'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrixLocal':[list(r) for r in b.matrix_local]} for b in meta.data.bones],'insideSurfaceDiagnostics':inside,'limits':['Joint placements provisional, not certified anatomical centers.','Nearest signed distance is a diagnostic; no movement/art/contact acceptance.']},indent=2)+'\n')
bpy.context.view_layer.objects.active=meta;meta.select_set(True)
bpy.ops.pose.rigify_generate();rig=bpy.context.object;rig.name='RiderAuthorRig'
for b in rig.data.bones:
 if b.use_deform:b.bbone_segments=1
for pb in rig.pose.bones:
 if 'IK_Stretch' in pb:pb['IK_Stretch']=0.0
# Conventional automatic bind is a first field candidate, then explicit FOUR.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
arm=next(m for m in body.modifiers if m.type=='ARMATURE');arm.use_deform_preserve_volume=False
full=[];four=[];used={};deform={b.name for b in rig.data.bones if b.use_deform};group_by_index={g.index:g.name for g in body.vertex_groups}
for v in body.data.vertices:
 rows=sorted([(group_by_index[g.group],g.weight) for g in v.groups if group_by_index[g.group] in deform and g.weight>0],key=lambda r:(-r[1],r[0]))
 full.append(rows);top=rows[:4];total=sum(w for _,w in top)
 assert total>1e-12,('Unweighted body vertex',v.index)
 normalized=[(n,w/total) for n,w in top];four.append(normalized)
 for n,w in normalized:used[n]=used.get(n,0)+1
for g in body.vertex_groups:g.remove(list(range(len(body.data.vertices))))
for i,rows in enumerate(four):
 for name,w in rows:body.vertex_groups[name].add([i],w,'REPLACE')
tri=body.modifiers.new('FrozenRestTriangles','TRIANGULATE');tri.quad_method='FIXED';tri.ngon_method='BEAUTY'
bpy.context.view_layer.objects.active=body
while body.modifiers.find(tri.name)>body.modifiers.find(arm.name):bpy.ops.object.modifier_move_up(modifier=tri.name)
meta.hide_render=True;meta.hide_set(True)
for obj in destination.objects[1:]:
 group=obj.vertex_groups.new(name='DEF-spine.006');group.add(list(range(len(obj.data.vertices))),1,'REPLACE');obj.parent=rig;m=obj.modifiers.new('AnatomicalEyes','ARMATURE');m.object=rig
# Retain visible material defaults, to be replaced by full dressed construction next.
def material(name,color,roughness):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness;return m
body.data.materials.clear();body.data.materials.append(material('TemporarySkin',(.46,.285,.20),.65))
for obj in destination.objects[1:]:
 obj.data.materials.clear();obj.data.materials.append(material('TemporaryEye',(.56,.55,.51),.25))
(out/'weights-full.json').write_text(json.dumps(full)+'\n');(out/'weights-four.json').write_text(json.dumps(four)+'\n')
report={'accepted':False,'kind':'unaccepted conventional rig construction','source':str(bundle),'heightMetres':1.78,'metarigBoneCount':len(meta.data.bones),'authorRigBoneCount':len(rig.data.bones),'deformBones':[b.name for b in rig.data.bones if b.use_deform],'weightedDeformVertexCounts':used,'bodyVertices':len(body.data.vertices),'fourSlotMaximum':max(map(len,four)),'maxRemovedFullMass':max(sum(w for _,w in rows[4:]) for rows in full),'allDeformBBoneSegmentsOne':all(b.bbone_segments==1 for b in rig.data.bones if b.use_deform),'limits':['Provisional joint fit and first automatic/FOUR field; no moving, clothed, engine or art acceptance.']}
(out/'joint-rest.json').write_text(json.dumps({'frame':'native-X-left-negative-Y-front-Z-up','units':'metres','sourceScale':scale,'sourceFloor':floor,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'deform':b.use_deform,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones]},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'anatomical-rig.blend'))
report['nativeSHA256']=hashlib.sha256((out/'anatomical-rig.blend').read_bytes()).hexdigest();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
