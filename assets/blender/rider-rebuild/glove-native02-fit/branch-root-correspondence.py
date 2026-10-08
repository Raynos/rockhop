"""Match actual source/target geometric split events, never MCP centers.

Both source and target retain complete connected palm/web geometry. A geometric
root is the existing source section's signed phase relative to a connectivity
split, transported to the corresponding target split and actual surface tip.
Negative phases explicitly remain on the connected web. No angular samples,
source faces or failed root trials are silently dropped.
"""
import importlib.util
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE.parent / "glove-charts01" / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


SOURCE = load("native02_source_sections", "measure-source.py")
AUDIT = load("native02_branch_contours", "audit-hand-anatomy.py")
GEOMETRY = load("native02_fit_geometry", "geometry-checks.py")
DIGITS = ["pinky", "ring", "middle", "index", "thumb"]
PADDING = .0035
MINIMUM_PADDING = .0025
MAX_RADIAL_EASE = 2.5


def normalize(vector):
    return vector / np.linalg.norm(vector)


def edges_of(faces):
    return np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)


def branch_component(vertices, edges, coordinate, cutoff, anchor):
    components = AUDIT.components_beyond(vertices, edges, coordinate, cutoff)
    return next(component for component in components if anchor in component)


def split_event(vertices, faces, labels, digit, axis, cuff_ids):
    """Find the exact vertex-critical interval where the seeded branch separates.

    The anchor's above-plane component shrinks monotonically. Binary search over
    every original vertex critical level therefore skips no possible event.
    Geometry, independent distal branch seeds and the real cuff are authority;
    native weights and skeleton joint centers are unused.
    """
    coordinate = vertices @ axis
    anchor = int(np.flatnonzero(labels == digit)[np.argmax(coordinate[labels == digit])])
    tagged = labels.copy()
    tagged[cuff_ids] = -2
    edges = edges_of(faces)
    levels = np.unique(coordinate[coordinate < coordinate[anchor]])
    cuts = (levels[:-1] + levels[1:]) * .5
    trials = []

    def query(index):
        ids = branch_component(vertices, edges, coordinate, float(cuts[index]), anchor)
        tags = sorted(set(int(value) for value in tagged[ids] if value != -1))
        pure = tags == [digit]
        trials.append({"criticalInterval": int(index), "cutoff": float(cuts[index]),
                       "componentVertexCount": len(ids), "geometricSeedLabels": tags, "pure": pure})
        return pure, ids, tags

    assert not query(0)[0], "Initial component must include the connected palm/cuff"
    assert query(len(cuts) - 1)[0], "Actual distal branch anchor must separate"
    lo, hi = 0, len(cuts) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if query(mid)[0]:
            hi = mid
        else:
            lo = mid
    assert not query(lo)[0] and query(hi)[0]
    event = float(levels[hi])
    # The split level is an original geometric critical vertex, not an epsilon
    # moved bone center. Root phase is measured from that level to the real tip.
    record = {"eventProjection": event, "actualTipProjection": float(coordinate[anchor]),
              "criticalVertexIds": np.flatnonzero(coordinate == event).tolist(),
              "beforeInterval": [float(levels[lo]), float(levels[lo + 1])],
              "afterInterval": [float(levels[hi]), float(levels[hi + 1])],
              "anchorVertex": anchor, "axis": axis.tolist(), "trials": trials,
              "usesNativeWeights": False, "usesJointCenters": False}
    return record, coordinate, edges, anchor, tagged


def matched_contour(vertices, faces, coordinate, edges, anchor, tagged, center, axis):
    cutoff = float(np.dot(center, axis))
    component = branch_component(vertices, edges, coordinate, cutoff, anchor)
    contours = AUDIT.all_contours(vertices, faces, center, axis)
    selected = []
    for contour in contours:
        positive = [a if coordinate[a] > cutoff else b for a, b in contour["sourceEdges"]]
        if np.all(np.isin(positive, component)):
            selected.append(contour)
    assert len(selected) == 1, "Branch component must have exactly one complete surface contour"
    contour = selected[0]
    section = SOURCE.section(vertices, faces, contour["centroid"], axis)
    assert set(section["selectedSourceTriangles"]) == set(contour["sourceHandTriangles"])
    assert section["missingRays"] == section["multipleHitRays"] == section["selectedContourDegreeNotTwo"] == 0
    tags = sorted(set(int(value) for value in tagged[component] if value != -1))
    return contour, section, tags


def on_arc(points, stations):
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    arcs = np.r_[0, np.cumsum(lengths)]
    assert np.all(lengths > 0)
    return np.array([[np.interp(s * arcs[-1], arcs, points[:, k]) for k in range(3)] for s in stations])


def target_sections(body, hand, atlas, source_report, report):
    source_vertices, source_faces = atlas["vertices"], atlas["faces"]
    source_labels = atlas["sourceBranchLabels"].astype(int) - 1
    source_labels[atlas["sourceBranchLabels"] == 0] = -1
    target_vertices, target_faces = hand["vertices"], hand["faces"]
    target_labels = hand["sourceHandBranchSeeds"]
    audit = source_report["anatomyAudit"]["sides"]["R"]["branches"]
    source_cuff = source_vertices[atlas["cuffBoundaryVertexIds"]].mean(0)
    source_roots = np.array([atlas[digit + "_centers"][0] for digit in DIGITS])
    root_rows, target_roots = [], []
    for digit_id, digit in enumerate(DIGITS):
        record = {"digit": digit, "sections": [], "nativeFieldGateUsed": False,
                  "MCPPositionUsedAsRoot": False}
        report.append(record)
        source_axis = normalize(atlas[digit + "_centers"][1] - atlas[digit + "_centers"][0])
        target_axis = normalize(np.array(audit[digit]["surfacePCAAxis"]))
        sr, sc, se, sa, sl = split_event(source_vertices, source_faces, source_labels, digit_id,
                                        source_axis, atlas["cuffBoundaryVertexIds"])
        tr, tc, te, ta, tl = split_event(target_vertices, target_faces, target_labels, digit_id,
                                        target_axis, np.unique(hand["cuffBoundaryEdges"]))
        record.update({"sourceSplit": sr, "targetSplit": tr})
        source_origin = atlas[digit + "_centers"][0]
        source_contour, _, source_tags = matched_contour(source_vertices, source_faces, sc, se, sa, sl,
                                                        source_origin, source_axis)
        source_row = next(row for row in source_report["sections"] if row["digit"] == digit and row["station"] == 0)
        source_original_rows = atlas["sourcePrototypeFaceRows"][source_contour["sourceHandTriangles"]]
        assert set(source_original_rows.tolist()) == set(source_row["selectedSourceTriangles"])
        phase = float((np.dot(source_origin, source_axis) - sr["eventProjection"]) /
                      (sr["actualTipProjection"] - sr["eventProjection"]))
        assert phase < 1, "Existing source root cannot be beyond the actual source tip"
        target_projection = tr["eventProjection"] + phase * (tr["actualTipProjection"] - tr["eventProjection"])
        target_origin = target_vertices[ta] + target_axis * (target_projection - tc[ta])
        target_contour, target_section, target_tags = matched_contour(target_vertices, target_faces, tc, te, ta, tl,
                                                                     target_origin, target_axis)
        assert source_tags == target_tags, "Source/target connected web branch footprint differs"
        root = target_contour["centroid"]
        target_roots.append(root)
        record.update({
                  "existingSourceRootPhase": phase, "sourceRootConnectedSeedLabels": source_tags,
                  "targetRootConnectedSeedLabels": target_tags, "sourceRootIsConnectedWeb": phase < 0,
                  "targetRoot": root.tolist(), "targetRootSourceEdges": target_contour["sourceEdges"],
                  "targetRootEdgeFractions": target_contour["sourceEdgeFractions"],
                  "targetRootSourceTriangles": target_contour["sourceHandTriangles"],
                  "rootTargetSection": target_section})
        names = body["jointNames"].tolist()
        stem = "thumb" if digit == "thumb" else "f_" + digit
        digit_joints = [names.index("DEF-" + stem + ".%02d.R" % segment) for segment in (1, 2, 3)]
        root_faces = np.array(target_contour["sourceHandTriangles"])
        record["separateArticulationMeasurements"] = {field: float(hand[field][target_faces[root_faces]][:, :, digit_joints].sum(2).mean())
                                                      for field in ("nativeCoefficients", "fourCoefficients", "fullRawCoefficients", "fullCoefficients")}
        root_rows.append((root, target_axis, tr, record))
    target_roots = np.array(target_roots)

    def frame(radial, forward):
        y = normalize(forward)
        x = normalize(radial - y * np.dot(radial, y))
        return np.column_stack([x, y, np.cross(x, y)])

    sf = frame(source_roots[3] - source_roots[0], source_roots[2] - source_cuff)
    tf = frame(target_roots[3] - target_roots[0], target_roots[2] - hand["cuffOrigin"])
    width = np.linalg.norm(target_roots[3] - target_roots[0]) / np.linalg.norm(source_roots[3] - source_roots[0])
    length = np.linalg.norm(target_roots[2] - hand["cuffOrigin"]) / np.linalg.norm(source_roots[2] - source_cuff)
    transform = (tf * [width, length, width]) @ sf.T
    assert np.linalg.det(transform) > 0
    constraints = []
    for digit, (root, axis, event, record) in zip(DIGITS, root_rows):
        centers = np.array([row["centroid"] for row in audit[digit]["sections"] if row["qualified"]])
        centers = centers[(centers - root) @ axis > 0]
        assert len(centers) >= 2, "Root correspondence would erase the measured distal centerline"
        tip = centers[-1] + axis * (event["actualTipProjection"] - np.dot(centers[-1], axis) + MINIMUM_PADDING)
        line = np.vstack([root, centers, tip])
        source_centers = atlas[digit + "_centers"]
        arcs = np.r_[0, np.cumsum(np.linalg.norm(np.diff(source_centers, axis=0), axis=1))]
        centers = on_arc(line, arcs / arcs[-1])
        record["targetCenterline"] = line.tolist()
        for station, center in enumerate(centers):
            tangent = axis if station == 0 else normalize(centers[min(station + 1, 3)] - centers[max(station - 1, 0)])
            source = next(row for row in source_report["sections"] if row["digit"] == digit and row["station"] == station)
            radial = transform @ np.array(source["radialFrame"])[:, 0]
            radial = normalize(radial - tangent * np.dot(radial, tangent))
            target_frame = np.column_stack([radial, np.cross(tangent, radial)])
            target = record["rootTargetSection"] if station == 0 else None
            if station != 3:
                if target is None:
                    target = SOURCE.section(target_vertices, target_faces, center, tangent)
                assert target["missingRays"] == target["multipleHitRays"] == target["selectedContourDegreeNotTwo"] == 0
                tf = np.array(target["radialFrame"])
                phase = np.arctan2(np.dot(radial, tf[:, 1]), np.dot(radial, tf[:, 0]))
                radii = np.array([row["radiusSourceUnits"] for row in target["rays"]])
                indices = (np.arange(360) + np.rad2deg(phase)) % 360
                target_radii = np.interp(indices, np.arange(361), np.r_[radii, radii[0]])
            else:
                target_radii = np.zeros(360)
            source_id = source_report["sections"].index(source)
            witnesses = source_report["rayWitnesses"][source_report["rayWitnesses"][:, 0].astype(int) == source_id]
            assert len(witnesses) == 360 and np.array_equal(witnesses[:, 1], np.arange(360))
            source_radii = witnesses[:, 6] * width
            ease = max(1., float(np.max((target_radii + PADDING) / source_radii)))
            assert ease <= MAX_RADIAL_EASE, ("Source contour distortion exceeds unchanged bound", digit, station, ease)
            angles = np.deg2rad(np.arange(360))
            desired = center + np.einsum("ij,nj->ni", target_frame,
                         np.column_stack([np.cos(angles), np.sin(angles)]) * (source_radii * ease)[:, None])
            constraints.extend((int(row[2]), row[3:6], goal) for row, goal in zip(witnesses, desired))
            record["sections"].append({"station": station, "center": center.tolist(),
                "frame": target_frame.tolist(), "radialEase": ease, "terminalSourceCap": station == 3,
                "targetMinRadiusM": float(target_radii.min()), "targetMaxRadiusM": float(target_radii.max()),
                "angularContainmentMarginM": float(np.min(source_radii * ease - target_radii)),
                "all360OriginalSourceDirectionsRetained": True})
        record.pop("rootTargetSection")
    assert len(constraints) == 7200
    return transform, source_cuff, report, constraints
