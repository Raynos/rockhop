"""Bounded read-only capture fixtures; no actual rider or Blender execution."""
import ast
import importlib.util
import json
import runpy
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'diagnose.py'))
wrapper, source = h['transformed_source']()
ast.parse(source)
frozen = wrapper['transformed_source']()
start = frozen.index("    wearer = bpy.data.objects['RiderBody__FullAnatomyReference']\n")
end = frozen.index('    moved, changed, field, fit_report = field_helper.fit(')
assert frozen[start:end] == source[source.index("    wearer = bpy.data.objects['RiderBody__FullAnatomyReference']\n"):source.index('    diagnose(')]
assert 'surgery.move(' not in source and 'save_pending(' not in source
assert h['pin'](h['checked'](h['INPUT'])) == h['INPUT']
config = json.loads(h['checked'](h['INPUT']).read_text())
path = h['checked'](config['pins']['fieldHelper'])
spec = importlib.util.spec_from_file_location('exact_field28', path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
original = module.Field.solve_planes

# A long source triangle joins an arm-seeded near component to a disconnected
# deficient remote vertex. The unchanged fit creates frozen vertex/centroid
# constraints; capture must precede the assertion and leave all values zero.
points = np.array([[0., -.005, 0.], [.01, -.005, 0.], [.6, -.005, 0.]])
faces = np.array([[0, 1, 2]])
seeds = np.array([True, True, False])
def nearest(p): return p[:, 1], np.tile([0., 1., 0.], (len(p), 1))
fit = h['capture_first_fit'](module, points, faces, seeds, nearest, config['field'], lambda _: None)
assert module.Field.solve_planes is original
assert not fit['field'].values.any() and fit['step'] == 0
bad, norm, active_count, deficit = h['deficit_masks'](fit, np)
assert bad.tolist() == [False, False, True, True]
assert active_count[2] == 0 and norm[2] == 0
try:
    original(fit['field'], fit['sample_embedding'], fit['solveNormal'], fit['solveLower'])
except AssertionError as error:
    assert str(error) == 'Deficient constraint reached frozen field boundary'
else:
    raise AssertionError('Expected exact original failure')
print(json.dumps({'passed': True, 'actualRiderRun': False,
    'checks': ['Exact frozen input pins and unchanged actual intake/retained-face block',
               'Read-only truncation precedes geometry movement and saving',
               'Original first-fit support closure produces correctly mapped unsupported vertex and centroid',
               'Capture restores exact original solver and runs no projection',
               'Original solver independently raises the precise frozen-boundary assertion']}))
