"""Documented lower-memory Pixal1024cascade seed after1536 guard stop."""
import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import types


def sha(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda:file.read(8*1024*1024),b''):result.update(block)
    return result.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for name in ('image','contract','out'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')==str(os.getppid())
    contract=json.loads(Path(args.contract).read_text())
    assert sha(args.image)==contract['referenceSHA256']
    for path,digest in contract['sourcePins'].items():assert sha(path)==digest,'Source changed: '+path
    source=Path(contract['source'])
    assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==contract['revision']
    sparse_control=json.loads(Path(contract['sparseControl']).read_text())
    assert sparse_control['signedNearestProtection'] and len(sparse_control['cases'])==15
    assert all(c['finite'] and c['maxCPUFloat64Error']<=c['threshold'] for c in sparse_control['cases'])
    conditioner_control=json.loads(Path(contract['conditioningControl']).read_text())
    assert len(conditioner_control['stages'])==4 and len(conditioner_control['nafChecks'])==3
    os.environ.update(ATTN_BACKEND='sdpa',SPARSE_ATTN_BACKEND='naive',SPARSE_CONV_BACKEND='flex_gemm',
                      FLEX_GEMM_BACKEND='metal',PIXAL3D_NATTEN_MPS='pytorch',
                      PIXAL3D_NAF_ROOT='/Users/raynos/ml/img2mesh/NAF',
                      PIXAL3D_NAF_WEIGHTS='/Users/raynos/projects/weights/manual/valeoai/NAF/naf_release.pth')
    for key in ('PIXAL3D_NAF_DEVICE','PIXAL3D_PROJ_GRID_DEVICE','PIXAL3D_NAF_METAL','PIXAL3D_NAF_ANE_WHOLE','PIXAL3D_NAF_ANE_REPLACE','PIXAL3D_NATTEN_MPS_ENABLE'):
        assert not os.environ.get(key),'Unqualified override: '+key
    sys.path.insert(0,str(source))
    import generate_mps as installed
    installed.load_runtime_deps()
    import numpy as np
    import torch
    import natten
    from PIL import Image
    from native_save import save_native
    from qualified_sparse_sampling import sample_with_float32_trilinear
    from qualified_pixal_sparse_sampling import sample_with_signed_nearest
    from pixal3d.pipelines.pixal3d_image_to_3d import Pixal3DImageTo3DPipeline
    from pixal3d.modules.sparse import config as sparse_config
    import pixal3d.modules.sparse.attention.full_attn as sparse_attention
    import pixal3d.trainers.flow_matching.mixins.image_conditioned_proj as conditioning
    import flex_gemm.ops.grid_sample as grid_module
    import pixal3d.representations.mesh.base as mesh_base
    torch.set_num_threads(4)
    assert torch.__version__=='2.12.0' and sparse_config.CONV=='flex_gemm' and sparse_config.ATTN=='naive'
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    report={'accepted':False,'model':'Pixal3D','quality':contract['quality'],'torch':torch.__version__,
            'workerSHA256':sha(__file__),'contractSHA256':sha(args.contract),'phase':'verify canonical weights',
            'weights':[],'loadedModels':{},'captures':{},'sampleCalls':[],'attentionChecks':[],
            'projectionChecks':[],'bilinearChecks':[],'nafChecks':[],'inputMatches':[], 'memory':[],
            'camera':conditioner_control['camera'],'backend':{'dense':'sdpa','sparse':'naive','conv':'flex_gemm','NAF':'installed PyTorch2048query'},
            'limits':['No full-model/CUDA/backward, topology-quality, fit, rig or art acceptance.',
                      'Camera estimate from real MoGe control, no calibrated reference geometry.',
                      'Raw output before cleanup/export/recolor; selected learned witnesses only.']}
    def save():
        report['elapsedSeconds']=time.monotonic()-started
        (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    def capture(label,value):
        if hasattr(value,'feats') and hasattr(value,'coords'):
            capture(label+'-coords',value.coords);value=value.feats
        cpu=value.detach().cpu().contiguous()
        array=cpu.view(torch.uint16).numpy() if cpu.dtype==torch.bfloat16 else cpu.numpy()
        archive=out/(label+'.npz');assert not archive.exists(),label
        np.savez_compressed(archive,data=array)
        item={'path':str(archive),'archiveSHA256':sha(archive),'CBytesSHA256':hashlib.sha256(memoryview(array)).hexdigest(),
              'shape':list(cpu.shape),'dtype':str(cpu.dtype),'storageDtype':str(array.dtype),'finite':bool(torch.isfinite(cpu).all())}
        report['captures'][label]=item;save();assert item['finite'],label
        if label in conditioner_control['captures']:
            original=conditioner_control['captures'][label]
            assert item['shape']==original['shape'] and item['dtype']==original['dtype'] and item['CBytesSHA256']==original['CBytesSHA256'],'Real conditioner input changed: '+label
            report['inputMatches'].append(label);save()
    def phase(label):
        report['phase']=label;torch.mps.synchronize()
        active=torch.mps.current_allocated_memory();driver=torch.mps.driver_allocated_memory()
        torch.mps.empty_cache();assert torch.mps.current_allocated_memory()==active
        report['memory'].append({'phase':label,'activeBytes':active,'driverBeforeBytes':driver,'driverAfterBytes':torch.mps.driver_allocated_memory()});save()
    save()
    for record in contract['weights']:
        assert sha(record['path'])==record['expectedSHA256'] and Path(record['path']).stat().st_size==record['bytes'],record['path']
        report['weights'].append(record);save()
    # Own process-local grid adapters; native hashmaps and interpolation preserved.
    native_grid=grid_module.grid_sample_3d
    def protected_grid(f,c,s,g,mode='trilinear'):
        nearest=lambda ff,cc,ss,gg,mode='trilinear':sample_with_signed_nearest(native_grid,ff,cc,ss,gg,mode)
        return sample_with_float32_trilinear(nearest,f,c,s,g,mode)
    grid_module.grid_sample_3d=protected_grid;mesh_base.grid_sample_3d=protected_grid
    original_load=torch.nn.Module.load_state_dict
    def observed_load(module,state,*a,**kw):
        result=original_load(module,state,*a,**kw)
        missing=set(result.missing_keys)&set(dict(module.named_parameters()))
        report.setdefault('checkpointLoads',[]).append({'module':type(module).__name__,'stateTensors':len(state),
                 'missingKeys':result.missing_keys,'unexpectedKeys':result.unexpected_keys,'missingParameters':sorted(missing)})
        save();assert not missing and not result.unexpected_keys,'Unqualified checkpoint load'
        return result
    torch.nn.Module.load_state_dict=observed_load
    phase('load actual Pixal pipeline')
    pipe=Pixal3DImageTo3DPipeline.from_pretrained('/Users/raynos/ml/img2mesh/pixal-view')
    assert pipe.low_vram
    for name,model in pipe.models.items():
        dtypes={}
        for parameter in model.parameters():dtypes[str(parameter.dtype)]=dtypes.get(str(parameter.dtype),0)+parameter.numel()
        report['loadedModels'][name]={'class':type(model).__name__,'parametersByDtype':dtypes}
    assert len(pipe.models)==7
    report['samplerDefaults']={k:getattr(pipe,k+'_sampler_params') for k in ('sparse_structure','shape_slat','tex_slat')}
    assert report['samplerDefaults']==contract['samplerParams'] and all(p['steps']==12 for p in report['samplerDefaults'].values())
    for stage,config in installed.IMAGE_COND_CONFIGS.items():
        model=installed.build_image_cond_model(config,torch.device('cpu'))
        if model.use_naf_upsample:model._load_naf()
        model.model.embeddings.register_forward_pre_hook(lambda module,a,label=stage:capture(label+'-actual-normalized-pixels',a[0]))
        model.model.register_forward_hook(lambda module,a,result,label=stage:capture(label+'-actual-DINO-features',result.last_hidden_state))
        if model.use_naf_upsample:
            model.naf_model.register_forward_pre_hook(lambda module,a,label=stage:(capture(label+'-actual-NAF-guide',a[0]),capture(label+'-actual-NAF-lowres-features',a[1])) and None)
        setattr(pipe,'image_cond_model_'+stage,model)
    torch.nn.Module.load_state_dict=original_load
    pipe.to(torch.device('mps'))
    image=pipe.preprocess_image(Image.open(args.image).convert('RGBA'));image.save(out/'conditioned-input.png')
    assert sha(out/'conditioned-input.png')==contract['preprocessingSHA256'];save()
    # Observe native projection; independent float64 camera transform on257rows.
    native_projection = conditioning.project_points_to_image_batch
    def checked_projection(points, transform, angle, resolution=518):
        actual = native_projection(points, transform, angle, resolution)
        count = points.shape[-2]
        rows = torch.linspace(0, count - 1, min(257, count)).long()
        selected = points[0, rows.to(points.device)] if points.ndim == 3 else points[rows.to(points.device)]
        xyz = selected.cpu().double().numpy()
        homogeneous = np.column_stack((xyz, np.ones(len(xyz))))
        matrix = transform[0].cpu().double().numpy()
        cam = (homogeneous @ np.linalg.inv(matrix).T)[:, :3]
        focal = resolution / (2 * math.tan(float(angle[0].cpu()) / 2))
        xy = np.column_stack((focal * cam[:, 0] / (-cam[:, 2] + 1e-8) + resolution/2,
                              -focal * cam[:, 1] / (-cam[:, 2] + 1e-8) + resolution/2))
        observed = actual[0][0, rows.to(points.device)].cpu().double().numpy()
        label = f'projection{len(report["projectionChecks"]):02d}-{report["phase"]}'
        archive = out / (label + '.npz')
        np.savez_compressed(archive, points=xyz, transform=matrix, expected=xy, actual=observed, rows=rows.numpy())
        error = float(np.max(abs(observed-xy)))
        report['projectionChecks'].append({'phase': report['phase'], 'resolution': resolution, 'selectedRows': len(rows),
                                           'maxPixelError': error, 'thresholdPixels': .001, 'archiveSHA256': sha(archive)})
        save()
        assert np.isfinite(observed).all() and error <= .001
        return actual
    conditioning.project_points_to_image_batch = checked_projection

    # Native bilinear sample on actual projected queries; independent4corners.
    native_sample = conditioning.sample_features
    def checked_sample(fmap, queries):
        actual = native_sample(fmap, queries)
        rows = torch.linspace(0, queries.shape[1]-1, min(257, queries.shape[1])).long()
        q = queries[0, rows.to(queries.device)].cpu().double().numpy()
        height, width = fmap.shape[-2:]
        x = np.clip((q[:, 0]+1)*width/2-.5, 0, width-1)
        y = np.clip((q[:, 1]+1)*height/2-.5, 0, height-1)
        x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
        x1, y1 = np.minimum(x0+1,width-1), np.minimum(y0+1,height-1)
        corners = [fmap[0, :, torch.tensor(yy,device=fmap.device), torch.tensor(xx,device=fmap.device)].T.cpu().double().numpy()
                   for yy,xx in ((y0,x0),(y0,x1),(y1,x0),(y1,x1))]
        ax, ay = (x-x0)[:,None], (y-y0)[:,None]
        expected = corners[0]*(1-ax)*(1-ay)+corners[1]*ax*(1-ay)+corners[2]*(1-ax)*ay+corners[3]*ax*ay
        got = actual[0, :, rows.to(actual.device)].T.cpu().double().numpy()
        label = f'bilinear{len(report["bilinearChecks"]):02d}-{report["phase"]}'
        archive = out / (label + '.npz')
        np.savez_compressed(archive, queries=q, corners=np.stack(corners), expected=expected, actual=got, rows=rows.numpy())
        error = float(np.max(abs(got-expected)))
        report['bilinearChecks'].append({'phase': report['phase'], 'featureMapShape': list(fmap.shape),
                                        'maxCPUFloat64Error': error, 'threshold': .0005, 'archiveSHA256': sha(archive)})
        save()
        assert np.isfinite(got).all() and error <= .0005
        return actual
    conditioning.sample_features = checked_sample

    # Observe installed PyTorch shifted-neighborhood path on real learned QKV.
    native_na2d = natten.na2d
    def checked_na2d(q, k, v, kernel_size, dilation=1, scale=None, **kw):
        actual = native_na2d(q,k,v,kernel_size,dilation,scale=scale,**kw)
        kh,kw_ = (kernel_size,kernel_size) if isinstance(kernel_size,int) else kernel_size
        dh,dw = (dilation,dilation) if isinstance(dilation,int) else dilation
        _,height,width,heads,channels = q.shape
        positions = [(0,0),(0,width-1),(height//2,width//2),(height-1,0),(height-1,width-1),(height//2,0)]
        q_selected=[]; key_selected=[]; value_selected=[]; references=[]; observed=[]
        for yy,xx in positions:
            centre_y=max(kh//2*dh,min(yy,height-1-kh//2*dh))
            centre_x=max(kw_//2*dw,min(xx,width-1-kw_//2*dw))
            ys=[centre_y+(i-kh//2)*dh for i in range(kh) for j in range(kw_)]
            xs=[centre_x+(j-kw_//2)*dw for i in range(kh) for j in range(kw_)]
            yi,xi=torch.tensor(ys,device=q.device),torch.tensor(xs,device=q.device)
            qc=q[0,yy,xx].cpu().double().numpy()
            kc=k[0,yi,xi].cpu().double().numpy()
            vc=v[0,yi,xi].cpu().double().numpy()
            scores=np.einsum('hd,khd->hk',qc,kc)*(channels**-.5 if scale is None else scale)
            weights=np.exp(scores-scores.max(-1,keepdims=True));weights/=weights.sum(-1,keepdims=True)
            references.append(np.einsum('hk,khd->hd',weights,vc))
            observed.append(actual[0,yy,xx].cpu().double().numpy())
            q_selected.append(qc);key_selected.append(kc);value_selected.append(vc)
        expected,got=np.stack(references),np.stack(observed)
        label=f'naf{len(report["nafChecks"]):02d}-{report["phase"]}'
        archive=out/(label+'.npz')
        np.savez_compressed(archive,q=np.stack(q_selected),k=np.stack(key_selected),v=np.stack(value_selected),positions=positions,expected=expected,actual=got)
        error=float(np.max(abs(got-expected)))
        report['nafChecks'].append({'phase':report['phase'],'qShape':list(q.shape),'kShape':list(k.shape),'vShape':list(v.shape),
                                    'kernel':kernel_size,'dilation':dilation,'positions':positions,'allHeads':heads,
                                    'maxCPUFloat64Error':error,'threshold':.0005,'archiveSHA256':sha(archive),
                                    'actualInstalledDispatch':'generate_mps.load_runtime_deps pure-PyTorch2048query shifted neighborhoods'})
        save()
        assert np.isfinite(got).all() and error<=.0005
        return actual
    natten.na2d=checked_na2d
    import natten.functional as functional
    if hasattr(functional,'na2d'):functional.na2d=checked_na2d


    import src.layers.attentions as naf_attention
    assert naf_attention.na2d is native_na2d
    naf_attention.na2d=checked_na2d
    for module_name,module in list(sys.modules.items()):
        if module_name.startswith('pixal3d.') and module is not None:
            for name,value in list(vars(module).items()):
                if value is native_grid:setattr(module,name,protected_grid)
    conditioner_names={id(getattr(pipe,'image_cond_model_'+stage)):stage for stage in installed.IMAGE_COND_CONFIGS}
    cond_calls=0
    original_ss=pipe.get_proj_cond_ss;original_shape=pipe.get_proj_cond_shape
    def keep_cond(stage,result):
        for kind,values in result.items():
            for name,value in values.items():capture(stage+'-'+kind+'-'+name,value)
        return result
    def get_ss(this,*a,**kw):
        nonlocal cond_calls
        cond_calls+=1;phase('conditioning-ss');return keep_cond('ss',original_ss(*a,**kw))
    def get_shape(this,model,*a,**kw):
        nonlocal cond_calls
        cond_calls+=1;stage=conditioner_names[id(model)];phase('conditioning-'+stage)
        report.setdefault('actualProjectionGrids',[]).append({'stage':stage,'gridResolution':kw.get('grid_resolution_override',model.grid_resolution)})
        save();return keep_cond(stage,original_shape(model,*a,**kw))
    pipe.get_proj_cond_ss=types.MethodType(get_ss,pipe);pipe.get_proj_cond_shape=types.MethodType(get_shape,pipe)
    model_names={id(model):name for name,model in pipe.models.items()};sampler_calls=0
    for sampler in (pipe.sparse_structure_sampler,pipe.shape_slat_sampler,pipe.tex_slat_sampler):
        original_sample,original_once=sampler.sample,sampler.sample_once;state={}
        def sample(this,model,noise,*a,_sample=original_sample,_state=state,**kw):
            nonlocal sampler_calls
            sampler_calls+=1;label=f'sampler{sampler_calls:02d}-'+model_names[id(model)]
            _state.update(label=label,step=0);phase(label);capture(label+'-initial-noise',noise)
            report['sampleCalls'].append({'label':label,'steps':kw.get('steps'),'params':{k:v for k,v in kw.items() if isinstance(v,(str,int,float,list,tuple))}})
            save();assert kw.get('steps')==12
            result=_sample(model,noise,*a,**kw);capture(label+'-final-sampled',result.samples);assert _state['step']==12
            return result
        def once(this,*a,_once=original_once,_state=state,**kw):
            result=_once(*a,**kw);_state['step']+=1;capture(_state['label']+f'-step{_state["step"]:02d}',result.pred_x_prev)
            return result
        sampler.sample=types.MethodType(sample,sampler);sampler.sample_once=types.MethodType(once,sampler)

    seen=set()
    def check_attention(q,k,v,actual,kind):
        key=(report['phase'],kind,'self' if q.shape[0]==k.shape[0] else 'cross')
        if key in seen or not report['phase'].startswith('sampler') or q.shape[0]<256:return
        seen.add(key);label=f'learned-attention{len(seen):02d}'
        for name,value in zip(('q','k','v'),(q,k,v)):capture(label+'-'+name,value)
        rows=torch.tensor([0,q.shape[0]//2,q.shape[0]-1]);qc,kc,vc=[x[:,0].detach().cpu().float() for x in (q,k,v)]
        reference=((qc[rows]@kc.T)/q.shape[-1]**.5).softmax(-1)@vc
        got=actual[rows.to(actual.device),0].detach().cpu().float()
        capture(label+'-selected-CPU-reference',reference);capture(label+'-selected-MPS-output',got)
        error=float((got-reference.to(q.dtype).float()).abs().max())
        threshold=.03125 if q.dtype==torch.bfloat16 else (.002 if q.dtype==torch.float16 else .0005)
        report['attentionChecks'].append({'phase':key[0],'backend':kind,'type':key[2],'qShape':list(q.shape),'kShape':list(k.shape),
                                          'dtype':str(q.dtype),'head':0,'selectedQueries':rows.tolist(),'allKeys':True,'maxCPUError':error,'threshold':threshold})
        save();assert torch.isfinite(got).all() and error<=threshold,'Actual learned attention failed'
    native_sdpa=torch.nn.functional.scaled_dot_product_attention
    def observed_sdpa(q,k,v,*a,**kw):
        actual=native_sdpa(q,k,v,*a,**kw)
        if q.ndim==4 and q.shape[0]==1 and q.shape[-2]>=256 and report['phase'].startswith('sampler'):
            assert not a and not kw,'Unqualified masked/scaled dense call'
            check_attention(q[0].transpose(0,1),k[0].transpose(0,1),v[0].transpose(0,1),actual[0].transpose(0,1),'native-dense-SDPA')
        return actual
    torch.nn.functional.scaled_dot_product_attention=observed_sdpa
    native_sparse=sparse_attention.sparse_scaled_dot_product_attention
    def observed_sparse(*a,**kw):
        assert not kw,'Actual sparse call must have positional original inputs'
        actual=native_sparse(*a,**kw)
        if len(a)==1:q,k,v=a[0].feats.unbind(1)
        elif len(a)==2:
            q=a[0].feats;kv=a[1].feats if hasattr(a[1],'feats') else a[1][0];k,v=kv.unbind(1)
        else:
            q=a[0].feats;k=a[1].feats if hasattr(a[1],'feats') else a[1][0];v=a[2].feats if hasattr(a[2],'feats') else a[2][0]
        output=actual.feats if hasattr(actual,'feats') else actual[0]
        check_attention(q,k,v,output,'installed-sparse-naive-fp32')
        return actual
    for module_name,module in list(sys.modules.items()):
        if module_name.startswith('pixal3d.') and module is not None:
            for name,value in list(vars(module).items()):
                if value is native_sparse:setattr(module,name,observed_sparse)
    original_decode=pipe.decode_latent
    def decode(this,shape,texture,resolution):
        report['effectiveResolution']=resolution;save();assert resolution==1024,'No silent cheaper cascade fallback'
        phase('decode-1024');capture('actual-final-shape-latent',shape);capture('actual-final-texture-latent',texture)
        return original_decode(shape,texture,resolution)
    pipe.decode_latent=types.MethodType(decode,pipe)
    phase('ready for one documented-quality seed')
    meshes,latent=pipe.run(image,camera_params=report['camera'],seed=42,pipeline_type='1024_cascade',preprocess_image=False,
                           sparse_structure_sampler_params={'steps':12},shape_slat_sampler_params={'steps':12},tex_slat_sampler_params={'steps':12},return_latent=True)
    assert len(meshes)==1 and latent[2]==1024 and sampler_calls==cond_calls==4
    assert len(report['nafChecks'])==3 and len(report['inputMatches'])==14
    assert {c['phase'] for c in report['attentionChecks']}=={c['label'] for c in report['sampleCalls']}
    phase('persist untouched raw arrays before display')
    native=save_native(meshes[0],out)
    with np.load(out/'native.npz',allow_pickle=False) as saved:
        vertices,faces=saved['vertices'],saved['faces']
        valid=bool(len(vertices) and len(faces) and np.isfinite(vertices).all() and np.isfinite(saved['attrs']).all() and faces.min()>=0 and faces.max()<len(vertices))
    report.update(status='Native raw1024 output persisted; moving review pending',validNative=valid,
                  vertices=len(vertices),triangles=len(faces),nativeArchiveSHA256=native['archiveSHA256'])
    save();assert valid,'Invalid native output retained; no derived export'
    print(json.dumps({k:report[k] for k in ('status','effectiveResolution','vertices','triangles','elapsedSeconds')}))


if __name__=='__main__':main()
