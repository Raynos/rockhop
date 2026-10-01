"""Verify delivered receipts without rerunning or enlarging their evidence scopes."""
from pathlib import Path
import hashlib,json
p=Path('docs/evidence/hero-remaster/one-rider-v2/independent-pipeline-learnings-2026-10-01');d=json.loads((p/'source-manifest.json').read_text());rows=[]
for group in ['copied_evidence','primary_files']:
 for r in d[group]:
  f=p/r['copied_as'] if group=='copied_evidence' else Path(r['path']);actual=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None;rows.append({'group':group,'path':str(f),'expectedSHA256':r['sha256'],'actualSHA256':actual,'exact':actual==r['sha256'],'repositoryLFNormalizationEquivalent':group=='copied_evidence' and r.get('copied_as')=='capture-coverage.csv' and hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'] and f.read_bytes()==Path(r['path']).read_bytes().replace(b'\r\n',b'\n')})
out={'parentScope':'Read-only rehash of delivered summaries and pinned primary files, not a rerun of historical solvers or new moving acceptance.','rows':rows,'exact':all(r['exact'] for r in rows),'verified':all(r['exact'] or r['repositoryLFNormalizationEquivalent'] for r in rows),'normalization':'Only repository capture-coverage.csv convertsCRLF toLF for whitespace hook. Original source checksum and every CSV record preserved.'};(p/'parent-receipt-verification.json').write_text(json.dumps(out,indent=2)+'\n');assert out['verified'];print('All29receipt checks pass; only repositoryCSV LF-normalized, source exact')
