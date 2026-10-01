"""Read-only source texel and actual Cycles emission color-space witness."""
import bpy,json,struct,hashlib,os
import numpy as np
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/cheek-texture04');O.mkdir(exist_ok=True)
T=R/'cheek-texture04';T.mkdir(exist_ok=True)
source=R/'generation/h21-buzz-native01/model.glb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(source)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');src=next(n.image for n in obj.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.name=='textured');pixels=np.asarray(src.pixels[:]).reshape(src.size[1],src.size[0],4)
y,x=np.unravel_index(np.argmin(np.linalg.norm(pixels[:,:,:3]-[.78,.53,.43],axis=2)),pixels.shape[:2]);c=pixels[y,x,:3];linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=2
rows=[]
for mode in ['source-image-shader','encoded-as-linear','decoded-as-linear']:
 mesh=bpy.data.meshes.new(mode);mesh.from_pydata([(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)],[],[(0,1,2,3)]);sample=mesh.uv_layers.new(name='source-sample');target=mesh.uv_layers.new(name='bake-target')
 for i,loop in enumerate(mesh.loops):sample.data[i].uv=((x+.5)/src.size[0],(y+.5)/src.size[1]);target.data[i].uv=((0,0),(1,0),(1,1),(0,1))[i]
 mesh.uv_layers.active=target
 obj=bpy.data.objects.new(mode,mesh);scene.collection.objects.link(obj);mat=bpy.data.materials.new(mode);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
 if mode=='source-image-shader':
  image=n.new('ShaderNodeTexImage');image.image=src;image.interpolation='Closest';uv=n.new('ShaderNodeUVMap');uv.uv_map='source-sample';mat.node_tree.links.new(uv.outputs['UV'],image.inputs['Vector']);mat.node_tree.links.new(image.outputs['Color'],em.inputs['Color'])
 else:em.inputs['Color'].default_value=(*(c if mode=='encoded-as-linear' else linear),1)
 dest=bpy.data.images.new(mode,width=16,height=16,alpha=True);dest.colorspace_settings.name='sRGB';node=n.new('ShaderNodeTexImage');node.image=dest;n.active=node;obj.data.materials.append(mat);bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;scene.render.bake.use_clear=True;scene.render.bake.margin=0;bpy.ops.object.bake(type='EMIT');path=T/(mode+'.png');dest.filepath_raw=str(path);dest.file_format='PNG';dest.save();rows.append({'mode':mode,'path':str(path),'SHA256':sha(path)});bpy.data.objects.remove(obj,do_unlink=True)
assert sha(source)==before
(O/'probe.json').write_text(json.dumps({'sourceSHA256':before,'sourceUnchanged':True,'sourceImageColorSpace':src.colorspace_settings.name,'sourceImageSize':list(src.size),'sourcePixelXYBottomOrigin':[int(x),int(y)],'sourceImagePixelsRGB':c.tolist(),'decodedLinearRGB':linear.tolist(),'witnesses':rows,'CPUThreads':2,'GPUJob':False},indent=2)+'\n')
