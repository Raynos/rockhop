"""Actual installed sparse-attention operator versus independent CPU fp32 math."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['trellis', 'pixal'], required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    output = Path(args.out)
    assert not output.exists(), 'Fresh control directory required'
    base = Path('/Users/raynos/ml/img2mesh')
    root = base / ('trellis-mac/TRELLIS.2' if args.model == 'trellis' else 'Pixal3D-mac')
    package = 'trellis2' if args.model == 'trellis' else 'pixal3d'
    source = root / package / 'modules/sparse/attention/full_attn.py'
    assert sha(source) == args.source_sha256, 'Installed operator changed'
    os.environ.update(ATTN_BACKEND='sdpa', SPARSE_ATTN_BACKEND='naive',
                      SPARSE_CONV_BACKEND='none', PYTORCH_ENABLE_MPS_FALLBACK='1')
    sys.path.insert(0, str(root))
    if args.model == 'trellis':
        sys.path.append(str(base / 'trellis-mac/stubs'))
    import numpy as np
    import torch
    torch.set_num_threads(4)
    assert torch.backends.mps.is_available()
    basic = importlib.import_module(package + '.modules.sparse.basic')
    config = importlib.import_module(package + '.modules.sparse.config')
    operator = importlib.import_module(package + '.modules.sparse.attention.full_attn')
    assert config.ATTN == 'naive'
    output.mkdir(parents=True)
    started = time.monotonic()
    report = {'accepted': False, 'model': args.model, 'modelRuns': 0,
              'device': 'mps', 'torch': torch.__version__, 'source': str(source),
              'sourceSHA256': sha(source), 'recipeSHA256': sha(__file__),
              'backend': config.ATTN, 'seed': 42, 'cases': [],
              'definition': 'Actual installed one-batch VarLenTensor operator; selected queries compared with CPU float32 matmul/softmax from identical quantized inputs.',
              'limits': ['Synthetic operator controls do not establish model/CUDA parity.',
                         'Single batch, no padding; no complete DiT or mesh/conditioning validation.']}
    for tokens, amplitude, dtype_name in [(256, 1, 'float32'), (16384, 1, 'float32'),
                                          (16384, 4, 'float32'), (16384, 4, 'bfloat16')]:
        dtype = getattr(torch, dtype_name)
        generator = torch.Generator(device='cpu').manual_seed(42)
        q, k, v = [torch.randn(tokens, 2, 64, generator=generator) for _ in range(3)]
        # Unit RMS with a position rotation gives nontrivial normalized inputs.
        position = torch.arange(tokens, dtype=torch.float32)[:, None, None] * .013
        for data in (q, k):
            data /= data.square().mean(dim=-1, keepdim=True).sqrt()
            even, odd = data[..., ::2].clone(), data[..., 1::2].clone()
            data[..., ::2] = even * position.cos() - odd * position.sin()
            data[..., 1::2] = even * position.sin() + odd * position.cos()
            data *= amplitude
        q, k, v = [data.to(dtype) for data in (q, k, v)]
        selected = torch.linspace(0, tokens - 1, min(tokens, 257)).long().unique()
        qh = q[selected].float().permute(1, 0, 2)
        kh = k.float().permute(1, 2, 0)
        vh = v.float().permute(1, 0, 2)
        reference = ((qh @ kh) / 8).softmax(-1) @ vh
        reference = reference.permute(1, 0, 2).to(dtype).float()
        stamp = time.monotonic()
        with torch.inference_mode():
            actual = operator.sparse_scaled_dot_product_attention(
                *[basic.VarLenTensor(data.to('mps')) for data in (q, k, v)])
            torch.mps.synchronize()
            actual_full = actual.feats.detach().float().cpu()
        observed = actual_full[selected]
        error = (observed - reference).abs()
        tolerance = .0005 if dtype_name == 'float32' else .03125
        name = f'{tokens}-amplitude{amplitude}-{dtype_name}'
        archive = output / (name + '.npz')
        np.savez_compressed(archive, q=q.float().numpy(), k=k.float().numpy(),
                            v=v.float().numpy(), selected=selected.numpy(),
                            cpuReference=reference.numpy(), mpsObserved=observed.numpy())
        case = {'tokens': tokens, 'heads': 2, 'channels': 64, 'amplitude': amplitude,
                'dtype': dtype_name, 'selectedQueries': len(selected),
                'mpsSeconds': time.monotonic() - stamp,
                'allOutputsFinite': bool(torch.isfinite(actual_full).all()),
                'maxAbsoluteError': float(error.max()), 'meanAbsoluteError': float(error.mean()),
                'referenceStd': float(reference.std()), 'observedStd': float(observed.std()),
                'tolerance': tolerance, 'pass': bool(torch.isfinite(actual_full).all() and error.max() <= tolerance),
                'fixtureSHA256': sha(archive)}
        report['cases'].append(case)
        (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(case), flush=True)
        del actual, actual_full, q, k, v
        torch.mps.empty_cache()
    report['allCasesPass'] = all(case['pass'] for case in report['cases'])
    report['elapsedSeconds'] = time.monotonic() - started
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
