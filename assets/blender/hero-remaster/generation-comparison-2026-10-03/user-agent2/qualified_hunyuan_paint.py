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
import types

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
    attention_mode = parser.add_mutually_exclusive_group()
    attention_mode.add_argument('--query-tiling', action='store_true')
    attention_mode.add_argument('--value-columns', action='store_true')
    parser.add_argument('--replay-progress')
    parser.add_argument('--replay-progress-sha256')
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(args.mesh) == '318c7536e5234c6a6e285f4d2111dad9fcdf3941e0329951a1f9a7ebf460612a'
    assert sha(args.wrapped) == 'f1d1fa95c9095c156dfc6840f93cf4db8f082f0dd835ffd53492d73e3774085f'
    assert sha(args.image) == '4cd768251ad3a0402db6ba94c7b99d7cd3c7642e83d5ab712debf2685c076d9c'
    assert sha(args.weights_receipt) == args.weights_receipt_sha256
    prior = None
    if args.replay_progress:
        assert args.replay_progress_sha256 and sha(args.replay_progress) == args.replay_progress_sha256
        prior = json.loads(Path(args.replay_progress).read_text())
        assert prior['inputMeshSHA256'] == sha(args.mesh) and prior['referenceSHA256'] == sha(args.image)
        assert prior['seed'] == 42 and prior['viewResolution'] == 768 and prior['paintSteps'] == 15
    assert not (args.query_tiling or args.value_columns) or prior is not None
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
              'queryTiling': args.query_tiling, 'valueColumns': args.value_columns,
              'replayProgressSHA256': args.replay_progress_sha256,
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
        if prior and label in prior:
            original_arrays, current_arrays = prior[label]['arrays'], report[label]['arrays']
            identical = original_arrays.keys() == current_arrays.keys() and all(
                all(original_arrays[key][field] == current_arrays[key][field]
                    for field in ('shape', 'dtype', 'CBytesSHA256')) for key in current_arrays)
            report[label]['priorCBytesIdentical'] = identical
            save()
            assert identical, 'Actual prior condition/noise differs; stop before interpreting attention retry'
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
        result = original_forward(images, controls, **keywords)
        report.update(stage='multiview images returned; upscale and bake',
                      multiviewElapsedSeconds=time.monotonic() - started)
        save()
        return result
    multiview.forward_one = forward
    if args.value_columns:
        from value_column_attention import value_column_attention
        report['valueColumnAdapterSHA256'] = sha(inspect.getfile(value_column_attention))
        report['torchGitVersion'] = torch.version.git_version
        report['prefillDisableEnv'] = os.environ.get('PYTORCH_MPS_DISABLE_PREFILL_ATTENTION')
        assert torch.version.git_version == '08187d9e0fba026dc8217405802ab5381dc88d90'
        assert report['prefillDisableEnv'] in (None, '0'), 'Native equal-width prefill was disabled'
        report['attentionSourceURL'] = 'https://raw.githubusercontent.com/pytorch/pytorch/08187d9e0fba026dc8217405802ab5381dc88d90/aten/src/ATen/native/mps/operations/Attention.mm'
        report['attentionDerivative'] = 'Complete Q/K, split independent V columns into head-width blocks and concatenate in original order; native SDPA retained for equal widths'
        report['actualAttentionShapes'] = {}
        report['ownedAttentionModules'] = []
        active_layer, processors = [], {}
        for name, module in pipeline.unet.named_modules():
            if not hasattr(module, 'processor'):
                continue
            owner = inspect.getmodule(type(module.processor))
            if owner is None or not hasattr(owner, 'AttnCore'):
                continue
            processors[owner.__name__] = owner
            def enter(module, inputs, _name=name):
                active_layer.append({'name': _name, 'processor': type(module.processor).__name__})
            def leave(module, inputs, result):
                active_layer.pop()
            module.register_forward_pre_hook(enter)
            module.register_forward_hook(leave)
        assert processors
        validated_routes = set()
        for name, owner in processors.items():
            source_sha = sha(inspect.getfile(owner))
            assert source_sha == '6df282d094627733623ddeaa28a493a11252ea58e7b99e4d52240e17f4f71d0f'
            original_sdpa = owner.F.scaled_dot_product_attention
            def owned_value_sdpa(query, key, value, _original=original_sdpa, **keywords):
                assert active_layer and query.dtype == key.dtype == value.dtype
                assert keywords.get('attn_mask') is None and keywords.get('dropout_p', 0) == 0
                assert not keywords.get('is_causal', False) and not keywords.get('enable_gqa', False)
                split = query.device.type == 'mps' and query.shape[-1] != value.shape[-1]
                route = 'nativeSDPA-V-column-blocks' if split else 'original-nativeSDPA'
                def info(tensor):
                    return {'shape': list(tensor.shape), 'stride': list(tensor.stride()),
                            'dtype': str(tensor.dtype), 'device': str(tensor.device)}
                descriptor = str((active_layer[-1]['name'], tuple(query.shape), tuple(key.shape), tuple(value.shape)))
                entry = report['actualAttentionShapes'].setdefault(descriptor, {
                    **active_layer[-1], 'calls': 0, 'query': info(query), 'key': info(key), 'value': info(value),
                    'route': route, 'allKeysViewsRetained': True, 'mask': None, 'dropout': 0,
                    'isCausal': False, 'scale': keywords.get('scale'),
                    'estimatedUnsplitFloat32ScoreGiB': int(np.prod(query.shape[:-2])) * query.shape[-2] * key.shape[-2] * 4 / 1024 ** 3})
                entry['calls'] += 1
                report['lastAttentionCall'] = {'descriptor': descriptor, 'call': entry['calls'],
                                               'status': 'before operator', 'elapsedSeconds': time.monotonic() - started}
                report['mpsBeforeAttention'] = {'allocatedBytes': torch.mps.current_allocated_memory(),
                                              'driverBytes': torch.mps.driver_allocated_memory()}
                save()  # Persist the stopping layer before its allocation, not only on success.
                first = route not in validated_routes
                if first:
                    capture('actual-first-' + ('value-column' if split else 'native') + '-attention-inputs',
                            {'query': query, 'key': key, 'value': value})
                output = value_column_attention(query, key, value, **keywords) if split else _original(query, key, value, **keywords)
                assert torch.isfinite(output).all(), 'Nonfinite actual native/value-column attention'
                if first:
                    selected = torch.tensor([0, query.shape[-2] // 2, query.shape[-2] - 1])
                    qc = query.detach().cpu()[:, :, selected].float()
                    kc, vc = key.detach().cpu().float(), value.detach().cpu().float()
                    expected = (torch.softmax(qc @ kc.transpose(-1, -2) / query.shape[-1] ** .5, dim=-1) @ vc).to(query.dtype)
                    error = float((output.detach().cpu()[:, :, selected].float() - expected.float()).abs().max())
                    entry['firstActualSelectedCPUError'] = error
                    assert error <= .002, 'Actual attention exceeds unchanged independent CPU threshold'
                    validated_routes.add(route)
                report['lastAttentionCall']['status'] = 'operator finite and returned'
                save()
                return output
            owner.F = types.SimpleNamespace(scaled_dot_product_attention=owned_value_sdpa)
            report['ownedAttentionModules'].append({'name': name, 'sourceSHA256': source_sha})
        original_scheduler_step = pipeline.scheduler.step
        report['actualDiffusionSteps'] = []
        def scheduler_step(*positional, **keywords):
            result = original_scheduler_step(*positional, **keywords)
            latent = (result[0] if isinstance(result, tuple) else result.prev_sample).detach().cpu().numpy()
            assert np.isfinite(latent).all(), 'Nonfinite real sampled paint latent'
            report['actualDiffusionSteps'].append({'step': len(report['actualDiffusionSteps']) + 1,
                'elapsedSeconds': time.monotonic() - started, 'shape': list(latent.shape),
                'dtype': str(latent.dtype), 'allFinite': True,
                'CBytesSHA256': hashlib.sha256(latent.tobytes()).hexdigest()})
            save()
            return result
        pipeline.scheduler.step = scheduler_step
        save()
    if args.query_tiling:
        from query_tiled_attention import query_tiled_attention
        report['queryTilingAdapterSHA256'] = sha(inspect.getfile(query_tiled_attention))
        processors = {}
        for module in pipeline.unet.modules():
            if hasattr(module, 'processor'):
                owner = inspect.getmodule(type(module.processor))
                if owner is not None and hasattr(owner, 'AttnCore'):
                    processors[owner.__name__] = owner
        assert processors, 'Actual custom processor module was not identified'
        report['ownedAttentionModules'] = []
        report['actualAttentionShapes'] = {}
        first_large = [False]
        for name, owner in processors.items():
            source_sha = sha(inspect.getfile(owner))
            assert source_sha == '6df282d094627733623ddeaa28a493a11252ea58e7b99e4d52240e17f4f71d0f'
            original_sdpa = owner.F.scaled_dot_product_attention
            def owned_sdpa(query, key, value, _original=original_sdpa, **keywords):
                score_bytes = int(np.prod(query.shape[:-2])) * query.shape[-2] * key.shape[-2] * 4
                if query.device.type != 'mps' or score_bytes <= 256 * 1024 ** 2:
                    return _original(query, key, value, **keywords)
                descriptor = str((tuple(query.shape), tuple(key.shape), tuple(value.shape)))
                entry = report['actualAttentionShapes'].setdefault(descriptor, {
                    'calls': 0, 'queryShape': list(query.shape), 'keyShape': list(key.shape),
                    'valueShape': list(value.shape), 'estimatedFullFloat32ScoreGiB': score_bytes / 1024 ** 3,
                    'queryTile': 128, 'allKeysRetained': True})
                entry['calls'] += 1
                if not first_large[0]:
                    capture('actual-first-large-attention-inputs', {'query': query, 'key': key, 'value': value})
                    selected = torch.tensor([0, query.shape[-2] // 2, query.shape[-2] - 1])
                    qc = query.detach().cpu()[:, :, selected].float()
                    kc, vc = key.detach().cpu().float(), value.detach().cpu().float()
                    expected = (torch.softmax(qc @ kc.transpose(-1, -2) / query.shape[-1] ** .5, dim=-1) @ vc).to(query.dtype)
                    output = query_tiled_attention(query, key, value, **keywords)
                    actual = output.detach().cpu()[:, :, selected]
                    error = float((actual.float() - expected.float()).abs().max())
                    report['actualFirstLargeSelectedCPUError'] = error
                    assert error <= .002, 'Actual attention differs from independent CPU reference'
                    first_large[0] = True
                    save()
                else:
                    output = query_tiled_attention(query, key, value, **keywords)
                assert torch.isfinite(output).all(), 'Nonfinite actual tiled attention'
                return output
            # Only this custom UNet processor module changes; torch/VAE/DINO globals stay original.
            owner.F = types.SimpleNamespace(scaled_dot_product_attention=owned_sdpa)
            report['ownedAttentionModules'].append({'name': name, 'sourceSHA256': source_sha})
        report['attentionDerivative'] = 'Query-tiled float32 SDPA math, no mask/dropout/causal; full keys/views retained, roundoff differs'
        save()
    painter(mesh_path=str(input_obj), image_path=Image.open(args.image).convert('RGBA'),
            output_mesh_path=str(out / 'painted.obj'), use_remesh=False, save_glb=False)
    if prior:
        required = [key for key in prior if key.startswith('actual-')]
        assert all(report.get(key, {}).get('priorCBytesIdentical') for key in required)
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
