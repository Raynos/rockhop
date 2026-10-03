"""Qualify V-column decomposition with full Q/K and the real PBR processor."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import types

import torch
import torch.nn.functional as functional
from value_column_attention import value_column_attention


SOURCE = Path('/Users/raynos/ml/img2mesh/hunyuan21-view/hunyuan3d-paintpbr-v2-1/unet/attn_processor.py')
SOURCE_SHA = '6df282d094627733623ddeaa28a493a11252ea58e7b99e4d52240e17f4f71d0f'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tensor_info(value):
    return {'shape': list(value.shape), 'stride': list(value.stride()),
            'dtype': str(value.dtype), 'device': str(value.device)}


def independent_attention(query, key, value, **kwargs):
    assert kwargs.get('dropout_p', 0) == 0 and not kwargs.get('is_causal', False)
    assert kwargs.get('attn_mask') is None
    scale = kwargs.get('scale') or query.shape[-1] ** -.5
    scores = query.double() @ key.double().transpose(-1, -2) * scale
    return (torch.softmax(scores, dim=-1) @ value.double()).to(query.dtype)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(SOURCE) == SOURCE_SHA
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    torch.set_num_threads(4)
    assert torch.backends.mps.is_available()
    started = time.monotonic()
    report = {'accepted': False, 'modelRuns': 0, 'torch': torch.__version__,
              'torchGitVersion': torch.version.git_version,
              'prefillDisableEnv': os.environ.get('PYTORCH_MPS_DISABLE_PREFILL_ATTENTION'),
              'recipeSHA256': sha(__file__), 'adapterSHA256': sha(Path(__file__).with_name('value_column_attention.py')),
              'processorSHA256': sha(SOURCE), 'cases': [],
              'limits': ['Synthetic activations, no full learned UNet or CUDA parity.',
                         'Complete Q/K retained; only independent V columns decomposed.',
                         'No original unequal-width large MPS call: dense fallback exceeds the fixed guard.',
                         'No blind stock slicing, trained processor replacement, key or view truncation.']}
    def save():
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    # Exercise the installed custom projections, head reshape and material output order.
    spec = importlib.util.spec_from_file_location('agent2_paint_attention_control', SOURCE)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    torch.manual_seed(42)
    attn = owner.Attention(query_dim=320, cross_attention_dim=320, heads=5, dim_head=64,
                           dropout=0., residual_connection=True, rescale_output_factor=1.3)
    processor = owner.RefAttnProcessor2_0(query_dim=320, cross_attention_dim=320,
                                         heads=5, dim_head=64, pbr_setting=['albedo', 'mr'])
    attn.set_processor(processor)
    attn.eval()
    q = torch.randn(2, 37, 320)
    context = torch.randn(2, 19, 320)
    owner.F = types.SimpleNamespace(scaled_dot_product_attention=independent_attention)
    with torch.inference_mode():
        expected = attn(q, encoder_hidden_states=context)
    for device, dtype in [('cpu', torch.float32), ('mps', torch.float16)]:
        local = copy.deepcopy(attn).to(device=device, dtype=dtype)
        descriptors = []
        def split_sdpa(query, key, value, **kwargs):
            descriptors.append({'query': tensor_info(query), 'key': tensor_info(key), 'value': tensor_info(value)})
            return value_column_attention(query, key, value, **kwargs)
        owner.F = types.SimpleNamespace(scaled_dot_product_attention=split_sdpa)
        report['phase'] = 'full installed reference processor ' + device
        save()
        with torch.inference_mode():
            result = local(q.to(device=device, dtype=dtype), encoder_hidden_states=context.to(device=device, dtype=dtype)).cpu().float()
        error = float((result - expected).abs().max())
        material_difference = float((result[:, 0] - result[:, 1]).abs().max())
        entry = {'name': 'installedRefProcessor-' + device, 'QKV': descriptors,
                 'maxIndependentCPUError': error, 'finite': bool(torch.isfinite(result).all()),
                 'materialOutputDifference': material_difference, 'outputShape': list(result.shape)}
        report['cases'].append(entry)
        save()
        assert entry['finite'] and error <= (.000002 if device == 'cpu' else .002)
        assert result.shape == (2, 2, 37, 320) and material_difference > .01
        del local, result
    del attn, expected, q, context
    torch.mps.empty_cache()
    # Transposed head layout matches the actual processor's Q/K reshape.
    for name, batch, heads, nq, nk, amplitude in [('view768', 1, 1, 9216, 9216, 1.),
                                                ('view768HighAmplitude', 1, 1, 9216, 9216, 4.),
                                                ('eightViewReference768', 3, 5, 73728, 9216, 1.)]:
        generator = torch.Generator(device='cpu').manual_seed(42)
        qc = (torch.randn(batch, nq, heads, 64, generator=generator) * amplitude).half().transpose(1, 2)
        kc = (torch.randn(batch, nk, heads, 64, generator=generator) * amplitude).half().transpose(1, 2)
        vc = torch.randn(batch, nk, heads, 128, generator=generator).half().transpose(1, 2)
        query, key, value = [tensor.to('mps') for tensor in (qc, kc, vc)]
        selected = torch.tensor([0, nq // 2, nq - 1])
        expected = independent_attention(qc[:, :, selected], kc, vc)
        report['phase'] = name
        report['beforeCall'] = {'query': tensor_info(query), 'key': tensor_info(key), 'value': tensor_info(value),
                                'estimatedUnsplitFloat32ScoreGiB': batch * heads * nq * nk * 4 / 1024 ** 3}
        save()
        call_started = time.monotonic()
        with torch.inference_mode():
            result = value_column_attention(query, key, value).cpu()
        elapsed = time.monotonic() - call_started
        error = float((result[:, :, selected].float() - expected.float()).abs().max())
        entry = {'name': name, **report['beforeCall'], 'seconds': elapsed,
                 'allFinite': bool(torch.isfinite(result).all()), 'maxSelectedCPUError': error,
                 'allKeysRetained': True, 'valueColumnBlockWidth': 64, 'outputShape': list(result.shape)}
        report['cases'].append(entry)
        save()
        assert entry['allFinite'] and error <= .002 and result.shape[-1] == 128
        del query, key, value, qc, kc, vc, result, expected
        torch.mps.empty_cache()
    report.update(phase='controls passed', elapsedSeconds=time.monotonic() - started)
    save()


if __name__ == '__main__':
    main()
