"""CPU mathematics, real source-branch intake, and lifecycle checks only."""
import ast
import copy
import json
import runpy
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'component.py'))
core = runpy.run_path(str(HERE/'multiscale.py')); Cage = core['Cage']
checks = []
for p in HERE.glob('*.py'): ast.parse(p.read_text(), feature_version=(3, 9))
wrapper, source = h['transformed_source'](); ast.parse(source, feature_version=(3, 9))
assert 'field_helper.fit(' not in source and 'surgery = B.Surgery' not in source
checks.append('Exact47 intake wrapper ends before retired construction; Python3.9 parsing')

p = np.array([[0., 0., 0.], [.02, 0., .02], [.03, .02, .05], [.1, .1, .1]])
cage = Cage(np.array([[-.2, -.2, -.2], [.2, .2, .2]]), .04)
_, w, dw = cage.embed(p)
assert np.max(abs(w.sum(1)-1)) < 1e-14 and np.max(abs(dw.sum(1))) < 1e-13
nodes = np.indices(cage.shape).reshape(3, -1).T*cage.spacing+cage.origin
matrix = np.array([[.1, .05, 0], [0, .1, -.03], [.05, 0, .05]])
cage.values = nodes@matrix.T
moved, differential = cage.evaluate(p, True)
assert np.max(abs(moved-(p+p@matrix.T))) < 1e-13
assert np.max(abs(differential-(np.eye(3)+matrix))) < 1e-13
checks.append('Cubic partition of unity and exact affine position/differential')

# Actual C2 continuity across a lattice plane, including first derivative of
# the Jacobian. The trilinear predecessor cannot satisfy this fixture.
cage.values[:] = 0; grid = cage.values.reshape(tuple(cage.shape)+(3,))
rng = np.random.default_rng(55); grid[3:-3, 3:-3, 3:-3] = rng.normal(size=grid[3:-3, 3:-3, 3:-3].shape)*.001
eps = 1e-7; q = np.array([[-eps, .013, .017], [0, .013, .017], [eps, .013, .017]])
_, j = cage.evaluate(q, True)
left, right = (j[1]-j[0])/eps, (j[2]-j[1])/eps
assert np.max(abs(left-right)) < 1e-4
assert cage.certificate()['compactC2ZeroExtensionProven']
checks.append('C2 differential continuity and compact zero extension')

x = np.array([[a, 0., b] for a in [-.15, 0, .15] for b in [-.15, 0, .15]])
paired = np.vstack((x, x+[0, .003, 0])); target = paired.copy()
target[:, 1] += .07*np.exp(-(paired[:, 0]**2+paired[:, 2]**2)/.02)
moved, jac, maps, report = core['fixed_targets'](paired, paired, target, .04, .85, lambda _: None, .003)
assert np.max(abs(moved-target)) <= report['nativeCoordinatePrecisionM']
assert np.linalg.det(jac).min() > 0 and np.min(np.linalg.norm(moved[9:]-moved[:9], axis=1)) > 0
assert np.max(abs(moved[:, 2]-paired[:, 2])) <= report['nativeCoordinatePrecisionM']
replay = paired.copy()
for field in maps: replay, _ = field.evaluate(replay)
assert np.array_equal(replay, moved)
checks.append('70mm paired-wall fixed endpoint fit, retained station order, positive Jacobians and exact replay')

# The actual55 architectural failure: a healthy rear sleeve endpoint may lie
# beyond every horizontal arm section. Its own anatomical radial branch still
# exists and must retain the fixed endpoint/ease.
G = runpy.run_path(str(HERE/'geometry.py')); M = runpy.run_path(str(HERE/'meridian.py'))
vertices, triangles = [], []
for cx, radius in ((0., .12), (.3, .05)):
    offset = len(vertices)
    for z in (0., 1.):
        vertices.extend([[cx+radius*np.cos(a), radius*np.sin(a), z] for a in np.arange(32)*2*np.pi/32])
    vertices.extend([[cx, 0, 0], [cx, 0, 1]])
    for i in range(32):
        j = (i+1)%32
        triangles.extend([[offset+i, offset+j, offset+32+j], [offset+i, offset+32+j, offset+32+i],
                          [offset+64, offset+j, offset+i], [offset+65, offset+32+i, offset+32+j]])
body = G['Mesh'](np.asarray(vertices), np.asarray(triangles))
offsets = np.array([[-.0015, 0., 0.], [.0015, 0., 0.]])
apex = np.array([.2, 0., .8])+offsets; end = np.array([.3, .09, .2])+offsets
assert len(body.x_hits(end.mean(0)[1], end.mean(0)[2], 1)) == 1
axis = M['Axis']([[.3, 0., 1.], [.3, 0., .5], [.3, 0., 0.]])
meridian = M['Meridian'](axis, apex, end, body, body.nearest, .0026, float(np.spacing(np.float32(1.))),
                       {'side': 'L', 'role': 'sleeve', 'fixture': 'healthy rear endpoint outside horizontal arm section'})
rows = [{'fraction': float(t)} for t in np.linspace(0, 1, 9)]
pairs = [(apex*(1-t)+end*t, apex*(1-t)+end*t, {}) for t in np.linspace(0, 1, 9)]
fitted, meridian_report = meridian.controls(rows, pairs)
assert np.array_equal(fitted[-1][1], end)
assert all(float(body.nearest(destination)[0].min()) >= .0026 for _, destination, _ in fitted)
assert np.all(np.diff([r['canonicalStation'] for _, _, r in fitted]) > 0)
assert meridian_report['healthy50EndpointEaseM'] == float(body.nearest(end)[0].min())
checks.append('Separate anatomical sleeve branch reaches healthy rear endpoint with no horizontal arm hit; endpoint/ease exact and station order retained')

assert (HERE/'sections.py').read_bytes() == (HERE.parent/'selected-anatomical-hoodie-fit55/sections.py').read_bytes()
assert (HERE/'targets.py').read_bytes() == (HERE.parent/'selected-anatomical-hoodie-fit64/targets.py').read_bytes()
assert (HERE/'meridian.py').read_bytes() == (HERE.parent/'selected-anatomical-hoodie-fit64/meridian.py').read_bytes()
checks.append('Frozen source sections and64 anatomical targets/numeric policy retained exactly')

frozen = h['read'](h['SOURCE47'])
config = {**frozen, 'sourceInput47': h['SOURCE47'], 'retired45mmRepairGateClaimed': False,
    'pins': {**frozen['pins'], 'component65': h['pin'](HERE/'component.py'), 'cage65': h['pin'](HERE/'multiscale.py'),
        'wrapper47': h['WRAPPER47'], **{k: h['pin'](HERE/v) for k, v in h['LOCAL'].items()}, **h['REFERENCE']}}
assert h['source_gate'](config)['status'] == h['c47']['INTAKE_QUALIFIED']
bad = copy.deepcopy(config); bad['field']['clothClearanceM'] *= 2
try: h['source_gate'](bad)
except AssertionError: pass
else: raise AssertionError('Changed clearance admitted')
checks.append('Exact source pins accepted; altered target rejected')
if (HERE/'input01.json').exists():
    assert h['source_gate'](h['read'](h['pin'](HERE/'input01.json'))) == h['source_gate'](config)
    checks.append('Final frozen65 input admits exactly the verified original47 source contract')

reader = runpy.run_path(str(HERE.parent/'selected-sleeve-support49/check_source_pair.py'))
doc, accessor = reader['glb'](reader['prior']['originalHoodie']); primitive = doc['meshes'][0]['primitives'][0]
raw = accessor(primitive['attributes']['POSITION'])[:, [0, 2, 1]].astype(float); raw[:, 1] *= -1
faces = accessor(primitive['indices']).reshape(-1, 3)
frames = h['read'](reader['prior']['hoodieSourceFrames'])
xyz = raw*np.asarray(frames['sourceDisplayAffine']['scale'])+frames['sourceDisplayAffine']['translation']
section = runpy.run_path(str(HERE/'sections.py')); actual = []
for side in ('L', 'R'):
    depth = frames['landmarks']['lowerAxilla.'+side]['source'][1]
    nodes, branches, witness = section['underarm'](xyz, faces, depth, side, frames)
    assert set(branches) == {'torso', 'sleeve'}
    for path in branches.values():
        rows = section['sample_path'](nodes, path, (xyz,), faces, 9)
        assert [r['fraction'] for r in rows] == list(np.linspace(0, 1, 9))
    actual.append(witness)
checks.append('Actual selected bilateral cavity apex with connected torso/sleeve branches and ordered material arclength')

text = (HERE/'component.py').read_text()
assert text.index("native = c47['save_native']") < text.index("write(out/'component-raw.json'") < text.index("'rebuiltHoodieGeometry': c['geometry'](hoodie)")
assert 'qualifier.measure' in text and 'construction-failure.json' in text
assert '.vertex_groups.new(' not in text and '.uv_layers.new(' not in text
checks.append('Raw native/receipt precede postscan; independent reopen contact; failure receipt and unchanged topology/fields')
assert text.index("np.savez_compressed(out/'fixed-material-targets.npz'") < text.index('moved, differential, maps, report = cage.fixed_targets')
assert "'solverContext': STAGE.get('solver')" in text
assert 'fine_spacing = float(np.linalg.norm(np.diff(np.asarray(wall_pairs)' in text
checks.append('Exact native material target arrays precede solve; failed solver preserves their pins and measured paired-wall spacing')
print(json.dumps({'passed': True, 'actualRiderConstructionExecuted': False, 'checks': checks,
    'pairedFixtureMaps': len(maps), 'pairedFixtureEndpointResidualM': report['maximumEndpointResidualM'],
    'actualSourceSectionIntake': actual}, indent=2))
