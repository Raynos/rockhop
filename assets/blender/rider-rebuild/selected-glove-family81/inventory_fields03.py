"""One admitted bilateral cache inventory. No native access or simplification."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import numpy as np

from extract import ROOT, BASE, RECEIPT, checked, pin
from left_normals import source_fan

HERE = Path(__file__).resolve().parent
EVIDENCE = ROOT/'docs/evidence/rider-rebuild/selected-glove-family81'
CPU = {'path': 'harness/out/rider-rebuild/selected-glove-family81/extract01/cpu-check.json',
       'sha256': '4c593323090894014d301b5a6835b9f0f916cc95b6a6168d46203bc03550bf60'}
PROOF = {'path': 'docs/evidence/rider-rebuild/selected-glove-family81/surface-landmarks02.json',
         'sha256': '8d82e318265c4798fad634902f8f67af3c4818c276595fb2420094647caef0f1'}
HELPERS = [
    {'path': 'assets/blender/rider-rebuild/selected-production-constructor37/construct.mjs', 'sha256': '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741'},
    {'path': 'assets/blender/rider-rebuild/selected-boot-fan59/construct.mjs', 'sha256': 'ff1328930687d5eb8e7b1c0e7f5961e2fac11f911e88d0e4224fa5e37f1c571f'},
    {'path': 'assets/blender/rider-rebuild/selected-boot-closure62/closure.mjs', 'sha256': '89cb51a5d9587a0c6726ab65d7678b9e0072756d16973dab3263e96e849ce294'}]
PERCENTILES = [0, 1, 5, 50, 95, 99, 100]


def distribution(values, ids):
    x = values[ids].astype(np.float64)
    if not len(ids): return {'count': 0}
    return {'count': len(ids), 'min': float(x.min()), 'max': float(x.max()),
            'percentiles': dict(zip(map(str, PERCENTILES), np.percentile(x, PERCENTILES).tolist())),
            'maximumAbsoluteDeviationFrom1': float(abs(x-1).max()),
            'minimumVertexId': int(ids[x.argmin()]), 'maximumVertexId': int(ids[x.argmax()]),
            'notExactly1': int((x != 1).sum()), 'nonpositive': int((x <= 0).sum())}


def main():
    started = time.monotonic()
    assert os.environ.get('OPENBLAS_NUM_THREADS') == '2' and os.environ.get('OMP_NUM_THREADS') == '2'
    output = EVIDENCE/'source-field-inventory03.json'; arrays_file = EVIDENCE/'source-field-inventory03.npz'
    assert not output.exists() and not arrays_file.exists()
    cpu = json.loads(checked(CPU).read_text()); e = json.loads(checked(cpu['extraction']).read_text())
    assert cpu['status'] == 'INDEPENDENT_CPU_ACTUAL41_CACHE_IDENTITY_PASSED_UNACCEPTED'
    q = json.loads(checked(RECEIPT).read_text()); proof = json.loads(checked(PROOF).read_text())
    assert e['sourceReceipt'] == RECEIPT and e['native'] == q['native'] and proof['extraction'] == cpu['extraction']
    for h in HELPERS: checked(h)
    frozen = [pin(HERE/n) for n in ('extract.py', 'check.py', 'construct.py', 'construct.mjs',
        'construct_left.py', 'construct_left.mjs', 'surface_landmarks02.py', 'left_normals.py',
        'construct_surface02.py', 'construct_surface02.mjs', 'construct_left_surface02.py', 'construct_left_surface02.mjs')]
    bones = {b['name']: b for b in e['sourceWitness']['rig']['bones']}; sides = {}; durable = {}
    for side in ('L', 'R'):
        name = 'ActualSelectedGlove.'+side; row = e['objects'][name]
        with np.load(checked(row['arrays']), allow_pickle=False) as a, np.load(checked(row['ancestry']), allow_pickle=False) as ancestry:
            names = row['groupNames']; p = a['positions']; tri = a['triangles']; n = len(p)
            offsets = a['fieldOffsets']; groups = a['fieldIndices']; weights = a['fieldWeights']
            counts = np.diff(offsets); ids = np.arange(n); used = np.zeros(n, bool); used[tri.ravel()] = True
            fields = np.zeros((n, len(names)), np.float32)
            fields[np.repeat(ids, counts), groups] = weights
            # Exact JS order: float64 += each float32 named field in schema order; cast once for Math.fround.
            sums = np.zeros(n, np.float64)
            for column in fields.T: sums += column
            rounded = sums.astype(np.float32); supports = (fields > 0).sum(1)
            prefix = ids < q['objects'][name]['sourceVertexCount']; roles = ancestry['authoredVertexRoles']
            populations = {'all': ids, 'referenced': ids[used], 'unreferenced': ids[~used],
                           'referencedSourcePrefix': ids[used & prefix], 'referencedConstructed': ids[used & ~prefix]}
            populations.update({f'referencedRole{role}': ids[used & (roles == role)] for role in np.unique(roles)})
            distributions = {key: {'sumFloat64': distribution(sums, ii), 'sumMathFround': distribution(rounded, ii),
                'supportHistogram': {str(k): int(v) for k, v in zip(*np.unique(supports[ii], return_counts=True))}}
                for key, ii in populations.items()}
            bad = ids[used & (rounded != 1)]; worst = ids[used][np.argsort(-abs(sums[used]-1), kind='stable')[:8]]
            def field_row(v):
                sl = slice(offsets[v], offsets[v+1]); parent = ancestry['vertexParentSourceIds'][v]
                return {'originalVertexId': int(v), 'sourcePrefix': bool(prefix[v]), 'authoredRole': int(roles[v]),
                    'sumFloat64': float(sums[v]), 'sumMathFround': float(rounded[v]), 'positionM': p[v].tolist(),
                    'namedRawMemberships': [[names[g], float(w)] for g, w in zip(groups[sl], weights[sl])],
                    'parentSourceIds': parent.tolist(), 'parentCoefficients': ancestry['vertexParentCoefficients'][v].tolist()}
            low = fields[used].min(0); high = fields[used].max(0); varying = np.flatnonzero(low != high)
            normal_lengths = np.linalg.norm(a['vertexNormals'].astype(np.float64), axis=1)
            zero_normals = ids[used & (normal_lengths == 0)]
            corners = a['cornerNormals']; triangle_points = p[tri].astype(np.float64)
            area2 = np.linalg.norm(np.cross(triangle_points[:, 1]-triangle_points[:, 0], triangle_points[:, 2]-triangle_points[:, 0]), axis=1)
            active_names = [names[j] for j in np.flatnonzero(high > 0)]
            centers = list(proof['sides'][side]['centerOriginalVertexIds'])
            singular = None
            if side == 'L':
                singular = source_fan(a); centers = sorted(set(centers) | {320543})
            # Temporary source views feed the unchanged topology functions; no candidate is made.
            with tempfile.TemporaryDirectory(prefix='field-inventory03-', dir=BASE) as temp:
                temp = Path(temp); binary = temp/'source.bin'; layout = {}
                arrays = {'positions': p, 'triangles': tri, 'loopIds': a['triangleLoopIds'], 'normals': a['vertexNormals'],
                          'cornerNormals': corners, 'fields': fields, 'materials': a['faceMaterialIds']}
                arrays.update({f'uv{i}': a[f'uvLayer{i}'] for i in range(len(row['uvLayerNames']))})
                with binary.open('xb') as stream:
                    for key, value in arrays.items():
                        layout[key] = {'dtype': value.dtype.str, 'byteOffset': stream.tell(), 'count': value.size}
                        stream.write(value.tobytes())
                manifest = temp/'input.json'; manifest.write_text(json.dumps({'binary': str(binary), 'layout': layout,
                    'names': names, 'uv': row['uvLayerNames'], 'centers': centers, 'helpers': HELPERS}))
                run = subprocess.run(['node', str(HERE/'inventory_topology03.mjs'), str(manifest)], check=True, capture_output=True, text=True, cwd=ROOT)
                topology = json.loads(run.stdout)
            normalized = np.divide(fields, sums[:, None], out=np.zeros(fields.shape, np.float64), where=sums[:, None] > 0)
            finite = {key: bool(np.isfinite(a[key]).all()) for key in a.files}
            sides[side] = {'sourceArrays': row['arrays'], 'sourceAncestry': row['ancestry'], 'sourceGeometry': row['geometry'],
                'sourceVertices': n, 'sourceTriangles': len(tri), 'groupNames': names, 'memberships': len(weights),
                'sourceArrayFinite': finite, 'individualWeightsInZeroOne': bool(((weights >= 0) & (weights <= 1)).all()),
                'maximumStoredMemberships': int(counts.max()), 'maximumNonzeroSupports': int(supports.max()),
                'distributions': distributions, 'referencedNotFloat32NormalizedVertexIds': bad.tolist(),
                'worstReferencedRawRows': [field_row(v) for v in worst],
                'varyingFieldNames': [names[i] for i in varying], 'metricChannels': len(varying)+3, 'metricChannelLimit32Passed': bool(len(varying)+3 <= 32),
                'activeNamedFieldsAllMapToDeformingBones': all(bones[n]['useDeform'] for n in active_names),
                'modifierWitness': e['sourceWitness']['sources'][name]['modifiers'],
                'sourceReferencedVertexNormalLengthRange': [float(normal_lengths[used].min()), float(normal_lengths[used].max())],
                'referencedZeroVertexNormalIds': zero_normals.tolist(), 'zeroCornerNormalIds': np.flatnonzero(np.linalg.norm(corners, axis=1) == 0).tolist(),
                'sourceGeometricDoubleAreaRangeM2': [float(area2.min()), float(area2.max())],
                'sourceZeroAreaFaceIds': np.flatnonzero(area2 == 0).tolist(), 'leftSingularFan': singular,
                'normalizedFullFieldMetricOnly': {'maximumAbsoluteChannelDifferenceFromRaw': float(abs(normalized[used]-fields[used]).max()),
                    'maximumL1DifferenceFromRaw': float(abs(normalized[used]-fields[used]).sum(1).max()),
                    'maximumRowSumErrorFloat64': float(abs(normalized[used].sum(1)-1).max()),
                    'storedFieldsChanged': False, 'nativeOrExportEvaluated': False},
                'originalTopologyPreconditions': topology}
            durable.update({side+'_sumFloat64': sums, side+'_sumMathFround': rounded, side+'_referenced': used,
                side+'_supportCounts': supports, side+'_membershipCounts': counts, side+'_authoredRoles': roles,
                side+'_notFloat32NormalizedReferencedIds': bad})
            checked(row['arrays']); checked(row['ancestry'])
    for row in frozen: checked(row)
    np.savez_compressed(arrays_file, **durable)
    report = {'status': 'ACTUAL41_BILATERAL_SOURCE_PRECONDITION_INVENTORY_ONLY', 'acceptedArt': False,
        'recipe': pin(__file__), 'topologyRecipe': pin(HERE/'inventory_topology03.mjs'), 'helpers': HELPERS,
        'cpuAdmission': CPU, 'extraction': cpu['extraction'], 'sourceReceipt': RECEIPT, 'native': e['native'],
        'surfaceProof': PROOF, 'sides': sides, 'perOriginalVertexStatistics': pin(arrays_file),
        'frozenRecipesUnchanged': frozen, 'candidateAttempts': 0, 'nativeMutation': False,
        'simplifierInvoked': False, 'elapsedSeconds': time.monotonic()-started,
        'limits': 'Source preconditions only. Candidate allocation, normal orientation, surface, full skin fidelity, bake, fit and motion are not evaluated.'}
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'report': pin(output), 'elapsedSeconds': report['elapsedSeconds'], 'sides': {
        s: {'referenced': r['distributions']['referenced'], 'metricChannels': r['metricChannels'],
            'topology': r['originalTopologyPreconditions']} for s, r in sides.items()}}, indent=2))


if __name__ == '__main__': main()
