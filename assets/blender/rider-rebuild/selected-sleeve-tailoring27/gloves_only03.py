"""Memory02 construction unchanged; store its native checkpoint uncompressed."""
import hashlib
import importlib.util
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
original = HERE/'gloves_only02.py'
assert hashlib.sha256(original.read_bytes()).hexdigest() == '61ade7d9c46b60fbbc28a8a1869e86eb67eecb6524b5808c9390c37cdbef2e4b'
spec = importlib.util.spec_from_file_location('selected_gloves_memory02', original)
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
helper = HERE/'checkpoint03.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == '9e3b44563e27da4e99be35ee43539ffc3bd9b0f5b357c06748b4fc224fc080c7'
checkpoint = runpy.run_path(str(helper))


if __name__ == '__main__':
    # Reuse memory02's actual lifetime wrapper and original protected-state
    # callback. Replace only its save function, then record THIS recipe hash.
    prior.prior.checkpoint['save'] = checkpoint['save']
    prior.prior.__file__ = __file__
    engine = prior.prior.prior.engine
    engine.full_cuff = prior.before_glove
    engine.sleeve = prior.prior.stop_after_gloves
    engine.main()
