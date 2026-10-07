"""Freeze exact source-ID hand rebinding support and a 28 mm wrist blend."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BASE = Path("docs/evidence/rider-rebuild/glove-charts01")


def pin(path):
    return {"path": str(path), "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", required=True)
    args = parser.parse_args(); out = ROOT / args.out; out.mkdir(parents=True, exist_ok=False)
    body_path = BASE / "target01/native-body.npz"
    body = dict(np.load(ROOT / body_path)); count = len(body["vertices"])
    alpha = np.zeros(count); side_index = np.zeros(count, dtype=np.int8); sides = {}
    inputs = [body_path, Path(__file__).resolve().relative_to(ROOT)]
    for side, tag in (("L", 1), ("R", 2)):
        hand_path = BASE / ("target01/native-hand-" + side + ".npz")
        inputs.append(hand_path); hand = dict(np.load(ROOT / hand_path))
        ancestry = hand["sourceEdgeAncestry"]
        ids = ancestry[ancestry[:, 0] == ancestry[:, 1], 0].astype(int)
        distance_from_cuff = -np.sum((body["vertices"][ids] - hand["cuffOrigin"]) * hand["cuffProximalAxis"], axis=1)
        assert np.min(distance_from_cuff) >= -1e-10
        t = np.clip(distance_from_cuff / .028, 0, 1)
        blend = t * t * (3 - 2 * t)
        assert np.all(side_index[ids] == 0)
        alpha[ids] = blend; side_index[ids] = tag
        sides[side] = {"sourceVertices": len(ids), "fullNewFieldVertices": int(np.sum(blend == 1)),
            "transitionVertices": int(np.sum((blend > 0) & (blend < 1))),
            "cuffOrigin": hand["cuffOrigin"].tolist(), "proximalAxis": hand["cuffProximalAxis"].tolist()}
    field_paths = [Path("harness/out/rider-rebuild/construction01/rig04") / ("weights-" + kind + ".json") for kind in ("full", "four")]
    names = set(body["jointNames"].tolist())
    field_stats = {}
    for path in field_paths:
        rows = json.loads((ROOT / path).read_text()); assert len(rows) == count
        assert all(name in names and weight > 0 for row in rows for name, weight in row)
        assert all(len(row) for row in rows)
        field_stats[path.stem] = {"rows": count, "maximumInfluences": max(map(len, rows)),
            "maximumSumDeviation": max(abs(sum(weight for _, weight in row) - 1) for row in rows)}
    inputs += field_paths + [Path("harness/out/rider-rebuild/construction01/combined04/rider-assembled.blend"),
        Path("harness/out/rider-rebuild/construction01/combined04/rider-contract.json"),
        BASE / "medial-correction01/proposed-joints.npz", BASE / "medial-correction01/verification.json"]
    arrays = out / "rebind-domain.npz"
    np.savez_compressed(arrays, nativeSourceVertexIds=np.arange(count), newFieldBlendAlpha=alpha,
        sideIndex=side_index, unchangedSourceVertexIds=np.flatnonzero(alpha == 0))
    result = {"accepted": False, "status": "PREPARED_HAND_FIELD_DOMAIN_NOT_EXECUTED",
        "inputs": [pin(path) for path in inputs], "arrays": pin(arrays.relative_to(ROOT)),
        "bodyVertices": count, "unchangedRows": int(np.sum(alpha == 0)),
        "changedDomainRows": int(np.sum(alpha > 0)), "sides": sides, "sourceFieldStatistics": field_stats,
        "blend": "Within exact connected clipped-hand source-ID support only: smoothstep(clamp(distance distal from cuff / 0.028, 0, 1)). Alpha=1 at wrist and distally; alpha=0 outside support.",
        "exactPreservation": "Alpha-zero old FULL and FOUR rows must be copied verbatim, with native FOUR float32 coefficients unchanged. Never renormalize those old rows.",
        "limits": ["No automatic bind has run and no skinning result is accepted.",
            "Domain is geometric connected hand support, independent of old heat labels.",
            "Old FULL coefficients are stored as emitted by Blender, including their measured normalization deviation; they remain exact outside the changing domain."]}
    (out / "rebind-domain.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("unchangedRows", "changedDomainRows", "sides", "sourceFieldStatistics")}))


if __name__ == "__main__":
    main()
