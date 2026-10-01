"""Read-only failed seam witness. No changed landmarks, selection, or repair."""
import bpy,bmesh,numpy as np,json,hashlib,math,time
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
RUN=R/'autonomous-lanes/A-manual-panel/trial01';OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-manual-panel/trial01')
if (OUT/'forensic.json').exists():raise RuntimeError('Frozen forensic exists')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((OUT/'report.json').read_text());bodypath=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';maskpath=R/'collar-trial1/collar-selection.npz'
assert sha(bodypath)==report['inputs'][str(bodypath)] and sha(maskpath)==report['inputs'][str(maskpath)]
bpy.ops.wm.open_mainfile(filepath=str(bodypath));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');bm=bmesh.new();bm.from_mesh(body.data)
data=np.load(maskpath);v=data['verticesBlender'];f=data['faces'];keep=data['retainedFaceMask'];tree=KDTree(len(f))
for i,ids in enumerate(f):tree.insert(v[ids].mean(0),i)
tree.balance();remove=[];matched=[]
for face in bm.faces:
 if len(face.verts)!=3:continue
 points=np.array([x.co for x in face.verts]);co,i,d=tree.find(points.mean(0))
 if d<2e-6 and not keep[i] and max(min(np.linalg.norm(q-p) for p in v[f[i]]) for q in points)<2e-6:remove.append(face);matched.append(i)
assert len(set(matched))==int((~keep).sum());bmesh.ops.delete(bm,geom=remove,context='FACES')
loose=[x for x in bm.verts if not x.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.verts.index_update();bm.verts.ensure_lookup_table();bm.faces.index_update()
seam=[bm.verts[i] for i in report['explicitSeam']['orderedSourceVertexIDs']]
lookup={frozenset(e.verts):e for e in bm.edges};seamEdges={lookup[frozenset((a,b))] for a,b in zip(seam,seam[1:]+seam[:1])}
rim={v for e in bm.edges if e.is_boundary for v in e.verts};inside={face for v in rim for face in v.link_faces};todo=list(inside)
while todo:
 face=todo.pop()
 for edge in face.edges:
  if edge in seamEdges:continue
  for other in edge.link_faces:
   if other not in inside:inside.add(other);todo.append(other)
forensic={'status':'FAILED exact first seam prefix, no panel deletion/head/join',
 'failure':report['failure'],'floodFaces':len(inside),'postMaskSourceFaces':len(bm.faces),'permittedPanelFacesExclusiveUpperLimit':len(bm.faces)//5,
 'floodIncludesSeamBothSides':sum(len(set(e.link_faces)&inside)==2 for e in seamEdges),
 'sourceFaceIndicesReached':sorted(face.index for face in inside),'seamSourceVertexIndices':report['explicitSeam']['orderedSourceVertexIDs'],
 'sourceMaskRemovedHistoricalTriangles':len(matched),'methodUnchanged':True,'newHeadNeverLoaded':True,'inputs':report['inputs'],
 'limits':['Open source mask prefix; not an assembled character.','Red seam overlay is a diagnostic curve, not a rider material or accepted garment.','No visible rider contacts or rigging measured.'],'views':[]}
bm.to_mesh(body.data);bm.free();body.data.update()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'failed-source-prefix.blend'))
bpy.ops.export_scene.gltf(filepath=str(RUN/'failed-source-prefix.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
forensic['rawGeometryOutputs']={str(p):sha(p) for p in [RUN/'failed-source-prefix.blend',RUN/'failed-source-prefix.glb']}
# Render-only neutral-gray source with exact selected source edge circuit in red.
gray=bpy.data.materials.new('Gray diagnostic only');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  o.data.materials.append(gray);index=len(o.data.materials)-1
  for p in o.data.polygons:p.material_index=index
red=bpy.data.materials.new('Exact selected seam diagnostic red');red.diffuse_color=(.65,.015,.01,1);red.use_nodes=True;red.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.65,.015,.01,1)
curve=bpy.data.curves.new('Actual selected source edge circuit','CURVE');curve.dimensions='3D';curve.bevel_depth=.0018;curve.bevel_resolution=1;poly=curve.splines.new('POLY');poly.points.add(len(seam)-1)
# Saved mesh retains source post-mask vertex ordering; the seam remains untouched.
for point,idx in zip(poly.points,forensic['seamSourceVertexIndices']):point.co=(*body.data.vertices[idx].co,1)
poly.use_cyclic_u=True;curve.materials.append(red);obj=bpy.data.objects.new(curve.name,curve);bpy.context.scene.collection.objects.link(obj)
scene=bpy.context.scene
for o in list(scene.objects):
 if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
world=bpy.data.worlds.new('Common gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=4;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.58))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Seam forensic');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);scene.camera=cam;data.type='ORTHO';data.ortho_scale=.5
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
for label,yaw in [('front',0),('profile',90),('rear',180),('three-quarter',45)]:
 target=Vector((0,.015,1.58));angle=math.radians(yaw);cam.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),.08));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();path=OUT/f'failed-seam-{label}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);forensic['views'].append({'label':label,'path':str(path),'sha256':sha(path)})
forensic['CPUSettings']={'threads':2,'device':'CPU','samples':16,'resolution':[640,640]}
assert report['inputs']=={p:sha(Path(p)) for p in report['inputs']}
(OUT/'forensic.json').write_text(json.dumps(forensic,indent=2)+'\n');print('EXACT_FORENSIC_FROZEN',json.dumps({k:forensic[k] for k in ['floodFaces','postMaskSourceFaces','floodIncludesSeamBothSides']}),flush=True)
