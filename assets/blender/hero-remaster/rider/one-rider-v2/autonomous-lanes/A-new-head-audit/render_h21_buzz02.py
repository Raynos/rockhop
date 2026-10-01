"""One frozen NEW H21 buzz source audit: exact native raw vs reduced vs PBR.

Read-only original assets, CPU two threads. Geometry-derived frame guard prevents
silently scoring an inverted H21 importer frame. No join/rig/asset promotion.
"""
import bpy,numpy as np,json,hashlib,math,time,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit');G=R/'generation/h21-buzz-native01'
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (O/'render-audit02.json').exists():raise RuntimeError('Frozen generated source audit exists')
proof=json.loads((O/'model-source-freeze.json').read_text());assert proof['completeWorkerReceipt']['exitCode']==0
for path,digest in proof['inputsSHA256'].items():assert sha(Path(path))==digest,'Frozen source changed'
start=time.perf_counter();report={'status':'UNACCEPTED actual completed H21 buzz source; parent scores', 'inputsSHA256':proof['inputsSHA256'],'recipeSHA256':sha(Path(__file__)),'CPUThreads':2,'visibleRiderContacts':'UNMEASURED','rig':'NONE','views':[]}

def import_mesh(path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update()
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 assert meshes and not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
 points=np.concatenate([np.array([o.matrix_world@v.co for v in o.data.vertices],np.float32) for o in meshes])
 return meshes,points

# Painted face is independent of raw importer triangle validation.
data=np.load(G/'raw-shape.npz');raw=data['vertices'];faces=data['faces']
assert np.isfinite(raw).all() and faces.min()>=0 and faces.max()<len(raw)
expected=np.stack((raw[:,0],-raw[:,2],raw[:,1]),axis=1).astype(np.float32)
forensic=json.loads((O/'raw-index-forensic.json').read_text())
for path,digest in forensic['inputsSHA256'].items():assert sha(Path(path))==digest
assert forensic['rawGLBIndicesEqualNativeNPZ'] and forensic['triangleCountDifference']==8 and forensic['missingFaceZeroAreaCount']==8 and forensic['missingFaceRepeatedVertexIndexCount']==8
report['preReductionSource']={'NPZSHA256':sha(G/'raw-shape.npz'),'GLBSHA256':sha(G/'raw-shape.glb'),'nativeVertices':len(raw),'nativeTriangles':len(faces),'rawGLBIndexPayloadPreservesAllNativeTriangles':True,'byteIndexProof':str(O/'raw-index-forensic.json'),'sourceGLBVerticesProof':None,'BlenderRenderExclusions':None}
# The reducer file is the exact geometry handed to the painter.
reducedMeshes,reducedWorld=import_mesh(G/'shape.glb');tree=KDTree(len(reducedWorld))
for i,p in enumerate(reducedWorld):tree.insert(p,i)
tree.balance();paintMeshes,paintWorld=import_mesh(G/'model.glb')
testTransforms=[('identity',Matrix.Identity(4)),('X90',Matrix.Rotation(math.pi/2,4,'X')),('X180',Matrix.Rotation(math.pi,4,'X')),('X270',Matrix.Rotation(3*math.pi/2,4,'X'))]
frameTests=[]
for name,matrix in testTransforms:
 distances=[tree.find(matrix@Vector(p))[2] for p in paintWorld]
 frameTests.append({'name':name,'maximumNearestSourceVertexDistanceM':max(distances),'RMSNearestSourceVertexDistanceM':float(np.sqrt(np.mean(np.square(distances)))),'matrix':[list(r) for r in matrix]})
chosen=min(frameTests,key=lambda row:row['RMSNearestSourceVertexDistanceM']);assert chosen['maximumNearestSourceVertexDistanceM']<5e-6,'No exact frozen reducer-to-painted export frame found; stop'
paintMatrix=Matrix(chosen['matrix']);report['paintedFrameGuard']={'candidates':frameTests,'chosen':chosen,'meaning':'Exact preserved reduced geometry positions determine importer frame; no sculpt/axis guessing or visual score.'}
# One shared display normalization from original raw geometry (not each variant).
lo=expected.min(0);hi=expected.max(0);roi=expected[expected[:,2]>=hi[2]-(hi[2]-lo[2])*.45];rlo=roi.min(0);rhi=roi.max(0);centre=(rlo+rhi)/2;scale=.20/float(rhi[0]-rlo[0]);translation=-centre*scale+np.array([0,0,1.58]);normalizer=Matrix.Translation(Vector(translation))@Matrix.Diagonal((scale,scale,scale,1))
fullLo=lo*scale+translation;fullHi=hi*scale+translation;fullTarget=Vector((0,0,float((fullLo[2]+fullHi[2])/2)));fullScale=max(float(fullHi[2]-fullLo[2]),float(fullHi[0]-fullLo[0]))*1.22
report['display']={'rawBoundsBlenderM':[lo.tolist(),hi.tolist()],'rawHeadROIBoundsM':[rlo.tolist(),rhi.tolist()],'ROI':'Upper45% of original raw bust height, framing only','scale':scale,'translation':translation.tolist(),'sharedNormalization':True,'fullTarget':list(fullTarget),'fullOrthoScale':fullScale,'faceTarget':[0,0,1.58],'faceOrthoScale':.34}
views=[('front',0,0),('front-left',45,0),('left',90,0),('rear-left',135,0),('rear',180,0),('rear-right',225,0),('right',270,0),('front-right',315,0),('top-front',0,30)]
variants=[('painted-PBR02',G/'model.glb',paintMatrix,False),('raw-gray02',G/'raw-shape.glb',Matrix.Identity(4),True),('reduced-gray02',G/'shape.glb',Matrix.Identity(4),True),('painted-gray02',G/'model.glb',paintMatrix,True)]
for variant,path,frame,grayMode in variants:
 meshes,points=import_mesh(path)
 if variant=='raw-gray02':
  assert len(points)==len(expected)
  error=float(np.linalg.norm(points-expected,axis=1).max());assert error<2e-6
  importedTriangles=sum(len(o.data.polygons) for o in meshes)
  assert importedTriangles==forensic['BlenderImportedTriangles']==len(faces)-8
  report['preReductionSource'].update(sourceGLBVerticesProof={'orderedMaximumCoordinateErrorM':error},BlenderRenderExclusions={'sourceTriangles':len(faces),'actualRenderedTriangleCount':importedTriangles,'excludedExactlyZeroAreaTriangles':8,'sourceFaceIDs':forensic['sourceMissingFaceIDs'],'allOtherSourceOccurrencesPresent':True})
 scene=bpy.context.scene;parent=bpy.data.objects.new('Read-only matched raw frame',None);scene.collection.objects.link(parent)
 roots=[o for o in scene.objects if o.parent is None and o!=parent]
 for obj in roots:original=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=original
 parent.matrix_world=normalizer@frame;bpy.context.view_layer.update()
 materialRows=[]
 for obj in meshes:
  materialRows.append({'mesh':obj.name,'vertices':len(obj.data.vertices),'triangles':len(obj.data.polygons),'materials':[m.name if m else None for m in obj.data.materials],'imageTextures':[{'material':m.name,'image':n.image.name,'size':list(n.image.size)} for m in obj.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]})
 if grayMode:
  gray=bpy.data.materials.new('Actual geometry neutral gray');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
  for obj in meshes:
   obj.data.materials.append(gray);index=len(obj.data.materials)-1
   for p in obj.data.polygons:p.material_index=index;p.use_smooth=True
 world=bpy.data.worlds.new('Common gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
 for name,position,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=position;o.rotation_euler=(Vector((0,0,1.58))-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('Matched actual source');camera=bpy.data.objects.new(d.name,d);scene.collection.objects.link(camera);scene.camera=camera;d.type='ORTHO'
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
 directory=O/variant;directory.mkdir(exist_ok=True);rendered=[]
 # Actual face first, so parent can judge before full-nine inspection finishes.
 for scope,selected,target,ortho in [('face',[('front',0,0),('profile',90,0),('three-quarter',45,0),('rear',180,0)],Vector((0,0,1.58)),.34),('nine',views,fullTarget,fullScale)]:
  for label,yaw,elevation in selected:
   a=math.radians(yaw);e=math.radians(elevation);camera.location=target+Vector((4*math.sin(a)*math.cos(e),-4*math.cos(a)*math.cos(e),4*math.sin(e)));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=ortho;p=directory/f'{scope}-{label}.png';scene.render.filepath=str(p);t=time.perf_counter();bpy.ops.render.render(write_still=True);row={'scope':scope,'view':label,'yaw':yaw,'elevation':elevation,'path':str(p),'SHA256':sha(p),'target':list(target),'orthoScale':ortho,'cameraMatrix':[list(r) for r in camera.matrix_world],'wallSeconds':time.perf_counter()-t};rendered.append(row);report['views'].append({'variant':variant,**row})
   (O/'render-progress02.json').write_text(json.dumps({'status':'Actual CPU renders in progress; no appearance acceptance','lastCompleted':{'variant':variant,'scope':scope,'view':label,'path':str(p)}},indent=2)+'\n')
 (directory/'manifest.json').write_text(json.dumps({'status':'UNACCEPTED standalone NEW bust, no rider/rig','source':str(path),'sourceSHA256':sha(path),'sourceFrame':[list(r) for r in frame],'sharedDisplay':report['display'],'materialsBeforeDiagnostic':materialRows,'grayMode':grayMode,'views':rendered},indent=2)+'\n')
for path,digest in proof['inputsSHA256'].items():assert sha(Path(path))==digest,'Frozen source changed during rendering'
report['sourcesUnchanged']=True;report['wallSeconds']=time.perf_counter()-start;report['parentFaceScore']=None;report['limits']=['Unrigged separate NEW bust, not game-ready or appearance accepted.','Raw shape contains all saved source triangles; no cleanup or retopology.','Reference likeness/eyes/brows/stubble/skin/buzz judged visually by parent, not triangle count.','Gray material/smooth shading diagnostic only; no source material/UV changes saved.','Original comparison and historical controls untouched.']
(O/'render-audit02.json').write_text(json.dumps(report,indent=2)+'\n');print('GENERATED_BUZZ_AUDIT_FROZEN',len(report['views']),flush=True)
