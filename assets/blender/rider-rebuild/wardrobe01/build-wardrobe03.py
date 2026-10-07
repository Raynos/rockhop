"""Complete unaccepted wardrobe for the coherent Blender CC0 male body.

Integration only: runpy.run_path(...)["buildWardrobe"](body, rig, out).
The caller owns the Blender process, source, rig, native save, and art review.
Body vertex order must remain the selected 10,582 point source order. Geometry
copies source surface charts and normalized FOUR weights, never old donor skins.
"""

import json
import math
from pathlib import Path


def buildWardrobe(body, rig, out):
    import bpy
    import numpy as np
    from mathutils import Vector
    from mathutils.kdtree import KDTree

    out = Path(out) / "wardrobe"
    out.mkdir(parents=True, exist_ok=True)
    assert len(body.data.vertices) == 10582, "Selected CC0 source order required"
    assert body.matrix_world.is_identity, "Wardrobe uses normalized body local frame"
    body.data.update()
    scale = 1.78 / (1.684413195 - (-0.005547829))
    source_floor = -0.005547829
    source = [Vector((v.co.x / scale, v.co.y / scale,
                      v.co.z / scale + source_floor)) for v in body.data.vertices]
    xyz = [v.co.copy() for v in body.data.vertices]
    normals = [v.normal.copy() for v in body.data.vertices]
    names = {g.index: g.name for g in body.vertex_groups}
    deform = {b.name for b in rig.data.bones if b.use_deform}
    weights = []
    for v in body.data.vertices:
        row = [(names[g.group], g.weight) for g in v.groups
               if names[g.group] in deform and g.weight > 0]
        assert 1 <= len(row) <= 4, ("Normalized FOUR required", v.index, row)
        assert abs(sum(w for _, w in row) - 1) < 2e-5
        weights.append(row)

    cuff_frames = {}
    for side in ("L", "R"):
        wrist = rig.data.bones["DEF-hand." + side].head_local.copy()
        elbow = rig.data.bones["DEF-forearm." + side].head_local.copy()
        axis = (elbow - wrist).normalized()
        cuff_frames[side] = {"wrist": wrist, "elbow": elbow, "axis": axis,
                             "hoodie": wrist + axis * .035,
                             "glove": wrist + axis * .018}
    boundary_fields = {}

    def normalize_four(row):
        top = sorted(((n, w) for n, w in row.items() if w > 0),
                     key=lambda item: (-item[1], item[0]))[:4]
        total = sum(w for _, w in top)
        assert total > 0
        return [(n, w / total) for n, w in top]

    def mean_field(source_ids):
        row = {}
        for si in source_ids:
            for n, w in weights[si]:
                row[n] = row.get(n, 0) + w / len(source_ids)
        return normalize_four(row)

    def co(x, y, z):
        return Vector((x * scale, y * scale, (z - source_floor) * scale))

    all_tree = KDTree(len(xyz))
    for i, point in enumerate(xyz):
        all_tree.insert(point, i)
    all_tree.balance()
    thorax_ids = [i for i, p in enumerate(source)
                  if abs(p.x) < .075 and 1.22 < p.z < 1.38]
    thorax_tree = KDTree(len(thorax_ids))
    for i in thorax_ids:
        thorax_tree.insert(xyz[i], i)
    thorax_tree.balance()

    def palette(name, color, roughness, kind):
        """Small baked PBR images; no procedural shader unsupported by glTF."""
        size = 1024
        yy, xx = np.indices((size, size), dtype=np.float32)
        rng = np.random.default_rng(20261007 + len(materials))
        grain = rng.normal(0, .028, (size, size)).astype(np.float32)
        if kind == "denim":
            pattern = .06 * np.sin((xx + yy) * 2.1) + .024 * np.sin(xx * .39)
        elif kind == "rib":
            pattern = .065 * np.cos(xx * math.pi / 4) + .012 * np.sin(yy * 2.4)
        elif kind == "fabric":
            pattern = .019 * (np.sin(xx * 2.2) + np.sin(yy * 2.2))
        elif kind == "leather":
            pattern = .035 * np.sin(xx * .71) * np.sin(yy * .63)
        else:
            pattern = .007 * np.sin(yy * .6)
        factor = np.clip(1 + grain + pattern, .72, 1.2)
        pixels = np.ones((size, size, 4), dtype=np.float32)
        pixels[:, :, :3] = np.asarray(color)[None, None, :] * factor[:, :, None]
        image = bpy.data.images.new(name + "_BaseColor", size, size, alpha=False)
        image.colorspace_settings.name = "sRGB"
        image.pixels.foreach_set(pixels.ravel())
        image.filepath_raw = str(out / (name + "-basecolor.png"))
        image.file_format = "PNG"
        image.save()
        image.pack()
        # ORM-compatible packed image: G roughness, B metallic, R occlusion.
        mr = bpy.data.images.new(name + "_MetallicRoughness", 256, 256, alpha=False)
        mr.colorspace_settings.name = "Non-Color"
        packed = np.ones((256, 256, 4), dtype=np.float32)
        packed[:, :, 1] = np.clip(roughness + grain[::4, ::4] * .4, 0, 1)
        packed[:, :, 2] = 0
        mr.pixels.foreach_set(packed.ravel())
        mr.filepath_raw = str(out / (name + "-metallicroughness.png"))
        mr.file_format = "PNG"
        mr.save()
        mr.pack()
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        p = nodes.get("Principled BSDF")
        p.inputs["Roughness"].default_value = roughness
        base = nodes.new("ShaderNodeTexImage")
        base.image = image
        links.new(base.outputs["Color"], p.inputs["Base Color"])
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = mr
        split = nodes.new("ShaderNodeSeparateColor")
        split.mode = "RGB"
        links.new(tex.outputs["Color"], split.inputs["Color"])
        links.new(split.outputs["Green"], p.inputs["Roughness"])
        links.new(split.outputs["Blue"], p.inputs["Metallic"])
        mat.diffuse_color = (*color, 1)
        materials.append(mat)
        return mat

    materials = []
    mustard = palette("RiderMustardFleece", (.70, .43, .055), .87, "fabric")
    rib = palette("RiderMustardRib", (.59, .34, .038), .9, "rib")
    denim = palette("RiderIndigoDenim", (.045, .12, .245), .86, "denim")
    leather = palette("RiderBlackLeather", (.025, .028, .033), .53, "leather")
    rubber = palette("RiderBlackRubber", (.035, .038, .043), .92, "rubber")
    objects, reports = [], []

    def mesh_object(name, points, faces, ancestors, mats, face_mats=None,
                    face_uvs=None, region=4, point_fields=None):
        mesh = bpy.data.meshes.new(name + "Mesh")
        mesh.from_pydata([tuple(p) for p in points], [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        for mat in mats:
            mesh.materials.append(mat)
        uv = mesh.uv_layers.new(name="UVMap")
        for pi, polygon in enumerate(mesh.polygons):
            polygon.use_smooth = True
            polygon.material_index = face_mats[pi] if face_mats else 0
            for corner, li in enumerate(polygon.loop_indices):
                if face_uvs:
                    uv.data[li].uv = face_uvs[pi][corner]
                else:
                    point = points[mesh.loops[li].vertex_index]
                    uv.data[li].uv = (point.x * 10, point.z * 10)
        fields = point_fields if point_fields is not None else [weights[i] for i in ancestors]
        for row in fields:
            assert 1 <= len(row) <= 4 and abs(sum(w for _, w in row) - 1) < 2e-5
            assert all(n in deform for n, _ in row)
        for name_ in sorted({name_ for row in fields for name_, _ in row}):
            obj.vertex_groups.new(name=name_)
        for vi, row in enumerate(fields):
            for bone_name, weight in row:
                obj.vertex_groups[bone_name].add([vi], weight, "REPLACE")
        for attr_name, vals in (("_NATIVE_ID", range(len(points))),
                                ("_REGION_ID", [region] * len(points)),
                                ("_SOURCE_VERTEX_ID", ancestors)):
            a = mesh.attributes.new(attr_name, "INT", "POINT")
            a.data.foreach_set("value", list(vals))
        obj.parent = rig
        tri = obj.modifiers.new("FrozenRestTriangles", "TRIANGULATE")
        tri.quad_method = "FIXED"
        arm = obj.modifiers.new("SharedAnatomicalFour", "ARMATURE")
        arm.object = rig
        arm.use_deform_preserve_volume = False
        obj["accepted"] = False
        obj["source"] = "Blender CC0 realistic male; mapped surface construction"
        objects.append(obj)
        reports.append({"object": obj.name, "vertices": len(points),
                        "polygons": len(faces),
                        "triangles": sum(len(f) - 2 for f in faces),
                        "region": region, "sourceVertexIds": ancestors,
                        "fourField": "bounded authored boundary FOUR field" if point_fields is not None else "exact selected body row per point",
                        "supplementalField": "explicit nearest source row; no old skin"})
        return obj

    original_uv = body.data.uv_layers.active

    def patch(name, predicate, offset, mats, region, ease=None):
        selected = []
        for polygon in body.data.polygons:
            center = sum((source[i] for i in polygon.vertices), Vector()) / len(polygon.vertices)
            if predicate(center):
                selected.append(polygon)
        indices = sorted({i for p in selected for i in p.vertices})
        remap = {si: vi for vi, si in enumerate(indices)}
        points = []
        for si in indices:
            point = xyz[si] + normals[si] * offset
            if ease:
                point = ease(point, source[si], normals[si])
            points.append(point)
        faces, uvs = [], []
        for p in selected:
            faces.append([remap[i] for i in p.vertices])
            if original_uv:
                uvs.append([tuple(original_uv.data[li].uv * 10) for li in p.loop_indices])
            else:
                uvs.append([(points[remap[i]].x * 10, points[remap[i]].z * 10)
                            for i in p.vertices])
        edge_count = {}
        for f in faces:
            for a, b in zip(f, f[1:] + f[:1]):
                key = tuple(sorted((a, b)))
                if key not in edge_count:
                    edge_count[key] = [0, (a, b)]
                edge_count[key][0] += 1
        boundaries = [directed for count, directed in edge_count.values() if count == 1]
        face_mats = [0] * len(faces)
        # Continuous source boundary loops become regular garment planes.
        # One common skin blend per loop preserves a plane under linear skinning;
        # four neighboring mesh rows ease back into the existing body field.
        boundary_graph = {}
        for a, b in boundaries:
            boundary_graph.setdefault(a, set()).add(b)
            boundary_graph.setdefault(b, set()).add(a)
        assert all(len(row) == 2 for row in boundary_graph.values()), name
        remaining = set(boundary_graph)
        loop_controls = []
        while remaining:
            queue = [min(remaining)]
            component = set(queue)
            while queue:
                for vi in boundary_graph[queue.pop()]:
                    if vi not in component:
                        component.add(vi)
                        queue.append(vi)
            remaining -= component
            loop = sorted(component)
            center_source = sum((source[indices[vi]] for vi in loop), Vector()) / len(loop)
            target = None
            if name == "RiderHoodie":
                if center_source.z > 1.37:
                    kind = "collar"
                    center, axis = co(0, 0, 1.408), Vector((0, 0, 1))
                    # Actual native lower-neck/upper-thorax bones, no head field.
                    assert "DEF-spine.003" in deform and "DEF-spine.004" in deform
                    target = [("DEF-spine.003", .65), ("DEF-spine.004", .35)]
                elif abs(center_source.x) > .29:
                    side = "L" if center_source.x > 0 else "R"
                    kind = "cuff." + side
                    center, axis = cuff_frames[side]["hoodie"], cuff_frames[side]["axis"]
                else:
                    kind = "hem"
                    center, axis = co(0, 0, .997), Vector((0, 0, 1))
                target = target or mean_field([indices[vi] for vi in loop])
            elif name == "RiderGloves":
                side = "L" if center_source.x > 0 else "R"
                kind = "cuff." + side
                center, axis = cuff_frames[side]["glove"], cuff_frames[side]["axis"]
                target = mean_field([indices[vi] for vi in loop])
            if target:
                for vi in loop:
                    points[vi] -= axis * (points[vi] - center).dot(axis)
                boundary_fields[(name, kind)] = target
                loop_controls.append({"kind": kind, "points": loop,
                                      "center": center, "axis": axis, "field": target})
        # Open boundary gets an inward lip, never a blind wrist/ankle cap.
        rim_indices = {}
        thickness = .0025 if region == 6 else .004
        for vi in sorted({v for e in boundaries for v in e}):
            si = indices[vi]
            rim_indices[vi] = len(points)
            points.append(points[vi] - normals[si] * thickness)
            indices.append(si)
        for a, b in boundaries:
            faces.append([b, a, rim_indices[a], rim_indices[b]])
            uvs.append([(0, 0), (1, 0), (1, .06), (0, .06)])
            face_mats.append(min(1, len(mats) - 1))
        fields = None
        if loop_controls:
            graph = [set() for _ in points]
            for face in faces:
                for a, b in zip(face, face[1:] + face[:1]):
                    graph[a].add(b)
                    graph[b].add(a)
            fields = [weights[si] for si in indices]
            for control in loop_controls:
                seeds = control["points"] + [rim_indices[vi] for vi in control["points"]]
                # Inner and outer rim are the same plane and common field.
                for vi in seeds:
                    points[vi] -= control["axis"] * (points[vi] - control["center"]).dot(control["axis"])
                distances = {vi: 0 for vi in seeds}
                frontier = seeds
                for step in range(1, 5):
                    next_frontier = []
                    for vi in frontier:
                        for neighbor in graph[vi]:
                            if neighbor not in distances:
                                distances[neighbor] = step
                                next_frontier.append(neighbor)
                    frontier = next_frontier
                for vi, distance in distances.items():
                    t = distance / 4
                    strength = 1 - 3 * t * t + 2 * t * t * t
                    row = {n: w * (1 - strength) for n, w in weights[indices[vi]]}
                    for n, w in control["field"]:
                        row[n] = row.get(n, 0) + w * strength
                    fields[vi] = normalize_four(row)
                control["neighborSupportPoints"] = len(distances)
        result = mesh_object(name, points, faces, indices, mats, face_mats, uvs, region,
                             point_fields=fields)
        reports[-1]["boundaryEdges"] = len(boundaries)
        reports[-1]["openWearableLips"] = True
        reports[-1]["sourceBodyFaces"] = [p.index for p in selected]
        if loop_controls:
            reports[-1]["conditionedBoundaryLoops"] = [
                {"kind": control["kind"], "nativeBoundaryPointIds": control["points"],
                 "centerMetres": list(control["center"]), "axis": list(control["axis"]),
                 "commonFourField": control["field"], "smoothFalloffMeshRows": 4,
                 "neighborSupportPoints": control["neighborSupportPoints"]}
                for control in loop_controls]
            reports[-1]["authoredFourRows"] = fields
        return result

    def hoodie_ease(point, p, n):
        if abs(p.x) < .245 and .98 < p.z < 1.31:
            point.x += math.copysign(.008 * scale, p.x) if abs(p.x) > .04 else 0
            point.y += math.copysign(.015 * scale, p.y + .025)
        return point

    hoodie = patch("RiderHoodie", lambda p: p.z < 1.408 and
                   (p.z > .987 if abs(p.x) < .245 else p.z > .914),
                   .024, [mustard, rib], 4, hoodie_ease)
    jeans = patch("RiderJeans", lambda p: abs(p.x) < .275 and .14 < p.z < 1.025,
                  .014, [denim], 5)
    gloves = patch("RiderGloves", lambda p: abs(p.x) > .285 and p.z < .913,
                   .0038, [leather], 6)
    shoes = patch("RiderShoeAnkles", lambda p: abs(p.x) < .30 and .122 < p.z < .154,
                  .010, [leather, rubber], 7)

    def ring_band(name, center, axis_u, axis_v, radius_u, radius_v,
                  height, mat, region, segments=40, field=None):
        center, u, v = Vector(center), Vector(axis_u), Vector(axis_v)
        axis = u.cross(v).normalized()
        points, ancestors = [], []
        for h, dr in ((-height / 2, 0), (height / 2, 0),
                      (height / 2, -.004), (-height / 2, -.004)):
            for j in range(segments):
                angle = math.tau * j / segments
                pt = center + u * ((radius_u + dr) * math.cos(angle)) + \
                    v * ((radius_v + dr) * math.sin(angle)) + axis * h
                points.append(pt)
                ancestors.append(all_tree.find(pt)[1])
        faces = []
        for r in range(4):
            for j in range(segments):
                faces.append([r * segments + j, r * segments + (j + 1) % segments,
                              ((r + 1) % 4) * segments + (j + 1) % segments,
                              ((r + 1) % 4) * segments + j])
        return mesh_object(name, points, faces, ancestors, [mat], region=region,
                           point_fields=[field] * len(points) if field else None)

    # Cuffs align to measured wrist direction, not world horizontal.
    for sign, side in ((1, "L"), (-1, "R")):
        wrist = cuff_frames[side]["hoodie"]
        axis = cuff_frames[side]["axis"]
        u = axis.cross(Vector((0, 1, 0))).normalized()
        v = axis.cross(u).normalized()
        ring_band("RiderHoodieCuff." + side, wrist, u, v,
                  .049, .045, .037, rib, 4, 32,
                  boundary_fields[("RiderHoodie", "cuff." + side)])
        ring_band("RiderGloveCuff." + side, cuff_frames[side]["glove"], u, v,
                  .035, .028, .021, leather, 6, 32,
                  boundary_fields[("RiderGloves", "cuff." + side)])
    ring_band("RiderHoodieHem", co(0, -.020, 1.002), (1, 0, 0), (0, 1, 0),
              .151 * scale, .109 * scale, .035, rib, 4, 64,
              boundary_fields[("RiderHoodie", "hem")])
    ring_band("RiderHoodieCollar", co(0, -.005, 1.408), (1, 0, 0), (0, 1, 0),
              .080 * scale, .070 * scale, .014, rib, 4, 64,
              boundary_fields[("RiderHoodie", "collar")])
    ring_band("RiderJeansWaist", co(0, -.026, 1.012), (1, 0, 0), (0, 1, 0),
              .139 * scale, .099 * scale, .029, denim, 5, 64)

    # A folded open hood rests behind and around the neck. It binds to upper
    # thorax rows so the head can turn independently. Double surface and rim.
    hood_points, hood_ids = [], []
    hood_u, hood_v = 40, 10
    for layer in range(2):
        for row in range(hood_v + 1):
            t = row / hood_v
            for column in range(hood_u + 1):
                angle = -.70 * math.pi + 1.40 * math.pi * column / hood_u
                x = (.108 + .035 * math.sin(t * math.pi)) * math.sin(angle)
                y = .015 + (.077 + .045 * math.sin(t * math.pi)) * math.cos(angle)
                z = 1.445 - .170 * t + .018 * math.cos(angle)
                if layer:
                    y -= .004 * math.cos(angle)
                    x -= .004 * math.sin(angle)
                point = co(x, y, z)
                hood_points.append(point)
                hood_ids.append(thorax_tree.find(point)[1])
    hood_faces, hood_uv = [], []
    stride = (hood_v + 1) * (hood_u + 1)
    for layer in range(2):
        for row in range(hood_v):
            for column in range(hood_u):
                a = layer * stride + row * (hood_u + 1) + column
                f = [a, a + 1, a + hood_u + 2, a + hood_u + 1]
                if layer:
                    f.reverse()
                hood_faces.append(f)
                hood_uv.append([(column / 4, row / 4), ((column + 1) / 4, row / 4),
                                ((column + 1) / 4, (row + 1) / 4),
                                (column / 4, (row + 1) / 4)])
    boundary = list(range(hood_u + 1))
    boundary += [r * (hood_u + 1) + hood_u for r in range(1, hood_v + 1)]
    boundary += [hood_v * (hood_u + 1) + c for c in range(hood_u - 1, -1, -1)]
    boundary += [r * (hood_u + 1) for r in range(hood_v - 1, 0, -1)]
    for a, b in zip(boundary, boundary[1:] + boundary[:1]):
        hood_faces.append([a, b, b + stride, a + stride])
        hood_uv.append([(0, 0), (1, 0), (1, .1), (0, .1)])
    mesh_object("RiderHood", hood_points, hood_faces, hood_ids,
                [mustard], face_uvs=hood_uv, region=4)

    # Kangaroo pocket: a padded curved front panel with recognizable diagonal
    # hand-entry shoulders. Explicit thorax ancestry keeps it on the sweatshirt.
    pocket_points, pocket_ids = [], []
    pocket_outline = [(-.112, 1.115), (-.071, 1.137), (.071, 1.137),
                      (.112, 1.115), (.112, 1.038), (-.112, 1.038)]
    for x, z in pocket_outline:
        front = [i for i, p in enumerate(source)
                 if abs(p.x - x) < .035 and abs(p.z - z) < .028 and p.y < -.025]
        assert front
        si = min(front, key=lambda i: source[i].y)
        point = co(x, source[si].y - .040, z)
        pocket_points.append(point)
        pocket_ids.append(si)
    center = sum(pocket_points, Vector()) / len(pocket_points)
    center.y -= .004
    pocket_points.append(center)
    pocket_ids.append(all_tree.find(center)[1])
    pocket_faces = [[i, (i + 1) % 6, 6] for i in range(6)]
    mesh_object("RiderKangarooPocket", pocket_points, pocket_faces, pocket_ids,
                [mustard], region=4)

    # Source feet splay outward: shoes follow ankle->ball rather than world Y.
    # Lofted upper encloses all toes as one sneaker; exact source ankle topology
    # is retained above. Supplemental points record nearest new-body FOUR rows.
    for sign, side in ((1, "L"), (-1, "R")):
        forward = Vector((sign * (.23 - .1694), -.065 - .05835, 0)).normalized()
        lateral = Vector((forward.y, -forward.x, 0))
        upper_points, upper_ids, upper_faces, upper_uv = [], [], [], []
        count = 48
        upper_rings = [(.211, -.025, .070, .155, .038),
                       (.211, -.020, .071, .153, .080),
                       (.183, .043, .050, .085, .125),
                       (.1694, .05835, .041, .050, .165)]
        for row, (cx, cy, rw, rl, z) in enumerate(upper_rings):
            for j in range(count):
                angle = math.tau * j / count
                xy = Vector((sign * cx, cy, 0)) + lateral * (rw * math.cos(angle)) + \
                    forward * (rl * math.sin(angle))
                # Low toe box, higher heel. The lower ring stays horizontal.
                zz = z - (.012 * math.sin(angle) if row in (1, 2) else 0)
                point = co(xy.x, xy.y, zz)
                upper_points.append(point)
                upper_ids.append(all_tree.find(point)[1])
        for row in range(len(upper_rings) - 1):
            for j in range(count):
                upper_faces.append([row * count + j, row * count + (j + 1) % count,
                                    (row + 1) * count + (j + 1) % count,
                                    (row + 1) * count + j])
                upper_uv.append([(j / 8, row / 3), ((j + 1) / 8, row / 3),
                                 ((j + 1) / 8, (row + 1) / 3), (j / 8, (row + 1) / 3)])
        mesh_object("RiderShoeUpper." + side, upper_points, upper_faces, upper_ids,
                    [leather], face_uvs=upper_uv, region=7)
        points, ids = [], []
        for z, spread in ((source_floor - .003, 1), (.016, 1.015), (.041, 1)):
            for j in range(count):
                a = math.tau * j / count
                xy = Vector((sign * .211, -.025, 0)) + \
                    lateral * (.072 * math.cos(a) * spread) + \
                    forward * (.157 * math.sin(a) * spread)
                pt = co(xy.x, xy.y, z)
                points.append(pt)
                ids.append(all_tree.find(pt)[1])
        faces = [list(reversed(range(count))), list(range(2 * count, 3 * count))]
        for row in range(2):
            for j in range(count):
                faces.append([row * count + j, row * count + (j + 1) % count,
                              (row + 1) * count + (j + 1) % count,
                              (row + 1) * count + j])
        mesh_object("RiderSole." + side, points, faces, ids, [rubber], region=7)

    total = sum(r["triangles"] for r in reports)
    body_triangles = sum(len(p.vertices) - 2 for p in body.data.polygons)
    report = {"accepted": False, "scope": "first complete dressed construction",
              "boundaryRevision": "wardrobe03; moving02 collar rejection retained",
              "cuffCalibration": {side: {
                  "wristJoint": "DEF-hand." + side,
                  "elbowJoint": "DEF-forearm." + side,
                  "wristMetres": list(frame["wrist"]),
                  "elbowMetres": list(frame["elbow"]),
                  "axis": list(frame["axis"]),
                  "hoodieProximalMetres": .035,
                  "gloveProximalMetres": .018}
                  for side, frame in cuff_frames.items()},
              "sourceBodyVertices": len(xyz), "sourceScale": scale,
              "sourceFloor": source_floor, "bodyTriangles": body_triangles,
              "wardrobeTriangles": total, "actorTriangles": total + body_triangles,
              "newMaterialCount": len(materials),
              "textureDecodedBytes": 5 * (1024 * 1024 + 256 * 256) * 4,
              "objects": reports,
              "limits": ["No moving/art/contact acceptance implied.",
                         "Boundary loop/neighbor fields are explicitly authored derivatives; body FOUR is unchanged.",
                         "Supplemental parts copy nearest new-body FOUR rows except matching boundary rib fields.",
                         "Rims are open wearable lips; soles are closed geometry.",
                         "The source body itself remains unchanged."]}
    assert total + body_triangles < 60000, report["actorTriangles"]
    (out / "construction.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"objects": objects, "materials": materials, "report": report,
            "reportPath": str(out / "construction.json")}
