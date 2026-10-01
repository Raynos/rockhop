"""One local anatomical cheek reconstruction, immutable original GLB buffers.

Only source index occurrences in explicit cheek regions are replaced. Source
POSITION/NORMAL/UV/image payloads remain byte-identical in the final GLB. The
new patch is a continuous physical perimeter, not another front skin shell.
"""
import bpy,numpy as np,json,hashlib,struct,copy,math,collections,time
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.geometry import tessellate_polygon
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit')
G=R/'generation/h21-buzz-native01';T=R/'cheek-retopo01';T.mkdir(exist_ok=True)
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/cheek-retopo01')
source=G/'model.glb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (O/'repair-report.json').exists() or (T/'geometry.glb').exists():raise RuntimeError('Frozen repair trial exists')
sourceDigest=sha(source);rawBytes=source.read_bytes();jsonLength=struct.unpack_from('<I',rawBytes,12)[0];originalJSON=json.loads(rawBytes[20:20+jsonLength]);binaryStart=20+jsonLength+8;binary=rawBytes[binaryStart:];primitive=originalJSON['meshes'][0]['primitives'][0]
def accessor(n):
 a=originalJSON['accessors'][n];v=originalJSON['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
 return np.frombuffer(binary,dtype=dtype,count=a['count']*width,offset=offset).reshape(a['count'],width).copy()
sourcePositions=accessor(primitive['attributes']['POSITION']);sourceNormals=accessor(primitive['attributes']['NORMAL']);sourceUV=accessor(primitive['attributes']['TEXCOORD_0']);sourceTriangles=accessor(primitive['indices']).reshape(-1,3)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=obj.data
positions=np.array([tuple(v.co) for v in mesh.vertices],np.float32);triangles=np.array([list(p.vertices) for p in mesh.polygons],np.uint32)
assert np.array_equal(sourceTriangles,triangles),'Importer source triangle order changed'
assert np.array_equal(positions,np.stack((sourcePositions[:,0],-sourcePositions[:,2],sourcePositions[:,1]),axis=1)),'Source attribute frame not exact'
normalLocal=np.stack((sourceNormals[:,0],-sourceNormals[:,2],sourceNormals[:,1]),axis=1)
classification=json.loads((O/'classification.json').read_text());assert classification['sourceSHA256']==sourceDigest and classification['componentCount']==1
image=next(n.image for n in mesh.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.name=='textured');pixels=np.array(image.pixels[:],np.float64).reshape(image.size[1],image.size[0],4)
mrImage=next(n.image for n in mesh.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.name!='textured');mrPixels=np.array(mrImage.pixels[:],np.float64).reshape(mrImage.size[1],mrImage.size[0],4)
def sample(tex,uv):
 h,w=tex.shape[:2];x=np.clip(uv[:,0]*w-.5,0,w-1);y=np.clip(uv[:,1]*h-.5,0,h-1);ix=np.floor(x).astype(int);iy=np.floor(y).astype(int);jx=np.minimum(ix+1,w-1);jy=np.minimum(iy+1,h-1);fx=x-ix;fy=y-iy
 return (tex[iy,ix]*(1-fx)[:,None]+tex[iy,jx]*fx[:,None])*(1-fy)[:,None]+(tex[jy,ix]*(1-fx)[:,None]+tex[jy,jx]*fx[:,None])*fy[:,None]
positionIDs={};canonical=[];mapping=[];representative=[]
for i,p in enumerate(positions):
 key=tuple(p)
 if key not in positionIDs:positionIDs[key]=len(canonical);canonical.append(p);representative.append(i)
 mapping.append(positionIDs[key])
mapping=np.array(mapping);canonical=np.array(canonical);representative=np.array(representative);physicalFaces=mapping[triangles]
outer=sorted([c for c in classification['circuits'] if c['vertexCount']>=30],key=lambda c:c['positionBounds'][0][0]);assert len(outer)==2
centroids=positions[triangles].mean(1);removed=np.zeros(len(triangles),bool);regions=[]
for side,circuit in zip(['left','right'],outer):
 lo=np.array(circuit['positionBounds'][0]);hi=np.array(circuit['positionBounds'][1]);lo[:2]-=.025;hi[:2]+=.025;lo[2]-=.05;hi[2]+=.05
 chosen=np.all((centroids>=lo)&(centroids<=hi),axis=1);removed|=chosen;regions.append({'side':side,'sourceLocalBounds':[lo.tolist(),hi.tolist()],'selectedSourceFaceIndices':np.flatnonzero(chosen).tolist()})
assert all(removed[face] for c in classification['circuits'] for face in c['sourceFaces']),'Explicit regions do not contain every malformed boundary; do not widen'
incidence=collections.defaultdict(list)
for i in np.flatnonzero(~removed):
 tri=physicalFaces[i]
 for n in range(3):incidence[tuple(sorted((int(tri[n]),int(tri[(n+1)%3]))))].append(i)
boundary={edge:faces for edge,faces in incidence.items() if len(faces)==1};adj=collections.defaultdict(list)
for a,b in boundary:adj[a].append(b);adj[b].append(a)
if any(len(v)!=2 for v in adj.values()):
 (O/'unsafe-prefix.json').open('x').write(json.dumps({'reason':'Local removal does not yield degree-two physical perimeter','regions':regions,'boundaryDegreeCounts':dict(collections.Counter(len(v) for v in adj.values()))},indent=2)+'\n');raise RuntimeError('Unsafe local perimeter; no patch constructed')
unseen=set(boundary);loops=[]
while unseen:
 seed=next(iter(unseen));walk=[seed[0]];current=seed[0];previous=None
 for _ in range(len(boundary)+1):
  nxt=next(v for v in adj[current] if v!=previous);unseen.discard(tuple(sorted((current,nxt))));previous,current=current,nxt
  if current==walk[0]:break
  walk.append(current)
 else:raise RuntimeError('Unclosed local perimeter')
 loops.append(walk)
if len(loops)!=2:
 (O/'unsafe-prefix.json').open('x').write(json.dumps({'reason':'Region removal does not leave exactly one perimeter per cheek','regions':regions,'perimeterCounts':[len(v) for v in loops]},indent=2)+'\n');raise RuntimeError('Unsafe local perimeter count; no patch constructed')
loops.sort(key=lambda ring:float(canonical[ring,0].mean()));patches=[]
for k,(region,ring) in enumerate(zip(regions,loops)):
 p=canonical[ring].copy();centre=p[:,:2].mean(0);extent=np.ptp(p[:,:2],axis=0)
 assert np.all(extent>0) and all(tuple(v) not in {tuple(u) for u in p[:i,:2]} for i,v in enumerate(p[:,:2])),'Overlapping projected perimeter'
 # Discrete source skin ring plus retained nearby anatomical samples only.
 lo,hi=np.array(region['sourceLocalBounds']);expandedLo=lo.copy();expandedHi=hi.copy();expandedLo[:2]-=.035;expandedHi[:2]+=.035
 near=np.all((positions>=expandedLo)&(positions<=expandedHi),axis=1)&~np.all((positions>=lo)&(positions<=hi),axis=1)
 indices=np.flatnonzero(near);assert len(indices)>=12,'Too few unaffected same-cheek samples'
 def features(xy):
  x,y=((xy-centre)/extent).T;return np.stack((np.ones(len(x)),x,y,x*x,x*y,y*y),axis=1)
 geometrySamples=np.concatenate((positions[indices],p));coeff=np.linalg.lstsq(features(geometrySamples[:,:2]),geometrySamples[:,2],rcond=None)[0]
 colorSamples=sample(pixels,sourceUV[indices])[:,:3];good=(colorSamples.mean(1)>.12)&(colorSamples.max(1)<.98)
 assert np.sum(good)>=12,'Insufficient unaffected skin colors'
 colorCoeff=np.linalg.lstsq(features(positions[indices[good],:2]),colorSamples[good],rcond=None)[0]
 roughness=float(np.median(sample(mrPixels,sourceUV[indices[good]])[:,1]))
 flat=[Vector((v[0],v[1],0)) for v in p];tess=tessellate_polygon([flat]);lookup={tuple(v):i for i,v in enumerate(flat)};vertices=list(p);vertexNormals=list(normalLocal[representative[ring]]);patchTriangles=[]
 for triangle in tess:
  ids=[lookup[tuple(v)] for v in triangle];a,b,c=p[ids];centrePoint=(a+b+c)/3;centrePoint[2]=float(features(centrePoint[None,:2])@coeff);centreID=len(vertices);vertices.append(centrePoint)
  x,y=(centrePoint[:2]-centre)/extent;dx=(coeff[1]+2*coeff[3]*x+coeff[4]*y)/extent[0];dy=(coeff[2]+coeff[4]*x+2*coeff[5]*y)/extent[1];normal=np.array((dx,dy,-1));normal/=np.linalg.norm(normal);vertexNormals.append(normal)
  for n in range(3):
   tri=[ids[n],ids[(n+1)%3],centreID];v=np.array(vertices)[tri];cross=np.cross(v[1]-v[0],v[2]-v[0]);assert np.linalg.norm(cross)>1e-12
   if cross[2]>0:tri.reverse()
   patchTriangles.append(tri)
 vertices=np.array(vertices,np.float32);normals=np.array(vertexNormals,np.float32);uv=(vertices[:,:2]-p[:,:2].min(0))/extent;uv[:,0]=(uv[:,0]*.46+.02+k*.5);uv[:,1]=uv[:,1]*.96+.02
 colors=np.clip(features(vertices[:,:2])@colorCoeff,np.quantile(colorSamples[good],.02,axis=0),np.quantile(colorSamples[good],.98,axis=0))
 patches.append({'vertices':vertices,'normals':normals,'uv':uv.astype(np.float32),'triangles':np.array(patchTriangles,np.uint32),'colors':colors,'roughness':roughness,'perimeterSourcePhysicalIDs':ring,'sourceLocalBounds':region['sourceLocalBounds'],'geometryFitCoefficients':coeff.tolist(),'colorFitCoefficients':colorCoeff.tolist(),'unaffectedAnatomicalColorSampleCount':int(np.sum(good)),'perimeterVertexCount':len(ring)})
report={'status':'UNACCEPTED local cheek repair attempt 1','defectID':'H21-cheekOpenings','repairAttempt':1,'sourceSHA256':sourceDigest,'recipeSHA256':sha(Path(__file__)),'classification':'One connected source component; both loops per cheek are local malformed front surface, not detached islands. Entire explicit region removed, leaving one shared perimeter per cheek.','regions':regions,'retainedSourceFaces':int(np.sum(~removed)),'removedSourceFaces':int(np.sum(removed)),'patches':[{key:value for key,value in p.items() if key not in ['vertices','normals','uv','triangles','colors']} for p in patches],'CPUThreads':2,'GPUJob':False}

def make_glb(path,texture=None):
 doc=copy.deepcopy(originalJSON);payload=bytearray(binary)
 def view(data):
  while len(payload)%4:payload.append(0)
  n=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(payload),'byteLength':len(data)});payload.extend(data);return n
 def acc(array,typ,component):
  n=len(doc['accessors']);doc['accessors'].append({'bufferView':view(array.tobytes()),'componentType':component,'count':len(array),'type':typ,**({'min':array.min(0).tolist(),'max':array.max(0).tolist()} if typ=='VEC3' else {})});return n
 kept=sourceTriangles[~removed].astype('<u4').reshape(-1,1);doc['meshes'][0]['primitives'][0]['indices']=acc(kept,'SCALAR',5125)
 material=copy.deepcopy(doc['materials'][0]);material['name']='Anatomically reconstructed cheek skin';material['pbrMetallicRoughness']={'baseColorFactor':[.55,.35,.28,1],'roughnessFactor':float(np.mean([p['roughness'] for p in patches])),'metallicFactor':0}
 if texture:
  imageID=len(doc['images']);doc['images'].append({'bufferView':view(texture.read_bytes()),'mimeType':'image/png','name':'CPU baked coherent cheek skin'});textureID=len(doc['textures']);doc['textures'].append({'source':imageID,'sampler':0});material['pbrMetallicRoughness']['baseColorFactor']=[1,1,1,1];material['pbrMetallicRoughness']['baseColorTexture']={'index':textureID}
 matID=len(doc['materials']);doc['materials'].append(material)
 for patch in patches:
  local=patch['vertices'];localNormals=patch['normals'];pos=np.stack((local[:,0],local[:,2],-local[:,1]),axis=1).astype('<f4');norm=np.stack((localNormals[:,0],localNormals[:,2],-localNormals[:,1]),axis=1).astype('<f4');indices=patch['triangles'].astype('<u4').reshape(-1,1)
  doc['meshes'][0]['primitives'].append({'attributes':{'POSITION':acc(pos,'VEC3',5126),'NORMAL':acc(norm,'VEC3',5126),'TEXCOORD_0':acc(patch['uv'].astype('<f4'),'VEC2',5126)},'indices':acc(indices,'SCALAR',5125),'material':matID})
 doc['buffers'][0]['byteLength']=len(payload);encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);payload+=b'\0'*((-len(payload))%4);data=struct.pack('<III',0x46546c67,2,12+8+len(encoded)+8+len(payload))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(payload),0x004e4942)+payload;path.open('xb').write(data)
 assert bytes(payload[:len(binary)])==binary,'Original attribute/image payload changed'
 return {'path':str(path),'SHA256':sha(path),'originalBinaryPrefixSHA256':hashlib.sha256(binary).hexdigest(),'sourceAttributesImagesCopiedByteForByte':True,'sourceNodeTransformsUnchanged':doc['nodes']==originalJSON['nodes'],'outsideTriangleIndicesByteIdentical':kept.tobytes()==sourceTriangles[~removed].astype('<u4').reshape(-1,1).tobytes()}

geometry=T/'geometry.glb';report['grayGeometry']=make_glb(geometry)
(O/'construction-prefix.json').open('x').write(json.dumps(report,indent=2)+'\n')

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
report['grayViews']=render(geometry,True,'actual-gray')
# New coherent UV atlas, deliberately baked from SAME anatomical cheek samples.
# No source atlas interpolation across disconnected chart islands.
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.samples=1
atlas=bpy.data.images.new('CPU reconstructed cheek skin atlas',width=1024,height=1024,alpha=True);atlas.colorspace_settings.name='sRGB';atlas.generated_color=(.3,.18,.12,1)
for k,patch in enumerate(patches):
 mesh=bpy.data.meshes.new('Explicit continuous cheek patch');mesh.from_pydata(patch['vertices'].tolist(),[],patch['triangles'].tolist());uv=mesh.uv_layers.new(name='Coherent cheek UV');color=mesh.color_attributes.new(name='AnatomicalSkinFit',type='FLOAT_COLOR',domain='POINT')
 for i,rgb in enumerate(patch['colors']):color.data[i].color=(*rgb,1)
 for loop in mesh.loops:uv.data[loop.index].uv=patch['uv'][loop.vertex_index]
 obj=bpy.data.objects.new('Isolated cheek bake '+str(k),mesh);scene.collection.objects.link(obj);mat=bpy.data.materials.new('CPU local skin reconstruction');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission');attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='AnatomicalSkinFit';mat.node_tree.links.new(attr.outputs['Color'],emission.inputs['Color']);mat.node_tree.links.new(emission.outputs[0],output.inputs['Surface']);dest=nodes.new('ShaderNodeTexImage');dest.image=atlas;nodes.active=dest;obj.data.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;scene.render.bake.use_clear=(k==0);scene.render.bake.margin=8;bpy.ops.object.bake(type='EMIT')
texture=T/'cheek-skin-albedo.png';atlas.filepath_raw=str(texture);atlas.file_format='PNG';atlas.save()
report['bake']={'method':'Actual Cycles CPU emission bake of coherent patch UVs, fitted linear colors from unaffected SAME anatomical cheek samples. No cross-chart nearest-color transfer.','atlas':str(texture),'SHA256':sha(texture),'size':[1024,1024],'CPUThreads':2,'sourceAtlasChanged':False}
final=T/'model.glb';report['finalModel']=make_glb(final,texture);report['PBRViews']=render(final,False,'actual-PBR');assert sha(source)==sourceDigest
report['sourceSHA256After']=sha(source);report['outsideSourceGeometryUVNormalsTexturePayloadExact']=True;report['limitations']=['Unaccepted static head derivative; parent alone judges anatomy/texture continuity.','Patch skin albedo reconstructs missing regions from local unaffected skin, not recovered detail.','No rig, neck motion, visible contacts or game asset promotion.','Original source attributes remain as unused retained vertices where local triangles were removed.']
(O/'repair-report.json').open('x').write(json.dumps(report,indent=2)+'\n');print('LOCAL_CHEEK_REPAIR_TRIAL_FROZEN',flush=True)
