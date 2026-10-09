"""Run one final supplied build through the unchanged shared memory guard."""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--build', required=True)
parser.add_argument('--expected', required=True)
parser.add_argument('--run', required=True, help='Fresh numbered run, e.g. run01')
args = parser.parse_args()
assert args.run.isalnum(), 'Use a simple fresh run name'
root = Path(__file__).resolve().parents[4]
build = Path(args.build).resolve()
expected = Path(args.expected).resolve()
assert (build / 'version.json').is_file() and expected.is_file()
guard = root / 'assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py'
assert hashlib.sha256(guard.read_bytes()).hexdigest() == 'cf8acd15d8b7484480bee74d23892be815d955ffd87115d3da8ed228ffb3d916'
evidence = root / 'docs/evidence/rider-rebuild/focused-mobile-gate09' / (args.run + '-guard')
assert not evidence.exists(), 'Fresh run required'
evidence.mkdir(parents=True)
output = root / 'harness/out/rider-rebuild/focused-mobile-gate09' / args.run
command = [sys.executable, '/tmp/rockhop-gameplay-telemetry-queuefast.py',
           str(evidence / 'admission-telemetry.jsonl'), str(evidence / 'guard.json'),
           sys.executable, str(guard), '--out', str(evidence), '--limit-seconds', '420', '--',
           'node', str(Path(__file__).with_name('run.mjs')), '--build=' + str(build),
           '--expected=' + str(expected), '--backend=metal', '--seconds=20', '--out=' + str(output)]
raise SystemExit(subprocess.call(command, cwd=root))
