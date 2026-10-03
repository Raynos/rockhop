"""Owned MPS forward adapter for the installed float-only weighted sampler.

Keep native hashmaps, voxel centers, weights and missing-neighbor semantics.
The caller must qualify installed pins and measured output error first.
"""


def sample_with_float32_trilinear(native, feats, coords, shape, grid,
                                 mode='trilinear'):
    import torch

    assert feats.device.type == 'mps', 'Only the measured MPS route is supported'
    assert coords.dtype == torch.int32 and grid.dtype == torch.float32
    assert feats.dtype in (torch.float32, torch.float16, torch.bfloat16)
    assert mode in ('nearest', 'trilinear')
    if mode == 'trilinear' and feats.dtype != torch.float32:
        # The compiled unsuffixed weighted-sum kernel reads/writes float*.
        # Promote real feature values, not pointer reinterpretation; cast once
        # after unchanged native interpolation. No dense grid or zero filling.
        return native(feats.float(), coords, shape, grid, mode=mode).to(feats.dtype)
    return native(feats, coords, shape, grid, mode=mode)
