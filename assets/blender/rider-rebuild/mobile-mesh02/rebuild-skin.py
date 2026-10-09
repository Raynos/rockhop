"""Exact selected boot/glove only: local-coordinate reduction, fresh UV, actual bake.

Native GLB coordinates remain unchanged; this does not import or export a rig.
The source corner normals, material images and source skin joint order are read
from the pinned GLB extraction. Outputs are experiments, never player assets.
"""
import bpy, numpy as np, json, sys, time, math, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
MODE,IN,OUT,REDUCED=sys.argv[sys.argv.index('--')+1:]
REDUCED=Path(REDUCED).resolve()
IN,OUT=Path(IN).resolve(),Path(OUT).resolve();OUT.mkdir(parents=True,exist_ok=True)

def log(s): print(s,flush=True)
def read(name,dtype,width):return np.fromfile(IN/(name+'.bin'),dtype=dtype).reshape(-1,width)
def arr(items,field,width,dtype=np.float32):
 a=np.empty((len(items),width),dtype);items.foreach_get(field,a.ravel());return a

def bary(p,a,b,c):
 v0=b-a;v1=c-a;v2=p-a;d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1
 den=d00*d11-d01*d01
 if abs(den)<1e-30:return np.array([1,0,0],np.float64)
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den
 q=np.clip([1-v-w,v,w],0,1);return q/q.sum()
def stats(a):
 a=np.asarray(a);return dict(mean=float(a.mean()),p95=float(np.quantile(a,.95)),p99=float(np.quantile(a,.99)),max=float(a.max()))
def mesh_object(name,pos,tri):
 m=bpy.data.meshes.new(name);m.from_pydata(pos.tolist(),[],tri.tolist());m.update()
 o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return o

def prepare():
 start=time.monotonic();bpy.ops.wm.read_factory_settings(use_empty=True)
 source_meta=json.loads((IN/'intake.json').read_text());assert source_meta['sha256']=='127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649'
 sp=read('POSITION','<f4',3);sn=read('NORMAL','<f4',3);su=read('TEXCOORD_0','<f4',2);si=read('indices','<u4',3)
 sj=read('JOINTS_0','u1',4);sw=read('WEIGHTS_0','<f4',4);native=read('_NATIVE_ID','<f4',1)
 unique,first,inverse=np.unique(sp,axis=0,return_index=True,return_inverse=True);faces=inverse[si]
 assert np.array_equal(sj,sj[first][inverse]),'Refuse welding different source joint tuples'
 assert np.array_equal(sw,sw[first][inverse]),'Refuse welding different source weights'
 log(f'Exact source {len(sp)} export vertices -> {len(unique)} unique positions; {len(faces)} triangles')
 high=mesh_object('ExactSelectedComponentDense',unique,faces)
 loops=si.ravel();uv=su[loops].copy();uv[:,1]=1-uv[:,1]
 high.data.uv_layers.new(name='ExactSelectedUV').data.foreach_set('uv',uv.ravel())
 high.data.polygons.foreach_set('use_smooth',np.ones(len(faces),bool))
 high.data.normals_split_custom_set(sn[loops].tolist());high.data.update()
 # Actual selected source images; no approximated material reconstruction.
 mat=bpy.data.materials.new('ExactSelectedPBR');mat.use_nodes=True;high.data.materials.append(mat)
 nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
 for kind in ('albedo','orm'):
  image=bpy.data.images.load(str(IN/(kind+'.png')),check_existing=False)
  image.colorspace_settings.name='sRGB' if kind=='albedo' else 'Non-Color'
  tex=nodes.new('ShaderNodeTexImage');tex.name=kind;tex.image=image;tex.interpolation='Linear'
  if kind=='albedo':links.new(tex.outputs['Color'],bs.inputs['Base Color'])
  else:
   split=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],split.inputs['Color'])
   links.new(split.outputs['Green'],bs.inputs['Roughness']);links.new(split.outputs['Blue'],bs.inputs['Metallic'])
 rp=np.fromfile(REDUCED/'POSITION.bin','<f4').reshape(-1,3);rf=np.fromfile(REDUCED/'indices.bin','<u4').reshape(-1,3)
 source_rows=np.fromfile(REDUCED/'source-row.u32','<u4')
 assert np.array_equal(rp,sp[source_rows]),'Retained positions must equal original native rows'
 low=mesh_object('AtlasReducedComponent',rp,rf)
 bpy.context.view_layer.objects.active=low;low.select_set(True)
 low.data.polygons.foreach_set('use_smooth',np.ones(len(low.data.polygons),bool));low.data.update()
 log(f'Reduced {len(low.data.polygons)} triangles {len(low.data.vertices)} vertices')
 low.data.uv_layers.new(name='SelectedComponentNewAtlas')
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.003,correct_aspect=True,scale_to_bounds=True)
 bpy.ops.object.mode_set(mode='OBJECT');log('Fresh unwrap complete')
 low.data.calc_loop_triangles();lp=arr(low.data.vertices,'co',3);lf=arr(low.data.loop_triangles,'vertices',3,np.int32)
 tree=BVHTree.FromPolygons(unique.tolist(),faces.tolist(),all_triangles=True)
 weights=np.zeros((len(lp),4),np.float32);joints=np.zeros((len(lp),4),np.uint8);native_ids=np.zeros((len(lp),1),np.float32)
 distances=[];closest_faces=np.zeros(len(lp),np.int32);bary_coords=np.zeros((len(lp),3),np.float32);skin_trunc=[]
 geom_owner=np.full(len(unique),len(si),np.int32)
 np.minimum.at(geom_owner,inverse[si.ravel()],np.repeat(np.arange(len(si),dtype=np.int32),3))
 for i,p in enumerate(lp):
  source_row=source_rows[i];face=int(geom_owner[inverse[source_row]]);assert face<len(si)
  rows=si[face];corner=int(np.argmin(np.linalg.norm(sp[rows]-p,axis=1)))
  assert np.array_equal(sp[rows[corner]],p),'Receiver must retain source vertex position'
  b=np.zeros(3,np.float32);b[corner]=1
  joints[i]=sj[source_row];weights[i]=sw[source_row];native_ids[i]=native[source_row]
  skin_trunc.append(0);closest_faces[i]=face;bary_coords[i]=b;distances.append(0)
 lowtree=BVHTree.FromPolygons(lp.tolist(),lf.tolist(),all_triangles=True)
 reverse=[]
 rng=np.random.default_rng(20261009)
 for face in rng.choice(len(faces),min(40000,len(faces)),replace=False):
  p=unique[faces[face]].mean(0);hit,_,f,d=lowtree.find_nearest(Vector(p));reverse.append(d)
 report={'source':source_meta,'coordinateAuthority':'Direct untransformed GLB local coordinates; no Blender importer or full rig exporter', 'sourceUniquePositions':len(unique),'sourceTriangles':len(faces),'targetVertices':len(lp),'targetTriangles':len(lf),'targetToSourceMeters':stats(distances),'sourceToTargetMeters':stats(reverse),'skinTransfer':'Meshopt retained exact original native vertex rows and four joint/weight slots; no interpolation or top4 discard. Source-corner provenance proves vertex identity; triangle interiors need independent posed comparison.', 'top4SkinDiscardedMass':stats(skin_trunc),'elapsedSeconds':time.monotonic()-start,'accepted':False}
 np.savez(OUT/'transfer.npz',joints=joints,weights=weights,native=native_ids,closestFaces=closest_faces,bary=bary_coords)
 (OUT/'prepare.json').write_text(json.dumps(report,indent=2)+'\n')
 bpy.context.scene.render.engine='CYCLES';bpy.context.scene.cycles.device='CPU';bpy.context.scene.cycles.samples=1
 bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=2
 high.select_set(False);low.select_set(False)
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'prepared.blend'));log(report)

def audit_fields(high,low,images,OUT):
 mat=high.data.materials[0];nodes=mat.node_tree.nodes
 # Quantify actual atlas fields at deterministic low triangle centroids.
 # This reports observed errors, including thin-wall/ray pairing and texel filtering.
 low.data.calc_loop_triangles();low.data.calc_tangents(uvmap='SelectedComponentNewAtlas')
 def pixels(image):
  a=np.empty(image.size[0]*image.size[1]*4,np.float32);image.pixels.foreach_get(a);return a.reshape(image.size[1],image.size[0],4)
 def sample(a,uv):
  h,w=a.shape[:2];q=np.asarray(uv)*[w,h]-.5;q%=np.array([w,h]);x,y=np.floor(q).astype(int);dx,dy=q-[x,y]
  return ((a[y%h,x%w]*(1-dx)+a[y%h,(x+1)%w]*dx)*(1-dy)+(a[(y+1)%h,x%w]*(1-dx)+a[(y+1)%h,(x+1)%w]*dx)*dy)[:3]
 hp=arr(high.data.vertices,'co',3);hf=arr(high.data.loop_triangles,'vertices',3,np.int32) if len(high.data.loop_triangles) else None
 high.data.calc_loop_triangles();hf=arr(high.data.loop_triangles,'vertices',3,np.int32);hl=arr(high.data.loop_triangles,'loops',3,np.int32)
 hn=arr(high.data.corner_normals,'vector',3);hu=arr(high.data.uv_layers.active.data,'uv',2)
 lp=arr(low.data.vertices,'co',3);lf=arr(low.data.loop_triangles,'vertices',3,np.int32);ll=arr(low.data.loop_triangles,'loops',3,np.int32)
 ln=arr(low.data.corner_normals,'vector',3);lu=arr(low.data.uv_layers.active.data,'uv',2);lt=arr(low.data.loops,'tangent',3);lb=arr(low.data.loops,'bitangent_sign',1)
 tree=BVHTree.FromPolygons(hp.tolist(),hf.tolist(),all_triangles=True)
 baked={k:pixels(v) for k,v in images.items()};original={k:pixels(nodes[k].image) for k in ('albedo','orm')}
 errors={'albedo':[],'orm':[],'normalDegrees':[]};probes=[]
 for f in np.random.default_rng(20261009).choice(len(lf),min(30000,len(lf)),replace=False):
  pos=lp[lf[f]].mean(0);hit,_,face,d=tree.find_nearest(Vector(pos));bc=bary(np.asarray(hit),*hp[hf[face]])
  srcuv=(hu[hl[face]]*bc[:,None]).sum(0);dstuv=lu[ll[f]].mean(0)
  for kind in ('albedo','orm'):errors[kind].append(float(np.abs(sample(original[kind],srcuv)-sample(baked[kind],dstuv)).mean()))
  normal=ln[ll[f]].mean(0);normal/=np.linalg.norm(normal);tangent=lt[ll[f]].mean(0);tangent-=normal*(normal@tangent);tangent/=np.linalg.norm(tangent)
  sign=np.sign(lb[ll[f]].mean());bitangent=np.cross(normal,tangent)*sign
  nm=sample(baked['normal'],dstuv)*2-1;world=tangent*nm[0]+bitangent*nm[1]+normal*nm[2];world/=np.linalg.norm(world)
  expected=(hn[hl[face]]*bc[:,None]).sum(0);expected/=np.linalg.norm(expected)
  angle=math.degrees(math.acos(float(np.clip(world@expected,-1,1))));errors['normalDegrees'].append(angle)
  if angle>15 or errors['albedo'][-1]>.05:
   rayhit,_,rayface,raydistance=tree.ray_cast(Vector(pos+normal*.003),Vector(-normal),.01)
   rayangle=None
   if rayhit is not None:
    raybc=bary(np.asarray(rayhit),*hp[hf[rayface]]);raynormal=(hn[hl[rayface]]*raybc[:,None]).sum(0);raynormal/=np.linalg.norm(raynormal)
    rayangle=math.degrees(math.acos(float(np.clip(world@raynormal,-1,1))))
   probes.append({'targetFace':int(f),'nearestSourceFace':int(face),'rayFirstSourceFace':None if rayhit is None else int(rayface),'rayDistanceMeters':raydistance,'localPosition':pos.tolist(),'nearestDistanceMeters':d,'sourceUV':srcuv.tolist(),'atlasUV':dstuv.tolist(),'normalToNearestDegrees':angle,'normalToRayFirstDegrees':rayangle,'albedoMeanAbsoluteError':errors['albedo'][-1],'ormMeanAbsoluteError':errors['orm'][-1]})
 field={'samples':30000,'method':'Deterministic low-face centroids, nearest exact source face barycentric source field versus bilinear actual baked4K atlas; includes source facets and filtered texels','errors':{k:stats(v) for k,v in errors.items()},'thresholdCounts':{'normalDegrees':{str(q):int((np.asarray(errors['normalDegrees'])>q).sum()) for q in [15,45,90]},'albedoMeanAbsoluteError':{str(q):int((np.asarray(errors['albedo'])>q).sum()) for q in [.05,.1]}},'worstNormalLocations':sorted(probes,key=lambda r:r['normalToNearestDegrees'],reverse=True)[:30],'worstAlbedoLocations':sorted(probes,key=lambda r:r['albedoMeanAbsoluteError'],reverse=True)[:30],'accepted':False}
 (OUT/'field.json').write_text(json.dumps(field,indent=2)+'\n');log(field)


def bake():
 bpy.ops.wm.open_mainfile(filepath=str(IN/'prepared.blend'),use_scripts=False)
 high=bpy.data.objects['ExactSelectedComponentDense'];low=bpy.data.objects['AtlasReducedComponent'];scene=bpy.context.scene
 mat=high.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;output=nodes.get('Material Output');bs=nodes.get('Principled BSDF')
 targetmat=bpy.data.materials.new('ExactSelectedAtlasReceiver');targetmat.use_nodes=True;low.data.materials.append(targetmat)
 node=targetmat.node_tree.nodes.new('ShaderNodeTexImage');targetmat.node_tree.nodes.active=node
 bpy.ops.object.select_all(action='DESELECT');high.select_set(True);low.select_set(True);bpy.context.view_layer.objects.active=low
 scene.render.bake.use_selected_to_active=True;scene.render.bake.use_cage=False;scene.render.bake.cage_extrusion=.003;scene.render.bake.max_ray_distance=.01;scene.render.bake.margin=8
 emission=nodes.new('ShaderNodeEmission');images={}
 for kind in ('albedo','orm','normal'):
  log('Bake actual selected '+kind)
  image=bpy.data.images.new('SelectedComponentAtlas_'+kind,width=2048,height=2048,alpha=False,float_buffer=False)
  image.colorspace_settings.name='sRGB' if kind=='albedo' else 'Non-Color';image.generated_color=(.5,.5,1,1) if kind=='normal' else (0,0,0,1);node.image=image
  if kind=='normal':links.new(bs.outputs['BSDF'],output.inputs['Surface']);bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT',normal_r='POS_X',normal_g='POS_Y',normal_b='POS_Z')
  else:links.new(nodes[kind].outputs['Color'],emission.inputs['Color']);links.new(emission.outputs[0],output.inputs['Surface']);bpy.ops.object.bake(type='EMIT')
  image.filepath_raw=str(OUT/(kind+'.png'));image.file_format='PNG';image.save();images[kind]=image
  log('Saved '+kind)
 audit_fields(high,low,images,OUT)
 positions=arr(low.data.vertices,'co',3);loops=arr(low.data.loop_triangles,'loops',3,np.int32).ravel();vertices=arr(low.data.loops,'vertex_index',1,np.int32).ravel()[loops]
 normals=arr(low.data.corner_normals,'vector',3)[loops];uv=arr(low.data.uv_layers.active.data,'uv',2)[loops];uv[:,1]=1-uv[:,1]
 tangent=np.concatenate([arr(low.data.loops,'tangent',3),arr(low.data.loops,'bitangent_sign',1)],axis=1)[loops]
 tr=np.load(IN/'transfer.npz')
 attrs={'POSITION':positions[vertices],'NORMAL':normals,'TEXCOORD_0':uv,'TANGENT':tangent,'JOINTS_0':tr['joints'][vertices],'WEIGHTS_0':tr['weights'][vertices],'_NATIVE_ID':tr['native'][vertices]}
 # Exact deduplication over every final attribute; preserves new UV/tangent seams.
 rowbytes=np.concatenate([a.view(np.uint8).reshape(len(vertices),-1) for a in attrs.values()],axis=1)
 _,first,inverse=np.unique(rowbytes,axis=0,return_index=True,return_inverse=True)
 np.asarray(tr['closestFaces'][vertices[first]],np.uint32).tofile(OUT/'source-face.u32')
 np.asarray(tr['bary'][vertices[first]],np.float32).tofile(OUT/'source-bary.f32')
 meta={}
 for name,a in attrs.items():
  b=np.ascontiguousarray(a[first]);b.tofile(OUT/(name+'.bin'));meta[name]={'count':len(b),'width':b.shape[1],'dtype':str(b.dtype),'min':b.min(0).tolist(),'max':b.max(0).tolist()}
 np.asarray(inverse,np.uint32).tofile(OUT/'indices.bin')
 report={'sourceSHA256':json.loads((IN/'prepare.json').read_text())['source']['sha256'],'attributes':meta,'indicesCount':len(inverse),'triangles':len(inverse)//3,'uvContract':'Blender atlas V flipped for glTF. Tangent.w is unmodified Blender bitangent_sign, matching Blender 5.2 glTF exporter.','bake':{'size':2048,'type':{'albedo':'selected source image through emission','orm':'selected source image through emission (Non-Color)','normal':'selected exact corner normal field, tangent-space'},'cageExtrusionMeters':.003,'maxRayDistanceMeters':.01,'marginPixels':8,'device':'CPU','threads':2},'accepted':False}
 for kind in images:
  p=OUT/(kind+'.png');report[kind]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 (OUT/'bake.json').write_text(json.dumps(report,indent=2)+'\n');log(report)

if MODE=='prepare':prepare()
elif MODE=='bake':bake()
elif MODE=='audit':
 bpy.ops.wm.open_mainfile(filepath=str(IN/'prepared.blend'),use_scripts=False)
 images={}
 for kind in ('albedo','orm','normal'):
  images[kind]=bpy.data.images.load(str(OUT/(kind+'.png')),check_existing=False)
  images[kind].colorspace_settings.name='sRGB' if kind=='albedo' else 'Non-Color'
 audit_fields(bpy.data.objects['ExactSelectedComponentDense'],bpy.data.objects['AtlasReducedComponent'],images,OUT)
else:raise ValueError(MODE)
