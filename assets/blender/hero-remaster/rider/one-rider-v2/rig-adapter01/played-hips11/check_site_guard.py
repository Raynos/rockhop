"""Bounded native renderer batch. Invoke only under the canonical lockf lock."""
from pathlib import Path
import json
import os
import signal
import subprocess
import time

repo = Path('/Users/raynos/projects/games/rockhop')
out = repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-hips11/framed02/site-check'
out.mkdir(parents=True, exist_ok=True)
def anonymous():
    vm = subprocess.check_output(['vm_stat'], text=True)
    size = int(vm.split('page size of ')[1].split(' bytes')[0])
    return int(next(l for l in vm.splitlines() if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.')) * size
start = time.monotonic()
peak = anonymous()
assert peak < 70 * 10**9
rows = []
try:
    for job in [0]:
        if job == 0:
            command = ['pnpm', 'exec', 'tsx', 'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/check_review_site.mts', str(out)]
            begin = time.monotonic()
            p = subprocess.Popen(command, cwd=repo, start_new_session=True)
            while p.poll() is None:
                peak = max(peak, anonymous())
                if peak >= 70 * 10**9 or time.monotonic() - start >= 1700:
                    os.killpg(p.pid, signal.SIGTERM)
                    p.wait(timeout=20)
                    raise RuntimeError('Stopped own batch at memory/time bound')
                time.sleep(1)
            rows.append({'command': command, 'status': p.returncode, 'seconds': time.monotonic() - begin})
            assert p.returncode == 0
finally:
    (out / 'process.json').write_text(json.dumps({'commands': rows,
        'seconds': time.monotonic() - start, 'peakAnonymousBytes': peak,
        'lock': 'lockf -k /Users/raynos/projects/localai/.model.lock',
        'memoryLimitBytes': 70 * 10**9, 'timeLimitSeconds':1700}, indent=2) + '\n')
