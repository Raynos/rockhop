"""Local source-section medial centers for the four proven hand defects.

No body projection, joint-root range extension, native edit or field mutation.
The measured station remains explicit; played anatomical acceptance is separate.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import Voronoi

from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parents[4]


def load(name, file):
    spec = spec_from_file_location(name, Path(__file__).with_name(file))
    value = module_from_spec(spec); spec.loader.exec_module(value)
    return value


def inside_polygon(points, polygon):
    first, second = polygon, np.roll(polygon, -1, axis=0)
    result = []
    for point in points:
        crossing = (first[:, 1] > point[1]) != (second[:, 1] > point[1])
        denominator = second[:, 1] - first[:, 1]
        x = first[:, 0] + (point[1] - first[:, 1]) * (second[:, 0] - first[:, 0]) / np.where(denominator != 0, denominator, 1)
        result.append(bool(np.count_nonzero(crossing & (x > point[0])) % 2))
    return np.array(result)


def medial_candidates(polygon, old_point, center, axis):
    radial = np.array([1., 0, 0]); radial -= axis * np.dot(radial, axis); radial /= np.linalg.norm(radial)
    frame = np.column_stack([radial, np.cross(axis, radial)])
    poly = np.einsum("ni,ij->nj", polygon - center, frame)
    edges = np.roll(poly, -1, axis=0) - poly; lengths = np.linalg.norm(edges, axis=1)
    total = lengths.sum(); starts = np.r_[0, np.cumsum(lengths)]
    samples = []
    for station in np.linspace(0, total, 512, endpoint=False):
        row = int(np.searchsorted(starts, station, side="right") - 1)
        samples.append(poly[row] + edges[row] * ((station - starts[row]) / lengths[row]))
    samples = np.array(samples); voronoi = Voronoi(samples)
    centers = voronoi.vertices[inside_polygon(voronoi.vertices, poly)]
    records = []
    for candidate in centers:
        t = np.clip(np.sum((candidate - poly) * edges, axis=1) / lengths**2, 0, 1)
        nearest = poly + edges * t[:, None]
        distances = np.linalg.norm(nearest - candidate, axis=1)
        radius = float(distances.min())
        support = nearest[distances <= radius + total / 512]
        angles = np.sort(np.arctan2(support[:, 1] - candidate[1], support[:, 0] - candidate[0]))
        gap = float(np.max(np.diff(np.r_[angles, angles[0] + 2 * np.pi])))
        xyz = center + frame @ candidate
        # Opposing support distinguishes a medial interior center from a tiny
        # near-corner Voronoi vertex. No nearest-skin under-offset is used.
        if gap <= np.pi + .03:
            records.append({"point": xyz.tolist(), "inscribedSectionRadiusM": radius,
                "opposingSupportMaximumAngularGapRadians": gap,
                "distanceFromOldJointM": float(np.linalg.norm(xyz - old_point))})
    assert records, "No source-supported opposing medial candidate"
    records.sort(key=lambda row: row["distanceFromOldJointM"])
    return records, frame


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", required=True)
    args = parser.parse_args(); out = ROOT / args.out; out.mkdir(parents=True, exist_ok=False)
    fit = load("fit_correction", "fit-exterior.py"); anatomy_tool = load("anatomy_correction", "audit-hand-anatomy.py")
    base = Path("docs/evidence/rider-rebuild/glove-charts01")
    body_path = base / "target01/native-body.npz"; audit_path = base / "anatomy-audit01/anatomy-audit.json"
    body = dict(np.load(ROOT / body_path)); names = body["jointNames"].tolist()
    audit = json.loads((ROOT / audit_path).read_text())
    corrected_heads = body["jointHeads"].copy(); corrected_tails = body["jointTails"].copy()
    report = {"acceptedAnatomy": False, "status": "LOCAL_SECTION_MEDIAL_CORRECTION_PROPOSAL",
        "recipe": fit.pin(Path(__file__).resolve().relative_to(ROOT)), "body": fit.pin(body_path),
        "anatomyAudit": fit.pin(audit_path), "corrections": [], "postCorrectionSegments": [], "palmNormals": {}}
    for side in ("R", "L"):
        hand_path = base / ("target01/native-hand-" + side + ".npz")
        hand = dict(np.load(ROOT / hand_path)); hv, hf = fit.GEOMETRY.close_planar_cuff(hand["vertices"], hand["faces"])
        seeds = np.load(ROOT / audit["sides"][side]["output"]["path"])["sourceHandBranchSeeds"]
        palm = hand["vertices"][seeds < 0]; delta = palm - palm.mean(0)
        _, eigenvectors = np.linalg.eigh(np.einsum("ni,nj->ij", delta, delta))
        normal = eigenvectors[:, 0]; normal *= np.sign(normal[0]) * (1 if side == "R" else -1)
        report["palmNormals"][side] = normal.tolist()
        for digit, joint in (("pinky", "DEF-f_pinky.01." + side), ("middle", "DEF-f_middle.02." + side)):
            k = names.index(joint); old = body["jointHeads"][k]
            axis = np.array(audit["sides"][side]["branches"][digit]["surfacePCAAxis"])
            contours = anatomy_tool.all_contours(hand["vertices"], hand["faces"], old, axis)
            contour = min(contours, key=lambda row: np.linalg.norm(row["polygon"] - old, axis=1).min())
            candidates, frame = medial_candidates(contour["polygon"], old, old, axis)
            # Local medial proposals must also be inside the actual 3D tissue.
            query = fit.GEOMETRY.signed_distances([row["point"] for row in candidates], hv, hf)
            for index, row in enumerate(candidates):
                row["signedDistanceM"] = float(query["signedDistance"][index])
                row["threeDimensionalInside"] = bool(query["signedDistance"][index] < 0 and not query["ambiguous"][index])
            selected = next(row for row in candidates if row["threeDimensionalInside"])
            point = np.array(selected["point"]); corrected_heads[k] = point
            parent = "DEF-palm.04." + side if digit == "pinky" else "DEF-f_middle.01." + side
            corrected_tails[names.index(parent)] = point
            contour.pop("polygon"); contour["centroid"] = contour["centroid"].tolist()
            report["corrections"].append({"joint": joint, "parentEndpoint": parent + "/tail", "oldPoint": old.tolist(),
                "sourceStationPlaneOrigin": old.tolist(), "sourceStationPlaneAxis": axis.tolist(),
                "sourceFrame": frame.tolist(), "sourceContour": contour, "selected": selected,
                "allMedialCandidates": candidates,
                "stationQualification": "Actual local skin section at the prior axial station; proximal extrapolation forbidden. Final knuckle/crease station remains a moving-art qualification."})
        for digit in fit.DIGITS:
            for segment in (1, 2, 3):
                name = "DEF-" + ("thumb" if digit == "thumb" else "f_" + digit) + ".%02d." % segment + side
                k = names.index(name); t = np.linspace(0, 1, 65)
                points = corrected_heads[k] * (1 - t[:, None]) + corrected_tails[k] * t[:, None]
                query = fit.GEOMETRY.signed_distances(points, hv, hf)
                assert not query["ambiguous"].any()
                report["postCorrectionSegments"].append({"joint": name, "fractions": t.tolist(),
                    "signedDistanceM": query["signedDistance"].tolist(), "outsideCount": int(np.sum(query["signedDistance"] >= 0)),
                    "minimumInsideClearanceM": float(-query["signedDistance"].max())})
    arrays_path = out / "proposed-joints.npz"
    np.savez_compressed(arrays_path, jointNames=body["jointNames"], heads=corrected_heads, tails=corrected_tails,
                        originalHeads=body["jointHeads"], originalTails=body["jointTails"])
    report["proposedJoints"] = fit.pin(arrays_path.relative_to(ROOT))
    report["all1950SegmentSamplesInside"] = all(row["outsideCount"] == 0 for row in report["postCorrectionSegments"])
    report["limits"] = ["No native rig or body/field mutation; corrected positions remain a source-supported derivative proposal.",
        "Medial support is measured from actual local contours, not nearest-surface projection or a distal centerline extrapolation.",
        "65 samples per segment are finite; continuous incident-segment tissue occupancy still requires its own bounded certificate.",
        "Static section support does not certify anatomical knuckle station, roll or motion; played individual curl/grip/opposition remains required."]
    (out / "medial-correction.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "all1950Inside": report["all1950SegmentSamplesInside"],
        "corrections": [{"joint": row["joint"], **row["selected"]} for row in report["corrections"]],
        "outside": [row["joint"] for row in report["postCorrectionSegments"] if row["outsideCount"]]}))


if __name__ == "__main__":
    main()
