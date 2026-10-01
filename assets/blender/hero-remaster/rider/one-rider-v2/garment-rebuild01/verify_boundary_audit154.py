"""Independent parent topology check of unbuilt seam proposals; CPU, read-only."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import struct
import numpy as np

ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
EVIDENCE = Path('docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01')
SOURCE = ROOT/'rig-adapter01/body-bind34/rider.glb'
CAGE = ROOT/'garment-rebuild01/cage04/fit04.npz'
raw = SOURCE.read_bytes()
fit_raw = CAGE.read_bytes()
sha = lambda b: hashlib.sha256(b).hexdigest()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20+n])
blob = raw[28+n:]

def accessor(i):
    a = doc['accessors'][i]
    v = doc['bufferViews'][a['bufferView']]
    assert 'sparse' not in a and 'byteStride' not in v
    widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    dtype = {5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]
    return np.frombuffer(blob, dtype=dtype, count=a['count']*widths[a['type']],
        offset=v.get('byteOffset', 0)+a.get('byteOffset', 0)).reshape(a['count'], -1)

def physical_primitive(i):
    p = doc['meshes'][0]['primitives'][i]
    positions, inv = np.unique(accessor(p['attributes']['POSITION']), axis=0,
        return_inverse=True)
    return positions, inv[accessor(p['indices']).reshape(-1, 3)]

def edge_uses(faces, namespace):
    uses = defaultdict(list)
    for face in faces:
        for a, b in zip(face, np.roll(face, -1)):
            x, y = (namespace, int(a)), (namespace, int(b))
            uses[tuple(sorted((x, y)))].append((x, y))
    return uses

proposal_raw = (EVIDENCE/'cuff-sole-audit154/sewing-proposal.json').read_bytes()
proposal = json.loads(proposal_raw)
assert proposal['sourceSHA256'] == sha(raw)
assert proposal['fit04SHA256'] == sha(fit_raw)
fit = np.load(CAGE)
P, inv = np.unique(fit['positions'], axis=0, return_inverse=True)
Q = inv[fit['quads']]
rows = []
for seam in proposal['seams']:
    SP, ST = physical_primitive(seam['sourcePrimitive'])
    if seam['sourceScope'] == 'shoeCutY02':
        ST = ST[(SP[ST, 1] < .2).all(1)]
    keep = np.ones(len(Q), dtype=bool)
    keep[seam['nativeRemovedQuadIDs']] = False
    native_edges = edge_uses(Q[keep], 'native')
    source_edges = edge_uses(ST, 'source')
    new_edges = defaultdict(list)
    for triangle in seam['bridgeTrianglesPhysicalNamespace']:
        for a, b in zip(triangle, triangle[1:]+triangle[:1]):
            x, y = tuple(a), tuple(b)
            new_edges[tuple(sorted((x, y)))].append((x, y))
    incidence_bad = []
    winding_bad = []
    for edge, uses in new_edges.items():
        combined = uses+native_edges.get(edge, [])+source_edges.get(edge, [])
        if len(combined) != 2:
            incidence_bad.append(edge)
        elif combined[0] != combined[1][::-1]:
            winding_bad.append(edge)
    # Check EVERY original ring edge was sewn, not merely the generated edges.
    missing = []
    for namespace, ring in [('native', seam['nativeOrderedPhysicalIDs']),
                             ('source', seam['sourceOrderedPhysicalIDs'])]:
        for a, b in zip(ring, ring[1:]+ring[:1]):
            e = tuple(sorted(((namespace, a), (namespace, b))))
            if e not in new_edges:
                missing.append(e)
    triangles = np.array([[P[i] if kind == 'native' else SP[i]
        for kind, i in tri] for tri in seam['bridgeTrianglesPhysicalNamespace']])
    areas = np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0],
        triangles[:, 2]-triangles[:, 0]), axis=1)/2
    assert not incidence_bad and not winding_bad and not missing
    assert areas.min() > 0
    rows.append({'seam': seam['name'], 'triangles': len(triangles),
        'edgeIncidenceErrors': len(incidence_bad), 'windingErrors': len(winding_bad),
        'missingRingEdges': len(missing), 'minimumRestTriangleAreaM2': float(areas.min())})

neck = json.loads((EVIDENCE/'neck-boundary-audit154/report.json').read_text())
shells = json.loads((EVIDENCE/'neck-boundary-audit154/native-transition-shells.json').read_text())
assert neck['sourceSHA256'] == sha(raw) and neck['cageSHA256'] == sha(fit_raw)
assert neck['sharedExactPositions'] == 307
assert neck['protectedInterfaceAttributes']['dense19WeightMaxDelta'] == 0
assert shells[-1]['faceShellsFromCollar'] == 8
assert len(shells[-1]['removedQuadIDs']) == 200
assert shells[-1]['newBoundaryComponents'][0]['degreeHistogram'] == {'2': 60}
assert SOURCE.read_bytes() == raw and CAGE.read_bytes() == fit_raw
report = {'sourceSHA256': sha(raw), 'fit04SHA256': sha(fit_raw),
    'proposalSHA256': sha(proposal_raw), 'sewingTopologyChecks': rows,
    'protectedHoodEndpointCount': 307, 'protectedHoodWeightDelta': 0,
    'nativeTransitionShellQuads': 200, 'nativeTransitionRingVertices': 60,
    'sourceAndFitUnchanged': True,
    'judgment': 'Retain literal topology evidence. Reject blind bridge construction: cuff CPU collapses and shoulder transition still needs anatomical fitting.',
    'limits': ['No model was sewn or reweighted.',
        'Topological ordering does not prove absence of geometric intersections.',
        'Four recorded-state CPU samples are diagnostics, not moving appearance acceptance.',
        'No new full-body/face grade, sitting, Garage or visible contact pass.']}
(EVIDENCE/'parent-boundary-review154.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
