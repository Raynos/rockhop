"""Parent independent replay of the rejected donor root transform."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
r = json.loads(Path(__file__).with_name('receipt.json').read_text())
for section in ('selectedInputPins', 'filesReadPins', 'imagesViewed'):
    for row in r[section]:
        assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
s = np.load(ROOT / 'docs/evidence/rider-rebuild/glove-charts01/atlas01/source-atlas.npz')
h = np.load(ROOT / 'docs/evidence/rider-rebuild/glove-native02-fit/target01/native-hand-R.npz')
b = np.load(ROOT / 'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz')
names = b['jointNames'].tolist()
head = lambda name: b['jointHeads'][names.index(name)]
unit = lambda value: value / np.linalg.norm(value)
cuff = s['vertices'][s['cuffBoundaryVertexIds']].mean(0)
old_forward = unit(s['middle_centers'][0] - cuff)
old_radial = unit(np.array([1., 0, 0]) - old_forward * old_forward[0])
old_frame = np.stack([old_radial, old_forward, unit(np.cross(old_radial, old_forward))], 1)
forward = unit(head('DEF-f_middle.01.R') - head('DEF-hand.R'))
radial = head('DEF-f_index.01.R') - head('DEF-f_pinky.01.R')
radial = unit(radial - forward * np.dot(radial, forward))
frame = np.stack([radial, forward, unit(np.cross(radial, forward))], 1)
rs = np.linalg.norm(head('DEF-f_index.01.R') - head('DEF-f_pinky.01.R')) / np.linalg.norm(s['index_centers'][0] - s['pinky_centers'][0])
ls = np.linalg.norm(head('DEF-f_middle.01.R') - h['cuffOrigin']) / np.linalg.norm(s['middle_centers'][0] - cuff)
matrix = np.einsum('ij,kj,j->ik', frame, old_frame, np.array([rs, ls, rs * .68]))
assert np.max(abs(matrix - np.asarray(r['measurements']['palmAffine']))) < 1e-12
for row in r['measurements']['rightHandRoots']:
    digit = row['digit']
    point = np.einsum('ij,j->i', matrix, s[digit + '_centers'][0] - cuff) + h['cuffOrigin']
    bone = 'DEF-thumb.01.R' if digit == 'thumb' else 'DEF-f_' + digit + '.01.R'
    error = float(np.linalg.norm(point - head(bone)))
    assert abs(error - row['rootControlResidualMeters']) < 1e-12
    print(digit, round(error * 1000, 6), 'mm')
print('Parent replay: all pins and five root residuals match')
