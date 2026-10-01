"""Third-round silent gate on the unchanged current private rider build."""
from pathlib import Path
import json
import os
import signal
import subprocess
import time

repo = Path('/Users/raynos/projects/games/rockhop')
out = repo / 'docs/evidence/hero-remaster/one-rider-v2/eye-strategy01/ship-gate105'
out.mkdir(parents=True, exist_ok=True)
command = ['pnpm', 'exec', 'tsx', 'harness/hero-remaster/replay.mts',
    '--build=harness/out/hero-remaster/new-rider-body11-build', f'--out={out}/replay.json',
    '--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json']


def anonymous_bytes():
    text = subprocess.check_output(['vm_stat'], text=True)
    size = int(text.split('page size of ')[1].split(' bytes')[0])
    return int(next(row for row in text.splitlines() if row.startswith('Anonymous pages:'))
               .split(':')[1].strip().rstrip('.')) * size


start = time.monotonic(); peak = anonymous_bytes(); assert peak < 70 * 10**9
p = subprocess.Popen(command, cwd=repo, start_new_session=True)
while p.poll() is None:
    peak = max(peak, anonymous_bytes())
    if peak >= 70 * 10**9 or time.monotonic() - start > 1700:
        os.killpg(p.pid, signal.SIGTERM); p.wait(timeout=20)
        raise RuntimeError('Own workload stopped at memory/batch bound')
    time.sleep(1)
(out / 'process.json').write_text(json.dumps({'command': command, 'status': p.returncode,
    'wallSeconds': time.monotonic() - start, 'peakAnonymousBytes': peak,
    'lock': 'lockf -k /Users/raynos/projects/localai/.model.lock'}, indent=2) + '\n')
assert p.returncode == 0
