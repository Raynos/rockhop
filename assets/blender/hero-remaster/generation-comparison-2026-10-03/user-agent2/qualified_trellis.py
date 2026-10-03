"""One serial proper-quality TRELLIS seed with durable actual input evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True)
    parser.add_argument('--contract', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    image_path, contract_path = Path(args.image).resolve(), Path(args.contract).resolve()
    contract = json.loads(contract_path.read_text())
    assert sha(image_path) == contract['referenceSHA256']
    for path, digest in contract['sourcePins'].items():
        assert sha(path) == digest, 'Changed source/control: ' + path
    control_path = next(p for p in contract['sourcePins'] if 'qualified-sparse-operator02/receipt.json' in p)
    control = json.loads(Path(control_path).read_text())
    assert control['protectedTrilinear'] and len(control['cases']) == 15
    assert all(c['finite'] and c['maxCPUFloat64Error'] <= c['threshold'] for c in control['cases'])
    source = Path('/Users/raynos/ml/img2mesh/trellis-mac')
    nested = source / 'TRELLIS.2'
    for path, expected in ((source, 'd58628f4f5b9c3de8274cb110074154f4b31cef2'),
                           (nested, '75fbf0183001ed9876c8dbb35de6b68552ee08bd')):
        assert subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip() == expected
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      PYTORCH_ENABLE_MPS_FALLBACK='1', ATTN_BACKEND='sdpa',
                      SPARSE_ATTN_BACKEND='sdpa', SPARSE_CONV_BACKEND='flex_gemm')
    sys.path.insert(0, str(nested))
    sys.path.insert(0, str(source))
    sys.path.append(str(source / 'stubs'))
    import numpy as np
    import torch
    from PIL import Image
    from native_save import save_native
    from qualified_sparse_sampling import sample_with_float32_trilinear
    from trellis2.pipelines.trellis2_image_to_3d import Trellis2ImageTo3DPipeline
    from trellis2.modules.sparse import config as sparse_config
    from trellis2.modules.sparse.conv import config as conv_config
    import trellis2.representations.mesh.base as mesh_base

    torch.set_num_threads(4)
    assert torch.backends.mps.is_available()
    assert sparse_config.CONV == 'flex_gemm' and sparse_config.ATTN == 'sdpa'
    assert conv_config.FLEX_GEMM_ALGO == 'masked_implicit_gemm_splitk'
    assert conv_config.FLEX_GEMM_HASHMAP_RATIO == 2.0
    started = time.monotonic()
    report = {'accepted': False, 'model': 'TRELLIS.2', 'quality': contract['quality'],
              'contractSHA256': sha(contract_path), 'workerSHA256': sha(__file__),
              'device': 'mps', 'torch': torch.__version__, 'backend': {'conv': sparse_config.CONV, 'attention': sparse_config.ATTN},
              'phase': 'canonical weight verification', 'weights': [], 'loadedModels': {},
              'captures': {}, 'sampleCalls': [], 'attentionChecks': [], 'memory': [],
              'cleanup': False, 'remesh': False, 'reduction': False,
              'limits': ['No CUDA/full-model parity, rig, fit or final-art acceptance.',
                         'Native geometry/attrs precede any derived display or material bake.']}

    def save():
        report['elapsedSeconds'] = time.monotonic() - started
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')

    def capture(label, value):
        if hasattr(value, 'feats') and hasattr(value, 'coords'):
            capture(label + '-coords', value.coords)
            value = value.feats
        cpu = value.detach().cpu().contiguous()
        # Preserve actual bf16 C bytes; NumPy has no native bf16 dtype.
        array = cpu.view(torch.uint16).numpy() if cpu.dtype == torch.bfloat16 else cpu.numpy()
        path = out / (label + '.npz')
        assert not path.exists(), 'Capture label reused: ' + label
        np.savez_compressed(path, data=array)
        report['captures'][label] = {'path': str(path), 'archiveSHA256': sha(path),
                                    'dtype': str(cpu.dtype), 'storageDtype': str(array.dtype),
                                    'shape': list(cpu.shape), 'stride': list(value.stride()) if isinstance(value, torch.Tensor) else None,
                                    'CBytesSHA256': hashlib.sha256(array.tobytes(order='C')).hexdigest(),
                                    'finite': bool(torch.isfinite(cpu).all())}
        save()
        assert report['captures'][label]['finite'], 'Actual tensor nonfinite: ' + label

    def phase(label):
        report['phase'] = label
        torch.mps.synchronize()
        active = torch.mps.current_allocated_memory()
        driver = torch.mps.driver_allocated_memory()
        torch.mps.empty_cache()  # Only unoccupied storage; no numerical change.
        assert torch.mps.current_allocated_memory() == active
        report['memory'].append({'phase': label, 'activeBytes': active,
                                 'driverBeforeBytes': driver, 'driverAfterBytes': torch.mps.driver_allocated_memory()})
        save()

    save()
    for record in contract['weights']:
        actual = sha(record['path'])
        assert actual == record['expectedSHA256'] and Path(record['path']).stat().st_size == record['bytes']
        report['weights'].append({'path': record['path'], 'SHA256': actual, 'bytes': record['bytes']})
        save()

    # Inspect the actual installed strict=False loader rather than trusting it.
    original_load = torch.nn.Module.load_state_dict
    def observed_load(module, state, *a, **kw):
        result = original_load(module, state, *a, **kw)
        missing_parameters = set(result.missing_keys) & set(dict(module.named_parameters()))
        report.setdefault('checkpointLoads', []).append({'module': type(module).__name__, 'stateTensors': len(state),
                                                         'missingKeys': result.missing_keys, 'unexpectedKeys': result.unexpected_keys,
                                                         'missingParameters': sorted(missing_parameters)})
        save()
        assert not missing_parameters and not result.unexpected_keys, 'Unqualified loaded state mismatch'
        return result
    torch.nn.Module.load_state_dict = observed_load
    phase('load actual pipeline')
    pipe = Trellis2ImageTo3DPipeline.from_pretrained('/Users/raynos/ml/img2mesh/trellis-view')
    torch.nn.Module.load_state_dict = original_load
    assert pipe.low_vram, 'Keep installed documented low-VRAM scheduling'
    for name, model in pipe.models.items():
        by_dtype = {}
        for parameter in model.parameters():
            key = str(parameter.dtype)
            by_dtype[key] = by_dtype.get(key, 0) + parameter.numel()
        report['loadedModels'][name] = {'class': type(model).__name__, 'parametersByDtype': by_dtype}
    report['samplerDefaults'] = {k: getattr(pipe, k + '_sampler_params') for k in ('sparse_structure', 'shape_slat', 'tex_slat')}
    assert report['samplerDefaults'] == contract['samplerParams'], 'Documented guidance/scheduling changed'
    assert all(x['steps'] == 12 for x in report['samplerDefaults'].values())
    pipe.to(torch.device('mps'))
    original = Image.open(image_path).convert('RGBA')
    conditioned = pipe.preprocess_image(original)
    conditioned.save(out / 'conditioned-input.png')
    assert sha(out / 'conditioned-input.png') == contract['preprocessingSHA256']
    report['conditionedImage'] = {'SHA256': sha(out / 'conditioned-input.png'), 'size': list(conditioned.size)}
    save()

    # Actual normalized DINO pixels enter embeddings; actual output features
    # and negative conditioning are captured at both cascade resolutions.
    cond_call = 0
    original_cond = pipe.get_cond
    def get_cond(this, image, resolution, include_neg_cond=True):
        nonlocal cond_call
        cond_call += 1
        phase('conditioning-' + str(resolution))
        def pixels(module, args):
            capture(f'dino-{resolution}-normalized-pixels', args[0])
        handle = pipe.image_cond_model.model.embeddings.register_forward_pre_hook(pixels)
        result = original_cond(image, resolution, include_neg_cond)
        handle.remove()
        for key, value in result.items():
            capture(f'dino-{resolution}-' + key, value)
        return result
    pipe.get_cond = types.MethodType(get_cond, pipe)

    # Save real initial noise, sampler params, each actual step and final latent.
    model_names = {id(model): name for name, model in pipe.models.items()}
    sampler_call = 0
    for sampler in (pipe.sparse_structure_sampler, pipe.shape_slat_sampler, pipe.tex_slat_sampler):
        original_sample, original_once = sampler.sample, sampler.sample_once
        state = {}
        def sample(this, model, noise, *a, _sample=original_sample, _state=state, **kw):
            nonlocal sampler_call
            sampler_call += 1
            label = f'sampler{sampler_call:02d}-' + model_names[id(model)]
            _state.update(label=label, step=0)
            phase(label)
            capture(label + '-initial-noise', noise)
            report['sampleCalls'].append({'label': label, 'steps': kw.get('steps'), 'params': {k:v for k,v in kw.items() if isinstance(v, (str,int,float,list,tuple))}})
            save()
            assert kw.get('steps') == 12
            result = _sample(model, noise, *a, **kw)
            capture(label + '-final-sampled', result.samples)
            assert _state['step'] == 12
            return result
        def once(this, *a, _once=original_once, _state=state, **kw):
            result = _once(*a, **kw)
            _state['step'] += 1
            capture(_state['label'] + f'-step{_state["step"]:02d}', result.pred_x_prev)
            return result
        sampler.sample = types.MethodType(sample, sampler)
        sampler.sample_once = types.MethodType(once, sampler)

    # Observe installed SDPA, never replace its math. One learned large call
    # per phase/type is compared against selected CPU queries with all keys.
    native_sdpa = torch.nn.functional.scaled_dot_product_attention
    seen = set()
    def checked_sdpa(q, k, v, *a, **kw):
        key = (report['phase'], 'self' if q.shape[-2] == k.shape[-2] else 'cross')
        check = report['phase'].startswith('sampler') and q.shape[-2] >= 4096 and key not in seen
        if check:
            seen.add(key)
            label = f'learned-attention{len(seen):02d}'
            for name, value in zip(('q','k','v'), (q,k,v)):
                capture(label + '-' + name, value)
            save()
        actual = native_sdpa(q, k, v, *a, **kw)
        if check:
            assert not a and not kw, 'Only unmasked installed inference SDPA is qualified'
            rows = torch.tensor([0, q.shape[-2]//2, q.shape[-2]-1])
            qc, kc, vc = [t.detach().cpu().float() for t in (q,k,v)]
            reference = ((qc[0,0,rows] @ kc[0,0].T) / q.shape[-1]**0.5).softmax(-1) @ vc[0,0]
            observed = actual.detach().cpu()[0,0,rows].float()
            capture(label + '-selected-CPU-reference', reference)
            capture(label + '-selected-MPS-output', observed)
            error = float((observed-reference.to(q.dtype).float()).abs().max())
            threshold = .03125 if q.dtype == torch.bfloat16 else (.002 if q.dtype == torch.float16 else .0005)
            report['attentionChecks'].append({'label': label, 'phase': key[0], 'type': key[1],
                                               'qShape': list(q.shape), 'kShape': list(k.shape), 'dtype': str(q.dtype),
                                               'selectedQueries': rows.tolist(), 'head': 0, 'allKeys': True,
                                               'maxCPUError': error, 'threshold': threshold})
            save()
            assert error <= threshold and torch.isfinite(actual).all(), 'Actual learned attention control failed'
        return actual
    torch.nn.functional.scaled_dot_product_attention = checked_sdpa

    # Needed only for actual low-precision MeshWithVoxel.query_attrs callers.
    native_grid = mesh_base.grid_sample_3d
    mesh_base.grid_sample_3d = lambda f,c,s,g,mode='trilinear': sample_with_float32_trilinear(native_grid,f,c,s,g,mode)
    original_decode = pipe.decode_latent
    def decode(this, shape, texture, resolution):
        report['effectiveResolution'] = resolution
        assert resolution == 1024, 'No silent cheaper cascade fallback'
        phase('decode-1024')
        capture('actual-final-shape-latent', shape)
        capture('actual-final-texture-latent', texture)
        return original_decode(shape, texture, resolution)
    pipe.decode_latent = types.MethodType(decode, pipe)
    result = pipe.run(conditioned, seed=42, pipeline_type='1024_cascade', preprocess_image=False,
                      sparse_structure_sampler_params={'steps':12}, shape_slat_sampler_params={'steps':12},
                      tex_slat_sampler_params={'steps':12}, return_latent=True)
    meshes, latent = result
    assert len(meshes) == 1 and latent[2] == 1024 and sampler_call == 4 and cond_call == 2
    mesh = meshes[0]
    phase('persist untouched raw geometry and attributes')
    native = save_native(mesh, out)
    with np.load(out/'native.npz', allow_pickle=False) as saved:
        vertices, faces = saved['vertices'], saved['faces']
        valid = bool(len(vertices) and len(faces) and np.isfinite(vertices).all() and
                     np.isfinite(saved['attrs']).all() and faces.min()>=0 and faces.max()<len(vertices))
    report.update(status='Raw native output persisted; moving review pending', validNative=valid,
                  vertices=len(vertices), triangles=len(faces), nativeArchiveSHA256=native['archiveSHA256'])
    save()
    assert valid, 'Invalid raw output retained; no derived export'
    print(json.dumps({k:report[k] for k in ('status','effectiveResolution','vertices','triangles','elapsedSeconds')}))


if __name__ == '__main__':
    main()
