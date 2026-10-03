"""Analytic cube through actual installed extraction branch; no neural weights."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path

import numpy as np
from audit_native import audit
from orient_derived_preview import orient_derived_preview

SOURCE = Path('/Users/raynos/ml/img2mesh/trellis-mac/stubs/o_voxel_override_convert.py')
SOURCE_SHA = '6de4b7149e7300ac056f2d83eec8d149560cac521cdded4fd812dadffd7bfa5c'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sphere_control(module, torch, output):
    import trimesh
    size=16; extent=3.1; voxel=extent/size
    coords=np.array(list(itertools.product(range(size),repeat=3)),dtype=np.int32)
    centres=(coords+.5)*voxel-extent/2
    projected=centres/np.linalg.norm(centres,axis=1)[:,None]
    dual=(projected+extent/2)/voxel-coords
    flags=np.zeros((len(coords),3),dtype=bool)
    for axis in range(3):
        offset=np.ones(3); offset[axis]=0
        start=(coords+offset)*voxel-extent/2
        end=start.copy(); end[:,axis]+=voxel
        flags[:,axis]=(np.linalg.norm(start,axis=1)<1)!=(np.linalg.norm(end,axis=1)<1)
    v,f=module.flexible_dual_grid_to_mesh(torch.from_numpy(coords),torch.from_numpy(dual.astype(np.float32)),
        torch.from_numpy(flags),torch.ones((len(coords),1)),aabb=[[-extent/2]*3,[extent/2]*3],grid_size=size,train=False)
    v,f=v.numpy(),f.numpy(); raw=audit(v,f)
    assert raw['boundaryEdges']==0 and raw['overusedEdges']==0 and raw['zeroAreaTriangles']==0
    assert np.max(np.abs(np.linalg.norm(v,axis=1)-1))<1e-6
    fixed,adapter=orient_derived_preview(v,f)
    control=trimesh.Trimesh(vertices=v.copy(),faces=fixed,process=False)
    vectors=np.cross(v[fixed[:,1]]-v[fixed[:,0]],v[fixed[:,2]]-v[fixed[:,0]])
    outward=np.einsum('ij,ij->i',vectors,v[fixed].mean(axis=1))
    assert adapter['derivedAudit']['equalDirectionTwoFaceEdges']==0 and np.all(outward>0)
    assert abs(control.volume-4*np.pi/3)/(4*np.pi/3)<.03
    np.savez_compressed(output/'sphere.npz',vertices=v,faces=f,coords=coords,dual=dual,flags=flags)
    return {'definition':'Analytic radius1 sphere, SDF sign-change edge flags and projected cell-centre dual vertices through actual installed extractor',
        'rawAudit':raw,'adapter':adapter,'allDerivedFaceNormalsOutward':True,
        'derivedVolume':float(control.volume),'analyticVolume':float(4*np.pi/3),
        'maximumRadiusError':float(np.max(np.abs(np.linalg.norm(v,axis=1)-1))),
        'localArchiveSHA256':sha(output/'sphere.npz')}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') != str(os.getppid()):
        raise RuntimeError('Use bounded owned-child controller')
    if sha(SOURCE) != SOURCE_SHA: raise ValueError('Installed extraction source changed')
    output = Path(args.out)
    if output.exists(): raise FileExistsError('Fresh fixture directory required')
    import torch
    import trimesh
    spec = importlib.util.spec_from_file_location('pinned_cube_extractor', SOURCE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    coords = np.array(list(itertools.product((0, 1), repeat=3)), dtype=np.int32)
    flags = np.zeros((8, 3), dtype=bool)
    for axis in range(3):
        flags[np.flatnonzero(np.all(coords == [0, 0, 0], axis=1))[0], axis] = True
        anchor = np.zeros(3, dtype=int); anchor[axis] = 1
        flags[np.flatnonzero(np.all(coords == anchor, axis=1))[0], axis] = True
    vertices, faces = module.flexible_dual_grid_to_mesh(
        torch.from_numpy(coords), torch.full((8, 3), .5, dtype=torch.float32),
        torch.from_numpy(flags), torch.ones((8, 1), dtype=torch.float32),
        aabb=[[0, 0, 0], [2, 2, 2]], grid_size=2, train=False)
    v, f = vertices.numpy(), faces.numpy()
    assert len(v) == 8 and len(f) == 12
    assert np.array_equal(v.min(axis=0), [.5, .5, .5]) and np.array_equal(v.max(axis=0), [1.5, 1.5, 1.5])
    raw = audit(v, f)
    assert raw['boundaryEdges'] == 0 and raw['overusedEdges'] == 0 and raw['zeroAreaTriangles'] == 0
    centres = v[f].mean(axis=1)
    normals = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    sign = np.einsum('ij,ij->i', normals, centres - [1, 1, 1])
    # Independent orientation control is applied ONLY to the analytic fixture.
    derived_faces, adapter = orient_derived_preview(v, f)
    control = trimesh.Trimesh(vertices=v.copy(), faces=derived_faces, process=False)
    corrected = audit(control.vertices, control.faces)
    assert corrected['equalDirectionTwoFaceEdges'] == 0 and abs(control.volume - 1) < 1e-8
    output.mkdir(parents=True)
    np.savez_compressed(output / 'cube.npz', vertices=v, faces=f, coords=coords, flags=flags)
    sphere = sphere_control(module, torch, output)
    report = {'accepted': False, 'purpose': 'Analytic cube AND sphere through actual installed learned-split branch and owned derived adapter',
              'sourcePath': str(SOURCE), 'sourceSHA256': sha(SOURCE), 'recipeSHA256': sha(__file__),
              'inputs': {'device': 'CPU', 'dualVertexOffset': [.5, .5, .5], 'splitWeight': 'ones, NON-None like decoder inference', 'closedCubeExtent': 1},
              'rawCube': raw, 'rawOutwardTriangles': int(np.count_nonzero(sign > 0)), 'rawInwardTriangles': int(np.count_nonzero(sign < 0)),
              'fixtureOrientationControl': {'equalDirectionTwoFaceEdges': corrected['equalDirectionTwoFaceEdges'], 'volume': float(control.volume), 'adapter':adapter},
              'localArchiveSHA256': sha(output / 'cube.npz'), 'sphereControl':sphere,'adapterSHA256':sha(Path(__file__).with_name('orient_derived_preview.py')),'modelRuns': 0, 'garmentArraysReadOrChanged': False,
              'inference': 'Known valid cube positions/closed connectivity still emerge with inconsistent orientation; denoising steps are absent from this assembly test.',
              'limits': ['Does not compare CUDA implementation or claim a Mac-only regression',
                         'No actual garment normal repair or extra visual comparison',
                         'Does not prove all dense garment contours are normals-only or qualify a new model run']}
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__': main()
