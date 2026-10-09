"""Parent-only targeted native diagnostic; no construction, edits or broad scan.

Original guarded Blender invocation: --python native.py -- NEW_OUTPUT_DIRECTORY
Writes progress before native read, BVH construction and each targeted stage.
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fan


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(fan.ROOT/'harness/out/rider-rebuild/selected-boot-fold57') and not out.exists()
    out.mkdir(parents=True)
    report = fan.cpu_report()
    report.update(status='PARTIAL_NATIVE57_BEFORE_READ', recipeSHA256=fan.sha(__file__),
                  fanRecipeSHA256=fan.sha(fan.__file__),
                  native=fan.pin(fan.NATIVE, fan.NATIVE_SHA))
    def write(): (out/'diagnostic.json').write_text(json.dumps(report, indent=2)+'\n')
    write()
    try:
        fan.pin(fan.ENGINE, fan.ENGINE_SHA); engine = fan.load(fan.ENGINE, 'fold57_frozen25')
        bpy.ops.wm.open_mainfile(filepath=str(fan.NATIVE))
        source = bpy.data.objects['ActualSelectedBoot.L']
        target = bpy.data.objects['Production.full.ActualSelectedBoot.L']
        target_id = fan.TARGET_ID; original_id = fan.ORIGINAL_ID
        assert target.data.attributes['ProductionOriginalVertex'].data[target_id].value == original_id
        point = np.asarray(target.data.vertices[target_id].co)
        assert np.array_equal(point, np.asarray(source.data.vertices[original_id].co))
        tn = np.asarray(target.data.vertices[target_id].normal)
        sn = np.asarray(source.data.vertices[original_id].normal)
        report['nativeVertexEvidence'] = {'targetNormal': tn.tolist(), 'sourceNormal': sn.tolist(),
            'consistentVertexNormalDot': float(sn@tn), 'positionExact': True, 'originalVertexIdExact': True}
        report['status'] = 'PARTIAL_NATIVE57_NORMALS_BEFORE_BVH'; write()
        sp = engine.points(source); sf = engine.triangles(source)
        bvh = engine.tree(sp, sf); near = bvh.find_nearest(Vector(point), .001)
        assert near[0] is not None
        face_id = int(near[2]); triangle = sp[sf[face_id]]
        normal = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0]); normal /= np.linalg.norm(normal)
        report['actualNearest'] = {'sourceFaceId': face_id, 'sourceVertexIds': sf[face_id].tolist(),
            'point': list(near[0]), 'distanceM': float(near[3]), 'geometricNormal': normal.tolist(),
            'dotTargetVertexNormal': float(normal@tn),
            'pointExactlyOriginalVertex': np.array_equal(np.asarray(near[0]), sp[original_id])}
        report['status'] = 'PARTIAL_NATIVE57_BEARING_BEFORE_FANS'; write()
        report['nativeSourceFan'] = fan.face_fan(sp, sf, original_id)
        tp = engine.points(target); tf = engine.triangles(target)
        original = np.empty(len(tp), np.int32)
        target.data.attributes['ProductionOriginalVertex'].data.foreach_get('value', original)
        report['nativeTargetFan'] = fan.face_fan(tp, tf, target_id, original)
        assert face_id == fan.INHERITED_SOURCE_FACE, ('Unexpected native bearing', face_id)
        assert report['actualNearest']['pointExactlyOriginalVertex'] and float(near[3]) == 0
        assert abs(float(normal@tn)-fan.REJECTED_DOT) < 1e-12
        for native_fan, cpu_fan in [(report['nativeSourceFan'], report['sourceFan']),
                                   (report['nativeTargetFan'], report['targetFan'])]:
            assert len(native_fan['incidentFaces']) == len(cpu_fan['incidentFaces'])
            assert all(a['faceId'] == b['faceId'] and a['positions'] == b['positions']
                       for a, b in zip(native_fan['incidentFaces'], cpu_fan['incidentFaces']))
        assert np.array_equal(sf[face_id], original[tf[fan.INHERITED_TARGET_FACE]])
        assert np.array_equal(sp[sf[face_id]], tp[tf[fan.INHERITED_TARGET_FACE]])
        assert float(sn@tn) >= .25
        report['status'] = 'CONFIRMED_INHERITED_FACE_ZERO_DISTANCE_VERTEX_TIE_UNACCEPTED'; write()
    except Exception as error:
        report.update(status='REJECTED_OR_INCOMPLETE_NATIVE57', failure=repr(error)); write(); raise


if __name__ == '__main__': main()
