"""Independent readback of native identity, source atlas coverage and ancestry."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]


def check_pin(record):
    assert hashlib.sha256((ROOT / record["path"]).read_bytes()).hexdigest() == record["sha256"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True); parser.add_argument("--atlas", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    target = json.loads((ROOT / args.target).read_text())
    atlas = json.loads((ROOT / args.atlas).read_text())
    for report in (target, atlas):
        check_pin(report["recipe"])
        for record in report["sourcePins"].values():
            check_pin(record)
    check_pin(target["body"]); check_pin(atlas["output"])
    body = dict(np.load(ROOT / target["body"]["path"]))
    original_weights = json.loads((ROOT / target["sourcePins"]["nativeWeights"]["path"]).read_text())
    joint_names = body["jointNames"].tolist()
    for i, row in enumerate(original_weights):
        actual = {joint_names[j]: float(value) for j, value in enumerate(body["nativeCoefficients"][i]) if value}
        assert actual == dict(row)
    assert len(body["vertices"]) == 10582 and len(joint_names) == 75
    hands = {}
    for side, record in target["hands"].items():
        check_pin(record["output"])
        hand = dict(np.load(ROOT / record["output"]["path"]))
        edge = hand["sourceEdgeAncestry"]
        a, b, t = edge[:, 0].astype(int), edge[:, 1].astype(int), edge[:, 2, None]
        assert np.max(abs(body["vertices"][a] * (1 - t) + body["vertices"][b] * t - hand["vertices"])) < 1e-15
        assert np.array_equal(body["nativeCoefficients"][a] * (1 - t) + body["nativeCoefficients"][b] * t,
                              hand["nativeCoefficients"])
        edges = hand["cuffBoundaryEdges"]
        adjacency = {}
        for a, b in edges:
            adjacency.setdefault(int(a), []).append(int(b)); adjacency.setdefault(int(b), []).append(int(a))
        assert all(len(row) == 2 for row in adjacency.values())
        seen, todo = set(), [int(edges[0, 0])]
        while todo:
            vertex = todo.pop()
            if vertex in seen:
                continue
            seen.add(vertex); todo.extend(adjacency[vertex])
        assert seen == set(adjacency)
        digit_counts = {}
        for digit in ("pinky", "ring", "middle", "index", "thumb"):
            for segment in (1, 2, 3):
                name = "DEF-" + ("thumb" if digit == "thumb" else "f_" + digit) + ".%02d." % segment + side
                count = int(np.sum(hand["nativeCoefficients"][:, joint_names.index(name)] > 0))
                assert count > 0
                digit_counts[name] = count
        hands[side] = {"cuffLoops": 1, "exactNativeInterpolatedCoefficients": True,
                       "all15SegmentVertexCounts": digit_counts}
    prepared = dict(np.load(ROOT / atlas["output"]["path"]))
    original = dict(np.load(ROOT / atlas["sourcePins"]["source"]["path"]))
    assert np.array_equal(prepared["vertices"], original["vertices"][prepared["sourceVertexRows"]])
    assert np.array_equal(prepared["sourceVertexRows"][prepared["faces"]], original["faces"])
    assert np.array_equal(prepared["sourcePrototypeCornerUV"], original["cornerUVPrototype"])
    assert np.array_equal(prepared["sourceDenseOriginalTriangleRows"], original["originalTriangleRows"][prepared["sourceVertexRows"]])
    assert np.array_equal(prepared["sourceDenseBarycentric"], original["barycentric"][prepared["sourceVertexRows"]])
    assert len(prepared["faceChart"]) == len(prepared["faces"]) == 14543
    assert prepared["faceChart"].min() >= 0 and prepared["faceChart"].max() < len(prepared["chartNames"])
    mixed = np.ptp(prepared["sourceBranchLabels"][prepared["faces"]], axis=1) > 0
    assert int(mixed.sum()) == 427
    assert all("_collar" in prepared["chartNames"][index] for index in prepared["faceChart"][mixed])
    errors = {}
    for digit in ("pinky", "ring", "middle", "index", "thumb"):
        read = lambda key: prepared[digit + "_" + key]
        segment, u = read("segment"), read("segmentParameter")[:, None]
        centers = read("centers")
        p = centers[segment] * (1 - u) + centers[segment + 1] * u
        angle, radius = read("angleRadians"), read("radiusSourceUnits")
        reconstructed = p + read("radial")[segment] * (radius * np.cos(angle))[:, None]
        reconstructed += read("normal")[segment] * (radius * np.sin(angle))[:, None]
        reconstructed += read("tangents")[segment] * read("axialResidualSourceUnits")[:, None]
        error = float(np.max(np.linalg.norm(reconstructed - prepared["vertices"], axis=1)))
        assert error < 1e-12
        errors[digit] = error
    report = {"acceptedWearable": False, "status": "PREPARATION_READBACK_PASS_NO_FIT",
              "nativeCoefficientsExactlyEqualNamedSource": True, "allSourceVerticesFacesCornerUVAncestryExact": True,
              "mixedPalmDigitTrianglesRetained": int(mixed.sum()), "hands": hands,
              "digitCoordinateReconstructionMaxSourceUnits": errors,
              "limits": ["No source deformation, appearance bake, native garment or played acceptance.",
                         "Exact source chart ownership is not a target correspondence or fit qualification."]}
    (ROOT / args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "nativeWeightsExact": True, "sourceAncestryExact": True,
                      "cuffLoopsEachHand": 1, "all15SegmentsEachHand": True, "retainedMixedTriangles": int(mixed.sum())}))


if __name__ == "__main__":
    main()
