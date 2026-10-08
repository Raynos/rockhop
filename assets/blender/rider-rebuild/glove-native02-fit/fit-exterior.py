"""Fit the unchanged selected exterior using anatomical contours and mesh ARAP.

No outer vertex is obtained from a body-normal ray or a replacement hand mesh.
The body is a unilateral obstacle; all output exterior rows retain source IDs.
"""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import time

import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve


def module(name, file):
    path = Path(__file__).with_name(file) if file == "branch-root-correspondence.py" else Path(__file__).resolve().parent.parent / "glove-charts01" / file
    spec = spec_from_file_location(name, path)
    value = module_from_spec(spec); spec.loader.exec_module(value)
    return value


SOURCE = module("measure", "measure-source.py")
GEOMETRY = module("geometry", "geometry-checks.py")
ROOT, pin = SOURCE.ROOT, SOURCE.pin
DIGITS = ["pinky", "ring", "middle", "index", "thumb"]
PADDING = .0035
MINIMUM_PADDING = .0025
MAX_RADIAL_EASE = 2.5


def normalize(vector):
    return vector / np.linalg.norm(vector)


def hand_frame(radial, forward):
    y = normalize(forward)
    x = normalize(radial - y * np.dot(radial, y))
    return np.column_stack([x, y, np.cross(x, y)])


def on_arc(points, stations):
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    arcs = np.r_[0, np.cumsum(lengths)]
    return np.array([[np.interp(s * arcs[-1], arcs, points[:, k]) for k in range(3)] for s in stations])


ROOTS = module("native02_branch_roots", "branch-root-correspondence.py")
target_sections = ROOTS.target_sections


def proper_rotations(source_edges, target_edges, edge_a, edge_b, weights, count):
    covariance = np.zeros((count, 3, 3))
    products = np.einsum("ni,nj->nij", target_edges, source_edges) * weights[:, None, None]
    np.add.at(covariance, edge_a, products); np.add.at(covariance, edge_b, products)
    u, _, vh = np.linalg.svd(covariance)
    sign = np.ones((count, 3)); sign[:, 2] = np.linalg.det(np.einsum("nij,njk->nik", u, vh))
    return np.einsum("nij,njk->nik", u * sign[:, None, :], vh)


def positive_orientation_path(before, after, faces):
    """Analytic lower bound for normal(t) dot normal(0), 0<=t<=1.

    Face edges interpolate linearly, so this dot product is quadratic. Checking
    its endpoints and interior stationary minimum certifies the entire step.
    """
    first = before[faces[:, 1]] - before[faces[:, 0]]
    second = before[faces[:, 2]] - before[faces[:, 0]]
    delta = after - before
    df = delta[faces[:, 1]] - delta[faces[:, 0]]
    ds = delta[faces[:, 2]] - delta[faces[:, 0]]
    normal = np.cross(first, second)
    a = np.sum(np.cross(df, ds) * normal, axis=1)
    b = np.sum((np.cross(df, second) + np.cross(first, ds)) * normal, axis=1)
    c = np.sum(normal * normal, axis=1)
    minimum = np.minimum(c, a + b + c)
    stationary = np.divide(-b, 2 * a, out=np.zeros_like(a), where=a > 0)
    interior = (a > 0) & (stationary > 0) & (stationary < 1)
    minimum[interior] = np.minimum(minimum[interior], (a * stationary**2 + b * stationary + c)[interior])
    return bool(np.all(minimum > 1e-26)), float(np.min(minimum / np.maximum(c, 1e-30)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--target", required=True, help="Fresh native02 target directory")
    parser.add_argument("--iterations", type=int, default=30)
    args = parser.parse_args()
    started = time.monotonic()
    output = (ROOT / args.out).resolve()
    assert output.is_relative_to(ROOT / "harness/out/rider-rebuild/glove-native02-fit")
    output.mkdir(parents=True, exist_ok=False)
    base = Path("docs/evidence/rider-rebuild/glove-charts01")
    target = (ROOT / args.target).resolve()
    target_report = json.loads((target / "target-extraction.json").read_text())
    assert target_report["status"] == "ACTUAL_NATIVE02_TARGET_EXTRACTION_ONLY"
    paths = {"body": (target / "native-body.npz").relative_to(ROOT),
             "hand": (target / "native-hand-R.npz").relative_to(ROOT),
             "atlas": base / "atlas01/source-atlas.npz", "sections": base / "source-measurements.json",
             "witnesses": base / "source-section-witnesses.npz",
             "anatomyAudit": base / "anatomy-audit01/anatomy-audit.json"}
    pins = {name: pin(path) for name, path in paths.items()}
    assert pins["body"] == target_report["body"]
    assert pins["hand"] == target_report["hands"]["R"]["arrays"]
    expected = json.loads(Path(__file__).with_name("inputs.json").read_text())
    for name in ("atlas", "sections", "witnesses", "anatomyAudit"):
        assert pins[name] == expected[name], ("Changed source evidence", name)
    report = {"acceptedWearable": False, "status": "RUNNING", "sourcePins": pins,
              "recipe": pin(Path(__file__).resolve().relative_to(ROOT)),
              "geometryHelper": pin((Path(__file__).resolve().parent.parent / "glove-charts01/geometry-checks.py").relative_to(ROOT)),
              "rootHelper": pin(Path(__file__).with_name("branch-root-correspondence.py").resolve().relative_to(ROOT)),
              "nativeMaster": target_report["sourcePins"]["nativeMaster"],
              "independentProof": target_report["sourcePins"]["independentProof"],
              "bounds": {"paddingGoalM": PADDING, "minimumPaddingM": MINIMUM_PADDING,
                         "maximumRadialEase": MAX_RADIAL_EASE, "maximumPrincipalStretch": 2.5,
                         "minimumPrincipalStretch": .20, "maximumTriangleCondition": 8}, "iterations": []}
    try:
        body, hand, atlas = (dict(np.load(ROOT / paths[name])) for name in ("body", "hand", "atlas"))
        source_report = json.loads((ROOT / paths["sections"]).read_text())
        source_report["rayWitnesses"] = np.load(ROOT / paths["witnesses"])["witnesses"]
        source_report["anatomyAudit"] = json.loads((ROOT / paths["anatomyAudit"]).read_text())
        report["contours"] = []
        transform, source_cuff, digit_report, contours = target_sections(body, hand, atlas, source_report, report["contours"])
        source = atlas["vertices"]; faces = atlas["faces"]
        calibrated = np.einsum("ij,nj->ni", transform, source - source_cuff) + hand["cuffOrigin"]
        report["calibration"] = {"transform": transform.tolist(), "sourceCuff": source_cuff.tolist(),
                                 "targetCuff": hand["cuffOrigin"].tolist(), "determinant": float(np.linalg.det(transform))}
        lookup = {int(row): i for i, row in enumerate(atlas["sourcePrototypeFaceRows"])}
        rows, columns, values, targets, anchor_weight = [], [], [], [], []
        for triangle, bary, target in contours:
            assert triangle in lookup, "Contour would borrow an excluded cuff-source triangle"
            for vertex, value in zip(faces[lookup[triangle]], bary):
                rows.append(len(targets)); columns.append(vertex); values.append(value)
            targets.append(target); anchor_weight.append(40.)
        # The actual source cuff is joined to the target aperture by source loop
        # order and radius, keeping every cuff vertex and the attached feature.
        cuff_ids = atlas["cuffBoundaryVertexIds"]
        cuff_src = calibrated[cuff_ids] - hand["cuffOrigin"]
        cuff_axis = hand["cuffProximalAxis"]
        radial = normalize(cuff_src[0] - cuff_axis * np.dot(cuff_src[0], cuff_axis))
        normal = np.cross(cuff_axis, radial)
        theta = np.unwrap(np.arctan2(cuff_src @ normal, cuff_src @ radial))
        winding = np.sum(np.arctan2(np.sin(np.diff(np.r_[theta, theta[0]])), np.cos(np.diff(np.r_[theta, theta[0]])))) / (2 * np.pi)
        assert abs(abs(winding) - 1) < 1e-7, "Cuff source projection is not a full angular loop"
        target_cuff_ids = np.unique(hand["cuffBoundaryEdges"])
        target_radius = np.max(np.linalg.norm(hand["vertices"][target_cuff_ids] - hand["cuffOrigin"], axis=1))
        source_radius = np.hypot(cuff_src @ radial, cuff_src @ normal)
        cuff_ease = max(1., float(np.max((target_radius + PADDING) / source_radius)))
        assert cuff_ease <= MAX_RADIAL_EASE
        for vertex, angle, radius in zip(cuff_ids, theta, source_radius):
            rows.append(len(targets)); columns.append(vertex); values.append(1.)
            targets.append(hand["cuffOrigin"] + radius * cuff_ease * (radial * np.cos(angle) + normal * np.sin(angle)))
            anchor_weight.append(200.)
        targets = np.array(targets); anchor_weight = np.array(anchor_weight)
        anchor = coo_matrix((values, (rows, columns)), shape=(len(targets), len(source))).tocsr()
        np.savez_compressed(output / "contour-constraints.npz", row=np.array(rows), column=np.array(columns),
                            value=np.array(values), targets=targets, weights=anchor_weight, calibratedSource=calibrated)
        report["cuff"] = {"sourceWinding": float(winding), "radialEase": cuff_ease, "sourceVerticesRetained": len(cuff_ids)}
        if args.prepare_only:
            report["status"] = "NATIVE02_GEOMETRIC_ROOT_CORRESPONDENCE_PREPARED_NO_FIT"
            return
        # Source mesh edges are shared across every chart. Local rigidity carries
        # actual selected padding and cuff detail through a single global solve.
        edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
        a, b = edges.T; rest_edges = calibrated[a] - calibrated[b]
        lengths = np.linalg.norm(rest_edges, axis=1); weights = np.median(lengths) / lengths
        graph = coo_matrix((np.r_[weights, weights], (np.r_[a, b], np.r_[b, a])), shape=(len(source), len(source))).tocsr()
        laplacian = diags(np.asarray(graph.sum(1)).ravel()) - graph
        anchor_matrix = anchor.T @ diags(anchor_weight) @ anchor
        anchor_rhs = anchor.T @ (targets * anchor_weight[:, None])
        closed_vertices, closed_faces = GEOMETRY.close_planar_cuff(hand["vertices"], hand["faces"])
        current = calibrated.copy()
        for iteration in range(args.iterations):
            rotations = proper_rotations(rest_edges, current[a] - current[b], a, b, weights, len(source))
            desired_edges = np.einsum("nij,nj->ni", (rotations[a] + rotations[b]) * .5, rest_edges) * weights[:, None]
            rhs = np.zeros_like(current); np.add.at(rhs, a, desired_edges); np.add.at(rhs, b, -desired_edges)
            contacts = GEOMETRY.signed_distances(current, closed_vertices, closed_faces)
            assert not np.any(contacts["ambiguous"])
            active = contacts["signedDistance"] < PADDING
            contact_weights = active.astype(float) * 80
            contact_targets = contacts["closestPoint"] + contacts["closestNormal"] * PADDING
            candidate = spsolve(laplacian + anchor_matrix + diags(contact_weights + 1e-8),
                                rhs + anchor_rhs + contact_weights[:, None] * contact_targets + 1e-8 * calibrated)
            assert np.isfinite(candidate).all()
            maximum_step = float(np.linalg.norm(candidate - current, axis=1).max())
            step = min(1., .006 / max(maximum_step, 1e-12))
            for backtrack in range(13):
                proposed = current + step * (candidate - current)
                path_pass, path_margin = positive_orientation_path(current, proposed, faces)
                if path_pass:
                    break
                step *= .5
            assert path_pass, "No orientation-preserving optimizer step within declared backtracking bound"
            current = proposed
            report["iterations"].append({"iteration": iteration, "activeContacts": int(active.sum()),
                "minimumSignedVertexDistanceM": float(contacts["signedDistance"].min()),
                "anchorMaxResidualM": float(np.linalg.norm(anchor @ current - targets, axis=1).max()),
                "step": step, "maximumStepBeforeLimitM": maximum_step,
                "orientationPathMargin": path_margin, "orientationBacktracks": backtrack})
            if iteration % 5 == 0:
                (output / "progress.json").write_text(json.dumps(report, indent=2) + "\n")
        # Save all actual source coordinates before any qualification assertion.
        np.savez_compressed(output / "fitted-selected-exterior.npz", vertices=current, faces=faces,
                            sourceVertexRows=atlas["sourceVertexRows"], sourcePrototypeFaceRows=atlas["sourcePrototypeFaceRows"],
                            sourceDenseOriginalTriangleRows=atlas["sourceDenseOriginalTriangleRows"],
                            sourceDenseBarycentric=atlas["sourceDenseBarycentric"], sourcePrototypeCornerUV=atlas["sourcePrototypeCornerUV"])
        metrics = GEOMETRY.deformation_metrics(current, calibrated, faces)
        clearance = GEOMETRY.signed_distances(current, closed_vertices, closed_faces)
        intersections = GEOMETRY.self_intersections(current, faces)
        surface_clearance = (GEOMETRY.certify_clearance(current, faces, closed_vertices, closed_faces,
                            minimum=MINIMUM_PADDING) if clearance["signedDistance"].min() >= MINIMUM_PADDING
                            else {"qualified": False, "reason": "Vertex clearance violation before adaptive triangle assay"})
        report["completeSurfaceClearance"] = surface_clearance
        np.savez_compressed(output / "fit-witnesses.npz", **metrics,
                            vertexClearance=clearance["signedDistance"], intersectingPairs=intersections["intersectingPairs"])
        report["measurement"] = {"minimumVertexClearanceM": float(clearance["signedDistance"].min()),
            "minimumPrincipalStretch": float(metrics["principalStretches"].min()),
            "maximumPrincipalStretch": float(metrics["principalStretches"].max()),
            "maximumTriangleCondition": float(metrics["condition"].max()),
            "nonadjacentIntersectionPairs": len(intersections["intersectingPairs"]),
            "fullSelfIntersectionQualified": intersections["fullSelfIntersectionQualified"],
            "orientationQualified": True, "orientationMethod": "Analytic continuous normal-dot bound at every optimizer step from proper source calibration",
            "completeSurfaceClearanceQualified": surface_clearance["qualified"]}
        gates = {"vertexClearance": clearance["signedDistance"].min() >= MINIMUM_PADDING,
                 "completeTriangleClearance": surface_clearance["qualified"],
                 "maximumStretch": metrics["principalStretches"].max() <= 2.5,
                 "minimumStretch": metrics["principalStretches"].min() >= .20,
                 "condition": metrics["condition"].max() <= 8,
                 "intersection": len(intersections["intersectingPairs"]) == 0 and intersections["fullSelfIntersectionQualified"]}
        report["geometryGates"] = {key: bool(value) for key, value in gates.items()}
        report["status"] = ("SOURCE_EXTERIOR_GEOMETRY_PASS_UNACCEPTED_ART_AND_DENSE_TRANSFER_PENDING" if all(gates.values())
                            else "SOURCE_EXTERIOR_REJECTED_BY_GEOMETRY_GATES")
    except Exception as error:
        report["status"] = "REJECTED_BEFORE_COMPLETE_GEOMETRY_QUALIFICATION"
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        for name, path in paths.items():
            assert pins[name] == pin(path), ("Input changed during fit", name)
        report["elapsedSeconds"] = time.monotonic() - started
        (output / "fit.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({key: report[key] for key in ("status", "elapsedSeconds", "error") if key in report}))


if __name__ == "__main__":
    main()
