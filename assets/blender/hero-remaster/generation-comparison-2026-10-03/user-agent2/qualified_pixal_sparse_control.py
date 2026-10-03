"""Qualify the installed Pixal runtime; never infer it from TRELLIS evidence.

Only forward synthetic controls here. Learned conditioning/model parity is
separate, and the known unsafe native half trilinear route remains disabled.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--contract', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    contract_path = Path(args.contract).resolve()
    contract = json.loads(contract_path.read_text())
    source = Path(contract['source'])
    assert subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == contract['revision']
    for path, digest in contract['sourcePins'].items():
        assert sha(path) == digest, 'Source changed: ' + path
    os.environ.update(ATTN_BACKEND='sdpa', SPARSE_ATTN_BACKEND='naive',
                      SPARSE_CONV_BACKEND='flex_gemm', FLEX_GEMM_BACKEND='metal')
    sys.path.insert(0, str(source))
    import numpy as np
    import torch
    import flex_gemm
    from flex_gemm import kernels
    from pixal3d.modules import sparse
    from pixal3d.modules.sparse import config as sparse_config
    from pixal3d.modules.sparse.conv import config as conv_config
    from qualified_sparse_operator_control import main as original_control
    assert torch.__version__ == contract['torch']
    assert str(Path(flex_gemm.__file__).resolve()) == contract['actualFlexGemm']
    assert str(Path(kernels.metal._C.__file__).resolve()) == contract['actualExtension']
    assert sparse_config.CONV == 'flex_gemm' and sparse_config.ATTN == 'naive'
    assert conv_config.FLEX_GEMM_ALGO == 'masked_implicit_gemm_splitk'
    assert conv_config.FLEX_GEMM_HASHMAP_RATIO == 2.0
    torch.set_num_threads(4)
    sys.argv = [sys.argv[0], '--out', args.out, '--protected-trilinear']
    original_control()
    out = Path(args.out).resolve()
    receipt_path = out / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    # Exercise the actual Pixal SparseConv3d wrapper using the persisted oracle
    # fixture. Weight storage is native Co,Kw,Kh,Kd,Ci after initialization.
    fixture = np.load(out / 'dense-tail-channels-float32.npz')
    coordinates = torch.from_numpy(fixture['coords']).to('mps')
    features = torch.from_numpy(fixture['features']).to('mps')
    value = sparse.SparseTensor(feats=features, coords=coordinates)
    layer = sparse.SparseConv3d(7, 5, 3, dilation=1, bias=True).to('mps')
    with torch.no_grad():
        layer.weight.copy_(torch.from_numpy(fixture['weights']).to('mps'))
        layer.bias.copy_(torch.from_numpy(fixture['bias']).to('mps'))
        actual = layer(value)
        repeated = layer(value)
    torch.mps.synchronize()
    got = actual.feats.cpu().numpy()
    module_error = float(np.max(np.abs(got - fixture['expected'])))
    module_record = {'class': type(layer).__module__ + '.' + type(layer).__name__,
                     'maxCPUFloat64Error': module_error, 'threshold': 1e-5,
                     'finite': bool(np.isfinite(got).all()),
                     'repeatByteIdentical': torch.equal(actual.feats.cpu(), repeated.feats.cpu()),
                     'coordinatesUnchanged': torch.equal(actual.coords.cpu(), coordinates.cpu()),
                     'featuresUnchanged': torch.equal(features.cpu(), torch.from_numpy(fixture['features']))}
    np.savez_compressed(out / 'actual-pixal-conv-wrapper.npz', actual=got, expected=fixture['expected'], coords=fixture['coords'])
    receipt.update(model='Pixal3D', contractSHA256=sha(contract_path),
                   wrapperSHA256=sha(__file__), actualSparseModule=module_record,
                   sparseBackend={'conv': sparse_config.CONV, 'attention': sparse_config.ATTN,
                                  'algorithm': conv_config.FLEX_GEMM_ALGO,
                                  'hashmapRatio': conv_config.FLEX_GEMM_HASHMAP_RATIO},
                   actualSourcePins=contract['sourcePins'],
                   limits=['Synthetic forward controls and actual Pixal wrapper only.',
                           'No learned conditioning, model generation, backward or CUDA parity.',
                           'Trilinear half/bfloat inputs use the owned float32 adapter, not unsafe native pointers.'])
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    assert module_error <= 1e-5 and all(module_record[k] for k in ('finite', 'repeatByteIdentical', 'coordinatesUnchanged', 'featuresUnchanged'))
    print(json.dumps({'cases': len(receipt['cases']), 'actualPixalWrapperError': module_error}))


if __name__ == '__main__':
    main()
