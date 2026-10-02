"""Authenticated headless playback; receive ephemeral token via non-echo stdin.

Invoke with canonical lockf -k. No credential is written to disk or argv.
"""
from pathlib import Path
import json, os, signal, subprocess, sys, termios, time

R = Path('/Users/raynos/projects/games/rockhop')
E = R/'docs/evidence/hero-remaster/one-rider-v2/gallery171/hosted'
E.mkdir(parents=True, exist_ok=True)
assert not (E/'events-check.json').exists(), 'Preserve completed receipts'
state = termios.tcgetattr(sys.stdin)
hidden = list(state)
hidden[3] &= ~termios.ECHO
termios.tcsetattr(sys.stdin, termios.TCSANOW, hidden)
try:
    print('READY_FOR_EPHEMERAL_SITE_PLAYBACK_TOKEN', flush=True)
    auth = json.loads(sys.stdin.readline())
finally:
    termios.tcsetattr(sys.stdin, termios.TCSANOW, state)
assert isinstance(auth.get('token'), str) and auth['token']

def anonymous():
    s = subprocess.check_output(['vm_stat'], text=True)
    page = int(s.split('page size of ')[1].split(' bytes')[0])
    return page*int(next(l for l in s.splitlines() if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))

cmd = ['pnpm', 'exec', 'tsx', 'harness/hero-remaster/basic-pose-gate/check_events171.mts', str(E), 'https://rockhop-rider-review.raynos.chatgpt.site/#structural-gate', '--auth-stdin']
start = time.monotonic()
peak = anonymous()
assert peak < 70*10**9
p = subprocess.Popen(cmd, cwd=R, stdin=subprocess.PIPE, start_new_session=True)
p.stdin.write((json.dumps(auth)+'\n').encode())
p.stdin.close()
auth = None
try:
    while p.poll() is None:
        peak = max(peak, anonymous())
        if peak >= 70*10**9 or time.monotonic()-start >= 1700:
            os.killpg(p.pid, signal.SIGTERM)
            p.wait(timeout=20)
            raise RuntimeError('Stopped own batch at resource bound')
        time.sleep(.5)
    assert p.returncode == 0
finally:
    (E/'process.json').write_text(json.dumps({'command':cmd, 'status':p.returncode, 'seconds':time.monotonic()-start, 'peakAnonymousBytes':peak, 'memoryLimitBytes':70*10**9, 'timeLimitSeconds':1700, 'lock':'lockf -k /Users/raynos/projects/localai/.model.lock', 'credentialHandling':'Non-echo stdin; same-origin header only; no credential persisted'}, indent=2)+'\n')
