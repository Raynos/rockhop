"""Local garment albedo continuity bake; source meshes/UVs immutable."""
import bpy,numpy as np,json,hashlib,heapq,math
from pathlib import Path
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');R=ROOT/'parent-assembly/donor-fit05';O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/parent-assembly/donor-fit05');source=ROOT/'parent-assembly/donor-fit04-correction01/rider.blend';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;body=next(o for o in scene.objects if o.type=='MESH' and 'protected' in o.name);m=body.data;v=np.asarray([x.co[:] for x in m.vertices]);f=np.asarray([p.vertices[:] for p in m.polygons]);mi=np.asarray([p.material_index for p in m.polygons]);originalUV=[np.asarray([x.uv[:] for x in l.data]) for l in m.uv_layers];positions=v.copy()
# The exact attachment boundary is where nativebody/material0 meets donorhood/material2.
edgeSets=[]
for index in [0,2]:
 q=f[mi==index];e=np.concatenate([q[:,[0,1]],q[:,[1,2]],q[:,[2,0]]]);u,c=np.unique(np.sort(e,axis=1),axis=0,return_counts=True);edgeSets.append({tuple(x) for x in u[c==1]})
seam=edgeSets[0]&edgeSets[1];assert len(seam)==307;seeds=set(x for e in seam for x in e);graph=[{} for _ in v]
for t in f[np.isin(mi,[0,2])]:
 for i in range(3):
  a=int(t[i]);b=int(t[(i+1)%3]);length=float(np.linalg.norm(v[a]-v[b]));graph[a][b]=length;graph[b][a]=length
D=np.full(len(v),np.inf);queue=[]
for i in seeds:D[i]=0;heapq.heappush(queue,(0,i))
while queue:
 d,a=heapq.heappop(queue)
 if d!=D[a]:continue
 for b,l in graph[a].items():
  q=d+l
  if q<D[b]:D[b]=q;heapq.heappush(queue,(q,b))
band=.065;weight=np.zeros(len(v));inside=D<band;t=D[inside]/band;weight[inside]=1-t*t*(3-2*t)
attr=m.color_attributes.new(name='LocalJoinBlend',type='FLOAT_COLOR',domain='CORNER')
for p in m.polygons:
 for li,vi in zip(p.loop_indices,p.vertices):a=float(weight[vi]) if p.material_index in [0,2] else 0;attr.data[li].color=(a,a,a,1)
def base_image(mat):
 p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');seen=set()
 def walk(socket):
  for link in socket.links:
   n=link.from_node
   if n.as_pointer() in seen:continue
   seen.add(n.as_pointer())
   if n.type=='TEX_IMAGE' and n.image:return n.image
   for inp in n.inputs:
    image=walk(inp)
    if image:return image
 return walk(p.inputs['Base Color'])
def sample(image,uv):
 a=np.asarray(image.pixels[:]).reshape(image.size[1],image.size[0],4);x=np.clip((uv[:,0]*image.size[0]).astype(int),0,image.size[0]-1);y=np.clip((uv[:,1]*image.size[1]).astype(int),0,image.size[1]-1);rgb=a[y,x,:3];return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4) if image.colorspace_settings.name=='sRGB' else rgb
colors=[];native=[]
for index in [0,2]:
 image=base_image(m.materials[index]);assert image;uv=[]
 for p in m.polygons:
  if p.material_index!=index:continue
  for li,vi in zip(p.loop_indices,p.vertices):
   if D[vi]<.01:uv.append(m.uv_layers[0].data[li].uv[:])
 rgb=sample(image,np.asarray(uv));median=np.median(rgb,axis=0);colors.append(median);native.append({'materialIndex':index,'image':image.name,'size':list(image.size),'colorSpace':image.colorspace_settings.name,'medianLinear':median.tolist(),'samples':len(rgb)})
common=np.mean(colors,axis=0);states=[];targets=[]
for index,mat in enumerate(m.materials):
 p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL');oldSurface=[(l.from_socket,l.to_socket) for l in out.inputs['Surface'].links];base=p.inputs['Base Color'];sourceSocket=base.links[0].from_socket if base.is_linked else None
 emission=mat.node_tree.nodes.new('ShaderNodeEmission');emission.inputs['Strength'].default_value=1
 if index in [0,2]:
  factor=mat.node_tree.nodes.new('ShaderNodeVertexColor');factor.layer_name='LocalJoinBlend';mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mat.node_tree.links.new(factor.outputs['Color'],mix.inputs[0]);mix.inputs[2].default_value=(*common,1)
  if sourceSocket:mat.node_tree.links.new(sourceSocket,mix.inputs[1])
  else:mix.inputs[1].default_value=base.default_value[:]
  mat.node_tree.links.new(mix.outputs[0],emission.inputs['Color'])
 elif sourceSocket:mat.node_tree.links.new(sourceSocket,emission.inputs['Color'])
 else:emission.inputs['Color'].default_value=base.default_value[:]
 for link in list(out.inputs['Surface'].links):mat.node_tree.links.remove(link)
 mat.node_tree.links.new(emission.outputs[0],out.inputs['Surface']);size=2048 if index in [0,2] else 16;image=bpy.data.images.new('BakedJoin-'+str(index),width=size,height=size,alpha=True);image.colorspace_settings.name='sRGB';node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
 for n in mat.node_tree.nodes:n.select=False
 node.select=True;mat.node_tree.nodes.active=node;states.append((mat,p,out,oldSurface));targets.append((index,image,node))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body;m.uv_layers.active_index=0;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.bake.margin=4;scene.render.bake.use_clear=True;bpy.ops.object.bake(type='EMIT')
for mat,p,out,oldSurface in states:
 for l in list(out.inputs['Surface'].links):mat.node_tree.links.remove(l)
 for a,b in oldSurface:mat.node_tree.links.new(a,b)
for index,image,node in targets:
 if index not in [0,2]:continue
 image.filepath_raw=str(R/('join-albedo-'+str(index)+'.png'));image.file_format='PNG';image.save();image.pack();p=next(n for n in m.materials[index].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 for l in list(p.inputs['Base Color'].links):m.materials[index].node_tree.links.remove(l)
 uv=m.materials[index].node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map=m.uv_layers[0].name;m.materials[index].node_tree.links.new(uv.outputs['UV'],node.inputs['Vector']);m.materials[index].node_tree.links.new(node.outputs['Color'],p.inputs['Base Color'])
assert np.array_equal(positions,np.asarray([x.co[:] for x in m.vertices]));assert all(np.array_equal(a,np.asarray([x.uv[:] for x in l.data])) for a,l in zip(originalUV,m.uv_layers));assert sha(source)==before
bpy.ops.wm.save_as_mainfile(filepath=str(R/'rider.blend'));bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(R/'rider.glb'),export_format='GLB',export_animations=False,export_skins=False)
report={'sourceSHA256':before,'sourceUnchanged':True,'outputGLBSHA256':sha(R/'rider.glb'),'meshPositionsUVsMaterialAssignmentsUnchanged':True,'seamEdges':len(seam),'bandM':band,'changedSurfaceVertices':int(sum(inside)),'commonLinearAlbedo':common.tolist(),'nativeWitnesses':native,'CPUThreads':2,'GPUJob':False,'limitations':['2048CPUwhole-atlas rebake changes filtering outside band; original sources retained','Localjoin colour detail attenuated over65mm, originalcoat farther/denim/gloves/head geometry unchanged','Private static model, visual/motion/rig acceptance pending']};(O/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
