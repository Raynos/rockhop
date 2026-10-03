"""Original Pixal decoders from actual saved final inputs; no sampling."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda:file.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for key in ('contract','out'):parser.add_argument('--'+key,required=True)
    args=parser.parse_args();assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')==str(os.getppid())
    contract=json.loads(Path(args.contract).read_text())
    for path,h in contract['sourcePins'].items():assert sha(path)==h,path
    assert subprocess.check_output(['git','-C',contract['source'],'rev-parse','HEAD'],text=True).strip()==contract['revision']
    for item in contract['weights']:assert sha(item['path'])==item['expectedSHA256'] and Path(item['path']).stat().st_size==item['bytes']
    os.environ.update(ATTN_BACKEND='sdpa',SPARSE_ATTN_BACKEND='naive',SPARSE_CONV_BACKEND='flex_gemm',FLEX_GEMM_BACKEND='metal',PIXAL3D_NATTEN_MPS='pytorch')
    sys.path.insert(0,contract['source'])
    import generate_mps as installed
    installed.load_runtime_deps()
    import torch
    import numpy as np
    from pixal3d.pipelines.pixal3d_image_to_3d import Pixal3DImageTo3DPipeline
    from pixal3d.modules.sparse import SparseTensor
    from flex_gemm.ops import grid_sample as grid_module
    import pixal3d.representations.mesh.base as mesh_base
    from qualified_sparse_sampling import sample_with_float32_trilinear
    from qualified_pixal_sparse_sampling import sample_with_signed_nearest
    from native_save import save_native
    assert torch.__version__=='2.12.0'
    prior=json.loads(Path(contract['decodeInputReceipt']).read_text())
    assert len(prior['noisePrefixReplay'])==3 and all(x['byteIdentical'] for x in prior['noisePrefixReplay'])
    assert len(prior['nafChecks'])==1 and len(prior['inputMatches'])==3
    assert all(x['maxCPUError']<=x['threshold'] for x in prior['attentionChecks'])
    out=Path(args.out);out.mkdir(exist_ok=False,parents=True);start=time.monotonic()
    report={'accepted':False,'torch':torch.__version__,'recipeSHA256':sha(__file__),
            'decodeInputReceiptSHA256':sha(contract['decodeInputReceipt']),'resolution':1024,
            'samplingCalls':0,'actualSamplingStepsAlreadyPersisted':48,'checkpointLoads':[],
            'restoredInputs':{},'status':'Restore real saved final inputs before original decoder'}
    def save():
        report['elapsedSeconds']=time.monotonic()-start;(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    native_grid=grid_module.grid_sample_3d
    def protected_grid(f,c,s,g,mode='trilinear'):
        nearest=lambda ff,cc,ss,gg,mode='trilinear':sample_with_signed_nearest(native_grid,ff,cc,ss,gg,mode)
        return sample_with_float32_trilinear(nearest,f,c,s,g,mode)
    grid_module.grid_sample_3d=protected_grid;mesh_base.grid_sample_3d=protected_grid
    original_load=torch.nn.Module.load_state_dict
    def observed_load(module,state,*a,**kw):
        result=original_load(module,state,*a,**kw)
        row={'module':type(module).__name__,'missingKeys':result.missing_keys,'unexpectedKeys':result.unexpected_keys}
        report['checkpointLoads'].append(row);save();assert not result.missing_keys and not result.unexpected_keys
        return result
    torch.nn.Module.load_state_dict=observed_load
    class DecodersOnly(Pixal3DImageTo3DPipeline):
        model_names_to_load=['shape_slat_decoder','tex_slat_decoder']
    pipe=DecodersOnly.from_pretrained('/Users/raynos/ml/img2mesh/pixal-view')
    torch.nn.Module.load_state_dict=original_load
    assert set(pipe.models)==set(DecodersOnly.model_names_to_load) and pipe.low_vram
    report['loadedModels']=list(pipe.models);pipe.to(torch.device('mps'));save()
    for module_name,module in list(sys.modules.items()):
        if module_name.startswith('pixal3d.') and module is not None:
            for name,value in list(vars(module).items()):
                if value is native_grid:setattr(module,name,protected_grid)
    def restore(label):
        item=prior['captures'][label];assert sha(item['path'])==item['archiveSHA256'] and item['finite']
        with np.load(item['path'],allow_pickle=False) as archive:value=archive['data'].copy()
        assert hashlib.sha256(memoryview(value)).hexdigest()==item['CBytesSHA256']
        assert list(value.shape)==item['shape'] and str(value.dtype)==item['storageDtype']
        assert item['dtype'] in ('torch.float32','torch.int32')
        report['restoredInputs'][label]={'CBytesSHA256':item['CBytesSHA256'],'byteIdentical':True};save()
        return torch.from_numpy(value).to(pipe.device)
    shape=SparseTensor(feats=restore('actual-final-shape-latent'),coords=restore('actual-final-shape-latent-coords'))
    texture=SparseTensor(feats=restore('actual-final-texture-latent'),coords=restore('actual-final-texture-latent-coords'))
    torch.mps.empty_cache()
    with torch.inference_mode():meshes=pipe.decode_latent(shape,texture,1024)
    assert len(meshes)==1
    # Persist first. A later qualification error must not lose completed output.
    native=save_native(meshes[0],out)
    report.update(status='Raw1024 mesh persisted before moving review',native=native)
    save()
    with np.load(out/'native.npz',allow_pickle=False) as data:
        v,f=data['vertices'],data['faces']
        valid=bool(len(v) and len(f) and np.isfinite(v).all() and np.isfinite(data['attrs']).all() and f.min()>=0 and f.max()<len(v))
        report.update(vertices=len(v),triangles=len(f),validNative=valid)
    save();assert valid
    print(json.dumps({'vertices':report['vertices'],'triangles':report['triangles'],'elapsedSeconds':report['elapsedSeconds']}))


if __name__=='__main__':main()
