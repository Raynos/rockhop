"""Explain frozen full-tree lint versus the existing frozen CI checkout scope."""
import hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path

root = Path.cwd()
out = root / 'harness/out/user-agent3-2026-10-03/release49'
receipt = json.loads((out / 'export.json').read_text())
tip = 'b9e6d3f4df716d487df081b8608999677689b8e9'
base = '296da2fea6e4c825b710c78f41d921fb2e2734a4'
assert receipt['sourceSHA'] == tip
source = Path(receipt['exportPath'])
scope = Path('/private/tmp/rockhop-agent3-release49-ci-b9e6d3f4')
scope.mkdir()
git = lambda *args: subprocess.check_output(['git', *args], cwd=root)
workflow = git('show', tip + ':.github/workflows/deploy.yml').decode()
block = workflow.split('sparse-checkout: |', 1)[1].split('sparse-checkout-cone-mode:', 1)[0]
patterns = [line.strip() for line in block.splitlines() if line.strip()]
assert patterns[0] == '/*'
denied = [p[2:] for p in patterns if p.startswith('!/')]
allowed = [p[1:] for p in patterns[1:] if not p.startswith('!')]
assert all(p.endswith('/') for p in denied)
paths = git('ls-tree', '-r', '--name-only', '-z', tip).decode().split('\0')[:-1]
selected = [p for p in paths if not any(p.startswith(d) for d in denied) or p in allowed]
for p in selected:
    dest = scope / p
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Independent physical source copies; no symlink to the mutable shared tree.
    shutil.copyfile(source / p, dest)
    shutil.copymode(source / p, dest)
os.symlink(source / 'node_modules', scope / 'node_modules', target_is_directory=True)
assert not (scope / '.git').exists()
diagnostics = []
for line in (out / 'lint.log').read_text().splitlines():
    m = re.match(r'(.+?):(\d+):(\d+): error (.+?):', line)
    if m:
        diagnostics.append({'path': m[1], 'line': int(m[2]), 'column': int(m[3]), 'rule': m[4]})
files = []
for p in sorted({d['path'] for d in diagnostics}):
    try:
        old = git('show', base + ':' + p)
    except subprocess.CalledProcessError:
        old = None
    current = git('show', tip + ':' + p)
    files.append({'path': p, 'errorCount': sum(d['path'] == p for d in diagnostics),
                  'baselinePresent': old is not None, 'baselineByteIdentical': old == current,
                  'frozenSHA256': hashlib.sha256(current).hexdigest(),
                  'existingCIIncludesPath': p in selected})
env = dict(os.environ, VERCEL_GIT_COMMIT_SHA=tip, GIT_CEILING_DIRECTORIES='/private/tmp', CI='true')
start = time.monotonic()
log = out / 'ci-scope-lint.log'
with log.open('xb') as stream:
    result = subprocess.run(['pnpm', 'run', 'lint'], cwd=scope, env=env,
                            stdout=stream, stderr=subprocess.STDOUT)
# Read-only discovery in the existing Git checkout, without executing lint or fixes.
discovery = out / 'git-checkout-lint-discovery.log'
with discovery.open('xb') as stream:
    discovery_run = subprocess.run([str(source / 'node_modules/.bin/oxlint'), '--debug=files'],
                                  cwd=root, stdout=stream, stderr=subprocess.STDOUT)
text = discovery.read_text()
for f in files:
    f['existingGitCheckoutDiscoveryIncludesPath'] = f['path'] in text
report = {'sourceSHA': tip, 'baselineSHA': base, 'fullTreeLintExit': 1,
          'fullTreeErrorCount': len(diagnostics), 'files': files,
          'existingCIPatterns': patterns, 'existingCISourceFiles': len(selected),
          'scopePath': str(scope), 'ciScopeLintExit': result.returncode,
          'ciScopeElapsedS': time.monotonic() - start,
          'ciScopeLogSHA256': hashlib.sha256(log.read_bytes()).hexdigest(),
          'gitCheckoutDiscoveryExit': discovery_run.returncode,
          'gitCheckoutDiscoverySHA256': hashlib.sha256(discovery.read_bytes()).hexdigest(),
          'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'sourceModified': False, 'ignoresChanged': False, 'gitCheckoutCreated': False,
          'publicationAttempted': False}
with (out / 'lint-diagnosis.json').open('x') as stream:
    stream.write(json.dumps(report, indent=2) + '\n')
print(json.dumps(report), flush=True)
raise SystemExit(result.returncode)
