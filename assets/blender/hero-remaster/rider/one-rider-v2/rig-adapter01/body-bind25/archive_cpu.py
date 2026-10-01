"""Retain exact CPU renderer payloads privately; no production assets or GPU."""
from pathlib import Path
import json,hashlib,shutil
OUT=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind25/morph01')
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind25/morph01')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for folder in ['cpu','baseline-normal01']:
 target=RUN/folder;target.mkdir(parents=True,exist_ok=True)
 for p in sorted((OUT/folder).glob('*.f64')):
  dst=target/p.name;digest=sha(p)
  if dst.exists():assert sha(dst)==digest
  else:shutil.copyfile(p,dst)
  assert sha(dst)==digest;rows.append({'folder':folder,'file':p.name,'privatePath':str(dst),'bytes':p.stat().st_size,'sha256':digest});p.unlink()
archive=OUT/'cpu-buffer-archive.json'
if rows:archive.write_text(json.dumps({'count':len(rows),'buffers':rows,'limits':'Actual CPU Three.js reconstruction payloads; no GPU clips or production assets.'},indent=2)+'\n')
else:
 assert archive.exists()
 for row in json.loads(archive.read_text())['buffers']:assert sha(Path(row['privatePath']))==row['sha256']
print(json.dumps({'archivedOrVerifiedBuffers':json.loads(archive.read_text())['count']}))
