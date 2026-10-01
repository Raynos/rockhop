from pathlib import Path
import os,subprocess,json,time,signal
S=Path(__file__).resolve().parent;repo=S.parents[7];R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind02');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind02')
E=R/'environment'
for n in ['config','scripts','extensions','tmp']:(E/n).mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.update(BLENDER_USER_CONFIG=str(E/'config'),BLENDER_USER_SCRIPTS=str(E/'scripts'),BLENDER_USER_EXTENSIONS=str(E/'extensions'),TMPDIR=str(E/'tmp'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--threads','2','--python-exit-code','1','-P',str(S/'build.py')];start=time.monotonic()
with (O/'cpu.log').open('x') as f:
 p=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 try:rc=p.wait(timeout=1790)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);rc=p.wait(timeout=5)
(O/'process.json').write_text(json.dumps({'command':cmd,'exitCode':rc,'wallSeconds':time.monotonic()-start,'CPUThreads':2,'GPUJob':False,'limitSeconds':1800},indent=2)+'\n');print('CPU_COMPLETE',rc,flush=True);raise SystemExit(rc)
