"""Localize attachment and linear-blend behavior at parent's played defects.

Read only the frozen field and measured poses; no projection/weight sweep or
candidate edit. Diagnostic regions never exclude contact or coverage witnesses.
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
for name in ["source", "field", "motion-field", "out"]:
    parser.add_argument("--" + name, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
source, field_path, motion_path, out = [
    Path(getattr(args, n.replace("-", "_"))).resolve() for n in ["source", "field", "motion-field", "out"]
]
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
pins = {str(p): sha(p) for p in [source, field_path, motion_path]}
assert pins[str(source)] == "4a0904b94a507f35590d1ec4ebfe763237fa5fb21fa189573842309cb776a0ad"
out.mkdir(parents=True, exist_ok=True)
assert not (out / "diagnosis.json").exists()
data, motion = np.load(field_path), np.load(motion_path)
names = data["boneNames"].tolist()
rest = data["nativeRestXYZ"]
weights = data["fourWeights"].astype(np.float64)
weights /= weights.sum(1)[:, None]
full_weights = data["fullWeights"].astype(np.float64)
full_weights /= full_weights.sum(1)[:, None]
bpy.ops.wm.open_mainfile(filepath=str(source))
g = bpy.data.objects["Actual donor explicit native-four skin, unaccepted"]
assert np.array_equal(np.array([v.co[:] for v in g.data.vertices]), rest)
edges = np.array([sorted(e.vertices) for e in g.data.edges])
lengths = np.linalg.norm(rest[edges[:, 1]] - rest[edges[:, 0]], axis=1)
valid_edges = lengths > 1e-12
cage_ancestry = data["patternTriangles"][data["patternTriangleID"]]
cage_anchors = np.einsum("vi,vij->vj", data["patternBarycentric"], data["patternNativeXYZ"][cage_ancestry])
cage_jump = np.linalg.norm(cage_anchors[edges[:, 1]] - cage_anchors[edges[:, 0]], axis=1)
weight_delta = np.abs(weights[edges[:, 1]] - weights[edges[:, 0]]).sum(1)
def column(name):
    return weights[:, names.index(name)]
regions = {}
for side in ["L", "R"]:
    upper, fore = column("upperArm." + side), column("forearm." + side)
    regions["elbowMix." + side] = (upper > .1) & (fore > .1)
    regions["shoulderMix." + side] = (column("chest") > .1) & (upper > .1)
counts = collections.Counter()
for poly in g.data.polygons:
    ids = list(poly.vertices)
    counts.update(tuple(sorted((ids[i], ids[(i + 1) % len(ids)]))) for i in range(len(ids)))
remaining = {edge for edge, count in counts.items() if count == 1}
loops = []
while remaining:
    first = min(remaining)
    remaining.remove(first)
    ids, todo = set(first), list(first)
    while todo:
        vertex = todo.pop()
        linked = [edge for edge in remaining if vertex in edge]
        for edge in linked:
            remaining.remove(edge)
            for other in edge:
                if other not in ids:
                    ids.add(other)
                    todo.append(other)
    loops.append(sorted(ids))
hem = np.array(min(loops, key=lambda ids: rest[ids, 2].mean()))
hem_mask = np.zeros(len(rest), dtype=np.bool_)
hem_mask[hem] = True
regions["hem"] = hem_mask
front = hem[rest[hem, 0] >= np.median(rest[hem, 0])]
center_threshold, flank_threshold = np.quantile(np.abs(rest[front, 1]), [.25, .75])
center = front[np.abs(rest[front, 1]) <= center_threshold]
flanks = front[np.abs(rest[front, 1]) >= flank_threshold]
assert len(center) and len(flanks)
def stats(values):
    if len(values) == 0:
        return None
    return dict(zip(["min", "p50", "p95", "max"], map(float, np.percentile(values, [0, 50, 95, 100]))))
def plane(points):
    center = points.mean(0)
    singular = np.linalg.svd(points - center, full_matrices=False)
    normal = singular[2][-1]
    distances = (points - center) @ normal
    return {
        "center": center.tolist(), "normal": normal.tolist(),
        "absoluteDistanceM": stats(np.abs(distances)),
    }
static = {}
for region, mask in regions.items():
    ids = np.flatnonzero(mask)
    edge_mask = valid_edges & mask[edges].all(1)
    selected = np.flatnonzero(edge_mask)
    static[region] = {
        "vertices": len(ids), "nativeBounds": [rest[ids].min(0).tolist(), rest[ids].max(0).tolist()] if len(ids) else None,
        "meanBoneWeights": {n: float(weights[ids, i].mean()) for i, n in enumerate(names) if len(ids) and weights[ids, i].sum() > 0},
        "internalEdges": len(selected),
        "neighborWeightL1": stats(weight_delta[selected]),
        "cageAnchorJumpOverMaterialEdge": stats(cage_jump[selected] / lengths[selected]),
        "largestJumpEdges": [
            {"edgeVertexIDs": edges[i].tolist(), "materialEdgeM": float(lengths[i]),
             "cageAnchorSeparationM": float(cage_jump[i]), "neighborWeightL1": float(weight_delta[i]),
             "cageTriangles": data["patternTriangleID"][edges[i]].tolist()}
            for i in selected[np.argsort(cage_jump[selected] / lengths[selected])[-8:]]
        ],
    }
sampled_ids = motion["sampledFrameIDs"].tolist()
frames = []
for frame_id in [0, 48, 72, 144, 168, 192]:
    skin = motion["poseSkinMatricesNative"][frame_id]
    index = sampled_ids.index(frame_id)
    actual = motion["fourActualWorld"][index].astype(np.float64)
    full_actual = motion["fullActualWorld"][index].astype(np.float64)
    vertex_linear = np.einsum("vj,jab->vab", weights, skin[:, :3, :3], optimize=True)
    vertex_offset = weights @ skin[:, :3, 3]
    singular_values = np.linalg.svd(vertex_linear, compute_uv=False)
    average_linear = (vertex_linear[edges[:, 0]] + vertex_linear[edges[:, 1]]) / 2
    affine_edge = np.einsum("vab,vb->va", average_linear, rest[edges[:, 1]] - rest[edges[:, 0]])
    midpoint = (rest[edges[:, 0]] + rest[edges[:, 1]]) / 2
    attachment_edge = np.einsum("vab,vb->va", vertex_linear[edges[:, 1]] - vertex_linear[edges[:, 0]], midpoint) + vertex_offset[edges[:, 1]] - vertex_offset[edges[:, 0]]
    world_rotation = motion["rigWorldRows"][:3, :3]
    predicted = (affine_edge + attachment_edge) @ world_rotation.T
    actual_edge = actual[edges[:, 1]] - actual[edges[:, 0]]
    residual = np.linalg.norm(predicted - actual_edge, axis=1)
    assert residual.max() < 2e-6
    row = {"frame": frame_id, "edgeDecompositionParityMaxM": float(residual.max()), "regions": {}}
    for region, mask in regions.items():
        ids = np.flatnonzero(mask)
        edge_ids = np.flatnonzero(valid_edges & mask[edges].all(1))
        row["regions"][region] = {
            "minimumBlendSingularValue": stats(singular_values[ids, -1]),
            "blendDeterminant": stats(np.linalg.det(vertex_linear[ids])),
            "actualFullVsFourLossM": stats(np.linalg.norm(actual[ids] - full_actual[ids], axis=1)),
            "actualEdgeLengthOverRest": stats(np.linalg.norm(actual_edge[edge_ids], axis=1) / lengths[edge_ids]),
            "averageBoneBlendEdgeLengthOverRest": stats(np.linalg.norm(affine_edge[edge_ids], axis=1) / lengths[edge_ids]),
            "differingAttachmentTermOverRestEdge": stats(np.linalg.norm(attachment_edge[edge_ids], axis=1) / lengths[edge_ids]),
        }
    pelvis = skin[names.index("pelvis")]
    world = motion["rigWorldRows"]
    actual_h = np.column_stack([actual, np.ones(len(actual))])
    pelvis_rest = (actual_h @ np.linalg.inv(world @ pelvis).T)[:, :3]
    center_residual = pelvis_rest[center, 2] - rest[center, 2]
    flank_residual = pelvis_rest[flanks, 2] - rest[flanks, 2]
    row["hem"] = {
        "actualBestFitPlane": plane(actual[hem]),
        "pelvisFrameCenterResidualZ_M": stats(center_residual),
        "pelvisFrameFlanksResidualZ_M": stats(flank_residual),
        "centerMinusFlanksMedianResidualZ_M": float(np.median(center_residual) - np.median(flank_residual)),
        "centerMeanBoneWeights": {n: float(weights[center, i].mean()) for i, n in enumerate(names) if weights[center, i].sum() > 0},
        "flankMeanBoneWeights": {n: float(weights[flanks, i].mean()) for i, n in enumerate(names) if weights[flanks, i].sum() > 0},
    }
    frames.append(row)
    print("LOCAL_ATTACHMENT_CAUSE", frame_id, "elbowLminSingular", row["regions"]["elbowMix.L"]["minimumBlendSingularValue"]["min"],
          "elbowRminSingular", row["regions"]["elbowMix.R"]["minimumBlendSingularValue"]["min"],
          "hemCenterMinusFlanksMm", row["hem"]["centerMinusFlanksMedianResidualZ_M"] * 1000, flush=True)
report = {
    "status": "UNACCEPTED readonly localized attachment/blend diagnosis at parent-played defects",
    "pins": pins, "recipeSHA256": sha(__file__), "diagnosticRegions": static, "frames": frames,
    "hemRestBestFitPlane": plane(rest[hem]),
    "hemCenterVertexIDs": center.tolist(), "hemFlankVertexIDs": flanks.tolist(),
    "frontHemDefinition": "Lowest-mean-Z actual degree2boundary loop; frontX>=medianX; center/flanks bottom/top quartiles of absnativeY within front.",
    "elbowShoulderRegionDefinition": "Existing four-field upperArm+forearm each>0.1 for elbow; chest+upperArm each>0.1 for shoulder. Diagnostic subsets only, not coverage/contact exclusions.",
    "zeroLengthMaterialEdges": int((~valid_edges).sum()),
    "decomposition": "Actual neighbor edge equals average bone-blend affine transform of rest edge plus difference between endpoint attachment fields at the rest midpoint. Pose matrices and actual endpoint positions reused from92; no source/pose edits. Smallest blend singular value describes local affine compression, not full spatial Jacobian/cloth thickness.",
    "limits": [
        "Localized diagnosis only, not a field repair or accepted causal intervention. Projection jump and bone-blend compression can coincide; neither alone certifies visible damage or clearance. Parentplayed93identified stiff shoulder/sleeve bulges, asymmetric elbow pinch and squatfronthem bow.",
        "Hem bestfit plane separates true nonplanarity from apparent tilt; pelvis-frame residuals are references, not underwear/body QA. No body/head/material/geometry/weight/rig source edits, newcapture or broadprojection/weight sweep.",
        "No engine admission, mask waiver, inference, worker, Library/player promotion/publication. All24coverage/cuffs/protectedhead baseline contacts/moving/M0-M5/mobile and exportednormals remain open.",
    ],
}
assert pins == {p: sha(p) for p in pins}
(out / "diagnosis.json").write_text(json.dumps(report, indent=2) + "\n")
print("LOCAL_SKIN_ATTACHMENT_DIAGNOSIS_READY", flush=True)
