"""Read-only signed occupancy of the failed, exact native pinky root trials."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", required=True)
    args = parser.parse_args()
    spec = spec_from_file_location("fit_diagnostic", Path(__file__).with_name("fit-exterior.py"))
    fit = module_from_spec(spec); spec.loader.exec_module(fit)
    base = Path("docs/evidence/rider-rebuild/glove-charts01/target01")
    body = dict(np.load(ROOT / base / "native-body.npz"))
    hand = dict(np.load(ROOT / base / "native-hand-R.npz"))
    vertices, faces = fit.GEOMETRY.close_planar_cuff(hand["vertices"], hand["faces"])
    names = body["jointNames"].tolist()
    probes, labels = [], []
    for digit in fit.DIGITS:
        name = "DEF-" + ("thumb" if digit == "thumb" else "f_" + digit) + ".01.R"
        index = names.index(name)
        for fraction in ([0, .1, .2, .3, .4, .6, .8, 1] if digit == "pinky" else [0]):
            point = body["jointHeads"][index] * (1 - fraction) + body["jointTails"][index] * fraction
            probes.append(point)
            labels.append({"joint": name, "fraction": fraction, "pointNativeM": point.tolist()})
    query = fit.GEOMETRY.signed_distances(probes, vertices, faces)
    assert not np.any(query["ambiguous"])
    for index, row in enumerate(labels):
        triangle = int(query["triangleRow"][index])
        assert triangle < len(hand["faces"]), "Nearest result borrowed mathematical cuff cap"
        row.update({"signedDistanceM": float(query["signedDistance"][index]),
                    "windingNumber": float(query["windingNumber"][index]),
                    "closestPointNativeM": query["closestPoint"][index].tolist(),
                    "handTriangle": triangle, "sourceBodyTriangle": int(hand["sourceBodyTriangleRows"][triangle]),
                    "sourceBodyCornerBarycentric": hand["sourceBodyCornerBarycentric"][triangle].tolist()})
    report = {"acceptedWearable": False, "status": "PINKY_ROOT_NATIVE_BONE_EXITS_ACTUAL_HAND_VOLUME",
              "recipe": fit.pin(Path(__file__).resolve().relative_to(ROOT)),
              "body": fit.pin(base / "native-body.npz"), "hand": fit.pin(base / "native-hand-R.npz"),
              "geometryHelper": fit.pin(Path(__file__).with_name("geometry-checks.py").resolve().relative_to(ROOT)),
              "negativeIsInside": True, "probes": labels,
              "limits": ["Occupancy diagnoses the failed bone-centered roots; it does not alone label an anatomical surface branch or prescribe a corrected skeleton.",
                         "All nearest triangles are actual body surface, not mathematical cuff caps.",
                         "No rig, source fit, body geometry, coefficients or thresholds changed."]}
    (ROOT / args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "pinkySignedDistancesM": [r["signedDistanceM"] for r in labels[:8]]}))


if __name__ == "__main__":
    main()
