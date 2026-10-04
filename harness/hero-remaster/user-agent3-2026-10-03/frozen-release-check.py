"""Run one normal check only in the pinned, independently verified clean export."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--step', required=True)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
root = Path(__file__).resolve().parents[3]
out = root / 'harness/out/user-agent3-2026-10-03/release49'
export = json.loads((out / 'export.json').read_text())
source = Path(export['exportPath']).resolve()
expected = 'b9e6d3f4df716d487df081b8608999677689b8e9'
assert export['sourceSHA'] == expected and source == Path('/private/tmp/rockhop-agent3-release49-b9e6d3f4')
assert not (source / '.git').exists()
assert a.command and a.command[0] == '--'
command = a.command[1:]
assert command and command[0] in ['pnpm', 'node']
assert a.step.replace('-', '').isalnum()
env = dict(os.environ, VERCEL_GIT_COMMIT_SHA=expected,
           GIT_CEILING_DIRECTORIES='/private/tmp', CI='true')
log = out / (a.step + '.log')
start = time.monotonic()
with log.open('xb') as stream:
    result = subprocess.run(command, cwd=source, env=env,
                            stdout=stream, stderr=subprocess.STDOUT)
report = {'sourceSHA': expected, 'step': a.step, 'command': command,
          'cwd': str(source), 'exitCode': result.returncode,
          'elapsedS': time.monotonic() - start,
          'logSHA256': hashlib.sha256(log.read_bytes()).hexdigest(),
          'logBytes': log.stat().st_size,
          'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'gitCheckoutCreated': False, 'publicationAttempted': False}
with (out / (a.step + '.json')).open('x') as stream:
    stream.write(json.dumps(report, indent=2) + '\n')
print(json.dumps(report), flush=True)
raise SystemExit(result.returncode)
