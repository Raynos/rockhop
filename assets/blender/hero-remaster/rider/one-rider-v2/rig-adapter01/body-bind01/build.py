"""Private fresh 19-bone bind and played sitting probe. No production donor."""
import bpy,math,json,hashlib,time
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
O=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind01';R=BASE/'rig-adapter01/body-bind01';R.mkdir(parents=True,exist_ok=True)
SOURCE=BASE/'parent-assembly/donor-fit05/rider.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
meshes=[o for o in scene.objects if o.type=='MESH'];body=next(o for o in meshes if 'protected' in o.name.lower());head=next(o for o in meshes if o!=body)
for o in list(scene.objects):
 if o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
for o in meshes:
 m=o.matrix_world.copy()
 for v in o.data.vertices:v.co=m@v.co
 o.matrix_world=Matrix.Identity(4);o.data.update()
rest={o.name:[v.co.copy() for v in o.data.vertices] for o in meshes}
report=json.loads((ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-landmarks/report.json').read_text());hands={r['nativeAnatomicalSide']:r for r in report['hands']}
# Deliberate estimates under clothes, actual wrist heads only. Runtime suffixes
# are opposite native source suffixes after the proper +90 degree rotation.
bones={}
def bone(name,p,t,parent=None):bones[name]=(Vector(p),Vector(t),parent)
bone('pelvis',(0,.015,.88),(0,.015,1.04));bone('spine',(0,.015,1.04),(0,.02,1.24),'pelvis');bone('chest',(0,.02,1.24),(0,.02,1.49),'spine');bone('neck',(0,.02,1.49),(0,.02,1.545),'chest');bone('head',(0,.02,1.545),(0,.02,1.795),'neck')
for sd,sign,native in [('L',-1,'R'),('R',1,'L')]:
 wrist=Vector(hands[native]['wristJoint']);palm=Vector(hands[native]['knuckleCentroid']);shoulder=Vector((sign*.205,.02,1.38));elbow=Vector((sign*.285,.025,1.125));hip=Vector((sign*.105,.015,.90));knee=Vector((sign*.145,0,.50));ankle=Vector((sign*.18,.045,.115))
 bone('shoulder.'+sd,(sign*.07,.02,1.38),shoulder,'chest');bone('upperArm.'+sd,shoulder,elbow,'shoulder.'+sd);bone('forearm.'+sd,elbow,wrist,'upperArm.'+sd);bone('hand.'+sd,wrist,palm,'forearm.'+sd);bone('thigh.'+sd,hip,knee,'pelvis');bone('shin.'+sd,knee,ankle,'thigh.'+sd);bone('foot.'+sd,ankle,(sign*.18,-.115,.055),'shin.'+sd)
data=bpy.data.armatures.new('NEW rider measured-wrist19');rig=bpy.data.objects.new(data.name,data);scene.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,(p,t,parent) in bones.items():
 b=data.edit_bones.new(name);b.head=p;b.tail=t
 if parent:b.parent=data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');assert len(data.bones)==19
# Four-or-fewer localized influences; torso/limb segmentation is explicit and
# provisional. Native hands keep measured shape rigid to hand in 19-bone export.
smooth=lambda t:(lambda u:u*u*(3-2*u))(max(0,min(1,t)))
handmap=json.loads((ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-landmarks/native-weight-transfer-map.json').read_text());nativeids={i:('R' if m['nativeSide']=='L' else 'L') for m in handmap['matches'] for i in m['completeVertexIds']}
def mix(a,b,t):return {a:1-t,b:t}
def armweights(p,sd):
 sh,el,_=bones['upperArm.'+sd];wr=bones['hand.'+sd][0];d=(p-el).dot((sh-wr).normalized())
 return mix('forearm.'+sd,'upperArm.'+sd,smooth((d+.045)/.09))
def torsoweights(p):
 z=p.z
 if z<1.05:return mix('pelvis','spine',smooth((z-.93)/.12))
 if z<1.24:return mix('spine','chest',smooth((z-1.12)/.12))
 return {'chest':1}
for obj in meshes:
 groups={n:obj.vertex_groups.new(name=n) for n in bones};counts={};maxsum=0
 for v in obj.data.vertices:
  p=v.co;sd='R' if p.x>0 else 'L'
  if obj==head:
   n=smooth((p.z-1.49)/.03);h=smooth((p.z-1.52)/.025);w={'chest':1-n,'neck':n*(1-h),'head':n*h}
  elif v.index in nativeids:w={'hand.'+nativeids[v.index]:1}
  elif p.z<.80:
   if p.z<.17:w=mix('foot.'+sd,'shin.'+sd,smooth((p.z-.105)/.065))
   elif p.z<.61:w=mix('shin.'+sd,'thigh.'+sd,smooth((p.z-.45)/.10))
   else:w=mix('thigh.'+sd,'pelvis',smooth((p.z-.735)/.10))
  else:
   threshold=.20 if p.z<1.2 else .20-(p.z-1.2)*.20
   aw=smooth((abs(p.x)-threshold)/.06) if p.z<1.43 else 0
   tw=torsoweights(p);ar=armweights(p,sd);w={k:a*(1-aw) for k,a in tw.items()}
   for k,a in ar.items():w[k]=w.get(k,0)+a*aw
   # Connected wrist collar follows native hand progressively below measured wrist.
   if p.z<.93 and abs(p.x)>.28:
    hw=smooth((.93-p.z)/.065);w={k:a*(1-hw) for k,a in w.items()};w['hand.'+sd]=hw
  w={k:a for k,a in w.items() if a>1e-8};total=sum(w.values());assert total>0 and len(w)<=4
  for k,a in w.items():groups[k].add([v.index],a/total,'REPLACE');counts[k]=counts.get(k,0)+1
  maxsum=max(maxsum,abs(sum(a/total for a in w.values())-1))
 mod=obj.modifiers.new('Explicit NEW nineteen-bone skin','ARMATURE');mod.object=rig;obj.parent=rig
 obj['skinScope']='Provisional documented joint estimates, not accepted riding contacts';obj['maxWeightSumError']=maxsum
# Sockets mark measured surface witnesses, not accepted handle/peg placements.
surfaces=json.loads((ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-landmarks/surface-witness.json').read_text())
for sd,sign,native in [('L',-1,'R'),('R',1,'L')]:
 # Skeletal palm centre is intentionally diagnostic; no false surface claim.
 for name,bn,p in [('gripSocket.'+sd,'hand.'+sd,hands[native]['skeletalPalmCentre']),('soleSocket.'+sd,'foot.'+sd,report['soleSurfaceWitnesses'][0 if native=='L' else 1]['bottom2mmVertexCentroid'])]:
  obj=bpy.data.objects.new(name,None);scene.collection.objects.link(obj);obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bn
  desired=Matrix.Translation(Vector(p));obj.matrix_world=desired;bpy.context.view_layer.update()
# Sitting probe preserves segment lengths. Hand orientation remains standing:
# this clip judges full-body skin only, not riding finger closure.
restmat={n:b.matrix_local.copy() for n,b in data.bones.items()};frames=[]
def aim(n,p,direction):
 b=data.bones[n];q=(b.tail_local-b.head_local).normalized().rotation_difference(direction.normalized());return Matrix.Translation(p)@q.to_matrix().to_4x4()@restmat[n].to_3x3().to_4x4()
for frame in range(1,25):
 t=(frame-1)/23;u=smooth(t);lean=math.radians(12)*math.sin(math.pi*t);torso=Vector((0,-math.sin(lean),math.cos(lean)));delta=Vector((0,.10*u,-.355*u));target={}
 for n in ['pelvis','spine','chest','neck','head']:
  p=bones[n][0];p0=bones['pelvis'][0];target[n]=aim(n,p0+delta+Vector((p.x,p.y-p0.y,0))+torso*(p.z-p0.z),torso)
 for sd,sign in [('L',-1),('R',1)]:
  for n in ['shoulder.'+sd,'upperArm.'+sd,'forearm.'+sd,'hand.'+sd]:
   p=bones[n][0];p0=bones['pelvis'][0];p=p0+delta+Vector((p.x,p.y-p0.y,0))+torso*(p.z-p0.z);target[n]=Matrix.Translation(p)@restmat[n].to_3x3().to_4x4()
  hip=bones['thigh.'+sd][0]+delta;l1=(bones['thigh.'+sd][1]-bones['thigh.'+sd][0]).length;l2=(bones['shin.'+sd][1]-bones['shin.'+sd][0]).length
  d1=(bones['thigh.'+sd][1]-bones['thigh.'+sd][0]).normalized().lerp(Vector((sign*.10,-.990,-.10)).normalized(),u).normalized();knee=hip+d1*l1
  d2=(bones['shin.'+sd][1]-bones['shin.'+sd][0]).normalized().lerp(Vector((sign*.09,.10,-.991)).normalized(),u).normalized();ankle=knee+d2*l2
  target['thigh.'+sd]=aim('thigh.'+sd,hip,d1);target['shin.'+sd]=aim('shin.'+sd,knee,d2);target['foot.'+sd]=Matrix.Translation(ankle)@restmat['foot.'+sd].to_3x3().to_4x4()
 for n,m in target.items():
  pb=rig.pose.bones[n];pb.matrix=m;pb.rotation_mode='QUATERNION';pb.keyframe_insert('location',frame=frame);pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('scale',frame=frame)
 scene.frame_set(frame);bpy.context.view_layer.update();frames.append({'frame':frame,'tSeconds':(frame-1)/12,'sitBlend':u,'pelvisShift':list(delta)})
rig.animation_data.action.name='stand_to_sit_probe';scene.frame_start=1;scene.frame_end=24;scene.render.fps=12;scene.frame_set(1)
# Proper rotation to file runtime frame; source rest geometry stays rigidly exact.
rig.matrix_world=Matrix.Translation((0,.65,0))@Matrix.Rotation(math.pi/2,4,'Z')
# Blender file Y+.65 exports glTF Z-.65, so shift must be Blender X+.65.
rig.matrix_world=Matrix.Translation((.65,0,0))@Matrix.Rotation(math.pi/2,4,'Z')
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(R/'rider.blend'));bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in meshes:o.select_set(True)
for o in scene.objects:
 if o.type=='EMPTY':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'rider.glb'),export_format='GLB',use_selection=True,export_animations=True,export_skins=True,export_force_sampling=True)
# Render in original authoring frame, same new skin and actual action.
rig.matrix_world=Matrix.Identity(4);scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Neutral');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
 ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.size=size;lo=bpy.data.objects.new(name,ld);scene.collection.objects.link(lo);lo.location=pos;lo.rotation_euler=(Vector((0,0,1.2))-lo.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Actual sitting probe');camera=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(camera);scene.camera=camera;cd.type='ORTHO';cd.ortho_scale=2;scene.render.resolution_x=384;scene.render.resolution_y=480;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for yaw in [0,90]:
 a=math.radians(yaw);target=Vector((0,0,.83));camera.location=target+Vector((4*math.sin(a),-4*math.cos(a),0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 for frame in range(1,25):
  scene.frame_set(frame);scene.render.filepath=str(O/f'actual-sit-{yaw:03d}-{frame:04d}.png');bpy.ops.render.render(write_still=True)
  deps=bpy.context.evaluated_depsgraph_get()
  for obj in meshes:
   ev=obj.evaluated_get(deps);me=ev.to_mesh();assert len(me.vertices)==len(rest[obj.name]) and all(math.isfinite(c) for v in me.vertices for c in v.co);ev.to_mesh_clear()
assert sha(SOURCE)==before
(O/'report.json').write_text(json.dumps({'sourceSHA256':before,'sourceUnchanged':True,'newBoneCount':19,'sourceGeometry':'Position/topology unchanged before skin; properrigid axis transform at export','jointDefinitions':{n:{'head':list(p),'tail':list(t),'parent':pa,'status':'Measured native wrist/palm' if n.startswith('hand.') else 'Documented under-clothing estimate'} for n,(p,t,pa) in bones.items()},'clip':'stand_to_sit_probe','frames':frames,'runtimeGLBSHA256':sha(R/'rider.glb'),'limits':['Provisional localizedweights, no acceptance before played inspection','Openhands/no ridingorientation adapter','Palm sockets are skeletal diagnostic centres, not accepted grip surface','Sittingprobe authored by Blender; no UniMate generation claimed','No production asset or physics changed']},indent=2)+'\n')
