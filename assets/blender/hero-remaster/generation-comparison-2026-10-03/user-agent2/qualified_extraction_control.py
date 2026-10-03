"""Analytic geometry through actual installed extraction paths, no weights."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path

import numpy as np
from audit_native import audit


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['pixal', 'hunyuan'], required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    output = Path(args.out)
    assert not output.exists(), 'Fresh control directory required'
    base = Path('/Users/raynos/ml/img2mesh')
    source = base / ('Pixal3D-mac/pixal3d/utils/mesh_extract.py' if args.model == 'pixal'
                     else 'Hunyuan3D-2.1/hy3dshape/hy3dshape/models/autoencoders/surface_extractors.py')
    assert sha(source) == args.source_sha256
    import torch
    torch.set_num_threads(4)
    assert torch.backends.mps.is_available()
    spec = importlib.util.spec_from_file_location('pinned_actual_extractor', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output.mkdir(parents=True)
    report = {'accepted': False, 'modelRuns': 0, 'model': args.model,
              'source': str(source), 'sourceSHA256': sha(source), 'recipeSHA256': sha(__file__),
              'torch': torch.__version__, 'cases': [],
              'limits': ['CPU/MPS analytic extraction agreement is not CUDA equivalence.',
                         'Closed analytic controls do not establish learned garment topology or material/fit quality.',
                         'Native orientation and coordinate mapping reported; no shared extractor edits.']}
    if args.model == 'pixal':
        cases = []
        coords = np.array(list(itertools.product((0, 1), repeat=3)), dtype=np.int32)
        flags = np.zeros((8, 3), dtype=bool)
        for axis in range(3):
            flags[0, axis] = True
            anchor = np.zeros(3, dtype=int)
            anchor[axis] = 1
            flags[np.flatnonzero(np.all(coords == anchor, axis=1))[0], axis] = True
        cases.append(('cube', coords, np.full((8, 3), .5, dtype=np.float32), flags,
                      [[0, 0, 0], [2, 2, 2]], 2))
        size, extent = 16, 3.1
        coords = np.array(list(itertools.product(range(size), repeat=3)), dtype=np.int32)
        centres = (coords + .5) * extent / size - extent / 2
        projected = centres / np.linalg.norm(centres, axis=1)[:, None]
        dual = ((projected + extent / 2) * size / extent - coords).astype(np.float32)
        flags = np.zeros((len(coords), 3), dtype=bool)
        for axis in range(3):
            offset = np.ones(3)
            offset[axis] = 0
            start = (coords + offset) * extent / size - extent / 2
            end = start.copy()
            end[:, axis] += extent / size
            flags[:, axis] = (np.linalg.norm(start, axis=1) < 1) != (np.linalg.norm(end, axis=1) < 1)
        cases.append(('sphere', coords, dual, flags, [[-extent / 2] * 3, [extent / 2] * 3], size))
        for name, coords, dual, flags, bounds, resolution in cases:
            # Exercise learned-split inference, including nonuniform weights.
            split = np.linspace(.2, 1.3, len(coords), dtype=np.float32)[:, None]
            results = {}
            for device in ('cpu', 'mps'):
                vertices, faces = module.flexible_dual_grid_to_mesh(
                    *[torch.from_numpy(x).to(device) for x in (coords, dual, flags, split)],
                    aabb=bounds, grid_size=resolution, train=False)
                results[device] = (vertices.cpu().numpy(), faces.cpu().numpy())
            cpu_v, cpu_f = results['cpu']
            mps_v, mps_f = results['mps']
            metrics = audit(mps_v, mps_f)
            archive = output / (name + '.npz')
            np.savez_compressed(archive, coords=coords, dual=dual, flags=flags, split=split,
                                cpuVertices=cpu_v, cpuFaces=cpu_f, mpsVertices=mps_v, mpsFaces=mps_f)
            case = {'name': name, 'resolution': resolution, 'nativeAudit': metrics,
                    'CPUAndMPSFaceArraysIdentical': bool(np.array_equal(cpu_f, mps_f)),
                    'maxCPUAndMPSVertexError': float(np.max(np.abs(cpu_v - mps_v))),
                    'fixtureSHA256': sha(archive), 'archivePath': str(archive)}
            case['passClosedConnectivityAndDeviceAgreement'] = bool(
                metrics['boundaryEdges'] == 0 and metrics['overusedEdges'] == 0
                and metrics['zeroAreaTriangles'] == 0 and np.array_equal(cpu_f, mps_f)
                and case['maxCPUAndMPSVertexError'] <= 1e-6)
            report['cases'].append(case)
    else:
        for resolution in (384, 512):
            axis = torch.linspace(-1.2, 1.2, resolution + 1)
            # Broadcast without storing three full coordinate grids.
            logits = 1 - (axis[:, None, None] ** 2 + axis[None, :, None] ** 2
                          + axis[None, None, :] ** 2).sqrt()
            results = {}
            for device in ('cpu', 'mps'):
                result = module.MCSurfaceExtractor()(logits[None].to(device),
                    mc_level=0, bounds=1.2, octree_resolution=resolution)[0]
                assert result is not None
                results[device] = (result.mesh_v, result.mesh_f)
            cpu_v, cpu_f = results['cpu']
            mps_v, mps_f = results['mps']
            metrics = audit(mps_v, mps_f)
            archive = output / f'sphere{resolution}.npz'
            np.savez_compressed(archive, cpuVertices=cpu_v, cpuFaces=cpu_f,
                                mpsVertices=mps_v, mpsFaces=mps_f)
            expected_centre = np.full(3, -1.2 / (resolution + 1))
            expected_radius = resolution / (resolution + 1)
            radius_error = np.max(np.abs(np.linalg.norm(mps_v - expected_centre, axis=1) - expected_radius))
            case = {'name': 'sphere', 'resolution': resolution, 'nativeAudit': metrics,
                    'CPUAndMPSArraysIdentical': bool(np.array_equal(cpu_v, mps_v) and np.array_equal(cpu_f, mps_f)),
                    'expectedNativeCentre': expected_centre.tolist(), 'expectedNativeRadius': expected_radius,
                    'maxRadiusErrorWithinNativeMapping': float(radius_error),
                    'mapping': 'Installed MC divides grid positions by octree+1; preserve this native shrink/translation.',
                    'fixtureSHA256': sha(archive), 'archivePath': str(archive)}
            case['passClosedConnectivityAndDeviceAgreement'] = bool(
                metrics['boundaryEdges'] == 0 and metrics['overusedEdges'] == 0
                and metrics['zeroAreaTriangles'] == 0 and case['CPUAndMPSArraysIdentical']
                and radius_error < .0001)
            report['cases'].append(case)
            del logits
            torch.mps.empty_cache()
    report['allClosedConnectivityAndDeviceControlsPass'] = all(
        c['passClosedConnectivityAndDeviceAgreement'] for c in report['cases'])
    report['allNativeOrientationsConsistent'] = all(
        c['nativeAudit']['equalDirectionTwoFaceEdges'] == 0 for c in report['cases'])
    report['limits'].append('Connectivity/device pass does not pass native orientation; check its separate flag.')
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
