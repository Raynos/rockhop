"""Bounded CPU33-station replay of the exact recorded58 right torso branch."""
import json
import runpy
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
D = runpy.run_path(str(HERE/'diagnose58.py'))
M = runpy.run_path(str(HERE/'meridian.py'))


def main():
    started = time.monotonic(); output = Path(sys.argv[1]).resolve(); assert not output.exists()
    raw, xyz, faces, frames, original, broad, body, cloth, body_pin = D['intake']()
    failure_path = D['H']['ROOT']/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit58/component01/construction-failure.json'
    failure = json.loads(failure_path.read_text()); c = failure['targetContext']
    precision = float(np.spacing(np.float32(max(abs(body.points).max(), 1.))))
    nodes, branches, record = D['S']['underarm'](xyz, faces, c['sourceDepth'], c['side'], frames)
    rows = D['S']['sample_path'](nodes, branches[c['role']], (original, broad), faces, 9)
    pairs, ties = [], []
    for row in rows:
        choices = D['variants'](row, cloth, broad, precision)
        # Mesh-native face order deterministically selects the first adjacent
        # normal, including182492 independently matching the recorded failure.
        pairs.append(choices[0]); ties.append([p[2]['sourceNormalFace'] for p in choices])
    apex, end = np.asarray(c['fixedApexPair']), np.asarray(c['healthy50EndpointPair'])
    #58 recorded this exact original-apex offset after translation. Retain it.
    pairs[0] = (apex, apex, {'offsetsFromExactRecordedApex': True})
    meridian = M['Meridian'](M['Axis'](c['canonicalAxisControlPoints']), apex, end, body,
        body.nearest, .0026, precision, {k: c[k] for k in ('side', 'sourceDepth', 'role')})
    stations = []
    for t in np.linspace(0, 1, 33):
        k = min(len(pairs)-2, int(t*(len(pairs)-1))); alpha = t*(len(pairs)-1)-k
        a, b = pairs[k][0], pairs[k+1][0]
        offset = ((a-a.mean(0))*(1-alpha)+(b-b.mean(0))*alpha)*(1-M['smooth'](t))+(end-end.mean(0))*M['smooth'](t)
        try:
            target = meridian.at(float(t), offset)
            stations.append({'parameter': float(t), 'passed': True, 'actualMinimumM': float(body.nearest(target)[0].min()),
                'targetPair': target.tolist(), 'intervals': meridian.last if 0 < t < 1 else None})
        except AssertionError as error:
            stations.append({'parameter': float(t), 'passed': False, 'context': meridian.last, 'error': str(error)})
    result = {'acceptedArt': False, 'cpuOnly': True, 'native58OffsetsWereNotRecorded': True,
        'sourceRecipe': D['H']['pin'](__file__), 'intervalRecipe': D['H']['pin'](HERE/'intervals.py'),
        'meridianRecipe': D['H']['pin'](HERE/'meridian.py'), 'diagnosticRecipe': D['H']['pin'](HERE/'diagnose58.py'),
        'actual58Failure': D['H']['pin'](failure_path), 'sourcePins': {**{k: D['H']['REFERENCE'][k] for k in ('original47Arrays', 'broad50Arrays')}, 'body': body_pin},
        'wallNormalCandidates': ties, 'chosenWallAncestry': [p[2] for p in pairs],
        'exactRecordedApexAndEndpointUsed': True, 'all33Passed': all(r['passed'] for r in stations),
        'elapsedSeconds': time.monotonic()-started, 'stations': stations}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': D['H']['pin'](output), 'all33Passed': result['all33Passed'], 'elapsedSeconds': result['elapsedSeconds'],
        'failed': [{'parameter': s['parameter'], 'context': s['context']} for s in stations if not s['passed']]}))


if __name__ == '__main__': main()
