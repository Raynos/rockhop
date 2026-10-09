"""Exact six-pose contact15 measurement with explicit local-paint16 admission.

The new receiver's hashes are read from its actual saved receipt, never guessed.
The original15 inspection/views remain labelled prior evidence only.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
ORIGINAL = ('assets/blender/rider-rebuild/selected-hoodie-joints77/posed_contact15.py',
            'fc543e997f60be4b7591990b370bb54b91dfd5093a15fe2f5486fc42d2f804e0')
PAINT = ('assets/blender/rider-rebuild/selected-hoodie-joints77/shoulder_paint16.py',
         '357a2218909aa98454669d5bb35a8559eaf9154084017c8d9690818b89369cc9')


def main(receipt_path, output):
    path = ROOT/ORIGINAL[0]; assert hashlib.sha256(path.read_bytes()).hexdigest() == ORIGINAL[1]
    assert hashlib.sha256((ROOT/PAINT[0]).read_bytes()).hexdigest() == PAINT[1]
    source = path.read_text()
    for old, new in {
        "receipt['connectedCapBinding']['bodyGuide']": "receipt['localShoulderPaintBinding']['bodyGuide']",
        "prior['receiverReceipt'] == pinfo('receiverReceipt')": "prior['receiverReceipt'] == pinfo('baseline15Receipt')",
        "'SAVED15_SIX_POSE_FINITE_TRIANGLE_CROSSINGS_MEASURED_UNACCEPTED'": "'LOCAL_PAINT16_SIX_POSE_FINITE_TRIANGLE_CROSSINGS_MEASURED_UNACCEPTED'",
        "'inputsAndSourceUnchanged': True, 'rows': rows,": "'inputsAndSourceUnchanged': True, 'rows': rows, 'inspectionAndViewsArePrior15Only': True,",
    }.items():
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    scope = {'__file__': __file__, '__name__': 'frozen_contact15_for16'}
    exec(compile(source, str(path), 'exec'), scope)
    pin, checked, np, pins = (scope[k] for k in ('pin', 'checked', 'np', 'PINS'))
    receipt_path = Path(receipt_path).resolve()
    assert receipt_path == ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77/receiver16/receiver.json'
    receipt = json.loads(receipt_path.read_text()); binding = receipt['localShoulderPaintBinding']
    assert binding['recipe'] == {'path': PAINT[0], 'sha256': PAINT[1]}
    assert binding['input'] == pin(checked('receiverReceipt'))
    assert binding['paint'] == receipt['construction']
    report_path = ROOT/binding['paint']['path']; assert pin(report_path) == binding['paint']
    report = json.loads(report_path.read_text())
    assert report['recipe'] == binding['recipe'] and report['input'] == binding['input'] and report['receiver'] == receipt['receiver']
    arrays_path = ROOT/receipt['receiver']['path']; assert pin(arrays_path) == receipt['receiver']
    before, after = np.load(checked('receiverArrays')), np.load(arrays_path)
    assert all(np.array_equal(before[k], after[k]) for k in before.files if k != 'namedFields')
    ids = after['localPaintVertexIds']
    assert ids.tolist() == report['changedVertexIds'] and len(ids) == report['changedVertices']
    assert np.array_equal(after['prior15NamedFields'], before['namedFields'])
    assert np.array_equal(after['localPaintOldFields'], before['namedFields'][ids])
    assert np.array_equal(after['localPaintNewFields'], after['namedFields'][ids])
    assert np.array_equal(np.flatnonzero(np.any(before['namedFields'] != after['namedFields'], axis=1)), ids)
    pins['baseline15Receipt'] = pins['receiverReceipt']; pins['baseline15Arrays'] = pins['receiverArrays']
    pins['priorContactRecipe'] = ORIGINAL; pins['localPaintRecipe'] = PAINT
    for key, row in (('receiverReceipt', pin(receipt_path)), ('receiverArrays', receipt['receiver']), ('construction', receipt['construction'])):
        pins[key] = (row['path'], row['sha256'])
    scope['main'](output)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    main(*args)
