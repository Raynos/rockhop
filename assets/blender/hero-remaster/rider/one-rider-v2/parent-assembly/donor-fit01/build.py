"""Private complete WHITE rider fitting; no accepted rig or player asset."""
import bpy,json,numpy as np,math,hashlib,collections,time
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
R=ROOT/'parent-assembly/donor-fit01';R.mkdir(parents=True,exist_ok=True)
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/parent-assembly/donor-fit01');O.mkdir(parents=True,exist_ok=True)
bodySource=ROOT/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';hoodSource=ROOT/'autonomous-lanes/C-garment-pattern/wholehood01-anatomical-trial02/anatomical-source-hood.glb';headSource=ROOT/'autonomous-lanes/A-new-head-audit/skin-response05/model.glb';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sourceProof={str(p):sha(p) for p in [bodySource,hoodSource,headSource]}
d=np.load(ROOT/'autonomous-lanes/B-local-volume/clean-construction/trial01/fresh-wholehood-exclusion.npz')
def boundary(v,f):
 unique,inv=np.unique(v,axis=0,return_inverse=True);_,first=np.unique(v,axis=0,return_index=True);q=inv[f];edges=np.concatenate([q[:,[0,1]],q[:,[1,2]],q[:,[2,0]]]);u,c=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True);oriented=[tuple(map(int,e)) for e in edges if tuple(sorted(e)) in {tuple(x) for x in u[c==1]}];nxt={a:b for a,b in oriented};assert len(nxt)==len(oriented),'Branched directed seam';seen=set();loops=[]
 for start in nxt:
  if start in seen:continue
  cur=start;seq=[]
  while cur not in seen:seen.add(cur);seq.append(int(first[cur]));cur=nxt[cur]
  assert cur==start;loops.append(np.asarray(seq))
 return loops
bpy.ops.wm.open_mainfile(filepath=str(bodySource));scene=bpy.context.scene;body=max((o for o in scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));mats=list(body.data.materials);uvNames=[x.name for x in body.data.uv_layers]
for o in list(scene.objects):
 if o!=body:bpy.data.objects.remove(o,do_unlink=True)
for mod in list(body.modifiers):body.modifiers.remove(mod)
bv=d['vertices'];bf=d['faces'];bodyUV=d['allTriangleUV'];bm=d['materialIndex'];bl=boundary(bv,bf);assert len(bl)==1;br=bl[0]
old=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(hoodSource));hood=next(o for o in scene.objects if o not in old and o.type=='MESH');hood.data.calc_loop_triangles();hv=np.asarray([hood.matrix_world@v.co for v in hood.data.vertices],np.float32);hf=np.asarray([t.vertices[:] for t in hood.data.loop_triangles],np.int32);hu=np.asarray([[hood.data.uv_layers.active.data[i].uv[:] for i in t.loops] for t in hood.data.loop_triangles],np.float32);hl=boundary(hv,hf);assert len(hl)==2
hr=min(hl,key=lambda a:float(hv[a,2].min()));hr=hr[::-1]
def start(v,ring):
 p=v[ring];i=int(np.argmin(np.abs(p[:,0])+.8*(p[:,1]-p[:,1].min())));return np.roll(ring,-i)
br=start(bv,br);hr=start(hv,hr)
def area(p):return np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
assert np.sign(area(bv[br]))==np.sign(area(hv[hr])),'Corresponding garment seams run opposite; no blind reversal'
verts=np.concatenate([bv,hv]);offset=len(bv);faces=list(bf)+list(hf+offset);uv0=list(bodyUV[0])+list(hu);uv1=list(bodyUV[1])+list(hu);mi=list(bm)+[len(mats)]*len(hf);mats.append(hood.data.materials[0]);bridgeUV=[np.zeros((3,2)) for _ in faces]
bridge=bpy.data.materials.new('NEW continuous garment join');bridge.use_nodes=True;p=bridge.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.48,.29,.12,1);p.inputs['Roughness'].default_value=.8;mats.append(bridge);bridgeIndex=len(mats)-1
arc=lambda p:np.r_[0,np.cumsum(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1))]
a=arc(bv[br]);a/=a[-1];b=arc(hv[hr]);b/=b[-1];i=j=0;added=0;skipped=0
while i<len(br) or j<len(hr):
 ac=int(br[i%len(br)]);bc=int(hr[j%len(hr)])+offset
 if j==len(hr) or (i<len(br) and a[i+1]<b[j+1]):ids=[int(br[(i+1)%len(br)]),ac,bc];uv=[(a[i+1],0),(a[i],0),(b[j],1)];i+=1
 else:ids=[ac,bc,int(hr[(j+1)%len(hr)])+offset];uv=[(a[i],0),(b[j],1),(b[j+1],1)];j+=1
 q=verts[ids]
 if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-12:skipped+=1;continue
 faces.append(ids);uv0.append(np.zeros((3,2)));uv1.append(np.zeros((3,2)));mi.append(bridgeIndex);bridgeUV.append(np.asarray(uv));added+=1
mesh=bpy.data.meshes.new('Protected body NEW hood joined garment');mesh.from_pydata(verts.tolist(),[],faces);mesh.update()
for m in mats:mesh.materials.append(m)
for polygon,index in zip(mesh.polygons,mi):polygon.material_index=int(index);polygon.use_smooth=True
for name,data in zip(uvNames+['GarmentJoinUV'],[uv0,uv1,bridgeUV]):
 layer=mesh.uv_layers.new(name=name)
 for polygon,tuv in zip(mesh.polygons,data):
  for li,uv in zip(polygon.loop_indices,tuv):layer.data[li].uv=uv
body.data=mesh;body.matrix_world=Matrix.Identity(4);body.name='NEW protected body and connected donorhood, static'
for o in list(scene.objects):
 if o!=body:bpy.data.objects.remove(o,do_unlink=True)
old=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(headSource));headObjects=[o for o in scene.objects if o not in old];adapter=Matrix.Translation((.0030476976323250858,.00262536417545427,1.595431884660573))@Matrix.Diagonal((.2002282143246857,)*3+(1,))@Matrix.Rotation(math.pi,4,'X')
for obj in headObjects:
 if obj.parent is None:obj.matrix_world=adapter@obj.matrix_world
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(R/'rider.blend'));bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for obj in headObjects:obj.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(R/'rider.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False)
protected=d['faceOrigin']>=0;assert np.sum(protected)==40386;assert np.array_equal(np.asarray([tuple(v.co) for v in mesh.vertices[:len(bv)]],np.float32),bv)
report={'status':'Private static fitting, UNACCEPTED','bodyProtectedTriangles':40386,'bodyUVsAndMaterialsPreserved':True,'hoodNativeTriangles':len(hf),'bodySeamVertices':len(br),'hoodLowerSeamVertices':len(hr),'newBridgeTriangles':added,'skippedZeroAreaBridgeTriangles':skipped,'headAdapter':[list(row) for row in adapter],'sizing':'Provisional65mmIPD/eyeZ1.670/crown1.796, uniform no warping','sources':sourceProof,'sourcesAfter':{p:sha(p) for p in sourceProof},'outputGLBSHA256':sha(R/'rider.glb'),'limitations':['Bridge fabric is plain unbaked, sourcehood/body albedo may mismatch','Ambiguous donor innerfold preserved unchanged; actual assembled visibility must be inspected','No weights,19bonecontract,neckmotion or gameplay qualification','No playerassetpromotion']};assert report['sources']==report['sourcesAfter'];(O/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
