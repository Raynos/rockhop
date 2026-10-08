"""Exact glove-only recipe with bounded construction-scratch lifetime only.

Original wrapper/source27 remains frozen. No geometry, UV, material, map, skin,
rest, profile, contact-method or threshold changes; no Blender IDs are purged.
"""
import hashlib
import importlib.util
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
original = HERE/'gloves_only.py'
assert hashlib.sha256(original.read_bytes()).hexdigest() == '279e936f3ab107434557e8efbb7d0a3b1525b9b7aeb6c6a7c63084b3bbb4455a'
spec = importlib.util.spec_from_file_location('selected_gloves_exact_checkpoint27', original)
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
helper = HERE/'memory_lifetime.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == 'e91325cce045c41373e557f3b92332b8779e0374c7c917133365036f6f8dcb90'
lifetime = runpy.run_path(str(helper))
installed = False


def record(row):
    print('GLOVE_CHECKPOINT_LIFETIME '+json.dumps(row), flush=True)


def before_glove(*args, **kwargs):
    global installed
    if not installed:
        lifetime['install'](prior.prior.engine.B, record)
        installed = True
    return prior.remember_protected_before_gloves(*args, **kwargs)


if __name__ == '__main__':
    # The reused save callback records THIS actual wrapper as its source recipe.
    # Its original protected geometry/hoodie/rest checks remain unchanged.
    prior.__file__ = __file__
    prior.prior.engine.full_cuff = before_glove
    prior.prior.engine.sleeve = prior.stop_after_gloves
    prior.prior.engine.main()
