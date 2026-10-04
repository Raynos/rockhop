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

def causal_saved_controls(output):
    """Current adapter versus validated legacy on retained analytic bytes."""
    output=Path(output);output.mkdir(exist_ok=False,parents=True)
    root=Path.cwd();base=root/'.tmp/generation-comparison-2026-10-03/user-agent2'
    cases=[]
    for label,name in [('cube','cube.npz'),('sphere','sphere.npz')]:
        path=base/'orientation-controls01'/name
        with np.load(path,allow_pickle=False) as saved:v,f=saved['vertices'].copy(),saved['faces'].copy()
        legacy,old_report=orient_derived_preview(v,f)
        derived,report,records=orient_derived_preview(v,f,bounded=True)
        assert np.array_equal(legacy,derived),label+' differs from validated legacy orientation'
        crosses=np.cross(v[derived[:,1]]-v[derived[:,0]],v[derived[:,2]]-v[derived[:,0]])
        centre=np.array([1,1,1]) if label=='cube' else np.zeros(3)
        outward=np.einsum('ij,ij->i',crosses,v[derived].mean(axis=1)-centre)
        assert (outward>0).all() and report['derivedEqualDirectionTwoFaceEdges']==0
        cases.append({'name':label,'savedArchiveSHA256':sha(path),'legacyFacesByteIdentical':True,'outwardNormals':True,'adapter':report})
        np.savez_compressed(output/(label+'.npz'),vertices=v,rawFaces=f,derivedFaces=derived,**records)
    v=np.array([[0,0,0],[1,0,0],[0,1,0],[1,1,0]],np.float32);f=np.array([[0,1,2],[1,2,3]],np.int32)
    derived,report,records=orient_derived_preview(v,f,bounded=True)
    assert np.array_equal(derived[0],f[0]) and report['derivedEqualDirectionTwoFaceEdges']==0 and report['closedOrientablePatches']==0
    cases.append({'name':'open_patch','nativeFirstFaceSignAnchorPreserved':True,'adapter':report})
    np.savez_compressed(output/'open-patch.npz',vertices=v,rawFaces=f,derivedFaces=derived,**records)
    v=np.array([[0,0,0],[1,0,0],[0,1,0],[0,-1,0],[0,0,1]],np.float32);f=np.array([[0,1,2],[0,1,3],[0,1,4]],np.int32)
    derived,report,records=orient_derived_preview(v,f,bounded=True)
    assert report['nonmanifoldEdgesUnchanged']==1 and report['nonmanifoldIncidentFacesPreserved']==3 and np.array_equal(derived,f)
    cases.append({'name':'nonmanifold_edge','nativeRowsPreserved':True,'adapter':report})
    np.savez_compressed(output/'nonmanifold.npz',vertices=v,rawFaces=f,derivedFaces=derived,**records)
    n=5;vertices=[];faces=[]
    for i in range(n):
        angle=i*2*np.pi/n
        for sign in (-1,1):
            radial=1+sign*.2*np.cos(angle/2)
            vertices.append([radial*np.cos(angle),radial*np.sin(angle),sign*.2*np.sin(angle/2)])
    for i in range(n):
        a,b=2*i,2*i+1;c,d=(2*(i+1),2*(i+1)+1) if i<n-1 else (1,0)
        faces.extend([[a,b,c],[b,d,c]])
    v=np.array(vertices,np.float32);f=np.array(faces,np.int32)
    derived,report,records=orient_derived_preview(v,f,bounded=True)
    assert report['contradictoryPatchesUnchanged']==1 and report['contradictoryFacesUnchanged']==len(f) and np.array_equal(derived,f)
    cases.append({'name':'mobius_contradiction','allNativeRowsPreserved':True,'adapter':report})
    np.savez_compressed(output/'mobius.npz',vertices=v,rawFaces=f,derivedFaces=derived,**records)
    receipt={'accepted':False,'controlPass':True,'cases':cases,'adapterSHA256':sha(Path(__file__).with_name('orient_derived_preview.py')),
             'recipeSHA256':sha(__file__),'modelInferenceExtractionRenderCalls':0,'rawGarmentsReadOrChanged':False,
             'limits':['Closed analytic agreement does not establish actual garment orientation/outside or self-intersection.',
                       'Open/native anchored patches have no global outward claim; nonmanifold and contradictions remain explicit.']}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))


def derive_saved_garment(family,control_path,output):
    """Only current frozen bytes after the actual saved analytic gate passes."""
    controls=json.loads(Path(control_path).read_text());assert controls['controlPass'] and len(controls['cases'])==5
    assert controls['adapterSHA256']==sha(Path(__file__).with_name('orient_derived_preview.py'))
    root=Path.cwd();base=root/'.tmp/generation-comparison-2026-10-03/user-agent2'
    name='qualified-trellis01' if family=='trellis' else 'qualified-pixal-decode01'
    native=base/name/'model/native.npz'
    expected='c9e0f72e6df3b2e2c8d2f8d81e989a644c8369b49e1bc845d9f1ebe41f5f8469' if family=='trellis' else 'fa99516e7d19fb3de5f021d9c92bf5d80ad432891b7552c86d39bf6bd2b4d982'
    assert sha(native)==expected
    with np.load(native,allow_pickle=False) as data:v,f=data['vertices'].copy(),data['faces'].copy()
    derived,report,records=orient_derived_preview(v,f,bounded=True)
    assert np.array_equal(np.sort(f,axis=1),np.sort(derived,axis=1))
    output=Path(output);output.mkdir(exist_ok=False,parents=True)
    archive=output/'derived-orientation.npz';np.savez_compressed(archive,faces=derived,**records)
    assert sha(native)==expected
    receipt={'accepted':False,'model':family,'nativeSHA256':expected,'nativeVertexCBytesSHA256':hashlib.sha256(v.tobytes()).hexdigest(),
             'rawFaceCBytesSHA256':hashlib.sha256(f.tobytes()).hexdigest(),'derivedFaceCBytesSHA256':hashlib.sha256(derived.tobytes()).hexdigest(),
             'outputArchiveSHA256':sha(archive),'controlReceiptSHA256':sha(control_path),'adapterSHA256':controls['adapterSHA256'],
             'adapter':report,'modelInferenceExtractionRenderCalls':0,'rawArchiveStillIdentical':True,
             'limits':['DERIVED display face order only; raw vertex positions and each original per-row face vertex SET retained.',
                       'Native sampled materials unchanged; no normals bake, topology repair or model selection.']}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', required=True)
    parser.add_argument("--causal-controls",action="store_true");parser.add_argument("--derived-family",choices=["trellis","pixal"]);parser.add_argument("--causal-controls-receipt")
    args = parser.parse_args()
    if os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') != str(os.getppid()):
        raise RuntimeError('Use bounded owned-child controller')
    if args.causal_controls:
        causal_saved_controls(args.out);return
    if args.derived_family:
        assert args.causal_controls_receipt
        derive_saved_garment(args.derived_family,args.causal_controls_receipt,args.out);return
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
