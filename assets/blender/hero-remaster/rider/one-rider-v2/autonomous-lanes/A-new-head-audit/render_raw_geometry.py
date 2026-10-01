"""Retained native triangle witnesses: no cleanup, reduction, UV or texture bake."""
import bpy,numpy as np,json,hashlib,math,time,gc
from pathlib import Path
from mathutils import Vector,Matrix
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit')
C=Path('/Users/raynos/Documents/Codex/2026-09-30/task-2/comparison/bust')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (O/'raw-shape-audit.json').exists():raise RuntimeError('Frozen raw audit exists')
rows=[]
for label,path,matrix in [('N1-Pixal-raw',C/'generation-v1/raw.npz',Matrix.Rotation(math.pi/2,4,'X')),('N3-TRELLIS2-raw',C/'trellis-v1/reference-head-neck.npz',Matrix.Identity(4))]:
 sourcehash=sha(path);out=O/label;sourceManifest=json.loads((out/'manifest.json').read_text())
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
 data=np.load(path);vertices=data['vertices'];faces=data['faces'];assert vertices.dtype==np.float32 and faces.dtype==np.int32
 assert np.isfinite(vertices).all() and faces.min()>=0 and faces.max()<len(vertices)
 m=bpy.data.meshes.new('Exact native pre-reduction triangle arrays');m.vertices.add(len(vertices));m.vertices.foreach_set('co',vertices.ravel());m.loops.add(faces.size);m.loops.foreach_set('vertex_index',faces.ravel());m.polygons.add(len(faces));m.polygons.foreach_set('loop_start',np.arange(len(faces),dtype=np.int32)*3);m.polygons.foreach_set('loop_total',np.full(len(faces),3,dtype=np.int32));m.polygons.foreach_set('use_smooth',np.ones(len(faces),dtype=bool));m.update()
 obj=bpy.data.objects.new(label+' untouched native triangle witness',m);scene.collection.objects.link(obj)
 # Explicit installed-export frame derivation: Pixal's native posttransform,
 # glTF import and 180deg display cancel to +90deg X; TRELLIS q=(x,z,-y)
 # glTF transform and +90deg importer cancel to native Z-up.
 norm=Matrix.Translation(Vector(sourceManifest['uniformDisplayTranslation']))@Matrix.Diagonal((sourceManifest['uniformDisplayScale'],)*3+(1,))
 obj.matrix_world=norm@matrix
 gray=bpy.data.materials.new('Geometry diagnostic neutral gray');gray.use_nodes=True;shader=gray.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.42,.42,.42,1);shader.inputs['Roughness'].default_value=.65;m.materials.append(gray)
 world=bpy.data.worlds.new('Common gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world;target=Vector((0,0,1.58))
 for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('Matched actual raw face');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=.34
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
 row={'label':label,'rawNPZ':str(path),'SHA256':sourcehash,'nativeVertices':len(vertices),'nativeTriangles':len(faces),'allTriangleIndicesRetained':True,'decimationOrCleanup':False,'rawMaterialMode':'Neutral gray, authored smooth normals only; no native attribute/PBR bake','sourceToAlignedBlenderMatrix':[list(r) for r in matrix],'displayFrameMatchesExportManifest':str(out/'manifest.json'),'displaySourceSHA256':sourceManifest['sourceSHA256'],'displayScale':sourceManifest['uniformDisplayScale'],'displayTranslation':sourceManifest['uniformDisplayTranslation'],'CPUThreads':2,'views':[],'topologyAcceptance':'NOT ACCEPTED / not independently repaired or manifold-tested'}
 del vertices,faces;data.close();gc.collect()
 for view,yaw in [('front',0),('profile',90),('three-quarter',45)]:
  a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();p=out/f'pre-reduction-gray-{view}.png';scene.render.filepath=str(p);t=time.perf_counter();bpy.ops.render.render(write_still=True);row['views'].append({'view':view,'path':str(p),'SHA256':sha(p),'wallSeconds':time.perf_counter()-t})
 assert sha(path)==sourcehash;rows.append(row);(out/'raw-shape-manifest.json').write_text(json.dumps(row,indent=2)+'\n');bpy.ops.wm.read_factory_settings(use_empty=True);gc.collect()
(O/'raw-shape-audit.json').write_text(json.dumps({'status':'UNACCEPTED actual pre-reduction shape witnesses, no topology cleanup','recipeSHA256':sha(Path(__file__)),'candidates':rows,'Hunyuan21':'Saved pre-paint shape is already post-FaceReducer; generator-versus-reducer attribution remains unavailable.'},indent=2)+'\n')
