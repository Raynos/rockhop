"""One parent-granted local paint16 followed by the same six finite poses."""
import hashlib
from pathlib import Path
import runpy

ROOT = Path('/Users/raynos/projects/games/rockhop')
PINS = (
    ('assets/blender/rider-rebuild/selected-hoodie-joints77/shoulder_paint16.py', '357a2218909aa98454669d5bb35a8559eaf9154084017c8d9690818b89369cc9'),
    ('assets/blender/rider-rebuild/selected-hoodie-joints77/posed_contact16.py', '849d2e074b0dbc8753b3f4d73210130f235113d4f430fee7c975030a5fc43e4e'),
)
def check():
    for path, digest in PINS: assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path

check()
own = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
base = ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77'
assert not (base/'receiver16').exists() and not (base/'contact16').exists()
receipt = runpy.run_path(str(ROOT/PINS[0][0]))['main'](base/'receiver16')
check()
runpy.run_path(str(ROOT/PINS[1][0]))['main'](receipt, base/'contact16')
check()
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == own
