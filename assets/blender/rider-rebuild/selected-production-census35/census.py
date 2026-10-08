"""Read-only census of the already-saved rejected boot; no reconstruction.

Parent bounded Blender job: -- INPUT NEW_OUT. Checkpoint every completed scan,
and every65536 points during reverse scans. Unchanged native is never resaved.
"""
import importlib.util
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from regions import connected_regions


def normals(points, faces):
    cross = np.cross(points[faces[:, 1]]-points[faces[:, 0]], points[faces[:, 2]]-points[faces[:, 0]])
    length = np.linalg.norm(cross, axis=1)
    return cross/np.maximum(length[:, None], 1e-30), length/2


def read_array(collection, prop, width, dtype):
    result = np.empty((len(collection), width), dtype)
    collection.foreach_get(prop, result.ravel())
    return result


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    input_path = Path(args[0]).resolve(); out = Path(args[1]).resolve()
    manifest = json.loads(input_path.read_text())
    spec = importlib.util.spec_from_file_location('census35_frozen25', ROOT/manifest['pins']['productionAuthor']['path'])
    engine = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
    for row in manifest['pins'].values(): engine.pin(row)
    config = json.loads(engine.pin(manifest['pins']['productionInput']).read_text())
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-production-census35') and not out.exists()
    bpy.ops.wm.open_mainfile(filepath=str(engine.pin(manifest['pins']['rejectedNative'])))
    source = bpy.data.objects['ActualSelectedBoot.L']; target = bpy.data.objects['Production.full.ActualSelectedBoot.L']
    rig = bpy.data.objects[config['rig']]; assert len(rig.data.bones) == 75
    sp = engine.points(source); sf = engine.triangles(source); tp = engine.points(target); tf = engine.triangles(target)
    assert len(sf) == 610934 and len(tf) == 8000
    sn, sa = normals(sp, sf); tn, ta = normals(tp, tf)
    limit = config['objects'][source.name]['maximumSurfaceErrorM']; minimum_dot = config['transfer']['minimumNormalDot']
    out.mkdir(parents=True)
    report = {'status': 'INCOMPLETE_REJECTED_BOOT_CENSUS', 'acceptedArt': False, 'sourcePins': manifest['pins'],
        'recipeSHA256': engine.sha(__file__), 'inputSHA256': engine.sha(input_path),
        'sourceVertices': len(sp), 'sourceTriangles': len(sf), 'targetVertices': len(tp), 'targetTriangles': len(tf),
        'surfaceBoundM': limit, 'minimumNormalDot': minimum_dot, 'stages': {},
        'limits': 'Finite-sample source orientation/surface census, not continuous Hausdorff, self-intersection, posed contact, full FOUR or art acceptance. No mesh, normal, field or native edits.'}
    def write(): (out/'census.json').write_text(json.dumps(report, indent=2)+'\n')
    write()
    names = [g.name for g in source.vertex_groups if g.name in rig.data.bones]
    weights = engine.skin_rows(source, names)
    loop_ids = read_array(source.data.loop_triangles, 'loops', 3, np.int32)
    # Exact source arrays for a later single ancestry-preserving constructor.
    # Nothing invokes meshoptimizer here; source UV/map donors remain native.
    arrays = {'positions': sp.astype(np.float32), 'triangles': sf, 'triangleLoopIds': loop_ids,
              'vertexNormals': read_array(source.data.vertices, 'normal', 3, np.float32),
              'cornerNormals': read_array(source.data.corner_normals, 'vector', 3, np.float32),
              'namedWeights': weights.astype(np.float32),
              'faceMaterialIds': np.asarray([tri.material_index for tri in source.data.loop_triangles], np.int32)}
    for index, layer in enumerate(source.data.uv_layers):
        arrays['uvLayer'+str(index)] = read_array(layer.data, 'uv', 2, np.float32)
    layout = {}; binary = out/'exact-source-arrays.bin'
    with binary.open('wb') as stream:
        for name, array in arrays.items():
            layout[name] = {'byteOffset': stream.tell(), 'dtype': array.dtype.str, 'shape': list(array.shape), 'byteLength': array.nbytes}
            stream.write(memoryview(np.ascontiguousarray(array)).cast('B'))
    report['sourceArrayPackage'] = {'path': str(binary.relative_to(ROOT)), 'sha256': engine.sha(binary),
        'layout': layout, 'groupNames': names, 'uvLayerNames': [layer.name for layer in source.data.uv_layers],
        'sourceVertexIds': 'Zero-based original native vertex ordinals; triangleLoopIds retain exact corner ownership.',
        'coordinateFrame': 'Original mesh local coordinates in meters; parent/world bind unchanged in pinned rejected native.'}
    del arrays, loop_ids
    write()
    source_tree = engine.tree(sp, sf); target_tree = engine.tree(tp, tf)

    def scan(stage, query, tree, query_normals=None, reference_normals=None):
        count = len(query); distances = np.full(count, np.nan, np.float32)
        face_ids = np.full(count, -1, np.int32); dots = np.full(count, np.nan, np.float32)
        def checkpoint(done):
            path = out/(stage+'.npz')
            np.savez(path, distanceM=distances, nearestFaceId=face_ids, normalDot=dots,
                     completedCount=np.asarray(done), totalCount=np.asarray(count))
            finite = distances[:done][np.isfinite(distances[:done])]
            valid_dots = dots[:done][np.isfinite(dots[:done])]
            report['stages'][stage] = {'completedCount': done, 'totalCount': count, 'complete': done == count,
                'maximumDistanceM': float(finite.max()) if len(finite) else None,
                'over1mmCount': int(np.count_nonzero(distances[:done] > limit)),
                'missingNearestCount': int(np.count_nonzero(face_ids[:done] < 0)),
                'normalBelowOriginalLimitCount': int(np.count_nonzero(valid_dots < minimum_dot)),
                'normalNegativeCount': int(np.count_nonzero(valid_dots < 0)),
                'minimumNormalDot': float(valid_dots.min()) if len(valid_dots) else None,
                'arrays': {'path': str(path.relative_to(ROOT)), 'sha256': engine.sha(path)}}
            write(); print(json.dumps({'stage': stage, 'completed': done, 'total': count}), flush=True)
        for i, point in enumerate(query):
            near = tree.find_nearest(Vector(point))
            if near[0] is not None:
                distances[i] = near[3]; face_ids[i] = near[2]
                if query_normals is not None: dots[i] = query_normals[i] @ reference_normals[near[2]]
            if (i+1) % 65536 == 0: checkpoint(i+1)
        checkpoint(count)
        return distances, face_ids, dots

    vertex_normals = read_array(target.data.vertices, 'normal', 3, np.float32)
    vd, vi, vn = scan('target-vertices', tp, source_tree, vertex_normals, sn)
    fd, fi, fn = scan('target-face-centroids', tp[tf].mean(axis=1), source_tree, tn, sn)
    ancestry = read_array(target.data.attributes['ProductionOriginalVertex'].data, 'value', 1, np.int32).ravel()
    assert np.all((ancestry >= 0) & (ancestry < len(sp)))
    source_vertex_normals = read_array(source.data.vertices, 'normal', 3, np.float32)
    corner_dots = np.einsum('ij,ikj->ik', tn, source_vertex_normals[ancestry[tf]])
    failure_faces = np.flatnonzero((fn < minimum_dot) | (fd > limit) | np.any(vn[tf] < minimum_dot, axis=1) | (ta == 0))
    regions = []
    for ids in connected_regions(tf, failure_faces):
        points = tp[np.unique(tf[ids])]
        regions.append({'faceIds': ids, 'triangleCount': len(ids), 'areaM2': float(ta[ids].sum()),
            'boundsLocal': [points.min(axis=0).tolist(), points.max(axis=0).tolist()],
            'negativeCentroidNormals': int(np.count_nonzero(fn[ids] < 0)),
            'allAncestryCornerNormalsOpposed': int(np.count_nonzero(np.max(corner_dots[ids], axis=1) < 0))})
    path = out/'target-fold-provenance.npz'
    np.savez(path, targetPointsLocal=tp.astype(np.float32), targetFaces=tf,
             targetVertexSourceAncestry=ancestry, sourceAncestryDisplacementM=np.linalg.norm(tp-sp[ancestry], axis=1),
             targetFaceAreaM2=ta, targetFaceNormal=tn, faceNormalDotOriginalAncestryCornerNormals=corner_dots,
             originalSourceFaceAreaM2=sa, failureFaceIds=failure_faces)
    report['orientationRegions'] = {'regions': regions, 'count': len(regions),
        'arrays': {'path': str(path.relative_to(ROOT)), 'sha256': engine.sha(path)},
        'ancestryLimitation': 'Recorded original-vertex integer attribute is a diagnostic anchor, not full collapsed-face provenance.'}
    write()
    edges = np.unique(np.sort(np.concatenate([tf[:, [0, 1]], tf[:, [1, 2]], tf[:, [2, 0]]]), axis=1), axis=0)
    scan('target-edge-midpoints', tp[edges].mean(axis=1), source_tree)
    # Each completed forward stage is on disk before either larger reverse pass.
    scan('source-vertices', sp, target_tree)
    scan('source-face-centroids', sp[sf].mean(axis=1), target_tree, sn, tn)
    report['status'] = 'COMPLETED_REJECTED_BOOT_CENSUS_UNACCEPTED'; write()


if __name__ == '__main__': main()
