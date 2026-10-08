"""Cheap canonical ownership audit; never invokes Blender or opens a scene.

Run from any cwd with the localai/runtime/unimate/.venv/bin/python runtime.
Outputs remain in this lane's evidence directory. Blender derivative/source
preservation, real garment openings and moving appearance are still untested.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import mask_core as core


def main():
    np.seterr(all="raise")
    out = ROOT / "docs/evidence/rider-rebuild/outfit-body-mask01"
    arrays_path = ROOT / "harness/out/rider-rebuild/native-hand-repair01/native02/native-body.npz"
    source = {"path": str(arrays_path.relative_to(ROOT)), "sha256": hashlib.sha256(arrays_path.read_bytes()).hexdigest()}
    assert source["sha256"] == "e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2"
    data = dict(np.load(arrays_path))
    loop_vertices, starts, totals = core.canonical_polygons(data)
    names = data["jointNames"].tolist()
    manifest = core.frozen_manifest(data["vertices"], loop_vertices, starts, totals,
        data["nativeCoefficients"], names, data["jointHeads"], data["jointTails"], source)
    coverage = core.vertex_coverage(data["vertices"], data["nativeCoefficients"], names,
        data["jointHeads"], data["jointTails"])
    ownership = core.polygon_ownership(coverage, loop_vertices, starts, totals)
    triangles = ownership[data["sourcePolygonRows"]]
    report = {"acceptedArt": False, "status": "NUMPY_SOURCE_AUDIT_ONLY_NO_BLENDER_RUN",
              "canonicalVertices": len(data["vertices"]), "canonicalPolygons": len(starts),
              "canonicalTriangles": len(triangles), "canonicalCorners": len(loop_vertices),
              "canonicalTopologySHA256": manifest["bodyTopologySHA256"], "source": source,
              "garments": {}, "sourceChecks": [], "limitations": core.POLICY["limits"]}
    for garment, bit in core.GARMENTS.items():
        ids = core.equipped_ids(manifest, [garment])
        assert np.array_equal(np.asarray(ids), np.flatnonzero(ownership & bit))
        tri_ids = np.flatnonzero(triangles & bit)
        assert set(data["sourcePolygonRows"][tri_ids]) == set(ids)
        # Assert whole-face ownership, so crossing opening polygons are retained.
        all_corners = np.concatenate([loop_vertices[start:start+total] for start, total in zip(starts[ids], totals[ids])])
        assert coverage[garment][all_corners].all()
        covered = data["vertices"][np.unique(all_corners)]
        report["garments"][garment] = {"polygons": len(ids), "triangles": len(tri_ids),
            "uniqueSourceVertices": len(np.unique(all_corners)), "bodyRegionBoundsM": [covered.min(0).tolist(), covered.max(0).tolist()],
            "bothSidesPresent": bool((covered[:, 0] < 0).any() and (covered[:, 0] > 0).any())}
        assert report["garments"][garment]["bothSidesPresent"]
    kept = np.setdiff1d(np.arange(len(starts)), core.equipped_ids(manifest, list(core.GARMENTS)))
    assert len(kept) > 0 and (triangles == 0).any()
    # The entire head is retained even when every garment is equipped.
    for p in np.flatnonzero(np.logical_and.reduceat(data["vertices"][loop_vertices, 2] >= 1.56, starts)):
        assert ownership[p] == 0, ("Covered face/head", int(p))
    report["sourceChecks"].append("Every head polygon above1.56m retained; every garment polygon has all corners in its fixed covered region.")
    core.validate_manifest(manifest, manifest)
    for key in ("bodyTopologySHA256", "bodyPositionSHA256", "bodyFieldSHA256", "restEndpointsSHA256", "policySHA256"):
        stale = dict(manifest); stale[key] = "stale"
        try: core.validate_manifest(stale, manifest)
        except AssertionError: report["sourceChecks"].append("Rejected changed " + key)
        else: raise AssertionError(("Accepted stale manifest", key))
    altered = json.loads(json.dumps(manifest))
    altered["garmentPolygonIds"]["gloves"].pop()
    try: core.validate_manifest(altered, manifest)
    except AssertionError: report["sourceChecks"].append("Rejected altered glove face ownership")
    else: raise AssertionError("Accepted altered ownership")
    manifest["garmentTriangleIds"] = {g: np.flatnonzero(triangles & bit).tolist() for g, bit in core.GARMENTS.items()}
    report["sourceChecks"].append("Every canonical triangle inherits its original native polygon's garment ownership.")
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(HERE / "canonical-face-ownership.npz", sourcePolygonOwnership=ownership,
        sourceTriangleOwnership=triangles, sourceTrianglePolygonIds=data["sourcePolygonRows"],
        sourceLoopVertices=loop_vertices, sourcePolygonLoopStarts=starts, sourcePolygonLoopTotals=totals)
    (HERE / "canonical-mask-manifest.json").write_text(json.dumps(manifest, separators=(",", ":")) + "\n")
    report["canonicalOwnershipSHA256"] = hashlib.sha256((HERE / "canonical-face-ownership.npz").read_bytes()).hexdigest()
    report["canonicalManifestSHA256"] = hashlib.sha256((HERE / "canonical-mask-manifest.json").read_bytes()).hexdigest()
    report["allOutfitKeptPolygons"] = len(kept)
    report["allOutfitRemovedPolygons"] = len(starts) - len(kept)
    (out / "numpy-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
