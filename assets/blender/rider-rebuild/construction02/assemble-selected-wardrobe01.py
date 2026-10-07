"""Internal selected clothing checkpoint; wearer and rest rig remain frozen04."""
import hashlib
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[4]
recipe = root / 'assets/blender/rider-rebuild/construction01/assemble-export04.py'
wardrobe = root / 'assets/blender/rider-rebuild/donor-wardrobe01/build-wardrobe.py'
native = root / 'harness/out/rider-rebuild/construction01/rig04/anatomical-rig.blend'
assert hashlib.sha256(wardrobe.read_bytes()).hexdigest() == '7ded4e43a627e23b3a7bfecb8327eb11025b399081b2d023a3f7f472898ec7b0'
args = sys.argv[sys.argv.index('--') + 1:]
assert len(args) == 1
sys.argv = [str(recipe), '--', str(native), str(Path(args[0]).resolve()), str(wardrobe)]
runpy.run_path(str(recipe), run_name='__main__')
