"""All fixed controls through every cage step; transport waits for native gate."""
import json
import runpy
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
H = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit64/component.py'))
C = runpy.run_path(str(HERE/'cage.py'))
CONTROLS = {'path': 'docs/evidence/rider-rebuild/selected-anatomical-hoodie-fit65/cage64-diagnosis.npz',
    'sha256': '4f22dc3ff6e587fbbeca3aa1906e550cc466b71004bafc83d657267edf189c38'}


def main():
    started = time.monotonic(); out = Path(sys.argv[1]).resolve(); assert not out.exists()
    arrays = np.load(H['checked'](CONTROLS)); source, target = arrays['sourceControls'], arrays['targetControls']
    original = np.load(H['checked'](H['REFERENCE']['original47Arrays']))['points'].astype(float)
    bounds = np.vstack((original.min(0), original.max(0)))
    config = H['read'](H['SOURCE47']); events = []
    def progress(row):
        events.append(row)
        print(row, flush=True)
    result = {'acceptedArt': False, 'nativeExecuted': False, 'fullOriginalVertexTransportExecuted': False,
        'sourceRecipe': H['pin'](__file__), 'cageRecipe': H['pin'](HERE/'cage.py'), 'controlArrays': CONTROLS,
        'scope': 'All656 fixed source/target constraints and exact fullsource bounds, every continuation step and global certificate. Only two bounds are transported after convergence.'}
    try:
        moved, jac, maps, report = C['fixed_targets'](bounds, source, target,
            config['field']['fieldCellM'], config['field']['maximumDerivativeBound'], progress)
        result.update(passed=True, report=report)
    except Exception as error:
        result.update(passed=False, exceptionType=type(error).__name__, error=str(error))
    result.update(elapsedSeconds=time.monotonic()-started, progress=events)
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'report': H['pin'](out), 'passed': result['passed'], 'elapsedSeconds': result['elapsedSeconds'], 'error': result.get('error')}))


if __name__ == '__main__': main()
