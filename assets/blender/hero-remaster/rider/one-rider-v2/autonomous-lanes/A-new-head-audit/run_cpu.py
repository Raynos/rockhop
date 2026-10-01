"""Isolated laneA CPU-only Blender launcher; shared binaries disclosed."""
import os,sys,subprocess,time,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
BLENDER=Path('/Applications/Blender.app/Contents/MacOS/Blender')
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit')
E=R/'environment';OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit')
script=Path(sys.argv[1]).resolve();tag=sys.argv[2];assert script.is_file() and script.is_relative_to(Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/A-new-head-audit'))
log=R/f'{tag}.log';process_file=OUT/f'{tag}-process.json'
if log.exists() or process_file.exists():raise RuntimeError('Frozen lane job exists')
env=os.environ.copy();env.update(BLENDER_USER_CONFIG=str(E/'config'),BLENDER_USER_SCRIPTS=str(E/'scripts'),BLENDER_USER_EXTENSIONS=str(E/'extensions'),TMPDIR=str(E/'tmp'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
cmd=[str(BLENDER),'--background','--factory-startup','--threads','2','--python-exit-code','1','--python',str(script)]
start=datetime.now(timezone.utc);deadline=datetime(2026,10,1,2,17,tzinfo=timezone.utc);remaining=(deadline-start).total_seconds()
if remaining<=0:raise RuntimeError('First lane deadline reached')
with log.open('x') as f:
 p=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=min(900,remaining))
report={'command':cmd,'startedUTC':start.isoformat(),'completedUTC':datetime.now(timezone.utc).isoformat(),'exitCode':p.returncode,'deadlineUTC':deadline.isoformat(),'environmentOverrides':{k:env[k] for k in ['BLENDER_USER_CONFIG','BLENDER_USER_SCRIPTS','BLENDER_USER_EXTENSIONS','TMPDIR','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']},'launcherPythonShared':sys.executable,'launcherPythonVersion':sys.version,'scriptSHA256':hashlib.sha256(script.read_bytes()).hexdigest(),'log':str(log),'logSHA256':hashlib.sha256(log.read_bytes()).hexdigest(),'GPUWorkload':False}
process_file.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));sys.exit(p.returncode)
