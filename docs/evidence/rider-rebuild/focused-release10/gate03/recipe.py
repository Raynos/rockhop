import hashlib,json,os,shutil,subprocess
from pathlib import Path
root=Path('/Users/raynos/projects/games/rockhop'); dist=root/'dist'; build=root/'harness/out/rider-rebuild/focused-release10/build03'; backup=root/'harness/out/rider-rebuild/focused-release10/pre-gate03-dist';ev=root/'docs/evidence/rider-rebuild/focused-release10/gate03';ev.mkdir(parents=True,exist_ok=False);assert not backup.exists()
metrics=root/'harness/out/metrics/ship-gate.partial.json';old=metrics.read_bytes() if metrics.exists() else None
if dist.exists():dist.rename(backup)
try:
 shutil.copytree(build,dist)
 env=dict(os.environ,TRIALS_BROWSER_BACKEND='metal')
 r=subprocess.run(['pnpm','exec','tsx','harness/gate/ship-gate.ts','--only=boot,clear,crash,restart,bundle,determinism','--jobs=1','--quiet-timing','--quick'],cwd=root,env=env)
 if metrics.exists():(ev/'report.json').write_bytes(metrics.read_bytes())
 (ev/'identity.json').write_text(json.dumps({'exitCode':r.returncode,'build':str(build),'sourceSHA256':'a069b90c847734513ed8c79df596cfcfa0602363e767659655458eb045d319b7','limits':'Partial played/replay gate. Selected cuff surface and physical phone judgment separate.'},indent=2)+'\n')
finally:
 if dist.exists():shutil.rmtree(dist)
 if backup.exists():backup.rename(dist)
 if old is not None:metrics.write_bytes(old)
 elif metrics.exists():metrics.unlink()
raise SystemExit(r.returncode)
