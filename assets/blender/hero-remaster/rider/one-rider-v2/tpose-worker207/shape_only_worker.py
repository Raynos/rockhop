"""Unexecuted structural shape-only adaptation; controller holds the GPU lock.

The decoded native arrays precede the official trimesh export's processing.
No cleanup, reduction, texturing, rigging, or production asset replacement.
"""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time


SOURCE = Path('/Users/raynos/ml/img2mesh/Hunyuan3D-2.1')
WEIGHTS = Path('/Users/raynos/projects/weights/manual/tencent/Hunyuan3D-2.1')
PRIVATE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
SOURCE_HEAD = '82920d643c0dc2f7bfd7255f45f62d386edfe60c'
FREEZE = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/tpose-worker207/freeze.json')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def native_diagnostics(vertices, faces, np):
    """Record all invalid element locations; untouched NPZ is authoritative."""
    vertex_shape_ok = vertices.ndim == 2 and vertices.shape[1] == 3
    face_shape_ok = faces.ndim == 2 and faces.shape[1] == 3
    bad_vertices = ~np.isfinite(vertices)
    bad_faces = (~np.isfinite(faces)) | (faces < 0) | (faces >= len(vertices))
    if faces.dtype.kind == 'f':
        bad_faces |= np.isfinite(faces) & (faces != np.floor(faces))
    vertex_locations = np.argwhere(bad_vertices)
    face_locations = np.argwhere(bad_faces)
    return {'vertexShape': list(vertices.shape), 'faceShape': list(faces.shape),
            'vertexDtype': str(vertices.dtype), 'faceDtype': str(faces.dtype),
            'vertexShapeOK': vertex_shape_ok, 'faceShapeOK': face_shape_ok,
            'nonfiniteVertexElementCount': int(bad_vertices.sum()),
            'nonfiniteVertexRowIDs': np.unique(vertex_locations[:, 0]).tolist(),
            'nonfiniteVertexElementLocations': vertex_locations.tolist(),
            'invalidFaceElementCount': int(bad_faces.sum()),
            'invalidFaceRowIDs': np.unique(face_locations[:, 0]).tolist(),
            'invalidFaceElementLocations': face_locations.tolist(),
            'invalidFaceValuesExactText': [str(faces[tuple(location)]) for location in face_locations],
            'invalidVertexValuesExactText': [str(vertices[tuple(location)]) for location in vertex_locations],
            'faceMinimumExactText': str(faces.min()) if faces.size else None,
            'faceMaximumExactText': str(faces.max()) if faces.size else None,
            'validForDisplay': bool(vertex_shape_ok and face_shape_ok and len(vertices) > 0
                                    and len(faces) > 0 and not bad_vertices.any() and not bad_faces.any()),
            'nativeArraysModified': False, 'repaired': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True)
    parser.add_argument('--image-sha256', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_TPOSE_LOCK_CONTROLLER_PID') == str(os.getppid()), 'Use run_bounded.py'
    image_path = Path(args.image).resolve()
    output = Path(args.out).resolve()
    assert output.is_relative_to(PRIVATE) and output != PRIVATE
    assert not output.exists(), 'Fresh private output required'
    assert sha(image_path) == args.image_sha256, 'Frozen input hash mismatch'
    frozen = json.loads(FREEZE.read_text())
    for group in ('computationalInputs', 'ownedFiles'):
        for path, pin in frozen[group].items():
            assert sha(path) == pin['sha256'], f'Readiness pin changed: {path}'
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == SOURCE_HEAD
    output.mkdir()
    os.environ.update(HF_HOME='/Users/raynos/projects/weights/hf', HF_HUB_OFFLINE='1',
                      TRANSFORMERS_OFFLINE='1', PYTORCH_ENABLE_MPS_FALLBACK='1',
                      HF_MODULES_CACHE=str(SOURCE / 'runtime/hf-modules'))
    sys.path.insert(0, str(SOURCE / 'hy3dshape'))
    import torch
    import numpy as np
    import trimesh
    from PIL import Image
    import torchvision.transforms.functional as functional
    sys.modules['torchvision.transforms.functional_tensor'] = functional
    # Retain the installed, proven MPS float64 adaptation only.
    original_to = torch.Tensor.to
    def safe_to(self, *positional, **keywords):
        target = keywords.get('device', positional[0] if positional else None)
        if self.dtype == torch.float64 and str(target).startswith('mps'):
            self = self.float()
        return original_to(self, *positional, **keywords)
    torch.Tensor.to = safe_to
    assert torch.backends.mps.is_available(), 'Actual MPS required'
    from hy3dshape import Hunyuan3DDiTFlowMatchingPipeline
    started = time.monotonic()
    record = {'status': 'STARTED_UNACCEPTED', 'version': 'Hunyuan3D-2.1',
              'input': str(image_path), 'inputSHA256': args.image_sha256,
              'runnerSHA256': sha(__file__), 'sourceHEAD': SOURCE_HEAD,
              'seed': args.seed, 'shapeSteps': 30, 'octree': 380,
              'numChunks': 200000, 'guidanceScale': 5.0, 'device': 'mps',
              'torch': torch.__version__, 'python': sys.version,
              'cleanup': False, 'reduction': False, 'texture': False,
              'nativeArrayDefinition': 'Latent2MeshOutput mesh_v/mesh_f before official export_to_trimesh',
              'displayDefinition': 'native vertices; reversed native faces copied; Trimesh(process=False)'}
    (output / 'start-settings.json').write_text(json.dumps(record, indent=2) + '\n')
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(str(WEIGHTS), device='mps', use_safetensors=False)
    pipeline.enable_flashvdm(mc_algo='mc')
    decoded = pipeline(image=Image.open(image_path).convert('RGBA'),
                       num_inference_steps=30, octree_resolution=380,
                       num_chunks=200000, guidance_scale=5.0,
                       generator=torch.Generator(device='cpu').manual_seed(args.seed),
                       output_type='mesh')[0]
    assert decoded is not None
    vertices, faces = np.asarray(decoded.mesh_v).copy(), np.asarray(decoded.mesh_f).copy()
    if vertices.dtype.kind not in 'biuf' or faces.dtype.kind not in 'biuf':
        raise TypeError('Decoder did not return API-safe real numeric arrays; stop without inference changes')
    # Preserve untouched decoder arrays BEFORE finite/index/shape validation.
    np.savez_compressed(output / 'native-decoded.npz', vertices=vertices, faces=faces)
    diagnostics = native_diagnostics(vertices, faces, np)
    diagnostics['nativeNPZSHA256'] = sha(output / 'native-decoded.npz')
    (output / 'native-diagnostics.json').write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + '\n')
    record['nativeDiagnostics'] = diagnostics
    if not diagnostics['validForDisplay']:
        record.update(status='REJECTED_NATIVE_ARRAYS_RETAINED_NO_DISPLAY',
                      wallSeconds=time.monotonic() - started, vertices=len(vertices), faces=len(faces),
                      peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        record['outputs'] = {'native-decoded.npz': {'bytes': (output / 'native-decoded.npz').stat().st_size,
                                                   'sha256': diagnostics['nativeNPZSHA256']}}
        (output / 'generation.json').write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
        raise AssertionError('Invalid decoded geometry; untouched native arrays and exact diagnostics retained')
    # This is a separate display copy, with no Trimesh merging or cleanup.
    display_faces = faces[:, ::-1].copy()
    display = trimesh.Trimesh(vertices=vertices.copy(), faces=display_faces, process=False)
    assert np.array_equal(display.vertices, vertices) and np.array_equal(display.faces, display_faces)
    display.export(output / 'native-display.glb')
    np.savez_compressed(output / 'display-geometry.npz', vertices=np.asarray(display.vertices), faces=np.asarray(display.faces))
    del pipeline
    gc.collect()
    torch.mps.empty_cache()
    record.update(status='GENERATED_UNACCEPTED_STRUCTURAL_SOURCE_ONLY',
                  wallSeconds=time.monotonic() - started, vertices=len(vertices), faces=len(faces),
                  peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    record['outputs'] = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                         for p in output.iterdir() if p.suffix in ('.npz', '.glb')}
    (output / 'generation.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
