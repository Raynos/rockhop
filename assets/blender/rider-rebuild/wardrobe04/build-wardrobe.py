"""One loose-cloth candidate after parent actual03 review; integration only.

Frozen wardrobe03/body/rig stay unchanged. Parent owns played acceptance; native
continuation owns guarded assembly. No body faces are hidden or deleted.
"""

import json
import math
import runpy
from pathlib import Path


def buildWardrobe(body, rig, out):
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    import bpy

    here = Path(__file__).resolve().parent
    base = here.parent / "wardrobe01" / "build-wardrobe03.py"
    prep = runpy.run_path(str(here / "construction-proposal.py"))
    result = runpy.run_path(str(base))["buildWardrobe"](body, rig, out)
    objects = {obj.name: obj for obj in result["objects"]}
    reports = {row["object"]: row for row in result["report"]["objects"]}
    hoodie, pocket = objects["RiderHoodie"], objects["RiderKangarooPocket"]
    scale = result["report"]["sourceScale"]
    floor = result["report"]["sourceFloor"]
    z_native = lambda z: (z - floor) * scale
    positions = [tuple(v.co) for v in body.data.vertices]
    polygons = [list(p.vertices) for p in body.data.polygons]
    group_names = {g.index: g.name for g in body.vertex_groups}
    deform = {b.name for b in rig.data.bones if b.use_deform}
    fields = [[(group_names[g.group], g.weight) for g in v.groups
               if group_names[g.group] in deform and g.weight > 0]
              for v in body.data.vertices]
    heights = [1.005, 1.035, 1.065, 1.095, 1.125,
               1.155, 1.185, 1.215, 1.245, 1.275, 1.295]
    source_edges = sorted({tuple(sorted((a, b))) for row in polygons
                           for a, b in zip(row, row[1:] + row[:1])})
    profiles = []
    for z in heights:
        plane = z_native(z)
        section = prep["central_section"](positions, polygons, plane)
        # Above the axilla the source cross-section graph can join the biceps
        # to the trunk. Exact edge-interpolated native roles remove those arms
        # from the envelope profile; connectivity alone is insufficient there.
        section_fields = {}
        for a, b in source_edges:
            p, q = positions[a], positions[b]
            if (p[2] - plane) * (q[2] - plane) < 0:
                t = (plane - p[2]) / (q[2] - p[2])
                point = tuple(p[d] + t * (q[d] - p[d]) for d in range(3))
                row = {name: weight * (1 - t) for name, weight in fields[a]}
                for name, weight in fields[b]:
                    row[name] = row.get(name, 0) + weight * t
                section_fields[tuple(round(value, 10) for value in point)] = list(row.items())
        retained = []
        for point in section:
            key = tuple(round(value, 10) for value in point)
            assert key in section_fields, "Exact anatomical source-edge role missing"
            if prep["torso_field_strength"](section_fields[key]) > .08:
                retained.append(point)
        assert len(retained) >= 12, ("Insufficient anatomical torso section", z, len(retained))
        table = prep["enclosing_profile"](retained, .026)
        table["connectedSectionPointCount"] = len(section)
        table["armRoleExcludedSectionPoints"] = len(section) - len(retained)
        profiles.append(table)

    def profile_at(z):
        if z <= profiles[0]["z"]:
            return profiles[0]
        if z >= profiles[-1]["z"]:
            return profiles[-1]
        for a, b in zip(profiles, profiles[1:]):
            if a["z"] <= z <= b["z"]:
                t = (z - a["z"]) / (b["z"] - a["z"])
                t = prep["smoothstep"](t)
                return {key: a[key] * (1 - t) + b[key] * t
                        for key in ("z", "cx", "cy", "rx", "ry")}
        raise AssertionError(z)

    # Exact source anatomy identities, connected source sections and native
    # weight roles identify trunk. Sleeves/biceps never enter an abs-X mask.
    ids = reports["RiderHoodie"]["sourceVertexIds"]
    graph = [set() for _ in hoodie.data.vertices]
    for poly in hoodie.data.polygons:
        row = list(poly.vertices)
        for a, b in zip(row, row[1:] + row[:1]):
            graph[a].add(b)
            graph[b].add(a)
    # Keep every regular outer/inner boundary and its first transition rows.
    seeds = set()
    for control in reports["RiderHoodie"]["conditionedBoundaryLoops"]:
        seeds.update(control["nativeBoundaryPointIds"])
    seed_sources = {ids[i] for i in seeds}
    seeds.update(i for i, si in enumerate(ids) if si in seed_sources)
    boundary_distance = {i: 0 for i in seeds}
    frontier = list(seeds)
    for step in range(1, 8):
        next_frontier = []
        for vi in frontier:
            for neighbor in graph[vi]:
                if neighbor not in boundary_distance:
                    boundary_distance[neighbor] = step
                    next_frontier.append(neighbor)
        frontier = next_frontier

    before = [v.co.copy() for v in hoodie.data.vertices]
    changed, core = [], []
    strengths = {}
    for vi, vertex in enumerate(hoodie.data.vertices):
        source_id = ids[vi]
        source_point = body.data.vertices[source_id].co
        source_z = source_point.z / scale + floor
        if not .997 < source_z < 1.305:
            continue
        table = profile_at(source_point.z)
        nx = (source_point.x - table["cx"]) / table["rx"]
        ny = (source_point.y - table["cy"]) / table["ry"]
        # A point beyond the enclosing central loop is not a trunk chart.
        if nx * nx + ny * ny > 1.16:
            continue
        field_strength = prep["torso_field_strength"](fields[source_id])
        support = boundary_distance.get(vi, 8)
        boundary_strength = prep["smoothstep"]((support - 3) / 4)
        height_strength = prep["smoothstep"]((source_z - .997) / .060) * \
            prep["smoothstep"]((1.305 - source_z) / .040)
        strength = field_strength * boundary_strength * height_strength
        if strength < .0001:
            continue
        angle = math.atan2(ny, nx)
        target = Vector((table["cx"] + table["rx"] * math.cos(angle),
                         table["cy"] + table["ry"] * math.sin(angle), vertex.co.z))
        # Broad hem gathering: millimetres, tapering to zero at attachments.
        fold = .0035 * math.sin(angle * 5 + source_z * 4) * \
            prep["smoothstep"]((1.17 - source_z) / .10)
        target.x += fold * math.cos(angle)
        target.y += fold * math.sin(angle)
        vertex.co = vertex.co.lerp(target, strength)
        changed.append(vi)
        strengths[vi] = strength
        if strength > .75 and support > 5:
            core.append(vi)
    assert changed and core, "No anatomically selected torso shell/core"
    hoodie.data.update()

    # Pocket follows the actual new cloth surface, not the retired body-front
    # placement. Raycast exact new torso faces; keep its source FOUR and topology.
    cloth_bvh = BVHTree.FromPolygons([v.co for v in hoodie.data.vertices],
                                   [list(p.vertices) for p in hoodie.data.polygons],
                                   all_triangles=False)
    pocket_hits = []
    for vertex in pocket.data.vertices:
        origin = Vector((vertex.co.x, -.65, vertex.co.z))
        hit, normal, face, distance = cloth_bvh.ray_cast(origin, Vector((0, 1, 0)), 1.3)
        assert hit is not None, ("Pocket cloth correspondence missing", vertex.index)
        vertex.co.y = hit.y - .0045
        pocket_hits.append({"nativePoint": vertex.index, "clothFace": face,
                            "hitMetres": list(hit), "clearanceMetres": .0045})
    pocket.data.update()

    # Compact glove rib; retain the common boundary field and open wearer cavity.
    for side in ("L", "R"):
        obj = objects["RiderGloveCuff." + side]
        frame = result["report"]["cuffCalibration"][side]
        axis = Vector(frame["axis"])
        center = Vector(frame["wristMetres"]) + axis * frame["gloveProximalMetres"]
        u = axis.cross(Vector((0, 1, 0))).normalized()
        v = axis.cross(u).normalized()
        for vertex in obj.data.vertices:
            relative = vertex.co - center
            # Short, restrained leather cuff instead of the tall flared band.
            vertex.co = center + u * (relative.dot(u) * (.031 / .035)) + \
                v * (relative.dot(v) * (.029 / .028)) + axis * (relative.dot(axis) * (.012 / .021))
        obj.data.update()

    # Keep the enclosing XY footprint from accepted02 toe fix; reduce sole
    # platform and toe-box height with an overlapping lower-upper seam.
    for side in ("L", "R"):
        sole = objects["RiderSole." + side]
        zmap = {0: floor - .003, 1: .009, 2: .025}
        for vi, vertex in enumerate(sole.data.vertices):
            vertex.co.z = z_native(zmap[vi // 48])
        sole.data.update()
        upper = objects["RiderShoeUpper." + side]
        for vi, vertex in enumerate(upper.data.vertices):
            row = vi // 48
            if row == 0:
                vertex.co.z = z_native(.022)
            elif row == 1:
                vertex.co.z -= .017 * scale
        upper.data.update()

    # Side seam relief derives from the actual relaxed surface, using its own
    # point fields. A small shaded rib stripe is geometry, not copied atlas UV.
    seam_rows = []
    for side, sign in (("L", 1), ("R", -1)):
        candidates = []
        for vi in changed:
            p = hoodie.data.vertices[vi].co
            table = profile_at(p.z)
            angle = math.atan2((p.y - table["cy"]) / table["ry"],
                               (p.x - table["cx"]) / table["rx"])
            wanted = 0 if sign > 0 else math.pi
            delta = abs(math.atan2(math.sin(angle - wanted), math.cos(angle - wanted)))
            if delta < .20 and strengths[vi] > .30:
                candidates.append(vi)
        # Native selected surface points give the seam its skin field exactly.
        selected = []
        for target_z in [1.06, 1.10, 1.14, 1.18, 1.22, 1.26]:
            if candidates:
                vi = min(candidates, key=lambda i: abs(hoodie.data.vertices[i].co.z - z_native(target_z)))
                if vi not in selected:
                    selected.append(vi)
        selected.sort(key=lambda i: hoodie.data.vertices[i].co.z)
        if len(selected) < 3:
            continue
        points, faces, rows = [], [], []
        for vi in selected:
            p = hoodie.data.vertices[vi].co.copy()
            p.x += sign * .0018
            points.extend([p + Vector((0, -.0015, 0)), p + Vector((0, .0015, 0))])
            rows.extend([vi, vi])
        for j in range(len(selected) - 1):
            face = [j * 2, j * 2 + 1, j * 2 + 3, j * 2 + 2]
            faces.append(face if sign > 0 else list(reversed(face)))
        mesh = bpy.data.meshes.new("RiderSideSeam." + side + "Mesh")
        mesh.from_pydata(points, [], faces)
        mesh.update()
        obj = bpy.data.objects.new("RiderSideSeam." + side, mesh)
        bpy.context.scene.collection.objects.link(obj)
        mesh.materials.append(bpy.data.materials["RiderMustardRib"])
        uv = mesh.uv_layers.new(name="UVMap")
        for polygon in mesh.polygons:
            polygon.use_smooth = True
            for li in polygon.loop_indices:
                p = mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv = (p.y * 10, p.z * 10)
        for group in hoodie.vertex_groups:
            obj.vertex_groups.new(name=group.name)
        names = {g.index: g.name for g in hoodie.vertex_groups}
        for pi, vi in enumerate(rows):
            for g in hoodie.data.vertices[vi].groups:
                obj.vertex_groups[names[g.group]].add([pi], g.weight, "REPLACE")
        for name, values in (("_NATIVE_ID", list(range(len(points)))),
                             ("_REGION_ID", [4] * len(points)),
                             ("_SOURCE_VERTEX_ID", [ids[vi] for vi in rows])):
            attr = mesh.attributes.new(name, "INT", "POINT")
            attr.data.foreach_set("value", values)
        obj.parent = rig
        tri = obj.modifiers.new("FrozenRestTriangles", "TRIANGULATE")
        tri.quad_method = "FIXED"
        arm = obj.modifiers.new("SharedAnatomicalFour", "ARMATURE")
        arm.object = rig
        arm.use_deform_preserve_volume = False
        obj["accepted"] = False
        result["objects"].append(obj)
        seam_rows.append({"object": obj.name, "sourceClothPoints": rows,
                          "vertices": len(points), "triangles": 2 * len(faces)})

    # Source measurement, not a radius proxy: skin point versus new exact cloth
    # surface. Signed nearest diagnostics are restricted to displaced torso core.
    measured = []
    for vi in core:
        source_id = ids[vi]
        skin = body.data.vertices[source_id].co
        near, normal, face, distance = cloth_bvh.find_nearest(skin)
        assert near is not None
        measured.append({"clothPoint": vi, "bodySourcePoint": source_id,
                         "clothFace": face, "distanceMetres": distance,
                         "signedSkinMinusClothMetres": (skin - near).dot(normal)})
    displacement = max((v.co - old).length for v, old in zip(hoodie.data.vertices, before))
    quality = {"accepted": False, "candidate": "one loose torso shell and cuff/profile unit",
               "anatomySelection": "connected central section graph + actual trunk/limb FOUR roles",
               "profilesMetres": profiles, "changedClothPointCount": len(changed),
               "corePointCount": len(core), "maxDisplacementMetres": displacement,
               "sourceBodyFacesHidden": False, "bodySkeletonAndFieldsChanged": False,
               "clothFourFieldsChangedFrom03": False,
               "preservedBoundarySupportRows": 3,
               "geometricNormals": "recomputed from modified rest cloth topology",
               "pocketExactClothHits": pocket_hits, "sideSeams": seam_rows,
               "coreSkinSurfaceDiagnostics": measured,
               "minimumCoreSkinSurfaceDistanceMetres": min(x["distanceMetres"] for x in measured),
               "maximumCoreSignedSkinMinusClothMetres": max(x["signedSkinMinusClothMetres"] for x in measured),
               "shoeToeFootprintPreserved": True, "soleTopSourceZ": .025,
               "upperLowerSourceZ": .022,
               "limits": ["Rest nearest-surface diagnostics do not certify posed collision/contact.",
                          "One candidate; no follow-up before parent actual game played verdict.",
                          "Field and actual generic/bike motion acceptance remain parent-owned."]}
    result["report"]["looseCloth04"] = quality
    extra_triangles = sum(row["triangles"] for row in seam_rows)
    result["report"]["wardrobeTriangles"] += extra_triangles
    result["report"]["actorTriangles"] += extra_triangles
    assert result["report"]["actorTriangles"] < 60000
    Path(result["reportPath"]).write_text(json.dumps(result["report"], indent=2) + "\n")
    return result
