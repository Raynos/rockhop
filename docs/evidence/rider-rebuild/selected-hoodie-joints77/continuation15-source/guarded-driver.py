"""Continue saved15 with its exact NumPy runtime; no candidate/native rerun."""
import hashlib
import os
from pathlib import Path
import runpy
import sys

# Import original Blender NumPy before adding any package search directory.
import numpy as np

ROOT = Path('/Users/raynos/projects/games/rockhop')
HERE = ROOT/'assets/blender/rider-rebuild/selected-hoodie-joints77'
OUT = ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77'
BLENDER_SITE = Path('/Applications/Blender.app/Contents/Resources/5.2/python/lib/python3.13/site-packages')
PILLOW_SITE = Path('/opt/homebrew/lib/python3.13/site-packages')
assert sys.version_info[:2] == (3, 13)
assert np.__version__ == '2.3.4' and Path(np.__file__).is_relative_to(BLENDER_SITE)
numpy_origin = np.__file__
sys.path.append(str(PILLOW_SITE))
import PIL
from PIL import Image, ImageDraw
assert PIL.__version__ == '12.3.0' and Path(PIL.__file__).is_relative_to(PILLOW_SITE)
assert sys.modules['numpy'] is np and np.__file__ == numpy_origin
assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')
assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['OMP_NUM_THREADS'] == '2'
os.chdir(ROOT)
pins = {
    HERE/'connected_cap15.py': '7b8c859863e9c7e8b1224973f4e7365cae2c022c7e8ceae6730ec806d1da65fc',
    HERE/'connected_cap_binding15.py': 'fbbc65482ce51632ae657c0693cc6515fce8807af197bf463a936e9128f25b40',
    HERE/'connected_cap_inspection15.py': '22319961c1bbb8b4e358b52c5b44316aeb6468548433530085b053dde475107d',
    HERE/'connected_cap_views15.py': '346291ea12a0c39b3cb141400bafb4217b32947a799af869c4256c8499a7cca0',
    OUT/'receiver15/receiver.json': 'd92c1060f855c5daf3dc199404250b63af3bd577253dfb0fb8162bf8b41b1a0a',
    OUT/'receiver15/receiver.npz': 'de556ac10b40fd625b922e072d49709dd40ccc99dc28c0df9274cbdb149b5305',
    OUT/'receiver15/connected-cap.json': '193db2d2cea4de7ccb0372f6560109177b73a75d1904d7c3b70453c7f024508b',
}
for path, digest in pins.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
for name in ('inspect15', 'views15'):
    assert not (OUT/name).exists(), name
print({'continuation': 'saved receiver15 only', 'numpy': np.__version__, 'numpyOrigin': numpy_origin,
       'Pillow': PIL.__version__, 'PillowOrigin': PIL.__file__, 'CPU': 2}, flush=True)
receipt = str(OUT/'receiver15/receiver.json')
print('binding/all482: reconstructive equations only; no second solve or candidate save', flush=True)
runpy.run_path(str(HERE/'connected_cap_inspection15.py'))['main'](receipt, str(OUT/'inspect15'))
print('both actual-bike endpoint sheets; painter depth sorting only', flush=True)
runpy.run_path(str(HERE/'connected_cap_views15.py'))['main'](receipt, str(OUT/'views15'))
assert sys.modules['numpy'] is np and np.__file__ == numpy_origin
for path, digest in pins.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
print('saved15 all482 and both endpoint sheets returned; unaccepted; native not run', flush=True)
