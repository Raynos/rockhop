"""Read the selected glove's actual contours; never construct an offset hand.

NumPy only, with exact edge/triangle identities for every section and ray hit.
This source-only assay does not qualify fit, material transfer, or appearance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PREP = Path("assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data")
OLD = Path("docs/evidence/hero-remaster/finish-2026-10-05/wardrobe")


def pin(path):
    path = Path(path)
    return {"path": str(path), "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def cross2(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def section(vertices, faces, center, tangent):
    """Intersect complete source triangles, joining by source edge identity."""
    tangent = tangent / np.linalg.norm(tangent)
    radial = np.array([1., 0., 0.])
    radial -= tangent * np.dot(tangent, radial)
    radial /= np.linalg.norm(radial)
    frame = np.column_stack([radial, np.cross(tangent, radial)])
    # Explicit reduction avoids the host BLAS matmul warning observed in assay01.
    signed = np.sum((vertices - center) * tangent, axis=1)
    assert np.isfinite(signed).all()
    cut = np.flatnonzero((signed[faces].min(1) < 0) & (signed[faces].max(1) > 0))
    nodes, positions, segments, triangle_rows, edge_ids, edge_t = {}, [], [], [], [], []
    for face_row in cut:
        face = faces[face_row]
        ends = []
        for j, k in ((0, 1), (1, 2), (2, 0)):
            a, b = sorted((int(face[j]), int(face[k])))
            if signed[a] * signed[b] >= 0:
                continue
            key = (a, b)
            if key not in nodes:
                nodes[key] = len(positions)
                t = float(signed[a] / (signed[a] - signed[b]))
                positions.append(vertices[a] * (1 - t) + vertices[b] * t)
                edge_ids.append(key)
                edge_t.append(t)
            ends.append(nodes[key])
        assert len(ends) == 2, "Section goes exactly through source vertex; explicit resampling required"
        segments.append(ends)
        triangle_rows.append(int(face_row))
    positions = np.array(positions)
    segments = np.array(segments, dtype=np.int32)
    adjacency = [[] for _ in positions]
    for index, (a, b) in enumerate(segments):
        adjacency[a].append((b, index))
        adjacency[b].append((a, index))
    seen, components = set(), []
    for seed in range(len(positions)):
        if seed in seen:
            continue
        todo, ids, rows = [seed], set(), set()
        while todo:
            node = todo.pop()
            if node in seen:
                continue
            seen.add(node)
            ids.add(node)
            for other, row in adjacency[node]:
                todo.append(other)
                rows.add(row)
        components.append((ids, rows))
    ids, rows = min(components, key=lambda pair: np.linalg.norm(positions[list(pair[0])].mean(0) - center))
    rows = np.array(sorted(rows))
    selected = segments[rows]
    xy = np.einsum("ijk,kl->ijl", positions[selected] - center, frame)
    start, delta = xy[:, 0], xy[:, 1] - xy[:, 0]
    rays, missing, multiple = [], 0, 0
    for degrees in range(360):
        theta = np.deg2rad(degrees)
        direction = np.array([np.cos(theta), np.sin(theta)])
        denominator = cross2(direction, delta)
        valid = abs(denominator) > 1e-12
        distance = cross2(start, delta) / np.where(valid, denominator, 1)
        fraction = cross2(start, direction) / np.where(valid, denominator, 1)
        hit = np.flatnonzero(valid & (distance > 0) & (fraction >= 0) & (fraction <= 1))
        missing += int(len(hit) == 0)
        multiple += int(len(hit) > 1)
        if len(hit) != 1:
            rays.append({"degrees": degrees, "hitCount": len(hit)})
            continue
        chosen = int(hit[0])
        segment_row = int(rows[chosen])
        source_face_row = triangle_rows[segment_row]
        face = faces[source_face_row]
        bary = np.zeros(3)
        for node, scale in zip(segments[segment_row], (1 - fraction[chosen], fraction[chosen])):
            for vertex, weight in zip(edge_ids[node], (1 - edge_t[node], edge_t[node])):
                bary[int(np.flatnonzero(face == vertex)[0])] += scale * weight
        point = bary @ vertices[face]
        assert np.linalg.norm(point - center - frame @ direction * distance[chosen]) < 1e-9
        rays.append({"degrees": degrees, "hitCount": 1, "sourceTriangle": source_face_row,
                     "barycentric": bary.tolist(), "radiusSourceUnits": float(distance[chosen])})
    return {"center": center.tolist(), "tangent": tangent.tolist(), "radialFrame": frame.tolist(),
            "completePlaneContourComponents": len(components), "selectedContourVertices": len(ids),
            "selectedContourDegreeNotTwo": sum(len(adjacency[index]) != 2 for index in ids),
            "missingRays": missing, "multipleHitRays": multiple,
            "selectedSourceTriangles": [triangle_rows[index] for index in rows], "rays": rays}


def topology(vertices, faces):
    edge_rows = {}
    for index, face in enumerate(faces):
        for a, b in zip(face, np.roll(face, -1)):
            edge_rows.setdefault(tuple(sorted((int(a), int(b)))), []).append(index)
    boundary = [edge for edge, rows in edge_rows.items() if len(rows) == 1]
    degrees = np.bincount(np.array(boundary).ravel(), minlength=len(vertices))
    return {"referencedVertices": len(np.unique(faces)), "faces": len(faces), "edges": len(edge_rows),
            "euler": len(np.unique(faces)) - len(edge_rows) + len(faces),
            "boundaryEdges": len(boundary), "boundaryDegreeNotTwo": int(np.sum((degrees > 0) & (degrees != 2))),
            "nonmanifoldEdges": sum(len(rows) > 2 for rows in edge_rows.values())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = ROOT / args.out
    output.mkdir(parents=True, exist_ok=True)
    files = {"prototype": PREP / "prep02/gloves/retopology-prototype.npz",
             "branches": PREP / "glove-anatomy02b/branches.npz",
             "classification": OLD / "glove-anatomy02/classification.json",
             "dense": PREP / "prep02/gloves/cleaned-donor.npz",
             "baseColor": PREP / "prep02/gloves/baseColorTexture.png",
             "metallicRoughness": PREP / "prep02/gloves/metallicRoughnessTexture.png",
             "cavity08": PREP / "glove-cavity08/open-glove-source.npz",
             "opening": OLD / "glove-cavity08/opening.json",
             "localization": OLD / "glove-cavity09/localization.json"}
    pins = {name: pin(path) for name, path in files.items()}
    donor = dict(np.load(ROOT / files["prototype"]))
    branch = dict(np.load(ROOT / files["branches"]))
    opened = dict(np.load(ROOT / files["cavity08"]))
    classification = json.loads((ROOT / files["classification"]).read_text())
    opening = json.loads((ROOT / files["opening"]).read_text())
    for name, key in (("prototype", "source"), ("cavity08", "candidate"), ("dense", "denseSource")):
        assert pins[name]["sha256"] == opening[key]["sha256"]
    assert np.array_equal(donor["vertices"], branch["vertices"])
    assert np.array_equal(donor["faces"], branch["faces"])
    assert np.array_equal(opened["vertices"], donor["vertices"])
    assert np.array_equal(opened["faces"], donor["faces"][opened["sourcePrototypeFaceRows"]])
    vertices, faces, labels = donor["vertices"], donor["faces"], branch["branchLabels"]
    sections = []
    for digit, record in classification["digits"].items():
        centers = np.array(record["sectionCenters"])
        for index, center in enumerate(centers):
            tangent = centers[min(index + 1, 3)] - centers[max(index - 1, 0)]
            row = section(vertices, faces, center, tangent)
            row.update({"digit": digit, "station": index})
            sections.append(row)
    mixed = np.flatnonzero(np.ptp(labels[faces], axis=1) > 0)
    report = {"acceptedWearable": False, "status": "SOURCE_CONTOUR_AND_CUFF_EVIDENCE_ONLY",
              "recipe": pin(Path(__file__).resolve().relative_to(ROOT)), "sourcePins": pins,
              "sections": sections, "sampledRadialDirections": len(sections) * 360,
              "missingDirections": sum(row["missingRays"] for row in sections),
              "multipleHitDirections": sum(row["multipleHitRays"] for row in sections),
              "mixedPalmDigitTrianglesExcludedByPureLabelTrees": len(mixed),
              "mixedTriangleRows": mixed.tolist(), "cavity08Topology": topology(vertices, opened["faces"]),
              "cavity08OriginalXYZAndRetainedFacesExact": True,
              "cavity08CuffBoundarySourceVertexIds": opening["topology"]["orderedSourceBoundaryVertexIds"],
              "cuffFeatureInterpretation": "Certified nonboundary cycles localize near cuff, not palm. Authored strap/detail interpretation remains parent-owned; preserve it.",
              "limits": ["20 source sections and 360 angles each are finite samples, not full source enclosure proof.",
                         "Source section centers are geometric hypotheses, not source joints or fingertip endpoints.",
                         "Cavity08 is reusable as an unchanged selected exterior candidate; its existing aperture still needs target wrist correspondence.",
                         "No fit, source deformation, dense material bake, articulated movement, or played art acceptance."]}
    assert report["missingDirections"] == report["multipleHitDirections"] == 0
    assert all(row["selectedContourDegreeNotTwo"] == 0 for row in sections)
    assert report["mixedPalmDigitTrianglesExcludedByPureLabelTrees"] == 427
    assert report["cavity08Topology"]["euler"] == -1
    assert report["cavity08Topology"]["boundaryEdges"] == 71
    for name, path in files.items():
        assert pin(path) == pins[name], "Input changed during source assay"
    witness_rows = []
    for section_id, row in enumerate(sections):
        for ray in row.pop("rays"):
            witness_rows.append([section_id, ray["degrees"], ray["sourceTriangle"],
                                 *ray["barycentric"], ray["radiusSourceUnits"]])
    witness_path = output / "source-section-witnesses.npz"
    np.savez_compressed(witness_path, columns=np.array([
        "section", "angleDegrees", "sourceTriangle", "baryA", "baryB", "baryC", "radiusSourceUnits"]),
        witnesses=np.array(witness_rows))
    report["witnesses"] = pin(witness_path.relative_to(ROOT))
    (output / "source-measurements.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key in
                      ("status", "sampledRadialDirections", "missingDirections", "multipleHitDirections", "cavity08Topology")}))


if __name__ == "__main__":
    main()
