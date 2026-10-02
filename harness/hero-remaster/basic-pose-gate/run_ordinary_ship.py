"""Fresh ordinary-source gate; invoke under canonical lockf -k."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--round', type=int, required=True)
args = parser.parse_args()
R = Path('/Users/raynos/projects/games/rockhop')
E = R / f'docs/evidence/hero-remaster/one-rider-v2/ship{args.round}'
build = R / f'harness/out/hero-remaster/ordinary-ship{args.round}'
assert not build.exists() and not (E / 'process.json').exists()
E.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

inputs = ['src/render/hero/gltfRider.ts', 'src/render/hero/sleeveSkin.ts',
          'harness/hero-remaster/build.mts', 'harness/hero-remaster/replay.mts']
hashes = {path: sha(R / path) for path in inputs}
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip()
commands = [
    ['pnpm', 'exec', 'tsx', 'harness/hero-remaster/build.mts', '--out=' + str(build)],
    ['pnpm', 'exec', 'tsx', 'harness/hero-remaster/replay.mts', '--build=' + str(build),
     '--out=' + str(E / 'ship-gate.json'),
     '--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json']
]

def anonymous():
    output = subprocess.check_output(['vm_stat'], text=True)
    page = int(output.split('page size of ')[1].split(' bytes')[0])
    count = int(next(line for line in output.splitlines() if line.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
    return page * count

start, peak, rows = time.monotonic(), anonymous(), []
assert peak < 70 * 10**9
try:
    for command in commands:
        step = time.monotonic()
        process = subprocess.Popen(command, cwd=R, start_new_session=True)
        while process.poll() is None:
            peak = max(peak, anonymous())
            if peak >= 70 * 10**9 or time.monotonic() - start >= 1700:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=20)
                raise RuntimeError('Stopped own batch at resource bound')
            time.sleep(.5)
        rows.append({'command': command, 'status': process.returncode,
                     'seconds': time.monotonic() - step})
        assert process.returncode == 0
    assert hashes == {path: sha(R / path) for path in inputs}
    review = json.loads((build / 'hero-review.json').read_text())
    assert not review['mapping'] and not review['newRiderAdapter']
    (E / 'build.json').write_text(json.dumps({
        'build': str(build), 'sourceHEAD': head, 'inputSHA256': hashes,
        'publicCatalogModels': len(review['models']), 'modelReplacements': 0,
        'privatePoseOverlay': False,
        'limits': 'Current ordinary code; no rejected rider or player promotion.'
    }, indent=2) + '\n')
finally:
    (E / 'process.json').write_text(json.dumps({
        'commands': rows, 'seconds': time.monotonic() - start,
        'peakAnonymousBytes': peak, 'memoryLimitBytes': 70 * 10**9,
        'timeLimitSeconds': 1700,
        'lock': 'lockf -k /Users/raynos/projects/localai/.model.lock'
    }, indent=2) + '\n')
