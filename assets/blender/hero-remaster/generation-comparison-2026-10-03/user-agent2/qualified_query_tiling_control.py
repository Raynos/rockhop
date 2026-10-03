"""Known SDPA tensors at768-view token counts; selected independent CPU math."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import torch
import torch.nn.functional as functional
import numpy as np
from query_tiled_attention import query_tiled_attention


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    torch.set_num_threads(4)
    assert torch.backends.mps.is_available()
    source = Path('/Users/raynos/ml/img2mesh/hunyuan21-view/hunyuan3d-paintpbr-v2-1/unet/attn_processor.py')
    assert source.read_text().count('F.scaled_dot_product_attention(') == 1
    started = time.monotonic()
    report = {'accepted': False, 'modelRuns': 0, 'torch': torch.__version__,
              'recipeSHA256': sha(__file__), 'adapterSHA256': sha(Path(__file__).with_name('query_tiled_attention.py')),
              'installedPaintProcessorSHA256': sha(source), 'cases': [],
              'limits': ['Synthetic known tensors, not full model activations or CUDA equivalence.',
                         'Long case uses one independent head/batch to avoid full paint memory allocation.',
                         'All key/value tokens retained; no view reduction, key truncation or model patch.',
                         'Owned float32 attention is a numerical derivative; report roundoff, not byte parity.']}
    for case, batch, heads, nq, nk, amplitude in [('view768', 2, 5, 9216, 9216, 1.),
                                                ('view768HighAmplitude', 2, 5, 9216, 9216, 4.),
                                                ('eightViewKeys768', 1, 1, 9216, 73728, 1.)]:
        generator = torch.Generator(device='cpu').manual_seed(42)
        qc = torch.randn(batch, heads, nq, 64, generator=generator) * amplitude
        kc = torch.randn(batch, heads, nk, 64, generator=generator) * amplitude
        vc = torch.randn(batch, heads, nk, 64, generator=generator)
        qc, kc, vc = [value.half() for value in (qc, kc, vc)]
        query, key, value = [item.to('mps') for item in (qc, kc, vc)]
        selected = torch.linspace(0, nq - 1, 33).long()
        # Independent selected-query CPU matmul/softmax, no SDPA or owned helper.
        scores = qc[:, :, selected].float() @ kc.float().transpose(-1, -2) / 8
        expected = (torch.softmax(scores, dim=-1) @ vc.float()).half()
        with torch.inference_mode():
            tiled = query_tiled_attention(query, key, value).cpu()
            original = functional.scaled_dot_product_attention(query, key, value, dropout_p=0., is_causal=False).cpu()
        metrics = {}
        for name, result in [('originalMPS', original), ('ownedTiledFloat32', tiled)]:
            sampled = result[:, :, selected]
            error = (sampled.float() - expected.float()).abs()
            metrics[name] = {'allFinite': bool(torch.isfinite(result).all()),
                             'maxSelectedCPUError': float(error.max()), 'meanSelectedCPUError': float(error.mean()),
                             'outputStd': float(result.float().std()),
                             'selectedOutputsIdenticalToCPU': bool(torch.equal(sampled, expected))}
        difference = (tiled.float() - original.float()).abs()
        archive = out / (case + '.npz')
        np.savez_compressed(archive, originalSelected=original[:, :, selected].numpy(),
                            tiledSelected=tiled[:, :, selected].numpy(), expected=expected.numpy())
        entry = {'name': case, 'batch': batch, 'heads': heads, 'queries': nq, 'keys': nk, 'channels': 64,
                 'inputDtype': 'float16', 'queryKeyAmplitude': amplitude, 'outputs': metrics,
                 'maxFullTiledVersusOriginalError': float(difference.max()),
                 'fullOutputsByteIdentical': bool(torch.equal(tiled, original)), 'fixtureSHA256': sha(archive)}
        report['cases'].append(entry)
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        assert metrics['ownedTiledFloat32']['allFinite'] and metrics['ownedTiledFloat32']['maxSelectedCPUError'] <= .002
        del query, key, value, tiled, original, difference, scores, expected, qc, kc, vc
        torch.mps.empty_cache()
    report['allOwnedControlsPass'] = True
    report['elapsedSeconds'] = time.monotonic() - started
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
