"""One bounded headless export batch; acquire canonical lock before invocation."""
from pathlib import Path
import json,os,signal,subprocess,time
repo=Path('/Users/raynos/projects/games/rockhop');private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');out=private/'basic-pose-gate160-wide'
assert not out.exists(),'Frozen output must remain untouched'
def anonymous():
 v=subprocess.check_output(['vm_stat'],text=True);page=int(v.split('page size of ')[1].split(' bytes')[0]);return page*int(next(x for x in v.splitlines()if x.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
command=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/capture.mts','--source='+str(private/'garment-rebuild01/physical-v5-control157/rider.glb'),'--fixture='+str(private/'basic-pose-gate158/fixture-v3.json'),'--out='+str(out)]
start=time.monotonic();peak=anonymous();assert peak<70*10**9
p=subprocess.Popen(command,cwd=repo,start_new_session=True)
try:
 while p.poll()is None:
  peak=max(peak,anonymous())
  if peak>=70*10**9 or time.monotonic()-start>=1700:
   os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at resource bound')
  time.sleep(1)
 assert p.returncode==0
finally:
 out.mkdir(parents=True,exist_ok=True);(out/'process.json').write_text(json.dumps({'command':command,'status':p.returncode,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','memoryLimitBytes':70*10**9,'timeLimitSeconds':1700},indent=2)+'\n')
