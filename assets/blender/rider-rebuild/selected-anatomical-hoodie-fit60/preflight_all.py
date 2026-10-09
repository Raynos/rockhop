"""Actual selected target-stage CPU preflight; no cage or Blender execution."""
import json
import runpy
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
D = runpy.run_path(str(HERE/'diagnose58.py'))
T = runpy.run_path(str(HERE/'targets.py'))
CANONICAL = {'path': 'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz',
    'sha256': 'e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2'}


def main():
    started = time.monotonic(); output = Path(sys.argv[1]).resolve(); assert not output.exists()
    raw, xyz, faces, frames, original, broad, body, cloth, body_pin = D['intake']()
    canonical = np.load(D['H']['checked'](CANONICAL))
    bones = {str(name): {'head': head.tolist(), 'tail': tail.tolist()}
        for name, head, tail in zip(canonical['jointNames'], canonical['jointHeads'], canonical['jointTails'])}
    precision = float(np.spacing(np.float32(max(abs(body.points).max(), 1.))))
    pair_log = []
    def pair(row):
        candidates = D['variants'](row, cloth, broad, precision)
        # Exact CPU nearest face determines the normal, with adjacent ties
        # logged. This is not a claim about an unobserved native BVH tie.
        _, closest = cloth.nearest(row['points'][0][None])
        selected = next((p for p in candidates if p[2]['sourceNormalFace'] == int(closest[0])), candidates[0])
        pair_log.append({'fraction': row['fraction'], 'sourceNormalFace': selected[2]['sourceNormalFace'],
            'candidateNormalFaces': [p[2]['sourceNormalFace'] for p in candidates]})
        return selected
    config = D['H']['read'](D['H']['SOURCE47'])
    context = {'controls': frames, 'source': raw, 'bp': body.points, 'bf': body.faces,
        'config': config, 'failureContext': {}}
    result = {'acceptedArt': False, 'cpuOnly': True, 'nativeOrCageExecuted': False,
        'sourceRecipe': D['H']['pin'](__file__), 'targetRecipe': D['H']['pin'](HERE/'targets.py'),
        'intervalRecipe': D['H']['pin'](HERE/'intervals.py'), 'meridianRecipe': D['H']['pin'](HERE/'meridian.py'),
        'diagnosisRecipe': D['H']['pin'](HERE/'diagnose58.py'), 'canonical': CANONICAL,
        'sourcePins': {**{k: D['H']['REFERENCE'][k] for k in ('original47Arrays', 'broad50Arrays')}, 'body': body_pin}}
    try:
        source, target, report = T['make'](context, original, broad, faces, body.nearest,
            config['field']['clothClearanceM']+config['field']['contactSolveMarginM'], pair, bones)
        result.update(passed=True, sourceControlCount=len(source), targetReport=report)
    except Exception as error:
        result.update(passed=False, failureContext=context['failureContext'], exceptionType=type(error).__name__, error=str(error))
    result.update(elapsedSeconds=time.monotonic()-started, wallPairNormalProvenance=pair_log)
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': D['H']['pin'](output), 'passed': result['passed'], 'elapsedSeconds': result['elapsedSeconds'],
        'sourceControlCount': result.get('sourceControlCount'), 'failureContext': result.get('failureContext')}))


if __name__ == '__main__': main()
