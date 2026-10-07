"""Independent source-pinned verification of the proposed four medial centers."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "docs/evidence/rider-rebuild/glove-charts01"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source = BASE / "medial-correction01/medial-correction.json"
    report = json.loads(source.read_text())
    for key in ("recipe", "body", "anatomyAudit", "proposedJoints"):
        pin = report[key]
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"], key
    body = dict(np.load(BASE / "target01/native-body.npz"))
    proposed = dict(np.load(ROOT / report["proposedJoints"]["path"]))
    assert np.array_equal(body["jointNames"], proposed["jointNames"])
    assert np.array_equal(body["jointHeads"], proposed["originalHeads"])
    assert np.array_equal(body["jointTails"], proposed["originalTails"])
    names = body["jointNames"].tolist()
    changed_heads = [names[k] for k in np.flatnonzero(np.any(proposed["heads"] != body["jointHeads"], axis=1))]
    changed_tails = [names[k] for k in np.flatnonzero(np.any(proposed["tails"] != body["jointTails"], axis=1))]
    assert set(changed_heads) == {"DEF-" + stem + "." + side for side in ("L", "R") for stem in ("f_pinky.01", "f_middle.02")}
    assert set(changed_tails) == {"DEF-" + stem + "." + side for side in ("L", "R") for stem in ("palm.04", "f_middle.01")}
    for row in report["corrections"]:
        head = proposed["heads"][names.index(row["joint"])]
        tail = proposed["tails"][names.index(row["parentEndpoint"].split("/")[0])]
        assert np.array_equal(head, tail)
        assert np.array_equal(head, row["selected"]["point"])
        axis = np.array(row["sourceStationPlaneAxis"])
        assert abs(np.dot(head - row["oldPoint"], axis)) < 1e-12
    spec = importlib.util.spec_from_file_location("correction_checks", Path(__file__).with_name("geometry-checks.py"))
    geometry = importlib.util.module_from_spec(spec); spec.loader.exec_module(geometry)
    segments = []
    for side in ("R", "L"):
        hand = dict(np.load(BASE / ("target01/native-hand-" + side + ".npz")))
        vertices, faces = geometry.close_planar_cuff(hand["vertices"], hand["faces"])
        for row in report["postCorrectionSegments"]:
            if not row["joint"].endswith("." + side):
                continue
            k = names.index(row["joint"])
            head, tail = proposed["heads"][k], proposed["tails"][k]
            fractions = np.linspace(0, 1, 65)
            points = head + fractions[:, None] * (tail - head)
            query = geometry.signed_distances(points, vertices, faces)
            assert not query["ambiguous"].any()
            assert np.all(query["signedDistance"] < 0)
            assert np.max(abs(query["signedDistance"] - row["signedDistanceM"])) < 1e-12
            # Unsigned surface distance is 1-Lipschitz. Every point on this
            # segment is at most half one sample interval from an inside
            # sample. A positive bound excludes every intervening crossing.
            half_interval = float(np.linalg.norm(tail - head) / 128)
            bound = float(-query["signedDistance"].max() - half_interval)
            assert bound > 0, (row["joint"], bound)
            segments.append({"joint": row["joint"], "sampleCount": 65,
                "minimumSampledClearanceM": float(-query["signedDistance"].max()),
                "maximumDistanceToSampleM": half_interval,
                "continuousSegmentClearanceLowerBoundM": bound})
    result = {"acceptedArt": False, "qualifiedStaticSegmentContainment": True,
        "sourceSHA256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "changedHeads": changed_heads, "changedTails": changed_tails,
        "sampleCount": 1950, "segments": segments,
        "minimumContinuousClearanceLowerBoundM": min(row["continuousSegmentClearanceLowerBoundM"] for row in segments),
        "limits": ["Certificate covers the 30 straight phalanx segments in the frozen skin volume; it does not certify new skinning or motion.",
            "Pinky MCP and middle PIP source-supported medial centers retain their prior axial stations. Anatomical station and flexion require review.",
            "No native rig, fields, body geometry, glove candidate or player asset has been modified."]}
    assert len(segments) == 30
    (ROOT / args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"qualified": True, "segments": len(segments), "samples": 1950,
        "continuousClearanceLowerBoundM": result["minimumContinuousClearanceLowerBoundM"]}))


if __name__ == "__main__":
    main()
