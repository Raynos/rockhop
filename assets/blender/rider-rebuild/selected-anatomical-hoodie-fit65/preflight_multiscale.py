"""Complete65 solve with frozen full CPU target ancestry, before native launch."""
import json
import runpy
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
D = runpy.run_path(str(HERE/'diagnose_cage.py'))
M = runpy.run_path(str(HERE/'multiscale.py'))


def main():
    started = time.monotonic(); output = Path(sys.argv[1]).resolve(); assert not output.exists()
    original, source, target, labels, provenance = D['controls']()
    pairs = np.array([i for i, row in enumerate(labels) if row.get('wall') == 0])
    fine = float(np.linalg.norm(source[pairs]-source[pairs+1], axis=1).min())
    # Exact original bounding box; no full clothing transport during CPU solve.
    bounds = np.vstack((original.min(0), original.max(0))); progress = []
    def log(row): progress.append(row); print(row, flush=True)
    moved, jac, maps, report = M['fixed_targets'](bounds, source, target, .04, .85, log, fine)
    replay = source.copy()
    for field in maps: replay, _ = field.evaluate(replay)
    residual = float(np.linalg.norm(replay-target, axis=1).max())
    assert residual == report['maximumEndpointResidualM']
    assert all(r['linearSystem']['constraintRank'] == len(source) for r in report['steps'])
    assert all(r['certificate']['globalDisplacementLipschitzUpperBound'] <= .85 for r in report['steps'])
    arrays = D['H']['ROOT']/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit65/cpu-solver01/sparse-maps.npz'
    assert not arrays.exists(); arrays.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(arrays, **M['map_arrays'](maps), sourceControls=source, targetControls=target)
    restored = M['restore_maps'](np.load(arrays)); test = source.copy()
    for field in restored: test, _ = field.evaluate(test)
    assert np.array_equal(test, replay)
    delta = target-source
    distances = np.linalg.norm(source[:, None]-source[None, :], axis=2)
    changes = np.linalg.norm(delta[:, None]-delta[None, :], axis=2)
    np.fill_diagonal(distances, np.inf); ratios = changes/distances
    i, j = np.unravel_index(np.argmax(ratios), ratios.shape)
    result = {'acceptedArt': False, 'passed': True, 'nativeExecuted': False,
        'fullOriginalVertexTransportExecuted': False, 'sourceRecipe': D['H']['pin'](__file__),
        'registrationRecipe': D['H']['pin'](HERE/'multiscale.py'), 'sourceTargetProvenance': provenance,
        'savedMapsAndControls': D['H']['pin'](arrays), 'sourceControlCount': len(source),
        'actualNative64TargetArraysAvailable': False,
        'fineSpacingM': fine, 'fineSpacingDerivation': 'Minimum actual original paired source wall span across all fixed material controls',
        'fixedEndpointReport': report, 'serializedReplayExact': True,
        'allPairDisplacementLipschitzLowerBound': float(ratios[i, j]),
        'lowerBoundWitness': {'sourceDistanceM': float(distances[i, j]), 'labels': [labels[i], labels[j]]},
        'elapsedSeconds': time.monotonic()-started, 'progress': progress}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': D['H']['pin'](output), 'passed': True, 'maps': len(maps),
        'endpointResidualM': residual, 'elapsedSeconds': result['elapsedSeconds'],
        'allPairDisplacementLipschitzLowerBound': result['allPairDisplacementLipschitzLowerBound']}))


if __name__ == '__main__': main()
