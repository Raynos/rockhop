"""Owned instance adapter: CPU numpy getters must not mutate renderer state."""
import numpy as np


def preserve_getter_state(renderer):
    original = renderer.get_mesh
    def copied_getter(*args, **kwargs):
        positions, uv = renderer.vtx_pos.clone(), renderer.vtx_uv.clone()
        try:
            return tuple(np.array(value, copy=True) for value in original(*args, **kwargs))
        finally:
            renderer.vtx_pos = positions
            renderer.vtx_uv = uv
    renderer.get_mesh = copied_getter
