"""One documented-quality Hunyuan2.1 shape seed; preserve real conditioning/noise."""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SOURCE = Path('/Users/raynos/ml/img2mesh/Hunyuan3D-2.1')
WEIGHTS = Path('/Users/raynos/projects/weights/manual/tencent/Hunyuan3D-2.1')
HEAD = '82920d643c0dc2f7bfd7255f45f62d386edfe60c'
DIT_SHA = '6b519fc7242f78e9b5f47ea4d55668fe3d944a2d27332f4ca68d29a6ff603f5e'


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('image', 'image-sha256', 'pipeline-sha256', 'out'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--num-chunks', type=int, choices=[200000, 32768], default=200000)
    parser.add_argument('--replay-progress')
    parser.add_argument('--replay-progress-sha256')
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    image, output = Path(args.image), Path(args.out)
    assert sha(image) == args.image_sha256 and not output.exists()
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == HEAD
    pipeline_source = SOURCE / 'hy3dshape/hy3dshape/pipelines.py'
    assert sha(pipeline_source) == args.pipeline_sha256
    replay = None
    if args.replay_progress:
        assert args.replay_progress_sha256 and sha(args.replay_progress) == args.replay_progress_sha256
        replay = json.loads(Path(args.replay_progress).read_text())
        assert replay['imageSHA256'] == args.image_sha256 and replay['seed'] == 42
        assert replay['pipelineSHA256'] == args.pipeline_sha256 and replay['numInferenceSteps'] == 30
    output.mkdir(parents=True)
    settings = {'accepted': False, 'stage': 'verify/load', 'model': 'Hunyuan3D-2.1',
                'sourceHEAD': HEAD, 'pipelineSHA256': sha(pipeline_source),
                'recipeSHA256': sha(__file__), 'imagePath': str(image), 'imageSHA256': sha(image),
                'seed': 42, 'numInferenceSteps': 30, 'guidanceScale': 5.0,
                'octreeResolution': 384, 'numChunks': args.num_chunks, 'device': 'mps',
                'effectiveFlashVDMResolutions': [95, 190, 380],
                'replayProgressPath': args.replay_progress,
                'replayProgressSHA256': args.replay_progress_sha256,
                'dtype': 'torch.float16', 'extractor': 'mc', 'paint': False,
                'cleanup': False, 'reduction': False,
                'checkpointPath': str(WEIGHTS / 'hunyuan3d-dit-v2-1/model.fp16.ckpt'),
                'checkpointSHA256': DIT_SHA,
                'ownedProcessAdaptations': ['Existing torchvision functional_tensor compatibility alias',
                                           'Existing float64-to-float32 conversion only when moving a tensor to MPS'],
                'rawDefinition': 'Latent2MeshOutput mesh_v/mesh_f BEFORE export_to_trimesh winding reversal/processing',
                'limits': ['One experimental shape seed; painting and root moving review separate.',
                           'No CUDA parity or calibrated camera/garment-fit/rig acceptance.']}
    def save():
        (output / 'progress.json').write_text(json.dumps(settings, indent=2) + '\n')
    save()
    assert sha(WEIGHTS / 'hunyuan3d-dit-v2-1/model.fp16.ckpt') == DIT_SHA
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      HF_HOME='/Users/raynos/projects/weights/hf',
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
    torch.set_num_threads(4)
    assert torch.backends.mps.is_available()
    from hy3dshape import Hunyuan3DDiTFlowMatchingPipeline
    from audit_native import audit
    started = time.monotonic()
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        str(WEIGHTS), device='mps', dtype=torch.float16, use_safetensors=False,
        subfolder='hunyuan3d-dit-v2-1', variant='fp16')
    pipe.enable_flashvdm(mc_algo='mc', replace_vae=False)
    components = {}
    for name in ('model', 'vae', 'conditioner'):
        component = getattr(pipe, name)
        params = list(component.parameters())
        components[name] = {'class': type(component).__module__ + '.' + type(component).__name__,
                            'importedSource': inspect.getfile(type(component)),
                            'parameters': sum(p.numel() for p in params),
                            'devices': sorted({str(p.device) for p in params}),
                            'dtypes': sorted({str(p.dtype) for p in params}),
                            'training': component.training}
    settings.update(loadedComponents=components, loadSeconds=time.monotonic() - started,
                    effectiveVAE='Embedded2.1 VAE from verified DiT checkpoint; no turbo replacement',
                    surfaceExtractor=type(pipe.vae.surface_extractor).__name__)
    assert Path(inspect.getfile(type(pipe))).resolve() == pipeline_source.resolve()
    original = Image.open(image).convert('RGBA')
    pixels = pipe.image_processor(original, to_tensor=False)
    Image.fromarray(pixels['image']).save(output / 'conditioned-input.png')
    assert sha(output / 'conditioned-input.png') == '211bb51818b3078cf745459695190c70f16fb9d608bc71ee595f72f8e2fb61ed'
    settings['conditionedImageSHA256'] = sha(output / 'conditioned-input.png')
    def persist_tensors(name, value):
        arrays = {}
        def walk(prefix, item):
            if isinstance(item, torch.Tensor):
                arrays[prefix] = item.detach().cpu().numpy().copy()
            elif isinstance(item, dict):
                for key, nested in item.items():
                    walk(prefix + '.' + str(key), nested)
        walk(name, value)
        assert arrays, 'Actual capture must contain tensors'
        archive = output / (name + '.npz')
        assert not archive.exists()
        np.savez_compressed(archive, **arrays)
        settings[name] = {'archiveSHA256': sha(archive), 'arrays': {
            key: {'shape': list(v.shape), 'dtype': str(v.dtype),
                  'sha256CBytes': hashlib.sha256(v.tobytes()).hexdigest(),
                  'finite': bool(np.isfinite(v).all()), 'std': float(v.astype(np.float64).std())}
            for key, v in arrays.items()}}
        if replay and name in replay:
            prior = replay[name]['arrays']
            current = settings[name]['arrays']
            assert prior.keys() == current.keys()
            identical = all(all(prior[k][field] == current[k][field]
                                for field in ('dtype', 'shape', 'sha256CBytes')) for k in prior)
            settings[name]['priorAttemptCBytesIdentical'] = identical
            assert identical, 'Preserve differing actual input/noise; stop before interpreting batch retry'
        save()
    for method_name, archive_name in [('prepare_image', 'actual-processor-tensors'),
                                      ('encode_cond', 'actual-conditioned-features'),
                                      ('prepare_latents', 'actual-initial-noise')]:
        original_method = getattr(pipe, method_name)
        def capture(*positional, _method=original_method, _name=archive_name, **keywords):
            result = _method(*positional, **keywords)
            persist_tensors(_name, result)
            return result
        setattr(pipe, method_name, capture)
    original_export = pipe._export
    def capture_export(*positional, **keywords):
        sampled = positional[0] if positional else keywords['latents']
        persist_tensors('actual-sampled-latents', sampled)
        return original_export(*positional, **keywords)
    pipe._export = capture_export
    settings['stage'] = 'shape inference'
    save()
    inference_start = time.monotonic()
    raw = pipe(image=original, num_inference_steps=30, octree_resolution=384,
               num_chunks=args.num_chunks, guidance_scale=5.0,
               generator=torch.Generator(device='cpu').manual_seed(42), output_type='mesh')[0]
    assert raw is not None, 'No surface; retain conditioning and guard'
    vertices, faces = np.asarray(raw.mesh_v).copy(), np.asarray(raw.mesh_f).copy()
    np.savez_compressed(output / 'native.npz', vertices=vertices, faces=faces)
    metrics = audit(vertices, faces)
    (output / 'native-audit.json').write_text(json.dumps(metrics, indent=2) + '\n')
    settings.update(stage='native saved; review pending', inferenceSeconds=time.monotonic() - inference_start,
                    elapsedSeconds=time.monotonic() - started, nativeSHA256=sha(output / 'native.npz'),
                    vertices=len(vertices), faces=len(faces), nativeAudit=metrics)
    save()
    assert metrics['validGeometryArrays'], 'Invalid raw retained; no display export'
    # A marked display derivative follows the official global MC winding reversal.
    display = trimesh.Trimesh(vertices=vertices.copy(), faces=faces[:, ::-1].copy(), process=False)
    display.export(output / 'native-display.glb')
    settings['displayDerivative'] = {'SHA256': sha(output / 'native-display.glb'),
        'method': 'Official global winding reversal; no repair/cleanup/decimation', 'accepted': False}
    (output / 'generation.json').write_text(json.dumps(settings, indent=2) + '\n')
    print(json.dumps({'stage': settings['stage'], 'vertices': len(vertices), 'faces': len(faces),
                      'elapsedSeconds': settings['elapsedSeconds']}), flush=True)


if __name__ == '__main__':
    main()
