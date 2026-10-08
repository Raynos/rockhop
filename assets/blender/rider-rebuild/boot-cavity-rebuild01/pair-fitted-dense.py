"""Independent original dense detail unit after a committed valid boot fit.

Never starts dense work for failed geometry. Original source inner-only cuts,
corner artwork and normals retain exact lineage; no compact UV fallback.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
DENSE = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/boots/cleaned-donor.npz'
HELPER = Path(__file__).with_name('cavity-geometry.py')
LINEAGE = Path(__file__).with_name('dense-cavity-lineage.py')
PINS = {DENSE: '9849de6444632c2dcd1e1d76fda42ac27a7cbe8c7d2c0263ab2082e24b94777f',
        HELPER: 'a961bc0c408cc87d1acb000e475e2cc9438eb231de3e343179b0c385c7ab0515',
        LINEAGE: 'a2c3516bf4084dfa291e9dafaa617159a11b22040b3ebfe51bcde59205ee62b1'}
SHA = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 2
fit_root, out = map(lambda path: Path(path).resolve(), args)
assert fit_root.is_relative_to(ROOT / 'harness/out/rider-rebuild')
assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild')
out.mkdir(parents=True, exist_ok=False)
report = {'accepted': False, 'status': 'RUNNING_INDEPENDENT_DENSE_SOURCE_PAIR',
          'recipeSHA256': SHA(__file__), 'fitReceiptSHA256': SHA(fit_root / 'fit.json'),
          'boots': [], 'limits': ['Dense original ancestry unit; no material bake, motion or art acceptance.',
                                 'Fitted geometry/fields/rest and original masters remain unchanged.']}

def save():
    (out / 'dense-pair.json').write_text(json.dumps(report, indent=2) + '\n')

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

try:
    assert all(SHA(path) == digest for path, digest in PINS.items())
    receipt = json.loads((fit_root / 'fit.json').read_text())
    assert receipt['status'] == 'SOURCE_CAVITY_GEOMETRY_CANDIDATE_UNACCEPTED_DENSE_APPEARANCE_PENDING'
    assert receipt.get('qualifiedRestFit') is True and receipt.get('bodyAnd75RestUntouched') is True
    native = Path(receipt['native']['path'])
    assert native.is_relative_to(fit_root) and SHA(native) == receipt['native']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(native))
    fits = {}
    for side in ('R', 'L'):
        path = fit_root / ('fitted-outer-' + side + '.npz')
        fit = dict(np.load(path)); obj = bpy.data.objects['ActualSelectedBoot.' + side]
        actual = np.asarray([tuple(v.co) for v in obj.data.vertices])
        assert obj.matrix_world.is_identity
        assert np.array_equal(actual[:len(fit['vertices'])], fit['vertices'].astype(np.float32).astype(np.float64))
        assert np.array_equal(np.asarray([tuple(f.vertices) for f in obj.data.polygons[:len(fit['faces'])]]), fit['faces'])
        fits[side] = fit
        report['boots'].append({'side': side, 'fitPath': str(path), 'fitSHA256': SHA(path)})
    helper = load_module(HELPER, 'independent_boot_cavity_geometry')
    lineage = load_module(LINEAGE, 'independent_boot_dense_lineage')
    dense = dict(np.load(DENSE)); cut = lineage.classify_dense(dense, helper, out)
    for side, record in zip(('R', 'L'), report['boots']):
        record['pairedOriginalDenseAppearance'] = lineage.pair_dense(dense, cut, fits[side], out, side)
        save()
    assert all(SHA(path) == digest for path, digest in PINS.items())
    assert SHA(native) == receipt['native']['sha256']
    assert SHA(fit_root / 'fit.json') == report['fitReceiptSHA256']
    report['status'] = 'ORIGINAL_DENSE_SOURCE_PAIRED_UNACCEPTED_4K_BAKE_PENDING'
except BaseException as error:
    report['status'] = 'REJECTED_DENSE_SOURCE_PAIR'
    report['error'] = type(error).__name__ + ': ' + str(error)
    raise
finally:
    save(); print(json.dumps({key: report[key] for key in ('status', 'error') if key in report}))
