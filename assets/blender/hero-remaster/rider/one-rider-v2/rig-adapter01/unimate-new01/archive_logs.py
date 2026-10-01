"""Keep exact generated logs compressed, plus whitespace-clean review text."""
from pathlib import Path
import gzip,json,hashlib
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/unimate-new01');rows=[]
for p in sorted(O.glob('*-log.txt')):
 raw=p.read_bytes();clean=b'\n'.join(line.rstrip() for line in raw.split(b'\n'))
 if clean==raw:continue
 archive=p.with_suffix('.txt.gz');assert not archive.exists();archive.write_bytes(gzip.compress(raw,mtime=0));p.write_bytes(clean);assert gzip.decompress(archive.read_bytes())==raw;rows.append({'rawCompressed':str(archive),'rawSHA256':hashlib.sha256(raw).hexdigest(),'reviewText':str(p),'reviewSHA256':hashlib.sha256(clean).hexdigest(),'normalization':'Trailing whitespace only; exact raw bytes retained losslessly'})
(O/'log-archive.json').write_text(json.dumps(rows,indent=2)+'\n')
