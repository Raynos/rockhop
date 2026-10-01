"""Coherent skin response experiment; original geometry/UV/image bytes retained."""
import bpy,json,struct,hashlib,math,copy
from pathlib import Path
from mathutils import Matrix,Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/skin-response05');O.mkdir(exist_ok=True)
T=R/'skin-response05';T.mkdir(exist_ok=True)
source=R/'cheek-texture04/model.glb';raw=source.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[n+28:];old=copy.deepcopy(doc['materials']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for mat in doc['materials']:
 mat.setdefault('extensions',{})['KHR_materials_specular']={'specularColorFactor':[1,1,1],'specularFactor':.25}
 p=mat.setdefault('pbrMetallicRoughness',{});p.pop('metallicRoughnessTexture',None);p['roughnessFactor']=.62;p['metallicFactor']=0
encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);path=T/'model.glb';path.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(encoded)+8+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)
assert path.read_bytes()[-len(binary):]==binary
def render(path,gray,label):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));scene=bpy.context.scene;meshes=[o for o in scene.objects if o.type=='MESH'];roots=[o for o in scene.objects if o.parent is None];w=json.loads((O.parent/'painted-orientation-witness01/manifest.json').read_text());f=next(v for v in w['views'] if v['label']=='X180');parent=bpy.data.objects.new('Reviewed X180 source display',None);scene.collection.objects.link(parent)
 for obj in roots:matrix=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=matrix
 parent.matrix_world=Matrix.Translation(Vector(f['translation']))@Matrix.Diagonal((f['displayScale'],)*3+(1,))@Matrix.Rotation(math.pi,4,'X')
 if gray:
  material=bpy.data.materials.new('Discarded diagnostic gray');material.use_nodes=True;bs=material.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
  for obj in meshes:
   obj.data.materials.append(material);index=len(obj.data.materials)-1
   for polygon in obj.data.polygons:polygon.material_index=index
 world=bpy.data.worlds.new('Matched neutral studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world;target=Vector((0,0,1.5))
 for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('Matched face comparison');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=.46;target=Vector((0,0,1.6));scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';views=[]
 for name,yaw in [('front',0),('profile',90),('three-quarter',45),('rear',180)]:
  a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();out=O/(label+'-'+name+'.png');scene.render.filepath=str(out);bpy.ops.render.render(write_still=True);views.append({'path':str(out),'SHA256':sha(out),'cameraMatrix':[list(r) for r in cam.matrix_world]});print('ACTUAL_FACE_VIEW',out,flush=True)
 return views

report={'status':'Unaccepted coherent material-response derivative','sourceSHA256':sha(source),'outputSHA256':sha(path),'allBinaryBuffersExact':True,'materialsBefore':old,'materialsAfter':doc['materials'],'deliberateLimit':'Uniform skin/hair roughness discards source MR variation for this controlled diagnostic, source map bytes retained unused; no texture pixel/UV/geometry change','CPUThreads':2,'GPUJob':False,'views':render(path,False,'actual-PBR')};(O/'report.json').write_text(json.dumps(report,indent=2)+'\n')
