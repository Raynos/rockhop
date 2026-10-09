"""Measure one actual-wearer skin map on every complete garment edge.

All 482 existing game matrices are replayed as CPU linear skinning.  This is
deformation evidence, not native/GPU parity, finite contact or an art pass.
"""
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
A = runpy.run_path(str(HERE / 'author.py'))
ROOT = A['ROOT']; pin = A['pin']; checked = A['checked']
GAME = {'path': 'harness/out/rider-rebuild/selected-authoring-motion11/gameplay-converted02/measured-gameplay-native-world.json',
        'sha256': 'f3e0444768655bf72500a9245745a559586a7717b3f6cb6b600b6e9d1d05c153'}


def main(receipt_path, output):
    receipt_path = Path(receipt_path).resolve(); output = Path(output).resolve()
    assert output.is_relative_to(ROOT / 'harness/out/rider-rebuild/selected-hoodie-joints77') and not output.exists()
    receipt = json.loads(receipt_path.read_text())
    assert receipt['wearerFieldBinding']['recipe'] == pin(HERE / 'wearer_fields.py')
    R = runpy.run_path(str(checked(receipt['wearerFieldBinding']['recipe'])))
    R['verify'](receipt_path)
    a = np.load(checked(receipt['receiver'])); p = a['positions']
    G = runpy.run_path(str(checked({'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/field_repair.py', 'sha256': 'ce027c64927dfb571bf8c1b1edb5502b619daf9749f78af8ae845a68b14f26e4'})))
    edges, length, _ = G['graph'](a)
    affected = np.ones(len(edges), dtype=bool)
    edges = edges[affected]; length = length[affected]
    game = json.loads(checked(GAME).read_text()); names = game['boneNames']
    rest = {b['name']: b for b in game['nativeRest']['bones']}
    inv = np.linalg.inv(np.asarray([rest[n]['matrix'] for n in names]))
    group_index = [names.index(str(n)) for n in a['groupNames']]
    before = np.zeros((len(p), len(names))); after = before.copy()
    before[:, group_index] = a['priorNamedFields']; after[:, group_index] = a['namedFields']
    active = np.flatnonzero(np.maximum(before, after).max(0) > 0)
    rows = []

    def endpoint_record(index, posed):
        ids = edges[index]
        return {'ids': ids.tolist(), 'roles': a['vertexRoles'][ids].tolist(),
                'restLengthM': float(length[index]),
                'posedLengthM': float(np.linalg.norm(posed[ids[1]] - posed[ids[0]])),
                'restPositions': p[ids].tolist(), 'posedPositions': posed[ids].tolist(),
                'namedFields': [{str(n): float(w) for n, w in zip(a['groupNames'], a['namedFields'][i])}
                                for i in ids]}

    for action in game['actions']:
        for fi, world in enumerate(np.asarray(action['nativeWorldMatrices'])):
            matrices = world @ inv; previous = np.zeros_like(p); posed = previous.copy()
            for j in active:
                q = p @ matrices[j, :3, :3].T + matrices[j, :3, 3]
                previous += q * before[:, j, None]; posed += q * after[:, j, None]
            ratio = np.linalg.norm(posed[edges[:, 1]] - posed[edges[:, 0]], axis=1) / length
            old_ratio = np.linalg.norm(previous[edges[:, 1]] - previous[edges[:, 0]], axis=1) / length
            largest = int(np.argmax(ratio)); smallest = int(np.argmin(ratio))
            rows.append({'action': action['name'], 'bike': action['bike'], 'frame': fi + 1,
                         'maximumRatio': float(ratio[largest]), 'minimumRatio': float(ratio[smallest]),
                         'ratioPercentiles': np.percentile(ratio, [0, 1, 5, 50, 95, 99, 100]).tolist(),
                         'priorMaximumRatio': float(old_ratio.max()), 'priorMinimumRatio': float(old_ratio.min()),
                         'maximumEdge': endpoint_record(largest, posed),
                         'minimumEdge': endpoint_record(smallest, posed),
                         'maximumPoseChangeM': float(np.linalg.norm(posed - previous, axis=1).max())})
    output.mkdir(parents=True)
    report = {'status': 'AUTHORED77_ACTUAL_WEARER_FIELDS_ALL482_MEASURED_UNACCEPTED',
              'acceptedArt': False, 'recipe': pin(__file__), 'receiverReceipt': pin(receipt_path),
              'gameplayMatrices': GAME, 'affectedEdges': len(edges), 'keys': len(rows),
              'maximum': max(rows, key=lambda r: r['maximumRatio']),
              'minimum': min(rows, key=lambda r: r['minimumRatio']), 'frames': rows,
              'supportCountHistogram': {str(k): int(v) for k, v in zip(*np.unique((a['namedFields'] > 0).sum(1), return_counts=True))},
              'limits': 'Every edge in the complete receiver, including retained source torso/hood/hem. Exact full fields, CPU linear skin only. No finite contact, self-intersection, production-four parity or played art pass.'}
    (output / 'field-inspection.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'keys', 'affectedEdges', 'maximum', 'minimum', 'supportCountHistogram')}, indent=2))


if __name__ == '__main__': main(*sys.argv[1:])
