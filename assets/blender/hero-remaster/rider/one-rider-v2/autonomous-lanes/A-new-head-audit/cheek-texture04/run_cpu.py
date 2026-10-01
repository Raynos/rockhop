"""Owned CPU2 Blender stage, fixed shared batch deadline, no GPU or mutation."""
import subprocess,os,sys,json,hashlib,signal
from pathlib import Path
from datetime import datetime,timezone
S=Path(__file__).resolve().parent
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit');E=R/'environment-parent-texture04'
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/cheek-texture04')
name=sys.argv[1]
if name not in ['classify','repair','render']:raise RuntimeError('Unknown owned stage')
script=S/(name+'.py');log=R/('h21-cheek-texture04-'+name+'-log.txt');receipt=O/(name+'-process.json')
if log.exists() or receipt.exists():raise RuntimeError('Frozen stage exists')
cmd=['/Applications/Blender.app/Contents/MacOS/Blender','--background','--factory-startup','--threads','2','--python-exit-code','1','--python',str(script)]
env=os.environ.copy();env.update(BLENDER_USER_CONFIG=str(E/'config'),BLENDER_USER_SCRIPTS=str(E/'scripts'),BLENDER_USER_EXTENSIONS=str(E/'extensions'),TMPDIR=str(E/'tmp'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
start=datetime.now(timezone.utc);deadline=datetime.fromisoformat(json.loads((O/'setup.json').read_text())['hardDeadlineUTC'])
if start>=deadline:raise RuntimeError('Fixed batch ceiling passed')
record={'startedUTC':start.isoformat(),'hardDeadlineUTC':deadline.isoformat(),'CPUThreads':2,'GPUJob':False,'command':cmd,'recipeSHA256':hashlib.sha256(script.read_bytes()).hexdigest()}
with log.open('x') as stream:
 p=subprocess.Popen(cmd,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 try:rc=p.wait(timeout=max(1,(deadline-start).total_seconds()-6))
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM)
  try:rc=p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
  record['stopReason']='Fixed30minutecompletegroupdeadline'
record.update(exitCode=rc,completedUTC=datetime.now(timezone.utc).isoformat(),logSHA256=hashlib.sha256(log.read_bytes()).hexdigest());receipt.open('x').write(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));sys.exit(rc)
