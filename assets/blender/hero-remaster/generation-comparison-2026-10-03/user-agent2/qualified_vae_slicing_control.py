"""Compare actual learned VAE decode packed and official independent-batch slicing."""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import time

import numpy as np
import torch
from diffusers import AutoencoderKL


ROOT = Path('/Users/raynos/ml/img2mesh/hunyuan21-view/hunyuan3d-paintpbr-v2-1/vae')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--latents', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(ROOT / 'config.json') == '424117cb534ce03497c41305ed868980123917b2b6abba4bbaa615e968772903'
    assert sha(ROOT / 'diffusion_pytorch_model.bin') == '1b4889b6b1d4ce7ae320a02dedaeff1780ad77d415ea0d744b476155c6377ddc'
    assert sha(args.latents) == '15bc15c3b47bd9d95fbc5fe3700e8973e11e4b61307db689b44ed032c9f3cbc8'
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    started = time.monotonic()
    torch.set_num_threads(4)
    model = AutoencoderKL.from_pretrained(ROOT, torch_dtype=torch.float16, local_files_only=True).to('mps').eval()
    assert sum(p.numel() for p in model.parameters()) == 83653863
    with np.load(args.latents, allow_pickle=False) as archive:
        original = archive['actual-encode_images-01'].copy()
    assert original.shape == (1, 8, 4, 96, 96) and original.dtype == np.float16 and np.isfinite(original).all()
    # Two genuine view latents at full768 resolution, no spatial crop/tiling.
    latent = torch.from_numpy(original[0, :2]).to('mps') / model.config.scaling_factor
    initial_bytes = latent.cpu().numpy().copy()
    report = {'accepted': False, 'newShapeOrSamplerRuns': 0, 'torch': torch.__version__,
              'recipeSHA256': sha(__file__), 'vaeSourceSHA256': sha(inspect.getfile(AutoencoderKL)),
              'weightSHA256': sha(ROOT / 'diffusion_pytorch_model.bin'), 'latentArchiveSHA256': sha(args.latents),
              'inputShape': list(latent.shape), 'inputDtype': str(latent.dtype),
              'outputPixelMaxDifferenceThreshold': 2, 'phase': 'packed decode',
              'limits': ['Two real encoded conditioning latents, not final sampled16-view PBR latents.',
                         'Packed-vs-sliced same learned MPS VAE, not independent CUDA equivalence.',
                         'Native official batch slicing only; no spatial tiling or trained attention replacement.']}
    def save():
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    model.disable_slicing()
    with torch.inference_mode():
        packed = model.decode(latent, return_dict=False)[0].cpu().numpy().copy()
    report.update(phase='official independent batch slicing', packedFinite=bool(np.isfinite(packed).all()))
    save()
    torch.mps.synchronize()
    torch.mps.empty_cache()
    model.enable_slicing()
    assert model.use_slicing and not model.use_tiling
    with torch.inference_mode():
        sliced = model.decode(latent, return_dict=False)[0].cpu().numpy().copy()
    assert packed.shape == sliced.shape == (2, 3, 768, 768)
    # Diffusers' denormalization/rounding is the final visible-image contract.
    def pixels(values):
        return np.rint(np.clip(values.astype(np.float32) / 2 + .5, 0, 1) * 255).astype(np.uint8)
    packed_pixels, sliced_pixels = pixels(packed), pixels(sliced)
    difference = np.abs(packed.astype(np.float32) - sliced.astype(np.float32))
    pixel_difference = np.abs(packed_pixels.astype(np.int16) - sliced_pixels.astype(np.int16))
    report.update(phase='decode comparison measured', outputShape=list(sliced.shape),
                  slicedFinite=bool(np.isfinite(sliced).all()), maxFloatError=float(difference.max()),
                  meanFloatError=float(difference.mean()), outputsByteIdentical=bool(np.array_equal(packed, sliced)),
                  maxPixelDifference=int(pixel_difference.max()), pixelsByteIdentical=bool(np.array_equal(packed_pixels, sliced_pixels)),
                  inputBytesUnchanged=bool(np.array_equal(latent.cpu().numpy(), initial_bytes)),
                  elapsedSeconds=time.monotonic() - started)
    np.savez_compressed(out / 'decoded-comparison.npz', packed=packed, sliced=sliced,
                        packedPixels=packed_pixels, slicedPixels=sliced_pixels)
    report['outputArchiveSHA256'] = sha(out / 'decoded-comparison.npz')
    save()
    assert report['packedFinite'] and report['slicedFinite'] and report['inputBytesUnchanged']
    assert report['maxPixelDifference'] <= report['outputPixelMaxDifferenceThreshold']
    report['phase'] = 'decode controls passed'
    save()


if __name__ == '__main__':
    main()
