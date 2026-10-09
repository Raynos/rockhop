"""Separate saved-native full contact and actual cloth tangent qualification."""
import hashlib
import runpy
from pathlib import Path
import numpy as np


def measure(report, config, hoodie, body, faces, out):
    h = runpy.run_path(str(Path(__file__).with_name('component.py')))
    checked, write, pin = (h[k] for k in ('checked', 'write', 'pin'))
    helper = runpy.run_path(str(h['HERE'].parent/'selected-sleeve-rebuild28/author.py'))
    original = np.load(checked(config['pins']['original47Arrays']))['points'].astype(float)
    current = np.empty_like(original, dtype=np.float32); hoodie.data.vertices.foreach_get('co', current.ravel())
    current = current.astype(float)
    bp = np.empty((len(body.data.vertices), 3), np.float32); body.data.vertices.foreach_get('co', bp.ravel())
    body.data.calc_loop_triangles(); bf = np.empty((len(body.data.loop_triangles), 3), np.int32)
    body.data.loop_triangles.foreach_get('vertices', bf.ravel())
    nearest = helper['actual_nearest'](bp, bf)
    retained = np.load(checked(report['qualificationInputs']))['retainedOriginalFaceIds']
    used = np.unique(faces[retained]); minimum = float('inf'); minimum_row = None
    below = 0; target = report['anatomicalRegistration']['contactTargetM']
    threshold = target-config['field']['numericalContactToleranceM']
    for kind, ids in (('originalNativeVertex', used), ('originalNativeFaceCentroid', retained)):
        for start in range(0, len(ids), 32768):
            chosen = ids[start:start+32768]
            points = current[chosen] if kind == 'originalNativeVertex' else current[faces[chosen]].mean(1)
            gap, _ = nearest(points); below += int((gap < threshold).sum())
            index = int(np.argmin(gap))
            if gap[index] < minimum:
                minimum = float(gap[index]); minimum_row = {'kind': kind, 'id': int(chosen[index]),
                    'point': points[index].tolist(), 'signedGapM': minimum}
        print('QUALIFY58 full retained '+kind+' minimum '+str(minimum), flush=True)
    displacement = np.linalg.norm(current-original, axis=1); changed = displacement > 0
    # All retained corners/centroids are measured, including fixed/changed
    # frontiers. This is stronger coverage than a selected support boundary.
    frontier = faces[retained][np.any(changed[faces[retained]], axis=1) & ~np.all(changed[faces[retained]], axis=1)]
    boundary = np.unique(frontier)
    boundary_minimum = float(nearest(current[boundary])[0].min()) if len(boundary) else minimum
    metrics, stretch, area = runpy.run_path(str(checked(config['pins']['tangent54'])))['measure'](original, current, faces)
    witness_ids = [754365, 713389, 734276, 729981]
    witnesses = []
    for face in witness_ids:
        point = current[faces[face]].mean(0)
        witnesses.append({'originalNativeFaceId': face, 'originalNativeVertexIds': faces[face].tolist(),
            'originalCentroid': original[faces[face]].mean(0).tolist(), 'savedCentroid': point.tolist(),
            'tangentPrincipalStretches': stretch[face].tolist(), 'areaRatio': float(area[face]),
            'signedFullReferenceCentroidGapM': float(nearest(point[None])[0][0])})
    pair = h['read'](config['pins']['sourcePair49']); first = pair['sourceFaceId']
    hit = pair['rays']['awayArmAxis']['firstHits'][0]; second = hit['sourceFaceId']; bary = np.asarray(hit['sourceBarycentric'])
    spans = []
    for points in (original, current):
        a = points[faces[first]].mean(0); b = bary@points[faces[second]]
        spans.append({'inner': a.tolist(), 'outer': b.tolist(), 'fixedMaterialPairSpanM': float(np.linalg.norm(b-a))})
    metrics.update(knownHealthySourceFaceWitnesses=witnesses, sourcePair49=config['pins']['sourcePair49'],
        pairedWallBeforeAfter=spans, globalRetainedContactWitness=minimum_row)
    write(out/'actual-tangent-and-pair.json', metrics)
    passed = below == 0 and boundary_minimum >= threshold
    report['anatomicalRegistration'].update(constructionContactSamplesPassed=passed,
        finalActualFullWearerMinimumM=minimum, deficientRetainedConstraintCount=below,
        fullRetainedConstraintVertices=len(used), fullRetainedConstraintCentroids=len(retained),
        contactQualificationStage='INDEPENDENT_SAVED_NATIVE_REOPEN',
        healthyRetainedBoundaryPassed=boundary_minimum >= threshold, sourceBoundaryMinimumM=boundary_minimum,
        boundaryDefinition='Saved retained fixed/changed frontier; if empty, complete retained domain minimum',
        boundaryVertices=len(boundary), maximumOriginalSourceDisplacementM=float(displacement.max()),
        sourceDisplacementPercentilesM=np.percentile(displacement, [0, 50, 90, 99, 100]).tolist(),
        changedSourceVertices=int(changed.sum()), newZeroAreaFromNondegenerateSource=metrics['newZeroAreaFromNondegenerateSource'])
    report['actualTangentAndPair'] = pin(out/'actual-tangent-and-pair.json')
    # Contact alone is not a dense triangle relation or moving appearance pass.
    report['geometryGatesPassed'] = False; report['movingReviewPassed'] = False
