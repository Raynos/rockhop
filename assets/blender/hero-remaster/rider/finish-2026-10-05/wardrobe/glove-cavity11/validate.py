"""Read back frozen25path witnesses and lineage; no second geometry assay."""
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


base = Path('docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/glove-cavity11')
report = json.loads((base / 'probe.json').read_text())
guard = json.loads((base / 'probe-guard/guard.json').read_text())
assert guard['exitCode'] == 0 and guard['elapsedSeconds'] < guard['limitSeconds'] == 60
assert report['recipeSHA256'] == sha('assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/glove-cavity11/probe-paths.py') == '2edd6d7279f73d82cc8a23382de213a0b3aaa28c5d710cb8b3afd71a3096db09'
assert sha(report['source']['path']) == report['source']['sha256']
assert all(sha(pin['path']) == pin['sha256'] for pin in report['inputPins'])
assert sha(report['raw']['path']) == report['raw']['sha256']
source, raw = np.load(report['source']['path']), np.load(report['raw']['path'])
xyz, faces = source['vertices'].astype(np.float64), source['faces']
assert len(report['records']) == 25
max_bary_residual, max_path_residual = 0., 0.
compact = []
for record in report['records']:
    key = f"anchor{record['anchorIndex']}-station{record['endY']}"
    distance2 = raw[key + '-surfaceDistanceSquared']
    hit_mask = raw[key + '-nonparallelFaceIntersections']
    assert distance2.shape == hit_mask.shape == (14543,) and np.isfinite(distance2).all() and (distance2 >= 0).all()
    nearest = int(distance2.argmin())
    assert float(np.sqrt(distance2[nearest])) == record['minimumWholeSegmentSurfaceDistanceSourceUnits']
    hit_rows = np.flatnonzero(hit_mask)
    fractions = raw[key + '-intersectionFractions']
    hit_rows = hit_rows[np.lexsort((hit_rows, fractions[hit_rows]))]
    assert len(hit_rows) == record['surfaceIntersectionFaceCount']
    assert hit_rows.tolist() == [hit['lineage']['retainedFaceRow'] for hit in record['allIntersectionFacesIncludingCoincidentEdgeHits']]
    witnesses = [record['closestSurfaceLineage']] + [hit['lineage'] for hit in record['allIntersectionFacesIncludingCoincidentEdgeHits']]
    start, end = np.array(record['startSourceXYZ']), np.array(record['endSourceXYZ'])
    assert start[1] < xyz[:, 1].min() and start[0] == end[0] and start[2] == end[2]
    assert np.array_equal(raw[key + '-surfacePathWitnesses'][nearest], np.array(record['closestPathSourceXYZ']))
    assert np.array_equal(raw[key + '-surfaceWitnesses'][nearest], np.array(record['closestSurfaceLineage']['witnessSourceXYZ']))
    for witness in witnesses:
        row = witness['retainedFaceRow']
        assert row == nearest if witness is witnesses[0] else row in hit_rows
        vertices = faces[row]
        assert vertices.tolist() == witness['sourceVertexIds']
        assert int(source['sourcePrototypeFaceRows'][row]) == witness['prototypeFaceRow']
        assert source['originalTriangleRows'][vertices].tolist() == witness['denseTriangleRowsByCorner']
        assert np.array_equal(source['barycentric'][vertices], np.array(witness['denseBarycentricByCorner']))
        assert np.array_equal(source['cornerUVPrototype'][row], np.array(witness['prototypeCornerUV']))
        weights = np.array(witness['witnessTriangleBarycentric'])
        reconstructed = (xyz[vertices] * weights[:, None]).sum(0)
        residual = float(np.linalg.norm(reconstructed - witness['witnessSourceXYZ']))
        assert residual < 1e-10 and abs(weights.sum() - 1) < 1e-10 and weights.min() > -1e-9
        max_bary_residual = max(max_bary_residual, residual)
        assert np.array_equal((source['cornerUVPrototype'][row] * weights[:, None]).sum(0), np.array(witness['witnessPrototypeUV']))
    for hit in record['allIntersectionFacesIncludingCoincidentEdgeHits']:
        row = hit['lineage']['retainedFaceRow']
        assert hit['pathFraction'] == float(fractions[row])
        assert np.array_equal(raw[key + '-intersectionBarycentric'][row], np.array(hit['triangleBarycentric']))
        point = start + hit['pathFraction'] * (end - start)
        residual = float(np.linalg.norm(point - hit['lineage']['witnessSourceXYZ']))
        assert residual < 1e-10
        max_path_residual = max(max_path_residual, residual)
    relations = [(record['boundaryRelation'], 'closestBoundarySourceEdge', 'boundaryWitness')] + [(r, 'closestSourceEdge', 'cycleWitness') for r in record['cycleRelations']]
    for relation, edge_key, point_key in relations:
        a, b = xyz[relation[edge_key]]
        point, path = np.array(relation[point_key]), np.array(relation['pathWitness'])
        d = b - a
        fraction = float(((point - a) * d).sum() / (d * d).sum())
        assert -1e-10 <= fraction <= 1 + 1e-10 and np.linalg.norm(a + fraction * d - point) < 1e-10
        assert abs(path[0] - start[0]) < 1e-10 and abs(path[2] - start[2]) < 1e-10
        assert start[1] - 1e-10 <= path[1] <= end[1] + 1e-10
        assert abs(np.linalg.norm(path - point) - relation['minimumDistanceSourceUnits']) < 1e-12
    compact.append({'anchor': record['anchorIndex'], 'endY': record['endY'], 'intersectionFaces': len(hit_rows), 'minimumSourceUnits': record['minimumWholeSegmentSurfaceDistanceSourceUnits'], 'firstHitY': record['allIntersectionFacesIncludingCoincidentEdgeHits'][0]['sourceY'] if len(hit_rows) else None, 'hitPrototypeFaces': [hit['lineage']['prototypeFaceRow'] for hit in record['allIntersectionFacesIncludingCoincidentEdgeHits']], 'boundaryDistanceSourceUnits': record['boundaryRelation']['minimumDistanceSourceUnits'], 'cycleDistancesSourceUnits': [r['minimumDistanceSourceUnits'] for r in record['cycleRelations']]})
worker_text = (base / 'probe-guard/worker.log').read_text()
assert len(worker_text.splitlines()) == 1
worker = json.loads(worker_text)
assert worker['segments'] == 25
film = Path('docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/glove-cavity10/paired-pbr-source-context.mp4')
assert sha(film) == '96e0a00b35c602dd0e35ce4d0c2db32d6a30f468fbc9970b41bbbe679acd5a83'
validation = {'acceptedWearable': False, 'status': 'FROZEN25PATH_WITNESS_AND_LINEAGE_READBACK_PASS', 'validatorSHA256': sha(__file__), 'probeSHA256': sha(base / 'probe.json'), 'guardSHA256': sha(base / 'probe-guard/guard.json'), 'workerExitCode': guard['exitCode'], 'elapsedSeconds': guard['elapsedSeconds'], 'sourceSHA256After': sha(report['source']['path']), 'sourceFilm41SHA256Unchanged': sha(film), 'rawSHA256': sha(report['raw']['path']), 'workerWarnings': 0, 'workerSummary': worker, 'maximumSourceTriangleBarycentricReconstructionResidual': max_bary_residual, 'maximumPathHitReconstructionResidual': max_path_residual, 'finiteWholeSurfaceDistanceArraysVerified': 25, 'records': compact, 'limits': ['Readback only, no second segment/triangle minimum or intersection assay. Parent independently judges the declared finite relation.', 'Finite zero-radius path/surface relation only; no endpoint occupancy, general cavity volume, hand-size clearance, specific cuff-mouth entry, strap/defect diagnosis or cut/fit acceptance.']}
(base / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps({'status': validation['status'], 'summary': worker, 'maximumBarycentricResidual': max_bary_residual}))
