"""Bounded sleeve gameplay comparison; canonical lock required around this batch."""
from pathlib import Path
import json,os,signal,subprocess,time,sys
repo=Path('/Users/raynos/projects/games/rockhop');out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind36';out.mkdir(parents=True,exist_ok=True)
def anonymous():
 vm=subprocess.check_output(['vm_stat'],text=True);size=int(vm.split('page size of ')[1].split(' bytes')[0]);return int(next(l for l in vm.splitlines() if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))*size
commands=[['pnpm','exec','tsx','harness/hero-remaster/replay.mts','--build=harness/out/hero-remaster/new-rider-body34-overlay',f'--out={out}/ship-gate147.json','--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json','--sleeve-review-driver=0']]
label='ship-process147.json'
start=time.monotonic();peak=anonymous();assert peak<70*10**9;rows=[]
try:
 for command in commands:
  begin=time.monotonic();p=subprocess.Popen(command,cwd=repo,start_new_session=True)
  while p.poll() is None:
   peak=max(peak,anonymous())
   if peak>=70*10**9 or time.monotonic()-start>=1700:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at memory/time bound')
   time.sleep(1)
  rows.append({'command':command,'status':p.returncode,'seconds':time.monotonic()-begin});assert p.returncode==0
finally:
 (out/label).write_text(json.dumps({'commands':rows,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','memoryLimitBytes':70*10**9,'timeLimitSeconds':1700},indent=2)+'\n')
