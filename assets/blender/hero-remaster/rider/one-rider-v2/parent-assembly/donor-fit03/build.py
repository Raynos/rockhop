"""Private complete WHITE rider fitting; no accepted rig or player asset."""
import bpy,json,numpy as np,math,hashlib,collections,time
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
R=ROOT/'parent-assembly/donor-fit03';R.mkdir(parents=True,exist_ok=True)
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/parent-assembly/donor-fit03');O.mkdir(parents=True,exist_ok=True)
bodySource=ROOT/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';hoodSource=ROOT/'autonomous-lanes/C-garment-pattern/wholehood01-anatomical-trial02/anatomical-source-hood.glb';headSource=ROOT/'autonomous-lanes/A-new-head-audit/skin-response05/model.glb';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sourceProof={str(p):sha(p) for p in [bodySource,hoodSource,headSource]}
d=np.load(ROOT/'autonomous-lanes/B-local-volume/clean-construction/trial01/fresh-wholehood-exclusion.npz')
def boundary(v,f):
 unique,inv=np.unique(v,axis=0,return_inverse=True);_,first=np.unique(v,axis=0,return_index=True);q=inv[f];edges=np.concatenate([q[:,[0,1]],q[:,[1,2]],q[:,[2,0]]]);u,c=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True);boundarySet={tuple(x) for x in u[c==1]};oriented=[tuple(map(int,e)) for e in edges if tuple(sorted(e)) in boundarySet];nxt={a:b for a,b in oriented};assert len(nxt)==len(oriented),'Branched directed seam';seen=set();loops=[]
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
# Fit ONLY the NEW donor's lower skirt to the untouched shirt boundary.
import heapq
def planar_arc(p):
 a=np.r_[0,np.cumsum(np.linalg.norm(np.roll(p[:,:2],-1,axis=0)-p[:,:2],axis=1))];return a/a[-1]
ba=planar_arc(bv[br])[:-1];ha=planar_arc(hv[hr])[:-1];delta=np.abs(ha[:,None]-ba[None,:]);delta=np.minimum(delta,1-delta);matching=np.argmin(delta,axis=1);target=bv[br[matching]];displacements=target-hv[hr]
originalHood=hv.copy();canonical,first,inverse=np.unique(hv,axis=0,return_index=True,return_inverse=True);graph=[{} for _ in canonical]
for triangle in inverse[hf]:
 for i in range(3):
  a=int(triangle[i]);b=int(triangle[(i+1)%3]);length=float(np.linalg.norm(canonical[a]-canonical[b]));graph[a][b]=length;graph[b][a]=length
D=np.full(len(canonical),np.inf);label=np.full(len(canonical),-1);heap=[]
for k,v in enumerate(inverse[hr]):D[v]=0;label[v]=k;heapq.heappush(heap,(0,int(v)))
while heap:
 distance,v=heapq.heappop(heap)
 if distance!=D[v]:continue
 for w,length in graph[v].items():
  candidate=distance+length
  if candidate<D[w]:D[w]=candidate;label[w]=label[v];heapq.heappush(heap,(candidate,w))
band=.065;weight=np.zeros(len(canonical));inside=D<band;t=D[inside]/band;weight[inside]=1-t*t*(3-2*t);move=np.zeros_like(canonical);move[inside]=displacements[label[inside]]*weight[inside,None];hv=(hv+move[inverse]).astype(np.float32)
assert np.array_equal(hv[~inside[inverse]],originalHood[~inside[inverse]]),'Far hood changed'
q=hv[hf];areas=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1);keep=areas>1e-12;removedHoodDegenerates=int(np.sum(~keep));assert all(np.all(inside[inverse[tri]]) for tri in hf[~keep]);hf=hf[keep];hu=hu[keep]
hl=boundary(hv,hf);assert len(hl)==2,'Local skirt fitting changed neck/attachment loop count';hr=start(hv,min(hl,key=lambda a:float(hv[a,2].min()))[::-1]);hoodFit={'method':'65mmgeodesic lower NEWhood skirt band, monotonebody-seam correspondence; outsidebandexact','bandM':band,'boundaryTargets':len(matching),'maximumBoundaryDisplacement':float(np.linalg.norm(displacements,axis=1).max()),'movedPhysicalVertices':int(np.sum(inside)),'removedNewLocalZeroAreaTriangles':removedHoodDegenerates,'remainingHoodTriangles':len(hf)}
verts=np.concatenate([bv,hv]);offset=len(bv);faces=list(bf)+list(hf+offset);uv0=list(bodyUV[0])+list(hu);uv1=list(bodyUV[1])+list(hu);mi=list(bm)+[len(mats)]*len(hf);mats.append(hood.data.materials[0]);bridgeUV=[np.zeros((3,2)) for _ in faces]
bridge=bpy.data.materials.new('NEW continuous garment join');bridge.use_nodes=True;p=bridge.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.48,.29,.12,1);p.inputs['Roughness'].default_value=.8;mats.append(bridge);bridgeIndex=len(mats)-1
arc=lambda p:np.r_[0,np.cumsum(np.linalg.norm(np.roll(p[:,:2],-1,axis=0)-p[:,:2],axis=1))]
a=arc(bv[br]);a/=a[-1];b=arc(hv[hr]);b/=b[-1];i=j=0;added=0;skipped=0
while i<len(br) or j<len(hr):
 ac=int(br[i%len(br)]);bc=int(hr[j%len(hr)])+offset
 if j==len(hr) or (i<len(br) and a[i+1]<b[j+1]):ids=[int(br[(i+1)%len(br)]),ac,bc];uv=[(a[i+1],0),(a[i],0),(b[j],1)];i+=1
 else:ids=[ac,bc,int(hr[(j+1)%len(hr)])+offset];uv=[(a[i],0),(b[j],1),(b[j+1],1)];j+=1
 q=verts[ids]
 if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-12:skipped+=1;continue
 faces.append(ids);uv0.append(np.zeros((3,2)));uv1.append(np.zeros((3,2)));mi.append(bridgeIndex);bridgeUV.append(np.asarray(uv));added+=1
# Direct original source corner texels constrain the NEW transition colors.
def albedo_image(mat):
 p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');seen=set()
 def walk(socket):
  for link in socket.links:
   node=link.from_node
   if node.as_pointer() in seen:continue
   seen.add(node.as_pointer())
   if node.type=='TEX_IMAGE' and node.image:return node.image
   for inp in node.inputs:
    image=walk(inp)
    if image:return image
 return walk(p.inputs['Base Color'])
def sample(image,uv):
 a=np.asarray(image.pixels[:],np.float64).reshape(image.size[1],image.size[0],4);x=np.clip(uv[:,0]*image.size[0]-.5,0,image.size[0]-1);y=np.clip(uv[:,1]*image.size[1]-.5,0,image.size[1]-1);i=np.floor(x).astype(int);j=np.floor(y).astype(int);ii=np.minimum(i+1,image.size[0]-1);jj=np.minimum(j+1,image.size[1]-1);fx=x-i;fy=y-j;rgb=((1-fx)[:,None]*(1-fy)[:,None]*a[j,i,:3]+fx[:,None]*(1-fy)[:,None]*a[j,ii,:3]+(1-fx)[:,None]*fy[:,None]*a[jj,i,:3]+fx[:,None]*fy[:,None]*a[jj,ii,:3]);return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4) if image.colorspace_settings.name=='sRGB' else rgb
bodyImage=albedo_image(mats[0]);hoodImage=albedo_image(mats[2]);assert bodyImage and hoodImage
bc=sample(bodyImage,bodyUV[0].reshape(-1,2));hc=sample(hoodImage,hu.reshape(-1,2));sums=np.zeros((len(verts),3));counts=np.zeros(len(verts));np.add.at(sums,bf.reshape(-1),bc);np.add.at(counts,bf.reshape(-1),1);np.add.at(sums,(hf+offset).reshape(-1),hc);np.add.at(counts,(hf+offset).reshape(-1),1);endpointColor=sums/np.maximum(counts,1)[:,None];originalFaces=np.asarray(faces,np.int32);bridgeColors=endpointColor[originalFaces[len(bf)+len(hf):]]
# Exact-coordinate weld with per-corner UVs/materials retained; remove unused source points.
originalVerts=verts.copy();used=np.unique(originalFaces);verts,canonical=np.unique(originalVerts[used],axis=0,return_inverse=True);mapping=np.full(len(originalVerts),-1,dtype=np.int32);mapping[used]=canonical;faces=mapping[originalFaces];assert np.array_equal(verts[faces[:len(bf)]],bv[bf])
for mat in [mats[0],mats[2],mats[3]]:
 p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 for name,value in [('Roughness',.75),('Metallic',0),('Specular IOR Level',.125),('Specular Tint',(1,1,1,1))]:
  if name not in p.inputs:continue
  for link in list(p.inputs[name].links):mat.node_tree.links.remove(link)
  p.inputs[name].default_value=value
attr=mats[3].node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='JoinAlbedo';p=next(n for n in mats[3].node_tree.nodes if n.type=='BSDF_PRINCIPLED');mats[3].node_tree.links.new(attr.outputs['Color'],p.inputs['Base Color'])
mesh=bpy.data.meshes.new('Protected body NEW hood joined garment');mesh.from_pydata(verts.tolist(),[],faces);mesh.update()
for m in mats:mesh.materials.append(m)
for polygon,index in zip(mesh.polygons,mi):polygon.material_index=int(index);polygon.use_smooth=True
for name,data in zip(uvNames+['GarmentJoinUV'],[uv0,uv1,bridgeUV]):
 layer=mesh.uv_layers.new(name=name)
 for polygon,tuv in zip(mesh.polygons,data):
  for li,uv in zip(polygon.loop_indices,tuv):layer.data[li].uv=uv
color=mesh.color_attributes.new(name='JoinAlbedo',type='FLOAT_COLOR',domain='CORNER')
for entry in color.data:entry.color=(1,1,1,1)
for polygon,colors in zip(list(mesh.polygons)[len(bf)+len(hf):],bridgeColors):
 for li,rgb in zip(polygon.loop_indices,colors):color.data[li].color=(*rgb,1)
body.data=mesh;body.matrix_world=Matrix.Identity(4);body.name='NEW protected body and connected donorhood, static'
for o in list(scene.objects):
 if o!=body:bpy.data.objects.remove(o,do_unlink=True)
old=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(headSource));headObjects=[o for o in scene.objects if o not in old];adapter=Matrix.Translation((.0030476976323250858,.00262536417545427,1.595431884660573))@Matrix.Diagonal((.2002282143246857,)*3+(1,))@Matrix.Rotation(math.pi,4,'X')
for obj in headObjects:
 if obj.parent is None:obj.matrix_world=adapter@obj.matrix_world
bpy.context.view_layer.update();baseFit=[]
for obj in headObjects:
 if obj.type!='MESH':continue
 inverse=obj.matrix_world.inverted();moved=0;maximum=0;protectedBefore=[tuple(v.co) for v in obj.data.vertices if (obj.matrix_world@v.co).z>=1.52]
 for v in obj.data.vertices:
  world=obj.matrix_world@v.co
  if world.z>=1.52:continue
  t=min(1,max(0,(world.z-1.44)/.08));factor=.75+.25*t*t*(3-2*t);fitted=Vector((world.x*factor,world.y*factor,world.z));maximum=max(maximum,(fitted-world).length);v.co=inverse@fitted;moved+=1
 assert protectedBefore==[tuple(v.co) for v in obj.data.vertices if (obj.matrix_world@v.co).z>=1.52]
 obj.data.update();baseFit.append({'object':obj.name,'movedLowerBustVertices':moved,'maximumWorldDisplacement':maximum,'faceAboveZ1_52Exact':True})
bpy.ops.wm.save_as_mainfile(filepath=str(R/'rider.blend'));bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for obj in headObjects:obj.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(R/'rider.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False)
protected=d['faceOrigin']>=0;assert np.sum(protected)==40386;assert np.array_equal(np.asarray([tuple(v.co) for v in mesh.vertices],np.float32)[faces[:len(bf)]],bv[bf])
report={'status':'Private static fitting, UNACCEPTED','bodyProtectedTriangles':40386,'bodyTriangleUVsAndMaterialAssignmentsPreserved':True,'hoodSourceTrianglesRetained':len(hf),'hoodFit':hoodFit,'bodySeamVertices':len(br),'hoodLowerSeamVertices':len(hr),'newBridgeTriangles':added,'exactCoordinateGarmentWeld':True,'garmentUsedVertexCount':len(verts),'baseFit':baseFit,'bridgeAlbedo':'Direct SAME source cornertexels, sRGB decoded, CORNER vertexcolors; no arbitraryUV chart interpolation','clothPBR':'Nonmetal, roughness.75/specular.25 coherent response, original maps retained unused','skippedZeroAreaBridgeTriangles':skipped,'headAdapter':[list(row) for row in adapter],'sizing':'Initialuniform65mmIPDfit; only lowerhiddenbustbase tapered belowZ1.52, faceexact','sources':sourceProof,'sourcesAfter':{p:sha(p) for p in sourceProof},'outputGLBSHA256':sha(R/'rider.glb'),'limitations':['Corner-color transition carries original endtexels but no microfabric detail; actual match needs review','Ambiguous donor innerfold preserved unchanged; actual assembled visibility must be inspected','No weights,19bonecontract,neckmotion or gameplay qualification','No playerassetpromotion']};assert report['sources']==report['sourcesAfter'];(O/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
