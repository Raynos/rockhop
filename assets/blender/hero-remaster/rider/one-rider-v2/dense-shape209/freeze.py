#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path('/Users/raynos/projects/games/rockhop')
ASSET = ROOT / 'assets/blender/hero-remaster/rider/one-rider-v2/dense-shape209'
OUT = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/dense-shape209'
AUDIT = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/native-extractor-audit208/freeze.json'


def pin(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


prior = json.loads(AUDIT.read_text())
for item in prior['inputPins']:
    assert pin(Path(item['path'])) == item
record = {'status': 'UNEXECUTED_CONDITIONAL_DENSE_ONLY256_PROXY_DRAFT',
          'modelExecutions': 0, 'gpuJobs': 0, 'installedSourceEdits': False,
          'inputPins': prior['inputPins'] + [pin(AUDIT)],
          'ownedFiles': [pin(p) for p in [ASSET / 'feasibility.py', ASSET / 'freeze.py',
                                         OUT / 'README.md', OUT / 'feasibility.json']],
          'actual207ReceiptIndependentlyInspected': False,
          'admissionOwner': '/root', 'matched380CurrentlyAdmitted': False}
target = OUT / 'freeze.json'
target.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(pin(target)))
