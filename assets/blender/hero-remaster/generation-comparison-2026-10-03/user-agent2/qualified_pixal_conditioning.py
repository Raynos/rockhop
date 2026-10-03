"""Actual Pixal hoodie conditioner control; no flow sampling or mesh export.

Archive real learned feature inputs and selected independent CPU witnesses.
The generated reference has no calibrated camera; MoGe estimates one.
"""
import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda: file.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('out', 'contract', 'image'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    contract = json.loads(Path(args.contract).read_text())
    assert sha(args.image) == contract['referenceSHA256']
    for path, digest in contract['sourcePins'].items():
        assert sha(path) == digest, 'Changed source: ' + path
    os.environ.update(ATTN_BACKEND='sdpa', SPARSE_ATTN_BACKEND='naive', SPARSE_CONV_BACKEND='flex_gemm',
                      PIXAL3D_NATTEN_MPS='pytorch', PIXAL3D_NAF_ROOT='/Users/raynos/ml/img2mesh/NAF',
                      PIXAL3D_NAF_WEIGHTS='/Users/raynos/projects/weights/manual/valeoai/NAF/naf_release.pth')
    for key in ('PIXAL3D_NAF_DEVICE', 'PIXAL3D_PROJ_GRID_DEVICE', 'PIXAL3D_NAF_METAL', 'PIXAL3D_NAF_ANE_WHOLE', 'PIXAL3D_NAF_ANE_REPLACE', 'PIXAL3D_NATTEN_MPS_ENABLE'):
        assert not os.environ.get(key), 'Unqualified override: ' + key
    sys.path.insert(0, contract['source'])
    import generate_mps as installed
    installed.load_runtime_deps()
    import numpy as np
    import torch
    from PIL import Image
    import natten
    from pixal3d.pipelines.pixal3d_image_to_3d import Pixal3DImageTo3DPipeline
    import pixal3d.trainers.flow_matching.mixins.image_conditioned_proj as conditioning
    torch.set_num_threads(4)
    assert torch.__version__ == '2.12.0' and torch.backends.mps.is_available()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {'accepted': False, 'model': 'Pixal3D', 'flowSamplingRuns': 0,
              'workerSHA256': sha(__file__), 'contractSHA256': sha(args.contract),
              'torch': torch.__version__, 'device': 'mps', 'phase': 'verify canonical conditioners',
              'weights': [], 'captures': {}, 'projectionChecks': [], 'bilinearChecks': [], 'nafChecks': [],
              'stages': [], 'memory': [], 'limits': ['No flow seed, mesh quality, backward or CUDA parity.',
              'Full learned pixel/DINO/NAF input arrays archived; projected and NAF output witnesses selected only.',
              'MoGe camera is an estimate for a generated2D reference, not calibrated geometry.']}

    def save():
        report['elapsedSeconds'] = time.monotonic() - started
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')

    def capture(label, value):
        cpu = value.detach().cpu().contiguous()
        array = cpu.view(torch.uint16).numpy() if cpu.dtype == torch.bfloat16 else cpu.numpy()
        archive = out / (label + '.npz')
        assert not archive.exists(), 'Repeated capture: ' + label
        np.savez_compressed(archive, data=array)
        record = {'path': str(archive), 'archiveSHA256': sha(archive), 'shape': list(cpu.shape),
                  'dtype': str(cpu.dtype), 'CBytesSHA256': hashlib.sha256(memoryview(array)).hexdigest(),
                  'finite': bool(torch.isfinite(cpu).all())}
        report['captures'][label] = record
        save()
        assert record['finite'], label

    def phase(label):
        report['phase'] = label
        torch.mps.synchronize()
        active = torch.mps.current_allocated_memory()
        before = torch.mps.driver_allocated_memory()
        torch.mps.empty_cache()
        assert torch.mps.current_allocated_memory() == active
        report['memory'].append({'phase': label, 'activeBytes': active, 'driverBeforeBytes': before,
                                 'driverAfterBytes': torch.mps.driver_allocated_memory()})
        save()

    save()
    for pin in contract['weights']:
        assert sha(pin['path']) == pin['expectedSHA256'] and Path(pin['path']).stat().st_size == pin['bytes']
        report['weights'].append(pin)
        save()
    # Actual installed preprocessing, with genuine alpha avoiding segmentation.
    image = Pixal3DImageTo3DPipeline.preprocess_image(SimpleNamespace(low_vram=True), Image.open(args.image).convert('RGBA'))
    image.save(out / 'conditioned-input.png')
    assert sha(out / 'conditioned-input.png') == contract['preprocessingSHA256']
    report['preprocessing'] = {'SHA256': sha(out / 'conditioned-input.png'), 'size': list(image.size)}
    phase('actual-MoGe-camera')
    moge = installed.load_moge_model(torch.device('mps'))
    infer = moge.infer
    def observed_infer(value, *a, **kw):
        capture('moge-actual-input', value)
        result = infer(value, *a, **kw)
        capture('moge-actual-intrinsics', result['intrinsics'])
        return result
    moge.infer = observed_infer
    camera = installed.get_camera_params_wild_moge(str(out / 'conditioned-input.png'), moge, torch.device('mps'), mesh_scale=1.0, extend_pixel=0, image_resolution=512)
    assert 0 < camera['camera_angle_x'] < math.pi and camera['distance'] > 0 and camera['mesh_scale'] == 1.0
    report['camera'] = camera
    save()
    moge.cpu()
    del moge, infer, observed_infer
    gc.collect()
    phase('MoGe released before actual DINO/NAF')

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

    for stage,config in installed.IMAGE_COND_CONFIGS.items():
        phase(stage)
        model=installed.build_image_cond_model(config,torch.device('mps'))
        handles=[]
        handles.append(model.model.embeddings.register_forward_pre_hook(lambda module,a,label=stage:capture(label+'-actual-normalized-pixels',a[0])))
        handles.append(model.model.register_forward_hook(lambda module,a,result,label=stage:capture(label+'-actual-DINO-features',result.last_hidden_state)))
        if model.use_naf_upsample:
            model._load_naf()
            handles.append(model.naf_model.register_forward_pre_hook(lambda module,a,label=stage:(capture(label+'-actual-NAF-guide',a[0]),capture(label+'-actual-NAF-lowres-features',a[1])) and None))
        camera_tensors={key:torch.tensor([camera[key]],device='mps') for key in ('camera_angle_x','distance','mesh_scale')}
        with torch.inference_mode():
            global_features,projected=model([image],**camera_tensors)
        capture(stage+'-actual-global-features',global_features)
        rows=torch.linspace(0,projected.shape[1]-1,min(257,projected.shape[1])).long().to('mps')
        capture(stage+'-selected-projected-features',projected[:,rows])
        finite=bool(torch.isfinite(projected).all())
        report['stages'].append({'stage':stage,'config':config,'globalShape':list(global_features.shape),
                                  'projectedShape':list(projected.shape),'allProjectedFinite':finite,
                                  'projectionOutputsArchived':'257 selected actual rows; full real DINO/NAF inputs archived'})
        save();assert finite
        for handle in handles:handle.remove()
        model.cpu();del model,global_features,projected,handles,camera_tensors
        gc.collect();phase(stage+' released')
    assert len(report['stages'])==4 and len(report['nafChecks'])==3
    report['status']='Four actual installed conditioners and selected independent learned witnesses pass; no flow seed'
    save();print(json.dumps({'status':report['status'],'elapsedSeconds':report['elapsedSeconds']}))


if __name__=='__main__':
    main()
