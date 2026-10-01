"""One bounded actual runtime probe; caller owns shared model lock."""
from pathlib import Path
import subprocess,time,os,signal,json,sys
repo=Path('/Users/raynos/projects/games/rockhop');out=Path(sys.argv[1]) if len(sys.argv)>1 else repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11'
def anon():
 v=subprocess.check_output(['vm_stat'],text=True);size=int(v.split('page size of ')[1].split(' bytes')[0]);return int(next(l for l in v.splitlines() if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))*size
start=time.monotonic();peak=anon();assert peak<70*10**9
command=['pnpm','exec','tsx','harness/hero-remaster/new-rider-visible-contact-probe.mts',f'--out={out}'];p=subprocess.Popen(command,cwd=repo,start_new_session=True)
try:
 while p.poll() is None:
  peak=max(peak,anon())
  if peak>=70*10**9 or time.monotonic()-start>=1100:
   os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own workload at memory/batch bound')
  time.sleep(1)
 assert p.returncode==0
finally:
 (out/'process.json').write_text(json.dumps({'command':command,'status':p.returncode,'wallSeconds':time.monotonic()-start,'peakAnonymousBytes':peak,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','memoryLimitDecimalBytes':70*10**9,'batchDeadlineSeconds':1100},indent=2)+'\n')
