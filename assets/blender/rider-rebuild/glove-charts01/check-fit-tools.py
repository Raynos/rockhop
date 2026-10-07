"""Bounded analytic and actual-target checks before the source fit experiment."""
import argparse
import json
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

import numpy as np

ROOT = Path(__file__).resolve().parents[4]


def load(name, filename):
    spec = spec_from_file_location(name, Path(__file__).with_name(filename))
    value = module_from_spec(spec); spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", required=True)
    args = parser.parse_args()
    geometry = load("geometry_smoke", "geometry-checks.py")
    fit = load("fit_smoke", "fit-exterior.py")
    v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    f = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])
    signed = geometry.signed_distances([[.1, .1, .1], [2, 2, 2], [0, 0, 0]], v, f)
    assert signed["signedDistance"][0] < 0 < signed["signedDistance"][1]
    assert signed["signedDistance"][2] == 0 and not signed["ambiguous"].any()
    rotation = np.array([[0., -1, 0], [1, 0, 0], [0, 0, 1]])
    metrics = geometry.deformation_metrics(2 * (v @ rotation.T), v, f,
                                            np.repeat(rotation[None], len(f), axis=0))
    assert np.allclose(metrics["principalStretches"], 2) and np.all(metrics["orientationDot"] > 0)
    assert not len(geometry.self_intersections(v, f)["intersectingPairs"])
    edge = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, -1, 0], [.3, .8, 0]], float)
    assert not geometry._shared_simplex_overlap(edge, np.array([0, 1, 2]), np.array([1, 0, 3]), np.array([0, 1]), 1e-10)
    assert geometry._shared_simplex_overlap(edge, np.array([0, 1, 2]), np.array([0, 1, 4]), np.array([0, 1]), 1e-10)
    vertex = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, -1, 0], [1, 1, 1], [1, 1, -1]], float)
    assert not geometry._shared_simplex_overlap(vertex, np.array([0, 1, 2]), np.array([0, 3, 4]), np.array([0]), 1e-10)
    assert geometry._shared_simplex_overlap(vertex, np.array([0, 1, 2]), np.array([0, 5, 6]), np.array([0]), 1e-10)
    clear = geometry.certify_clearance([[3, 0, 0], [3, .1, 0], [3, 0, .1]], [[0, 1, 2]], v, f, minimum=.1)
    assert clear["qualified"]
    bad = geometry.certify_clearance([[.1, .1, .1], [.2, .1, .1], [.1, .2, .1]], [[0, 1, 2]], v, f, minimum=.01)
    assert not bad["qualified"] and bad["failures"]
    triangle = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], float)
    assert fit.positive_orientation_path(triangle, triangle * 2, np.array([[0, 1, 2]]))[0]
    assert not fit.positive_orientation_path(triangle, triangle[[0, 2, 1]], np.array([[0, 1, 2]]))[0]
    hands = {}
    for side in ("L", "R"):
        path = ROOT / ("docs/evidence/rider-rebuild/glove-charts01/target01/native-hand-" + side + ".npz")
        hand = dict(np.load(path)); hv, hf = geometry.close_planar_cuff(hand["vertices"], hand["faces"])
        rows = np.linspace(0, len(hand["faces"]) - 1, 30, dtype=int)
        tri = hv[hf[rows]]; center = tri.mean(1)
        normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); normal /= np.linalg.norm(normal, axis=1)[:, None]
        outside = geometry.signed_distances(center + normal * 1e-7, hv, hf)
        inside = geometry.signed_distances(center - normal * 1e-7, hv, hf)
        assert np.all(outside["signedDistance"] > 0) and np.all(inside["signedDistance"] < 0)
        assert not (outside["ambiguous"].any() or inside["ambiguous"].any())
        hands[side] = {"signedOffsetPairs": 30, "offsetM": 1e-7, "closedMathematicalTriangles": len(hf), "pass": True}
    report = {"acceptedWearable": False, "status": "FIT_TOOL_SMOKE_PASS_NO_FIT_EXECUTED",
              "recipe": fit.pin(Path(__file__).resolve().relative_to(ROOT)),
              "fitRecipe": fit.pin(Path(__file__).with_name("fit-exterior.py").resolve().relative_to(ROOT)),
              "geometryHelper": fit.pin(Path(__file__).with_name("geometry-checks.py").resolve().relative_to(ROOT)),
              "tests": ["exhaustive closest/winding tetra inside outside boundary", "proper rotation and doubled principal stretch",
                        "tetra full adjacent/nonadjacent intersection", "shared edge valid versus fold", "shared vertex disjoint versus crossing",
                        "whole-triangle clearance pass versus violation", "analytic continuous orientation pass versus inversion"],
              "actualHands": hands, "limits": ["No selected exterior fit or complete fitted geometry qualification has executed."]}
    (ROOT / args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "analyticTestFamilies": len(report["tests"]), "actualHandSignedPairs": 60}))


if __name__ == "__main__":
    main()
