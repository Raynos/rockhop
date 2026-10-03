"""Actual FlashVDM coarse mini-grid attention, packed versus serial groups."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    source = Path('/Users/raynos/ml/img2mesh/Hunyuan3D-2.1/hy3dshape/hy3dshape/models/autoencoders/attention_processors.py')
    assert sha(source) == args.source_sha256
    output = Path(args.out)
    assert not output.exists()
    import numpy as np
    import torch
    torch.set_num_threads(4)
    assert torch.backends.mps.is_available()
    spec = importlib.util.spec_from_file_location('actual_flashvdm_processor', source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    output.mkdir(parents=True)
    generator = torch.Generator(device='cpu').manual_seed(42)
    q = torch.randn(3, 16, 13824, 64, generator=generator).to(torch.float16).to('mps')
    k = torch.randn(3, 16, 4096, 64, generator=generator).to(torch.float16).to('mps')
    v = torch.randn(3, 16, 4096, 64, generator=generator).to(torch.float16).to('mps')
    processor = module.FlashVDMCrossAttentionProcessor(topk=True)
    with torch.inference_mode():
        packed = processor(None, q, k, v).cpu()
        serial = []
        for i in range(3):
            processor.topk = True
            serial.append(processor(None, q[i:i + 1], k[i:i + 1], v[i:i + 1]).cpu())
        serial = torch.cat(serial)
    error = (packed.float() - serial.float()).abs()
    selected = torch.linspace(0, 13823, 257).long()
    archive = output / 'selected-output.npz'
    np.savez_compressed(archive, packed=packed[:, :, selected].numpy(),
                        serial=serial[:, :, selected].numpy())
    report = {'accepted': False, 'modelRuns': 0, 'sourcePath': str(source),
              'sourceSHA256': sha(source), 'recipeSHA256': sha(__file__),
              'torch': torch.__version__, 'device': 'mps', 'dtype': 'float16',
              'groups': 3, 'heads': 16, 'queriesPerGrid': 13824,
              'latentKeys': 4096, 'channels': 64, 'seed': 42,
              'method': 'Actual coarse FlashVDM adaptive-KV processor, same inputs packed3groups versus serial1group; no neural weights.',
              'allOutputsFinite': bool(torch.isfinite(packed).all() and torch.isfinite(serial).all()),
              'maxAbsoluteError': float(error.max()), 'meanAbsoluteError': float(error.mean()),
              'packedStd': float(packed.float().std()), 'serialStd': float(serial.float().std()),
              'byteIdenticalOutputs': bool(torch.equal(packed, serial)),
              'selectedOutputSHA256': sha(archive),
              'limits': ['Known synthetic operator inputs, not complete geometry-decoder/CUDA equivalence.',
                         'Supported query batching preserves grid groups mathematically; actual neural retry must retain sampler/decode settings and record any numerical change.']}
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
