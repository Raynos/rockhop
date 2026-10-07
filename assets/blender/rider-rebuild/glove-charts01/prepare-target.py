"""Extract the frozen native hand from GLB source IDs and named native FOUR.

The exported skin order supplies joint identity only; its normalized/truncated
weights are deliberately not the native coefficient authority.
"""
import argparse
import json
from pathlib import Path
import struct

import numpy as np

from importlib.util import module_from_spec, spec_from_file_location
_spec = spec_from_file_location("source_measure", Path(__file__).with_name("measure-source.py"))
_source = module_from_spec(_spec)
_spec.loader.exec_module(_source)
ROOT, pin, topology = _source.ROOT, _source.pin, _source.topology


def glb(path):
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw)
    size, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4E4F534A
    document = json.loads(raw[20:20 + size])
    offset = 20 + size
    size, kind = struct.unpack_from("<II", raw, offset)
    assert kind == 0x004E4942
    binary = raw[offset + 8:offset + 8 + size]

    def accessor(index):
        record = document["accessors"][index]
        assert "sparse" not in record and not record.get("normalized", False)
        view = document["bufferViews"][record["bufferView"]]
        dtype = np.dtype({5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2",
                          5125: "<u4", 5126: "<f4"}[record["componentType"]])
        width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[record["type"]]
        offset = view.get("byteOffset", 0) + record.get("byteOffset", 0)
        stride = view.get("byteStride", width * dtype.itemsize)
        return np.ndarray((record["count"], width), dtype=dtype, buffer=binary,
                          offset=offset, strides=(stride, dtype.itemsize)).copy()
    return document, accessor


def clipped_hand(vertices, faces, fields, bones, side):
    """Exact plane clip with shared source-edge ancestry, then connectivity."""
    wrist = np.array(bones["DEF-hand." + side]["head"])
    proximal = np.array(bones["DEF-forearm." + side]["head"]) - wrist
    proximal /= np.linalg.norm(proximal)
    cuff = wrist + proximal * .028
    signed = np.sum((vertices - cuff) * proximal, axis=1)
    points = list(vertices)
    coefficients = list(fields)
    ancestry = [(index, index, 0.) for index in range(len(vertices))]
    intersections, clipped, parent_faces, parent_bary = {}, [], [], []
    for row, triangle in enumerate(faces):
        if signed[triangle].min() > 0:
            continue
        polygon = []
        for j in range(3):
            a, b = int(triangle[j]), int(triangle[(j + 1) % 3])
            if signed[a] <= 0:
                bary = np.zeros(3); bary[j] = 1
                polygon.append((a, bary))
            if signed[a] * signed[b] < 0:
                lo, hi = sorted((a, b))
                key = (lo, hi)
                fraction = float(signed[lo] / (signed[lo] - signed[hi]))
                if key not in intersections:
                    intersections[key] = len(points)
                    points.append(vertices[lo] * (1 - fraction) + vertices[hi] * fraction)
                    coefficients.append(fields[lo] * (1 - fraction) + fields[hi] * fraction)
                    ancestry.append((lo, hi, fraction))
                bary = np.zeros(3)
                bary[np.flatnonzero(triangle == lo)[0]] = 1 - fraction
                bary[np.flatnonzero(triangle == hi)[0]] = fraction
                polygon.append((intersections[key], bary))
        for j in range(1, len(polygon) - 1):
            tri = [polygon[0], polygon[j], polygon[j + 1]]
            clipped.append([x[0] for x in tri])
            parent_faces.append(row)
            parent_bary.append([x[1] for x in tri])
    points, clipped = np.array(points), np.array(clipped, dtype=np.int32)
    used = np.unique(clipped)
    adjacency = [[] for _ in points]
    for triangle in clipped:
        for a, b in zip(triangle, np.roll(triangle, -1)):
            adjacency[a].append(int(b)); adjacency[b].append(int(a))
    tip = np.array(bones["DEF-f_middle.03." + side]["tail"])
    seed = int(used[np.argmin(np.linalg.norm(points[used] - tip, axis=1))])
    keep, todo = set(), [seed]
    while todo:
        index = todo.pop()
        if index in keep:
            continue
        keep.add(index); todo.extend(adjacency[index])
    keep = np.array(sorted(keep))
    mask = np.all(np.isin(clipped, keep), axis=1)
    mapping = np.full(len(points), -1, dtype=np.int32); mapping[keep] = np.arange(len(keep))
    p, f = points[keep], mapping[clipped[mask]]
    assert np.linalg.norm(p - wrist, axis=1).max() < .29
    result = {"vertices": p, "faces": f, "nativeCoefficients": np.array(coefficients)[keep],
              "sourceEdgeAncestry": np.array(ancestry)[keep],
              "sourceBodyTriangleRows": np.array(parent_faces)[mask],
              "sourceBodyCornerBarycentric": np.array(parent_bary)[mask],
              "cuffOrigin": cuff, "cuffProximalAxis": proximal}
    stats = topology(p, f)
    assert stats["euler"] == 1 and stats["nonmanifoldEdges"] == stats["boundaryDegreeNotTwo"] == 0
    edge_counts = {}
    for triangle in f:
        for a, b in zip(triangle, np.roll(triangle, -1)):
            key = tuple(sorted((int(a), int(b)))); edge_counts[key] = edge_counts.get(key, 0) + 1
    boundary = np.array([key for key, count in edge_counts.items() if count == 1])
    ids = np.unique(boundary)
    aperture_error = float(np.max(np.abs(np.sum((p[ids] - cuff) * proximal, axis=1))))
    assert aperture_error < 1e-12
    result["cuffBoundaryEdges"] = boundary
    # Check every retained triangle corner reconstructs its original body face.
    reconstructed = np.einsum("ijk,ikl->ijl", result["sourceBodyCornerBarycentric"],
                              vertices[faces[result["sourceBodyTriangleRows"]]])
    error = float(np.max(np.linalg.norm(reconstructed - p[f], axis=2)))
    assert error < 1e-12
    stats.update({"sourceCornerReconstructionMaxM": error, "aperturePlaneMaxResidualM": aperture_error,
                  "wrist": wrist.tolist(), "cuffOffsetM": .028,
                  "coefficientSumMaxResidual": float(np.max(abs(result["nativeCoefficients"].sum(1) - 1))),
                  "maximumInterpolatedInfluences": int(np.count_nonzero(result["nativeCoefficients"], axis=1).max())})
    return result, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = ROOT / args.out; output.mkdir(parents=True, exist_ok=True)
    base = Path("harness/out/rider-rebuild/construction01")
    paths = {"glb": base / "combined04/rider.glb", "contract": base / "combined04/rider-contract.json",
             "nativeWeights": base / "rig04/weights-four.json", "originalRest": base / "rig04/joint-rest.json"}
    pins = {name: pin(path) for name, path in paths.items()}
    assert pins["glb"]["sha256"] == "58677cc37aff6b22bb98144762eb5a93dfe689ac207ea0b74a214ba60538f6fc"
    document, accessor = glb(ROOT / paths["glb"])
    contract = json.loads((ROOT / paths["contract"]).read_text())
    native = json.loads((ROOT / paths["nativeWeights"]).read_text())
    original = {row["name"]: row for row in json.loads((ROOT / paths["originalRest"]).read_text())["bones"]}
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
    primitives = document["meshes"][node["mesh"]]["primitives"]
    assert len(primitives) == 1
    primitive = primitives[0]
    source_ids_raw = accessor(primitive["attributes"]["_SOURCE_VERTEX_ID"]).ravel()
    source_ids = source_ids_raw.astype(np.int32)
    assert np.array_equal(source_ids, source_ids_raw)
    position = accessor(primitive["attributes"]["POSITION"]).astype(np.float64)
    position = position[:, [0, 2, 1]] * np.array([1, -1, 1])
    assert len(native) == 10582 and np.array_equal(np.unique(source_ids), np.arange(len(native)))
    vertices = np.zeros((len(native), 3))
    vertices[source_ids] = position
    assert np.array_equal(vertices[source_ids], position)
    faces = source_ids[accessor(primitive["indices"]).ravel()].reshape(-1, 3)
    order = [document["nodes"][index]["name"] for index in document["skins"][node["skin"]]["joints"]]
    assert len(order) == 75 and len(set(order)) == 75
    lookup = {name: i for i, name in enumerate(order)}
    coefficients = np.zeros((len(native), len(order)))
    for index, row in enumerate(native):
        assert len(row) <= 4
        for name, weight in row:
            assert name in lookup
            coefficients[index, lookup[name]] = weight
    assert np.max(abs(coefficients.sum(1) - 1)) < 1e-12
    bones = {row["name"]: row for row in contract["nativeRest"]["bones"]}
    assert set(bones) == set(order)
    checks = []
    for name in order:
        if not name.startswith(("DEF-hand", "DEF-forearm", "DEF-palm", "DEF-thumb", "DEF-f_")):
            continue
        delta = {key: float(np.max(abs(np.array(bones[name][key]) - original[name][key])))
                 for key in ("head", "tail", "matrix")}
        assert delta["head"] < 1e-7 and delta["tail"] < 1e-7 and delta["matrix"] < 1e-6
        checks.append({"name": name, "absoluteResiduals": delta})
    body_path = output / "native-body.npz"
    np.savez_compressed(body_path, vertices=vertices, faces=faces, nativeCoefficients=coefficients,
                        jointNames=np.array(order), jointHeads=np.array([bones[name]["head"] for name in order]),
                        jointTails=np.array([bones[name]["tail"] for name in order]),
                        jointMatrices=np.array([bones[name]["matrix"] for name in order]))
    hands = {}
    for side in ("R", "L"):
        arrays, stats = clipped_hand(vertices, faces, coefficients, bones, side)
        path = output / ("native-hand-" + side + ".npz")
        np.savez_compressed(path, **arrays, jointNames=np.array(order))
        hands[side] = {"output": pin(path.relative_to(ROOT)), "measurements": stats}
    for name, path in paths.items():
        assert pins[name] == pin(path)
    report = {"acceptedWearable": False, "status": "EXACT_NATIVE_TARGET_EXTRACTION_ONLY", "sourcePins": pins,
              "recipe": pin(Path(__file__).resolve().relative_to(ROOT)), "body": pin(body_path.relative_to(ROOT)),
              "nativeVertexCount": len(vertices), "exportedVertexCount": len(position),
              "duplicatePositionResidualM": 0, "allSourceIDsCovered": True,
              "nativeWeightAuthority": "rig04/weights-four.json; exported normalized/truncated weights unused",
              "skinJointOrder": order, "handRestChecks": checks, "hands": hands,
              "limits": ["Original rig04 has 404 control/deformation bones; contract and GLB select the same 75 exported joint names.",
                         "Hand rest comparison includes native float reconstruction residuals, not byte equality of JSON coordinates.",
                         "Clipped seam coefficients interpolate exact native FOUR and can have more than four influences; no silent truncation.",
                         "This is a body reference and future inner-cavity reference only, never the glove exterior."]}
    (output / "target-extraction.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "nativeVertices": len(vertices), "hands":
                      {side: row["measurements"] for side, row in hands.items()}}))


if __name__ == "__main__":
    main()
