"""Actual official decoded motion export, isolated two-thread CPU Blender."""
from pathlib import Path
import os,subprocess,json,time,signal
A=Path('/Users/raynos/projects/localai');P=A/'runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/unimate-new01';E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/unimate-new01');env=os.environ.copy();env.update(BLENDER_USER_CONFIG=str(P/'environment/config'),BLENDER_USER_SCRIPTS=str(P/'environment/scripts'),BLENDER_USER_EXTENSIONS=str(P/'environment/extensions'),TMPDIR=str(P/'environment/tmp'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2');rows=[];started=time.monotonic()
for kind in ['gt','raw']:
 command=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--threads','2','--python-exit-code','1','-P',str(A/'bin/unimate/blender_animate.py'),'--','--character',str(P/'preprocessed/RockhopWhiteRider_canonical.glb'),'--motion',str(P/(kind+'-decoded.npz')),'--output',str(P/(kind+'-animated'))];t=time.monotonic()
 with (E/(kind+'-export-log.txt')).open('x') as f:
  p=subprocess.Popen(command,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:rc=p.wait(timeout=300)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);rc=p.wait(timeout=5)
 rows.append({'kind':kind,'command':command,'exitCode':rc,'wallSeconds':time.monotonic()-t,'CPUthreads':2,'GPUjob':False});(E/'export-process.json').write_text(json.dumps({'rows':rows,'wallSeconds':time.monotonic()-started},indent=2)+'\n');assert rc==0
print('NEW_RIDER_DECODED_EXPORT_COMPLETE',flush=True)
