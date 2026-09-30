"""Installed Pixal worker with its existing cache hooks and early shape save.

No shared source changes. Generation remains 1024 cascade; only the export
atlas is reduced. Save sampled latents before decoding and dense shape before
texture decoding, so an export/decoder failure cannot erase completed stages.
"""
import gc
import json
import sys
from pathlib import Path
import numpy as np

PORT = Path('/Users/raynos/ml/img2mesh/Pixal3D-mac')
sys.path.insert(0, str(PORT))
import generate_mps as installed

args = installed.parse_args()
args.low_vram = True
installed.parse_args = lambda: args
original_load = installed.load_pipeline
out = Path(args.output).parent


def load(*a, **kw):
    pipeline = original_load(*a, **kw)
    decode = pipeline.decode_latent
    shape_decode = pipeline.decode_shape_slat

    def decode_with_checkpoint(shape, texture, resolution):
        gc.collect()
        installed.maybe_empty_cache(pipeline.device)
        installed.torch.save({
            'shape_feats': shape.feats.detach().cpu(),
            'shape_coords': shape.coords.detach().cpu(),
            'texture_feats': texture.feats.detach().cpu(),
            'texture_coords': texture.coords.detach().cpu(),
            'resolution': resolution,
        }, out / 'sampled-latents.pt')
        print('[Checkpoint] Sampled latents retained before decode', flush=True)
        return decode(shape, texture, resolution)

    def shape_with_checkpoint(slat, resolution):
        result = shape_decode(slat, resolution)
        meshes, _ = result
        for i, mesh in enumerate(meshes):
            payload = {'vertices': mesh.vertices.detach().cpu().numpy(),
                       'faces': mesh.faces.detach().cpu().numpy(),
                       'resolution': np.int32(resolution)}
            for name in ['fdg_coords', 'fdg_dual_vertices', 'fdg_intersected', 'fdg_split_weight']:
                if hasattr(mesh, name):
                    payload[name] = getattr(mesh, name).detach().cpu().numpy()
            np.savez(out / f'decoded-shape-{i}.npz', **payload)
            print('[Checkpoint] Dense shape retained before texture decode',
                  json.dumps({'vertices': len(payload['vertices']), 'faces': len(payload['faces'])}), flush=True)
        return result

    pipeline.decode_latent = decode_with_checkpoint
    pipeline.decode_shape_slat = shape_with_checkpoint
    return pipeline


installed.load_pipeline = load
installed.main()
