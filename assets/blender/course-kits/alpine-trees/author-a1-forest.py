"""Freeze audited seeded anchors into the owned A1 placement module; no scene RNG is rerun."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
AUDIT = ROOT / 'docs/evidence/course-remaster/alpine-tree-kit/a1-existing-tree-audit.json'
audit = json.loads(AUDIT.read_text())
rows = audit['allOriginalTreePlacements']
assert len(rows) == 276
lines = []
for r in rows:
    m = r['matrix']
    lines.append(f"  ['{r['name']}', {r['index']}, {r['x']:.15g}, {r['z']:.15g}, {m[5]:.15g}, {math.atan2(m[8],m[0]):.15g}],")
template = (HERE/'a1Forest.ts.template').read_text()
source = template.replace('__ANCHORS__', '\n'.join(lines)).replace('__AUDIT_SHA__', hashlib.sha256(AUDIT.read_bytes()).hexdigest())
(ROOT/'src/render/world/zones/a1Forest.ts').write_text(source)
print(f'Authored {len(rows)} frozen A1 anchors; source audit SHA-256 {hashlib.sha256(AUDIT.read_bytes()).hexdigest()}')
