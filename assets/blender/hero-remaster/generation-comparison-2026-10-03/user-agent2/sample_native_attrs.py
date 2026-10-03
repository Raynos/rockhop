"""CPU sparse voxel sampling for derived donor displays, never native mutation."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

UPSTREAM = Path('/Users/raynos/ml/img2mesh/trellis-mac/.venv/lib/python3.11/site-packages/flex_gemm/ops/grid_sample/grid_sample_torch.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sample(attrs, coords, grid_queries, chunk_size=32768):
    """Normalized trilinear weights around centres coords+.5; missing is explicit."""
    attrs = np.asarray(attrs)
    coords = np.asarray(coords)
    queries = np.asarray(grid_queries, dtype=np.float64)
    if (attrs.ndim != 2 or coords.shape != (len(attrs), 3) or
            not np.issubdtype(coords.dtype, np.integer) or
            queries.ndim != 2 or queries.shape[1] != 3 or
            not len(attrs) or not np.isfinite(attrs).all() or
            not np.isfinite(queries).all() or chunk_size <= 0):
        raise ValueError('Invalid finite sparse field/query arrays')
    low, high = coords.min(axis=0), coords.max(axis=0)
    extent = high.astype(np.int64) - low + 1
    if int(extent[0]) * int(extent[1]) * int(extent[2]) >= np.iinfo(np.int64).max:
        raise ValueError('Coordinate key range exceeds int64')
    def key(points):
        relative = points.astype(np.int64) - low
        return (relative[:, 0] * extent[1] + relative[:, 1]) * extent[2] + relative[:, 2]
    keys = key(coords)
    order = np.argsort(keys)
    sorted_keys = keys[order]
    if np.any(sorted_keys[1:] == sorted_keys[:-1]):
        raise ValueError('Duplicate voxel coordinates are ambiguous')
    values = np.zeros((len(queries), attrs.shape[1]), dtype=np.float64)
    support = np.zeros(len(queries), dtype=np.float64)
    for start in range(0, len(queries), chunk_size):
        query = queries[start:start + chunk_size]
        base = np.floor(query - .5).astype(np.int64)
        total = values[start:start + len(query)]
        weight_sum = support[start:start + len(query)]
        for offset in itertools.product((0, 1), repeat=3):
            neighbour = base + np.asarray(offset)
            inside = np.all((neighbour >= low) & (neighbour <= high), axis=1)
            index = np.searchsorted(sorted_keys, key(neighbour))
            safe_index = np.minimum(index, len(sorted_keys) - 1)
            found = inside & (index < len(sorted_keys)) & (sorted_keys[safe_index] == key(neighbour))
            weight = np.prod(1 - np.abs(neighbour + .5 - query), axis=1)
            weight = np.where(found, weight, 0)
            total += attrs[order[safe_index]] * weight[:, None]
            weight_sum += weight
        total /= np.maximum(weight_sum[:, None], 1e-12)
    return values.astype(np.float32), support.astype(np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', required=True)
    parser.add_argument('--native-sha256', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--metadata-sha256', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if sha(args.native) != args.native_sha256 or sha(args.metadata) != args.metadata_sha256:
        raise ValueError('Frozen archive/metadata changed')
    metadata = json.loads(Path(args.metadata).read_text())
    if metadata['archiveSHA256'] != args.native_sha256:
        raise ValueError('Native sidecar does not name this archive')
    output = Path(args.out)
    if output.exists():
        raise FileExistsError('Fresh derived output directory required')
    with np.load(args.native, allow_pickle=False) as raw:
        for name, pin in metadata['arrays'].items():
            if (str(raw[name].dtype) != pin['dtype'] or list(raw[name].shape) != pin['shape'] or
                    hashlib.sha256(raw[name].tobytes(order='C')).hexdigest() != pin['sha256CBytes']):
                raise ValueError('Native array sidecar mismatch: ' + name)
        vertices, attrs, coords, origin = [raw[name].copy() for name in ['vertices', 'attrs', 'coords', 'origin']]
    voxel_size = metadata['voxelSize']
    if not np.isfinite(voxel_size) or voxel_size <= 0:
        raise ValueError('Invalid voxel scale')
    values, support = sample(attrs, coords, (vertices - origin) / voxel_size)
    output.mkdir(parents=True)
    archive = output / 'sampled-vertex-attrs.npz'
    np.savez_compressed(archive, attrs=values, support=support)
    report = {'accepted': False, 'nativeSHA256': sha(args.native),
              'nativeMetadataSHA256': sha(args.metadata), 'recipeSHA256': sha(__file__),
              'upstreamSparseSamplerPath': str(UPSTREAM), 'upstreamSparseSamplerSHA256': sha(UPSTREAM),
              'definition': 'derived normalized trilinear voxel-centre samples at decoded vertices',
              'archiveSHA256': sha(archive), 'layout': metadata['layout'],
              'vertices': len(vertices), 'unsupportedVertices': int(np.count_nonzero(support == 0)),
              'partialSupportVertices': int(np.count_nonzero((support > 0) & (support < .99999))),
              'channelMin': values.min(axis=0).tolist(), 'channelMax': values.max(axis=0).tolist(),
              'limits': ['Native arrays unchanged', 'Not a UV bake, fitted garment or topology pass',
                         'Unsupported samples remain zero with explicit support mask; do not hide them',
                         'No model, GPU allocation, dense volume, remesh or cleanup']}
    (output / 'sampling.json').write_text(json.dumps(report, indent=2) + '\n')
    if sha(args.native) != args.native_sha256:
        raise ValueError('Native archive changed during read-only derivation')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
