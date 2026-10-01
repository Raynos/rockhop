"""Freeze diagnostic buffers privately with exact SHA receipts."""
from pathlib import Path
import hashlib,json,shutil
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind16')
private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind16')
for folder in ['baseline-cpu','baseline-cpu-affine02','localized-dq-cpu']:
    root=base/folder; target=private/folder;target.mkdir(parents=True,exist_ok=True); rows=[]
    for p in sorted(root.glob('*.f64')):
        q=target/p.name;old=p.read_bytes();sha=hashlib.sha256(old).hexdigest()
        if q.exists():assert hashlib.sha256(q.read_bytes()).hexdigest()==sha
        else:shutil.copy2(p,q)
        assert hashlib.sha256(q.read_bytes()).hexdigest()==sha
        rows.append({'file':p.name,'bytes':len(old),'sha256':sha,'privatePath':str(q)})
    if rows:
        (root/'buffer-archive.json').write_text(json.dumps({'rows':rows,'exact':True},indent=2)+'\n')
        for p in root.glob('*.f64'):p.unlink()
    print(folder,len(rows))
