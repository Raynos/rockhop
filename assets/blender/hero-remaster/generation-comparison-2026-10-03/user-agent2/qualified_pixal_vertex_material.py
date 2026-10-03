"""Actual native voxel interpolation at raw vertices; no geometry edits/bake."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np


def sha(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(args.native) == 'fa99516e7d19fb3de5f021d9c92bf5d80ad432891b7552c86d39bf6bd2b4d982'
    sys.path.insert(0, '/Users/raynos/ml/img2mesh/Pixal3D-mac')
    import generate_mps as installed
    installed.load_runtime_deps()
    import torch
    assert torch.__version__=='2.12.0'
    from flex_gemm import kernels
    from flex_gemm.ops.grid_sample import grid_sample_3d
    from qualified_sparse_sampling import sample_with_float32_trilinear
    assert kernels._BACKEND == 'metal'
    control = json.loads(Path('docs/evidence/hero-remaster/generation-comparison-2026-10-03/user-agent2/qualified-pixal-sparse02/receipt.json').read_text())
    assert sha(kernels.metal._C.__file__) == control['compiledExtension']['SHA256']
    assert sha(Path(kernels.metal.__file__).parent/'flex_gemm.metallib') == control['metallib']['SHA256']
    with np.load(args.native, allow_pickle=False) as raw:
        vertices = raw['vertices'].copy()
        coords = raw['coords'].copy()
        attributes = raw['attrs'].copy()
        origin = raw['origin'].copy()
    assert vertices.dtype == attributes.dtype == np.float32 and coords.dtype == np.int32
    assert len(vertices) == 2823607 and len(coords) == len(attributes)
    # SparseTensor's installed __cal_spatial_shape is coords.amax+1.
    spatial = coords.max(axis=0).astype(np.int64) + 1
    assert (coords>=0).all() and (spatial<=1024).all()
    shape = (1,6,*spatial.tolist())
    grid = np.ascontiguousarray((vertices-origin)*1024, dtype=np.float32)
    coords4 = np.column_stack((np.zeros(len(coords),np.int32), coords))
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {'accepted':False, 'nativeSHA256':sha(args.native), 'recipeSHA256':sha(__file__),
              'definition':'Installed voxel-center trilinear values at original raw vertices, for display only',
              'voxelSize':1/1024, 'shape':shape, 'inputDtype':'float32',
              'interpolation':'Native existing-neighbor weight renormalization; no KDTree, dense fill or nearest substitute',
              'chunkVertices':131072, 'chunks':[], 'geometryChanged':False,
              'limits':['Per-vertex display derivative, not a UV texture bake or map-level pass.',
                        'Selected CPU coordinate oracle, not full CUDA/mesh/material equivalence.']}
    started = time.monotonic()
    def save():
        report['elapsedSeconds'] = time.monotonic()-started
        (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    feats = torch.from_numpy(attributes).to('mps')
    c = torch.from_numpy(coords4).to('mps')
    sampled = np.empty((len(vertices),6),np.float32)
    with torch.inference_mode():
        for start in range(0,len(vertices),131072):
            end = min(start+131072,len(vertices))
            q = torch.from_numpy(grid[start:end][None]).to('mps')
            value = sample_with_float32_trilinear(grid_sample_3d,feats,c,shape,q)[0].cpu().numpy()
            sampled[start:end] = value
            archive = out/f'chunk-{start:07d}.npz'
            np.savez_compressed(archive,grid=grid[start:end],sampled=value)
            report['chunks'].append({'start':start,'end':end,'SHA256':sha(archive),'finite':bool(np.isfinite(value).all())})
            save()
            assert np.isfinite(value).all()
            del q,value
            torch.mps.synchronize()
            active=torch.mps.current_allocated_memory()
            torch.mps.empty_cache()
            assert torch.mps.current_allocated_memory()==active
    # Independent sorted coordinate lookup; all eight basis corners and only
    # their existing weights participate. No nearest-feature approximation.
    keys = (coords[:,0].astype(np.int64)*spatial[1]+coords[:,1])*spatial[2]+coords[:,2]
    order = np.argsort(keys)
    sorted_keys = keys[order]
    assert (np.diff(sorted_keys)>0).all(), 'Duplicate source voxel coordinates'
    selected = np.unique(np.linspace(0,len(vertices)-1,257).astype(np.int64))
    queries = grid[selected].astype(np.float64)
    basis = np.floor(queries-.5).astype(np.int64)
    reference = np.zeros((len(selected),6),np.float64)
    total = np.zeros(len(selected),np.float64)
    for x in (0,1):
        for y in (0,1):
            for z in (0,1):
                xyz=basis+np.array([x,y,z])
                valid=((xyz>=0)&(xyz<spatial)).all(axis=1)
                candidate=(xyz[:,0]*spatial[1]+xyz[:,1])*spatial[2]+xyz[:,2]
                index=np.searchsorted(sorted_keys,candidate).clip(0,len(sorted_keys)-1)
                valid &= sorted_keys[index]==candidate
                weights=np.prod(1-np.abs(queries-xyz-.5),axis=1)*valid
                reference += attributes[order[index]].astype(np.float64)*weights[:,None]
                total += weights
    reference /= np.where(total>=1e-12,total,1)[:,None]
    error=float(np.max(np.abs(sampled[selected]-reference)))
    np.savez_compressed(out/'actual-selected-coordinate-control.npz',selected=selected,queries=queries,reference=reference,observed=sampled[selected])
    np.savez_compressed(out/'vertex-material.npz',attrs=sampled)
    report.update(selectedVertices=len(selected),maxCPUFloat64Error=error,fixedThreshold=1e-5,
                  outputSHA256=sha(out/'vertex-material.npz'),outputCBytesSHA256=hashlib.sha256(sampled.tobytes()).hexdigest(),
                  materialMin=sampled.min(axis=0).tolist(),materialMax=sampled.max(axis=0).tolist(),
                  originalArchiveStillIdentical=sha(args.native)=='fa99516e7d19fb3de5f021d9c92bf5d80ad432891b7552c86d39bf6bd2b4d982')
    save()
    assert error<=1e-5 and report['originalArchiveStillIdentical']
    report['status']='Actual native vertex material sampled; matched moving review pending'
    save()
    print(json.dumps({k:report[k] for k in ('status','maxCPUFloat64Error','elapsedSeconds')}))


if __name__=='__main__':
    main()
