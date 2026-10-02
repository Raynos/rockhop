"""Authoritative CPU-only exit/elapsed capture with hard per-batch timeout."""
from pathlib import Path
import os,json,subprocess,time,sys,hashlib
root=Path(__file__).resolve().parent
private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/source-ruled194')
name=sys.argv[1];assert name in ['build','verify','final_checks'];env=dict(os.environ);env.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
batchOrdinal=1+len(list(private.glob(name+'-construction-terminal*.log')));suffix='-'+str(batchOrdinal);log=private/(name+'-construction-terminal'+suffix+'.log');assert not log.exists();start=time.monotonic()
with log.open('wb') as f:
 try:r=subprocess.run(['/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python',str(root/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT,env=env,timeout=890);code=r.returncode;timedout=False
 except subprocess.TimeoutExpired:code=124;timedout=True
v={'batch':name,'terminalExitCode':code,'timeout':timedout,'elapsedSeconds':time.monotonic()-start,'CPUThreads':2,'GPU':False,'logSHA256':hashlib.sha256(log.read_bytes()).hexdigest(),'command':['/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python',str(root/(name+'.py'))]}
(private/(name+'-construction-exit'+suffix+'.json')).write_text(json.dumps(v,indent=2)+'\n');print(log.read_text());print(json.dumps(v));sys.exit(code)
