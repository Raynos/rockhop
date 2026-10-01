"""Bounded native renderer batch. Invoke only under the canonical lockf lock."""
from pathlib import Path
import json
import os
import signal
import subprocess
import time

repo = Path('/Users/raynos/projects/games/rockhop')
out = repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind19/morph01/played'
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
    for angle in ['side', 'rear-three-quarter']:
        for surface in ['textured', 'gray']:
            command = ['pnpm', 'exec', 'tsx', 'harness/hero-remaster/new-rider-hip-motion.mts',
                '--build=harness/out/hero-remaster/new-rider-body19-overlay',
                f'--out={out}/{angle}/{surface}', f'--angle={angle}', f'--surface={surface}', '--camera-version=orbit02', '--hip-review-driver=1']
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
