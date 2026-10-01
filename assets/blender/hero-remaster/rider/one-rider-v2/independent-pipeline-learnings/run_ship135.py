from pathlib import Path
import json,signal,subprocess,time,os
repo=Path('/Users/raynos/projects/games/rockhop');out=repo/'docs/evidence/hero-remaster/one-rider-v2/independent-pipeline-learnings-2026-10-01';start=time.monotonic()
def anon():
 s=subprocess.check_output(['vm_stat'],text=True);size=int(s.split('page size of ')[1].split(' bytes')[0]);return int(next(x for x in s.splitlines() if x.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))*size
peak=anon();assert peak<70*10**9
c=['pnpm','exec','tsx','harness/hero-remaster/replay.mts','--build=harness/out/hero-remaster/new-rider-body11-build',f'--out={out}/ship-gate135.json','--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json'];p=subprocess.Popen(c,cwd=repo,start_new_session=True)
while p.poll() is None:
 peak=max(peak,anon())
 if peak>=70*10**9 or time.monotonic()-start>1700:
  os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Own workload stopped at bound')
 time.sleep(1)
(out/'ship-process135.json').write_text(json.dumps({'command':c,'exit':p.returncode,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','limits':'Required thirdround silent unchanged11gate, no new candidate acceptance.'},indent=2)+'\n');assert p.returncode==0
