"""Owned Pixal nearest forward adapter retaining the native Metal hashmap.

The installed op casts uint32 missing-neighbor0xffffffff to int32; compare
that signed tensor to -1. Qualify the actual library and runtime first.
"""


def sample_with_signed_nearest(native, feats, coords, shape, grid,
                               mode='trilinear'):
    import torch
    from flex_gemm import kernels
    from flex_gemm.ops import grid_sample, utils

    assert feats.device.type == 'mps'
    assert coords.dtype == torch.int32 and grid.dtype == torch.float32
    if mode != 'nearest':
        return native(feats, coords, shape, grid, mode=mode)
    assert feats.ndim == 2 and coords.ndim == 2 and coords.shape[1] == 4
    assert grid.ndim == 3 and grid.shape[2] == 3
    assert feats.shape[0] == coords.shape[0]
    channels, width, height, depth = shape[-4:]
    batch, count = grid.shape[:2]
    keys, values = utils.init_hashmap(shape, int(grid_sample.HASHMAP_RATIO * len(coords)), coords.device)
    indices = kernels.cuda.hashmap_build_grid_sample_3d_nearest_neighbor_map(
        keys, values, coords, grid, width, height, depth).int()
    valid = indices != -1
    safe_indices = indices.clamp_min(0)
    return valid.unsqueeze(-1) * feats.index_select(0, safe_indices.reshape(-1)).reshape(batch, count, channels)
