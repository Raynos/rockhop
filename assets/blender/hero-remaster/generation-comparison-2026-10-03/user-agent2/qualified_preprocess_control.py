"""Invoke installed single-image preprocessing without constructing neural models."""
import argparse
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('image', 'image-sha256', 'source-sha256', 'out'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--model', choices=['hunyuan', 'trellis', 'pixal'], required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    image, output = Path(args.image), Path(args.out)
    assert sha(image) == args.image_sha256 and not output.exists()
    base = Path('/Users/raynos/ml/img2mesh')
    sources = {
        'hunyuan': base / 'Hunyuan3D-2.1/hy3dshape/hy3dshape/preprocessors.py',
        'trellis': base / 'trellis-mac/TRELLIS.2/trellis2/pipelines/trellis2_image_to_3d.py',
        'pixal': base / 'Pixal3D-mac/pixal3d/pipelines/pixal3d_image_to_3d.py'}
    source = sources[args.model]
    assert sha(source) == args.source_sha256
    os.environ.update(ATTN_BACKEND='sdpa', SPARSE_ATTN_BACKEND='naive',
                      SPARSE_CONV_BACKEND='none', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    import numpy as np
    import torch
    from PIL import Image
    torch.set_num_threads(4)
    original = Image.open(image).convert('RGBA')
    alpha = np.asarray(original)[..., 3]
    assert alpha.min() == 0 and alpha.max() == 255 and np.any(alpha > 204)
    output.mkdir(parents=True)
    if args.model == 'hunyuan':
        spec = importlib.util.spec_from_file_location('actual_hunyuan_preprocessor', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        processor = module.ImageProcessorV2(size=512, border_ratio=.15)
        pixels = processor(original, to_tensor=False)
        tensors = processor(original, to_tensor=True)
        conditioned = Image.fromarray(pixels['image'])
        Image.fromarray(pixels['mask'].squeeze()).save(output / 'conditioned-mask.png')
        np.savez_compressed(output / 'processor-tensors.npz',
                            image=tensors['image'].numpy(), mask=tensors['mask'].numpy())
        tensor_info = {k: {'shape': list(v.shape), 'dtype': str(v.dtype),
                           'min': float(v.min()), 'max': float(v.max()),
                           'allFinite': bool(torch.isfinite(v).all())} for k, v in tensors.items()}
        contract = 'RGBA PIL preserves RGB; nonzero-alpha crop; .15border; white composite; cv2 cubic512 RGB and nearest mask; tensor RGB[-1,1]. DINO518 normalization happens later.'
        signature = str(inspect.signature(processor.__call__))
        imported_source = str(inspect.getfile(module.ImageProcessorV2))
    else:
        root = base / ('trellis-mac/TRELLIS.2' if args.model == 'trellis' else 'Pixal3D-mac')
        package = 'trellis2' if args.model == 'trellis' else 'pixal3d'
        sys.path.insert(0, str(root))
        if args.model == 'trellis':
            sys.path.append(str(base / 'trellis-mac/stubs'))
        module_name = package + '.pipelines.' + ('trellis2_image_to_3d' if args.model == 'trellis' else 'pixal3d_image_to_3d')
        module = importlib.import_module(module_name)
        cls = getattr(module, 'Trellis2ImageTo3DPipeline' if args.model == 'trellis' else 'Pixal3DImageTo3DPipeline')
        # Genuine RGBA takes the mask branch; no pipeline/model initialization.
        processor = cls.__new__(cls)
        conditioned = processor.preprocess_image(original)
        signature = str(inspect.signature(cls.preprocess_image))
        imported_source = str(inspect.getfile(cls))
        tensor_info = None
        contract = 'Long-edge cap1024; original nonopaque RGBA avoids matting; alpha>204 crop; square multiplier' + ('1.0' if args.model == 'trellis' else '1.1') + '; RGB alpha-composite black. Stage DINO512/1024 normalization happens later.'
    assert Path(imported_source).resolve() == source.resolve()
    conditioned.save(output / 'conditioned-input.png')
    array = np.asarray(conditioned)
    report = {'accepted': False, 'modelRuns': 0, 'model': args.model,
              'inputPath': str(image), 'inputSHA256': sha(image), 'inputSize': list(original.size),
              'inputMode': original.mode, 'sourcePath': str(source), 'sourceSHA256': sha(source),
              'importedSourcePath': imported_source, 'callSignature': signature,
              'recipeSHA256': sha(__file__), 'preprocessContract': contract,
              'conditionedImagePath': str(output / 'conditioned-input.png'),
              'conditionedImageSHA256': sha(output / 'conditioned-input.png'),
              'conditionedSize': list(conditioned.size), 'conditionedMode': conditioned.mode,
              'RGBChannelMeans': array.mean(axis=(0, 1)).tolist(), 'processorTensors': tensor_info,
              'backgroundRemovalCalled': False,
              'limits': ['No neural models constructed or weights loaded.',
                         'Actual downstream DINO/NAF tensors, FOV estimation and neural noise must be recorded during inference.',
                         'Generated appearance reference has approximate camera/pose; no calibrated multiview or topology input.']}
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
