"""Read back the one frozen homology receipt; no new cycle search or source edit."""
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


base = Path('docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/glove-cavity09')
receipt = json.loads((base / 'localization.json').read_text())
guard = json.loads((base / 'diagnosis-guard/guard.json').read_text())
assert guard['exitCode'] == 0 and guard['limitSeconds'] == 60
assert guard['elapsedSeconds'] < 60
assert sha(receipt['source']['path']) == receipt['source']['sha256']
assert sha(receipt['rawCertificate']['path']) == receipt['rawCertificate']['sha256']
assert receipt['recipeSHA256'] == sha('assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/glove-cavity09/localize-handle.py')
source = np.load(receipt['source']['path'])
certificate = np.load(receipt['rawCertificate']['path'])
faces, xyz = source['faces'], source['vertices']
edges = certificate['sourceEdgeVertexIds']
rows = {}
for row, face in enumerate(faces):
    for a, b in zip(face, np.roll(face, -1)):
        rows.setdefault(tuple(sorted((int(a), int(b)))), []).append(row)
assert np.array_equal(edges, np.array(sorted(rows)))
incidence = [rows[tuple(edge)] for edge in edges]
cap = len(faces)
assert np.array_equal(certificate['dualIncidentFaceRows'], np.array([r if len(r) == 2 else r + [cap] for r in incidence]))
parity = np.zeros(cap + 1, np.uint8)
for code, pair in zip(certificate['edgeCocycleCodes'], certificate['dualIncidentFaceRows']):
    parity[pair[0]] ^= code
    parity[pair[1]] ^= code
assert not parity.any()
primal, dual, leftover = [set(certificate[name].tolist()) for name in ['primalTreeEdges', 'dualTreeEdges', 'leftoverEdges']]
assert not primal & dual and not primal & leftover and not dual & leftover
assert primal | dual | leftover == set(range(len(edges)))
assert [len(primal), len(dual), len(leftover)] == [7305, 14543, 2]
assert [int(np.bitwise_xor.reduce(certificate['edgeCocycleCodes'][certificate[name]])) for name in ['referenceCycle0', 'referenceCycle1']] == [1, 2]
edge_lookup = {tuple(edge): index for index, edge in enumerate(edges)}
cycles = []
for cycle in receipt['localizedCycles']:
    ids = cycle['sourceVertexIds']
    pairs = [tuple(sorted((ids[i], ids[(i + 1) % len(ids)]))) for i in range(len(ids))]
    assert pairs == [tuple(edge) for edge in cycle['sourceEdges']]
    assert len(ids) == len(set(ids)) and len(pairs) == len(set(pairs))
    indices = [edge_lookup[pair] for pair in pairs]
    assert int(np.bitwise_xor.reduce(certificate['edgeCocycleCodes'][indices])) == cycle['homologyClass']
    assert np.array_equal(xyz[ids], np.array(cycle['sourceXYZ']))
    incident = sorted({row for index in indices for row in incidence[index]})
    assert incident == cycle['incidentRetainedFaceRows']
    assert source['sourcePrototypeFaceRows'][incident].tolist() == cycle['incidentPrototypeFaceRows']
    assert source['originalTriangleRows'][ids].tolist() == cycle['vertexDenseTriangleRows']
    assert np.array_equal(source['barycentric'][ids], np.array(cycle['vertexDenseBarycentric']))
    length = float(np.linalg.norm(np.roll(xyz[ids], -1, axis=0) - xyz[ids], axis=1).sum())
    assert length == cycle['lengthSourceUnits']
    cycles.append({'class': cycle['homologyClass'], 'vertices': len(ids), 'actualSourceEdges': len(indices), 'lengthSourceUnits': length, 'incidentSourceFaces': len(incident), 'sourceIDXYZLineageExact': True})
boundary_vertices = np.unique(edges[certificate['virtualCuffBoundaryEdges']])
worker_text = (base / 'diagnosis-guard/worker.log').read_text()
assert len(worker_text.splitlines()) == 1 and json.loads(worker_text)['roots'] == 17
report = {'acceptedWearable': False, 'status': 'FROZEN_HOMOLOGY_RECEIPT_ARRAY_READBACK_PASS', 'validatorSHA256': sha(__file__), 'localizationSHA256': sha(base / 'localization.json'), 'commandSHA256': sha(base / 'COMMAND.txt'), 'guardSHA256': sha(base / 'diagnosis-guard/guard.json'), 'sourceSHA256After': sha(receipt['source']['path']), 'rawCertificateSHA256': sha(receipt['rawCertificate']['path']), 'workerExitCode': guard['exitCode'], 'guardElapsedSeconds': guard['elapsedSeconds'], 'workerOutputJSON': json.loads(worker_text), 'workerWarnings': 0, 'disjointTreeCotreeLeftoverCounts': [len(primal), len(dual), len(leftover)], 'actualSourceFaceCocycleParityNonzero': int(np.count_nonzero(parity)), 'virtualCuffVertices': len(boundary_vertices), 'cuffBoundarySourceBounds': [xyz[boundary_vertices].min(0).tolist(), xyz[boundary_vertices].max(0).tolist()], 'cuffBoundarySourceMean': xyz[boundary_vertices].mean(0).tolist(), 'cycles': cycles, 'limits': ['Readback of frozen arrays and certificate only, no second cycle search/native/model/fit/cut/render.', 'The cuff is virtual algebra only. The cycles certify nontrivial surface homology, not geometric cavity traversal, free volume, enclosed fingers or wearable acceptance.', 'All coordinates/lengths in uncalibrated source units. Label0 still has unresolved palm/web/cuff semantics.']}
(base / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'cycles': cycles}))
