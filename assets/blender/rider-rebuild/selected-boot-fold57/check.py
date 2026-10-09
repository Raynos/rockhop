"""CPU-only bounded fan and conditional vertex-orientation mutation fixtures."""
import ast
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace

import numpy as np

import author
import fan
import orientation

checks = []


def rejected(fn, expected=''):
    try:
        fn()
    except (AssertionError, KeyError) as error:
        assert expected in str(error), (expected, repr(error))
    else:
        raise AssertionError('Mutation was accepted: '+expected)


report = fan.cpu_report()
assert len(report['sourceFan']['incidentFaces']) == 5
assert len(report['targetFan']['incidentFaces']) == 8
assert report['inheritedFaceExact'] and report['inheritedFaceMaterialExact']
assert abs(report['cpuPredictedRejectedDot']-fan.REJECTED_DOT) < 2e-7
assert report['consistentVertexNormalDotCPU'] > .995
assert sum(row['dotDonorVertexNormal'] < .25 for row in report['sourceFan']['incidentFaces']) == 1
assert sum(row['dotDonorVertexNormal'] < .25 for row in report['targetFan']['incidentFaces']) == 1
checks.append('Actual2485 maps to56390; sole opposing face is exact inherited113358→5011')

for file in Path(__file__).parent.glob('*.py'): ast.parse(file.read_text())
source, _, _ = author.adapted_source(); ast.parse(source)
raw = fan.ENGINE.read_bytes()
modified = orientation.adapted_transfer_source(raw)
assert modified.replace(orientation.NEW_SETUP, orientation.OLD_SETUP).replace(orientation.NEW_NORMAL, orientation.OLD_NORMAL) == orientation.kernel.adapted_transfer_source(raw)
assert "assert dot>=config['transfer']['minimumNormalDot']" in modified
assert "assert difference<=config['transfer']['maximumSkinWeightL1']" in modified
assert "sourceSurfaceBoundM" in modified
assert "surface_checks(engine, source, target, spec['maximumSurfaceErrorM'], config['transfer']['minimumNormalDot']" in source
assert "assert receipt_path == CANDIDATE56 and sha(receipt_path) == CANDIDATE56_SHA" in source
checks.append('Only ancestry intake and vertex normal reference differ; gate thresholds/geometric checks/candidate pins persist')

# Synthetic proof exists in memory only. It cannot stand in for native evidence.
proof = {'status': 'CONFIRMED_INHERITED_FACE_ZERO_DISTANCE_VERTEX_TIE_UNACCEPTED',
         'recipeSHA256': fan.sha(Path(__file__).with_name('native.py')), 'fanRecipeSHA256': fan.sha(fan.__file__),
         'native': {'sha256': fan.NATIVE_SHA}, 'constructor': {'sha256': fan.CANDIDATE_SHA},
         'production': {'sha256': fan.PRODUCTION_SHA}, 'targetVertexId': 2485, 'originalVertexId': 56390,
         'actualNearest': {'sourceFaceId': 113358, 'sourceVertexIds': [56390, 56936, 56633],
             'distanceM': 0., 'pointExactlyOriginalVertex': True, 'dotTargetVertexNormal': fan.REJECTED_DOT},
         'inheritedFaceExact': True, 'inheritedFaceMaterialExact': True,
         'nativeVertexEvidence': {'positionExact': True, 'originalVertexIdExact': True,
             'consistentVertexNormalDot': 1., 'sourceNormal': [0., 0., 1.], 'targetNormal': [0., 0., 1.]}}
orientation.verify_proof_data(proof)
for path, value in [(('status',), 'PARTIAL_NATIVE57_BEARING_BEFORE_FANS'),
                    (('actualNearest', 'sourceFaceId'), 113359),
                    (('actualNearest', 'distanceM'), 1e-9),
                    (('actualNearest', 'pointExactlyOriginalVertex'), False),
                    (('native', 'sha256'), 'wrong'),
                    (('inheritedFaceExact',), False),
                    (('nativeVertexEvidence', 'consistentVertexNormalDot'), .1),
                    (('nativeVertexEvidence', 'originalVertexIdExact'), False)]:
    mutation = copy.deepcopy(proof); row = mutation
    for key in path[:-1]: row = row[key]
    row[path[-1]] = value
    rejected(lambda: orientation.verify_proof_data(mutation))
checks.append('Incomplete/wrong-face/nonzero-distance/wrong-native/nonexact ancestry proof mutations rejected')

# The actual native proof records float32 vector arithmetic. Recomputing the
# same components in float64 differs by4.27e-8, so reproduce the recorded dtype
# rather than widening the proof tolerance or changing the angular gate.
stored_proof = copy.deepcopy(proof)
stored_proof['nativeVertexEvidence'].update(
    sourceNormal=[-0.9771018624305725, 0.21056947112083435, 0.03053584322333336],
    targetNormal=[-0.9885111451148987, 0.14583207666873932, -0.03973494470119476],
    consistentVertexNormalDot=0.9953705668449402)
orientation.verify_proof_data(stored_proof)
wrong_precision = copy.deepcopy(stored_proof)
vertex = wrong_precision['nativeVertexEvidence']
vertex['consistentVertexNormalDot'] = float(np.asarray(vertex['sourceNormal'])@vertex['targetNormal'])
rejected(lambda: orientation.verify_proof_data(wrong_precision))
wrong_storage = copy.deepcopy(stored_proof)
wrong_storage['nativeVertexEvidence']['sourceNormal'][0] += 1e-12
rejected(lambda: orientation.verify_proof_data(wrong_storage))
checks.append('Actual native float32 normal-dot witness reproduced exactly; wrong arithmetic/storage mutations rejected')


class Foreach:
    def __init__(self, array): self.array = np.asarray(array)
    def foreach_get(self, name, destination): destination[:] = self.array.ravel()


base = np.array([[0., 0., 0.], [1e-7, 0., 0.], [0., 1e-7, 0.]])
donor = SimpleNamespace(name='source', vertex_groups=[SimpleNamespace(name='bone')],
    data=SimpleNamespace(vertices=Foreach([[0., 0., 1.]]*3)))
def target(normal):
    return SimpleNamespace(data=SimpleNamespace(vertices=[SimpleNamespace(normal=np.array(normal))],
        attributes={'ProductionOriginalVertex': SimpleNamespace(domain='POINT', data_type='INT', data=Foreach([0]))}))

target_obj = target([0, 0, 1])
orientation.ancestry(donor, target_obj, base, base[:1])
rejected(lambda: orientation.ancestry(donor, target_obj, base, base[:1]+1e-8), 'position changed')
target_obj.data.attributes['ProductionOriginalVertex'].data = Foreach([-1])
rejected(lambda: orientation.ancestry(donor, target_obj, base, base[:1]), 'Invalid original')
target_obj.data.attributes.clear()
rejected(lambda: orientation.ancestry(donor, target_obj, base, base[:1]), 'ancestry required')
checks.append('Exact ancestry position, valid ordinal and point attribute are mandatory')

rig = SimpleNamespace(data=SimpleNamespace(bones={'bone'}))
config = {'levels': {'full': {'surfaceErrorMultiplier': 1}},
          'transfer': {'minimumNormalDot': .25, 'maximumSkinWeightL1': .3}}
for normal, expected in [([0, 0, -1], 'Wrong-facing'), ([0, 0, 1], 'Selected source detail exceeds geometry bound')]:
    target_obj = target(normal); tree_count = [0]
    def tree(p, f):
        tree_count[0] += 1
        if tree_count[0] == 1:
            return SimpleNamespace(find_nearest=lambda point, limit: (np.zeros(3), None, 0, 0.))
        return SimpleNamespace(find_nearest=lambda point, limit: (None, None, None, None))
    engine = SimpleNamespace(__file__=str(fan.ENGINE), np=np, Vector=lambda p: p,
        points=lambda obj: base if obj is donor else base[:1],
        triangles=lambda obj: np.array([[0, 2, 1]]),
        skin_rows=lambda obj, names: np.ones((3, 1)) if obj is donor else np.ones((1, 1)), tree=tree)
    with tempfile.TemporaryDirectory() as temporary:
        out = Path(temporary)
        orientation.install(engine, out, {'fixtureOnly': True})
        rejected(lambda: engine.transfer(donor, target_obj, rig, {'maximumSurfaceErrorM': .001}, 'full', config, out), expected)
        assert json.loads((out/'correspondence56.json').read_text())['kernelCalls'] == 1
        assert json.loads((out/'orientation57.json').read_text())['normalAttributesWritten'] is False
checks.append('Installed transfer rejects reversed target vertex normal; matching vertex normals proceed to unchanged reverse geometry rejection')

out = fan.ROOT/'docs/evidence/rider-rebuild/selected-boot-fold57'
out.mkdir(parents=True, exist_ok=True)
(out/'fixtures.json').write_text(json.dumps({'status': 'CPU_FIXTURES_PASSED_NATIVE_PROOF_PENDING',
    'acceptedArt': False, 'checks': checks, 'limits': 'Synthetic proof only in memory; no native57 diagnostic or production acceptance generated.'}, indent=2)+'\n')
print('\n'.join('PASS: '+item for item in checks))
