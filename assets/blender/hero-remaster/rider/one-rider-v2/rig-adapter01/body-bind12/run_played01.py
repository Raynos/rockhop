"""Evaluate the first two-sheet eye trial in the actual silent engine."""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import time

repo = Path('/Users/raynos/projects/games/rockhop')
root = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
master = root / 'rig-adapter01/body-bind12/construction01/rider.glb'
assert master.exists(), 'Construction must freeze before running actual comparison'
out = repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind12/played01'
out.mkdir(parents=True, exist_ok=True)
mapping_file = out / 'mapping-full-diagnostic.json'
mapping_file.write_text(json.dumps({n: str(master) for n in
    ['models/rider-street-mustard.glb', 'models/rider-street-mustard-lod.glb']}, indent=2) + '\n')
build = repo / 'harness/out/hero-remaster/new-rider-body12-build'
commands = [
    ['pnpm', 'exec', 'tsx', 'harness/hero-remaster/build.mts', f'--out={build}',
     f'--models={mapping_file}', '--new-rider-adapter=1'],
    ['pnpm', 'exec', 'tsx', 'harness/hero-remaster/replay.mts', f'--build={build}',
     f'--out={out}/replay.json',
     '--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json']]
for surface in ['textured', 'gray']:
    commands.append(['pnpm', 'exec', 'tsx', 'harness/hero-remaster/new-rider-played-capture.mts',
        f'--build={build}', f'--out={out}/{surface}', '--mode=ride', '--tier=high',
        '--seconds=6', '--fps=12', '--focus=face', '--detail-zoom=3', '--center-focus=1',
        f'--surface={surface}',
        '--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json'])


def anonymous_bytes():
    vm = subprocess.check_output(['vm_stat'], text=True)
    size = int(vm.split('page size of ')[1].split(' bytes')[0])
    return int(next(l for l in vm.splitlines() if l.startswith('Anonymous pages:'))
               .split(':')[1].strip().rstrip('.')) * size


start = time.monotonic(); peak = anonymous_bytes(); assert peak < 70 * 10**9
rows = []
try:
    for command in commands:
        p = subprocess.Popen(command, cwd=repo, start_new_session=True)
        begin = time.monotonic()
        while p.poll() is None:
            peak = max(peak, anonymous_bytes())
            if peak >= 70 * 10**9 or time.monotonic() - start > 1700:
                os.killpg(p.pid, signal.SIGTERM); p.wait(timeout=20)
                raise RuntimeError('Stopped own workload at memory/batch bound')
            time.sleep(1)
        rows.append({'command': command, 'status': p.returncode, 'seconds': time.monotonic() - begin})
        assert p.returncode == 0
finally:
    (out / 'process.json').write_text(json.dumps({
        'sourceSHA256': hashlib.sha256(master.read_bytes()).hexdigest(),
        'commands': rows, 'wallSeconds': time.monotonic() - start, 'peakAnonymousBytes': peak,
        'lock': 'lockf -k /Users/raynos/projects/localai/.model.lock',
        'limits': 'Both logical tiers use FULL geometry. Eye trial unaccepted until parent actual-motion review; same input and private surface-focus camera.'}, indent=2) + '\n')
    if (build / 'hero-review.json').exists():
        (out / 'build-manifest.json').write_bytes((build / 'hero-review.json').read_bytes())
