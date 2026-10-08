"""Rest-space garment ownership, shared by cheap NumPy audit and Blender apply.

No Blender dependency, nearest-body transfer, camera predicate or mesh editing.
Each bit denotes an equipped garment's complete native polygon ownership.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

GARMENTS = {"hoodie": 1, "jeans": 2, "gloves": 4, "boots": 8}
POLICY = json.loads(Path(__file__).with_name("policy.json").read_text())


def digest(*arrays):
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(str((a.dtype.str, a.shape)).encode())
        h.update(a.tobytes())
    return h.hexdigest()


def topology_hash(vertex_count, loop_vertices, starts, totals):
    return digest(np.array([vertex_count], dtype="<i8"),
                  np.asarray(loop_vertices, dtype="<i4"),
                  np.asarray(starts, dtype="<i4"), np.asarray(totals, dtype="<i4"))


def canonical_polygons(arrays):
    """Reconstruct original native polygons using exact triangle corner ancestry."""
    faces = arrays["faces"]
    rows = arrays["sourcePolygonRows"]
    source_loops = arrays["sourceLoopRows"]
    loop_vertices = np.full(int(source_loops.max()) + 1, -1, dtype=np.int32)
    for loop, vertex in zip(source_loops.flat, faces.flat):
        assert loop_vertices[loop] in (-1, vertex), ("Inconsistent source corner", int(loop))
        loop_vertices[loop] = vertex
    assert (loop_vertices >= 0).all(), "Unmapped native corner"
    starts, totals = [], []
    for polygon in range(int(rows.max()) + 1):
        loops = np.unique(source_loops[rows == polygon])
        assert len(loops) >= 3 and np.array_equal(loops, np.arange(loops[0], loops[-1] + 1))
        starts.append(loops[0]); totals.append(len(loops))
    assert np.array_equal(np.asarray(starts)[1:], np.cumsum(totals)[:-1])
    return loop_vertices, np.asarray(starts, dtype=np.int32), np.asarray(totals, dtype=np.int32)


def vertex_coverage(vertices, weights, names, heads, tails, policy=POLICY):
    """Semantic native75 regions with deliberately retained opening skin bands."""
    vertices = np.asarray(vertices, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    names = list(names)
    assert weights.shape == (len(vertices), len(names)) and len(names) == 75
    assert np.isfinite(vertices).all() and np.isfinite(weights).all()
    assert np.allclose(weights.sum(1), 1., atol=1e-5), "Noncanonical skin rows"
    lookup = {name: i for i, name in enumerate(names)}
    assert len(lookup) == 75
    z = vertices[:, 2]
    threshold = policy["minimumRegionMass"]

    def mass(selected):
        indices = [lookup[n] for n in selected]
        assert indices
        return weights[:, indices].sum(1)

    arms = [n for n in names if n.startswith(("DEF-shoulder.", "DEF-upper_arm.", "DEF-forearm."))]
    torso = ["DEF-spine", "DEF-spine.001", "DEF-spine.002", "DEF-spine.003"]
    lower = [n for n in names if n.startswith(("DEF-pelvis.", "DEF-thigh.", "DEF-shin."))] + ["DEF-spine"]
    h = policy["hoodie"]
    hoodie = (mass(arms) >= threshold) | ((mass(torso) >= threshold) & (z >= h["hemInnerZ"]))
    # New neck/chest topology carries neck weights. Do not nearest-map it to the
    # discarded canonical neck; use the actual central low chest in this body.
    hoodie |= (np.abs(vertices[:, 0]) < .20) & (z >= h["hemInnerZ"]) & (z < h["neckKeepAboveZ"])
    neck_origin = heads[lookup["DEF-spine.004"]]
    neck_radius = np.linalg.norm(vertices[:, :2] - neck_origin[:2], axis=1)
    hoodie &= (z < h["neckKeepAboveZ"]) | (neck_radius > h["neckKeepRadiusM"])
    gloves = np.zeros(len(vertices), dtype=bool)
    boots = np.zeros(len(vertices), dtype=bool)
    for side in ("L", "R"):
        hand = "DEF-hand." + side
        wrist = heads[lookup[hand]]
        forearm = "DEF-forearm." + side + ".001"
        direction = wrist - heads[lookup[forearm]]
        direction /= np.linalg.norm(direction)
        # Elementwise dot avoids platform BLAS dispatch for this tiny 3-vector.
        distal = ((vertices - wrist) * direction).sum(1)
        same_arm = mass([n for n in arms if side in n.split(".")]) >= threshold
        hoodie &= ~same_arm | (distal <= -h["wristKeepProximalM"])
        hand_names = [n for n in names if n.endswith("." + side) and n.startswith(
            ("DEF-hand.", "DEF-palm.", "DEF-f_", "DEF-thumb."))]
        gloves |= (mass(hand_names) >= threshold) & (distal >= policy["gloves"]["wristKeepDistalM"])
        foot_names = ["DEF-foot." + side, "DEF-toe." + side, "DEF-shin." + side + ".001"]
        boots |= (mass(foot_names) >= threshold) & (z <= policy["boots"]["collarInnerZ"])
    j = policy["jeans"]
    jeans = (mass(lower) >= threshold) & (z <= j["waistInnerZ"]) & (z >= j["cuffInnerZ"])
    return {"hoodie": hoodie, "jeans": jeans, "gloves": gloves, "boots": boots}


def polygon_ownership(coverage, loop_vertices, starts, totals):
    ownership = np.zeros(len(starts), dtype=np.uint8)
    # Polygon interior follows every boundary corner, never a center or majority.
    for garment, bit in GARMENTS.items():
        covered = coverage[garment][loop_vertices]
        complete = np.logical_and.reduceat(covered, starts)
        assert len(complete) == len(totals)
        ownership[complete] |= bit
    return ownership


def frozen_manifest(vertices, loop_vertices, starts, totals, weights, names, heads, tails, source):
    coverage = vertex_coverage(vertices, weights, names, heads, tails)
    ownership = polygon_ownership(coverage, loop_vertices, starts, totals)
    return {"schemaVersion": 1, "acceptedArt": False, "source": source,
            "bodyTopologySHA256": topology_hash(len(vertices), loop_vertices, starts, totals),
            "bodyPositionSHA256": digest(np.asarray(vertices, dtype="<f4")),
            "bodyFieldSHA256": digest(np.asarray(weights, dtype="<f4")),
            "jointNames": list(names), "restEndpointsSHA256": digest(
                np.asarray(heads, dtype="<f8"), np.asarray(tails, dtype="<f8")),
            "policySHA256": hashlib.sha256(Path(__file__).with_name("policy.json").read_bytes()).hexdigest(),
            "vertices": len(vertices), "polygons": len(starts), "corners": len(loop_vertices),
            "garmentPolygonIds": {name: np.flatnonzero(ownership & bit).tolist() for name, bit in GARMENTS.items()},
            "limits": POLICY["limits"]}


def validate_manifest(manifest, actual):
    for key in ("schemaVersion", "bodyTopologySHA256", "bodyPositionSHA256", "bodyFieldSHA256",
                "jointNames", "restEndpointsSHA256", "policySHA256", "garmentPolygonIds"):
        assert manifest[key] == actual[key], ("Stale or altered body mask", key)


def equipped_ids(manifest, equipped):
    assert equipped and len(equipped) == len(set(equipped)) and set(equipped) <= set(GARMENTS)
    ids = sorted({i for name in equipped for i in manifest["garmentPolygonIds"][name]})
    assert ids and min(ids) >= 0 and max(ids) < manifest["polygons"]
    return ids
