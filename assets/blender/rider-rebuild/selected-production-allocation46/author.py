"""Exact hash-pinned author37 adapter; only unsupported target rejection changes.

Parent-only: blender -b -t 2 --python-exit-code 1 --python author.py --
  CONSTRUCTOR46_JSON NEW_OUTPUT_DIRECTORY
No native job is launched by importing this lightweight patch definition.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FROZEN = ROOT/'assets/blender/rider-rebuild/selected-production-constructor37/author.py'
FROZEN_SHA = 'b5ec57c735a1e2e4c030f14d90597097b043fbe59f945793de42bd134e7556cc'
CONSTRUCTOR_SHA = '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741'

# Explicit single-occurrence edits; all remaining frozen qualification executes
# verbatim, including native ancestry, maps, locks, surface/normal/skin gates.
PATCHES = [
    ("selected-production-constructor37'", "selected-production-allocation46'"),
    ("assert receipt['status'] in ['UNACCEPTED_CANDIDATE_AWAITING_NATIVE_QUALIFICATION', 'REJECTED_ALLOCATION_ABOVE_8000']",
     "assert receipt['status'] == 'UNACCEPTED_SCENE_BUDGET_PENDING'"),
    ("assert receipt['recipeSHA256'] == sha(HERE/'construct.mjs')",
     "assert receipt['recipeSHA256'] == sha(HERE/'construct.mjs')\n    assert receipt['constructorAncestry'] == {'path': 'assets/blender/rider-rebuild/selected-production-constructor37/construct.mjs', 'sha256': '"+CONSTRUCTOR_SHA+"'}\n    assert receipt['simplificationTargetIsSoft'] is True and receipt['sceneBudgetPassed'] is False and receipt['allocationPassed'] is False"),
    ("assert len(f) <= spec['full'], 'Allocation exceeds8000; candidate retained unaccepted, no forced reduction'",
     "assert len(f) == receipt['targetTriangles']  # Exact measured output; soft target never awards scene allocation"),
    ("'targetBudget': spec['full']", "'simplificationTargetTriangles': spec['full'], 'sceneBudgetPassed': False"),
    ("'status': 'UNACCEPTED_BEFORE_TRANSFER'", "'status': 'UNACCEPTED_SCENE_BUDGET_PENDING', 'authorAncestry': {'path': str(FROZEN.relative_to(ROOT)), 'sha256': FROZEN_SHA}, 'sceneBudgetPassed': False, 'allocationPassed': False"),
    ("'UNACCEPTED-constructor37-before-transfer.blend'", "'UNACCEPTED-constructor46-before-transfer.blend'"),
    ("'Constructor37.original-position-topology'", "'Constructor46.original-position-topology'"),
    ("'UNACCEPTED_CONSTRUCTOR37_BEFORE_QUALIFICATION'", "'UNACCEPTED_CONSTRUCTOR46_BEFORE_QUALIFICATION'"),
    ("'REJECTED_NATIVE_CONSTRUCTOR37_UNACCEPTED'", "'REJECTED_NATIVE_CONSTRUCTOR46_UNACCEPTED'"),
    ("report['status'] = 'UNACCEPTED_LEFT_BOOT_GEOMETRY_AND_ATLAS_PREPARED'",
     "report['status'] = 'UNACCEPTED_SCENE_BUDGET_PENDING'"),
]


def adapted_source():
    raw = FROZEN.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FROZEN_SHA, 'Frozen author37 changed'
    source = raw.decode()
    for old, new in PATCHES:
        assert source.count(old) == 1, ('Adapter patch drift', old)
        source = source.replace(old, new)
    return source


if __name__ == '__main__':
    namespace = {'__file__': str(Path(__file__).resolve()), '__name__': 'allocation46_native',
                 'FROZEN': FROZEN, 'FROZEN_SHA': FROZEN_SHA}
    exec(compile(adapted_source(), str(FROZEN)+'[allocation46 explicit adapter]', 'exec'), namespace)
    namespace['main']()
