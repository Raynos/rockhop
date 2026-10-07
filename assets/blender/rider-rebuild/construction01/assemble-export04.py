"""Assemble one unaccepted dressed rider; conventional linear deformation export."""
import bpy,json,sys,math,hashlib,runpy,struct
from pathlib import Path
from mathutils import Vector,Matrix
args=sys.argv[sys.argv.index('--')+1:]
native=Path(args[0]).resolve();out=Path(args[1]).resolve();wardrobe=Path(args[2]).resolve() if len(args)>2 else None
out.mkdir(parents=True,exist_ok=False)
(out/'input-receipt.json').write_text(json.dumps({'accepted':False,'inputs':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [Path(__file__).resolve(),native]+([wardrobe] if wardrobe else [])]},indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(native))
body=bpy.data.objects['RiderBody'];author=bpy.data.objects['RiderAuthorRig'];scene=bpy.context.scene
for obj in scene.objects:
 if obj.type=='MESH' and '.eye.' in obj.name:
  bounds=[[min(v.co[k] for v in obj.data.vertices),max(v.co[k] for v in obj.data.vertices)] for k in range(3)]
  assert max(abs(x) for x in bounds[0])<.08 and bounds[2][0]>1.55 and bounds[2][1]<1.75,('Source eyes outside actual face region',obj.name,bounds)
fit=json.loads((native.parent/'metarig-fit.json').read_text());scale=fit['sourceScale'];floor=fit['sourceFloor']
convert=lambda p:Vector((p[0]*scale,p[1]*scale,(p[2]-floor)*scale))
# Explicit deform hierarchy replaces Rigify ORG bridges for direct runtime control.
bpy.ops.object.select_all(action='DESELECT');bpy.ops.object.armature_add();rig=bpy.context.object;rig.name='RiderSkeleton';rig.data.name='RiderSkeleton'
bpy.ops.object.mode_set(mode='EDIT');ed=rig.data.edit_bones
for b in list(ed):ed.remove(b)
source_bones=[b for b in author.data.bones if b.use_deform]
parents={}
for b in source_bones:
 n=ed.new(b.name);n.head=b.head_local;n.tail=b.tail_local;n.matrix=b.matrix_local;n.use_deform=True;n.bbone_segments=1
 parents[b.name]=b.parent.name if b.parent and b.parent.use_deform else None
parents['DEF-spine']=None
for s in ['L','R']:
 parents['DEF-pelvis.'+s]='DEF-spine';parents['DEF-thigh.'+s]='DEF-spine'
 parents['DEF-shoulder.'+s]='DEF-spine.003';parents['DEF-upper_arm.'+s]='DEF-shoulder.'+s
 for i,f in enumerate(['f_index','f_middle','f_ring','f_pinky'],1):
  parents['DEF-palm.%02d.'%i+s]='DEF-hand.'+s;parents['DEF-'+f+'.01.'+s]='DEF-palm.%02d.'%i+s
 parents['DEF-thumb.01.'+s]='DEF-hand.'+s
for name,parent in parents.items():
 if parent:ed[name].parent=ed[parent]
for s,sign in [('L',1),('R',-1)]:
 palm=ed.new('PalmSocket.'+s);palm.head=convert((sign*.396,-.086,.844));palm.tail=palm.head+Vector((-sign*.03,0,0));palm.parent=ed['DEF-hand.'+s];palm.use_deform=True
 sole=ed.new('SoleSocket.'+s);sole.head=convert((sign*.211,-.025,.001));sole.tail=sole.head+Vector((0,0,.03));sole.parent=ed['DEF-foot.'+s];sole.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
# The native author rig remains inspectable; export skeleton is constraint-free.
for obj in list(scene.objects):
 if obj.type=='MESH' and any(m.type=='ARMATURE' and m.object==author for m in obj.modifiers):
  obj.parent=rig
  for m in obj.modifiers:
   if m.type=='ARMATURE':m.object=rig;m.use_deform_preserve_volume=False
# Appearance: ordinary glTF materials and scalp following the exact continuous head.
def mat(name,color,rough=.7):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
skin=mat('RiderWarmSkin',(.245,.105,.055),.72);body.data.materials.clear();body.data.materials.append(skin)
sclera=mat('EyeIvory',(.72,.70,.65),.28);iris=mat('EyeBrown',(.055,.031,.016),.34);pupil=mat('EyePupil',(.006,.008,.007),.2)
for obj in scene.objects:
 if obj.type=='MESH' and '.eye.' in obj.name:
  obj.data.materials.clear()
  for m in [sclera,iris,pupil]:obj.data.materials.append(m)
  center=sum((v.co for v in obj.data.vertices),Vector())/len(obj.data.vertices)
  for p in obj.data.polygons:
   c=sum((obj.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices);d=c-center;r=math.hypot(d.x,d.z)
   p.material_index=2 if d.y<-.006 and r<.0035 else 1 if d.y<-.006 and r<.0065 else 0
# Scalp vertices are offset2mm from exact source; no floating independent head shell.
def hair_distance(point):
 p=point/scale;z=p.z+floor
 t=max(0,min(1,(p.y+.075)/.13));smooth=t*t*(3-2*t)
 return z-(1.632-.088*smooth)
hair_points=[];hair_faces=[];hair_lookup={}
def hair_vertex(co,normal):
 pos=co+normal.normalized()*.0015;key=tuple(round(v,7) for v in pos)
 if key not in hair_lookup:hair_lookup[key]=len(hair_points);hair_points.append(pos)
 return hair_lookup[key]
for p in body.data.polygons:
 rows=[(body.data.vertices[i].co.copy(),body.data.vertices[i].normal.copy()) for i in p.vertices]
 clipped=[]
 for a,b in zip(rows,rows[1:]+rows[:1]):
  da,db=hair_distance(a[0]),hair_distance(b[0])
  if da>=0:clipped.append(a)
  if (da>=0)!=(db>=0):
   t=da/(da-db);clipped.append((a[0].lerp(b[0],t),a[1].lerp(b[1],t)))
 if len(clipped)>=3:hair_faces.append([hair_vertex(*r) for r in clipped])
mesh=bpy.data.meshes.new('BuzzcutMesh');mesh.from_pydata(hair_points,[],hair_faces);mesh.update()
hair=bpy.data.objects.new('RiderBuzzcut',mesh);scene.collection.objects.link(hair);hair.parent=rig
hair.data.materials.append(mat('ShortDarkBrownHair',(.023,.017,.012),.95))
for p in mesh.polygons:p.use_smooth=True
g=hair.vertex_groups.new(name='DEF-spine.006');g.add(list(range(len(mesh.vertices))),1,'REPLACE');m=hair.modifiers.new('HeadFollow','ARMATURE');m.object=rig
# Brow strips project onto the actual continuous facial surface and follow head.
from mathutils.bvhtree import BVHTree
bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])
brow_points=[];brow_faces=[]
for sign in [1,-1]:
 start=len(brow_points)
 for i in range(17):
  t=i/16;x=sign*(.016+.041*t);z=1.591+.006*math.sin(math.pi*t)-.002*t
  width=.0018*math.sin(math.pi*(.08+.84*t))
  for dz in [-width,width]:
   origin=convert((x,-.25,z+dz));location,normal,index,distance=bvh.ray_cast(origin,Vector((0,1,0)))
   assert location is not None,('Missing brow projection',x,z+dz)
   brow_points.append(location+normal*.0008)
 for i in range(16):
  face=[start+2*i,start+2*i+1,start+2*i+3,start+2*i+2];brow_faces.append(list(reversed(face)) if sign>0 else face)
bm=bpy.data.meshes.new('BrowMesh');bm.from_pydata(brow_points,[],brow_faces);bm.update();brows=bpy.data.objects.new('RiderBrows',bm);scene.collection.objects.link(brows);brows.parent=rig
bm.materials.append(mat('BrowDarkBrown',(.016,.011,.008),.94))
for p in bm.polygons:p.use_smooth=True
bg=brows.vertex_groups.new(name='DEF-spine.006');bg.add(list(range(len(bm.vertices))),1,'REPLACE');ba=brows.modifiers.new('HeadFollow','ARMATURE');ba.object=rig
for name,values in [('_NATIVE_ID',range(len(body.data.vertices))),('_SOURCE_VERTEX_ID',range(len(body.data.vertices))),('_REGION_ID',[1]*len(body.data.vertices))]:
 attr=body.data.attributes.get(name) or body.data.attributes.new(name,'INT','POINT');attr.data.foreach_set('value',list(values))
wardrobe_report=None
if wardrobe:
 wardrobe_report=runpy.run_path(str(wardrobe))['buildWardrobe'](body,rig,out)
 wardrobe_report={'reportPath':wardrobe_report['reportPath'],'objects':[o.name for o in wardrobe_report['objects']],'materials':[m.name for m in wardrobe_report['materials']],'metrics':{k:v for k,v in wardrobe_report['report'].items() if k!='objects'}}
assert len(body.data.vertices)==10582,'Body source vertex identities must survive appearance changes'
for name,values in [('_NATIVE_ID',range(len(body.data.vertices))),('_SOURCE_VERTEX_ID',range(len(body.data.vertices))),('_REGION_ID',[1]*len(body.data.vertices))]:
 attr=body.data.attributes.get(name) or body.data.attributes.new(name,'INT','POINT');attr.data.foreach_set('value',list(values))
# Contact sockets are calibrated to actual finished soles, not the bare-foot floor.
sole_anchors={}
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for side in ['L','R']:
 sole=bpy.data.objects.get('RiderSole.'+side)
 if sole:
  bone=rig.data.edit_bones['SoleSocket.'+side];head=bone.head.copy();head.z=min(v.co.z for v in sole.data.vertices);bone.head=head;bone.tail=head+Vector((0,0,.03));sole_anchors[side]=list(head)
bpy.ops.object.mode_set(mode='OBJECT')
# Deformation-only master: explicit rest matrices, no constraints or B-Bone-only deformation.
for b in rig.data.bones:b.bbone_segments=1
for obj in scene.objects:
 if obj.type=='ARMATURE' and obj!=rig:obj.hide_render=True;obj.hide_set(True)
for col in bpy.data.collections:
 if col.name.startswith('WGTS'):col.hide_render=True;col.hide_viewport=True
meshes=[o for o in scene.objects if o.type=='MESH' and o.parent==rig]
# Small measured native movement clip; engine adapter authors ride directly on same skeleton.
scene.render.fps=24;scene.frame_start=1;scene.frame_end=49
rig.animation_data_create();action=bpy.data.actions.new('RiderIdleBreath');rig.animation_data.action=action
for f,angle in [(1,0),(13,.012),(25,0),(37,-.012),(49,0)]:
 scene.frame_set(f)
 for name,mult in [('DEF-spine.002',1),('DEF-spine.003',-.5),('DEF-spine.006',-.5)]:
  pb=rig.pose.bones[name];pb.rotation_mode='XYZ';pb.rotation_euler=(angle*mult,0,0);pb.keyframe_insert(data_path='rotation_euler',frame=f,group=name)
scene.frame_set(1)
motion={}
for frame in [1,13]:
 scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 motion[frame]={o.name:[list(v.co) for v in o.evaluated_get(dg).data.vertices] for o in meshes}
motion_deltas={name:max((Vector(a)-Vector(b)).length for a,b in zip(motion[1][name],motion[13][name])) for name in motion[1]}
scene.frame_set(1)
roles={'pelvis':'DEF-spine','trunk':['DEF-spine','DEF-spine.001','DEF-spine.002','DEF-spine.003'],'neck':['DEF-spine.004','DEF-spine.005'],'head':'DEF-spine.006'}
hands={};flex={}
for side,s,sign in [('left','L',1),('right','R',-1)]:
 title=side.title()
 for role,stem in [('upperArm','upper_arm'),('forearm','forearm'),('thigh','thigh'),('shin','shin')]:roles[role+title]=['DEF-'+stem+'.'+s,'DEF-'+stem+'.'+s+'.001']
 for role,stem in [('shoulder','shoulder'),('wrist','hand'),('foot','foot'),('toe','toe')]:roles[role+title]='DEF-'+stem+'.'+s
 digits={label:['DEF-'+stem+'.%02d.'%i+s for i in range(1,4)] for label,stem in [('thumb','thumb'),('index','f_index'),('middle','f_middle'),('ring','f_ring'),('pinky','f_pinky')]}
 hands[side]={'wristJointId':'DEF-hand.'+s,'socketNodeName':'PalmSocket.'+s,'digits':digits,'forwardJointId':digits['middle'][0],'radialJointId':digits['index'][0],'ulnarJointId':digits['pinky'][0],'normalSign':sign}
 flex[side]={}
 for label,chain in digits.items():
  for name in chain:
   b=rig.data.bones[name];direction=(b.tail_local-b.head_local).normalized();axis=direction.cross(Vector((-sign,0,0))).normalized();local=b.matrix_local.to_3x3().inverted()@axis
   flex[side][name]={'axisLocal':list(local),'maxRadians':.85 if label=='thumb' else 1.15}
contract={'accepted':False,'specification':{'units':'metres','frame':'gltf-y-up','jointNames':{b.name:b.name for b in rig.data.bones},'roles':roles,'meshNames':{o.name:o.name for o in meshes},'hands':hands},'driver':{'assetToBikeQuaternionXYZW':[0,math.sqrt(.5),0,math.sqrt(.5)],'sideZ':{'left':-1,'right':1},'soleSocketNames':{'left':'SoleSocket.L','right':'SoleSocket.R'},'digitFlex':flex,'socketOrientationCalibrationRequired':True},'nativeRest':{'frame':'X-left,-Y-forward,Z-up','sourceScale':scale,'sourceFloor':floor,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones]},'limits':['Unaccepted first dressed construction; requires actual engine moving review.','Driver must solve body and contact against authored actual bones; no Rigify controls exported.']}
(out/'rider-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
bpy.ops.object.select_all(action='DESELECT');rig.hide_set(False);rig.select_set(True)
for obj in meshes:obj.hide_set(False);obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider-assembled.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'rider.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_force_sampling=True,export_bake_animation=True,export_def_bones=True,export_skins=True,export_influence_nb=4,export_all_influences=False,export_apply=True,export_yup=True,export_attributes=True)
raw=(out/'rider.glb').read_bytes();n,kind=struct.unpack_from('<II',raw,12);gltf=json.loads(raw[20:20+n])
contract['exportedObjectMeshes']=[{'nodeIndex':i,'nodeName':node.get('name'),'meshIndex':node['mesh'],'meshName':gltf['meshes'][node['mesh']].get('name'),'primitiveCount':len(gltf['meshes'][node['mesh']]['primitives'])} for i,node in enumerate(gltf['nodes']) if 'mesh' in node]
contract['glbSHA256']=hashlib.sha256(raw).hexdigest()
(out/'rider-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
(out/'gltf-structure.json').write_text(json.dumps({k:gltf.get(k) for k in ['nodes','skins','meshes','animations','accessors']},indent=2)+'\n')
report={'accepted':False,'sourceNative':str(native),'nativeSHA256':hashlib.sha256((out/'rider-assembled.blend').read_bytes()).hexdigest(),'glbSHA256':hashlib.sha256(raw).hexdigest(),'glbBytes':len(raw),'deformJointCount':len(rig.data.bones),'meshNames':[o.name for o in meshes],'meshVertices':{o.name:len(o.data.vertices) for o in meshes},'wardrobe':wardrobe_report,'animationCount':len(gltf.get('animations',[])),'skinCount':len(gltf.get('skins',[]))}
report['nativeBreathMaxVertexDeltaMetres']=motion_deltas
report['soleAnchorsNativeMetres']=sole_anchors
report['eyeBoundsNativeMetres']={o.name:[[min(v.co[k] for v in o.data.vertices),max(v.co[k] for v in o.data.vertices)] for k in range(3)] for o in meshes if '.eye.' in o.name}
(out/'report.json').write_text(json.dumps(report,indent=2,default=str)+'\n');print(json.dumps(report,default=str))
