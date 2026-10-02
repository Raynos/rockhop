"""Bound silent matched-film decoder; canonical lockf -k required."""
from pathlib import Path
import json,signal,subprocess,time
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/tube-motion173';m=json.loads((E/'matched-evidence.json').read_text())
cmd=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/play_tube173.mts',m['matchedMovie'],str(E/'playback.json')]
def anonymous():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
start=time.monotonic();peak=anonymous();assert peak<70*10**9
p=subprocess.Popen(cmd,cwd=R,start_new_session=True)
try:
 while p.poll()is None:
  peak=max(peak,anonymous())
  if peak>=70*10**9 or time.monotonic()-start>=60:
   os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at resource bound')
  time.sleep(.25)
 assert p.returncode==0
finally:
 (E/'playback-process.json').write_text(json.dumps({'command':cmd,'status':p.returncode,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'memoryLimitBytes':70*10**9,'timeLimitSeconds':60,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock'},indent=2)+'\n')
