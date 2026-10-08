"""Save unchanged memory02 gloves before a separate protected-state qualifier."""
import hashlib
import importlib.util
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
original = HERE/'gloves_only02.py'
assert hashlib.sha256(original.read_bytes()).hexdigest() == '61ade7d9c46b60fbbc28a8a1869e86eb67eecb6524b5808c9390c37cdbef2e4b'
spec = importlib.util.spec_from_file_location('selected_gloves_memory02', original)
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
helper = HERE/'checkpoint04.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == 'd9e1c4f0b8fee05cae085482490fa4650c994c1dfc6213c234b3988ae3011406'
checkpoint = runpy.run_path(str(helper))
input_pin = {'path': 'assets/blender/rider-rebuild/glove-over-sleeve08/input.json',
             'sha256': '912e724a6d296709c92a4c48704f5be490e7f228cdfe55b84814e76c85224eed'}
inputs = json.loads(checkpoint['checked'](input_pin).read_text())


def stop_before_protected_scan(*args, **kwargs):
    out = Path(sys.argv[sys.argv.index('--')+1]).resolve()
    checkpoint['save_pending'](out, checkpoint['pin'](__file__), prior.prior.protected_state,
                               inputs, input_pin, prior.prior.prior.engine.bpy)
    raise SystemExit(0)


if __name__ == '__main__':
    engine = prior.prior.prior.engine
    engine.full_cuff = prior.before_glove
    engine.sleeve = stop_before_protected_scan
    engine.main()
