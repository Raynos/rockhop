"""Prepared only: parent-queued single model job, canonical lock, no eviction.

Default is a dry-run. --execute requires the parent to actually queue this job.
Whole worker process group includes sampling, Metal exports and CPU bake/export.
"""
import argparse,os,sys,json,time,subprocess,signal,hashlib
from pathlib import Path
LOCK=Path('/Users/raynos/projects/localai/.model.lock')
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit')
MEM=Path('/Users/raynos/projects/localai/bin/mem-gb.sh')
LIMIT_GIB=70e9/2**30
STOP_GIB=65e9/2**30
POLL_SECONDS=1

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');parser.add_argument('--inside-lock',action='store_true');parser.add_argument('--tag',required=True);parser.add_argument('command',nargs=argparse.REMAINDER);args=parser.parse_args()
 command=args.command[1:] if args.command and args.command[0]=='--' else args.command
 if not command:raise RuntimeError('Missing actual engine command')
 if not args.execute:
  print(json.dumps({'status':'PREPARED ONLY; parent has not queued GPU work','command':command,'canonicalLock':str(LOCK),'lockMode':'lockf -k','timeLimitSeconds':1800,'anonymousLimitBytes':70e9,'limitGiB':LIMIT_GIB,'preemptiveStopBytes':65e9,'preemptiveStopGiB':STOP_GIB,'pollIntervalSeconds':POLL_SECONDS,'eviction':False},indent=2));return
 if not args.inside_lock:
  os.execv('/usr/bin/lockf',['lockf','-k',str(LOCK),sys.executable,str(Path(__file__).resolve()),'--execute','--inside-lock','--tag',args.tag,'--']+command)
 R.mkdir(parents=True,exist_ok=True);log=R/(args.tag+'-model-log.txt');receipt=R/(args.tag+'-model-process.json')
 if log.exists() or receipt.exists():raise RuntimeError('Frozen job tag exists')
 started=time.monotonic();deadline=started+1800;stopDeadline=deadline-6
 def memory():
  value=subprocess.run(['bash',str(MEM)],capture_output=True,text=True,check=True,timeout=5).stdout
  anonymous=float(value.split()[0]);return anonymous
 def terminate(p):
  if p.poll() is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 record={'command':command,'canonicalLock':str(LOCK),'lockMode':'lockf -k','timeLimitSeconds':1800,'terminationGraceReservedSeconds':6,'anonymousLimitBytes':70e9,'preemptiveStopBytes':65e9,'preemptiveStopGiB':STOP_GIB,'pollIntervalSeconds':POLL_SECONDS,'lockInheritedByCompleteWorkerGroup':True,'noEviction':True,'samples':[]}
 while True:
  anon=memory();record['samples'].append({'stage':'memory-gate','elapsedSeconds':time.monotonic()-started,'anonymousGiB':anon})
  if anon<STOP_GIB:break
  if time.monotonic()>=stopDeadline:
   record.update(stopReason='Memory gate timed out within 30-minute lock batch',exitCode=None,wallSeconds=time.monotonic()-started)
   receipt.write_text(json.dumps(record,indent=2)+'\n');raise RuntimeError(record['stopReason'])
  time.sleep(POLL_SECONDS)
 env=os.environ.copy();E=R/'environment'
 env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2',NUMEXPR_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTORCH_ENABLE_MPS_FALLBACK='1',BLENDER_USER_CONFIG=str(E/'config'),BLENDER_USER_SCRIPTS=str(E/'scripts'),BLENDER_USER_EXTENSIONS=str(E/'extensions'),TMPDIR=str(E/'tmp'))
 with log.open('x') as stream:
  p=subprocess.Popen(command,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   while p.poll() is None:
    anon=memory();record['samples'].append({'stage':'worker','elapsedSeconds':time.monotonic()-started,'anonymousGiB':anon})
    if anon>=STOP_GIB:record['stopReason']='Anonymous memory reached preemptive 65 GB stop margin';terminate(p);break
    if time.monotonic()>=stopDeadline:record['stopReason']='30-minute complete process-group deadline';terminate(p);break
    time.sleep(min(POLL_SECONDS,max(0,stopDeadline-time.monotonic())))
  except BaseException:
   terminate(p);raise
  finally:
   record['exitCode']=p.wait();record['wallSeconds']=time.monotonic()-started;record['logSHA256']=hashlib.sha256(log.read_bytes()).hexdigest();receipt.write_text(json.dumps(record,indent=2)+'\n')
 if record['exitCode']!=0:sys.exit(record['exitCode'])

if __name__=='__main__':main()
