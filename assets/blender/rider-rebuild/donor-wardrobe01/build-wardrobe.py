"""Actual selected garment derivatives; integration in the owner's Blender job.

The old skeleton supplies measured rest landmarks only. Its skin is discarded.
All new fields come from the coherent new wearer, scoped to anatomical regions.
Source materials, seams and shading remain authoritative; no painted body shell.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HOODIE = ROOT / "assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie25/crease-normal-candidate.blend"
PREP = ROOT / "assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/jeans"
HOODIE_SHA = "c732d98076f6b9b1a209a45e8a0cddf793484807ea8b3ae9011fa4f82c151df0"
JEANS_SHA = "6907492293a23765f49b41a64a65cbdf18a6e10b15cfd183416113352f759a49"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def buildWardrobe(body, rig, out):
    import bpy
    import numpy as np
    from mathutils import Vector, Matrix
    from mathutils.kdtree import KDTree
    from mathutils.bvhtree import BVHTree

    out = Path(out) / "actual-donor-wardrobe"
    out.mkdir(parents=True, exist_ok=True)
    assert digest(HOODIE) == HOODIE_SHA
    assert digest(PREP / "retopology-prototype.npz") == JEANS_SHA
    assert len(body.data.vertices) == 10582
    assert body.matrix_world.is_identity and rig.matrix_world.is_identity
    deform = {b.name for b in rig.data.bones if b.use_deform}
    group_names = {g.index: g.name for g in body.vertex_groups}
    body_fields = []
    body_points = [v.co.copy() for v in body.data.vertices]
    for v in body.data.vertices:
        field = {group_names[g.group]: g.weight for g in v.groups
                 if group_names[g.group] in deform and g.weight > 0}
        assert 1 <= len(field) <= 4 and abs(sum(field.values()) - 1) < 2e-5
        body_fields.append(field)

    def trunk(n):
        return n.startswith("DEF-spine") or n.startswith("DEF-pelvis")

    def belongs_to_side(n, side):
        # Rigify's deformation splits use e.g. DEF-upper_arm.L.001.
        return n.endswith("."+side) or ("."+side+".") in n

    scopes = {
        "torso": lambda n: trunk(n) and n not in {"DEF-spine.005", "DEF-spine.006"},
        "Larm": lambda n: belongs_to_side(n, "L") and ("upper_arm" in n or "forearm" in n or "shoulder" in n),
        "Rarm": lambda n: belongs_to_side(n, "R") and ("upper_arm" in n or "forearm" in n or "shoulder" in n),
        "Lleg": lambda n: belongs_to_side(n, "L") and ("thigh" in n or "shin" in n),
        "Rleg": lambda n: belongs_to_side(n, "R") and ("thigh" in n or "shin" in n),
        "pelvis": lambda n: n in {"DEF-spine", "DEF-pelvis.L", "DEF-pelvis.R"},
    }
    trees = {}
    for scope, allowed in scopes.items():
        ids = [i for i, field in enumerate(body_fields)
               if sum(w for n, w in field.items() if allowed(n)) > .55]
        assert ids, ("empty anatomical scope", scope)
        tree = KDTree(len(ids))
        for i in ids:
            tree.insert(body_points[i], i)
        tree.balance()
        trees[scope] = tree

    def normalized(row):
        row = sorted(((n, w) for n, w in row.items() if w > 0),
                     key=lambda x: (-x[1], x[0]))[:4]
        total = sum(w for n, w in row)
        assert total > 0
        return {n: w / total for n, w in row}

    def field_at(p, scope):
        allowed = scopes[scope]
        neighbors = trees[scope].find_n(p, 8)
        row = {}
        for _, i, distance in neighbors:
            factor = 1 / max(.006, distance) ** 2
            for n, w in body_fields[i].items():
                if allowed(n):
                    row[n] = row.get(n, 0) + w * factor
        return normalized(row)

    def mix_fields(a, b, t):
        return normalized({n: a.get(n, 0) * (1-t) + b.get(n, 0) * t
                           for n in set(a) | set(b)})

    def smooth(a, b, value):
        t = min(1., max(0., (value-a)/(b-a)))
        return t*t*(3-2*t)

    def bind(obj, fields, region):
        obj.vertex_groups.clear()
        groups = {n: obj.vertex_groups.new(name=n)
                  for n in sorted({n for field in fields for n in field})}
        for i, field in enumerate(fields):
            for name, weight in field.items():
                groups[name].add([i], weight, "REPLACE")
        obj.modifiers.clear()
        arm = obj.modifiers.new("Shared75AnatomicalSkin", "ARMATURE")
        arm.object = rig
        arm.use_deform_preserve_volume = False
        obj.parent = rig
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_world = Matrix.Identity(4)
        obj.hide_viewport = False
        obj.hide_render = False
        for name, domain, values in [
            ("_NATIVE_ID", "POINT", list(range(len(obj.data.vertices)))),
            ("_SOURCE_VERTEX_ID", "POINT", list(range(len(obj.data.vertices)))),
            ("_REGION_ID", "POINT", [region]*len(obj.data.vertices)),
            ("_CORNER_ID", "CORNER", list(range(len(obj.data.loops)))),
        ]:
            prior = obj.data.attributes.get(name)
            if prior:
                obj.data.attributes.remove(prior)
            attr = obj.data.attributes.new(name, "INT", domain)
            attr.data.foreach_set("value", values)

    # Append exact selected appearance; library remains unchanged. Only the
    # selected garment and its old anatomical rig supply construction controls.
    source_name = "Actual selected donor, compact interior flow, unaccepted"
    rig_name = "Independent anatomical foundation rig"
    with bpy.data.libraries.load(str(HOODIE), link=False) as (available, selected):
        assert source_name in available.objects and rig_name in available.objects
        selected.objects = [source_name, rig_name]
    hoodie, old_rig = selected.objects
    bpy.context.scene.collection.objects.link(hoodie)
    original_uv = np.asarray([x.uv[:] for x in hoodie.data.uv_layers.active.data])
    original_cycles = [tuple(p.vertices) for p in hoodie.data.polygons]
    source_points = [hoodie.matrix_world @ v.co for v in hoodie.data.vertices]
    # Proper rotation (determinant +1): source +X front -> new -Y front.
    # Historical source L is -Y; its named side therefore becomes target R.
    # Match spatial laterality explicitly instead of reflecting all topology.
    basis = Matrix(((0., 1., 0.), (-1., 0., 0.), (0., 0., 1.)))
    source_points = [basis @ p for p in source_points]

    def oldbone(name):
        b = old_rig.data.bones.get(name)
        assert b is not None, (name, list(old_rig.data.bones.keys()))
        return (basis @ (old_rig.matrix_world @ b.head_local),
                basis @ (old_rig.matrix_world @ b.tail_local))

    def newbone(name):
        b = rig.data.bones[name]
        return b.head_local.copy(), b.tail_local.copy()

    arm_controls = {}
    for side in ("L", "R"):
        source_side = "R" if side == "L" else "L"
        os, oe = oldbone("upperArm."+source_side)
        oe2, ow = oldbone("forearm."+source_side)
        ns, ne = newbone("DEF-upper_arm."+side)
        ne2, nw = newbone("DEF-forearm."+side)
        # The generated DEF-upper_arm is half of a twist chain: its tail is
        # not the elbow. Full anatomical upper-arm ends at forearm.head.
        ne = ne2.copy()
        # The target cuff meets the actual wrist while keeping original cuffs.
        nw = rig.data.bones["DEF-hand."+side].head_local.copy()
        arm_controls[side] = [(os, oe, ns, ne), (oe2, ow, ne2, nw)]
    old_shoulder_z = sum(arm_controls[s][0][0].z for s in ("L", "R"))/2
    new_shoulder_z = sum(arm_controls[s][0][2].z for s in ("L", "R"))/2
    old_half = sum(abs(arm_controls[s][0][0].x) for s in ("L", "R"))/2
    new_half = sum(abs(arm_controls[s][0][2].x) for s in ("L", "R"))/2
    old_hem = min(p.z for p in source_points)
    # Waist rests above the pelvis; full donor hem overlaps original jeans.
    new_hem = rig.data.bones["DEF-spine"].head_local.z + .050
    torso_zscale = (new_shoulder_z-new_hem)/(old_shoulder_z-old_hem)
    lateral_scale = new_half/old_half
    front_scale = lateral_scale

    def segment_map(p, control):
        a, b, c, d = control
        old_axis = b-a
        target_axis = d-c
        t = (p-a).dot(old_axis)/old_axis.length_squared
        old_center = a+old_axis*t
        rotation = old_axis.normalized().rotation_difference(target_axis.normalized())
        radial = rotation @ (p-old_center)
        return c+target_axis*t+radial*lateral_scale, t, (p-old_center).length

    hoodie_fields = []
    regions = []
    for v, p in zip(hoodie.data.vertices, source_points):
        torso = Vector((p.x*lateral_scale, p.y*front_scale,
                        new_hem+(p.z-old_hem)*torso_zscale))
        side = "L" if p.x >= 0 else "R"
        controls = arm_controls[side]
        maps = [segment_map(p, control) for control in controls]
        near_upper, near_fore = maps
        # A continuous elbow transition in source axial distance, not a
        # nearest-bone discontinuity; torso/axilla blends on shoulder distance.
        along = (p-controls[0][0]).dot((controls[0][1]-controls[0][0]).normalized())
        elbow_distance = (controls[0][1]-controls[0][0]).length
        elbow_t = smooth(elbow_distance-.075, elbow_distance+.075, along)
        arm_point = near_upper[0].lerp(near_fore[0], elbow_t)
        arm_t = smooth(old_half*.78, old_half+ .100, abs(p.x))
        # Hood/head stays torso scoped; lateral hood edges cannot become biceps.
        arm_t *= 1-smooth(old_shoulder_z+.015, old_shoulder_z+.100, p.z)
        point = torso.lerp(arm_point, arm_t)
        v.co = point
        torso_field = field_at(point, "torso")
        arm_field = field_at(point, side+"arm")
        field = mix_fields(torso_field, arm_field, arm_t)
        hem_t = 1-smooth(old_hem+.025, old_hem+.110, p.z)
        if hem_t > 0 and arm_t < .05:
            field = mix_fields(field, field_at(point, "pelvis"), hem_t)
        hoodie_fields.append(field)
        regions.append(arm_t)
    # Original garment ports stay open and retain all original vertices/UVs.
    # Boundary cycles share coherent endpoint fields; adjacent rows blend away
    # continuously, preventing per-point nearest-body collar/cuff sawteeth.
    edge_faces = {}
    neighbors = [set() for _ in source_points]
    for poly in original_cycles:
        for a, b in zip(poly, poly[1:]+poly[:1]):
            neighbors[a].add(b)
            neighbors[b].add(a)
            key = tuple(sorted((a,b)))
            edge_faces[key] = edge_faces.get(key, 0)+1
    boundary_adjacency = {}
    for (a,b), count in edge_faces.items():
        if count == 1:
            boundary_adjacency.setdefault(a,set()).add(b)
            boundary_adjacency.setdefault(b,set()).add(a)
    remaining = set(boundary_adjacency)
    boundary_reports = []
    while remaining:
        seed = remaining.pop()
        component, stack = {seed}, [seed]
        while stack:
            for other in boundary_adjacency[stack.pop()]:
                if other not in component:
                    component.add(other)
                    remaining.discard(other)
                    stack.append(other)
        center = sum((source_points[i] for i in component), Vector())/len(component)
        source_z = [source_points[i].z for i in component]
        boundary_kind, endpoint_field = "unclassified original port", None
        if max(source_z) < old_hem+.080:
            boundary_kind = "pelvis hem"
            endpoint_field = {"DEF-spine": 1.}
        elif abs(center.x) > old_half+.120:
            side = "L" if center.x>0 else "R"
            boundary_kind = side+" wrist cuff"
            wrist = rig.data.bones["DEF-hand."+side].head_local
            elbow = rig.data.bones["DEF-forearm."+side].head_local
            endpoint_field = field_at(wrist+(elbow-wrist).normalized()*.035, side+"arm")
        elif min(source_z) > old_shoulder_z-.025 and max(abs(source_points[i].x) for i in component)<old_half*1.2:
            boundary_kind = "neck collar"
            endpoint_field = normalized({"DEF-spine.003": .70, "DEF-spine.004": .30})
        if endpoint_field is not None:
            visited = set(component)
            row = set(component)
            for factor in (1., .67, .33):
                for i in row:
                    hoodie_fields[i] = mix_fields(hoodie_fields[i], endpoint_field, factor)
                next_row = set().union(*(neighbors[i] for i in row))-visited
                visited.update(next_row)
                row = next_row
        boundary_reports.append({"sourceVertexCount": len(component),
                                 "sourceCenter": list(center), "kind": boundary_kind,
                                 "endpointField": endpoint_field})
    hoodie.name = "RiderHoodie"
    hoodie.data.update()
    assert np.array_equal(original_uv, np.asarray([x.uv[:] for x in hoodie.data.uv_layers.active.data]))
    assert original_cycles == [tuple(p.vertices) for p in hoodie.data.polygons]
    bind(hoodie, hoodie_fields, 4)
    bpy.data.objects.remove(old_rig, do_unlink=True)

    # Source jeans topology retains actual seams/fly/pockets, not wearer UVs.
    donor = np.load(PREP / "cleaned-donor.npz")
    proto = np.load(PREP / "retopology-prototype.npz")
    source_v = proto["vertices"].astype(float)
    faces = proto["faces"].astype(int)
    dense_v, dense_f = donor["vertices"], donor["faces"]
    original_rows = donor["originalTriangleRows"]
    original_corner_uv = donor["originalCornerUV"]
    dense_tree = BVHTree.FromPolygons([Vector(p) for p in dense_v], dense_f.tolist(), all_triangles=True)
    corner_uv = []
    ancestry = []
    uv_diagnostics = {"minBarycentric": 1., "maxBarycentric": 0., "maxActualCornerProjectionDistance": 0.,
                      "cornersOutsideTextureUnitSquare": 0,
                      "ownership": "Each corner query inset1e-5 toward its own face midpoint, then closest point of ACTUAL original corner onto selected dense source triangle"}

    def barycentric(point, a, b, c):
        v0, v1, v2 = b-a, c-a, point-a
        d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
        d20, d21 = v2.dot(v0), v2.dot(v1)
        denom = d00*d11-d01*d01
        assert abs(denom) > 1e-18
        v = (d11*d20-d01*d21)/denom
        w = (d00*d21-d01*d20)/denom
        return np.asarray((1-v-w, v, w))

    def closest_on_triangle(point, a, b, c):
        bary = barycentric(point, a, b, c)
        if bary.min() >= 0:
            return a*float(bary[0])+b*float(bary[1])+c*float(bary[2]), bary
        candidates = []
        for pa, pb, ia, ib in ((a,b,0,1), (b,c,1,2), (c,a,2,0)):
            edge = pb-pa
            t = min(1., max(0., (point-pa).dot(edge)/edge.length_squared))
            closest = pa+edge*t
            row = np.zeros(3)
            row[ia], row[ib] = 1-t, t
            candidates.append(((closest-point).length_squared, closest, row))
        _, closest, row = min(candidates, key=lambda item: item[0])
        return closest, row

    # Each actual corner chooses its source chart from the inward face side.
    # This preserves discontinuous seam ownership without extrapolating the
    # entire compact triangle from one tiny dense source triangle's UV plane.
    for face in faces:
        center = Vector(source_v[face].mean(axis=0))
        field_uv, field_ancestry = [], []
        for vi in face:
            actual_corner = Vector(source_v[vi])
            ownership_probe = actual_corner.lerp(center, 1e-5)
            _, _, source_face, _ = dense_tree.find_nearest(ownership_probe)
            tri = [Vector(p) for p in dense_v[dense_f[source_face]]]
            projected, bary = closest_on_triangle(actual_corner, *tri)
            corner_distance = (projected-actual_corner).length
            uv_diagnostics["maxActualCornerProjectionDistance"] = max(uv_diagnostics["maxActualCornerProjectionDistance"], corner_distance)
            uvs = original_corner_uv[source_face]
            value = bary @ uvs
            uv_diagnostics["minBarycentric"] = min(uv_diagnostics["minBarycentric"], float(bary.min()))
            uv_diagnostics["maxBarycentric"] = max(uv_diagnostics["maxBarycentric"], float(bary.max()))
            uv_diagnostics["cornersOutsideTextureUnitSquare"] += int(bool((value < 0).any() or (value > 1).any()))
            field_uv.append(value.tolist())
            field_ancestry.append({"originalTriangleRow": int(original_rows[source_face]),
                                   "barycentric": bary.tolist(),
                                   "sourceChartFace": int(source_face),
                                   "actualCornerProjectionDistance": corner_distance})
        corner_uv.append(field_uv)
        ancestry.append(field_ancestry)
    # Source Y up, +Z front -> normalized wearer's Z up, -Y front.
    source_floor = float(source_v[:,1].min())
    source_top = float(source_v[:,1].max())
    waist_z = new_hem + .018
    ankle_z = sum(rig.data.bones["DEF-foot."+s].head_local.z for s in ("L", "R"))/2 + .030
    zscale = (waist_z-ankle_z)/(source_top-source_floor)
    hip_half = sum(abs(rig.data.bones["DEF-thigh."+s].head_local.x) for s in ("L", "R"))/2
    # Measure actual waist body extent; wearer X/Y cross-section sets scale,
    # keeping the source pattern and silhouette instead of copying muscles.
    waist_body = [p for p in body_points if abs(p.z-waist_z)<.035 and abs(p.x)<.24]
    assert waist_body
    width = max(abs(p.x) for p in waist_body)+.015
    waist_source = source_v[source_v[:,1] > source_top-.12]
    xscale = width / max(abs(waist_source[:,0]).max(), .001)
    depth = max(abs(p.y) for p in waist_body)+.014
    yscale = depth / max(abs(waist_source[:,2]).max(), .001)
    jeans_points, jeans_fields = [], []
    for sv in source_v:
        x, up, forward = sv
        z = ankle_z+(up-source_floor)*zscale
        side = "L" if x >= 0 else "R"
        thigh = rig.data.bones["DEF-thigh."+side]
        shin = rig.data.bones["DEF-shin."+side]
        ankle = rig.data.bones["DEF-foot."+side].head_local
        blend = smooth(ankle_z+.015, waist_z-.160, z)
        # Continuous center-line spread increases down the leg to follow the
        # actual source stance without crushing the donor crotch/fly.
        desired_x = np.interp(z, [ankle.z, shin.head_local.z, thigh.head_local.z],
                             [ankle.x, shin.head_local.x, thigh.head_local.x])
        desired_y = np.interp(z, [ankle.z, shin.head_local.z, thigh.head_local.z],
                             [ankle.y, shin.head_local.y, thigh.head_local.y])
        source_level = source_v[abs(source_v[:,1]-up)<.040]
        side_level = source_level[source_level[:,0]* (1 if side=="L" else -1)>0]
        center_x = float(np.median(side_level[:,0])) if len(side_level) else x
        offset = (desired_x-center_x*xscale)*(1-smooth(waist_z-.220, waist_z-.080, z))
        point = Vector((x*xscale+offset, -forward*yscale+desired_y*(1-blend), z))
        pelvis_field = field_at(point, "pelvis")
        leg_field = field_at(point, side+"leg")
        leg_t = 1-smooth(waist_z-.220, waist_z-.080, z)
        field = mix_fields(pelvis_field, leg_field, leg_t)
        jeans_points.append(point)
        jeans_fields.append(field)
    mesh = bpy.data.meshes.new("ActualOriginalJeansMesh")
    mesh.from_pydata(jeans_points, [], faces.tolist())
    mesh.update()
    jeans = bpy.data.objects.new("RiderJeans", mesh)
    bpy.context.scene.collection.objects.link(jeans)
    uv = mesh.uv_layers.new(name="OriginalDonorCornerUV")
    for polygon, uvs in zip(mesh.polygons, corner_uv):
        polygon.use_smooth = True
        for li, value in zip(polygon.loop_indices, uvs):
            uv.data[li].uv = value
    mat = bpy.data.materials.new("ActualOriginalJeansPBR")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    base = mat.node_tree.nodes.new("ShaderNodeTexImage")
    base.image = bpy.data.images.load(str(PREP / "baseColorTexture.png"), check_existing=True)
    base.image.colorspace_settings.name = "sRGB"
    base.image.pack()
    mat.node_tree.links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
    mr = mat.node_tree.nodes.new("ShaderNodeTexImage")
    mr.image = bpy.data.images.load(str(PREP / "metallicRoughnessTexture.png"), check_existing=True)
    mr.image.colorspace_settings.name = "Non-Color"
    mr.image.pack()
    split = mat.node_tree.nodes.new("ShaderNodeSeparateColor")
    split.mode = "RGB"
    mat.node_tree.links.new(mr.outputs["Color"], split.inputs["Color"])
    mat.node_tree.links.new(split.outputs["Green"], bsdf.inputs["Roughness"])
    mat.node_tree.links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
    mesh.materials.append(mat)
    bind(jeans, jeans_fields, 5)
    lineage_path = out / "jeans-source-corner-lineage.json"
    lineage_path.write_text(json.dumps({"source": str(PREP / "cleaned-donor.npz"),
                                       "sourceSHA256": digest(PREP / "cleaned-donor.npz"),
                                       "corners": ancestry}, separators=(",", ":")))
    report = {
        "status": "ACTUAL_SOURCE_DERIVATIVE_UNACCEPTED_REQUIRES_PLAYED_REVIEW",
        "helperSHA256": digest(__file__),
        "sources": {str(HOODIE): digest(HOODIE), str(PREP / "retopology-prototype.npz"): digest(PREP / "retopology-prototype.npz")},
        "hoodie": {"vertices": len(hoodie.data.vertices), "faces": len(hoodie.data.polygons),
                   "sourceUVAndPolygonCyclesExact": True, "newHemZ": new_hem,
                   "oldShoulderZ": old_shoulder_z, "newShoulderZ": new_shoulder_z,
                   "lateralScale": lateral_scale, "torsoZScale": torso_zscale,
                   "originalPortFields": boundary_reports,
                   "armLandmarks": {s: [[list(p) for p in c] for c in controls] for s,controls in arm_controls.items()},
                   "materials": [m.name for m in hoodie.data.materials]},
        "jeans": {"vertices": len(mesh.vertices), "faces": len(mesh.polygons),
                  "originalMapsSHA256": [digest(PREP / name) for name in ("baseColorTexture.png", "metallicRoughnessTexture.png")],
                  "cornerLineage": str(lineage_path), "waistZ": waist_z, "ankleZ": ankle_z,
                  "uvProjectionDiagnostics": uv_diagnostics,
                  "sourceToRestScales": [xscale, yscale, zscale]},
        "fields": "New wearer anatomical-scoped inverse-distance blend, normalized FOUR; no old skin copied",
        "limits": ["Source triangles/loops and source-map lineage retained; chart-projected jeans corner UV are a measured derivative, not byte-exact original topology.",
                   "No claimed collision freedom, device budget, motion quality or art acceptance before independent whole-outfit moving review.",
                   "No body face hiding or source master edits."]}
    report_path = out / "construction.json"
    report_path.write_text(json.dumps(report, indent=2)+"\n")
    return {"objects": [hoodie, jeans],
            "materials": list(hoodie.data.materials)+[mat],
            "report": report, "reportPath": str(report_path)}
