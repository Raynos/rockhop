"""Reproduce float32 Newell cancellation from a pinned Blender witness receipt."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
source, out = Path(args.input), Path(args.out)
assert not out.exists()
witness = json.loads(source.read_text())
f32 = lambda x: struct.unpack('f', struct.pack('f', x))[0]
distance = lambda a, b: math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def newell(xyz, rounded):
    cast = f32 if rounded else float
    total, terms = [0.0, 0.0, 0.0], []
    for i in range(len(xyz)):
        previous, current = xyz[i - 1], xyz[i]
        term = [cast(cast(previous[k] - current[k]) *
                     cast(previous[(k + 1) % 3] + current[(k + 1) % 3]))
                for k in (1, 2, 0)]
        terms.append(term)
        total = [cast(a + b) for a, b in zip(total, term)]
    length = math.sqrt(sum(value * value for value in total))
    return {'terms': terms, 'sum': total, 'normal': [value / length for value in total]}

records = {}
for field, record in witness['records'].items():
    measured = record['moving']
    single, double = newell(measured['localXYZ'], True), newell(measured['localXYZ'], False)
    error = distance(single['normal'], measured['faceNormalLocal'])
    assert error < 1e-6
    assert record['movingCornerToFaceMaximumVectorError'] < 1e-6
    assert measured['packedCustomNormals'] == [[0, 0], [0, 0], [0, 0]]
    assert record['rawDeformMemberships'] == [{'head': 1.0}] * 3
    assert record['maximumManualNativeLocalPositionErrorM'] < 5e-8
    records[field] = {'newellFloat32': single, 'newellFloat64': double,
                      'float32NewellToActualFaceVectorError': error,
                      'float64NewellToDirectCrossVectorError': distance(double['normal'], measured['localCrossFloat64']['normal']),
                      'actualFaceToDirectFloat32CrossVectorError': record['movingFaceToCrossVectorError'],
                      'automaticCornersToActualFaceMaximumVectorError': record['movingCornerToFaceMaximumVectorError'],
                      'linearSkinNormalToNativeCornerMaximumVectorError': record['maximumLinearNormalVectorError'],
                      'nativeToManualPositionMaximumErrorM': record['maximumManualNativeLocalPositionErrorM'],
                      'restTriangleMinimumAltitudeM': record['rest']['localCrossFloat64']['minimumAltitudeM']}
report = {'status': 'UNACCEPTED_SINGLE_WITNESS_NUMERICAL_CAUSE_REPRODUCED',
          'input': str(source), 'inputSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'mechanism': 'Float32 Newell accumulation subtracts milliscale local-coordinate products to nanometre-squared area. Cancellation perturbs the recomputed automatic face normal; packed custom_normal[0,0] uses the automatic fan normal, and these three evaluated corner normals follow this face.',
          'records': records,
          'limits': ['This reproduction explains only rigid head native triangle61196/polygon61151 at saved turn244.',
                     'Position parity does not grant normal parity. Maximum whole-head/body errors near2 remain unresolved and their parity gates remain failed.',
                     'No tolerance was relaxed and no geometry, normals, weights, bind, animation or player asset was changed.',
                     'CPU/native normal diagnosis grants no GPU, moving-art, contact or device acceptance.']}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
print(json.dumps({field: record['float32NewellToActualFaceVectorError'] for field, record in records.items()}))
