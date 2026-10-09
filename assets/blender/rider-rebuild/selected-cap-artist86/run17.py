"""Parent-only worker. No command has been granted or executed for17."""
import os
from pathlib import Path
import runpy
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'harness/out/rider-rebuild/selected-cap-artist86'
assert sys.version_info[:2] == (3, 13) and np.__version__ == '2.3.4'
assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['OMP_NUM_THREADS'] == '2'
assert int(os.environ['ROCKHOP_GENERATION_CONTROLLER_PID']) == os.getppid()
R = runpy.run_path(str(HERE/'refit.py'))
receipt = R['main'](OUT/'receiver17')
R['verify'](receipt)
# check_poses imports bpy/mathutils; this driver runs within headless Blender.
runpy.run_path(str(HERE/'check_poses.py'))['main'](receipt, OUT/'contact17')
