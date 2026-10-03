"""One documented-quality mesh/reference paint; reuse proven UV, preserve mesh."""
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
STORE = Path('/Users/raynos/projects/weights/manual')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('mesh', 'wrapped', 'image', 'weights-receipt', 'weights-receipt-sha256', 'out'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(args.mesh) == '318c7536e5234c6a6e285f4d2111dad9fcdf3941e0329951a1f9a7ebf460612a'
    assert sha(args.wrapped) == 'f1d1fa95c9095c156dfc6840f93cf4db8f082f0dd835ffd53492d73e3774085f'
    assert sha(args.image) == '4cd768251ad3a0402db6ba94c7b99d7cd3c7642e83d5ab712debf2685c076d9c'
    assert sha(args.weights_receipt) == args.weights_receipt_sha256
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == '82920d643c0dc2f7bfd7255f45f62d386edfe60c'
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    started = time.monotonic()
    report = {'accepted': False, 'stage': 'verify/load', 'newShapeRuns': 0,
              'recipeSHA256': sha(__file__), 'inputMeshSHA256': sha(args.mesh),
              'wrappedSHA256': sha(args.wrapped), 'referenceSHA256': sha(args.image),
              'weightsReceiptSHA256': sha(args.weights_receipt),
              'seed': 42, 'scheduler': 'UniPCMultistepScheduler trailing', 'paintSteps': 15,
              'maxSelectedViews': 8, 'viewResolution': 768, 'renderSize': 2048, 'textureSize': 4096,
              'remesh': False, 'simplification': False, 'device': 'mps', 'rendererDevice': 'cpu',
              'UVReuse': 'Frozen actual installed xatlas result with identical triangle coordinates; no repeated unwrap',
              'limits': ['One reference/seed, no paint or garment fit acceptance before root played review.',
                         'Original six zero-area triangles and detached component retained.',
                         'Owned process/instance adapters, no shared installation edits or CUDA parity.']}
    def save():
        (out / 'progress.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    weights = json.loads(Path(args.weights_receipt).read_text())
    assert weights['allSelectedPinsMatch'] and len(weights['files']) == 22
    for entry in weights['files']:
        assert sha(entry['path']) == entry['actualSHA256']
    for entry in weights['runtimeView']:
        assert sha(entry['path']) == entry['SHA256']
    os.environ.update(HF_HOME='/Users/raynos/projects/weights/hf', HF_HUB_OFFLINE='1',
                      TRANSFORMERS_OFFLINE='1', HF_MODULES_CACHE=str(SOURCE / 'runtime/hf-modules'))
    sys.path.insert(0, str(SOURCE / 'hy3dpaint'))
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
    from paint_geometry_getter import preserve_getter_state
    import textureGenPipeline as paint_module
    assert sha(inspect.getfile(paint_module.Hunyuan3DPaintPipeline)) == '174951ccd0cc79bad985756b009fcb832026b3410cda1f00897ea3eb2c444610'
    # Pin all imported runtime source files actually used, not an assumed backend name.
    report['paintPipelineSourceSHA256'] = sha(inspect.getfile(paint_module.Hunyuan3DPaintPipeline))
    with np.load(args.mesh, allow_pickle=False) as archive:
        original_v, original_f = archive['vertices'].copy(), archive['faces'][:, ::-1].copy()
    with np.load(args.wrapped, allow_pickle=False) as archive:
        wrapped_v, wrapped_f, wrapped_uv = archive['vertices'].copy(), archive['faces'].copy(), archive['uv'].copy()
    assert np.array_equal(wrapped_v[wrapped_f], original_v[original_f])
    input_obj = out / 'shape.obj'
    trimesh.Trimesh(vertices=original_v, faces=original_f, process=False).export(input_obj, digits=9)
    original_load = trimesh.load
    def frozen_load(path, *positional, **keywords):
        if isinstance(path, (str, Path)) and Path(path).resolve() == input_obj.resolve():
            report['ownedFrozenGeometryLoaded'] = True
            return trimesh.Trimesh(vertices=original_v.copy(), faces=original_f.copy(), process=False)
        return original_load(path, *positional, **keywords)
    trimesh.load = frozen_load
    def frozen_wrap(mesh):
        assert np.array_equal(mesh.vertices, original_v) and np.array_equal(mesh.faces, original_f)
        result = trimesh.Trimesh(vertices=wrapped_v.copy(), faces=wrapped_f.copy(), process=False)
        result.visual = trimesh.visual.texture.TextureVisuals(uv=wrapped_uv.copy())
        report['ownedProvenUVReused'] = True
        return result
    paint_module.mesh_uv_wrap = frozen_wrap
    config = paint_module.Hunyuan3DPaintConfig(max_num_view=8, resolution=768)
    config.device, config.renderer_device = 'mps', 'cpu'
    config.seed, config.paint_steps = 42, 15
    config.multiview_cfg_path = str(SOURCE / 'hy3dpaint/cfgs/hunyuan-paint-pbr.yaml')
    config.multiview_pretrained_path = '/Users/raynos/ml/img2mesh/hunyuan21-view'
    config.dino_ckpt_path = str(STORE / 'facebook/dinov2-giant')
    config.realesrgan_ckpt_path = str(STORE / 'xinntao/Real-ESRGAN/RealESRGAN_x4plus.pth')
    config.render_size, config.texture_size = 2048, 4096
    painter = paint_module.Hunyuan3DPaintPipeline(config)
    preserve_getter_state(painter.render)
    assert str(painter.render.device) == 'cpu'
    multiview = painter.models['multiview_model']
    pipeline = multiview.pipeline
    components = {}
    for name, component in [('unet', pipeline.unet), ('vae', pipeline.vae),
                            ('text_encoder', pipeline.text_encoder), ('dino', multiview.dino_v2)]:
        params = list(component.parameters())
        components[name] = {'class': type(component).__module__ + '.' + type(component).__name__,
                            'sourceSHA256': sha(inspect.getfile(type(component))),
                            'parameters': sum(p.numel() for p in params),
                            'devices': sorted({str(p.device) for p in params}),
                            'dtypes': sorted({str(p.dtype) for p in params})}
    report.update(stage='paint', loadedComponents=components, actualScheduler=type(pipeline.scheduler).__name__,
                  storedButUnregisteredComponents=['image_encoder'],
                  dinoClass=type(multiview.dino_v2).__name__, rendererSourceSHA256=sha(inspect.getfile(type(painter.render))),
                  actualConfig={'resolution': config.resolution, 'render': painter.render.default_resolution,
                                'texture': painter.render.texture_size, 'maxViews': config.max_selected_view_num})
    save()
    captures = {}
    def capture(name, value):
        number = captures.get(name, 0)
        captures[name] = number + 1
        label = f'{name}-{number:02d}'
        arrays = {}
        def walk(prefix, item):
            if isinstance(item, torch.Tensor):
                arrays[prefix] = item.detach().cpu().numpy().copy()
            elif isinstance(item, dict):
                for key, nested in item.items():
                    walk(prefix + '.' + str(key), nested)
            elif isinstance(item, (tuple, list)):
                for index, nested in enumerate(item):
                    walk(prefix + '.' + str(index), nested)
        walk(label, value)
        assert arrays
        np.savez_compressed(out / (label + '.npz'), **arrays)
        report[label] = {'archiveSHA256': sha(out / (label + '.npz')), 'arrays': {
            key: {'shape': list(v.shape), 'dtype': str(v.dtype), 'finite': bool(np.isfinite(v).all()),
                  'CBytesSHA256': hashlib.sha256(v.tobytes()).hexdigest()} for key, v in arrays.items()}}
        save()
        assert all(np.isfinite(v).all() for v in arrays.values()), 'Invalid actual conditioning/noise'
    for name in ('prepare_latents', 'encode_images'):
        original = getattr(pipeline, name)
        def wrapped(*positional, _name=name, _original=original, **keywords):
            if _name == 'encode_images':
                capture('actual-VAE-image-input', positional[0] if positional else keywords['images'])
            result = _original(*positional, **keywords)
            capture('actual-' + _name, result)
            return result
        setattr(pipeline, name, wrapped)
    multiview.dino_v2.register_forward_hook(lambda module, inputs, result: capture('actual-dino-features', result))
    multiview.dino_v2.dino_v2.register_forward_pre_hook(lambda module, inputs, keywords: capture('actual-dino-model-input', inputs or keywords), with_kwargs=True)
    original_selection = painter.view_processor.bake_view_selection
    def selection(*positional, **keywords):
        result = original_selection(*positional, **keywords)
        report['actualSelectedViews'] = {'elevations': list(result[0]), 'azimuths': list(result[1]), 'weights': list(result[2])}
        save()
        return result
    painter.view_processor.bake_view_selection = selection
    original_forward = multiview.forward_one
    def forward(images, controls, **keywords):
        directory = out / 'actual-paint-conditioning'
        directory.mkdir()
        rows = []
        for family, values in [('style', images), ('control', controls)]:
            for index, image in enumerate(values):
                path = directory / f'{family}-{index:02d}.png'
                image.save(path)
                rows.append({'family': family, 'index': index, 'size': list(image.size), 'mode': image.mode, 'SHA256': sha(path)})
        report['actualPaintInputPNGs'] = rows
        save()
        return original_forward(images, controls, **keywords)
    multiview.forward_one = forward
    painter(mesh_path=str(input_obj), image_path=Image.open(args.image).convert('RGBA'),
            output_mesh_path=str(out / 'painted.obj'), use_remesh=False, save_glb=False)
    report.update(stage='painted OBJ saved; preservation audit', elapsedSeconds=time.monotonic() - started)
    save()
    painted = original_load(out / 'painted.obj', process=False, maintain_order=True)
    assert isinstance(painted, trimesh.Trimesh) and painted.faces.shape == original_f.shape
    error = float(np.max(np.abs(painted.vertices[painted.faces] - original_v[original_f])))
    report['paintedGeometry'] = {'vertices': len(painted.vertices), 'triangles': len(painted.faces),
                                'maxTriangleCoordinateError': error, 'OBJPrecision': 'Installed writer %.6f',
                                'uvFinite': bool(np.isfinite(painted.visual.uv).all())}
    save()
    assert error < 8e-7 and report['paintedGeometry']['uvFinite']
    maps = {}
    for name, filename in [('baseColor', 'painted.jpg'), ('roughness', 'painted_roughness.jpg'), ('metallic', 'painted_metallic.jpg')]:
        path = out / filename
        maps[name] = {'SHA256': sha(path), 'size': list(Image.open(path).size)}
        assert maps[name]['size'] == [4096, 4096]
    base = Image.open(out / 'painted.jpg').convert('RGB')
    rough = np.asarray(Image.open(out / 'painted_roughness.jpg').convert('L'))
    metal = np.asarray(Image.open(out / 'painted_metallic.jpg').convert('L'))
    packed = Image.fromarray(np.stack([np.full_like(rough, 255), rough, metal], axis=-1))
    packed.save(out / 'metallic-roughness-packed.png')
    material = trimesh.visual.material.PBRMaterial(baseColorTexture=base, metallicRoughnessTexture=packed,
                                                  metallicFactor=1., roughnessFactor=1., alphaMode='OPAQUE')
    painted.visual = trimesh.visual.texture.TextureVisuals(uv=painted.visual.uv.copy(), material=material)
    painted.export(out / 'painted.glb')
    loaded = original_load(out / 'painted.glb', force='mesh', process=False)
    assert loaded.faces.shape == original_f.shape
    glb_error = float(np.max(np.abs(loaded.vertices[loaded.faces] - original_v[original_f])))
    assert glb_error < 9e-7
    report.update(stage='PBR saved; root moving review pending', maps=maps, paintedGLBSHA256=sha(out / 'painted.glb'),
                  GLBTriangleCoordinateError=glb_error, elapsedSeconds=time.monotonic() - started)
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'stage': report['stage'], 'GLBSHA256': report['paintedGLBSHA256'],
                      'elapsedSeconds': report['elapsedSeconds']}), flush=True)


if __name__ == '__main__':
    main()
