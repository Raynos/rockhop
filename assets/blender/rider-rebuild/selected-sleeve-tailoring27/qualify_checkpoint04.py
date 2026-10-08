"""Reopen a pending04 native and compare its complete protected fingerprints."""
import hashlib
import runpy
import sys
from pathlib import Path
import bpy

helper = Path(__file__).with_name('checkpoint04.py')
assert hashlib.sha256(helper.read_bytes()).hexdigest() == 'd9e1c4f0b8fee05cae085482490fa4650c994c1dfc6213c234b3988ae3011406'
checkpoint = runpy.run_path(str(helper))
args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 1
checkpoint['qualify'](args[0], bpy, runpy.run_path)
