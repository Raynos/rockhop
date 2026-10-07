"""Verify required immutable pause inputs; never launch or repair anything."""
import hashlib
import json
from pathlib import Path

root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
manifest = json.loads(Path(__file__).with_name('resume-inputs.json').read_text())
failures = []
for row in manifest['inputs']:
    path = root / row['path']
    if not path.is_file():
        failures.append({'path': row['path'], 'failure': 'MISSING'})
        continue
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    if digest.hexdigest() != row['sha256']:
        failures.append({'path': row['path'], 'failure': 'HASH_MISMATCH'})
print(json.dumps({'status': 'FAIL' if failures else 'FROZEN_INPUTS_EXACT',
                  'checkedInputs': len(manifest['inputs']), 'failures': failures}))
raise SystemExit(bool(failures))
