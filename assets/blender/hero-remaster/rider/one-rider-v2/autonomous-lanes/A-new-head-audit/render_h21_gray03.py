"""Actual fresh source diagnosis, read-only CPU2, parent-reviewed painted X180.

Raw and reduced use their native Blender imported frame. Shared framing is a
display comparison, not a proved per-vertex reducer/painted correspondence.
No numeric match prerequisite, no mesh cleanup, no saved asset derivatives.
"""
import bpy, json, hashlib, math, time
from pathlib import Path
from mathutils import Vector, Matrix
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit')
G=R/'generation/h21-buzz-native01'
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/gray-diagnostic03')
O.mkdir(exist_ok=True)
if (O/'manifest.json').exists(): raise RuntimeError('Frozen gray diagnostic exists')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={str(G/n):sha(G/n) for n in ['model.glb','raw-shape.glb','raw-shape.npz','shape.glb']}
witness=json.loads((O.parent/'painted-orientation-witness01/manifest.json').read_text())
frame=next(v for v in witness['views'] if v['label']=='X180')
scale=frame['displayScale']; translation=Vector(frame['translation'])
normalizer=Matrix.Translation(translation)@Matrix.Diagonal((scale,scale,scale,1))
views=[('front',0,0),('profile',90,0),('three-quarter',45,0),('rear',180,0)]
nine=[('front',0,0),('front-left',45,0),('left',90,0),('rear-left',135,0),('rear',180,0),('rear-right',225,0),('right',270,0),('front-right',315,0),('top-front',0,30)]
report={'status':'UNACCEPTED actual source diagnostic; parent alone judges','sourceSHA256':sources,'recipeSHA256':sha(Path(__file__)),'CPUThreads':2,'GPUJob':False,'variants':[], 'display':{'paintedXRotationDegrees':180,'rawReducedXRotationDegrees':0,'scale':scale,'translation':list(translation),'correspondence':'Shared camera/framing; no per-vertex painted-to-reduced identity claimed.'}}
for label,filename,angle,gray in [('painted-gray','model.glb',180,True),('painted-PBR','model.glb',180,False),('raw-gray','raw-shape.glb',0,True),('reduced-gray','shape.glb',0,True)]:
 bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(G/filename)); scene=bpy.context.scene
 meshes=[o for o in scene.objects if o.type=='MESH']; roots=[o for o in scene.objects if o.parent is None]
 parent=bpy.data.objects.new('Read-only recorded display frame',None);scene.collection.objects.link(parent)
 for obj in roots: original=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=original
 parent.matrix_world=normalizer@Matrix.Rotation(math.radians(angle),4,'X');bpy.context.view_layer.update()
 counts=[]
 for obj in meshes:
  incidence={}
  for p in obj.data.polygons:
   for edge in p.edge_keys:incidence[edge]=incidence.get(edge,0)+1
  boundary=[e for e,n in incidence.items() if n==1]; nm=[e for e,n in incidence.items() if n>2]
  counts.append({'name':obj.name,'vertices':len(obj.data.vertices),'triangles':len(obj.data.polygons),'boundaryEdges':len(boundary),'nonManifoldAbove2Edges':len(nm),'materials':[m.name if m else None for m in obj.data.materials],'boundaryWorldSegments':[[list(obj.matrix_world@obj.data.vertices[i].co) for i in e] for e in boundary]})
 if gray:
  mat=bpy.data.materials.new('Neutral gray geometry diagnostic');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
  for obj in meshes:
   obj.data.materials.append(mat);index=len(obj.data.materials)-1
   for p in obj.data.polygons:p.material_index=index
 world=bpy.data.worlds.new('Common neutral gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world;target=Vector((0,0,1.5))
 for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;obj=bpy.data.objects.new(name,d);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('Actual matched display camera');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO'
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
 rendered=[]
 for scope,chosen,look,ortho in [('face',views,Vector((0,0,1.6)),.46),('nine',nine,Vector((0,0,1.5)),.7)]:
  for name,yaw,elev in chosen:
   a=math.radians(yaw);e=math.radians(elev);cam.location=look+Vector((4*math.sin(a)*math.cos(e),-4*math.cos(a)*math.cos(e),4*math.sin(e)));cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=ortho;path=O/f'{label}-{scope}-{name}.png';scene.render.filepath=str(path);start=time.perf_counter();bpy.ops.render.render(write_still=True)
   row={'scope':scope,'view':name,'path':str(path),'SHA256':sha(path),'cameraMatrix':[list(r) for r in cam.matrix_world],'target':list(look),'orthoScale':ortho,'wallSeconds':time.perf_counter()-start};rendered.append(row)
   (O/'progress.json').write_text(json.dumps({'status':'Actual source CPU diagnostic in progress','lastCompleted':{'variant':label,**row}},indent=2)+'\n')
 report['variants'].append({'label':label,'source':str(G/filename),'sourceSHA256':sources[str(G/filename)],'frameRotationXDegrees':angle,'meshes':counts,'grayDiagnosticOnly':gray,'views':rendered})
 (O/f'{label}-manifest.json').write_text(json.dumps(report['variants'][-1],indent=2)+'\n')
for path,digest in sources.items():assert sha(Path(path))==digest,'Original source changed'
report['sourcesUnchanged']=True
report['rawImportLimits']={'nativeSourceTriangles':985183,'BlenderImportedTriangles':985175,'excludedRepeatedIndexZeroAreaTriangles':8,'exactFaceIDsReport':str(O.parent/'raw-index-forensic.json'),'sourceNPZAndGLBStillContainEveryOriginalIndex':True}
report['limits']=['No geometry fixes, paint edits, new model jobs or saved mesh derivatives.','Gray changes material only in discarded diagnostic scene; source normals/smooth flags unchanged.','No rig, visible contact, neck motion or appearance acceptance.','Raw-to-painted geometry correspondence not asserted; shared display frame explicitly recorded.']
(O/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('ACTUAL_GRAY_DIAGNOSTIC_FROZEN',len(report['variants']),flush=True)
