from pathlib import Path
import json,hashlib,subprocess,time
r=Path('/Users/raynos/projects/games/rockhop');recipe=r/'assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body07/preflight_shoulder_fields_v4.py';out=r/'docs/evidence/hero-remaster/finish-2026-10-05/construction/body07/array-preflight04'
assert hashlib.sha256(recipe.read_bytes()).hexdigest()=='42efff7881708f9e62d9486d8219e05d37a175070ac1c5987c2ef21ea8252526' and not out.exists()
cmd=['/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python',str(recipe),'--out',str(out)];t=time.monotonic();p=subprocess.run(cmd,cwd=r,text=True,capture_output=True,timeout=180)
e=r/'docs/evidence/hero-remaster/finish-2026-10-05/construction/body07';(e/'array-attempt45-trace.txt').write_text(p.stdout+p.stderr);(e/'array-attempt45-execution.json').write_text(json.dumps({'command':cmd,'exitCode':p.returncode,'wallSeconds':time.monotonic()-t,'stderr':p.stderr,'round':45,'guard':'harness/out/rider-finish-2026-10-05/round45-guard/guard.json'},indent=2)+'\n');print('ARRAY45_EXIT',p.returncode,flush=True)
subprocess.run(['/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python','/tmp/rockhop-finish-gate-round45.py'],cwd=r,check=True,timeout=180)
assert p.returncode==0,'Array45 failed; mandatory ordinary gate still ran'
