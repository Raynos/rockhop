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
    parser.add_argument('--signed-nearest', action='store_true')
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
    sentinel_probe = None
    if args.signed_nearest:
        from qualified_pixal_sparse_sampling import sample_with_signed_nearest
        from flex_gemm.ops import grid_sample as grid_module, utils
        from qualified_sparse_operator_control import grid_oracle
        native_grid = grid_module.grid_sample_3d
        probe_coords = np.asarray([[0, 0, 0, 0], [0, 1, 1, 1], [1, 0, 0, 0]], np.int32)
        probe_features = np.asarray([[0.25, 0.5], [0.75, 1.0], [1.25, 1.5]], np.float32)
        probe_queries = np.asarray([[[0.5, 0.5, 0.5], [1.5, 0.5, 0.5], [-2, -2, -2], [3, 3, 3]]]*2, np.float32)
        c = torch.from_numpy(probe_coords).to('mps')
        f = torch.from_numpy(probe_features).to('mps')
        q = torch.from_numpy(probe_queries).to('mps')
        shape = (2, 2, 2, 2, 2)
        keys, values = utils.init_hashmap(shape, 6, c.device)
        indices = kernels.cuda.hashmap_build_grid_sample_3d_nearest_neighbor_map(keys, values, c, q, 2, 2, 2).int()
        unsigned_valid = indices != 0xffffffff
        signed_valid = indices != -1
        original_values = native_grid(f, c, shape, q, mode='nearest')
        protected_values = sample_with_signed_nearest(native_grid, f, c, shape, q, mode='nearest')
        torch.mps.synchronize()
        expected = grid_oracle(probe_coords, probe_features, probe_queries, shape, 'nearest')
        sentinel_probe = {'signedIndices': indices.cpu().tolist(),
                          'originalUnsignedMask': unsigned_valid.cpu().tolist(),
                          'correctSignedMask': signed_valid.cpu().tolist(),
                          'maskDifferences': int((unsigned_valid != signed_valid).sum().item()),
                          'originalMaxError': float(np.max(abs(original_values.cpu().numpy()-expected))),
                          'protectedMaxError': float(np.max(abs(protected_values.cpu().numpy()-expected))),
                          'threshold': 1e-5}
        assert sentinel_probe['maskDifferences'] > 0 and sentinel_probe['originalMaxError'] > 1e-5
        assert sentinel_probe['protectedMaxError'] <= 1e-5
        # Owned process-local forward substitution; installed files untouched.
        grid_module.grid_sample_3d = lambda feats, coords, shape, grid, mode='trilinear': sample_with_signed_nearest(native_grid, feats, coords, shape, grid, mode)
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
    receipt.update(model='Pixal3D', signedNearestProtection=args.signed_nearest, sentinelProbe=sentinel_probe, contractSHA256=sha(contract_path),
                   wrapperSHA256=sha(__file__), actualSparseModule=module_record,
                   sparseBackend={'conv': sparse_config.CONV, 'attention': sparse_config.ATTN,
                                  'algorithm': conv_config.FLEX_GEMM_ALGO,
                                  'hashmapRatio': conv_config.FLEX_GEMM_HASHMAP_RATIO},
                   actualSourcePins=contract['sourcePins'],
                   limits=['Synthetic forward controls and actual Pixal wrapper only.',
                           'No learned conditioning, model generation, backward or CUDA parity.',
                           'Trilinear half/bfloat uses owned float32 adapter; optional nearest uses signed sentinel. Native files unchanged.'])
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    assert module_error <= 1e-5 and all(module_record[k] for k in ('finite', 'repeatByteIdentical', 'coordinatesUnchanged', 'featuresUnchanged'))
    print(json.dumps({'cases': len(receipt['cases']), 'actualPixalWrapperError': module_error}))


if __name__ == '__main__':
    main()
