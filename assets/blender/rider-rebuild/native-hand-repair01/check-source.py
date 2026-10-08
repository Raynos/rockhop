"""Small deterministic checks for native hand recipe; no Blender/heat solve."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'docs/evidence/rider-rebuild/glove-charts01'
spec = importlib.util.spec_from_file_location('field_math', Path(__file__).with_name('field-math.py'))
math = importlib.util.module_from_spec(spec); spec.loader.exec_module(math)
receipt = json.loads((BASE / 'rebind-domain01/rebind-domain.json').read_text())
for record in receipt['inputs'] + [receipt['arrays']]:
    assert hashlib.sha256((ROOT / record['path']).read_bytes()).hexdigest() == record['sha256'], record['path']
domain = np.load(ROOT / receipt['arrays']['path'])
alpha = domain['newFieldBlendAlpha']
assert np.sum(alpha > 0) == 1446 and np.sum(alpha == 0) == 9136
proposal = np.load(BASE / 'medial-correction01/proposed-joints.npz')
correction = json.loads((BASE / 'medial-correction01/medial-correction.json').read_text())
assert hashlib.sha256((BASE / 'medial-correction01/medial-correction.json').read_bytes()).hexdigest() == '4047b86c8935a303d0158fedb83d3a8cfc2032162f86d8756dc4e9023f2be623'
names = proposal['jointNames'].tolist()
diagnostic_path=ROOT/'docs/evidence/rider-rebuild/native-hand-repair01/edit-roundtrip01/rest-byte-comparison.npz'
assert hashlib.sha256(diagnostic_path.read_bytes()).hexdigest()=='bbb8ae3342b471852baf46a2e49513acca5ab0bf74ba419f6f4ced41bbfa3731'
diagnostic=dict(np.load(diagnostic_path))
assert np.array_equal(diagnostic['jointNames'],proposal['jointNames'])
for field in ('heads','tails','matrices'):
    assert np.array_equal(diagnostic['noOp_source_'+field+'_double'],diagnostic['noOp_result_'+field+'_double'])
scope={field:[names[i] for i in np.flatnonzero(np.any(diagnostic['correction_source_'+field+'_double']!=diagnostic['correction_result_'+field+'_double'],axis=tuple(range(1,diagnostic['correction_source_'+field+'_double'].ndim))))] for field in ('heads','tails','matrices')}
assert len(scope['heads'])==4 and len(scope['tails'])==4 and len(scope['matrices'])==14
frames = []
for side in ('L', 'R'):
    for stem in ('palm.04', 'f_pinky.01', 'f_middle.01', 'f_middle.02'):
        name = 'DEF-' + stem + '.' + side; i = names.index(name)
        frame = math.proper_frame(proposal['heads'][i], proposal['tails'][i], correction['palmNormals'][side])
        axis = math.flex_axis(proposal['heads'][i], proposal['tails'][i], correction['palmNormals'][side], frame)
        assert abs(np.linalg.norm(axis) - 1) < 1e-12
        frames.append(name)
# Deliberately unnormalized old FULL must survive outside the source-ID domain.
old_full = [[['a', .4], ['b', .3]], [['a', .4], ['b', .3]], [['a', .4], ['b', .3]]]
old_four = [[['a', 4/7], ['b', 3/7]] for _ in range(3)]
new = [[['c', .2], ['d', .2], ['e', .2], ['f', .2], ['g', .2]] for _ in range(3)]
full, four, loss = math.blend_fields(old_full, old_four, new, [0, .5, 1], list('abcdefg'), [])
assert full[0] is old_full[0] and four[0] is old_four[0]
assert abs(sum(w for _, w in full[0]) - .7) < 1e-15
assert [n for n, _ in four[2]] == ['c', 'd', 'e', 'f'] and abs(loss[2] - .2) < 1e-15
assert all(abs(sum(w for _, w in row)-1) < 1e-15 for row in full[1:] + four[1:])
print(json.dumps({'status':'SOURCE_MATH_ONLY_PASS','sourcePins':len(receipt['inputs'])+1,
    'properAffectedFrames':frames,'domain':1446,'verbatimRows':9136,
    'checks':['zero-alpha identity, unnormalized preservation, normalization, stable top4 tie, removed mass, proper anatomical frames'],
    'nativeRestDiagnosticScope':scope,'acceptedArt':False}))
