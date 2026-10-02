#!/usr/bin/env python3
"""Freeze only the owned CPU audit and exact synthetic outputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path('/Users/raynos/projects/games/rockhop')
ASSET = ROOT / 'assets/blender/hero-remaster/rider/one-rider-v2/native-extractor-audit208'
EVIDENCE = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/native-extractor-audit208'


def check(item):
    path = Path(item['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
    assert path.stat().st_size == item['bytes']


def pin(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


report = json.loads((EVIDENCE / 'report.json').read_text())
for item in report['sources']:
    check(item)
private = [case['arrays'] for case in report['cases']]
for item in private:
    check(item)
freeze = {'status': report['status'], 'sourceUnchanged': True,
          'inputPins': report['sources'], 'privateOutputs': private,
          'ownedFiles': [pin(p) for p in [ASSET / 'reproduce.py', ASSET / 'freeze.py',
                                         EVIDENCE / 'README.md', EVIDENCE / 'report.json']],
          'geometryAttempts': 0, 'modelExecutions': 0, 'gpuWorkloads': 0,
          'actual207DiagnosisAssessed': False}
path = EVIDENCE / 'freeze.json'
path.write_text(json.dumps(freeze, indent=2) + '\n')
print(json.dumps(pin(path)))
