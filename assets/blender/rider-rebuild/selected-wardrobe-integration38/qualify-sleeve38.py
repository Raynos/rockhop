"""Parent guarded separate process; no dense or art success is inferred."""
import runpy
import sys
from pathlib import Path
import bpy

helper = runpy.run_path(str(Path(__file__).with_name('sleeve_checkpoint.py')))
args = sys.argv[sys.argv.index('--')+1:]
assert len(args) == 1
helper['qualify'](args[0], bpy, runpy.run_path)
