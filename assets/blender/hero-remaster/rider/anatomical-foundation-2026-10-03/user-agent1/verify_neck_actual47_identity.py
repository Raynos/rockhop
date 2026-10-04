"""Bound actual Blender pose reconstruction error against every recorded K.

This complements the actual evaluated/manual parity, avoiding an assumption
that Blender matrix-basis reconstruction preserves the requested game field.
No source edits, new pose evaluation, capture or controller simulation.
"""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[6]
ev = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
out = ev / 'neck-interface99'
qa = root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
motion = json.loads((out / 'motion.json').read_text())
pose_path = out / 'pose-witnesses.npz'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(pose_path) == motion['archiveSHA256']
pose = np.load(pose_path)
freeze = json.loads((ev / 'neck-interface98/triangulation.json').read_text())
native = root / freeze['native']
field_path = native.parent / 'triangulated-neck-fields.npz'
assert sha(native) == freeze['nativeSHA256'] and sha(field_path) == freeze['fieldsSHA256']
f = np.load(field_path)
e = np.load(qa / 'body52/export-fields.npz')
actual_path = qa / 'garment47/first.weights.ndjson.gz'
with gzip.open(actual_path, 'rt') as stream: actual = [json.loads(line) for line in stream]
normalize = lambda name: name.replace('.', '').replace('_', '')
order = [list(map(normalize, e['jointNames'])).index(normalize(name)) for name in pose['boneNames']]
world = pose['rigWorldRows']; inv_world = np.linalg.inv(world)
C = np.array([[1., 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
sparse = {}
for key in ['body', 'head']:
    for label in ['full', 'four']:
        w = f[key + label.title() + 'Weights'].astype(float); w /= w.sum(axis=1)[:, None]
        sparse[key, label] = [(np.flatnonzero(w[:, j] > 0), w[w[:, j] > 0, j]) for j in range(51)]
rows = []
for i in np.flatnonzero(pose['domains'] == 'actual47'):
    source_id = int(pose['sourceIndices'][i])
    K = np.array(actual[source_id - 1]['matrices']).reshape(51, 4, 4).transpose(0, 2, 1)[order]
    requested = inv_world @ C.T @ K @ C @ world
    delta = pose['rigLocalSkinMatrices'][i] - requested
    row = {'sourceIndex': source_id, 'maximumMatrixComponentDifference': float(np.abs(delta).max()), 'parts': {}}
    record = next(r for r in motion['frames'] if r['domain'] == 'actual47' and r['sourceIndex'] == source_id)
    for key in ['body', 'head']:
        rest = np.column_stack([f[key + 'RestXYZ'], np.ones(len(f[key + 'RestXYZ']))])
        for label in ['full', 'four']:
            difference = np.zeros_like(rest, dtype=float)
            for j, (ids, weights) in enumerate(sparse[key, label]):
                if len(ids): difference[ids] += (rest[ids] @ delta[j].T) * weights[:, None]
            error = np.linalg.norm((difference @ world.T)[:, :3], axis=1)
            bound = float(error.max()) + record['variants'][label]['parts'][key]['manualNativeLBSParityMaxM']
            row['parts'][key + label] = {'matrixReconstructionPositionErrorMaxM': float(error.max()),
                'worstVertex': int(np.argmax(error)), 'actualEvaluatedVsRecordedFieldErrorUpperBoundM': bound,
                'within2Micrometres': bound <= 2e-6}
    rows.append(row)
assert len(rows) == 703 and [r['sourceIndex'] for r in rows] == list(range(1, 704))
summary = {key + label: {'maximumActualEvaluatedVsRecordedFieldErrorUpperBoundM': max(r['parts'][key + label]['actualEvaluatedVsRecordedFieldErrorUpperBoundM'] for r in rows),
    'outside2MicrometreBarSamples': sum(not r['parts'][key + label]['within2Micrometres'] for r in rows)} for key in ['body', 'head'] for label in ['full', 'four']}
passed = all(r['outside2MicrometreBarSamples'] == 0 for r in summary.values())
report = {'status': 'RECORDED_ACTUAL47_IDENTITY_ERROR_BOUNDED' if passed else 'FAILED_RECORDED_ACTUAL47_IDENTITY_ERROR_BAR',
    'recipeSHA256': sha(__file__), 'motionSHA256': sha(out / 'motion.json'), 'archiveSHA256': sha(pose_path),
    'fieldSHA256': sha(field_path), 'actual47SHA256': sha(actual_path), 'samples': 703, 'summary': summary, 'rows': rows,
    'method': 'Every703recorded primary51K converted through the same glTF/native/file frame. Linear normalized skinning of actual-rig minus requested matrices bounds per-vertex error. Add independently measured actual evaluated/manual native parity by triangle inequality.',
    'limits': ['Upper bound, not a byte-identical game trace or full-control runtime trace. No new source pose/controller evaluation/capture.',
        'Seam precision, local contact/collapse and art remain separate. All M0-M5 open.']}
(out / 'actual47-identity.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'summary': summary}, indent=2))
