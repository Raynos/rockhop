"""One cached-source check of corrected landmarks on both actual41 sides."""
import json
from pathlib import Path
import sys
import time

import numpy as np

from extract import ROOT, RECEIPT, checked, pin
from surface_landmarks02 import landmarks

HERE = Path(__file__).resolve().parent


def main(extraction_file, output):
    started = time.monotonic(); extraction_file = Path(extraction_file).resolve(); output = Path(output).resolve()
    assert not output.exists(); e = json.loads(extraction_file.read_text()); assert e['sourceReceipt'] == RECEIPT
    qualified = json.loads(checked(RECEIPT).read_text()); assert e['native'] == qualified['native']
    result = {'status': 'ACTUAL41_SURFACE_LANDMARK_SOURCE_CHECK_PENDING', 'acceptedArt': False,
        'recipe': pin(__file__), 'selector': pin(HERE/'surface_landmarks02.py'), 'frozenPriorSelector': pin(HERE/'construct.py'),
        'extraction': pin(extraction_file), 'sourceReceipt': RECEIPT, 'sides': {}, 'candidateAttempts': 0,
        'limits': 'Cached source landmarks only. No simplifier, native mutation, fit, budget or art acceptance.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    def write(): output.write_text(json.dumps(result, indent=2)+'\n')
    write()
    for side in ('L', 'R'):
        row = e['objects']['ActualSelectedGlove.'+side]
        with np.load(checked(row['arrays']), allow_pickle=False) as source:
            a = {key: source[key] for key in ('positions', 'triangles', 'fieldOffsets', 'fieldIndices', 'fieldWeights')}
        with np.load(checked(row['ancestry']), allow_pickle=False) as source:
            ancestry = {key: source[key] for key in ('authoredVertexRoles', 'authoredFaceRoles')}
        fields = np.zeros((len(a['positions']), len(row['groupNames'])), np.float32)
        fields[np.repeat(np.arange(len(fields)), np.diff(a['fieldOffsets'])), a['fieldIndices']] = a['fieldWeights']
        used = np.zeros(len(fields), bool); used[a['triangles'].ravel()] = True
        centers, records = landmarks(a['positions'], fields, row['groupNames'], used, e['rest'], side,
                                    a['triangles'], ancestry, qualified['hands'][side]['glove'])
        fans = np.isin(a['triangles'], centers).any(axis=1)
        result['sides'][side] = {'sourceArrays': row['arrays'], 'sourceAncestry': row['ancestry'],
            'centerOriginalVertexIds': centers.tolist(), 'centers': len(centers),
            'requiredSourceFanFaces': int(fans.sum()), 'requiredSourceFanVertices': len(np.unique(a['triangles'][fans])),
            'landmarks': records, 'sourceObject': 'ActualSelectedGlove.'+side}
        write()
    result.update(status='ACTUAL41_BILATERAL_SURFACE_LANDMARK_SOURCE_CHECK_PASSED_UNACCEPTED', elapsedSeconds=time.monotonic()-started)
    write()
    print(json.dumps({'status': result['status'], 'elapsedSeconds': result['elapsedSeconds'],
        'sides': {side: {k: r[k] for k in ('centers', 'requiredSourceFanFaces', 'requiredSourceFanVertices')} for side, r in result['sides'].items()}}, indent=2))


if __name__ == '__main__':
    assert len(sys.argv) == 3
    main(*sys.argv[1:])
