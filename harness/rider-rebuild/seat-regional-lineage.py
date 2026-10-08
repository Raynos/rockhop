"""Extract actual selected pelvis-rear native lineage only; no native/pose edits.
Parent: blender -b -t 2 --python-exit-code 1 --python THIS -- CONTEXT_UNIT REPORT FRESH_JSON
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def row(path): return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}

def main():
    context_path, report_path, output = (Path(p).resolve() for p in sys.argv[sys.argv.index('--')+1:])
    assert not output.exists()
    context, report = (json.loads(p.read_text()) for p in (context_path, report_path))
    assert context['part'] == 'Jeans' and context['visible'] == ['RiderJeans']
    native = ROOT/context['native']['path']
    assert context['native'] == report['resultNative'] and sha(native) == context['native']['sha256']
    capture = next(r for r in report['capture'] if r['region'] == 'pelvis-rear')
    capture_path = ROOT/capture['path']; assert capture['passed'] and sha(capture_path) == capture['sha256']
    requested = ['RiderJeans', 'RearOriginalReceiverUVReference']
    with bpy.data.libraries.load(str(native), link=False) as (available, selected):
        assert set(requested) <= set(available.objects); selected.objects = requested
    target, rear = selected.objects
    assert target.matrix_world.is_identity and rear.matrix_world.is_identity
    assert len(target.data.vertices) == report['finishedGarment']['vertices']
    assert len(target.data.polygons) == report['finishedGarment']['polygons']
    vertex_ids, face_ids = rear.data.attributes['BakeOriginalVertex'], rear.data.attributes['BakeOriginalFace']
    region = sorted({int(v.value) for v in face_ids.data})
    for polygon in rear.data.polygons:
        original = int(face_ids.data[polygon.index].value)
        ids = [int(vertex_ids.data[index].value) for index in polygon.vertices]
        assert set(ids) <= set(target.data.polygons[original].vertices)
        for index, identity in zip(polygon.vertices, ids):
            assert rear.data.vertices[index].co == target.data.vertices[identity].co
    with np.load(capture_path, allow_pickle=False) as arrays:
        sampled = sorted(set(int(v) for v in arrays['receiverOriginalFace']))
    assert set(sampled) <= set(region)
    target.data.calc_loop_triangles(); selected_faces = set(region)
    triangles = [{'originalPolygonID': face.polygon_index, 'nativeVertexIDs': list(face.vertices)}
                 for face in target.data.loop_triangles if face.polygon_index in selected_faces]
    used = sorted({v for triangle in triangles for v in triangle['nativeVertexIDs']})
    result = {'accepted': False, 'recipeSHA256': sha(__file__), 'region': 'pelvis-rear',
        'sourceContext': row(context_path), 'sourceReport': row(report_path), 'sourceNative': context['native'],
        'directCapture': {'path': capture['path'], 'sha256': capture['sha256']},
        'object': target.name, 'regionalObject': rear.name,
        'nativeVertexCount': len(target.data.vertices), 'nativePolygonCount': len(target.data.polygons),
        'originalPolygonIDs': region, 'sampledOriginalPolygonIDs': sampled,
        'nativeTriangles': triangles, 'nativeRestPositions': [[v, list(target.data.vertices[v].co)] for v in used],
        'regionalReceiverNativePositionsAndFaceMembershipExact': True,
        'classification': 'Existing original selected pelvis-rear transfer region; actual lower posterior/support identity requires parent review. Not an automatically authored buttock-floor patch.',
        'limits': 'Native region extraction only. No pose/geometry write, offset, contact or art acceptance.'}
    output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({'output': str(output), 'originalPolygons': len(region), 'nativeTriangles': len(triangles), 'nativeVertices': len(used), 'accepted': False}))

if __name__ == '__main__': main()
