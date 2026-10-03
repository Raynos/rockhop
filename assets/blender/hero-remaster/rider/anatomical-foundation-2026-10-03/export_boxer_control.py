"""Export modest anatomy view from frozen control; never alter its source."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, out = Path(a.source).resolve(), Path(a.out).resolve()
before = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
names = ['Foundation file frame, game x0.65', 'Independent anatomical foundation rig',
         'Canonical anatomical body, baked adult hm08', 'Opaque boxer fitting garment']
for name in names:
    obj = bpy.data.objects[name]
    obj.hide_render = False
    obj.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects[names[1]]
bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', use_selection=True,
                        export_animations=False, export_yup=True, export_extras=True)
assert before == hashlib.sha256(source.read_bytes()).hexdigest()
print('BOXER_REFERENCE_EXPORTED', json.dumps({'sourceSHA256': before,
      'exportSHA256': hashlib.sha256(out.read_bytes()).hexdigest(), 'bytes': out.stat().st_size}))
