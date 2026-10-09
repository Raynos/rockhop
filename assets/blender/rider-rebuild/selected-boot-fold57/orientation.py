"""Consistent vertex-normal comparison at verified exact original ancestry.

No normal value is authored, averaged, flipped or overridden. Native donor and
target vertex normals are compared. Source BVH bearing and skin interpolation,
0.25 threshold, and separate geometric surface/orientation gates remain.
"""
import json
from pathlib import Path

import numpy as np

import fan

KERNEL56 = fan.ROOT/'assets/blender/rider-rebuild/selected-boot-correspondence56/kernel.py'
KERNEL56_SHA = '71fc5add2e5e7fa876329a03b213eea891141f06539554056f58fb2652a9593f'
fan.pin(KERNEL56, KERNEL56_SHA)
kernel = fan.load(KERNEL56, 'orientation57_kernel56')
OLD_NORMAL = 'dot=float(normals[tri]@np.asarray(target.data.vertices[i].normal))'
NEW_NORMAL = 'dot=float(donor_vertex_normals57[original57[i]]@np.asarray(target.data.vertices[i].normal))'
OLD_SETUP = 'sp=points(source);sf=triangles(source);tp=points(target);tf=triangles(target)'
NEW_SETUP = OLD_SETUP+'\n    donor_vertex_normals57,original57=ancestry57(source,target,sp,tp)'


def verify_proof(path, expected_sha):
    path = Path(path).resolve()
    assert path.is_relative_to(fan.ROOT/'harness/out/rider-rebuild/selected-boot-fold57'), 'Proof outside native57'
    proof_pin = fan.pin(path, expected_sha)
    proof = json.loads(path.read_text())
    verify_proof_data(proof)
    return proof_pin


def verify_proof_data(proof):
    assert proof['status'] == 'CONFIRMED_INHERITED_FACE_ZERO_DISTANCE_VERTEX_TIE_UNACCEPTED'
    assert proof['recipeSHA256'] == fan.sha(Path(__file__).with_name('native.py'))
    assert proof['fanRecipeSHA256'] == fan.sha(fan.__file__)
    assert proof['native']['sha256'] == fan.NATIVE_SHA
    assert proof['constructor']['sha256'] == fan.CANDIDATE_SHA
    assert proof['production']['sha256'] == fan.PRODUCTION_SHA
    assert proof['targetVertexId'] == fan.TARGET_ID and proof['originalVertexId'] == fan.ORIGINAL_ID
    near = proof['actualNearest']
    assert near['sourceFaceId'] == fan.INHERITED_SOURCE_FACE
    assert near['sourceVertexIds'] == [56390, 56936, 56633]
    assert near['distanceM'] == 0 and near['pointExactlyOriginalVertex'] is True
    assert abs(near['dotTargetVertexNormal']-fan.REJECTED_DOT) < 1e-12
    assert proof['inheritedFaceExact'] is True and proof['inheritedFaceMaterialExact'] is True
    vertex = proof['nativeVertexEvidence']
    assert vertex['positionExact'] is True and vertex['originalVertexIdExact'] is True
    assert vertex['consistentVertexNormalDot'] >= .25
    # mathutils vectors and the recorded NumPy dot are float32 in native57.
    # Recompute at that storage precision; float64 arithmetic changes the
    # recorded result even though the serialized vector components are exact.
    normals = np.asarray([vertex['sourceNormal'], vertex['targetNormal']], dtype=np.float32)
    assert np.array_equal(normals.astype(np.float64), np.asarray([vertex['sourceNormal'], vertex['targetNormal']], dtype=np.float64))
    assert float(normals[0]@normals[1]) == vertex['consistentVertexNormalDot']


def ancestry(source, target, sp, tp):
    attribute = target.data.attributes.get('ProductionOriginalVertex')
    assert attribute is not None and attribute.domain == 'POINT' and attribute.data_type == 'INT', 'Exact original ancestry required'
    original = np.empty(len(tp), np.int32); attribute.data.foreach_get('value', original)
    assert np.all(original >= 0) and np.all(original < len(sp)), 'Invalid original vertex id'
    assert np.array_equal(tp, sp[original]), 'Orientation ancestry position changed'
    normal = np.empty_like(sp, dtype=np.float32)
    source.data.vertices.foreach_get('normal', normal.ravel())
    normal = normal.astype(float)
    assert np.isfinite(normal).all() and np.all(np.linalg.norm(normal[original], axis=1) > 0), 'Invalid donor vertex normal'
    return normal, original


def adapted_transfer_source(raw):
    source = kernel.adapted_transfer_source(raw)
    for old, new in [(OLD_SETUP, NEW_SETUP), (OLD_NORMAL, NEW_NORMAL)]:
        assert source.count(old) == 1, 'Frozen vertex-orientation patch drift'
        source = source.replace(old, new)
    return source


def install(engine, out, proof_pin):
    audit = kernel.Audit()
    namespace = dict(vars(engine), correspondence56=audit, ancestry57=ancestry)
    exec(compile(adapted_transfer_source(Path(engine.__file__).read_bytes()), str(engine.__file__)+'[orientation57]', 'exec'), namespace)
    frozen_transfer = namespace['transfer']
    orientation_report = {'status': 'UNACCEPTED_EXACT_ANCESTRY_VERTEX_NORMAL_POLICY', 'nativeProof': proof_pin,
        'comparison': 'Native source vertex normal at exact ProductionOriginalVertex versus native target vertex normal',
        'minimumNormalDot': .25, 'sourceBVHBearingChanged': False, 'sourceSkinInterpolationChanged': False,
        'sourceGeometryChanged': False, 'normalAttributesWritten': False,
        'limits': 'Vertex metric is now consistently vertex-to-vertex. Original geometric face-centroid orientation, edge/reverse surface, skin/contact/bake/motion gates remain required.'}

    def transfer(*args, **kwargs):
        try:
            result = frozen_transfer(*args, **kwargs)
            result['vertexOrientation57'] = orientation_report
            result['correspondenceKernel56'] = audit.report()
            return result
        finally:
            (out/'correspondence56.json').write_text(json.dumps(audit.report(), indent=2)+'\n')
            (out/'orientation57.json').write_text(json.dumps(orientation_report, indent=2)+'\n')

    engine.transfer = transfer
