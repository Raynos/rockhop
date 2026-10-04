"""One hem-only analytic attachment counterfactual; never write a skin asset."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
for name in ["diagnosis", "field", "motion-field", "out"]:
    parser.add_argument("--" + name, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
diagnosis, field_path, motion_path, out = [
    Path(getattr(args, n.replace("-", "_"))).resolve() for n in ["diagnosis", "field", "motion-field", "out"]
]
assert not out.exists()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
d = json.loads(diagnosis.read_text())
field, motion = np.load(field_path), np.load(motion_path)
names = field["boneNames"].tolist()
rest = field["nativeRestXYZ"]
# Reconstruct exact hem IDs from the diagnostic script's recorded front cohorts
# and original field geometry; no extra projection or threshold sweep.
import bpy
bpy.ops.wm.open_mainfile(filepath=next(p for p in d["pins"] if p.endswith(".blend")))
g = bpy.data.objects["Actual donor explicit native-four skin, unaccepted"]
import collections
counts = collections.Counter()
for poly in g.data.polygons:
    ids = list(poly.vertices)
    counts.update(tuple(sorted((ids[i], ids[(i + 1) % len(ids)]))) for i in range(len(ids)))
remaining = {e for e, count in counts.items() if count == 1}
loops = []
while remaining:
    first = min(remaining)
    remaining.remove(first)
    ids, todo = set(first), list(first)
    while todo:
        v = todo.pop()
        for e in [e for e in remaining if v in e]:
            remaining.remove(e)
            for other in e:
                if other not in ids:
                    ids.add(other)
                    todo.append(other)
    loops.append(sorted(ids))
hem = np.array(min(loops, key=lambda ids: rest[ids, 2].mean()))
assert len(hem) == d["diagnosticRegions"]["hem"]["vertices"]
original = field["fourWeights"][hem].astype(np.float64)
original /= original.sum(1)[:, None]
counterfactual = original.copy()
thigh_ids = [names.index("thigh.L"), names.index("thigh.R")]
pelvis_id = names.index("pelvis")
moved = counterfactual[:, thigh_ids].sum(1)
counterfactual[:, pelvis_id] += moved
counterfactual[:, thigh_ids] = 0
counterfactual /= counterfactual.sum(1)[:, None]
assert (counterfactual > 0).sum(1).max() <= 4
homogeneous = np.column_stack([rest[hem], np.ones(len(hem))])
def plane(points):
    center = points.mean(0)
    normal = np.linalg.svd(points - center, full_matrices=False)[2][-1]
    deviation = np.abs((points - center) @ normal)
    return {"normal": normal.tolist(), "p95DeviationM": float(np.percentile(deviation, 95)), "maxDeviationM": float(deviation.max())}
frames = []
for frame_id in [0, 48, 72, 144, 168, 192]:
    matrices = motion["poseSkinMatricesNative"][frame_id]
    world = motion["rigWorldRows"]
    baseline = (np.einsum("vj,jab,vb->va", original, matrices, homogeneous, optimize=True) @ world.T)[:, :3]
    proposed = (np.einsum("vj,jab,vb->va", counterfactual, matrices, homogeneous, optimize=True) @ world.T)[:, :3]
    actual = motion["fourActualWorld"][motion["sampledFrameIDs"].tolist().index(frame_id), hem]
    parity = np.linalg.norm(baseline - actual, axis=1)
    assert parity.max() < 1e-6
    frames.append({
        "frame": frame_id, "baselinePredictionParityMaxM": float(parity.max()),
        "originalHemBestFitPlane": plane(baseline), "counterfactualHemBestFitPlane": plane(proposed),
        "maximumHemPositionChangeM": float(np.linalg.norm(proposed - baseline, axis=1).max()),
    })
result = {
    "status": "UNACCEPTED one hem-only analytic thigh-to-pelvis counterfactual, no asset change",
    "pins": {str(p): sha(p) for p in [diagnosis, field_path, motion_path]},
    "recipeSHA256": sha(__file__), "hemVertices": len(hem), "hemVertexIDs": hem.tolist(),
    "meanMovedThighMass": float(moved.mean()), "maximumMovedThighMass": float(moved.max()),
    "counterfactualMaxInfluences": int((counterfactual > 0).sum(1).max()), "frames": frames,
    "rule": "On the149existing hem boundary vertices only, mathematically move exactly existing thigh.L/R mass to existing pelvis, preserving all other mass. No blend radius/count search or new projection.",
    "limits": [
        "This isolates leg attachment contribution to the observed hem bow. It is not a repair: neighboring surface vertices are intentionally unchanged and transition/collision/coverage/appearance effects are not tested. No weight/rig/body/head/geometry source edits or native save.",
        "No new capture/engine admission or field adoption. All numerical failures/24coverage/cuffs/head baseline contacts/M0-M5/mobile remain open. Parent alone judges appearance; underwear/bodyQA stays independent.",
    ],
}
out.write_text(json.dumps(result, indent=2) + "\n")
print("HEM_ONLY_ATTACHMENT_COUNTERFACTUAL", json.dumps(frames[-1]), flush=True)
