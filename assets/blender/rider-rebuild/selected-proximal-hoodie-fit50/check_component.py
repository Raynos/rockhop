"""Source/lifecycle/receipt checks without pretending to execute Blender."""
import ast
import copy
import json
import runpy
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'component.py'))
wrapper, source = h['transformed_source']()
ast.parse(source)
old = wrapper['transformed_source']()
start = old.index("    wearer = bpy.data.objects['RiderBody__FullAnatomyReference']\n")
end = old.index('    surgery = B.Surgery(hoodie, source)\n')
assert old[start:end] == source[source.index("    wearer = bpy.data.objects['RiderBody__FullAnatomyReference']\n"):source.index('    build(')]
assert 'surgery = B.Surgery' not in source and 'field_helper.fit(' not in source
assert h['WRAPPER47'] == h['read'](h['SOURCE47'])['pins']['constructor47']
frozen = h['read'](h['SOURCE47'])
config = {**frozen, 'sourceInput47': h['SOURCE47'], 'retired45mmRepairGateClaimed': False,
          'pins': {**frozen['pins'], 'component50': h['pin'](HERE/'component.py'),
                   'registration50': h['pin'](HERE/'registration.py'), 'wrapper47': h['WRAPPER47']}}
actual = h['source_gate'](config)
assert actual['status'] == h['c47']['INTAKE_QUALIFIED']
bad = copy.deepcopy(config); bad['field']['clothClearanceM'] *= 2
try: h['source_gate'](bad)
except AssertionError: pass
else: raise AssertionError('Changed geometric target was admitted')
bad = copy.deepcopy(config); bad['retired45mmRepairGateClaimed'] = True
try: h['source_gate'](bad)
except AssertionError: pass
else: raise AssertionError('Retired repair acceptance was admitted')
text = (HERE/'component.py').read_text()
assert text.index("native = c47['save_native']") < text.index("assert invariant(hoodie, faces, author, np) == before")
assert text.index("write(out/'component-raw.json'") < text.index("'rebuiltHoodieGeometry': c['geometry'](hoodie)")
assert 'mesh.vertices.foreach_set' in text and 'mesh.normals_split_custom_set' in text
assert '.vertex_groups.new(' not in text and '.uv_layers.new(' not in text
assert 'maximumDisplacementM' not in (HERE/'registration.py').read_text()
print(json.dumps({'passed': True, 'actualRiderRun': False, 'checks': [
    'Exact frozen original reference intake before new construction',
    'Qualified actual47 source accepted, changed target and false retired-cap claim rejected',
    'Raw native and raw receipt precede postconstruction fingerprints and strain scan',
    'Original source topology/UV/PBR/groups retained by position/normal-only writes',
    'Old45mm repair cap neither changed nor claimed by broad registration']}))
