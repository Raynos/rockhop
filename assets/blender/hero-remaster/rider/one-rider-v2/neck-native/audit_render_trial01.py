"""Independent roundtrip audit + four CPU gray closeups, no source edits."""
import bpy,bmesh,json,hashlib,time,math
from pathlib import Path
from collections import Counter
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=R/'neck-native/trial01'
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/neck-native/trial01');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (OUT/'audit.json').exists():raise RuntimeError('Frozen audit already exists')
start=time.perf_counter();blend=RUN/'body-head.blend';glb=RUN/'body-head.glb';source={str(p):sha(p) for p in [blend,glb]}
def records():
 rows=[];materials=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  m=o.data;m.calc_loop_triangles();uv=m.uv_layers.active
  counts=Counter(p.material_index for p in m.polygons)
  materials.append({'object':o.name,'vertices':len(m.vertices),'faces':len(m.polygons),'materialFaceCounts':dict(counts),'slots':[mat.name if mat else None for mat in m.materials]})
  for t in m.loop_triangles:
   corners=[]
   for li in t.loops:
    p=o.matrix_world@m.vertices[m.loops[li].vertex_index].co;u=uv.data[li].uv
    corners.append(tuple(round(float(x),5) for x in list(p)+list(u)))
   rows.append((m.materials[t.material_index].name if m.materials and m.materials[t.material_index] else '',tuple(sorted(corners))))
 return Counter(rows),materials
bpy.ops.wm.open_mainfile(filepath=str(blend));before,material_before=records()
body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'collar' in o.name)
bm=bmesh.new();bm.from_mesh(body.data)
body_topology={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges)};bm.free()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb));bpy.context.view_layer.update();after,material_after=records()
uv_before=Counter(corners for (material,corners),count in before.items() for _ in range(count));uv_after=Counter(corners for (material,corners),count in after.items() for _ in range(count))
report={'status':'UNACCEPTED independent trial01 audit','inputs':source,'recipeSHA256':sha(Path(__file__)),'bodyBlendTopology':body_topology,'preExportMaterialAssignments':material_before,'reimportMaterialAssignments':material_after,'roundtripTriangles':{'before':sum(before.values()),'after':sum(after.values()),'materialAndCornerUVMismatchCount':sum((before-after).values())+sum((after-before).values()),'geometryAndCornerUVOnlyMismatchCount':sum((uv_before-uv_after).values())+sum((uv_after-uv_before).values()),'comparisonPrecision':'World positions and face-corner UV rounded1e-5; triangle corner-order invariant'},'actualTrialMaterialProblem':'Four intended body slots populated after material.clear(), resetting stored polygon indices to0. Export has one body primitive: no accepted skin/glove/lining assignment.','visibleRiderContacts':'UNMEASURED','neckTurnAndBend':'UNMEASURED; no rig','textureAndNormalContinuity':'UNMEASURED/unaccepted; material assignment failed','views':[]}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
scene=bpy.context.scene
for o in list(scene.objects):
 if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
gray=bpy.data.materials.new('Geometry diagnostic only neutral gray');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
for o in scene.objects:
 if o.type=='MESH':o.data.materials.clear();o.data.materials.append(gray)
world=bpy.data.worlds.new('Common gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.58))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Native collar geometry closeup');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=.50
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
for label,yaw in [('front',0),('profile',90),('rear',180),('three-quarter',45)]:
 target=Vector((0,.015,1.58));angle=math.radians(yaw);cam.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),.08));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();p=OUT/f'gray-{label}.png';scene.render.filepath=str(p);t=time.perf_counter();bpy.ops.render.render(write_still=True);report['views'].append({'label':label,'yaw':yaw,'path':str(p),'sha256':sha(p),'wallSeconds':time.perf_counter()-t})
assert source=={p:sha(Path(p)) for p in source}
report['inputsAfter']={p:sha(Path(p)) for p in source};report['CPUSettings']={'threads':4,'cyclesDevice':'CPU','samples':16,'resolution':[640,640],'orthoScale':.5,'target':[0,.015,1.58],'material':'Neutral gray only; no skin texture trial','denoising':True};report['wallSeconds']=time.perf_counter()-start
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print('AUDIT_FROZEN',json.dumps({'roundtrip':report['roundtripTriangles'],'views':len(report['views']),'status':report['status']}),flush=True)
