"""Preserve CPU proof buffers privately, keeping hash-indexed manifests in Git."""
from pathlib import Path
import json,hashlib,shutil
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34')
private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu');private.mkdir(parents=True,exist_ok=True)
rows=[]
for p in sorted((base/'candidate-cpu').glob('*.f64')):
 dest=private/p.name
 if dest.exists():assert dest.read_bytes()==p.read_bytes()
 else:shutil.copy2(p,dest)
 rows.append({'file':p.name,'privatePath':str(dest),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});p.unlink()
(base/'buffer-archive.json').write_text(json.dumps({'count':len(rows),'buffers':rows,'limits':'Actual recorded-state CPU reconstruction. Private unaccepted fresh-rig mapping, no moving appearance claim.'},indent=2)+'\n')
