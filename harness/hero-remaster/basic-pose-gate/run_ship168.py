"""Required third-round retained runtime gate; canonical lockf -k required."""
from pathlib import Path
import json,signal,subprocess,time
repo=Path('/Users/raynos/projects/games/rockhop')
out=repo/'docs/evidence/hero-remaster/one-rider-v2/ship168';out.mkdir(parents=True,exist_ok=True)
assert not (out/'ship-gate.json').exists(),'Preserve completed receipts'
def anonymous():
 v=subprocess.check_output(['vm_stat'],text=True);page=int(v.split('page size of ')[1].split(' bytes')[0])
 return page*int(next(x for x in v.splitlines()if x.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
cmd=['pnpm','exec','tsx','harness/hero-remaster/replay.mts','--build=harness/out/hero-remaster/new-rider-body34-overlay','--out='+str(out/'ship-gate.json'),'--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json']
start=time.monotonic();peak=anonymous();assert peak<70*10**9
p=subprocess.Popen(cmd,cwd=repo,start_new_session=True)
try:
 while p.poll()is None:
  peak=max(peak,anonymous())
  if peak>=70*10**9 or time.monotonic()-start>=1700:
   os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at resource bound')
  time.sleep(1)
 assert p.returncode==0
finally:
 (out/'process.json').write_text(json.dumps({'command':cmd,'status':p.returncode,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','memoryLimitBytes':70*10**9,'timeLimitSeconds':1700,'limits':'Retained34 functional replay, not acceptance of new garment, real mobile performance or surface contacts.'},indent=2)+'\n')
