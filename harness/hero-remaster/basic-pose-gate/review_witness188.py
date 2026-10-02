"""Independent parent raw-GLB reconstruction of actual Three witnesses/path."""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

R = Path('/Users/raynos/projects/games/rockhop')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/source-rig188'
A = E / 'actual-three'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB, worlds
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (E / 'parent-review.json').exists(), 'Preserve finished parent review'
verified = []
for folder in ['read-only', 'actual-three']:
    freeze = json.loads((E / folder / 'freeze.json').read_text())
    for rec in freeze['files']:
        p = Path(rec['path'])
        assert p.stat().st_size == rec['bytes'] and sha(p) == rec['SHA256'], str(p)
        verified.append(rec)
pins = json.loads((E / 'read-only/report.json').read_text())['pins']
for rec in pins:
    assert sha(rec['path']) == rec['SHA256'], rec['path']
archives = json.loads((A / 'lossless-archives.json').read_text())['archives']
for rec in archives:
    packed = Path(rec['path']).read_bytes()
    raw = gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest() == rec['SHA256']
    assert len(raw) == rec['uncompressedBytes']
    assert hashlib.sha256(raw).hexdigest() == rec['uncompressedSHA256']
report = json.loads((A / 'report.json').read_text())
g = GLB(report['source'])
assert sha(g.path) == report['sourceSHA256']
fixture = json.loads(Path(report['fixture']).read_text())
assert sha(report['fixture']) == report['fixtureSHA256']
skin = g.j['skins'][0]
rest = np.asarray(worlds(g.j))[skin['joints']]
inverse = g.array(skin['inverseBindMatrices']).reshape(19,4,4).transpose(0,2,1)
fields = []
for primitive in g.j['meshes'][0]['primitives']:
    attrs = primitive['attributes']
    p = g.array(attrs['POSITION']).astype(float)
    j = g.array(attrs['JOINTS_0'])
    raw = g.array(attrs['WEIGHTS_0']).astype(float)
    w = (raw / np.abs(raw).sum(1,keepdims=True)).astype('f4').astype(float)
    W = np.zeros((len(p),19))
    for k in range(4):
        np.add.at(W,(np.arange(len(p)),j[:,k]),w[:,k])
    morphs = [g.array(t['POSITION']).astype(float) for t in primitive.get('targets',[])]
    fields.append((p,W,morphs,g.array(primitive['indices']).reshape(-1,3)))
names = g.j['meshes'][0]['extras']['targetNames']
trajectories = json.loads(gzip.decompress((A / 'witness-trajectories.json.gz').read_bytes()))
assert len(trajectories) == len(fixture['frames'])*4 == 21616
maximum = 0.0
for i, frame in enumerate(fixture['frames']):
    D = np.asarray(frame['deformationWorldColumnMajor']).reshape(19,4,4).transpose(0,2,1)
    M = D @ rest @ inverse
    for k, witness in enumerate(report['witnesses']):
        rec = trajectories[i*4+k]
        assert (rec['witness'],rec['family'],rec['frame']) == (witness['label'],frame['family'],frame['frame'])
        ids = witness['ids']
        p,W,morphs,_ = fields[witness['field']]
        points = p[ids].copy()
        for name, delta in zip(names,morphs):
            side = frame.get('gripSide')
            matches = not side or name.endswith('.'+side) or name.endswith('_'+side)
            alpha = frame['closedGrip'] if 'grip' in name.lower() and matches else 0
            points += alpha*delta[ids]
        predicted = np.einsum('vj,jab,vb->va',W[ids],M[:,:3,:],np.c_[points,np.ones(2)])
        actual = np.asarray(rec['actualWorldPositionsM'])
        error = float(np.linalg.norm(predicted-actual,axis=1).max())
        maximum = max(maximum,error)
        assert error < 1e-10
        assert abs(np.linalg.norm(actual[1]-actual[0])-rec['edgeLengthM']) < 1e-12
# Rebuild the physical topology; verify exact patch and literal constrained path.
P = np.concatenate([f[0] for f in fields])
U, inv = np.unique(P,axis=0,return_inverse=True)
offset = np.r_[0,np.cumsum([len(f[0]) for f in fields])]
T = inv[np.concatenate([f[3]+offset[i] for i,f in enumerate(fields)])]
edges = np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1),axis=0)
length = np.linalg.norm(U[edges[:,0]]-U[edges[:,1]],axis=1)
graph = coo_matrix((np.r_[length,length],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(U),len(U))).tocsr()
distance = dijkstra(graph,indices=inv[[2030,2172]],directed=False,min_only=True)
inside = distance <= .04
cross = edges[inside[edges[:,0]] != inside[edges[:,1]]]
outer = np.unique(cross[inside[cross]])
inventory = json.loads((A / 'patch-inventory.json').read_text())
assert np.flatnonzero(inside).tolist() == [x['physicalID'] for x in inventory]
assert len(inventory) == 52 and len(outer) == 24
proof = json.loads((A / 'preflight-edges2mm.json').read_text())['worst']
path = proof['pathPhysicalIDs']
edge_set = set(map(tuple,edges.tolist()))
assert all(tuple(sorted(pair)) in edge_set for pair in zip(path,path[1:]))
assert all(inside[i] for i in path) and path[0] in outer and path[-1] in outer
L = np.linalg.norm(np.diff(U[path],axis=0),axis=1)
assert L.min() >= .002 and np.allclose(L,proof['pathRestEdgeLengthsM'],atol=1e-15,rtol=0)
frame = next(f for f in fixture['frames'] if f['family']==proof['family'] and f['frame']==proof['frame'])
D = np.asarray(frame['deformationWorldColumnMajor']).reshape(19,4,4).transpose(0,2,1)
M = D @ rest @ inverse
ids = [np.flatnonzero(inv[:offset[1]]==path[i])[0] for i in [0,-1]]
p,W,_,_ = fields[0]
Q = np.einsum('vj,jab,vb->va',W[ids],M[:,:3,:],np.c_[p[ids],np.ones(2)])
span = float(np.linalg.norm(Q[1]-Q[0]))
assert abs(span-proof['posedEndpointDistanceM']) < 1e-12
bound = span/float(L.sum())
assert abs(bound-proof['minimumNecessaryStrainBound']) < 1e-12 and bound > 1.5
result = {'status':'ACTUAL_WITNESSES_RECONSTRUCTED_TINY_PATCH_REJECTED_NOT_GLOBAL_INFEASIBILITY','frozenFilesVerified':len(verified),'inputPinsVerified':len(pins),'losslessArchivesVerified':len(archives),'actualControlledFrames':5404,'actualWitnessRecordsReconstructed':len(trajectories),'maximumActualVsParentRawAffineErrorM':maximum,'patchPhysicalNodes':52,'fixedOuterNodes':24,'constrainedPathPhysicalIDs':path,'sourcePathEdgeLengthsM':L.tolist(),'posedFixedEndpointDistanceM':span,'minimumNecessaryStrain':bound,'proposedMaximumStrain':1.5,'weightsSolverOrGeometryOutputs':0,'limits':'Seven finite vertices on authored controls only. Refutes this exact fixed-boundary40mm patch, not broader ownership/construction or deformation. Existing played187 web/hip failures remain; no anatomy/contact/Garage/game/mobile acceptance.'}
(E / 'parent-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
