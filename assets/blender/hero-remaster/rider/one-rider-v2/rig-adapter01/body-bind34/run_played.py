"""Bounded sleeve gameplay comparison; canonical lock required around this batch."""
from pathlib import Path
import json,os,signal,subprocess,time,sys
repo=Path('/Users/raynos/projects/games/rockhop');out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/played';out.mkdir(parents=True,exist_ok=True)
def anonymous():
 vm=subprocess.check_output(['vm_stat'],text=True);size=int(vm.split('page size of ')[1].split(' bytes')[0]);return int(next(l for l in vm.splitlines() if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))*size
commands=[]
for label,build,driver in [('candidate','new-rider-body34-overlay','0')]:
 for angle in ['side','rear-three-quarter']:
  for surface in ['textured','gray']:
   commands.append(['pnpm','exec','tsx','harness/hero-remaster/new-rider-fresh-rig-motion.mts',f'--build=harness/out/hero-remaster/{build}',f'--out={out}/{label}/{angle}/{surface}',f'--angle={angle}',f'--surface={surface}','--camera-version=orbit02',f'--sleeve-review-driver={driver}',f'--camera-reference=docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind25/morph01/played/baseline/{angle}/{surface}/report.json'])
commands.append(['pnpm','exec','tsx','harness/hero-remaster/replay.mts','--build=harness/out/hero-remaster/new-rider-body34-overlay',f'--out={out}/ship-gate144.json','--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json','--sleeve-review-driver=0'])
label='candidate-process.json'
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
