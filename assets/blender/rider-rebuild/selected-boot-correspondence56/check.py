"""CPU numerical/mutation fixtures; no Blender, simplifier or browser launch."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EVIDENCE = ROOT/'docs/evidence/rider-rebuild/selected-boot-correspondence56'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


kernel = load(HERE/'kernel.py', 'kernel56_check')
author = load(HERE/'author.py', 'author56_check')
checks = []


def reject(fn, message):
    try:
        fn()
    except AssertionError as error:
        assert message in str(error), (message, repr(error))
    else:
        raise AssertionError('Mutation was not rejected: '+message)


base = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
expected = np.array([.2, .3, .5])
for scale in [1e-100, 1e-6, 1., 1e6, 1e100]:
    triangle = base*scale
    coefficient = kernel.barycentric(expected@triangle, triangle)
    np.testing.assert_allclose(coefficient, expected, rtol=0, atol=3e-16)
    np.testing.assert_allclose((coefficient@triangle)/scale, (expected@triangle)/scale,
                               rtol=0, atol=3e-16)
checks.append('Identical barycentrics and reconstruction across meter/micron/extreme scales')
for triangle in [np.zeros((3, 3)), np.array([[0., 0., 0.], [1., 2., 3.], [2., 4., 6.]])]:
    reject(lambda: kernel.barycentric(triangle[0], triangle), 'Degenerate')
for bad in [np.nan, np.inf]:
    reject(lambda: kernel.barycentric([bad, 0, 0], base), 'Nonfinite')
    triangle = base.copy(); triangle[0, 0] = bad
    reject(lambda: kernel.barycentric([0, 0, 0], triangle), 'Nonfinite')
reject(lambda: kernel.barycentric([2., 2., 0.], base), 'Outside')
reject(lambda: kernel.barycentric([0., 0.], base), 'shape')
checks.append('True collinear/coincident, nonfinite, malformed and outside bearings fail closed')
projected = kernel.barycentric([.3, .5, .2], base)
np.testing.assert_allclose(projected, expected, rtol=0, atol=3e-16)
skinny = np.array([[0., 0., 0.], [1., 1., 0.], [1., 1.+1e-10, 0.]])
a, b = skinny[1], skinny[2]
assert (a@a)*(b@b)-(a@b)**2 == 0
np.testing.assert_allclose(kernel.barycentric(skinny[1], skinny), [0, 1, 0], atol=1e-15)
checks.append('Projection semantics retained; nonzero skinny area survives Gram cancellation')

source, _ = author.adapted_source(); ast.parse(source)
raw = (ROOT/'assets/blender/rider-rebuild/selected-rider-production25/author.py').read_bytes()
node = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == 'transfer')
original_transfer = ''.join(raw.decode().splitlines(keepends=True)[node.lineno-1:node.end_lineno])
assert kernel.adapted_transfer_source(raw).replace(kernel.NEW_CALL, kernel.OLD_CALL) == original_transfer
for old in [b"maximumSkinWeightL1", b"minimumNormalDot", b"maximumSurfaceErrorM"]:
    reject(lambda: kernel.adapted_transfer_source(raw.replace(old, old+b'_MUTATED')), 'Frozen engine25 changed')
for token in ["spec['full'] == 8000 and spec['maximumSurfaceErrorM'] == 0.001",
              "'minimumNormalDot': 0.25, 'maximumSkinWeightL1': 0.3",
              "'maximumInfluences': 4, 'maximumRemovedMass': 0.001",
              "'maximumAdditionalAdjacentWeightL1': 0.002, 'supportEpsilon': 1e-05",
              "assert receipt_path == CANDIDATE56 and sha(receipt_path) == CANDIDATE56_SHA",
              "assert before == witness.retained(sources, rig)",
              "surface_checks(engine, source, target, spec['maximumSurfaceErrorM']",
              "and not out.exists()", "'sceneBudgetPassed': False"]:
    assert token in source, token
assert source.index('bpy.ops.wm.save_as_mainfile') < source.index("report['objects'][name]['transfer'] = engine.transfer")
checks.append('Only kernel call differs in transfer; frozen hashes, gates and precheck native save retained')

# Exercise unchanged downstream failures through the installed transfer itself.
engine_path = ROOT/'assets/blender/rider-rebuild/selected-rider-production25/author.py'
source_object = SimpleNamespace(name='source', vertex_groups=[SimpleNamespace(name='bone')])
rig = SimpleNamespace(data=SimpleNamespace(bones={'bone'}))
config = {'levels': {'full': {'surfaceErrorMultiplier': 1}},
          'transfer': {'minimumNormalDot': .25, 'maximumSkinWeightL1': .3}}
for normal, inherited, failure in [([0, 0, -1], 1., 'Wrong-facing'), ([0, 0, 1], .1, 'Anatomical field')]:
    target = SimpleNamespace(data=SimpleNamespace(vertices=[SimpleNamespace(normal=np.array(normal))]))
    with tempfile.TemporaryDirectory() as temporary:
        out = Path(temporary)
        engine = SimpleNamespace(__file__=str(engine_path), np=np, Vector=lambda p: p,
            points=lambda obj: base*1e-7 if obj is source_object else np.array([[0., 0., 0.]]),
            triangles=lambda obj: np.array([[0, 1, 2]]),
            skin_rows=lambda obj, names: np.ones((3, 1)) if obj is source_object else np.array([[inherited]]),
            tree=lambda p, f: SimpleNamespace(find_nearest=lambda p, limit: (np.zeros(3), None, 0, 0.)))
        kernel.install(engine, out)
        reject(lambda: engine.transfer(source_object, target, rig, {'maximumSurfaceErrorM': .001}, 'full', config, out), failure)
        report = json.loads((out/'correspondence56.json').read_text())
        assert report['kernelCalls'] == 1 and report['kernelFailure'] is None
        assert report['formerlyRejectedBearings'][0]['sourceFaceId'] == 0
checks.append('Actual frozen transfer still rejects wrong-facing and skin-mismatched mutations after corrected tiny bearing')

receipt_bytes = author.CANDIDATE.read_bytes()
assert hashlib.sha256(receipt_bytes).hexdigest() == author.CANDIDATE_SHA
receipt = json.loads(receipt_bytes)
pin = receipt['sourceArrayPackage']; package = (ROOT/pin['path']).read_bytes()
assert hashlib.sha256(package).hexdigest() == pin['sha256']
def array(name):
    row = pin['layout'][name]
    return np.frombuffer(package, dtype=row['dtype'], count=int(np.prod(row['shape'])),
                         offset=row['byteOffset']).reshape(row['shape'])
p = array('positions').astype(np.float64); f = array('triangles')
a = p[f[:, 1]]-p[f[:, 0]]; b = p[f[:, 2]]-p[f[:, 0]]
aa = np.einsum('ij,ij->i', a, a); bb = np.einsum('ij,ij->i', b, b)
ab = np.einsum('ij,ij->i', a, b); gram = aa*bb-ab*ab
cross = np.cross(a, b); area_squared = np.einsum('ij,ij->i', cross, cross)
failed = np.flatnonzero(gram <= 1e-24)
assert len(failed) == 78 and np.all(area_squared > 0) and np.all(gram > 0)
maximum_coefficient_error = 0.; maximum_reconstruction = 0.
for face_id in failed:
    triangle = p[f[face_id]]
    for coefficient in [*np.eye(3), np.full(3, 1/3)]:
        point = coefficient@triangle; actual = kernel.barycentric(point, triangle)
        assert np.isfinite(actual).all() and actual.min() >= 0 and abs(actual.sum()-1) < 1e-15
        maximum_coefficient_error = max(maximum_coefficient_error, float(np.max(np.abs(actual-coefficient))))
        maximum_reconstruction = max(maximum_reconstruction, float(np.linalg.norm(actual@triangle-point)))
assert maximum_coefficient_error < 2e-8 and maximum_reconstruction < 2e-16
# Mutation fixture: the frozen absolute kernel must fail all 78 real centroids.
node = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == 'barycentric')
old_kernel_source = ''.join(raw.decode().splitlines(keepends=True)[node.lineno-1:node.end_lineno])
namespace = {'np': np}; exec(old_kernel_source, namespace)
for face_id in failed:
    triangle = p[f[face_id]]
    reject(lambda: namespace['barycentric'](triangle.mean(axis=0), triangle), 'Degenerate')
checks.append('All 78 actual cutoff faces: original kernel rejected; corrected corners/centroids finite, inside and reconstructed')

report = {'status': 'CPU_KERNEL_FIXTURES_PASSED_NATIVE_PENDING', 'acceptedArt': False,
          'sourceArrayPackage': {'path': pin['path'], 'sha256': pin['sha256']},
          'constructorReceipt': {'path': str(author.CANDIDATE.relative_to(ROOT)), 'sha256': author.CANDIDATE_SHA},
          'sourceTriangles': len(f), 'genuineDegenerateTriangles': int(np.count_nonzero(area_squared == 0)),
          'minimumCrossSquaredM4': float(area_squared.min()), 'frozenAbsoluteCutoffM4': 1e-24,
          'cutoffFaceCount': len(failed), 'maximumCutoffConditionProxy': float(np.max(aa[failed]*bb[failed]/area_squared[failed])),
          'maximumCoefficientError': maximum_coefficient_error, 'maximumReconstructionResidualM': maximum_reconstruction,
          'cutoffFaces': [{'sourceFaceId': int(i), 'sourceVertexIds': f[i].tolist(),
                           'gramDeterminantM4': float(gram[i]), 'crossSquaredM4': float(area_squared[i])} for i in failed],
          'checks': checks,
          'limits': 'The failed native01 log contains no nearest-bearing face ID. These 78 are the complete source cutoff set, not claimed to be the actual trigger. Parent native02 remains required; no geometry, skin, contact, PBR, bake or motion acceptance follows from numerical fixtures.'}
EVIDENCE.mkdir(parents=True, exist_ok=True)
(EVIDENCE/'numerical-fixtures.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k: v for k, v in report.items() if k != 'cutoffFaces'}, indent=2))
