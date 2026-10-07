"""Read-only fixed-point skin protocol proof; no bpy, scene, export or render."""
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[4]
source = root / 'harness/out/rider-rebuild/construction01/rig04/weights-four.json'
exporter = Path('/Applications/Blender.app/Contents/Resources/5.2/scripts/addons_core/io_scene_gltf2/blender/exp')
pins = {'primitive_extract.py': '55e14cbe849b0c4ec5545c85a1aae3d8c2c7d65eade67de43eb1a43b05738684',
        'primitive_attributes.py': '815331d39cdf06e73ae110e9921ebfc8cb37825290843cbcbf4d1a7559899e5d'}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert all(sha(exporter / name) == digest for name, digest in pins.items())
output = Path(sys.argv[1]).resolve(); assert not output.exists()
rows = json.loads(source.read_text())
grid = 1 << 24; minimum = math.floor(.0001 * grid) + 1
removed, max_delta, max_rounding, changed, corrections, actual = [], 0., 0., 0, 0, []
for field in rows:
    original = {name: float(np.float32(weight)) for name, weight in field}
    kept = sorted([(name, weight) for name, weight in original.items() if weight > .0001])
    total = sum(weight for _, weight in kept)
    ideal = [weight / total * grid for _, weight in kept]
    counts = [max(minimum, math.floor(value)) for value in ideal]
    remainder = grid - sum(counts)
    if remainder > 0:
        for i in sorted(range(len(kept)), key=lambda i: (-(ideal[i] - counts[i]), kept[i][0]))[:remainder]:
            counts[i] += 1
    elif remainder < 0:
        i = max(range(len(kept)), key=lambda i: (counts[i], kept[i][0]))
        counts[i] += remainder; corrections += 1
    assert sum(counts) == grid and all(value >= minimum for value in counts)
    result = {name: float(np.float32(count / grid)) for (name, _), count in zip(kept, counts)}
    values = np.zeros(4, dtype=np.float32); values[:len(kept)] = list(result.values())
    for permutation in itertools.permutations(values):
        array = np.asarray(permutation, dtype=np.float32).reshape(1, 4)
        assert array.sum(axis=1)[0] == 1
        assert np.array_equal(array, array / array.sum(axis=1).reshape(-1, 1))
    removed.append(sum(weight for _, weight in original.items() if weight <= .0001))
    delta = max(abs(original.get(name, 0) - result.get(name, 0)) for name in set(original) | set(result))
    max_delta = max(max_delta, delta); changed += bool(delta)
    max_rounding = max(max_rounding, max(abs(weight / total - result[name]) for name, weight in kept))
    actual.append(sorted(result.items()))
report = {'accepted': False, 'kind': 'read-only proposed canonical final FOUR protocol proof',
          'validatorSHA256': sha(__file__), 'frozenFields': {'path': str(source), 'sha256': sha(source)},
          'installedExporter': [{'path': str(exporter / name), 'sha256': digest} for name, digest in pins.items()],
          'cutoff': .0001, 'cutoffComparison': 'drop weight <= cutoff', 'gridDenominator': grid,
          'rows': len(rows), 'dropAffectedRows': sum(value > 0 for value in removed),
          'maximumRemovedMass': max(removed), 'maximumNamedWeightDelta': max_delta,
          'gridQuantizationMaximumAbsoluteDelta': max_rounding, 'normalizationChangedRows': changed,
          'minimumRetainedGridCount': minimum, 'minimumFloorCorrectionRows': corrections,
          'everyFOUROrderingFloat32SumExactlyOne': True, 'exporterNormalizationByteNoOp': True,
          'canonicalNamedFieldSHA256': hashlib.sha256(json.dumps(actual, separators=(',', ':')).encode()).hexdigest(),
          'rejectedDominantOnlyULPCandidate': {'sourceID': 1922, 'mechanism': 'dominant-only nextafter adjustment',
              'oscillatingFloat32Sums': [1.0000001192092896, .9999999403953552], 'noNativeMutation': True},
          'limits': ['Frozen fields only; final joined face/garments/gloves still require measured operator/readback.',
                     'This read-only protocol proof does not change the frozen source or certify deformation/art.']}
output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
