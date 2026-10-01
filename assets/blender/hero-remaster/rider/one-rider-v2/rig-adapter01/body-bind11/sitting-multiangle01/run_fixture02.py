from pathlib import Path
import json
import os
import signal
import subprocess
import time

recipe=Path(__file__).resolve().parent
root=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01')
out=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/fixture02');out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
for name,key in [('config','BLENDER_USER_CONFIG'),('scripts','BLENDER_USER_SCRIPTS'),('extensions','BLENDER_USER_EXTENSIONS'),('tmp','TMPDIR')]:
    folder=root/name;folder.mkdir(parents=True,exist_ok=True);env[key]=str(folder)
env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--threads','2','--python-exit-code','1','-P',str(recipe/'render_fixture02.py')]
start=time.monotonic()
with (out/'cpu.log').open('x') as log:
    process=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:status=process.wait(timeout=1790)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGTERM);status=process.wait(timeout=10)
(out/'process.json').write_text(json.dumps({'command':cmd,'exitCode':status,'wallSeconds':time.monotonic()-start,
    'CPUThreads':2,'GPUJob':False,'limitSeconds':1800,'isolatedEnvironment':str(root)},indent=2)+'\n')
print('CPU sitting render:',status,flush=True)
raise SystemExit(status)
