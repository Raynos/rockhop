"""Split only independent V columns; preserve complete Q/K and material order."""
import torch
import torch.nn.functional as functional


def value_column_attention(query, key, value, attn_mask=None, dropout_p=0.0,
                           is_causal=False, scale=None, enable_gqa=False):
    assert dropout_p == 0 and not is_causal and not enable_gqa
    width = query.shape[-1]
    assert key.shape[-1] == width and value.shape[-1] % width == 0
    outputs = []
    for start in range(0, value.shape[-1], width):
        columns = value[..., start:start + width].contiguous()
        outputs.append(functional.scaled_dot_product_attention(
            query, key, columns, attn_mask=attn_mask, dropout_p=0., is_causal=False,
            scale=scale, enable_gqa=False))
    return torch.cat(outputs, dim=-1)
