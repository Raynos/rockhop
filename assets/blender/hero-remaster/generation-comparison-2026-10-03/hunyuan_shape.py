"""Installed Hunyuan2.1 cheap shape probe; native arrays saved before validation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SOURCE = Path('/Users/raynos/ml/img2mesh/Hunyuan3D-2.1')
WEIGHTS = Path('/Users/raynos/projects/weights/manual/tencent/Hunyuan3D-2.1')
SOURCE_HEAD = '82920d643c0dc2f7bfd7255f45f62d386edfe60c'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True)
    parser.add_argument('--image-sha256', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    image = Path(args.image).resolve()
    assert sha(image) == args.image_sha256
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == SOURCE_HEAD
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    assert not (output / 'start-settings.json').exists()
    os.environ.update(HF_HOME='/Users/raynos/projects/weights/hf',
                      HF_MODULES_CACHE=str(SOURCE / 'runtime/hf-modules'))
    sys.path.insert(0, str(SOURCE / 'hy3dshape'))
    import numpy as np
    import torch
    import trimesh
    from PIL import Image
    import torchvision.transforms.functional as functional
    sys.modules['torchvision.transforms.functional_tensor'] = functional
    original_to = torch.Tensor.to
    def safe_to(self, *positional, **keywords):
        target = keywords.get('device', positional[0] if positional else None)
        if self.dtype == torch.float64 and str(target).startswith('mps'):
            self = self.float()
        return original_to(self, *positional, **keywords)
    torch.Tensor.to = safe_to
    assert torch.backends.mps.is_available()
    from hy3dshape import Hunyuan3DDiTFlowMatchingPipeline
    settings = {'accepted': False, 'model': 'Hunyuan3D-2.1', 'seed': 42,
                'steps': 8, 'octree': 192, 'chunks': 32768, 'guidance': 5.0,
                'device': 'mps', 'image': str(image), 'imageSHA256': sha(image),
                'sourceHEAD': SOURCE_HEAD, 'workerSHA256': sha(__file__),
                'weightsRevision': '0b94677654c57bb9a6b6845cd7b704ccf551d327',
                'cleanup': False, 'reduction': False, 'paint': False,
                'rawDefinition': 'mesh_v and mesh_f before export_to_trimesh'}
    (output / 'start-settings.json').write_text(json.dumps(settings, indent=2) + '\n')
    started = time.monotonic()
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(str(WEIGHTS), device='mps', use_safetensors=False)
    pipe.enable_flashvdm(mc_algo='mc')
    raw = pipe(image=Image.open(image).convert('RGBA'), num_inference_steps=8,
               octree_resolution=192, num_chunks=32768, guidance_scale=5.0,
               generator=torch.Generator(device='cpu').manual_seed(42), output_type='mesh')[0]
    assert raw is not None
    vertices, faces = np.asarray(raw.mesh_v).copy(), np.asarray(raw.mesh_f).copy()
    np.savez_compressed(output / 'native.npz', vertices=vertices, faces=faces)
    good = bool(vertices.ndim == 2 and vertices.shape[1] == 3 and faces.ndim == 2
                and faces.shape[1] == 3 and len(vertices) and len(faces)
                and np.isfinite(vertices).all() and np.isfinite(faces).all()
                and (faces >= 0).all() and (faces < len(vertices)).all()
                and (faces == np.floor(faces)).all())
    settings.update(validNativeArrays=good, vertices=len(vertices), faces=len(faces),
                    nonfiniteVertexElements=int((~np.isfinite(vertices)).sum()),
                    nativeSHA256=sha(output / 'native.npz'), elapsedSeconds=time.monotonic() - started)
    (output / 'generation.json').write_text(json.dumps(settings, indent=2) + '\n')
    assert good, 'Native arrays retained; rejected before any display processing'
    display = trimesh.Trimesh(vertices=vertices.copy(), faces=faces[:, ::-1].copy(), process=False)
    display.export(output / 'native-display.glb')
    print(json.dumps(settings), flush=True)


if __name__ == '__main__':
    main()
