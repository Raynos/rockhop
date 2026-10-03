"""Owned SDPA math derivative, all keys retained, independent query tiles."""
import math
import torch


def query_tiled_attention(query, key, value, attn_mask=None, dropout_p=0.0,
                          is_causal=False, scale=None, enable_gqa=False):
    assert attn_mask is None and dropout_p == 0 and not is_causal and not enable_gqa
    assert query.shape[:-2] == key.shape[:-2] == value.shape[:-2]
    assert query.shape[-1] == key.shape[-1] and key.shape[-2] == value.shape[-2]
    factor = scale if scale is not None else 1 / math.sqrt(query.shape[-1])
    keys = key.float().transpose(-1, -2)
    values = value.float()
    result = torch.empty((*query.shape[:-1], value.shape[-1]), device=query.device, dtype=query.dtype)
    for start in range(0, query.shape[-2], 128):
        stop = min(start + 128, query.shape[-2])
        weights = torch.softmax((query[..., start:stop, :].float() @ keys) * factor, dim=-1)
        result[..., start:stop, :] = (weights @ values).to(query.dtype)
    return result
