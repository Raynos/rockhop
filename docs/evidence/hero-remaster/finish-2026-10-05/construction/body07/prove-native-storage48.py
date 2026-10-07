"""Freeze a bounded representation for four one-hot FULL anchor weights.

The first harmonic solution remains immutable; this is transport, not retuning.
No native source is opened. All normalized FULL/FOUR fields must stay byte exact.
"""
from pathlib import Path
import hashlib
import json
import numpy as np

root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body07'
source = evidence / 'array-preflight04/frozen-shoulder-fields.npz'
out = evidence / 'native-transport48'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source) == 'dc92e1192a411d0ba90a67ef7144bdf697008164b2f2014c10dff69a149dfd35'
assert not out.exists()
raw = np.load(source)
arrays = {key: raw[key].copy() for key in raw.files}
full, four = arrays['productionFullWeights'], arrays['productionFourWeights']
assert np.isfinite(full).all() and np.isfinite(four).all() and np.all(full >= 0) and np.all(four >= 0)
rows, columns = np.nonzero(full > 1)
assert rows.tolist() == [36, 111, 4588, 4661]
assert columns.tolist() == [22, 22, 3, 3]
assert np.all(full[rows, columns] == np.float32(1.0000001192092896))
assert np.all(np.count_nonzero(full[rows], axis=1) == 1)
assert four.max() <= 1
arrays['trial45RawProductionFullReference'] = full.copy()
full[rows, columns] = np.float32(1)
assert full.max() <= 1
checks = {}
for title in ['Full', 'Four']:
    original = raw['production' + title + 'Weights'].astype(np.float64)
    bounded = arrays['production' + title + 'Weights'].astype(np.float64)
    first = original / original.sum(axis=1)[:, None]
    second = bounded / bounded.sum(axis=1)[:, None]
    assert np.isfinite(first).all() and np.array_equal(first, second)
    checks[title.lower()] = {'normalizedFloat64ArrayByteExact': first.tobytes() == second.tobytes(),
        'normalizedMaxDifference': float(abs(first - second).max()),
        'normalizedArraySHA256': hashlib.sha256(first.tobytes()).hexdigest()}
for key in raw.files:
    if key != 'productionFullWeights':
        assert np.array_equal(raw[key], arrays[key]), key
changed = np.argwhere(full != raw['productionFullWeights'])
assert changed.tolist() == [[36, 22], [111, 22], [4588, 3], [4661, 3]]
out.mkdir()
np.savez_compressed(out / 'native-storage-fields.npz', **arrays)
report = {'status': 'ROOT_ADMITS_FOUR_ONE_HOT_STORAGE_REPRESENTATIONS_NOT_NATIVE_PASS',
    'round': 48, 'recipeSHA256': sha(Path(__file__)),
    'trial45': {'path': str(source.relative_to(root)), 'sha256': sha(source)},
    'storageFields': {'path': str((out / 'native-storage-fields.npz').relative_to(root)), 'sha256': sha(out / 'native-storage-fields.npz')},
    'changes': [{'nativeID': int(v), 'joint': str(raw['boneNames'][j]), 'trial45Raw': float(raw['productionFullWeights'][v,j]),
                 'storageRaw': float(full[v,j]), 'otherPositiveInfluences': 0} for v,j in zip(rows, columns)],
    'all9183NormalizedFields': checks,
    'mechanism': 'Four sole-positive FULL anchor memberships exceed1 by one Float32 step. Represent these as1. Their normalized51-vector is the same exact unit vector for every possible own51 pose; all FOUR/raw controls/other candidate fields remain exact. No harmonic solve or global normalization.',
    'rawReferences': 'Original frozen trial45 raw FULL retained separately in storage NPZ. Original body06/body52 raw FULL controls remain immutable.',
    'scope': 'Only the four declared one-hot FULL memberships change storage; they are within the already-admitted330 effective/438 scope. No source geometry/rig/UV/normals/materials/pose/control mutation.',
    'nativeNext': 'Next native author must measure actual RNA weight bounds and record actual mismatches before assertion; exact bounded storage fields must save/reopen. No silent clamp or normalized-source claim.',
    'limits': ['Array transport proof only. Actual cause of failed47 readback remains unmeasured; native API behavior not yet observed.',
               'Exact normalized fields prove identical weighted LBS inputs under measured native normalization; shader/conditioner/bind consumption and physical appearance remain separate.',
               'No native master, art, whole contacts, clothing, engine or device acceptance.']}
(out / 'scope.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'storageFieldsSHA256': report['storageFields']['sha256'], 'fourOneHotMemberships': 4, 'normalizedFieldsMaxDifference': 0}))
