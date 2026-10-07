"""One source-derived padded glove retopology, cavity and original-PBR bake."""
import hashlib
import json
import math
from pathlib import Path


def buildSelectedGloves(body, rig, out):
    import bpy
    import bmesh
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import barycentric_transform

    root = Path(__file__).resolve().parents[4]
    base = root / "assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data"
    out = Path(out) / "selected-glove02"
    out.mkdir(parents=True, exist_ok=False)
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    prototype_path = base / "prep02/gloves/retopology-prototype.npz"
    branch_path = base / "glove-anatomy02b/branches.npz"
    classification_path = root / "docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/glove-anatomy02/classification.json"
    semantics_path = root / "docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/semantic-registration.json"
    assert sha(prototype_path) == "746c99bb9fc109492b27e6e9bd3d7281bf3d4799488cb0d6beebf2804d8a6c5e"
    assert sha(branch_path) == "2bb0068e983394ed6bbb6afd94de4b0f735bc62a94b449204ead8d8058e03562"
    assert sha(classification_path) == "4a0428f4b3054562e33db8f70accfb4cd0073fe561b2dd5823af6fd04fa4e154"
    assert sha(semantics_path) == "e9ac95b7b7fc8a22dd71bff4831d9fa2aa8d6544f3611db14b23e8aa074aa93a"
    donor = dict(np.load(prototype_path))
    branches = dict(np.load(branch_path))
    assert np.array_equal(branches["vertices"], donor["vertices"])
    assert np.array_equal(branches["faces"], donor["faces"])
    classification = json.loads(classification_path.read_text())
    semantics = json.loads(semantics_path.read_text())["gloves"]
    digits = ["pinky", "ring", "middle", "index", "thumb"]
    native_name = lambda digit, joint: "DEF-" + ("thumb" if digit == "thumb" else "f_" + digit) + ".%02d.R" % joint
    body_names = {group.index: group.name for group in body.vertex_groups}
    measured_tips = {}
    for digit in digits:
        name = native_name(digit, 3); bone = rig.data.bones[name]
        axis = (bone.tail_local - bone.head_local).normalized()
        distances = [float((vertex.co - bone.head_local).dot(axis)) for vertex in body.data.vertices
            if sum(group.weight for group in vertex.groups if body_names[group.group] == name) > .3]
        assert distances
        extent = float(np.quantile(distances, .99))
        measured_tips[digit] = tuple(bone.head_local + axis * (extent + .002))
    target_controls = np.concatenate([np.array([tuple(rig.data.bones[native_name(digit, joint)].head_local)
        for joint in (1, 2, 3)] + [measured_tips[digit]]) for digit in digits])
    source_controls = np.concatenate([np.array(classification["digits"][digit]["sectionCenters"]) for digit in digits])
    # The donor thumb sections belong to the isolated digit, not the metacarpal.
    # Preserve their measured relative arc stations and map them onto MCP/IP/tip.
    source_thumb = source_controls[16:20].copy()
    source_thumb_arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(source_thumb, axis=0), axis=1))]
    source_thumb_stations = source_thumb_arc / source_thumb_arc[-1]
    thumb_arc = np.array([tuple(rig.data.bones[native_name("thumb", 2)].head_local),
        tuple(rig.data.bones[native_name("thumb", 3)].head_local), measured_tips["thumb"]])
    thumb_lengths = np.linalg.norm(np.diff(thumb_arc, axis=0), axis=1)
    thumb_stations = np.r_[0, np.cumsum(thumb_lengths)]
    target_controls[16:20] = np.array([[np.interp(station * thumb_stations[-1], thumb_stations,
        thumb_arc[:, coordinate]) for coordinate in range(3)] for station in source_thumb_stations])
    thumb_mcp_axis = (thumb_arc[1] - thumb_arc[0]) / thumb_lengths[0]
    thumb_transition_arc_m = float(source_thumb_stations[1] * thumb_stations[-1])
    thumb_registration = {"sourceSectionRelativeArcStations": source_thumb_stations.tolist(),
        "actualMCPIPAndSkinTip": thumb_arc.tolist(), "newSectionTargets": target_controls[16:20].tolist(),
        "metacarpalHeadExcludedFromIsolatedDigitControls": tuple(rig.data.bones[native_name("thumb", 1)].head_local),
        "MCPTransitionArcM": thumb_transition_arc_m,
        "limits": ["Original donor section centers are geometric hypotheses, not annotated source joints",
                   "Thumb deformation fields remain untouched; only source appearance correspondence changes"]}

    source_wrist = np.array(semantics["coarsePalmRegistration"]["R"]["sourceWristCentre"])
    target_wrist = np.array(rig.data.bones["DEF-hand.R"].head_local)

    def frame(radial, forward):
        y = forward / np.linalg.norm(forward)
        x = radial - y * np.dot(radial, y); x /= np.linalg.norm(x)
        return np.column_stack([x, y, np.cross(x, y)])

    source_frame = frame(source_controls[12] - source_controls[0], source_controls[8] - source_wrist)
    target_frame = frame(target_controls[12] - target_controls[0], target_controls[8] - target_wrist)
    width = np.linalg.norm(target_controls[12] - target_controls[0]) / np.linalg.norm(source_controls[12] - source_controls[0])
    length = np.linalg.norm(target_controls[8] - target_wrist) / np.linalg.norm(source_controls[8] - source_wrist)
    transform = (target_frame * np.array([width, length, width])[None, :]) @ source_frame.T
    current = (np.vstack([donor["vertices"], source_controls, source_wrist]) - source_wrist) @ transform.T + target_wrist
    start = len(donor["vertices"])
    targets = np.vstack([target_controls, target_wrist])
    sigma, steps = .025, []
    kernel = lambda points, controls: np.exp(-np.sum((points[:, None] - controls[None]) ** 2, axis=2) / (2 * sigma ** 2))
    for iteration in range(600):
        controls = current[start:]; error = targets - controls
        residual = float(np.linalg.norm(error, axis=1).max())
        if residual < .00015: break
        coefficient = np.linalg.solve(kernel(controls, controls) + np.eye(len(controls)) * 1e-7, error)
        bound = float(np.linalg.norm(coefficient, axis=1).sum() * np.exp(-.5) / sigma)
        h = min(.30, .18 / max(bound, 1e-12))
        current += h * (kernel(current, controls) @ coefficient)
        steps.append({"iteration": iteration, "controlErrorM": residual, "stepLipschitzProduct": h * bound})
    fitted = current[:start]
    residual = float(np.linalg.norm(targets - current[start:], axis=1).max())
    (out / "registration.json").write_text(json.dumps({"accepted": False, "controlResidualM": residual,
        "properInitialDeterminant": float(np.linalg.det(transform)), "steps": steps,
        "sourceControls": source_controls.tolist(), "exact75TargetControls": targets.tolist(),
        "bodySurfaceTipsPlus2mm": measured_tips, "thumbAnatomicalRegistration": thumb_registration}, indent=2) + "\n")
    assert residual < .00025, "Selected exterior does not reach the exact new hand correspondences"

    # Retopology is the coherent wearer's hand chart, never the genus1 donor cavity.
    wrist = rig.data.bones["DEF-hand.R"].head_local.copy()
    proximal = (rig.data.bones["DEF-forearm.R"].head_local - wrist).normalized()
    cuff = wrist + proximal * .028
    bm = bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.delete(bm, geom=[vertex for vertex in bm.verts if (vertex.co - wrist).length > .29], context="VERTS")
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-6,
        plane_co=cuff, plane_no=proximal, clear_outer=True, clear_inner=False)
    # Keep only the anatomical hand component nearest the named middle terminal.
    terminal = rig.data.bones["DEF-f_middle.03.R"].tail_local
    seed = min(bm.verts, key=lambda vertex: (vertex.co - terminal).length)
    keep, todo = set(), [seed]
    while todo:
        vertex = todo.pop()
        if vertex in keep: continue
        keep.add(vertex); todo.extend(edge.other_vert(vertex) for edge in vertex.link_edges)
    bmesh.ops.delete(bm, geom=[vertex for vertex in bm.verts if vertex not in keep], context="VERTS")
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.verts.ensure_lookup_table(); bm.verts.index_update(); bm.normal_update()
    boundary = [edge for edge in bm.edges if len(edge.link_faces) == 1]
    assert len(bm.verts) - len(bm.edges) + len(bm.faces) == 1
    assert all(len(edge.link_faces) in (1, 2) for edge in bm.edges)
    assert all(len([edge for edge in vertex.link_edges if edge in boundary]) == 2 for edge in boundary for vertex in edge.verts)
    original = [vertex.co.copy() for vertex in bm.verts]
    normals = [vertex.normal.copy() for vertex in bm.verts]
    original_faces = [[vertex.index for vertex in face.verts] for face in bm.faces]
    source_labels = branches["branchLabels"]
    region_ids = {digit: classification["digits"][digit]["regionId"] for digit in digits}
    group_names = {group.index: group.name for group in body.vertex_groups}
    deform = bm.verts.layers.deform.active
    def closest_arc(point, centerline):
        segments = np.diff(centerline, axis=0); lengths = np.linalg.norm(segments, axis=1)
        t = np.clip(np.sum((point - centerline[:-1]) * segments, axis=1) / (lengths * lengths), 0, 1)
        centers = centerline[:-1] + segments * t[:, None]
        distances = np.linalg.norm(centers - point, axis=1); index = int(np.argmin(distances))
        return float(distances[index]), float(np.sum(lengths[:index]) + t[index] * lengths[index])

    point_semantics, domain_witnesses = [], []
    for vertex in bm.verts:
        field = {group_names[group]: weight for group, weight in vertex[deform].items()}
        masses = {digit: sum(field.get(native_name(digit, joint), 0) for joint in (1, 2, 3)) for digit in digits}
        digit = max(masses, key=masses.get); mass = masses[digit]
        region = region_ids[digit] if mass >= .20 else 0
        point = np.array(tuple(vertex.co)); signed_mcp = float(np.dot(point - thumb_arc[0], thumb_mcp_axis))
        thumb_distance, thumb_arc_m = closest_arc(point, thumb_arc)
        other_distances = {name: closest_arc(point, target_controls[i * 4:i * 4 + 4])[0]
            for i, name in enumerate(digits) if name != "thumb"}
        thumb_is_nearest_digit = thumb_distance < min(other_distances.values())
        # Proximal thenar belongs to palm chart 0 despite thumb metacarpal influence.
        # Distal anatomical thumb is determined by MCP plane and downstream arc.
        if digit == "thumb" or (region == 0 and thumb_is_nearest_digit):
            if signed_mcp >= 0 and thumb_is_nearest_digit:
                region, digit, mass = region_ids["thumb"], "thumb", masses["thumb"]
            elif digit == "thumb":
                region = 0
        palm_blend = (region == region_ids["thumb"] and thumb_arc_m <= thumb_transition_arc_m) or (
            region not in (0, region_ids["thumb"]) and mass < .55)
        point_semantics.append((region, digit, mass, palm_blend))
        domain_witnesses.append({"vertex": vertex.index, "sourceAppearanceRegion": int(region),
            "dominantDeformationDigit": max(masses, key=masses.get), "thumbDeformationMass": masses["thumb"],
            "signedMCPDistanceM": signed_mcp, "distanceToThumbArcM": thumb_distance,
            "thumbArcDistanceM": thumb_arc_m, "otherDigitArcDistancesM": other_distances,
            "thumbNearestDigitArc": thumb_is_nearest_digit, "allowedSourceRegions": [0, int(region)] if palm_blend else [int(region)]})
    (out / "anatomical-surface-domains.json").write_text(json.dumps({"accepted": False,
        "method": "Actual MCP plane and downstream thumb arc; metacarpal deformation influence is not a source surface chart",
        "thumbRegistration": thumb_registration, "witnesses": domain_witnesses}, indent=2) + "\n")

    def section_coordinates(points, centerline):
        """Actual closest centerline segment, arc station and stable radial frame."""
        segments = np.diff(centerline, axis=0); lengths = np.linalg.norm(segments, axis=1)
        starts = np.r_[0, np.cumsum(lengths[:-1])]
        records = []
        for point in points:
            t = np.clip(np.sum((point - centerline[:-1]) * segments, axis=1) / (lengths * lengths), 0, 1)
            centers = centerline[:-1] + segments * t[:, None]
            index = int(np.argmin(np.linalg.norm(centers - point, axis=1)))
            axis = segments[index] / lengths[index]
            radial = target_frame[:, 0] - axis * np.dot(target_frame[:, 0], axis)
            radial /= np.linalg.norm(radial); normal = np.cross(axis, radial)
            delta = point - centers[index]
            records.append(((starts[index] + t[index] * lengths[index]) / lengths.sum(),
                float(np.dot(delta, radial)), float(np.dot(delta, normal)), centers[index], radial, normal, delta))
        return records

    # Positive volume control is measured from the actual skin, not assumed from
    # centerline alignment. Ease each original anatomical branch radially, keeping
    # its selected-source detail/UV chart and longitudinal correspondences intact.
    volume_controls = []
    for region in [0] + list(region_ids.values()):
        digit = next((name for name, value in region_ids.items() if value == region), None)
        centerline = target_controls[digits.index(digit) * 4:digits.index(digit) * 4 + 4] if digit else np.vstack([target_wrist, target_controls[8]])
        source_ids = np.flatnonzero(source_labels == region)
        skin_ids = [i for i, row in enumerate(point_semantics) if row[0] == region]
        assert len(source_ids) > 20 and len(skin_ids) > 3
        source_sections = section_coordinates(fitted[source_ids], centerline)
        skin_sections = section_coordinates(np.array([tuple(original[i]) for i in skin_ids]), centerline)
        profiles = []
        for station in np.linspace(0, 1, 6):
            source_local = [row for row in source_sections if abs(row[0] - station) <= .21]
            skin_local = [row for row in skin_sections if abs(row[0] - station) <= .21]
            if not source_local or not skin_local:
                source_local = source_sections; skin_local = skin_sections
            selected_radii = [max(abs(row[k]) for row in source_local) for k in (1, 2)]
            wearer_radii = [max(abs(row[k]) for row in skin_local) for k in (1, 2)]
            scales = [max(1, (wearer + .0035) / max(selected, 1e-8)) for wearer, selected in zip(wearer_radii, selected_radii)]
            profiles.append({"station": float(station), "selectedRadiiM": selected_radii,
                "actualSkinRadiiM": wearer_radii, "radialEaseScales": scales,
                "sourceSamples": len(source_local), "skinSamples": len(skin_local),
                "usedWholeRegionFallback": not any(abs(row[0] - station) <= .21 for row in source_sections) or
                    not any(abs(row[0] - station) <= .21 for row in skin_sections),
                "failsMaximum2_5": max(scales) > 2.5})
        for source_id, row in zip(source_ids, source_sections):
            station, x, y, center, radial, normal, delta = row
            sx = float(np.interp(station, [row["station"] for row in profiles], [row["radialEaseScales"][0] for row in profiles]))
            sy = float(np.interp(station, [row["station"] for row in profiles], [row["radialEaseScales"][1] for row in profiles]))
            fitted[source_id] += radial * x * (sx - 1) + normal * y * (sy - 1)
        volume_controls.append({"sourceSemanticRegion": int(region), "digit": digit or "palm/wrist",
            "actualSkinPoints": len(skin_ids), "selectedDonorPoints": len(source_ids), "profiles": profiles})
    (out / "anatomical-volume-controls.json").write_text(json.dumps({"accepted": False,
        "paddingGoalM": .0035, "method": "Measured branch section radial ease, original selected source coordinates and charts retained",
        "controls": volume_controls}, indent=2) + "\n")
    assert all(not profile["failsMaximum2_5"] for row in volume_controls for profile in row["profiles"]), "Selected branch cannot faithfully enclose actual hand volume"
    source_points = [Vector(point) for point in fitted]
    source_trees = {}
    for region in [0] + list(region_ids.values()):
        for palm_blend in (False, True):
            allowed = {region, 0} if palm_blend else {region}
            rows = [index for index, face in enumerate(donor["faces"])
                    if set(int(source_labels[i]) for i in face).issubset(allowed)]
            assert rows
            source_trees[(region, palm_blend)] = (BVHTree.FromPolygons(source_points,
                [donor["faces"][i].tolist() for i in rows], all_triangles=True), rows)
    evidence, unsupported, outer = [], [], []
    for index, (point, normal) in enumerate(zip(original, normals)):
        region, digit, mass, palm_blend = point_semantics[index]
        # MCP transition uses only palm and this thumb; distal thumb never borrows
        # another finger. Other fingers retain their measured proximal mixed field.
        source_tree, source_rows = source_trees[(region, palm_blend)]
        hits, distance = [], -.006
        ray_origin = point + normal * distance
        for _ in range(32):
            hit, hit_normal, triangle, travel = source_tree.ray_cast(ray_origin, normal, .085 - distance)
            if hit is None: break
            distance += travel
            if distance > .001 and hit_normal.dot(normal) > .05: hits.append((distance, hit.copy(), source_rows[triangle]))
            ray_origin = hit + normal * .00002; distance += .00002
        if hits:
            distance, hit, triangle = max(hits, key=lambda row: row[0])
            outer.append(hit)
            face = donor["faces"][triangle]
            bary = barycentric_transform(hit, *(Vector(fitted[i]) for i in face),
                Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
            evidence.append({"vertex": index, "sourceCompactTriangle": int(triangle), "barycentric": list(bary),
                             "paddingFromWearerM": distance, "targetSemanticRegion": int(region),
                             "targetDominantDigit": digit, "targetDigitMass": mass,
                             "palmWebBoundaryBlend": palm_blend,
                             "sourceSemanticRegions": sorted(set(int(source_labels[i]) for i in face))})
        else:
            unsupported.append({"vertex": index, "targetSemanticRegion": int(region),
                                "dominantDigit": digit, "digitMass": mass,
                                "palmWebBoundaryBlend": palm_blend}); outer.append(None)
    (out / "surface-correspondence.json").write_text(json.dumps({"accepted": False, "vertices": len(original),
        "sourceSupportedVertices": len(evidence), "unsupportedVertices": unsupported, "witnesses": evidence,
        "handPatchEuler": 1, "cuffBoundaryEdges": len(boundary)}, indent=2) + "\n")
    assert not unsupported, "Missing selected donor exterior correspondence; no offset-hand fallback is permitted"
    assert min(row["paddingFromWearerM"] for row in evidence) > .0025, "Selected padding fails the positive-thickness cavity"

    # Every reconstructed face must preserve the anatomical patch orientation.
    reversed_faces = []
    for face_index, face in enumerate(original_faces):
        a, b, c = face
        before = (original[b] - original[a]).cross(original[c] - original[a])
        after = (outer[b] - outer[a]).cross(outer[c] - outer[a])
        if not (after.length > 1e-10 and before.dot(after) > 0):
            reversed_faces.append({"face": face_index, "vertices": face, "afterAreaTwice": after.length,
                "orientationDot": before.dot(after)})
    (out / "face-orientation.json").write_text(json.dumps({"accepted": False,
        "faces": len(original_faces), "reversedOrDegenerateFaces": reversed_faces}, indent=2) + "\n")
    assert not reversed_faces, "Selected padding correspondence reverses a hand face"
    fields = []
    for vertex in bm.verts:
        four = sorted(((group_names[index], value) for index, value in vertex[deform].items() if value > .0001),
                      key=lambda row: (-row[1], row[0]))[:4]
        total = sum(value for _, value in four)
        fields.append([(name, value / total) for name, value in four])

    # Recover exact original corner texture charts, including the side of seams.
    dense_path = base / "prep02/gloves/cleaned-donor.npz"
    dense = dict(np.load(dense_path))
    assert sha(dense_path) == "f07a705f334d3d2b802fa7d23baec3e9cd54b211d160b7bbd6ab2c9f4a96541c"
    dense_points = [Vector(point) for point in dense["vertices"]]
    dense_faces = dense["faces"].tolist()
    dense_tree = BVHTree.FromPolygons(dense_points, dense_faces, all_triangles=True)
    source_uv, uv_ancestry, uv_edge_clamps = [], [], 0
    def closest_barycentric64(point, triangle):
        a, b, c = np.asarray(triangle, dtype=np.float64)
        ab, ac, ap = b - a, c - a, np.asarray(point, dtype=np.float64) - a
        normal = np.cross(ab, ac); denominator = float(np.dot(normal, normal))
        assert denominator > 0 and np.isfinite(denominator), "Actual dense donor triangle is degenerate"
        beta = float(np.dot(np.cross(ap, ac), normal) / denominator)
        gamma = float(np.dot(np.cross(ab, ap), normal) / denominator)
        bary = np.array([1 - beta - gamma, beta, gamma], dtype=np.float64)
        if bary.min() >= 0: return bary, False
        # An actual closest point on this selected source triangle, not unstable
        # float32 barycentrics or a blind independent coordinate clamp.
        candidates = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            start, end = triangle[i], triangle[j]; axis = end - start
            t = float(np.clip(np.dot(point - start, axis) / np.dot(axis, axis), 0, 1))
            row = np.zeros(3, dtype=np.float64); row[i] = 1 - t; row[j] = t
            candidates.append((float(np.linalg.norm(row @ triangle - point)), row))
        return min(candidates, key=lambda row: row[0])[1], True
    for face in donor["faces"]:
        center = donor["vertices"][face].mean(axis=0)
        row = []
        for index in face:
            query = donor["vertices"][index] * (1 - 1e-4) + center * 1e-4
            hit, _, triangle, _ = dense_tree.find_nearest(Vector(query))
            assert hit is not None
            ids = dense_faces[triangle]
            bary, clamped = closest_barycentric64(query, dense["vertices"][ids].astype(np.float64))
            uv_edge_clamps += int(clamped)
            uv = bary @ dense["originalCornerUV"][triangle].astype(np.float64)
            assert np.isfinite(uv).all()
            row.append(tuple(uv)); uv_ancestry.append(int(dense["originalTriangleRows"][triangle]))
        source_uv.append(row)

    def make_mesh(name, points, faces):
        data = bpy.data.meshes.new(name + "Mesh"); data.from_pydata(points, [], faces); data.update()
        obj = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(obj)
        for polygon in data.polygons: polygon.use_smooth = True
        return obj

    appearance = make_mesh("SelectedGloveAppearanceControl", fitted.tolist(), donor["faces"].tolist())
    layer = appearance.data.uv_layers.new(name="OriginalSelectedCornerUV")
    for face, corners in zip(appearance.data.polygons, source_uv):
        for loop, uv in zip(face.loop_indices, corners): layer.data[loop].uv = uv
    source_mat = bpy.data.materials.new("SelectedGloveOriginalPBRAuthority"); source_mat.use_nodes = True
    appearance.data.materials.append(source_mat)
    source_nodes, source_links = source_mat.node_tree.nodes, source_mat.node_tree.links
    source_nodes.clear()
    source_output = source_nodes.new("ShaderNodeOutputMaterial")
    emission = source_nodes.new("ShaderNodeEmission")
    source_links.new(emission.outputs[0], source_output.inputs["Surface"])
    image_node = source_nodes.new("ShaderNodeTexImage")
    source_links.new(image_node.outputs["Color"], emission.inputs["Color"])

    target = make_mesh("ActualSelectedGlove.R", [tuple(point) for point in outer], original_faces)
    target.data.uv_layers.new(name="SelectedGloveBakeAtlas")
    bpy.ops.object.select_all(action="DESELECT"); target.select_set(True); bpy.context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.025)
    bpy.ops.object.mode_set(mode="OBJECT")
    target_mat = bpy.data.materials.new("ActualSelectedGloveBakedPBR"); target_mat.use_nodes = True
    target.data.materials.append(target_mat)
    target_nodes = target_mat.node_tree.nodes
    destination_node = target_nodes.new("ShaderNodeTexImage"); target_nodes.active = destination_node
    scene = bpy.context.scene; scene.render.engine = "CYCLES"; scene.cycles.samples = 1; scene.cycles.device = "CPU"
    scene.render.bake.use_selected_to_active = True; scene.render.bake.cage_extrusion = .015
    scene.render.bake.max_ray_distance = .12; scene.render.bake.margin = 16
    images, maps = {}, []
    for role, filename, colorspace in (("baseColor", "baseColorTexture.png", "sRGB"),
                                     ("metallicRoughness", "metallicRoughnessTexture.png", "Non-Color")):
        original_path = base / "prep02/gloves" / filename
        expected_map = "9633beec8bf2bb3bd73918589b931d2fc4f33f8e3e702415094ed173a129f95c" if role == "baseColor" else "a7a712769a73844a9560d4bef1d163ce3fb8721e388d1a7ecfa07a3515280e67"
        assert sha(original_path) == expected_map
        source_image = bpy.data.images.load(str(original_path), check_existing=True)
        source_image.colorspace_settings.name = colorspace; image_node.image = source_image
        image = bpy.data.images.new("ActualSelectedGlove" + role, 4096, 4096, alpha=False)
        image.colorspace_settings.name = colorspace; destination_node.image = image
        bpy.ops.object.select_all(action="DESELECT"); appearance.select_set(True); target.select_set(True)
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.bake(type="EMIT")
        image.filepath_raw = str(out / (role + ".png")); image.file_format = "PNG"; image.save(); image.pack()
        images[role] = image; maps.append({"role": role, "originalPath": str(original_path),
            "originalSHA256": sha(original_path), "bakedPath": image.filepath_raw, "bakedSHA256": sha(image.filepath_raw)})
    normal_image = bpy.data.images.new("ActualSelectedGlovePaddingNormal", 4096, 4096, alpha=False)
    normal_image.colorspace_settings.name = "Non-Color"; destination_node.image = normal_image
    bpy.ops.object.bake(type="NORMAL")
    normal_image.filepath_raw = str(out / "padding-normal.png"); normal_image.file_format = "PNG"
    normal_image.save(); normal_image.pack()
    maps.append({"role": "paddingNormal", "bakedPath": normal_image.filepath_raw,
                 "bakedSHA256": sha(normal_image.filepath_raw), "authority": "Measured fitted selected compact donor surface"})
    # Build true thin cloth around the coherent hand cavity and connect both cuff rings.
    outer_uv = [[tuple(target.data.uv_layers.active.data[i].uv) for i in face.loop_indices] for face in target.data.polygons]
    count = len(original)
    points = [tuple(point) for point in outer] + [tuple(point + normal * .001) for point, normal in zip(original, normals)]
    faces = original_faces + [[i + count for i in face[::-1]] for face in original_faces]
    corners = outer_uv + [row[::-1] for row in outer_uv]
    vertex_uv = {}
    for face, row in zip(original_faces, outer_uv):
        for index, uv in zip(face, row): vertex_uv.setdefault(index, uv)
    for edge in boundary:
        face = edge.link_faces[0]; indices = [vertex.index for vertex in face.verts]
        for a, b in zip(indices, indices[1:] + indices[:1]):
            if {a, b} == {vertex.index for vertex in edge.verts}: break
        faces.extend([[b, a, a + count], [b, a + count, b + count]])
        corners.extend([[vertex_uv[b], vertex_uv[a], vertex_uv[a]], [vertex_uv[b], vertex_uv[a], vertex_uv[b]]])
    old_data = target.data
    new_data = bpy.data.meshes.new("ActualSelectedGloveProductionSurface")
    new_data.from_pydata(points, [], faces); new_data.update(); target.data = new_data
    new_data.materials.append(target_mat); layer = new_data.uv_layers.new(name="SelectedGloveBakeAtlas")
    for polygon, row in zip(new_data.polygons, corners):
        polygon.use_smooth = True
        for loop, uv in zip(polygon.loop_indices, row): layer.data[loop].uv = uv
    nodes, links = target_mat.node_tree.nodes, target_mat.node_tree.links
    principal = nodes.get("Principled BSDF")
    destination_node.image = images["baseColor"]; links.new(destination_node.outputs["Color"], principal.inputs["Base Color"])
    packed = nodes.new("ShaderNodeTexImage"); packed.image = images["metallicRoughness"]
    split = nodes.new("ShaderNodeSeparateColor"); split.mode = "RGB"
    links.new(packed.outputs["Color"], split.inputs["Color"])
    links.new(split.outputs["Green"], principal.inputs["Roughness"]); links.new(split.outputs["Blue"], principal.inputs["Metallic"])
    normal_texture = nodes.new("ShaderNodeTexImage"); normal_texture.image = normal_image
    normal_map = nodes.new("ShaderNodeNormalMap")
    links.new(normal_texture.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], principal.inputs["Normal"])

    objects = [target]
    left = target.copy(); left.data = target.data.copy(); left.name = "ActualSelectedGlove.L"
    bpy.context.scene.collection.objects.link(left)
    for vertex in left.data.vertices: vertex.co.x *= -1
    lbm = bmesh.new(); lbm.from_mesh(left.data); bmesh.ops.reverse_faces(lbm, faces=list(lbm.faces)); lbm.to_mesh(left.data); lbm.free()
    objects.append(left)
    topology = []
    for obj, side in zip(objects, ("R", "L")):
        groups = {}
        for index, field in enumerate(fields + fields):
            for name, weight in field:
                name = name if side == "R" else name.replace(".R", ".L")
                if name not in groups: groups[name] = obj.vertex_groups.new(name=name)
                groups[name].add([index], weight, "REPLACE")
        obj.parent = rig; modifier = obj.modifiers.new("ExactShared75Glove", "ARMATURE")
        modifier.object = rig; modifier.use_deform_preserve_volume = False
        check = bmesh.new(); check.from_mesh(obj.data)
        assert all(len(edge.link_faces) == 2 for edge in check.edges)
        assert len(check.verts) - len(check.edges) + len(check.faces) == 2
        topology.append({"name": obj.name, "vertices": len(check.verts), "faces": len(check.faces), "Euler": 2,
                         "boundaryEdges": 0, "cuffRingEdges": len(boundary), "shared75": True})
        check.free()
    bpy.data.objects.remove(appearance, do_unlink=True)
    bm.free()
    report = {"accepted": False, "recipeSHA256": sha(__file__), "selectedPrototypeSHA256": sha(prototype_path),
        "denseSourceSHA256": sha(dense_path), "controlResidualM": residual, "sourceSupportedOuterVertices": len(evidence),
        "outerMinimumPaddingM": min(row["paddingFromWearerM"] for row in evidence),
        "sourceCornerTriangleIDs": uv_ancestry, "sourceCornerFloat64ClosestEdgeProjections": uv_edge_clamps,
        "originalPBRBake": maps, "objects": topology,
        "limits": ["One reconstructed exterior and original-PBR atlas candidate; not parent art acceptance",
                   "Padding normal bake derives from selected compact donor; source microdetail beyond that derivative is unqualified",
                   "Selected-to-active bake may query an adjacent finger; per-pixel semantic source correspondence remains unqualified",
                   "Manifold topology does not prove zero geometric self-intersections or grip surface clearance",
                   "Actual full dressed movement, original appearance similarity and device cost require parent review"]}
    path = out / "report.json"; path.write_text(json.dumps(report, indent=2) + "\n")
    return {"objects": objects, "materials": [target_mat], "report": report, "reportPath": str(path)}
