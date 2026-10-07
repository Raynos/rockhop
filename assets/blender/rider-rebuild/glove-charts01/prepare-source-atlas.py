"""Complete source-surface ownership and shared-seam coordinates for fitting.

This is a geometric patch atlas on the original 3D surface, not replacement UVs
or an assertion that the cuff handle can be flattened into a disk. All material
coordinates and geometric detail continue to belong to the selected donor.
"""
import argparse
import json
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve

_spec = spec_from_file_location("source_measure", Path(__file__).with_name("measure-source.py"))
_source = module_from_spec(_spec); _spec.loader.exec_module(_source)
ROOT, PREP, OLD, pin = _source.ROOT, _source.PREP, _source.OLD, _source.pin
DIGITS = ["pinky", "ring", "middle", "index", "thumb"]


def arc_coordinates(points, centers):
    """Reconstruct every point exactly, including terminal axial residual."""
    segments = np.diff(centers, axis=0)
    lengths = np.linalg.norm(segments, axis=1)
    tangent = segments / lengths[:, None]
    # A proper parallel transported frame, not independently flipped section axes.
    first = np.array([1., 0., 0.]); first -= tangent[0] * np.dot(first, tangent[0])
    first /= np.linalg.norm(first)
    radial = [first]
    for before, after in zip(tangent[:-1], tangent[1:]):
        axis = np.cross(before, after)
        sine = np.linalg.norm(axis); cosine = np.dot(before, after)
        if sine < 1e-12:
            assert cosine > 0
            value = radial[-1].copy()
        else:
            axis /= sine
            value = radial[-1] * cosine + np.cross(axis, radial[-1]) * sine + axis * np.dot(axis, radial[-1]) * (1 - cosine)
        value -= after * np.dot(value, after); value /= np.linalg.norm(value)
        radial.append(value)
    radial = np.array(radial); normal = np.cross(tangent, radial)
    delta = points[:, None, :] - centers[None, :-1, :]
    parameter = np.clip(np.sum(delta * segments[None], axis=2) / lengths[None] ** 2, 0, 1)
    projected = centers[None, :-1] + parameter[..., None] * segments[None]
    selected = np.argmin(np.sum((points[:, None] - projected) ** 2, axis=2), axis=1)
    p = projected[np.arange(len(points)), selected]
    residual = points - p
    x = np.sum(residual * radial[selected], axis=1)
    y = np.sum(residual * normal[selected], axis=1)
    z = np.sum(residual * tangent[selected], axis=1)
    angle = np.arctan2(y, x); radius = np.hypot(x, y)
    arc = np.r_[0, np.cumsum(lengths[:-1])][selected] + parameter[np.arange(len(points)), selected] * lengths[selected]
    rebuilt = p + radial[selected] * (radius * np.cos(angle))[:, None] + normal[selected] * (radius * np.sin(angle))[:, None] + tangent[selected] * z[:, None]
    assert np.max(np.linalg.norm(rebuilt - points, axis=1)) < 1e-12
    return {"segment": selected, "segmentParameter": parameter[np.arange(len(points)), selected],
            "arcSourceUnits": arc, "angleRadians": angle, "radiusSourceUnits": radius,
            "axialResidualSourceUnits": z, "centers": centers, "tangents": tangent,
            "radial": radial, "normal": normal}, float(np.max(np.linalg.norm(rebuilt - points, axis=1)))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", required=True)
    args = parser.parse_args(); output = ROOT / args.out; output.mkdir(parents=True, exist_ok=True)
    paths = {"source": PREP / "glove-cavity08/open-glove-source.npz",
             "branches": PREP / "glove-anatomy02b/branches.npz",
             "classification": OLD / "glove-anatomy02/classification.json",
             "localization": OLD / "glove-cavity09/localization.json",
             "opening": OLD / "glove-cavity08/opening.json"}
    pins = {name: pin(path) for name, path in paths.items()}
    source = dict(np.load(ROOT / paths["source"]))
    branches = dict(np.load(ROOT / paths["branches"]))
    classification = json.loads((ROOT / paths["classification"]).read_text())
    opening = json.loads((ROOT / paths["opening"]).read_text())
    localized = json.loads((ROOT / paths["localization"]).read_text())
    assert pins["source"]["sha256"] == opening["candidate"]["sha256"]
    original_ids = np.unique(source["faces"])
    global_to_local = np.full(len(source["vertices"]), -1, dtype=np.int32)
    global_to_local[original_ids] = np.arange(len(original_ids))
    vertices = source["vertices"][original_ids]
    faces = global_to_local[source["faces"]]
    labels = branches["branchLabels"][original_ids]
    assert np.array_equal(source["vertices"], branches["vertices"])
    edge_faces = {}
    for row, triangle in enumerate(faces):
        for a, b in zip(triangle, np.roll(triangle, -1)):
            edge_faces.setdefault(tuple(sorted((int(a), int(b)))), []).append(row)
    edges = np.array(list(edge_faces))
    lengths = np.linalg.norm(vertices[edges[:, 1]] - vertices[edges[:, 0]], axis=1)
    assert lengths.min() > 0
    data = 1 / lengths
    graph = coo_matrix((np.r_[data, data], (np.r_[edges[:, 0], edges[:, 1]], np.r_[edges[:, 1], edges[:, 0]])),
                       shape=(len(vertices), len(vertices))).tocsr()
    laplacian = diags(np.asarray(graph.sum(1)).ravel()) - graph
    cuff_global = np.array(opening["topology"]["orderedSourceBoundaryVertexIds"])
    cuff_local = global_to_local[cuff_global]
    assert np.all(cuff_local >= 0)
    boundary = (labels > 0)
    boundary[cuff_local] = True
    boundary_ids, free_ids = np.flatnonzero(boundary), np.flatnonzero(~boundary)
    partition = np.zeros((len(vertices), 6))
    partition[np.flatnonzero(labels > 0), labels[labels > 0]] = 1
    partition[cuff_local, 0] = 1
    assert np.all(partition[boundary_ids].sum(1) == 1)
    rhs = -(laplacian[free_ids][:, boundary_ids] @ partition[boundary_ids])
    partition[free_ids] = spsolve(laplacian[free_ids][:, free_ids], rhs)
    partition_error = float(np.max(abs(partition.sum(1) - 1)))
    residual = float(np.max(abs(laplacian[free_ids] @ partition)))
    assert partition.min() > -1e-12 and partition.max() < 1 + 1e-12 and partition_error < 1e-11
    # Cuff feature remains its exact source neighborhood plus two mesh rings.
    feature_rows = set()
    lookup = {int(row): i for i, row in enumerate(source["sourcePrototypeFaceRows"])}
    for cycle in localized["localizedCycles"]:
        for row in cycle["incidentPrototypeFaceRows"]:
            assert int(row) in lookup
            feature_rows.add(lookup[int(row)])
    feature_seed_rows = sorted(feature_rows)
    for _ in range(2):
        ids = set(faces[list(feature_rows)].ravel().tolist())
        feature_rows.update(i for i, face in enumerate(faces) if any(int(vertex) in ids for vertex in face))
    centers = vertices[faces].mean(1)
    normal = np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]], vertices[faces[:, 2]] - vertices[faces[:, 0]])
    face_partition = partition[faces].mean(1)
    names, assignments = [], []
    for row, face in enumerate(faces):
        unique = sorted(set(int(value) for value in labels[face]))
        digits = [x for x in unique if x > 0]
        if row in feature_rows:
            name = "cuff_feature"
        elif digits:
            assert len(digits) == 1, "Source triangle bridges two distal digits; explicit chart decision required"
            name = DIGITS[digits[0] - 1] + ("_collar" if 0 in unique else "_digit")
        elif face_partition[row, 0] >= .65:
            name = "cuff"
        else:
            rank = np.argsort(face_partition[row, 1:])[::-1]
            strongest, second = face_partition[row, rank[0] + 1], face_partition[row, rank[1] + 1]
            if second >= .20 and strongest + second >= .65:
                pair = sorted([int(rank[0]), int(rank[1])])
                name = "web_" + "_".join(DIGITS[i] for i in pair)
            elif abs(normal[row, 2]) < .25 * np.linalg.norm(normal[row]):
                name = "palm_side"
            else:
                name = "palm_positive_z" if normal[row, 2] > 0 else "palm_negative_z"
        if name not in names:
            names.append(name)
        assignments.append(names.index(name))
    assignments = np.array(assignments, dtype=np.int32)
    seams, seam_charts = [], []
    for edge, rows in edge_faces.items():
        if len(rows) == 2 and assignments[rows[0]] != assignments[rows[1]]:
            seams.append(edge); seam_charts.append([assignments[row] for row in rows])
    coordinates, reconstruction = {}, {}
    for digit in DIGITS:
        chart, error = arc_coordinates(vertices, np.array(classification["digits"][digit]["sectionCenters"]))
        coordinates.update({digit + "_" + key: value for key, value in chart.items()})
        reconstruction[digit] = error
    arrays = {"vertices": vertices, "faces": faces, "sourceVertexRows": original_ids,
              "sourcePrototypeFaceRows": source["sourcePrototypeFaceRows"],
              "sourceDenseOriginalTriangleRows": source["originalTriangleRows"][original_ids],
              "sourceDenseBarycentric": source["barycentric"][original_ids],
              "sourcePrototypeCornerUV": source["cornerUVPrototype"],
              "sourceBranchLabels": labels, "cuffBoundaryVertexIds": cuff_local,
              "chartNames": np.array(names), "faceChart": assignments,
              "sourceHarmonicPartition": partition, "sharedSeamEdges": np.array(seams, dtype=np.int32),
              "sharedSeamChartPairs": np.array(seam_charts, dtype=np.int32),
              "protectedCuffFeatureFaces": np.array(sorted(feature_rows), dtype=np.int32),
              "sourcePalmCuffCoordinatesXYZ": vertices.copy(), **coordinates}
    path = output / "source-atlas.npz"; np.savez_compressed(path, **arrays)
    assert np.array_equal(vertices[faces], source["vertices"][source["faces"]])
    report = {"acceptedWearable": False, "status": "COMPLETE_SOURCE_PATCH_OWNERSHIP_WITH_SHARED_SEAMS",
              "recipe": pin(Path(__file__).resolve().relative_to(ROOT)), "sourcePins": pins,
              "output": pin(path.relative_to(ROOT)), "referencedSourceVertices": len(vertices),
              "retainedSourceFaces": len(faces), "unassignedFaces": 0, "duplicatedGeometryVertices": 0,
              "sourceXYZFacesPrototypeCornerUVUnchanged": True, "sharedSeamEdges": len(seams),
              "chartFaceCounts": {name: int(np.sum(assignments == index)) for index, name in enumerate(names)},
              "sourcePartitionMinimum": float(partition.min()), "sourcePartitionMaximum": float(partition.max()),
              "sourcePartitionUnityMaxResidual": partition_error, "harmonicFreeEquationMaxResidual": residual,
              "digitCoordinateReconstructionMaxSourceUnits": reconstruction,
              "cuffFeature": {"exactCycleIncidentFaceSeeds": feature_seed_rows, "twoRingProtectedFaces": len(feature_rows),
                              "interpretation": "Unchanged actual cuff feature neighborhood, no automatic topology repair"},
              "limits": ["Geometric patch atlas in 3D, not a claim of bijective 2D flattening or replacement texture UVs.",
                         "Web/palm/cuff patch ownership derives from explicit harmonic partition and face orientation; anatomical naming remains a fitting hypothesis.",
                         "Partition fields are source interpolation coordinates, not garment skinning weights or source-to-target correspondence.",
                         "Source preserved at identity; no fitted deformation or deformed distortion/enclosure pass claimed.",
                         "Prototype corner UV is an unchanged proxy; final appearance still requires dense original corner UV authority."]}
    for name, source_path in paths.items():
        assert pins[name] == pin(source_path)
    (output / "source-atlas.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "vertices": len(vertices), "faces": len(faces),
                      "seams": len(seams), "chartFaceCounts": report["chartFaceCounts"], "partitionResidual": partition_error}))


if __name__ == "__main__":
    main()
