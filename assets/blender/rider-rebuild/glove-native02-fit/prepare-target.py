"""Refresh actual native02 geometry, rest and FULL/FOUR hand targets.

The independent saved-native proof, rather than a stale contract, is authority.
Original geometric branch evidence is reused only by original source vertex ID.
Run through the parent's serial bounded lease after a source checkpoint.
"""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


OLD = module("native02_original_target_reader", HERE.parent / "glove-charts01/prepare-target.py")
pin = OLD.pin


def named_fields(rows, names):
    lookup = {name: i for i, name in enumerate(names)}
    result = np.zeros((len(rows), len(names)), dtype=np.float64)
    for vertex, row in enumerate(rows):
        assert len({name for name, _ in row}) == len(row)
        for name, weight in row:
            assert name in lookup and np.isfinite(weight) and weight >= 0
            result[vertex, lookup[name]] = weight
    assert np.all(result.sum(1) > 0)
    return result


def canonical_faces(faces):
    return sorted(tuple(np.roll(face, -int(np.argmin(face)))) for face in faces)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    assert out.is_relative_to(ROOT / "harness/out/rider-rebuild/glove-native02-fit")
    assert not out.exists()
    inputs = json.loads((HERE / "inputs.json").read_text())
    paths = {name: ROOT / record["path"] for name, record in inputs.items()}
    for name, record in inputs.items():
        assert pin(record["path"]) == record, ("Changed input", name)
    proof = json.loads(paths["independentProof"].read_text())
    controls = json.loads(paths["controls"].read_text())
    assert controls["rigNativeSHA256"] == inputs["nativeMaster"]["sha256"]
    assert proof["native"]["sha256"] == inputs["nativeMaster"]["sha256"]
    assert proof["glb"]["sha256"] == inputs["nativeGLB"]["sha256"]
    assert proof["acceptedArt"] is False
    authority = dict(np.load(paths["nativeArrays"]))
    names = authority["jointNames"].tolist()
    assert len(names) == len(set(names)) == 75
    vertices = authority["vertices"].astype(np.float64)
    faces = authority["faces"]
    assert len(vertices) == 10582
    assert np.array_equal(authority["nativeSourceVertexIds"], np.arange(10582))
    raw_full = named_fields(json.loads(paths["nativeFull"].read_text()), names)
    raw_full_sums = raw_full.sum(1)
    # Native02 intentionally retains original outside-domain FULL JSON rows.
    # Preserve those raw coefficients and their sums before any interpolation.
    # Only this separately named target field is normalized, never the source.
    full = raw_full / raw_full_sums[:, None]
    assert np.max(abs(full.sum(1) - 1)) < 1e-12
    four = named_fields(json.loads(paths["nativeFour"].read_text()), names)
    assert np.max(abs(four.sum(1) - 1)) < 1e-12
    assert np.count_nonzero(four, axis=1).max() <= 4
    native = authority["nativeCoefficients"]
    assert np.array_equal(four.astype(np.float32), native)
    old_body = dict(np.load(paths["oldBodyGeometry"]))
    assert np.array_equal(vertices, old_body["vertices"])
    assert canonical_faces(faces) == canonical_faces(old_body["faces"])
    document, accessor = OLD.glb(paths["nativeGLB"])
    body_index = next(i for i, node in enumerate(document["nodes"]) if node.get("name") == "RiderBody")
    parents = {child: i for i, node in enumerate(document["nodes"]) for child in node.get("children", [])}
    current = body_index
    while True:
        node = document["nodes"][current]
        assert node.get("translation", [0, 0, 0]) == [0, 0, 0]
        assert node.get("rotation", [0, 0, 0, 1]) == [0, 0, 0, 1]
        assert node.get("scale", [1, 1, 1]) == [1, 1, 1]
        assert node.get("matrix", np.eye(4).ravel().tolist()) == np.eye(4).ravel().tolist()
        if current not in parents:
            break
        current = parents[current]
    node = document["nodes"][body_index]
    skin_order = [document["nodes"][i]["name"] for i in document["skins"][node["skin"]]["joints"]]
    assert len(skin_order) == 75 and set(skin_order) == set(names)
    primitives = document["meshes"][node["mesh"]]["primitives"]
    assert len(primitives) == 1
    primitive = primitives[0]
    ids_raw = accessor(primitive["attributes"]["_SOURCE_VERTEX_ID"]).ravel()
    ids = ids_raw.astype(int)
    assert np.array_equal(ids_raw, ids) and np.array_equal(np.unique(ids), np.arange(10582))
    decoded = accessor(primitive["attributes"]["POSITION"]).astype(float)[:, [0, 2, 1]] * [1, -1, 1]
    assert np.array_equal(decoded, vertices[ids])
    decoded_faces = ids[accessor(primitive["indices"]).ravel().astype(int)].reshape(-1, 3)
    assert canonical_faces(decoded_faces) == canonical_faces(faces)
    bones = {name: {"head": authority["jointHeads"][i], "tail": authority["jointTails"][i],
                    "matrix": authority["jointMatrices"][i]} for i, name in enumerate(names)}
    out.mkdir(parents=True)
    body = {**authority, "fullCoefficients": full, "fourCoefficients": four,
            "fullRawCoefficients": raw_full, "fullRawRowSums": raw_full_sums}
    np.savez_compressed(out / "native-body.npz", **body)
    hands = {}
    for side in ("R", "L"):
        hand, stats = OLD.clipped_hand(vertices, faces, native.astype(float), bones, side)
        ancestry = hand["sourceEdgeAncestry"]
        lo, hi = ancestry[:, 0].astype(int), ancestry[:, 1].astype(int)
        t = ancestry[:, 2, None]
        hand["fullCoefficients"] = full[lo] * (1 - t) + full[hi] * t
        hand["fullRawCoefficients"] = raw_full[lo] * (1 - t) + raw_full[hi] * t
        hand["fullRawRowSums"] = hand["fullRawCoefficients"].sum(1)
        hand["fourCoefficients"] = four[lo] * (1 - t) + four[hi] * t
        old_hand = dict(np.load(paths["oldHand" + side]))
        branch = dict(np.load(paths["oldBranches" + side]))
        assert np.array_equal(branch["sourceHandVertices"], old_hand["vertices"])
        assert np.array_equal(branch["sourceHandFaces"], old_hand["faces"])
        old_labels = branch["sourceHandBranchSeeds"]
        seed_source = {}
        for old_id in np.flatnonzero(old_labels >= 0):
            a, b, fraction = old_hand["sourceEdgeAncestry"][old_id]
            assert a == b and fraction == 0, "Distal seed must be an original body vertex"
            seed_source[int(a)] = int(old_labels[old_id])
        hand["sourceHandBranchSeeds"] = np.array([seed_source.get(int(a), -1) if a == b else -1
                                                    for a, b in zip(lo, hi)], dtype=np.int32)
        assert np.sum(hand["sourceHandBranchSeeds"] >= 0) == len(seed_source)
        hand["jointNames"] = np.array(names)
        for key in ("fullCoefficients", "fourCoefficients"):
            assert np.max(abs(hand[key].sum(1) - 1)) < 1e-12
        original_rows = hand["sourceBodyTriangleRows"]
        hand["sourceBodyOriginalPolygonRows"] = authority["sourcePolygonRows"][original_rows]
        hand["sourceBodyOriginalLoopRows"] = authority["sourceLoopRows"][original_rows]
        target_path = out / ("native-hand-" + side + ".npz")
        np.savez_compressed(target_path, **hand)
        hands[side] = {"arrays": pin(target_path.relative_to(ROOT)), "geometry": stats,
                       "branchSeedCounts": {digit: int(np.sum(hand["sourceHandBranchSeeds"] == i))
                                            for i, digit in enumerate(("pinky", "ring", "middle", "index", "thumb"))}}
    for name, record in inputs.items():
        assert pin(record["path"]) == record, ("Input changed during extraction", name)
    report = {"acceptedWearable": False, "status": "ACTUAL_NATIVE02_TARGET_EXTRACTION_ONLY",
              "recipe": pin(Path(__file__).resolve().relative_to(ROOT)), "sourcePins": inputs,
              "body": pin((out / "native-body.npz").relative_to(ROOT)), "hands": hands,
              "skinJointOrder": skin_order, "namedNativeJointOrder": names,
              "nativeGeometryAndRestExact": True, "nativeFULLAndFOURRefreshed": True,
              "fullTargetNormalization": {"rawNativeCoefficientsAndRowSumsRetained": True,
                  "method": "Divide each raw named FULL row by its positive sum before target edge interpolation",
                  "rawRowSumMaximumResidualFromOne": float(np.max(abs(raw_full_sums - 1))),
                  "rawRowSumMinimum": float(raw_full_sums.min()), "rawRowSumMaximum": float(raw_full_sums.max()),
                  "normalizedTargetRowSumMaximumResidual": float(np.max(abs(full.sum(1) - 1))),
                  "nativeMasterAndSourceJSONModified": False},
              "geometricBranchAuthority": "Unchanged original mesh connectivity; labels transported by original source vertex ID",
              "limits": ["No glove deformation, appearance, ranges or played art acceptance.",
                         "FOUR fields are native float32 authority; raw FULL, raw sums and explicitly normalized FULL target fields are retained separately.",
                         "Clipped coefficients interpolate source edges; no silent four-slot reduction at the cuff.",
                         "Geometric branch roots and source web transitions must be derived in correspondence preparation."]}
    (out / "target-extraction.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "hands": {side: row["branchSeedCounts"] for side, row in hands.items()}}))


if __name__ == "__main__":
    main()
