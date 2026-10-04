"""Localize baseline garment/head surface contacts without changing either."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

parser = argparse.ArgumentParser(description=__doc__)
for name in ["flat", "smooth", "four", "out"]:
    parser.add_argument("--" + name, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
paths = {key: Path(getattr(args, key)).resolve() for key in ["flat", "smooth", "four"]}
out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)
assert not (out / "contacts.json").exists()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
pins = {str(path): sha(path) for path in paths.values()}
expected = {
    "flat": "86b85d476b13f709ba832e11dfcd14a17f071f5af69f3ebbbaf7dd1dbe6f58f9",
    "smooth": "c732d98076f6b9b1a209a45e8a0cddf793484807ea8b3ae9011fa4f82c151df0",
    "four": "4a0904b94a507f35590d1ec4ebfe763237fa5fb21fa189573842309cb776a0ad",
}
assert all(pins[str(paths[key])] == expected[key] for key in paths)
def surface(obj):
    obj.hide_set(False)
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vertices = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    triangles = np.array([t.vertices[:] for t in mesh.loop_triangles])
    polygons = np.array([t.polygon_index for t in mesh.loop_triangles])
    evaluated.to_mesh_clear()
    tree = BVHTree.FromPolygons([Vector(v) for v in vertices], triangles.tolist(), all_triangles=True)
    return vertices, triangles, polygons, tree
def intersect_segment(start, end, tri):
    normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
    normal_length = np.linalg.norm(normal)
    direction = end - start
    segment_length = np.linalg.norm(direction)
    if normal_length < 1e-14 or segment_length < 1e-14:
        return None, "degenerate"
    denominator = normal @ direction
    if abs(denominator) < 1e-12 * normal_length * segment_length:
        coplanar = max(abs(normal @ (start - tri[0])), abs(normal @ (end - tri[0]))) / normal_length < 1e-9
        return None, "coplanar" if coplanar else "parallel"
    parameter = -(normal @ (start - tri[0])) / denominator
    if parameter < -1e-10 or parameter > 1 + 1e-10:
        return None, "outsideSegment"
    point = start + parameter * direction
    uv = np.linalg.lstsq(np.column_stack([tri[1] - tri[0], tri[2] - tri[0]]), point - tri[0], rcond=None)[0]
    bary = np.array([1 - uv.sum(), uv[0], uv[1]])
    if bary.min() < -1e-8:
        return None, "outsideTriangle"
    return point, "hit"
records = {}
baseline_native = None
for key, path in paths.items():
    bpy.ops.wm.open_mainfile(filepath=str(path))
    object_name = "Actual donor explicit native-four skin, unaccepted" if key == "four" else "Actual selected donor, compact interior flow, unaccepted"
    garment = bpy.data.objects[object_name]
    head = bpy.data.objects["Protected textured head above hidden neck interface"]
    logical = bpy.data.objects["Canonical anatomical body, baked adult hm08"]
    head.hide_set(False)
    logical.hide_set(False)
    bpy.data.objects["Independent anatomical foundation rig"].hide_set(False)
    bpy.context.view_layer.update()
    native_xyz = np.array([v.co[:] for v in garment.data.vertices])
    if baseline_native is None:
        baseline_native = native_xyz
    assert np.array_equal(native_xyz, baseline_native)
    gv, gf, gp, gt = surface(garment)
    hv, hf, hp, ht = surface(head)
    lv, lf, lp, lt = surface(logical)
    pairs = gt.overlap(ht)
    translation = np.array(bpy.data.objects["Independent anatomical foundation rig"].matrix_world.translation)
    witnesses = []
    all_points = []
    for garment_id, head_id in pairs:
        garment_tri = gv[gf[garment_id]]
        head_tri = hv[hf[head_id]]
        points, flags = [], {}
        for edge_tri, target_tri in [(garment_tri, head_tri), (head_tri, garment_tri)]:
            for index in range(3):
                point, status = intersect_segment(edge_tri[index], edge_tri[(index + 1) % 3], target_tri)
                flags[status] = flags.get(status, 0) + 1
                if point is not None and all(np.linalg.norm(point - other) > 1e-9 for other in points):
                    points.append(point)
        all_points.extend(points)
        native_points = [point - translation for point in points]
        witnesses.append({
            "garmentTriangle": int(garment_id), "garmentPolygon": int(gp[garment_id]),
            "garmentVertexIDs": gf[garment_id].tolist(),
            "headTriangle": int(head_id), "headPolygon": int(hp[head_id]), "headVertexIDs": hf[head_id].tolist(),
            "actualSegmentIntersectionPointsNative": [p.tolist() for p in native_points],
            "segmentTests": flags, "coplanarNeedsSeparateTest": not points and flags.get("coplanar", 0) > 0,
            "garmentTriangleNativeXYZ": (garment_tri - translation).tolist(),
            "headTriangleNativeXYZ": (head_tri - translation).tolist(),
        })
    contact_vertices = sorted({int(vertex) for garment_id, head_id in pairs for vertex in gf[garment_id]})
    points = np.array(all_points) - translation
    records[key] = {
        "garmentObject": object_name, "garmentSkinModifier": [m.type for m in garment.modifiers],
        "protectedHeadNativeContactPairs": len(pairs),
        "logicalBodyNativeContactPairs": len(gt.overlap(lt)),
        "pairsWithExplicitSegmentCrossing": sum(bool(w["actualSegmentIntersectionPointsNative"]) for w in witnesses),
        "coplanarUnresolvedPairs": sum(w["coplanarNeedsSeparateTest"] for w in witnesses),
        "otherNoSegmentCrossingPairs": sum(not w["actualSegmentIntersectionPointsNative"] and not w["coplanarNeedsSeparateTest"] for w in witnesses),
        "uniqueGarmentTriangles": len({i for i, j in pairs}),
        "uniqueHeadTriangles": len({j for i, j in pairs}),
        "uniqueGarmentContactVertices": len(contact_vertices),
        "intersectionPointNativeXYZBounds": [points.min(0).tolist(), points.max(0).tolist()] if len(points) else None,
        "garmentContactVertexNativeXYZBounds": [native_xyz[contact_vertices].min(0).tolist(), native_xyz[contact_vertices].max(0).tolist()],
        "headMaterialNames": [m.name for m in head.data.materials],
        "allPairs": witnesses,
    }
    print("BASELINE_PROTECTED_HEAD_CONTACTS", key, len(pairs), records[key]["pairsWithExplicitSegmentCrossing"], records[key]["intersectionPointNativeXYZBounds"], flush=True)
assert pins == {p: sha(p) for p in pins}
report = {
    "status": "UNACCEPTED readonly baseline garment/protected-head contact localization",
    "pins": pins, "recipeSHA256": sha(__file__), "variants": records,
    "nativeGarmentPositionsExactAcrossAllThree": True,
    "numerics": "Float64 segment-plane/barycentric calculations on actual Float32 evaluated world geometry: degeneracy1e-14,relative parallel1e-12,coplanar1nm,segment parameter1e-10,barycentric1e-8,point dedup1nm. World file-frame translation removed once for witness coordinates.",
    "limits": [
        "Exact original flat24,normal25,andfour26 are loaded; no pose driver, geometry/normal/weight/mask/material edits or source save. Body/head/original51bind unchanged.",
        "Surface contact localization only, not signed penetration depth, drawable alpha/culling classification, closed-head volume, independent Agent3 body/seam QA or appearance judgment. No contact waiver.",
        "No field retry, head trim, local/global garment shrink/rebuild, rest capture, inference, worker, Library/player promotion/publication. All24coverage,cuffs,native moving/M0-M5/mobile/export-engine normals open; parent played93 pending.",
    ],
}
(out / "contacts.json").write_text(json.dumps(report, indent=2) + "\n")
print("BASELINE_HEAD_CONTACT_LOCALIZATION_READY", flush=True)
