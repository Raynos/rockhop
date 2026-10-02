"""Single CPU-only attempt runner; saves exit/time and replay inputs privately."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
A=Path(__file__).resolve().parent;R=A.parents[5];E=R/'docs/evidence/hero-remaster/one-rider-v2/local-shell200';S=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/local-shell200');python='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/ipc-admission197/.venv/bin/python';start=time.monotonic();env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2',NUMEXPR_NUM_THREADS='2');exits=[]
assert not (S/'construction.npz').exists() and not (E/'attempt.json').exists(),'Exactly one indexed attempt'
with (E/'terminal.log').open('w') as log:
 for recipe in ['solve.py','verify.py']:
  begin=time.monotonic()
  try:r=subprocess.run([python,str(A/recipe)],cwd=A,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200);code=r.returncode
  except subprocess.TimeoutExpired:code=124
  exits.append({'recipe':recipe,'exitCode':code,'elapsedSeconds':time.monotonic()-begin});log.flush()
  if code:break
result={'phases':exits,'elapsedSeconds':time.monotonic()-start,'CPUThreads':2,'GPU':False,'batchTimeoutSeconds':1200,'python':python,'environment':{k:env[k] for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']}}
(E/'exit.json').write_text(json.dumps(result,indent=2)+'\n')
# Preserve every actual pinned input plus exact recipes without importing session data.
archive=S/'repro-inputs';archive.mkdir(exist_ok=True);records={}
for p in [E/'build-report.json',E/'report.json']:
 if p.exists():records.update(json.loads(p.read_text()).get('inputPins',{}))
for p in A.glob('*.py'):records[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
manifest=[]
for path,record in sorted(records.items()):
 p=Path(path);assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],p
 target=archive/(record['sha256']+'-'+p.name)
 if not target.exists():shutil.copyfile(p,target)
 manifest.append({'originalPath':path,'frozenCopy':str(target),**record})
(S/'repro-manifest.json').write_text(json.dumps({'inputs':manifest,'process':result},indent=2)+'\n');print(json.dumps(result))
sys.exit(exits[-1]['exitCode'])
