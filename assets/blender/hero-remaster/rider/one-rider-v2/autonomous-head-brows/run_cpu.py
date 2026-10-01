"""Bounded parent CPU construction; separate config/scripts/tmp, no GPU."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RUNTIME = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-head-brows')
EVIDENCE = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-head-brows')
script = Path(sys.argv[1]).resolve()
assert script.parent == ROOT
tag = sys.argv[2]
assert tag.replace('-', '').isalnum()
env = os.environ.copy()
overrides = {}
for name, folder in [('BLENDER_USER_CONFIG', 'config'), ('BLENDER_USER_SCRIPTS', 'scripts'),
                     ('BLENDER_USER_EXTENSIONS', 'extensions'), ('TMPDIR', 'tmp')]:
    directory = RUNTIME / 'environment' / folder
    directory.mkdir(parents=True, exist_ok=True)
    overrides[name] = str(directory)
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    overrides[name] = '2'
env.update(overrides)
EVIDENCE.mkdir(parents=True, exist_ok=True)
log = EVIDENCE / (tag + '-log.txt')
report = EVIDENCE / (tag + '-process.json')
assert not log.exists() and not report.exists()
start = datetime.datetime.now(datetime.timezone.utc)
command = ['/Applications/Blender.app/Contents/MacOS/Blender', '--background',
           '--factory-startup', '--threads', '2', '--python-exit-code', '1',
           '--python', str(script)]
exit_code = None
timed_out = False
try:
    with log.open('x') as output:
        exit_code = subprocess.run(command, env=env, stdout=output,
                                   stderr=subprocess.STDOUT, timeout=720).returncode
except subprocess.TimeoutExpired:
    timed_out = True
finally:
    report.write_text(json.dumps({'command': command, 'startedUTC': start.isoformat(),
        'completedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'exitCode': exit_code, 'timedOut': timed_out, 'batchLimitSeconds': 720,
        'CPUThreads': 2, 'GPUWorkload': False, 'environmentOverrides': overrides,
        'launcherInterpreter': sys.executable, 'launcherVersion': sys.version,
        'scriptSHA256': hashlib.sha256(script.read_bytes()).hexdigest(),
        'log': str(log), 'logSHA256': hashlib.sha256(log.read_bytes()).hexdigest()
    }, indent=2) + '\n')
sys.exit(124 if timed_out else exit_code)
