"""Two unchanged stockThree captures, sequential under one canonical lock."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,os,time,signal,re,hashlib
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');S=B/'source-preserving-garment187';E=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment187';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();save=lambda p,x:p.write_text(json.dumps(x,indent=2)+'\n');fixture=S/'fixture-three-families.json';sources={'candidate':B/'candidate-handoff170/hood-fixed185-187/rider.glb','baseline':B/'rig-adapter01/body-bind34/rider.glb'}
if '--worker'in sys.argv:
 for label,source in sources.items():
  out=S/label;assert not out.exists(),'Preserve frozen captures';cmd=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/capture.mts','--source='+str(source),'--fixture='+str(fixture),'--out='+str(out)];print(json.dumps({'stage':label,'startedUTC':datetime.now(timezone.utc).isoformat(),'command':cmd}),flush=True)
  with(S/'logs'/f'{label}.log').open('wb')as log:p=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',UV_THREADPOOL_SIZE='2'))
  assert p.returncode==0,(label,p.returncode);rep=json.loads((out/'report.json').read_text());assert len(rep['frames'])==579 and not rep['errors']and'failure'not in rep;assert rep['sourceSHA256']==sha(source)and rep['loaded']==[sha(source)];assert rep['fixtureSHA256']==sha(fixture);assert all(r['matrixError']<1e-8 for r in rep['frames']);print(json.dumps({'stage':label,'status':'579CAPTURED_AND_HASHVERIFIED'}),flush=True)
 sys.exit(0)
prep=json.loads((E/'preparation.json').read_text());assert prep['status']=='ONE_UNMODIFIED_MAPPING_AND_MATCHED_BASELINE_VERIFIED';(S/'logs').mkdir(exist_ok=True);start=time.monotonic();cmd=['/usr/bin/lockf','-k','/Users/raynos/projects/localai/.model.lock','/usr/bin/python3',str(Path(__file__).resolve()),'--worker'];log=(S/'logs/batch.log').open('wb');p=subprocess.Popen(cmd,cwd=R,start_new_session=True,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',UV_THREADPOOL_SIZE='2'));rep={'status':'QUEUED_SINGLE_CANONICAL_BATCH','startedUTC':datetime.now(timezone.utc).isoformat(),'pid':p.pid,'command':cmd,'memorySamples':[],'limitSeconds':1700,'anonymousLimitGB':70};save(E/'process.json',rep);print(json.dumps({'pid':p.pid,'startedUTC':rep['startedUTC'],'canonicalBatch':True}),flush=True);reason=None
while p.poll()is None:
 v=subprocess.check_output(['vm_stat'],text=True);pg=int(re.search(r'page size of (\d+)',v).group(1));anon=pg*int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1))/1e9;rep['memorySamples'].append({'seconds':time.monotonic()-start,'anonymousGB':anon})
 if anon>=70:reason='shared anonymous70GB guard'
 if time.monotonic()-start>=1700:reason='own1700s batch bound'
 if reason:
  os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);break
 time.sleep(1)
log.close();rep.update(status='FROZEN_BOTH_MATCHED_CAPTURES_COMPLETE'if p.returncode==0 else'FROZEN_CAPTURE_FAILURE',exitCode=p.returncode,seconds=time.monotonic()-start,stopReason=reason,batchLogSHA256=sha(S/'logs/batch.log'));save(E/'process.json',rep);attempt=json.loads((E/'attempt.json').read_text());attempt['status']=rep['status']
if p.returncode:attempt['failures'].append({'stage':'canonical matched capture batch','exitCode':p.returncode,'stopReason':reason})
save(E/'attempt.json',attempt);print(json.dumps({k:v for k,v in rep.items()if k!='memorySamples'}),flush=True)
