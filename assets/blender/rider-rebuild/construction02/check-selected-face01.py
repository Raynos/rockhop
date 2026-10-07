"""Guarded native construction check only; no appearance acceptance or renders."""
import hashlib
import json
import runpy
import sys
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[4]
source = root / 'assets/blender/rider-rebuild/construction02/build-selected-face01.py'
native = root / 'harness/out/rider-rebuild/construction01/combined04/rider-assembled.blend'
out = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
out.mkdir(parents=True, exist_ok=False)
(out / 'input-receipt.json').write_text(json.dumps({'accepted': False, 'inputs': [
    {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    for p in (Path(__file__).resolve(), source, native)]}, indent=2) + '\n')
bpy.ops.wm.open_mainfile(filepath=str(native))
rig = bpy.data.objects['RiderSkeleton']; body = bpy.data.objects['RiderBody']
result = runpy.run_path(str(source))['buildFace'](body, rig, out)
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'selected-face-native.blend'))
print(json.dumps(result['report']))
