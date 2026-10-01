"""Retain SHA-proven CPU payloads privately; never put model buffers in Git."""
import json,shutil
from common import RUN,OUT,sha
rows=[]
for folder in ['baseline-cpu','candidate-cpu']:
 target=RUN/folder;target.mkdir(parents=True,exist_ok=True)
 for p in sorted((OUT/folder).glob('*.f64')):
  dst=target/p.name;digest=sha(p.read_bytes())
  if dst.exists():assert sha(dst.read_bytes())==digest
  else:shutil.copyfile(p,dst)
  assert sha(dst.read_bytes())==digest;rows.append({'folder':folder,'file':p.name,'privatePath':str(dst),'bytes':p.stat().st_size,'sha256':digest});p.unlink()
archive=OUT/'buffer-archive.json'
if rows:archive.write_text(json.dumps({'buffers':rows,'count':len(rows),'limits':'CPU source/pose payloads, not production assets.'},indent=2)+'\n')
else:
 assert archive.exists()
 for row in json.loads(archive.read_text())['buffers']:assert sha(__import__('pathlib').Path(row['privatePath']).read_bytes())==row['sha256']
print(json.dumps({'archivedOrVerifiedBuffers':len(json.loads(archive.read_text())['buffers'])}))
