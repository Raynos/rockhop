"""Read-only first-solve witness for the exact frozen component47 intake.

Parent serial CPU2 guard only. No field, source geometry, target or tolerance
changes. Capture the real field28 fit locals before its first projection.
"""
import gc
import inspect
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
WRAPPER = {'path': 'assets/blender/rider-rebuild/selected-sleeve-component47/sleeve47.py',
           'sha256': 'a90e56476dffc95b1089a6d2af6df75e75fd3bfe10df173a9135d55014ea3b84'}
INPUT = {'path': 'assets/blender/rider-rebuild/selected-sleeve-component47/input01.json',
         'sha256': '7426ed1631f88fd4f6dc6c951ce10fb09d257c739add94f553243a8a3e2e6599'}
CANONICAL = {'path': 'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz',
             'sha256': 'e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2'}
io = runpy.run_path(str(HERE.parent/'selected-sleeve-tailoring27/checkpoint04.py'))
checked, pin = io['checked'], io['pin']


def capture_first_fit(helper, points, triangles, seeds, nearest, settings, progress):
    """Execute fit verbatim, replacing only its first solve with a capture/stop."""
    class Captured(Exception):
        pass
    captured = {}
    original = helper.Field.solve_planes

    def capture(field, embedding, normal, lower, iterations=256):
        caller = inspect.currentframe().f_back
        assert caller.f_code is helper.fit.__code__
        captured.update(caller.f_locals)
        assert captured['step'] == 0 and not field.values.any()
        captured.update(field=field, solveLower=lower, solveNormal=normal)
        raise Captured

    helper.Field.solve_planes = capture
    try:
        helper.fit(points, triangles, seeds, nearest, settings, progress)
    except Captured:
        pass
    finally:
        helper.Field.solve_planes = original
    assert captured, 'Exact fit never reached the first solve; failure changed'
    return captured


def deficit_masks(fit, np):
    ids, weights = fit['sample_embedding'][:2]
    active_ids = fit['field'].active[ids]
    norm = np.sum((weights*active_ids)**2, axis=1)
    current = np.sum(fit['field'].evaluate(fit['sample_embedding'])*fit['solveNormal'], axis=1)
    deficit = fit['solveLower']-current
    # Literal field28 line86 predicate, not a new numerical tolerance.
    bad = (norm == 0) & (deficit > 1e-8)
    return bad, norm, active_ids.sum(1), deficit


def diagnose(context):
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    c = context
    assert pin(c['config_path']) == INPUT
    assert c['config']['pins']['constructor47'] == WRAPPER
    fit = capture_first_fit(c['field_helper'], c['world'], c['faces'][c['retained']],
                            c['seeds'], c['actual_nearest'](c['bp'], c['bf']),
                            c['config']['field'], c['progress'])
    bad, norm, active_count, deficit = deficit_masks(fit, np)
    failing = np.flatnonzero(bad)
    assert len(failing), 'Frozen field boundary failure did not reproduce'
    retained_ids = np.flatnonzero(c['retained'])
    affected_ids = retained_ids[fit['face_ids']]
    unique = fit['unique']; nverts = len(unique)
    origin = (c['bp'].min(0)+c['bp'].max(0))*.5
    tree = BVHTree.FromPolygons([Vector(p) for p in c['bp']-origin], c['bf'].tolist(), all_triangles=True)
    canonical = np.load(checked(CANONICAL))
    canonical_vertices = canonical['vertices']; canonical_ids = canonical['nativeSourceVertexIds']
    canonical_face_sources = canonical_ids[canonical['faces']]
    canonical_faces = defaultdict(list)
    for i, ids in enumerate(canonical_face_sources):
        canonical_faces[tuple(sorted(map(int, ids)))].append(i)
    canonical_rows = {int(source): i for i, source in enumerate(canonical_ids)}
    prefix = 'RiderBody__FullAnatomyReference_'
    regions = c['reference'][prefix+'_REGION_ID']
    sources = c['reference'][prefix+'_SOURCE_VERTEX_ID']
    body_groups = {g.index: g.name for g in c['wearer'].vertex_groups}
    target = fit['target']
    nearest_cache = {}; cloth_cache = {}
    inner_faces = {}; inner_vertices = {}
    for side in ('L', 'R'):
        arrays = np.load(c['pin'](c['ownership']['hands'][side]['arrays']))
        inner_faces[side] = np.zeros(len(c['faces']), bool)
        inner_faces[side][arrays['innerSourceFaceIds']] = True
        inner_vertices[side] = np.zeros(len(c['world']), bool)
        inner_vertices[side][np.unique(c['faces'][inner_faces[side]])] = True

    def named_field(ids, body=False):
        result = defaultdict(float)
        for vertex in ids:
            if body:
                row = {g.group: g.weight for g in c['wearer'].data.vertices[int(vertex)].groups}
                names = body_groups
            else:
                row = c['surgery'].old_weights[int(vertex)]; names = c['groups']
            for group, weight in row.items(): result[names[group]] += weight/len(ids)
        return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))

    def detail(index):
        native = int(unique[index]) if index < nverts else None
        face = None if native is not None else int(affected_ids[index-nverts])
        cloth_ids = [native] if native is not None else list(map(int, c['faces'][face]))
        key = tuple(cloth_ids)
        if key not in cloth_cache: cloth_cache[key] = named_field(cloth_ids)
        cloth_weights = cloth_cache[key]
        point = fit['samples'][index]
        q, normal, tid, distance = tree.find_nearest(Vector(point-origin))
        assert tid is not None
        if tid not in nearest_cache:
            body_ids = c['bf'][tid]; source_ids = sources[body_ids]; region_ids = regions[body_ids]
            body_weights = named_field(body_ids, body=True)
            canon = canonical_faces.get(tuple(sorted(map(int, source_ids))), []) if np.all(region_ids == 1) else []
            exact = bool(canon) and all(int(s) in canonical_rows and
                np.array_equal(c['bp'][v], canonical_vertices[canonical_rows[int(s)]])
                for v, s in zip(body_ids, source_ids))
            nearest_cache[tid] = {'fullReferenceTriangleId': int(tid),
                'fullReferenceVertexIds': body_ids.tolist(), 'sourceVertexIds': source_ids.tolist(),
                'regionIds': region_ids.tolist(), 'namedSkinFieldMean': body_weights,
                'canonicalNative02TriangleIds': canon, 'canonicalCoordinatesExact': exact}
        body = nearest_cache[tid]
        inward = [side for side in ('L', 'R') if
                  (inner_vertices[side][native] if native is not None else inner_faces[side][face])]
        classification = {'kind': 'vertex' if native is not None else 'centroid',
            'support': ('movable' if norm[index] > 0 else
                        'zero_weight_active_ids' if active_count[index] else 'no_active_ids'),
            'clothDominantBone': next(iter(cloth_weights), '<unweighted>'),
            'bodyDominantBone': next(iter(body['namedSkinFieldMean']), '<unweighted>'),
            'bodyRegionIds': sorted(set(body['regionIds'])),
            'sourceInnerFaceOrIncidentVertexSides': inward,
            'anyOriginalArmSeed': bool(c['seeds'][cloth_ids].any())}
        return {'sampleIndex': int(index), 'classification': classification,
            'originalNativeVertexId': native, 'originalNativeFaceId': face,
            'clothVertices': cloth_ids, 'worldPoint': point.tolist(),
            'sourcePoints': c['source'][cloth_ids].tolist(),
            'signedFullReferenceGapM': float(fit['distance'][index]),
            'requiredDisplacementAlongNormalM': float(deficit[index]),
            'effectiveActiveWeightSquared': float(norm[index]), 'activeCornerIds': int(active_count[index]),
            'initialUnsafeVertices': (fit['gap'][cloth_ids] < target+c['config']['field']['contactReserveM']).tolist(),
            'namedClothSkinFieldMean': cloth_weights, 'nearestFullReference': body}

    classes = Counter(); details = []; per_class = Counter()
    # Smallest gaps first. Every failure contributes to exact class counts;
    # at most two rows per class and 64 total become readable witnesses.
    selected = set()
    for index in failing[np.argsort(fit['distance'][failing], kind='stable')]:
        row = detail(int(index)); key = json.dumps(row['classification'], sort_keys=True)
        classes[key] += 1
        if per_class[key] < 2 and len(details) < 64:
            details.append(row); selected.add(int(index)); per_class[key] += 1
    for row in details:
        vertex = row['originalNativeVertexId']
        if vertex is not None:
            incident = affected_ids[np.any(c['faces'][affected_ids] == vertex, axis=1)]
            row['incidentAffectedOriginalFaceCount'] = len(incident)
            row['incidentAffectedOriginalFaceIdsFirst16'] = incident[:16].tolist()
            row['originalVertexTouchedByAnyActiveId'] = bool(fit['touched'][vertex])
            removed = np.flatnonzero(~c['retained'] & np.any(c['faces'] == vertex, axis=1))
            row['scheduledRemovedIncidentFaceCount'] = len(removed)
    minimum_index = int(np.argmin(fit['distance']))
    minimum = detail(minimum_index)
    minimum['isFrozenDeficientSample'] = bool(bad[minimum_index])
    out = c['out']; out.mkdir(parents=True)
    np.savez_compressed(out/'frozen-deficient-samples.npz', sampleIndices=failing,
        signedGapsM=fit['distance'][failing], points=fit['samples'][failing],
        originalNativeVertexIds=np.where(failing < nverts, unique[np.minimum(failing, nverts-1)], -1),
        originalNativeFaceIds=np.where(failing >= nverts, affected_ids[np.maximum(failing-nverts, 0)], -1),
        activeCornerIdCounts=active_count[failing], effectiveActiveWeightsSquared=norm[failing])
    report = {'status': 'READ_ONLY_ACTUAL_FROZEN_SUPPORT_FAILURE_REPRODUCED', 'acceptedArt': False,
        'nativeGeometryChanged': False, 'nativeSaved': False, 'solverProjectionExecuted': False,
        'sourceInput': INPUT, 'sourceConstructor': WRAPPER, 'diagnosticRecipe': pin(__file__),
        'fullReference': c['config']['pins']['referenceSamples'], 'canonicalBody': CANONICAL,
        'fieldSettingsUnchanged': c['config']['field'], 'support': fit['support'],
        'totalConstraintSamples': len(fit['samples']), 'constraintVertices': nverts,
        'constraintCentroids': len(fit['centers']), 'affectedOriginalTriangles': len(affected_ids),
        'frozenDeficientSamples': len(failing),
        'frozenDeficientVertices': int(np.sum(failing < nverts)),
        'frozenDeficientCentroids': int(np.sum(failing >= nverts)),
        'frozenMinimumGapM': float(fit['distance'][failing].min()),
        'globalMinimum': minimum,
        'classifications': [{'classification': json.loads(k), 'count': v} for k, v in sorted(classes.items())],
        'boundedWitnesses': details, 'exactFailingArrays': pin(out/'frozen-deficient-samples.npz'),
        'scheduledRemovalExcludedFromConstraints': c['removed_constraint_counts'],
        'limits': ['Raw bone names and region IDs are measured labels, not semantic garment ownership.',
                   'Region1 canonical triangle ancestry is reported only with explicit coordinate equality.',
                   'Nearest-oriented-face sign is exactly the source method; global solid containment is not proven.',
                   'No ease, support expansion, cloth strain, self intersection or moving-art acceptance follows.']}
    (out/'diagnostic.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'diagnostic': pin(out/'diagnostic.json'),
                      'frozenDeficientSamples': len(failing), 'nativeGeometryChanged': False}), flush=True)


def transformed_source():
    wrapper = runpy.run_path(str(checked(WRAPPER)))
    source = wrapper['transformed_source']()
    marker = '    moved, changed, field, fit_report = field_helper.fit('
    assert source.count(marker) == 1
    source = source[:source.index(marker)]+'    diagnose({**globals(), **locals()})\n'
    old = "ROOT/'harness/out/rider-rebuild/selected-sleeve-component47'"
    assert source.count(old) == 1
    source = source.replace(old, "ROOT/'harness/out/rider-rebuild/selected-sleeve-support49'")
    return wrapper, source


if __name__ == '__main__':
    checked(INPUT); checked(CANONICAL)
    wrapper, source = transformed_source()
    namespace = {'__name__': 'sleeve49_read_only_capture', '__file__': str(checked(wrapper['ORIGINAL'])),
        'helper47': wrapper['helper47'], 'ORIGINAL': wrapper['ORIGINAL'], 'WRAPPER': str(checked(WRAPPER)),
        'gc': gc, 'diagnose': diagnose}
    exec(compile(source, namespace['__file__'], 'exec'), namespace)
    namespace['main']()
