"""Compare exported four-weight Three.js LBS to full-weight Blender source."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source', required=True)
ap.add_argument('--evidence', required=True)
a = ap.parse_args()
source, evidence = Path(a.source), Path(a.evidence)
sample_path = evidence / 'export-sampled-positions.json'
samples = json.loads(sample_path.read_text())
manifest = json.loads((evidence / 'export-manifest.json').read_text())
time_pose = {'0': 'native_A', '1': 'neutral', '2': 'T', '4': 'forward',
             '5': 'bent_elbows', '6': 'raised', '7': 'asymmetric'}


def load(label, region):
    p = source / f'{label}-{region}.npz'
    vv = np.load(p)['verticesBlenderWorldM']
    return vv[:, [0, 2, 1]] * np.array([1, 1, -1])


rows = []
for region, prefix in [('body', 'Canonical_'), ('cloth', 'Separate_fitted_sweatshirt')]:
    name = next(n for n in samples['0'] if n.startswith(prefix))
    native = load('native_A', region)
    exported = np.array(samples['0'][name]).reshape(-1, 3)
    buckets = {}
    for i, p in enumerate(native):
        buckets.setdefault(tuple(np.rint(p * 1e5).astype(int)), []).append(i)
    mapping, rest_errors = [], []
    for p in exported:
        key = np.rint(p * 1e5).astype(int)
        choices = list(itertools.chain.from_iterable(
            buckets.get(tuple(key + delta), []) for delta in itertools.product([-1, 0, 1], repeat=3)))
        if not choices:
            raise RuntimeError('Export rest vertex has no source within spatial bucket')
        distances = np.linalg.norm(native[choices] - p, axis=1)
        best = int(np.argmin(distances))
        if distances[best] > 3e-6:
            raise RuntimeError(f'Rest mismatch {distances[best]}m')
        mapping.append(choices[best])
        rest_errors.append(float(distances[best]))
    mapping = np.array(mapping, dtype=np.int32)
    np.savez_compressed(evidence / f'{region}-export-to-native.npz',
                        nativeVertexForExportRow=mapping, restErrorsM=np.array(rest_errors))
    pose_rows = []
    for key, label in time_pose.items():
        reference = load(label, region)[mapping]
        actual = np.array(samples[key][name]).reshape(-1, 3)
        errors = np.linalg.norm(reference - actual, axis=1)
        pose_rows.append({'pose': label, 'clipTimeS': float(key) + manifest['clipTimeline']['firstKeyS'],
            'maxM': float(errors.max()), 'p99M': float(np.quantile(errors, .99)),
            'rmsM': float(np.sqrt((errors ** 2).mean())),
            'verticesAbove100um': int((errors > 1e-4).sum()),
            'verticesAbove1mm': int((errors > 1e-3).sum())})
    rows.append({'region': region, 'mesh': name, 'nativeVertices': len(native),
                 'exportedRows': len(exported), 'restMappingMaxM': max(rest_errors), 'poses': pose_rows})
report = {'status': 'MEASURED full native weights versus exported four-weight LBS; unaccepted',
    'exportSHA256': manifest['sha256'], 'samplePositionsSHA256': hashlib.sha256(sample_path.read_bytes()).hexdigest(),
    'rows': rows, 'fourWeightExportWarning': True,
    'limits': ['Measures seven authored source endpoints; continuous interpolation parity not established.',
               'UV/normal split rows mapped by measured rest position within3micrometres.',
               'Source deformation quality, body/cloth collision, art and device gates independent.']}
(evidence / 'four-weight-parity.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
