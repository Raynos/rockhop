"""All656 preserved actual-source CPU controls: normal vs direct equations.

Native64 did not save its target arrays. This reconstruction is explicitly the
pinned60 full CPU target preflight, never represented as exact native64 targets.
"""
import json
import runpy
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
H = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit64/component.py'))
C = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit64/cage.py'))


def controls():
    reference = H['REFERENCE']['allBranchesCPU60']; report = H['read'](reference)['targetReport']
    original = np.load(H['checked'](H['REFERENCE']['original47Arrays']))['points'].astype(float)
    broad = np.load(H['checked'](H['REFERENCE']['broad50Arrays']))['points'].astype(float)
    source, target, labels = [], [], []
    for section in report['sourceMeridians']:
        source.extend(section['actualOriginalApexPair']); target.extend(section['targetApexPair'])
        prefix = {'side': section['side'], 'depth': section['sourceDepth']}
        labels.extend([{**prefix, 'role': 'apex', 'wall': wall} for wall in (0, 1)])
        for role, branch in section['branches'].items():
            for row in branch['controls']:
                source.extend(row['sourcePair']); target.extend(row['targetPair'])
                labels.extend([{**prefix, 'role': role, 'fraction': row['materialFraction'], 'wall': wall} for wall in (0, 1)])
    anchors = report['healthy50OriginalNativeAnchorIds']
    source.extend(original[anchors]); target.extend(broad[anchors]); labels.extend([{'originalNativeAnchor': v} for v in anchors])
    return original, np.asarray(source), np.asarray(target), labels, reference


def system(original, current, targets, spacing):
    cage = C['Cage'](np.vstack((original.min(0), original.max(0), current, targets)), spacing)
    ids, weights, _ = cage.embed(current); unique, inverse = np.unique(ids, return_inverse=True)
    matrix = np.zeros((len(current), len(unique)))
    np.add.at(matrix, (np.repeat(np.arange(len(current)), 64), inverse.ravel()), weights.ravel())
    return cage, unique, matrix


def main():
    started = time.monotonic(); out = Path(sys.argv[1]).resolve(); assert not out.exists()
    original, source, target, labels, reference = controls()
    config = H['read'](H['SOURCE47']); spacing = config['field']['fieldCellM']
    precision = float(np.spacing(np.float32(max(abs(target).max(), 1.))))
    unique_source, inverse, counts = np.unique(source, axis=0, return_inverse=True, return_counts=True)
    duplicates = []
    for i in np.flatnonzero(counts > 1):
        rows = np.flatnonzero(inverse == i)
        duplicates.append({'rows': rows.tolist(), 'exactSameTargets': bool(np.all(target[rows] == target[rows[0]])),
            'targetDiameterM': float(np.linalg.norm(target[rows]-target[rows[0]], axis=1).max()), 'labels': [labels[j] for j in rows]})
    cage, columns, matrix = system(original, source, target, spacing); residual = target-source
    gram = matrix@matrix.T
    old, _, old_rank, old_singular = np.linalg.lstsq(gram, residual, rcond=None)
    old_error = np.linalg.norm(matrix@(matrix.T@old)-residual, axis=1)
    coefficients, _, rank, singular = np.linalg.lstsq(matrix, residual, rcond=None)
    direct_error = np.linalg.norm(matrix@coefficients-residual, axis=1)
    worst = int(np.argmax(direct_error))
    result = {'acceptedArt': False, 'nativeExecuted': False, 'sourceRecipe': H['pin'](__file__),
        'sourceTargetProvenance': reference, 'actualNative64TargetArraysAvailable': False,
        'sourceOriginal47': H['REFERENCE']['original47Arrays'], 'broad50': H['REFERENCE']['broad50Arrays'],
        'sourceControlCount': len(source), 'uniqueSourceCount': len(unique_source), 'exactDuplicateGroups': duplicates,
        'cellM': spacing, 'matrixShape': list(matrix.shape), 'nativeCoordinatePrecisionM': precision,
        'normalEquations': {'rank': int(old_rank), 'defaultCutoff': float(np.finfo(float).eps*max(gram.shape)*old_singular[0]),
            'maxResidualM': float(old_error.max())},
        'directEquations': {'rank': int(rank), 'defaultCutoff': float(np.finfo(float).eps*max(matrix.shape)*singular[0]),
            'maximumSingularValue': float(singular[0]), 'minimumSingularValue': float(singular[-1]),
            'minimumRetainedSingularValue': float(singular[rank-1]), 'maxResidualM': float(direct_error.max()),
            'worstControl': labels[worst], 'passesNativePrecision': bool(direct_error.max() <= precision)},
        'singularValues': singular.tolist(), 'elapsedSeconds': time.monotonic()-started}
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2)+'\n')
    arrays = out.with_suffix('.npz'); assert not arrays.exists()
    np.savez_compressed(arrays, sourceControls=source, targetControls=target, sourceLabelsJSON=np.array(json.dumps(labels)))
    print(json.dumps({k: result[k] for k in ('sourceControlCount', 'uniqueSourceCount', 'exactDuplicateGroups', 'matrixShape', 'normalEquations', 'directEquations', 'elapsedSeconds')}))
    print(json.dumps({'report': H['pin'](out), 'controlArrays': H['pin'](arrays)}))


if __name__ == '__main__': main()
