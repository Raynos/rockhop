"""Derive actual distal branches without bone/weight labels, then audit joints.

Source geometry and coefficients stay untouched. Surface-derived centerlines
are measurements; extrapolated proximal centers are explicit proposals only.
"""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[4]


def load(name, file):
    spec = spec_from_file_location(name, Path(__file__).with_name(file))
    value = module_from_spec(spec); spec.loader.exec_module(value)
    return value


def components_beyond(vertices, edges, coordinate, cutoff):
    ids = np.flatnonzero(coordinate > cutoff)
    inverse = np.full(len(vertices), -1, int); inverse[ids] = np.arange(len(ids))
    selected = edges[np.all(coordinate[edges] > cutoff, axis=1)]
    graph = coo_matrix((np.ones(len(selected) * 2),
        (np.r_[inverse[selected[:, 0]], inverse[selected[:, 1]]],
         np.r_[inverse[selected[:, 1]], inverse[selected[:, 0]]])), shape=(len(ids), len(ids))).tocsr()
    count, labels = connected_components(graph)
    return [ids[labels == i] for i in range(count)]


def all_contours(vertices, faces, center, axis):
    signed = np.sum((vertices - center) * axis, axis=1)
    rows = np.flatnonzero((signed[faces].min(1) < 0) & (signed[faces].max(1) > 0))
    nodes, points, source_edges, fractions, segments, face_rows = {}, [], [], [], [], []
    for row in rows:
        triangle = faces[row]; ends = []
        for a, b in zip(triangle, np.roll(triangle, -1)):
            lo, hi = sorted((int(a), int(b)))
            if signed[lo] * signed[hi] >= 0:
                continue
            key = (lo, hi)
            if key not in nodes:
                t = float(signed[lo] / (signed[lo] - signed[hi]))
                nodes[key] = len(points); source_edges.append(key); fractions.append(t)
                points.append(vertices[lo] * (1 - t) + vertices[hi] * t)
            ends.append(nodes[key])
        assert len(ends) == 2
        segments.append(ends); face_rows.append(int(row))
    points = np.array(points); adjacency = [[] for _ in points]
    for index, (a, b) in enumerate(segments):
        adjacency[a].append((b, index)); adjacency[b].append((a, index))
    remaining = set(range(len(points))); contours = []
    while remaining:
        first = min(remaining); order, triangles, previous, current = [], [], -1, first
        if len(adjacency[current]) != 2:
            raise ValueError("Open contour at this slice")
        while True:
            order.append(current); remaining.remove(current)
            choices = [(v, row) for v, row in adjacency[current] if v != previous]
            nxt, row = choices[0]; triangles.append(face_rows[row])
            if nxt == first:
                break
            assert nxt in remaining and len(adjacency[nxt]) == 2
            previous, current = current, nxt
        poly = points[order]
        radial = np.array([1., 0, 0]); radial -= axis * np.dot(axis, radial); radial /= np.linalg.norm(radial)
        normal = np.cross(axis, radial)
        relative = poly - center
        xy = np.column_stack([np.sum(relative * radial, axis=1), np.sum(relative * normal, axis=1)])
        following = np.roll(xy, -1, axis=0)
        cross = xy[:, 0] * following[:, 1] - following[:, 0] * xy[:, 1]
        area_twice = cross.sum(); assert abs(area_twice) > 1e-12
        centroid2 = np.sum((xy + following) * cross[:, None], axis=0) / (3 * area_twice)
        centroid = center + radial * centroid2[0] + normal * centroid2[1]
        contours.append({"centroid": centroid, "areaM2": abs(float(area_twice)) * .5,
            "sourceHandTriangles": triangles, "sourceEdges": [source_edges[i] for i in order],
            "sourceEdgeFractions": [fractions[i] for i in order], "polygon": poly})
    return contours


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", required=True)
    args = parser.parse_args(); out = ROOT / args.out; out.mkdir(parents=True, exist_ok=False)
    fit = load("fit_anatomy", "fit-exterior.py")
    base = Path("docs/evidence/rider-rebuild/glove-charts01/target01")
    body = dict(np.load(ROOT / base / "native-body.npz")); names = body["jointNames"].tolist()
    contract_path = Path("harness/out/rider-rebuild/construction01/combined04/rider-contract.json")
    contract = json.loads((ROOT / contract_path).read_text())
    report = {"acceptedAnatomy": False, "status": "ACTUAL_MESH_BRANCH_AND_NATIVE_JOINT_AUDIT",
              "recipe": fit.pin(Path(__file__).resolve().relative_to(ROOT)), "body": fit.pin(base / "native-body.npz"),
              "contract": fit.pin(contract_path), "sides": {}}
    for side in ("R", "L"):
        hand_path = base / ("native-hand-" + side + ".npz"); hand = dict(np.load(ROOT / hand_path))
        vertices, faces = hand["vertices"], hand["faces"]
        edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
        cuff = vertices[np.unique(hand["cuffBoundaryEdges"])].mean(0)
        centered = vertices - vertices.mean(0)
        _, eigenvectors = np.linalg.eigh(np.einsum("ni,nj->ij", centered, centered))
        distal = eigenvectors[:, -1]; distal *= np.sign(np.dot(distal, vertices.mean(0) - cuff))
        coordinate = np.sum((vertices - cuff) * distal, axis=1)
        trials, long_components, long_cut = [], None, None
        # Every actual vertex critical level is considered; no guessed bone plane.
        cuts = np.unique(coordinate[(coordinate > .07) & (coordinate < .18)]) + 1e-9
        for cutoff in cuts:
            components = components_beyond(vertices, edges, coordinate, cutoff)
            sizes = sorted([len(row) for row in components], reverse=True)
            trials.append({"cutoffM": float(cutoff), "componentSizes": sizes})
            if len(components) == 4 and min(map(len, components)) >= 20:
                long_components, long_cut = components, float(cutoff)
                break
        assert long_components is not None
        # Native source axis -Y goes across index-to-pinky. Geometry establishes
        # the four disconnected branches; names follow their actual spatial order.
        long_components.sort(key=lambda ids: -float(vertices[ids, 1].mean()))
        branch = {name: ids for name, ids in zip(fit.DIGITS[:4], long_components)}
        thumb, thumb_cut = None, None
        for cutoff in cuts[cuts < long_cut]:
            components = components_beyond(vertices, edges, coordinate, cutoff)
            if len(components) != 2 or min(map(len, components)) < 20:
                continue
            contains_long = [all(np.intersect1d(ids, long).size for long in long_components) for ids in components]
            if sum(contains_long) == 1:
                thumb = components[contains_long.index(False)]; thumb_cut = float(cutoff)
                break
        assert thumb is not None; branch["thumb"] = thumb
        seed_labels = np.full(len(vertices), -1, int)
        for i, digit in enumerate(fit.DIGITS):
            assert np.all(seed_labels[branch[digit]] == -1)
            seed_labels[branch[digit]] = i
        closed_v, closed_f = fit.GEOMETRY.close_planar_cuff(vertices, faces)
        side_report = {"hand": fit.pin(hand_path), "pcaDistalAxis": distal.tolist(),
            "fourLongBranchCutoffM": long_cut, "thumbSeparationCutoffM": thumb_cut,
            "topologyTrials": trials, "branchDerivationUsesWeights": False, "branches": {}, "jointAudit": []}
        report["sides"][side] = side_report
        for digit in fit.DIGITS:
            ids = branch[digit]; cloud = vertices[ids]; mean = cloud.mean(0)
            _, eig = np.linalg.eigh(np.einsum("ni,nj->ij", cloud - mean, cloud - mean))
            axis = eig[:, -1]; axis *= np.sign(np.dot(axis, distal))
            projection = np.sum((cloud - mean) * axis, axis=1)
            sections = []
            for fraction in np.linspace(.15, .85, 8):
                station = float(projection.min() + fraction * np.ptp(projection))
                contours = all_contours(vertices, faces, mean + axis * station, axis)
                candidates = []
                for contour in contours:
                    supporting = np.any(np.isin(faces[contour["sourceHandTriangles"]], ids), axis=1)
                    support = float(supporting.mean())
                    if support >= .95:
                        candidates.append((contour, support))
                if len(candidates) != 1:
                    sections.append({"fraction": float(fraction), "qualified": False, "candidateCount": len(candidates)})
                    continue
                contour, support = candidates[0]
                query = fit.GEOMETRY.signed_distances([contour["centroid"]], closed_v, closed_f)
                assert query["signedDistance"][0] < 0 and not query["ambiguous"][0]
                contour.pop("polygon")
                contour["centroid"] = contour["centroid"].tolist()
                sections.append({"fraction": float(fraction), "qualified": True, "trueBranchFaceSupport": support,
                                 "centroidClearanceM": float(-query["signedDistance"][0]), **contour})
            centers = np.array([row["centroid"] for row in sections if row["qualified"]])
            assert len(centers) >= 3
            branches_record = {"seedHandVertices": ids.tolist(), "surfacePCAAxis": axis.tolist(),
                "seedMean": mean.tolist(), "sections": sections,
                "centerlineLengthM": float(np.linalg.norm(np.diff(centers, axis=0), axis=1).sum())}
            side_report["branches"][digit] = branches_record
            for segment in (1, 2, 3):
                name = "DEF-" + ("thumb" if digit == "thumb" else "f_" + digit) + ".%02d." % segment + side
                k = names.index(name); head, tail = body["jointHeads"][k], body["jointTails"][k]
                t = np.linspace(0, 1, 33)
                probes = head * (1 - t[:, None]) + tail * t[:, None]
                query = fit.GEOMETRY.signed_distances(probes, closed_v, closed_f)
                assert not np.any(query["ambiguous"])
                matrix = body["jointMatrices"][k][:3, :3]
                direction = (tail - head) / np.linalg.norm(tail - head)
                driver = contract["driver"]["digitFlex"]["right" if side == "R" else "left"][name]
                axis_world = matrix @ np.array(driver["axisLocal"]); axis_world /= np.linalg.norm(axis_world)
                # Propose transverse recentering from measured surface centers.
                # Proximal extrapolation remains explicit, never certified as an
                # anatomical knuckle simply because it is inside the surface.
                center_station = np.sum((centers - mean) * axis, axis=1)
                proposal = []
                for endpoint, point in (("head", head), ("tail", tail)):
                    station = float(np.dot(point - mean, axis))
                    if station < center_station[0]:
                        pair = (0, 1); extrapolation = float(center_station[0] - station)
                    elif station > center_station[-1]:
                        pair = (-2, -1); extrapolation = float(station - center_station[-1])
                    else:
                        hi = int(np.searchsorted(center_station, station, side="right")); hi = min(hi, len(centers)-1)
                        pair = (max(hi - 1, 0), hi); extrapolation = 0.
                    a, b = pair; u = (station - center_station[a]) / (center_station[b] - center_station[a])
                    proposed = centers[a] * (1 - u) + centers[b] * u
                    q = fit.GEOMETRY.signed_distances([proposed], closed_v, closed_f)
                    proposal.append({"endpoint": endpoint, "point": proposed.tolist(),
                        "displacementM": float(np.linalg.norm(proposed - point)), "surfaceCurveExtrapolationM": extrapolation,
                        "signedDistanceM": float(q["signedDistance"][0]), "anatomicalJointAccepted": False})
                side_report["jointAudit"].append({"joint": name,
                    "anatomicalRole": ("CMC/metacarpal" if segment == 1 else "MCP/proximal phalanx" if segment == 2 else "IP/distal phalanx") if digit == "thumb" else ("MCP/proximal phalanx" if segment == 1 else "PIP/middle phalanx" if segment == 2 else "DIP/distal phalanx"),
                    "head": head.tolist(), "tail": tail.tolist(), "sampleFractions": t.tolist(),
                    "signedDistancesM": query["signedDistance"].tolist(), "nearestHandTriangles": query["triangleRow"].tolist(),
                    "outsideSampleCount": int(np.sum(query["signedDistance"] > 0)),
                    "maximumOutsideDistanceM": float(max(0, query["signedDistance"].max())),
                    "properFrameDeterminant": float(np.linalg.det(matrix)),
                    "localYAxisDirectionResidual": float(np.linalg.norm(matrix[:, 1] - direction)),
                    "flexAxisDotBone": float(np.dot(axis_world, direction)), "flexAxisWorld": axis_world.tolist(),
                    "surfaceCenterlineProposal": proposal})
        path = out / ("topological-branches-" + side + ".npz")
        np.savez_compressed(path, sourceHandVertices=vertices, sourceHandFaces=faces,
                            sourceHandBranchSeeds=seed_labels, pcaDistalAxis=distal, pcaDistalCoordinate=coordinate)
        side_report["output"] = fit.pin(path.relative_to(ROOT))
    report["limits"] = ["Actual branch connectivity and distal surface centroids are independent of heat fields and bone labels.",
        "Branch names follow native geometry ordering only after four long components and a separate thumb have been identified.",
        "MCP planes may lie in the connected palm; they are not assumed to be isolated surface-digit roots.",
        "Extrapolated proximal surface-center proposals are not certified joint anatomy. A corrected derivative must verify actual joint position and motion.",
        "No native rig, body positions, rest matrices, fields, driver or glove fit changed."]
    (out / "anatomy-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "sides": {side: {
        "longCutoffM": row["fourLongBranchCutoffM"], "thumbCutoffM": row["thumbSeparationCutoffM"],
        "outsideSegments": [{"joint": item["joint"], "count": item["outsideSampleCount"], "maximumM": item["maximumOutsideDistanceM"]}
                            for item in row["jointAudit"] if item["outsideSampleCount"]]} for side, row in report["sides"].items()}}))


if __name__ == "__main__":
    main()
