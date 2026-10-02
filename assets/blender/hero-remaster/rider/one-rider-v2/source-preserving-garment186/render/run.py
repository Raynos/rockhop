"""Canonical serialized CPU render, isolated Blender environment, own watchdog."""
from pathlib import Path
from datetime import datetime,timezone
import os,signal,subprocess,time,json,re,hashlib
R=Path('/Users/raynos/projects/games/rockhop');S=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/source-preserving-garment186/render');E=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment186/render';A=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment186/render'
env=dict(os.environ,BLENDER_USER_CONFIG=str(S/'blender-config'),BLENDER_USER_SCRIPTS=str(S/'blender-scripts'),OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',CYCLES_DEVICE='CPU');cmd=['/usr/bin/lockf','-k','/Users/raynos/projects/localai/.model.lock','/Applications/Blender.app/Contents/MacOS/Blender','--background','--threads','2','--python',str(A/'render.py')];start=time.monotonic();utc=datetime.now(timezone.utc).isoformat();log=(S/'logs/blender.log').open('wb');p=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);receipt={'status':'QUEUED_CANONICAL_LOCK_CPU_RENDER','startedUTC':utc,'pid':p.pid,'argv':cmd,'envOverrides':{k:env[k]for k in ['BLENDER_USER_CONFIG','BLENDER_USER_SCRIPTS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','CYCLES_DEVICE']},'memory':[]};(E/'process.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'pid':p.pid,'startedUTC':utc,'queuedCanonicalLock':True}),flush=True)
reason=None
while p.poll()is None:
 v=subprocess.check_output(['vm_stat'],text=True);pages=int(re.search(r'page size of (\d+)',v).group(1));anon=int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1))*pages/1e9;receipt['memory'].append({'seconds':time.monotonic()-start,'anonymousGB':anon})
 if anon>=70:reason='anonymous memory70GB guard'
 if time.monotonic()-start>=360:reason='six minute own job guard inside eight minute task bound'
 if reason:
  os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=15);break
 time.sleep(10)
log.close();receipt.update(status='FROZEN_CPU_RENDER_COMPLETE'if p.returncode==0 else'FROZEN_CPU_RENDER_FAILURE',exitCode=p.returncode,seconds=time.monotonic()-start,stopReason=reason,logSHA256=hashlib.sha256((S/'logs/blender.log').read_bytes()).hexdigest());(E/'process.json').write_text(json.dumps(receipt,indent=2)+'\n');attempt=json.loads((E/'attempt.json').read_text());attempt['status']=receipt['status']
if p.returncode:attempt['failures'].append({'stage':'CPU render','exitCode':p.returncode,'reason':reason})
(E/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k not in ['memory','envOverrides','argv']}),flush=True)
