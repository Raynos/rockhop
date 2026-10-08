"""Exact-input body face subset; source-only until the parent's guarded run.

Library: freeze_and_apply(body, rig, equipped, source_pin, manifest=None).
CLI: blender -b -t 2 --python-exit-code 1 --python apply.py -- CONFIG FRESH_OUT
No render, bake, fitting, rig changes, player files or garment modification.
"""
import hashlib
import json
from pathlib import Path
import sys

import bmesh
import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import mask_core as core

POLYGON_ID = "OutfitSourcePolygonId"
CORNER_ID = "OutfitSourceCornerId"
SOURCE_NORMAL = "OutfitExactSourceCornerNormal"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while block := handle.read(1024 * 1024): h.update(block)
    return h.hexdigest()


def read(rows, field, width=1, dtype=np.float32):
    result = np.empty(len(rows) * width, dtype=dtype)
    rows.foreach_get(field, result)
    return result.reshape((-1, width)) if width > 1 else result


def rest(rig):
    return [(b.name, b.parent.name if b.parent else None, tuple(b.head_local),
             tuple(b.tail_local), [list(r) for r in b.matrix_local], b.use_deform)
            for b in rig.data.bones]


def fields(body, names):
    lookup = {g.index: names.index(g.name) for g in body.vertex_groups if g.name in names}
    weights = np.zeros((len(body.data.vertices), len(names)), dtype=np.float32)
    for vertex in body.data.vertices:
        for g in vertex.groups:
            if g.group in lookup: weights[vertex.index, lookup[g.group]] = g.weight
    return weights


def snapshot(body, rig):
    mesh = body.data
    assert body.type == "MESH" and rig.type == "ARMATURE" and len(rig.data.bones) == 75
    assert body.matrix_world.is_identity and rig.matrix_world.is_identity
    assert mesh.shape_keys is None, "This exact native body lane has no shape keys; do not silently drop new ones"
    armatures = [m for m in body.modifiers if m.type == "ARMATURE" and m.show_viewport and m.show_render]
    assert len(armatures) == 1 and armatures[0].object == rig, "Body must use the sole shared75 deform target"
    names = [b.name for b in rig.data.bones]
    return {"vertices": read(mesh.vertices, "co", 3),
            "loop_vertices": read(mesh.loops, "vertex_index", dtype=np.int32),
            "starts": read(mesh.polygons, "loop_start", dtype=np.int32),
            "totals": read(mesh.polygons, "loop_total", dtype=np.int32),
            "weights": fields(body, names), "names": names,
            "heads": np.array([b.head_local[:] for b in rig.data.bones], dtype=np.float64),
            "tails": np.array([b.tail_local[:] for b in rig.data.bones], dtype=np.float64),
            "normals": read(mesh.corner_normals, "vector", 3),
            "uv": {layer.name: read(layer.data, "uv", 2) for layer in mesh.uv_layers},
            "material_ids": read(mesh.polygons, "material_index", dtype=np.int32),
            "smooth": read(mesh.polygons, "use_smooth", dtype=bool),
            "materials": [m.as_pointer() if m else None for m in mesh.materials],
            "rigRest": rest(rig)}


def body_manifest(body, rig, source_pin):
    data = snapshot(body, rig)
    manifest = core.frozen_manifest(*(data[k] for k in (
        "vertices", "loop_vertices", "starts", "totals", "weights", "names", "heads", "tails")), source_pin)
    # A full hierarchy/rest-matrix pin supplements the policy's endpoint pin.
    manifest["rigRestSHA256"] = hashlib.sha256(json.dumps(data["rigRest"]).encode()).hexdigest()
    body.data.calc_loop_triangles()
    triangles = np.array([t.polygon_index for t in body.data.loop_triangles], dtype=np.int32)
    manifest["triangles"] = len(triangles)
    manifest["garmentTriangleIds"] = {
        name: np.flatnonzero(np.isin(triangles, ids)).tolist()
        for name, ids in manifest["garmentPolygonIds"].items()}
    return manifest, data


def verify_original(data, body, rig):
    current = snapshot(body, rig)
    for name in data:
        if isinstance(data[name], np.ndarray):
            assert np.array_equal(data[name], current[name]), ("Original body changed", name)
        elif name == "uv":
            assert data[name].keys() == current[name].keys()
            for layer in data[name]: assert np.array_equal(data[name][layer], current[name][layer]), layer
        else: assert data[name] == current[name], ("Original body or shared75 changed", name)


def freeze_and_apply(body, rig, equipped, source_pin, manifest=None):
    """Freeze actual native polygons, then create a derivative using only those IDs.

    The full source object stays in place as a hidden reference. All original
    vertices remain at the same indices, including unused covered vertices.
    No imported body, second skeleton, garment geometry or material is created.
    Returns (render_body, exact_manifest, numerical_receipt).
    """
    actual, before = body_manifest(body, rig, source_pin)
    def triangle_key(polygon, corners):
        corners = tuple(map(int, corners))
        return (int(polygon), min(corners[i:] + corners[:i] for i in range(3)))
    original_triangles = {
        triangle_key(t.polygon_index, t.loops): i for i, t in enumerate(body.data.loop_triangles)}
    assert len(original_triangles) == actual["triangles"]
    if manifest is not None:
        core.validate_manifest(manifest, actual)
        assert manifest["rigRestSHA256"] == actual["rigRestSHA256"], "Changed shared75 rest"
        assert manifest["garmentTriangleIds"] == actual["garmentTriangleIds"], "Stale triangle ancestry"
    else: manifest = actual
    hidden_ids = core.equipped_ids(manifest, equipped)
    assert len(hidden_ids) < len(body.data.polygons), "Mask cannot remove the entire wearer"
    render = body.copy()
    render.data = body.data.copy()
    render.name = body.name + "__SelectedOutfitRender"
    render.data.name = body.data.name + "__ExactFaceSubset"
    for col in body.users_collection: col.objects.link(render)
    mesh = render.data
    for name in (POLYGON_ID, CORNER_ID, SOURCE_NORMAL):
        assert name not in mesh.attributes, ("Already masked body or conflicting source attribute", name)
    attr = mesh.attributes.new(POLYGON_ID, "INT", "FACE")
    attr.data.foreach_set("value", np.arange(len(mesh.polygons), dtype=np.int32))
    attr = mesh.attributes.new(CORNER_ID, "INT", "CORNER")
    attr.data.foreach_set("value", np.arange(len(mesh.loops), dtype=np.int32))
    attr = mesh.attributes.new(SOURCE_NORMAL, "FLOAT_VECTOR", "CORNER")
    attr.data.foreach_set("vector", before["normals"].ravel())
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        poly_id = bm.faces.layers.int.get(POLYGON_ID)
        assert poly_id is not None
        hidden = set(hidden_ids)
        faces = [f for f in bm.faces if f[poly_id] in hidden]
        assert len(faces) == len(hidden_ids)
        bmesh.ops.delete(bm, geom=faces, context="FACES_ONLY")
        bm.to_mesh(mesh)
    finally: bm.free()
    mesh.update()
    poly_rows = read(mesh.attributes[POLYGON_ID].data, "value", dtype=np.int32)
    corner_rows = read(mesh.attributes[CORNER_ID].data, "value", dtype=np.int32)
    assert len(poly_rows) == len(before["starts"]) - len(hidden_ids)
    assert set(poly_rows) == set(range(len(before["starts"]))) - set(hidden_ids)
    assert len(corner_rows) == int(before["totals"][poly_rows].sum())
    source_normals = before["normals"][corner_rows]
    assert np.array_equal(read(mesh.attributes[SOURCE_NORMAL].data, "vector", 3), source_normals)
    # BMesh does not preserve compressed custom split normals. Restore the exact
    # source vectors by original corner IDs, retain the float source attribute,
    # and report re-encoding error separately instead of claiming byte equality.
    mesh.normals_split_custom_set(source_normals.tolist())
    mesh.update()
    after = snapshot(render, rig)
    for key in ("vertices", "weights"):
        assert np.array_equal(after[key], before[key]), ("Changed source rows", key)
    assert np.array_equal(after["loop_vertices"], before["loop_vertices"][corner_rows])
    for key in ("material_ids", "smooth"):
        assert np.array_equal(after[key], before[key][poly_rows]), ("Changed polygon data", key)
    assert after["materials"] == before["materials"] and after["rigRest"] == before["rigRest"]
    assert after["uv"].keys() == before["uv"].keys()
    for layer, values in after["uv"].items():
        assert np.array_equal(values, before["uv"][layer][corner_rows]), ("Changed genuine UV", layer)
    normal_error = np.linalg.norm(after["normals"] - source_normals, axis=1)
    assert np.isfinite(normal_error).all()
    verify_original(before, body, rig)
    body.hide_render = True; body.hide_viewport = False; body.hide_set(True)
    render.hide_render = False; render.hide_viewport = False; render.hide_set(False)
    render["acceptedArt"] = False
    render["outfitBodyMaskGarments"] = json.dumps(list(equipped))
    render["outfitFullBodyReference"] = body.name
    render["outfitBodyMaskTopologySHA256"] = manifest["bodyTopologySHA256"]
    mesh.calc_loop_triangles()
    source_triangles = []
    for t in mesh.loop_triangles:
        key = triangle_key(poly_rows[t.polygon_index], corner_rows[list(t.loops)])
        assert key in original_triangles, "Subset changed original polygon triangulation or winding"
        source_triangles.append(original_triangles[key])
    expected_triangles = {i for i, t in enumerate(body.data.loop_triangles) if t.polygon_index not in hidden}
    assert set(source_triangles) == expected_triangles, "Lost or duplicated source triangle"
    receipt = {"acceptedArt": False, "renderBody": render.name, "fullBodyReference": body.name,
               "equipped": list(equipped), "removedSourcePolygonIds": hidden_ids,
               "keptSourcePolygonIds": poly_rows.tolist(), "keptSourceCornerIds": corner_rows.tolist(),
               "keptSourceTriangleIds": source_triangles,
               "renderTriangles": len(mesh.loop_triangles), "originalTriangles": manifest["triangles"],
               "allOriginalVertexRowsWeightsUVMaterialsPreserved": True,
               "originalFullBodyAnd75RestUnchanged": True,
               "exactSourceCornerNormalsRetainedAsFloatAttribute": SOURCE_NORMAL,
               "evaluatedCornerNormalMaxError": float(normal_error.max(initial=0)),
               "evaluatedCornerNormalP99Error": float(np.quantile(normal_error, .99)) if len(normal_error) else 0.,
               "evaluatedCornerNormalsByteIdentical": bool(np.array_equal(after["normals"], source_normals)),
               "normalStatus": "MEASURED_REENCODING_RESIDUAL_REQUIRES_PARENT_GATE",
               "limits": manifest["limits"]}
    assert len(source_triangles) == len(mesh.loop_triangles), "Subset changed native triangulation count"
    return render, manifest, receipt


def set_full_body_reference(render, full_body, enabled):
    """Explicit diagnostic toggle; never show both body surfaces together."""
    assert render["outfitFullBodyReference"] == full_body.name
    for obj, show in ((render, not enabled), (full_body, enabled)):
        obj.hide_render = not show; obj.hide_viewport = False; obj.hide_set(not show)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    assert len(args) == 2
    config_path, out = map(lambda x: Path(x).resolve(), args)
    config = json.loads(config_path.read_text())
    assert not out.exists() and out.is_relative_to(ROOT / "harness/out/rider-rebuild/outfit-body-mask01")
    row = config["inputNative"]
    source = ROOT / row["path"]
    assert sha(source) == row["sha256"], "Changed actual selected input native"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    body = bpy.data.objects[config["bodyObject"]]
    rig = bpy.data.objects[config["rigObject"]]
    for name in config["requiredVisibleGarmentObjects"]:
        obj = bpy.data.objects[name]
        assert obj.type == "MESH" and not obj.hide_render and not obj.hide_get(), name
    render, manifest, receipt = freeze_and_apply(body, rig, config["equipped"], row)
    out.mkdir(parents=True)
    candidate = out / "editable-selected-outfit-body-mask.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(candidate), compress=True)
    receipt["candidate"] = {"path": str(candidate.relative_to(ROOT)), "sha256": sha(candidate)}
    receipt["source"] = row
    receipt["recipeSHA256"] = sha(__file__)
    receipt["coreSHA256"] = sha(HERE / "mask_core.py")
    assert sha(source) == row["sha256"], "Original file changed"
    (out / "body-mask-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "report.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"candidate": receipt["candidate"], "normalError": receipt["evaluatedCornerNormalMaxError"],
                      "removedPolygons": len(receipt["removedSourcePolygonIds"])}), flush=True)


if __name__ == "__main__": main()
