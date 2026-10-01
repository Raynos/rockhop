"""Archive exact candidate CPU payloads privately, without changing source assets."""
import json,shutil
from pathlib import Path
from common import RUN,OUT,sha
folder=OUT/'candidate-cpu';target=RUN/'candidate-cpu';target.mkdir(parents=True,exist_ok=True);rows=[]
for p in sorted(folder.glob('*.f64')):
 dst=target/p.name;digest=sha(p.read_bytes())
 if dst.exists():assert sha(dst.read_bytes())==digest
 else:shutil.copyfile(p,dst)
 assert sha(dst.read_bytes())==digest;rows.append({'file':p.name,'privatePath':str(dst),'bytes':p.stat().st_size,'sha256':digest});p.unlink()
archive=OUT/'buffer-archive.json'
if rows:archive.write_text(json.dumps({'count':len(rows),'buffers':rows,'limits':'CPU actual recorded-pose payloads only; no GPU clips or production assets.'},indent=2)+'\n')
else:
 assert archive.exists()
 for r in json.loads(archive.read_text())['buffers']:assert sha(Path(r['privatePath']).read_bytes())==r['sha256']
print(json.dumps({'archivedOrVerifiedBuffers':json.loads(archive.read_text())['count']}))
