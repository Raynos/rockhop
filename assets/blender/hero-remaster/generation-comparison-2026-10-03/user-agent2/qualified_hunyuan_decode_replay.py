"""Decode immutable sampled latents; preserve sparse field and native MC first."""
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
DIT_SHA = '6b519fc7242f78e9b5f47ea4d55668fe3d944a2d27332f4ca68d29a6ff603f5e'
VAE_SHA = '5cbe97f25e6e7abd4bccc80ab07524ec0c86d24118486a9ba49bb5dfb070288a'
LATENTS_SHA = 'd077285011d50187dbcfb5be30890d44d4f6be9def3ee51d1b1e4252793a0bb2'
RAW_SHA = '0d2d531e400480bc2df077a91c4db0702675947afaed6e34e6bbead563dd8164'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ('latents', 'raw', 'out'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(args.latents) == LATENTS_SHA and sha(args.raw) == RAW_SHA
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == '82920d643c0dc2f7bfd7255f45f62d386edfe60c'
    started = time.monotonic()
    report = {'accepted': False, 'stage': 'verify same VAE', 'newSamplerRuns': 0,
              'latentsSHA256': LATENTS_SHA, 'originalRawSHA256': RAW_SHA,
              'recipeSHA256': sha(__file__), 'requestedResolution': 384,
              'numChunks': 32768, 'bounds': 1.01, 'mcLevel': 0.0,
              'coordinateMapping': 'Preserve original MC divide by requested octree+1=385, even if actual field381.',
              'limits': ['Owned finite-cell extraction derivative, never field filling or mesh cleanup.',
                         'No CUDA/PBR/fit/motion/asset acceptance; root judges played evidence.']}
    def save():
        (out / 'progress.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    dit = WEIGHTS / 'hunyuan3d-dit-v2-1/model.fp16.ckpt'
    vae_path = WEIGHTS / 'hunyuan3d-vae-v2-1/model.fp16.ckpt'
    assert sha(dit) == DIT_SHA and sha(vae_path) == VAE_SHA
    import numpy as np
    import torch
    import yaml
    torch.set_num_threads(4)
    assert torch.backends.mps.is_available()
    dit_state = torch.load(dit, map_location='cpu', weights_only=True, mmap=True)
    standalone_state = torch.load(vae_path, map_location='cpu', weights_only=True, mmap=True)
    embedded_state = dit_state['vae']
    assert embedded_state.keys() == standalone_state.keys()
    mismatches = [key for key in embedded_state if embedded_state[key].dtype != standalone_state[key].dtype
                  or embedded_state[key].shape != standalone_state[key].shape
                  or not torch.equal(embedded_state[key], standalone_state[key])]
    report['checkpointComparison'] = {'embeddedDiTSHA256': DIT_SHA, 'standaloneVAESHA256': VAE_SHA,
                                      'tensorCount': len(embedded_state), 'mismatches': mismatches,
                                      'allTensorValuesShapesDtypesIdentical': not mismatches}
    cfg = yaml.safe_load((WEIGHTS / 'hunyuan3d-vae-v2-1/config.yaml').read_text())
    dit_cfg = yaml.safe_load((WEIGHTS / 'hunyuan3d-dit-v2-1/config.yaml').read_text())
    report['VAEParametersIdentical'] = cfg['params'] == dit_cfg['vae']['params']
    save()
    assert not mismatches and report['VAEParametersIdentical'], 'Standalone VAE is not the original embedded VAE'
    del dit_state, embedded_state, standalone_state
    import gc
    gc.collect()
    sys.path.insert(0, str(SOURCE / 'hy3dshape'))
    import torchvision.transforms.functional as functional
    sys.modules['torchvision.transforms.functional_tensor'] = functional
    original_to = torch.Tensor.to
    def safe_to(self, *positional, **keywords):
        target = keywords.get('device', positional[0] if positional else None)
        if self.dtype == torch.float64 and str(target).startswith('mps'):
            self = self.float()
        return original_to(self, *positional, **keywords)
    torch.Tensor.to = safe_to
    from hy3dshape.models.autoencoders import ShapeVAE
    from finite_cell_mc import extract
    from audit_native import audit
    vae = ShapeVAE.from_pretrained(str(WEIGHTS), device='mps', dtype=torch.float16,
                                    use_safetensors=False, variant='fp16', subfolder='hunyuan3d-vae-v2-1')
    vae.enable_flashvdm_decoder(mc_algo='mc')
    report.update(stage='decode original sampled latents', loadedVAEClass=type(vae).__module__ + '.' + type(vae).__name__,
                  parameters=sum(p.numel() for p in vae.parameters()), dtype=str(next(vae.parameters()).dtype),
                  device=str(next(vae.parameters()).device), scaleFactor=vae.scale_factor,
                  loadedSourceSHA256=sha(inspect.getfile(type(vae))),
                  installedExtractorSHA256=sha(inspect.getfile(type(vae.surface_extractor))),
                  volumeDecoderSHA256=sha(inspect.getfile(type(vae.volume_decoder))))
    save()
    latent_array = np.load(args.latents, allow_pickle=False)['actual-sampled-latents'].copy()
    assert np.isfinite(latent_array).all()
    assert hashlib.sha256(latent_array.tobytes()).hexdigest() == '6595898a97dc5a7f4f23647828b4ddd7b83f4433a6dfe198003ac2ea586da60c'
    report['neuralQueryBatches'] = []
    def check_neural_output(module, positional, keywords, result):
        values = result.detach().cpu().numpy()
        entry = {'shape': list(values.shape), 'finite': bool(np.isfinite(values).all()),
                 'sentinelValuedSamples': int((values == -10000).sum()),
                 'minimum': float(np.nanmin(values)), 'maximum': float(np.nanmax(values))}
        report['neuralQueryBatches'].append(entry)
        if not entry['finite'] or entry['sentinelValuedSamples']:
            np.savez_compressed(out / 'invalid-neural-batch.npz', logits=values,
                                queries=keywords['queries'].detach().cpu().numpy())
            save()
            raise AssertionError('Invalid or sentinel-valued evaluated neural output; no masked extraction')
    hook = vae.geo_decoder.register_forward_hook(check_neural_output, with_kwargs=True)
    target = inspect.unwrap(type(vae.volume_decoder).__call__)
    lines, first_line = inspect.getsourcelines(target)
    conversions = [first_line + i for i, line in enumerate(lines)
                   if "grid_logits[grid_logits == -10000.] = float('nan')" in line]
    assert len(conversions) == 1
    evaluated_capture = {}
    def local_trace(frame, event, arg):
        if event == 'line' and frame.f_lineno == conversions[0]:
            local = frame.f_locals
            # Explicit final scatter indices BEFORE sentinel conversion, not inferred from finite values.
            mask = np.zeros(tuple(local['grid_logits'].shape[1:]), dtype=bool)
            indices = tuple(index.detach().cpu().numpy() for index in local['nidx'])
            mask[indices] = True
            before = local['grid_logits'].detach().cpu().numpy().copy()
            assert np.isfinite(before[0][mask]).all() and not (before[0][mask] == -10000).any()
            evaluated_capture['mask'] = mask
            np.savez_compressed(out / 'actual-pre-sentinel-field.npz', logits=before, evaluated=mask)
        return local_trace
    def global_trace(frame, event, arg):
        return local_trace if frame.f_code is target.__code__ else None
    assert sys.gettrace() is None
    with torch.inference_mode():
        latents = torch.from_numpy(latent_array).to(device='mps', dtype=torch.float16)
        latents = 1. / vae.scale_factor * latents
        latents = vae(latents)
        sys.settrace(global_trace)
        try:
            field = vae.volume_decoder(latents, vae.geo_decoder, bounds=1.01, mc_level=0.,
                                       num_chunks=32768, octree_resolution=384, mc_algo='mc', enable_pbar=True)
        finally:
            sys.settrace(None)
            hook.remove()
    field_array = field.detach().cpu().numpy().copy()
    evaluated = evaluated_capture['mask']
    assert np.array_equal(evaluated, np.isfinite(field_array[0]))
    np.savez_compressed(out / 'actual-field.npz', logits=field_array)
    report.update(stage='actual field preserved before native extraction', fieldShape=list(field_array.shape),
                  fieldDtype=str(field_array.dtype), finiteFieldElements=int(np.isfinite(field_array).sum()),
                  nonfiniteFieldElements=int((~np.isfinite(field_array)).sum()),
                  infiniteFieldElements=int(np.isinf(field_array).sum()), fieldSHA256=sha(out / 'actual-field.npz'),
                  fieldCBytesSHA256=hashlib.sha256(field_array.tobytes()).hexdigest(),
                  preSentinelFieldSHA256=sha(out / 'actual-pre-sentinel-field.npz'),
                  evaluatedSiteMaskSHA256=hashlib.sha256(evaluated.tobytes()).hexdigest(),
                  evaluatedSites=int(evaluated.sum()), allEvaluatedNeuralBatchesFinite=True)
    save()
    original = vae.surface_extractor(field, bounds=1.01, mc_level=0., octree_resolution=384)[0]
    assert original is not None
    vertices, faces = np.asarray(original.mesh_v).copy(), np.asarray(original.mesh_f).copy()
    np.savez_compressed(out / 'native-replayed.npz', vertices=vertices, faces=faces)
    with np.load(args.raw, allow_pickle=False) as prior:
        equality = {'vertexCBytes': vertices.tobytes() == prior['vertices'].tobytes(),
                    'faceCBytes': faces.tobytes() == prior['faces'].tobytes(),
                    'vertexShapesDtypes': vertices.shape == prior['vertices'].shape and vertices.dtype == prior['vertices'].dtype,
                    'faceShapesDtypes': faces.shape == prior['faces'].shape and faces.dtype == prior['faces'].dtype}
    report.update(stage='native replay saved', nativeAudit=audit(vertices, faces), nativeReplayEquality=equality,
                  nativeReplaySHA256=sha(out / 'native-replayed.npz'))
    save()
    assert all(equality.values()), 'Native replay differs; retain evidence before derivative interpretation'
    before = hashlib.sha256(field_array.tobytes()).hexdigest()
    grid_vertices, derived_faces, counts = extract(field_array[0], level=0., evaluated=evaluated)
    derived_vertices = (grid_vertices / [385] * [2.02] - [1.01]).astype(np.float32)
    assert hashlib.sha256(field_array.tobytes()).hexdigest() == before
    np.savez_compressed(out / 'finite-cell-derived.npz', vertices=derived_vertices, faces=derived_faces)
    derived_audit = audit(derived_vertices, derived_faces)
    report.update(stage='owned derivative saved; root review pending', derivedAudit=derived_audit,
                  finiteCellCounts=counts, fieldBytesUnchanged=True,
                  adapterSHA256=sha(Path(__file__).with_name('finite_cell_mc.py')),
                  derivedSHA256=sha(out / 'finite-cell-derived.npz'), elapsedSeconds=time.monotonic() - started)
    save()
    assert derived_audit['validGeometryArrays']
    import trimesh
    display = trimesh.Trimesh(vertices=derived_vertices.copy(), faces=derived_faces[:, ::-1].copy(), process=False)
    display.export(out / 'finite-cell-display.glb')
    report['displayDerivative'] = {'SHA256': sha(out / 'finite-cell-display.glb'),
                                   'method': 'Original official global winding reversal; no repair/reduction', 'accepted': False}
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
