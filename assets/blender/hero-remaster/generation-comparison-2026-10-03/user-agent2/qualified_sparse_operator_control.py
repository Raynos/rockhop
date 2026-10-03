"""Independent coordinate oracles for installed TRELLIS Metal operators.

This qualifies synthetic forward contracts, not learned model/CUDA parity.
Run only beneath the shared bounded controller; never change installed code.
"""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import time

import numpy as np


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'SHA256': hashlib.sha256(path.read_bytes()).hexdigest()}


def conv_oracle(coords, feats, weights, bias, shape, dilation):
    """Cross-correlation in NCWHD, independently address a Python dictionary."""
    lookup = {tuple(c): i for i, c in enumerate(coords.tolist())}
    kernel = weights.shape[1:4]
    neighbors = np.full((len(coords), np.prod(kernel)), 0xffffffff, np.uint32)
    result = np.broadcast_to(bias.astype(np.float64), (len(coords), len(bias))).copy()
    for row, (batch, *position) in enumerate(coords.tolist()):
        for tap, index in enumerate(itertools.product(*(range(k) for k in kernel))):
            xyz = tuple(p + (i - k // 2) * d
                        for p, i, k, d in zip(position, index, kernel, dilation))
            if any(p < 0 or p >= s for p, s in zip(xyz, shape[2:])):
                continue
            source = lookup.get((batch, *xyz))
            if source is not None:
                neighbors[row, tap] = source
                result[row] += weights[(slice(None), *index)].astype(np.float64) @ feats[source].astype(np.float64)
    return result, neighbors


def grid_oracle(coords, feats, points, shape, mode):
    """Voxel units, center +0.5; trilinear renormalizes existing neighbors."""
    lookup = {tuple(c): i for i, c in enumerate(coords.tolist())}
    result = np.zeros((*points.shape[:2], feats.shape[1]), np.float64)
    for batch, queries in enumerate(points):
        for row, query in enumerate(queries):
            if mode == 'nearest':
                xyz = tuple(int(q) for q in query)  # native truncation toward zero
                if all(0 <= p < s for p, s in zip(xyz, shape[2:])):
                    source = lookup.get((batch, *xyz))
                    if source is not None:
                        result[batch, row] = feats[source]
                continue
            base = np.floor(query.astype(np.float64) - 0.5).astype(int)
            weight_sum = 0.0
            for offset in itertools.product((0, 1), repeat=3):
                xyz = tuple(base + offset)
                if not all(0 <= p < s for p, s in zip(xyz, shape[2:])):
                    continue
                source = lookup.get((batch, *xyz))
                if source is None:
                    continue
                weight = float(np.prod(1.0 - np.abs(query.astype(np.float64) - np.asarray(xyz) - 0.5)))
                weight_sum += weight
                result[batch, row] += weight * feats[source].astype(np.float64)
            if weight_sum >= 1e-12:
                result[batch, row] /= weight_sum
            else:
                result[batch, row] = 0
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--protected-trilinear', action='store_true')
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Bounded controller required'
    import torch
    import flex_gemm
    from flex_gemm import kernels
    from flex_gemm.ops import spconv
    from flex_gemm.ops.grid_sample import grid_sample_3d
    from qualified_sparse_sampling import sample_with_float32_trilinear

    assert torch.backends.mps.is_available()
    assert kernels._BACKEND == 'metal'
    assert spconv.ALGORITHM == spconv.Algorithm.MASKED_IMPLICIT_GEMM_SPLITK
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {'accepted': False, 'control': 'synthetic forward only',
              'torch': torch.__version__, 'flexGemm': pin(flex_gemm.__file__),
              'backend': kernels._BACKEND, 'algorithm': spconv.ALGORITHM,
              'protectedTrilinear': args.protected_trilinear,
              'adapter': pin(Path(__file__).with_name('qualified_sparse_sampling.py')),
              'compiledExtension': pin(kernels.metal._C.__file__),
              'metallib': pin(Path(kernels.metal.__file__).parent / 'flex_gemm.metallib'),
              'ops': [pin(Path(flex_gemm.__file__).parent / p) for p in
                      ('ops/spconv/submanifold_conv3d.py', 'ops/grid_sample/grid_sample.py')],
              'limits': ['No learned weights, full model, backward or CUDA parity.',
                         'Synthetic sparse voxel values; learned input capture remains required.'],
              'cases': []}
    started = time.monotonic()
    rng = np.random.default_rng(42)

    def save():
        report['elapsedSeconds'] = time.monotonic() - started
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')

    save()
    # Dyadic axis-coded features and nonuniform taps expose swaps and cross-batch leaks.
    for label, channels, kernel, dilation, holes in (
        ('dense-tail-channels', (7, 5), (3, 3, 3), (1, 1, 1), False),
        ('holes-dilation', (32, 32), (3, 3, 3), (2, 1, 2), True),
        ('anisotropic-axis', (64, 64), (3, 1, 3), (1, 2, 1), True)):
        ci, co = channels
        shape = (2, ci, 4, 5, 6)
        coords = np.asarray([p for p in itertools.product(range(2), range(4), range(5), range(6))
                             if not holes or (p[1] + 2*p[2] + 3*p[3]) % 4 != 1], np.int32)
        # Unsorted, with >64 rows and partial final mask block.
        coords = coords[rng.permutation(len(coords))].copy()
        codes = coords @ np.asarray([128, 16, 4, 1], np.int32)
        feats = ((codes[:, None] + 3*np.arange(ci)[None]) % 31 - 15).astype(np.float32) / 32
        weights = rng.integers(-4, 5, (co, *kernel, ci)).astype(np.float32) / 512
        bias = rng.integers(-4, 5, co).astype(np.float32) / 128
        for dtype, tolerance in ((torch.float32, 1e-5), (torch.float16, 0.001), (torch.bfloat16, 0.01)):
            f = torch.from_numpy(feats).to('mps', dtype).contiguous()
            w = torch.from_numpy(weights).to('mps', dtype).contiguous()
            b = torch.from_numpy(bias).to('mps', dtype)
            c = torch.from_numpy(coords).to('mps').contiguous()
            expected, neighbor_expected = conv_oracle(coords, f.float().cpu().numpy(), w.float().cpu().numpy(), b.float().cpu().numpy(), shape, dilation)
            before = [t.cpu().clone() for t in (f, w, b, c)]
            actual, cache = spconv.sparse_submanifold_conv3d(f, c, shape, w, b, dilation=dilation)
            repeat, reused = spconv.sparse_submanifold_conv3d(f, c, shape, w, b, neighbor_cache=cache, dilation=dilation)
            torch.mps.synchronize()
            values = actual.float().cpu().numpy()
            neighbors = cache['neighbor_map'].cpu().numpy()
            key = f'{label}-{str(dtype).split(".")[-1]}'
            archive = out / f'{key}.npz'
            np.savez_compressed(archive, coords=coords, features=f.float().cpu().numpy(), weights=w.float().cpu().numpy(), bias=b.float().cpu().numpy(), expected=expected, actual=values, neighbors=neighbors, expectedNeighbors=neighbor_expected)
            record = {'kind': 'conv', 'case': key, 'rows': len(coords), 'channels': channels,
                      'shape': shape, 'kernel': kernel, 'dilation': dilation,
                      'archive': pin(archive), 'maxCPUFloat64Error': float(np.max(np.abs(values-expected))),
                      'threshold': tolerance, 'finite': bool(np.isfinite(values).all()),
                      'neighborMapExact': bool(np.array_equal(neighbors, neighbor_expected)),
                      'cacheSameObject': reused is cache, 'repeatByteIdentical': torch.equal(actual.cpu(), repeat.cpu()),
                      'inputsUnchanged': all(torch.equal(t.cpu(), original) for t, original in zip((f,w,b,c), before))}
            report['cases'].append(record)
            save()
            assert record['finite'] and record['maxCPUFloat64Error'] <= tolerance, record
            assert all(record[k] for k in ('neighborMapExact', 'cacheSameObject', 'repeatByteIdentical', 'inputsUnchanged')), record

    # Different centers, missing cells, batch values, boundaries and unsupported space.
    ci = 7
    shape = (2, ci, 4, 5, 6)
    coords = np.asarray([p for p in itertools.product(range(2), range(4), range(5), range(6))
                         if (p[1] + 2*p[2] + 3*p[3]) % 4 != 1], np.int32)
    feats = ((coords @ np.asarray([128,16,4,1]))[:,None] + np.arange(ci)).astype(np.float32) / 64
    queries = np.asarray([[0.5,0.5,0.5], [1.5,2.5,3.5], [2,2,2], [1.75,2.125,3.875],
                          [0,0,0], [-0.25,0.5,0.5], [-2,-2,-2], [4.25,4.75,5.75],
                          [6,7,8], [3.5,4.5,5.5], [0.5,0.5,1.5]], np.float32)
    queries = np.stack((queries, queries[::-1].copy()))
    for dtype, tolerance in ((torch.float32, 1e-5), (torch.float16, 0.002), (torch.bfloat16, 0.02)):
        f = torch.from_numpy(feats).to('mps', dtype).contiguous()
        c = torch.from_numpy(coords).to('mps').contiguous()
        q = torch.from_numpy(queries).to('mps').contiguous()
        for mode in ('nearest', 'trilinear'):
            assert args.protected_trilinear or dtype == torch.float32 or mode == 'nearest', 'Known unsafe native low-precision weighted-sum route is disabled'
            expected = grid_oracle(coords, f.float().cpu().numpy(), queries, shape, mode)
            before = [t.cpu().clone() for t in (f, c, q)]
            if args.protected_trilinear:
                actual = sample_with_float32_trilinear(grid_sample_3d, f, c, shape, q, mode)
            else:
                actual = grid_sample_3d(f, c, shape, q, mode=mode)
            torch.mps.synchronize()
            values = actual.float().cpu().numpy()
            key = f'grid-{mode}-{str(dtype).split(".")[-1]}'
            archive = out / f'{key}.npz'
            np.savez_compressed(archive, coords=coords, features=f.float().cpu().numpy(), queries=queries, expected=expected, actual=values)
            record = {'kind': 'grid', 'case': key, 'archive': pin(archive),
                      'resultShape': list(values.shape), 'threshold': tolerance,
                      'float32Promotion': args.protected_trilinear and mode == 'trilinear' and dtype != torch.float32,
                      'outputDtypePreserved': actual.dtype == dtype,
                      'inputsUnchanged': all(torch.equal(t.cpu(), original) for t, original in zip((f,c,q), before)),
                      'maxCPUFloat64Error': float(np.max(np.abs(values-expected))),
                      'finite': bool(np.isfinite(values).all())}
            report['cases'].append(record)
            save()
            assert values.shape == expected.shape and record['finite'] and record['maxCPUFloat64Error'] <= tolerance, record
            assert record['outputDtypePreserved'] and record['inputsUnchanged'], record
    report['status'] = 'All synthetic forward contracts pass; learned/model proof pending'
    save()
    print(json.dumps({'status': report['status'], 'cases': len(report['cases'])}))


if __name__ == '__main__':
    main()
