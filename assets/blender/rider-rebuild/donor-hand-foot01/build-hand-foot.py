"""Selected appearance donors on the exact anatomical75 rig; no wearer edits."""
import hashlib
import json
from pathlib import Path


def buildHandFoot(body, rig, out):
    import bpy
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import barycentric_transform

    root = Path(__file__).resolve().parents[4]
    source = root / "assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02"
    out = Path(out) / "selected-hand-foot01"
    out.mkdir(parents=True, exist_ok=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert body.matrix_world.is_identity and len(body.data.vertices) == 10582
    xyz = [v.co.copy() for v in body.data.vertices]
    body.data.calc_loop_triangles()
    triangles = [list(t.vertices) for t in body.data.loop_triangles]
    names = {group.index: group.name for group in body.vertex_groups}
    body_fields = [{names[g.group]: g.weight for g in v.groups if g.weight > 0}
                   for v in body.data.vertices]
    objects, materials, records = [], [], []

    def material(item):
        mat = bpy.data.materials.new("ActualSelected" + item.capitalize())
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        principal = nodes.get("Principled BSDF")
        paths = [source / item / "baseColorTexture.png", source / item / "metallicRoughnessTexture.png"]
        base, packed = [bpy.data.images.load(str(p), check_existing=True) for p in paths]
        base.colorspace_settings.name = "sRGB"
        packed.colorspace_settings.name = "Non-Color"
        base.pack(); packed.pack()
        tex = nodes.new("ShaderNodeTexImage"); tex.image = base
        links.new(tex.outputs["Color"], principal.inputs["Base Color"])
        tex = nodes.new("ShaderNodeTexImage"); tex.image = packed
        split = nodes.new("ShaderNodeSeparateColor"); split.mode = "RGB"
        links.new(tex.outputs["Color"], split.inputs["Color"])
        links.new(split.outputs["Green"], principal.inputs["Roughness"])
        links.new(split.outputs["Blue"], principal.inputs["Metallic"])
        materials.append(mat)
        return mat, [{"path": str(p), "sha256": sha(p)} for p in paths]

    def original_corner_uv(item, prototype, faces):
        """Query exact dense donor triangles per corner, on the compact face's side."""
        dense_path = source / item / "cleaned-donor.npz"
        dense = dict(np.load(dense_path))
        prototype_xyz = prototype["vertices"]
        points = [Vector(row) for row in dense["vertices"]]
        source_faces = dense["faces"].tolist()
        tree = BVHTree.FromPolygons(points, source_faces, all_triangles=True)
        result, distances = [], []
        for face in faces:
            center = sum((Vector(prototype_xyz[i]) for i in face), Vector()) / 3
            row = []
            for index in face:
                vertex = Vector(prototype_xyz[index])
                # A tiny inward displacement resolves which side of an original UV seam
                # this compact triangle occupies. The UV remains source-corner based.
                hit, _, triangle_index, distance = tree.find_nearest(vertex.lerp(center, 1e-4))
                assert hit is not None
                original = source_faces[triangle_index]
                uv = dense["originalCornerUV"][triangle_index]
                value = barycentric_transform(hit, *(points[i] for i in original),
                    *(Vector((float(p[0]), float(p[1]), 0)) for p in uv))
                row.append((value.x, value.y)); distances.append(float(distance))
            result.append(row)
        return result, {"denseSource": {"path": str(dense_path), "sha256": sha(dense_path)},
                        "maximumCompactCornerProjectionMSourceUnits": max(distances)}

    def transferred(point, tree, target_faces):
        hit, _, triangle_index, _ = tree.find_nearest(point)
        face = target_faces[triangle_index]
        bary = barycentric_transform(hit, *(xyz[i] for i in face),
                                    Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        fields = {}
        for i, weight in zip(face, bary):
            for name, value in body_fields[i].items():
                fields[name] = fields.get(name, 0) + max(0, weight) * value
        four = sorted(((name, value) for name, value in fields.items() if value > .0001),
                      key=lambda row: (-row[1], row[0]))[:4]
        total = sum(value for _, value in four)
        assert total > 0
        return [(name, value / total) for name, value in four]

    def mesh(name, vertices, faces, uvs, fields, mat):
        data = bpy.data.meshes.new(name + "Mesh")
        data.from_pydata(vertices, [], faces); data.update()
        obj = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(obj)
        data.materials.append(mat)
        layer = data.uv_layers.new(name="UVMap")
        for polygon, corners in zip(data.polygons, uvs):
            polygon.use_smooth = True
            for loop, uv in zip(polygon.loop_indices, corners): layer.data[loop].uv = uv
        groups = {name: obj.vertex_groups.new(name=name) for name in sorted({n for row in fields for n, _ in row})}
        for index, row in enumerate(fields):
            for name, weight in row: groups[name].add([index], weight, "REPLACE")
        obj.parent = rig
        modifier = obj.modifiers.new("Exact shared anatomical75", "ARMATURE"); modifier.object = rig
        modifier.use_deform_preserve_volume = False
        objects.append(obj)
        return obj

    prototype_path = source / "boots/retopology-prototype.npz"
    prototype = dict(np.load(prototype_path))
    assert sha(prototype_path) == "d420da6bc7db4fa02ea095266dc174ff07cd3fb657cb0b01b91a319aa6b17853"
    original = prototype["vertices"]
    uvs, uv_report = original_corner_uv("boots", prototype, prototype["faces"])
    mat, maps = material("boots")
    low, high = original.min(0), original.max(0)
    for side, sign in (("R", -1), ("L", 1)):
        foot_names = {"DEF-foot." + side, "DEF-toe." + side}
        ids = [i for i, p in enumerate(xyz) if p.x * sign > 0 and p.z < .16
               and sum(body_fields[i].get(name, 0) for name in foot_names) > .25]
        assert len(ids) > 100
        wearer = np.array([tuple(xyz[i]) for i in ids])
        xmin, ymin, _ = wearer.min(0); xmax, ymax, _ = wearer.max(0)
        # Source toe is -X, source up is +Y, source lateral is Z. Fit the real
        # foot footprint with6mm total allowance, preserve the selected heel/toe.
        lateral_scale = (xmax - xmin + .012) / (high[2] - low[2])
        length_scale = (ymax - ymin + .014) / (high[0] - low[0])
        sole_z = rig.data.bones["SoleSocket." + side].head_local.z
        ankle = rig.data.bones["DEF-foot." + side].head_local
        height = ankle.z + .100 - sole_z
        height_scale = height / (high[1] - low[1])
        vertices = np.column_stack([
            (original[:, 2] - (low[2] + high[2]) / 2) * lateral_scale + (xmin + xmax) / 2,
            (original[:, 0] - (low[0] + high[0]) / 2) * length_scale + (ymin + ymax) / 2,
            (original[:, 1] - low[1]) * height_scale + sole_z])
        if side == "L": vertices[:, 0] = (xmin + xmax) - vertices[:, 0]
        faces = prototype["faces"] if side == "R" else prototype["faces"][:, ::-1]
        corner_uv = uvs if side == "R" else [row[::-1] for row in uvs]
        target_faces = [face for face in triangles if all(xyz[i].x * sign > 0 and xyz[i].z < .28 for i in face)]
        tree = BVHTree.FromPolygons(xyz, target_faces, all_triangles=True)
        fields = [transferred(Vector(point), tree, target_faces) for point in vertices]
        mesh("ActualSelectedBoot." + side, vertices.tolist(), faces.tolist(), corner_uv, fields, mat)
        records.append({"role": "boot." + side, "selectedPrototype": {"path": str(prototype_path), "sha256": sha(prototype_path)},
                        "maps": maps, "cornerUV": uv_report, "triangles": len(faces), "vertices": len(vertices),
                        "fitScales": [length_scale, height_scale, lateral_scale], "soleZ": sole_z,
                        "wearerFootBounds": [wearer.min(0).tolist(), wearer.max(0).tolist()],
                        "mirrored": side == "L", "reverseTriangleAndCornerUV": side == "L",
                        "skin": "Closest wearer triangle BVH, barycentric exact source fields, normalized FOUR; shared75 rig"})
    report = {"accepted": False, "recipeSHA256": sha(__file__), "objects": records,
              "gloves": "Pending proper selected source cavity repair; never replaced by body-offset proxy",
              "limits": ["Compact source edge-collapse topology is retained; per-corner original donor UV recovered",
                         "Actual boot surface coverage, sole compression and played deformation require parent review",
                         "Native/GPU tiny-weight cutoff applies to derived fields only; original wearer remains unchanged"]}
    report_path = out / "report.json"; report_path.write_text(json.dumps(report, indent=2) + "\n")
    return {"objects": objects, "materials": materials, "report": report, "reportPath": str(report_path)}
