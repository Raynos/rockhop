"""Read-only actual NEW bust face comparison, CPU two threads, no source saves."""
import bpy,bmesh,json,hashlib,math,time,sys,os
from pathlib import Path
from mathutils import Vector,Matrix
R=Path('/Users/raynos/Documents/Codex/2026-09-30/task-2');C=R/'comparison';P=R/'rider-refinement/pixal-comp-a'
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit')
OUT=OUT/"alignment-correction01";OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
candidates=[
 ('N1-Pixal-raw',C/'bust/generation-v1/bust.glb',180,'Actual Pixal generated bust',C/'bust/final-report.json'),
 ('N2-Hunyuan21-raw',C/'bust/hunyuan21-v1/model.glb',0,'Actual Hunyuan3D 2.1 generated bust',C/'bust/final-report.json'),
 ('N3-TRELLIS2-raw',C/'bust/trellis-v1/reference-head-neck.glb',0,'Actual TRELLIS.2 generated bust',C/'bust/final-report.json'),
 ('N4-regional11d',P/'trial11d-clean-regional-bake/bust.glb',0,'NEW authored Blender loft/reference-projected albedo; not neural output',P/'trial11d-clean-regional-bake/provenance.json'),
 ('N5-eyes12c',P/'trial12c-eye-material-finish/bust.glb',0,'NEW Blender-derived reconstruction with separate eyes',P/'trial12c-eye-material-finish/construction.json'),
 ('N6-focused14b',P/'trial14b-focused-bust-corrected/bust.glb',0,'NEW focused Blender eye/lid/sculpt refinement',P/'trial14b-focused-bust-corrected/refinement.json'),
 ('N7-hair18',P/'trial18-hair-ear-costume/bust.glb',0,'NEW Blender-derived short swept locks/ears/material refinement',P/'trial18-hair-ear-costume/construction.json')]
if (OUT/'audit.json').exists():raise RuntimeError('Frozen comparison exists')
candidates=[row for row in candidates if row[0]=="N2-Hunyuan21-raw"]
records=[];start=time.perf_counter()
for label,source,zrotate,method,provenance in candidates:
 directory=OUT/label;directory.mkdir(exist_ok=True);sourcehash=sha(source)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));scene=bpy.context.scene
 meshes=[o for o in scene.objects if o.type=='MESH' and o.visible_get()]
 assert meshes and not any(o.type=='ARMATURE' for o in scene.objects),'Only unrigged NEW bust sources'
 roots=[o for o in scene.objects if o.parent is None];align=bpy.data.objects.new('Read-only display alignment',None);scene.collection.objects.link(align)
 for obj in roots:matrix=obj.matrix_world.copy();obj.parent=align;obj.matrix_world=matrix
 align.rotation_euler.z=math.radians(zrotate);align.rotation_euler.x=math.pi;bpy.context.view_layer.update()
 allpoints=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 lo=Vector([min(p[i] for p in allpoints) for i in range(3)]);hi=Vector([max(p[i] for p in allpoints) for i in range(3)])
 # Deliberate framing only: head mesh when author explicitly separated it;
 # otherwise upper 45% of original bust bounds. No mesh/UV/material edits.
 headmeshes=[o for o in meshes if 'Standalone head-neck' in o.name]
 if headmeshes:
  points=[o.matrix_world@v.co for o in headmeshes for v in o.data.vertices];roi='Explicit standalone authored head mesh'
 else:
  points=[p for p in allpoints if p.z>=hi.z-(hi.z-lo.z)*.45];roi='Upper 45% of whole generated bust original height'
 hlo=Vector([min(p[i] for p in points) for i in range(3)]);hhi=Vector([max(p[i] for p in points) for i in range(3)]);centre=(hlo+hhi)*.5;scale=.20/(hhi.x-hlo.x)
 norm=bpy.data.objects.new('Read-only uniform face framing',None);scene.collection.objects.link(norm);align.parent=norm;norm.scale=(scale,)*3;norm.location=-centre*scale+Vector((0,0,1.58));bpy.context.view_layer.update()
 materials=[];topology=[]
 for obj in meshes:
  bm=bmesh.new();bm.from_mesh(obj.data);topology.append({'mesh':obj.name,'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges)});bm.free()
  for material in obj.data.materials:
   if not material:continue
   materials.append({'name':material.name,'nodes':[{'node':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'imageSize':list(n.image.size) if n.type=='TEX_IMAGE' and n.image else None} for n in material.node_tree.nodes] if material.use_nodes else []})
 world=bpy.data.worlds.new('Common gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
 target=Vector((0,0,1.58));lightRows=[]
 for name,position,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
  data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=position;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler();lightRows.append({'name':name,'position':position,'powerWatts':power,'size':size})
 data=bpy.data.cameras.new('Matched face orthographic');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO';data.ortho_scale=.34
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
 views=[]
 for mode in ['PBR','gray']:
  if mode=='gray':
   gray=bpy.data.materials.new('Geometry-only neutral gray');gray.use_nodes=True;shader=gray.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.42,.42,.42,1);shader.inputs['Roughness'].default_value=.65
   for obj in meshes:
    obj.data.materials.append(gray);index=len(obj.data.materials)-1
    for poly in obj.data.polygons:poly.material_index=index
  for view,yaw in [('front',0),('profile',90),('three-quarter',45)]:
   angle=math.radians(yaw);camera.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();path=directory/f'{mode}-{view}.png';scene.render.filepath=str(path);t=time.perf_counter();bpy.ops.render.render(write_still=True);views.append({'mode':mode,'view':view,'yaw':yaw,'path':str(path),'SHA256':sha(path),'wallSeconds':time.perf_counter()-t,'cameraMatrix':[list(row) for row in camera.matrix_world]})
 assert sha(source)==sourcehash
 row={'label':label,'source':str(source),'sourceSHA256':sourcehash,'sourceSHA256After':sha(source),'provenanceFile':str(provenance),'provenanceSHA256':sha(provenance),'provenance':json.loads(provenance.read_text()),'method':method,'noHistoricalProductionDonor':True,'topology':topology,'materials':materials,'alignmentZDegrees':zrotate,'alignmentXDegrees':180,'alignmentControlManifest':str(C/'bust/views-hunyuan21-native/manifest.json'),'wholeBoundsBeforeDisplay':[list(lo),list(hi)],'faceROI':roi,'faceROIBoundsBeforeDisplay':[list(hlo),list(hhi)],'uniformDisplayScale':scale,'uniformDisplayTranslation':list(norm.location),'framedHeadWidthM':.2,'lights':lightRows,'views':views,'parentScore':None,'accepted':False}
 records.append(row);(directory/'manifest.json').write_text(json.dumps(row,indent=2)+'\n')
 (OUT/'audit-progress.json').write_text(json.dumps({'status':'Read-only actual candidates; no acceptance','completed':[r['label'] for r in records]},indent=2)+'\n')
report={'status':'UNACCEPTED NEW head audit; parent alone scores', 'startedUTC':'2026-10-01T01:54:05Z','deadlineUTC':'2026-10-01T02:24:05Z','rendererSHA256':sha(Path(__file__)),'blenderVersion':bpy.app.version_string,'blenderBinarySHA256':sha(Path(bpy.app.binary_path)),'PythonVersion':sys.version,'isolatedRoots':{k:os.environ.get(k) for k in ['BLENDER_USER_CONFIG','BLENDER_USER_SCRIPTS','BLENDER_USER_EXTENSIONS','TMPDIR']},'CPUSettings':{'device':'CPU','threads':2,'samples':24,'resolution':[640,640],'orthoScale':.34,'cameraTarget':[0,0,1.58],'worldRGB':[.16]*3,'worldStrength':.65,'viewTransform':'AgX'},'candidates':records,'wallSeconds':time.perf_counter()-start,'limits':['Matched lighting/camera/normalized ROI width; physical source scale differs and is recorded.','Generated ROI is deliberately approximate, not a face landmark measurement or identity score.','Native PBR unchanged; gray is diagnostic scene-only replacement.','No source saves, graft, rig, motion, contact or gameplay acceptance.','Blender reference-albedo reconstructions are explicitly distinguished from actual neural generation.']}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print('HEAD_AUDIT_FROZEN',len(records),flush=True)
