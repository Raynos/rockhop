"""One bounded TRELLIS probe; exact decoded arrays before any display export."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SOURCE = Path('/Users/raynos/ml/img2mesh/trellis-mac')
MODEL = SOURCE / 'TRELLIS.2'
VIEW = Path('/Users/raynos/ml/img2mesh/trellis-view')
EXPECTED_SOURCE = 'd58628f4f5b9c3de8274cb110074154f4b31cef2'
EXPECTED_MODEL = '75fbf0183001ed9876c8dbb35de6b68552ee08bd'
EXPECTED_MODULE = '48a47e42f0d4f116701502730226216364dbfc3fe394343b3646170fe27ccc58'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('image', 'image-sha256', 'contract', 'contract-sha256',
                 'view-sha256', 'out'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') != str(os.getppid()):
        raise RuntimeError('Run as the reviewed bounded controller owned child')
    image = Path(args.image).resolve()
    contract = Path(args.contract).resolve()
    if sha(image) != args.image_sha256 or sha(contract) != args.contract_sha256:
        raise ValueError('Qualified input/contract bytes changed')
    json.loads(contract.read_text())
    config = VIEW / 'pipeline.json'
    if sha(config) != args.view_sha256:
        raise ValueError('Installed pipeline config changed')
    for folder, expected in ((SOURCE, EXPECTED_SOURCE), (MODEL, EXPECTED_MODEL)):
        actual = subprocess.check_output(['git', '-C', str(folder), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != expected:
            raise ValueError('Installed source HEAD changed: ' + str(folder))
    module = MODEL / 'trellis2/pipelines/trellis2_image_to_3d.py'
    if sha(module) != EXPECTED_MODULE:
        raise ValueError('Installed model pipeline bytes changed')
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    settings_path = output / 'start-settings.json'
    if settings_path.exists() or (output / 'native.npz').exists():
        raise FileExistsError('Fresh numbered probe directory required')
    settings = {'accepted': False, 'model': 'TRELLIS.2', 'seed': 42,
                'pipeline': '512', 'stepsPerStage': 8, 'device': 'mps',
                'image': str(image), 'imageSHA256': sha(image),
                'contract': str(contract), 'contractSHA256': sha(contract),
                'viewSHA256': sha(config), 'sourceHEAD': EXPECTED_SOURCE,
                'nestedModelHEAD': EXPECTED_MODEL, 'pipelineModuleSHA256': sha(module),
                'workerSHA256': sha(__file__), 'cleanup': False,
                'reduction': False, 'displayExport': 'geometry only; diagnostic donor',
                'worldScale': 'native normalized output; integration fit still required',
                'preprocessing': 'upstream alpha crop/square/black composite, saved separately'}
    settings_path.write_text(json.dumps(settings, indent=2) + '\n')
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      PYTORCH_ENABLE_MPS_FALLBACK='1', ATTN_BACKEND='sdpa',
                      SPARSE_ATTN_BACKEND='sdpa', SPARSE_CONV_BACKEND='flex_gemm')
    sys.path.insert(0, str(MODEL))
    sys.path.insert(0, str(SOURCE))
    sys.path.append(str(SOURCE / 'stubs'))
    import numpy as np
    import torch
    import trimesh
    from PIL import Image
    from native_save import save_native
    from trellis2.pipelines.trellis2_image_to_3d import Trellis2ImageTo3DPipeline
    if not torch.backends.mps.is_available():
        raise RuntimeError('MPS unavailable; do not silently change device')
    started = time.monotonic()
    pipe = Trellis2ImageTo3DPipeline.from_pretrained(str(VIEW))
    pipe.rembg_model.model.float()
    pipe.to(torch.device('mps'))
    original = Image.open(image).convert('RGBA')
    conditioned = pipe.preprocess_image(original)
    conditioned_path = output / 'conditioned-input.png'
    conditioned.save(conditioned_path)
    settings.update(conditionedImageSHA256=sha(conditioned_path),
                    originalSize=list(original.size), conditionedSize=list(conditioned.size),
                    loadSeconds=time.monotonic() - started)
    settings_path.write_text(json.dumps(settings, indent=2) + '\n')
    result = pipe.run(conditioned, seed=42, pipeline_type='512', preprocess_image=False,
                      sparse_structure_sampler_params={'steps': 8},
                      shape_slat_sampler_params={'steps': 8},
                      tex_slat_sampler_params={'steps': 8})
    mesh = result[0] if isinstance(result, list) else result
    receipt = save_native(mesh, output)
    # Decoded invalid data persists before all following admission checks.
    with np.load(output / 'native.npz', allow_pickle=False) as saved:
        vertices, faces = saved['vertices'].copy(), saved['faces'].copy()
    good = bool(vertices.ndim == 2 and vertices.shape[1] == 3 and
                faces.ndim == 2 and faces.shape[1] == 3 and len(vertices) and len(faces) and
                np.isfinite(vertices).all() and np.issubdtype(faces.dtype, np.integer) and
                (faces >= 0).all() and (faces < len(vertices)).all())
    settings.update(validNativeArrays=good, nativeSHA256=receipt['archiveSHA256'],
                    vertices=len(vertices), faces=len(faces),
                    elapsedSeconds=time.monotonic() - started)
    (output / 'generation.json').write_text(json.dumps(settings, indent=2) + '\n')
    if not good:
        raise ValueError('Invalid decoded geometry retained; no display processing')
    trimesh.Trimesh(vertices=vertices, faces=faces, process=False).export(output / 'native-display.glb')
    print(json.dumps(settings), flush=True)


if __name__ == '__main__':
    main()
