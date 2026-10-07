from pathlib import Path
import subprocess,json,time
r=Path('/Users/raynos/projects/games/rockhop');cmd=['/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python','docs/evidence/hero-remaster/finish-2026-10-05/construction/body07/prove-native-storage48.py'];t=time.monotonic();p=subprocess.run(cmd,cwd=r,text=True,capture_output=True,timeout=30);e=r/'docs/evidence/hero-remaster/finish-2026-10-05/construction/body07';(e/'array-storage48-trace.txt').write_text(p.stdout+p.stderr);(e/'array-storage48-execution.json').write_text(json.dumps({'command':cmd,'exitCode':p.returncode,'wallSeconds':time.monotonic()-t,'stderr':p.stderr},indent=2)+'\n');print('STORAGE48_EXIT',p.returncode,flush=True)
subprocess.run(['/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python','/tmp/rockhop-finish-gate-round48.py'],cwd=r,check=True,timeout=180)
assert p.returncode==0
