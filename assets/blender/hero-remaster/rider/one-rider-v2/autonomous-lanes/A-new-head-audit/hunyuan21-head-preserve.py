"""Pinned official Hunyuan3D 2.1 shape + 2.1 PBR painter, isolated MPS adaptation."""
import argparse,gc,json,os,pathlib,resource,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=pathlib.Path(os.environ.get('HY3D21_ROOT',str(pathlib.Path.home()/'ml/img2mesh/Hunyuan3D-2.1')))
VIEW=pathlib.Path(os.environ.get('HY3D21_VIEW',str(pathlib.Path.home()/'ml/img2mesh/hunyuan21-view')))
WEIGHTS=pathlib.Path.home()/'projects/weights/manual'
sys.path[:0]=[str(SOURCE/'hy3dshape'),str(SOURCE/'hy3dpaint')]
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','1')
os.environ.update(HF_HOME=os.environ.get('HF_HOME',str(WEIGHTS.parent/'hf')),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_MODULES_CACHE='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit/environment/hf-modules')
import torch
import numpy as np,hashlib
from PIL import Image
import torchvision.transforms.functional as functional
sys.modules['torchvision.transforms.functional_tensor']=functional
original_to=torch.Tensor.to
def safe_to(self,*args,**kwargs):
    target=kwargs.get('device',args[0] if args else None)
    if self.dtype==torch.float64 and str(target).startswith('mps'):self=self.float()
    return original_to(self,*args,**kwargs)
torch.Tensor.to=safe_to
p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--out',required=True);p.add_argument('--seed',type=int,default=42);p.add_argument('--smoke',action='store_true');p.add_argument('--shape-steps',type=int,default=24);p.add_argument('--octree',type=int,default=320);p.add_argument('--target-faces',type=int,default=100000);p.add_argument('--resume-shape',action='store_true');a=p.parse_args()
out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
assert not (out/'model.glb').exists(),'Preserve previous output'
assert torch.backends.mps.is_available(),'Actual MPS required'
record={'version':'Hunyuan3D-2.1','device':'mps','seed':a.seed,'shape_steps':8 if a.smoke else a.shape_steps,'paint_steps':2 if a.smoke else 15,'octree':192 if a.smoke else a.octree,'paint_views':6,'paint_view_size':256 if a.smoke else 512,'render_size':512 if a.smoke else 1024,'texture_size':512 if a.smoke else 1024,'torch':torch.__version__,'python':sys.version,'cpu_components':['texture rendering/baking','custom_rasterizer','mesh_inpaint_processor','marching cubes','Blender export'],'source_commit':subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip(),'weights_revision':'0b94677654c57bb9a6b6845cd7b704ccf551d327'}
t=time.monotonic()
(out/'start-settings.json').write_text(json.dumps(record,indent=2))
from hy3dshape import Hunyuan3DDiTFlowMatchingPipeline,FaceReducer,FloaterRemover,DegenerateFaceRemover
image=Image.open(a.image).convert("RGBA")
if not a.resume_shape:
    shp=Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(str(WEIGHTS/'tencent/Hunyuan3D-2.1'),device='mps',use_safetensors=False)
    shp.enable_flashvdm(mc_algo='mc')
    print('[2.1] Shape loaded on',shp.device,flush=True)
    image=Image.open(a.image).convert('RGBA');ts=time.monotonic()
    mesh=shp(image=image,num_inference_steps=record['shape_steps'],octree_resolution=record['octree'],num_chunks=200000,guidance_scale=5.0,generator=torch.Generator(device='cpu').manual_seed(a.seed),output_type='trimesh')[0]
    record['shape_seconds']=round(time.monotonic()-ts,3);record['raw_faces']=len(mesh.faces)
    # Preserve actual native shape BEFORE every cleanup and reducer.
    np.savez_compressed(out/'raw-shape.npz',vertices=np.asarray(mesh.vertices,dtype=np.float32),faces=np.asarray(mesh.faces,dtype=np.int32))
    mesh.export(out/'raw-shape.glb')
    record['raw_shape_sha256']=hashlib.sha256((out/'raw-shape.npz').read_bytes()).hexdigest()
    (out/'raw-shape-settings.json').write_text(json.dumps(record,indent=2))
    mesh=FloaterRemover()(mesh);mesh=DegenerateFaceRemover()(mesh);mesh=FaceReducer()(mesh,max_facenum=a.target_faces)
    record['faces']=len(mesh.faces);mesh.export(out/'shape.glb');mesh.export(out/'shape.obj');(out/'shape-progress.json').write_text(json.dumps(record,indent=2))
    del shp;gc.collect();torch.mps.empty_cache()
else:
    assert (out/"shape.obj").exists(), "No saved 2.1 shape"
    import hashlib
    record["resumed_shape_sha256"]=hashlib.sha256((out/"shape.obj").read_bytes()).hexdigest()
from textureGenPipeline import Hunyuan3DPaintPipeline,Hunyuan3DPaintConfig
c=Hunyuan3DPaintConfig(record['paint_views'],record['paint_view_size']);c.device='mps';c.renderer_device='cpu';c.seed=a.seed;c.paint_steps=record['paint_steps']
c.multiview_cfg_path=str(SOURCE/'hy3dpaint/cfgs/hunyuan-paint-pbr.yaml');c.multiview_pretrained_path=str(VIEW);c.dino_ckpt_path=str(WEIGHTS/'facebook/dinov2-giant');c.realesrgan_ckpt_path=str(WEIGHTS/'xinntao/Real-ESRGAN/RealESRGAN_x4plus.pth');c.render_size=record['render_size'];c.texture_size=record['texture_size']
tp=time.monotonic();paint=Hunyuan3DPaintPipeline(c);print('[2.1] PBR painter loaded on',paint.models['multiview_model'].pipeline.device,flush=True)
paint(mesh_path=str(out/'shape.obj'),image_path=image,output_mesh_path=str(out/'textured.obj'),use_remesh=False,save_glb=False)
record['paint_seconds']=round(time.monotonic()-tp,3)
del paint;gc.collect();torch.mps.empty_cache()
subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python','/Users/raynos/projects/localai/bin/img2mesh/hunyuan21-export.py','--',str(out/'textured.obj'),str(out/'model.glb')],check=True)
record['wall_seconds']=round(time.monotonic()-t,3);record['peak_rss_gb']=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e9,3)
(out/'generation.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
