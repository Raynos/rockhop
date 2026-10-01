from pathlib import Path
import os,sys,subprocess,json,time,signal
S=Path(__file__).resolve().parent;P=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/unimate-new01');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/unimate-new01');env=os.environ.copy();env.update(BLENDER_USER_CONFIG=str(P/'environment/config'),BLENDER_USER_SCRIPTS=str(P/'environment/scripts'),BLENDER_USER_EXTENSIONS=str(P/'environment/extensions'),TMPDIR=str(P/'environment/tmp'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2');preview='--preview' in sys.argv;rows=[];started=time.monotonic()
for kind in (['gt'] if preview else ['gt','raw']):
 command=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--threads','2','--python-exit-code','1','-P',str(S/'render.py'),'--','--kind',kind]+(['--preview'] if preview else []);t=time.monotonic();limit=90 if preview else 850
 with (E/(kind+('-preview' if preview else '-render')+'-log.txt')).open('x') as f:
  child=subprocess.Popen(command,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:rc=child.wait(timeout=limit)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGTERM);rc=child.wait(timeout=5)
 rows.append({'kind':kind,'command':command,'exitCode':rc,'wallSeconds':time.monotonic()-t,'CPUthreads':2,'GPUjob':False});(E/(('preview' if preview else 'render')+'-process.json')).write_text(json.dumps({'rows':rows,'wallSeconds':time.monotonic()-started,'limitSeconds':1800},indent=2)+'\n');assert rc==0
print('ACTUAL_RENDER_COMPLETE',flush=True)
