"""Bounded owned-process CPU witness runner; never touches unrelated jobs."""
import os,subprocess,time,signal,json,re
from pathlib import Path
root=Path('/Users/raynos/projects/games/rockhop');out=root/'docs/evidence/hero-remaster/one-rider-v2/source-rig188/actual-three';env=os.environ.copy();env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',UV_THREADPOOL_SIZE='2');start=time.monotonic();peak=0;reason=None
with (out/'process.log').open('w')as log:
 p=subprocess.Popen(['pnpm','exec','tsx',str(Path(__file__).with_name('evaluate.mts'))],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 while p.poll()is None:
  v=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',v).group(1));anon=int(re.search(r'Anonymous pages:\s*(\d+)',v).group(1))*page;peak=max(peak,anon)
  if time.monotonic()-start>720 or anon>=70_000_000_000:
   reason='elapsed720seconds'if time.monotonic()-start>720 else'anonymous70GB';os.killpg(p.pid,signal.SIGTERM);break
  time.sleep(.25)
 code=p.wait(timeout=10)
result={'exitCode':code,'wallSeconds':time.monotonic()-start,'maximumAnonymousBytes':peak,'CPUThreads':2,'timeoutSeconds':720,'anonymousLimitBytes':70_000_000_000,'stopReason':reason,'GPUUsed':False,'diagnosticSetupFailures':['Initial relative import climbed one directory too far; no model/export; replaced with explicit repository absolute module paths.']};(out/'process.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));print((out/'process.log').read_text()[-5000:]);assert code==0 and reason is None
