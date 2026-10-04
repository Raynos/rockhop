"""Measure full/four actual native skin and contacts at all frozen FK samples."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

parser = argparse.ArgumentParser(description=__doc__)
for name in ["source", "field", "driver", "out"]:
    parser.add_argument("--" + name, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
source, field_path, driver_path, out = [Path(getattr(args, n)).resolve() for n in ["source", "field", "driver", "out"]]
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
pins = {str(p): sha(p) for p in [source, field_path, driver_path]}
assert pins[str(source)] == "4a0904b94a507f35590d1ec4ebfe763237fa5fb21fa189573842309cb776a0ad"
assert pins[str(driver_path)] == "8c40c42af362a8d3d8ae44d27a0b07570f600b26adc66d325239413f66c7625b"
driver = json.loads(driver_path.read_text())
data = np.load(field_path)
out.mkdir(parents=True, exist_ok=True)
assert not (out / "motion.json").exists()
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects["Independent anatomical foundation rig"]
bone_names = [b.name for b in rig.data.bones]
assert bone_names == data["boneNames"].tolist()
assert len(driver["frames"]) == 529 and set(driver["jointOrderNative"]) == set(bone_names)
variants = {
    "full": bpy.data.objects["Actual donor full-influence cage control, unaccepted"],
    "four": bpy.data.objects["Actual donor explicit native-four skin, unaccepted"],
}
targets = {
    "logicalBody": bpy.data.objects["Canonical anatomical body, baked adult hm08"],
    "displayBody": bpy.data.objects["Canonical body with hidden head interface"],
    "protectedHead": bpy.data.objects["Protected textured head above hidden neck interface"],
    "protectedCheek": bpy.data.objects["Protected coherent cheek patch"],
}
for obj in [rig] + list(variants.values()) + list(targets.values()):
    obj.hide_set(False)
bpy.context.view_layer.update()
weights = {key: data[key + "Weights"].astype(np.float64) for key in variants}
for values in weights.values():
    values /= values.sum(1)[:, None]
rest = data["nativeRestXYZ"]
rest_h = np.column_stack([rest, np.ones(len(rest))])
fixed_garment = data["triangles"]
fixed_targets = {}
for key, obj in targets.items():
    obj.data.calc_loop_triangles()
    fixed_targets[key] = np.array([t.vertices[:] for t in obj.data.loop_triangles])
def tree(points, triangles):
    return BVHTree.FromPolygons([Vector(p) for p in points], triangles.tolist(), all_triangles=True)
def surface(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    positions = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    triangles = np.array([t.vertices[:] for t in mesh.loop_triangles])
    evaluated.to_mesh_clear()
    return positions, triangles, tree(positions, triangles)
def nonadjacent(surface_tree, triangles):
    sets = [frozenset(row) for row in triangles]
    return [(i, j) for i, j in surface_tree.overlap(surface_tree) if i < j and sets[i].isdisjoint(sets[j])]
def stats(values):
    return {"maxM": float(values.max()), "p95M": float(np.percentile(values, 95)), "p50M": float(np.percentile(values, 50))}
world = np.array(rig.matrix_world)
all_records = []
skin_matrices = []
sample_ids, full_positions, four_positions = [], [], []
start = time.monotonic()
worst = {"maxM": -1}
for frame in driver["frames"]:
    for name, trs in frame["poseBasisBlender"].items():
        bone = rig.pose.bones[name]
        bone.rotation_mode = "QUATERNION"
        bone.location = trs["location"]
        bone.rotation_quaternion = trs["quaternionWXYZ"]
        bone.scale = trs["scale"]
    bpy.context.view_layer.update()
    matrices = np.array([np.array(rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()) for n in bone_names])
    skin_matrices.append(matrices)
    target_surfaces = {key: surface(obj) for key, obj in targets.items()}
    target_fixed_trees = {
        key: tree(positions, fixed_targets[key]) if not np.array_equal(triangles, fixed_targets[key]) else native_tree
        for key, (positions, triangles, native_tree) in target_surfaces.items()
    }
    record = {
        "frame": frame["index"], "timeS": frame["timeS"], "endpoint": frame["endpoint"],
        "segment": frame["segment"], "variants": {},
        "targetRetessellatedTriangleRows": {
            key: int(np.any(triangles != fixed_targets[key], axis=1).sum())
            for key, (positions, triangles, native_tree) in target_surfaces.items()
        },
    }
    evaluated_positions = {}
    for key, obj in variants.items():
        positions, triangles, native_tree = surface(obj)
        assert np.isfinite(positions).all()
        evaluated_positions[key] = positions
        manual = (np.einsum("vj,jab,vb->va", weights[key], matrices, rest_h, optimize=True) @ world.T)[:, :3]
        parity = np.linalg.norm(manual - positions, axis=1)
        assert parity.max() < 3e-6, (key, frame["index"], parity.max())
        retessellation = int(np.any(triangles != fixed_garment, axis=1).sum())
        fixed_tree = tree(positions, fixed_garment) if retessellation else native_tree
        native_self = nonadjacent(native_tree, triangles)
        fixed_self = nonadjacent(fixed_tree, fixed_garment) if retessellation else native_self
        contacts = {}
        for target_key, (target_positions, target_triangles, target_tree) in target_surfaces.items():
            native_pairs = native_tree.overlap(target_tree)
            fixed_pairs = fixed_tree.overlap(target_fixed_trees[target_key]) if retessellation or record["targetRetessellatedTriangleRows"][target_key] else native_pairs
            contacts[target_key] = {
                "nativeTrianglePairs": len(native_pairs), "fixedExportTrianglePairs": len(fixed_pairs),
                "firstNativeWitnesses": native_pairs[:8], "firstFixedWitnesses": fixed_pairs[:8],
            }
        record["variants"][key] = {
            "manualLBSParity": stats(parity), "retessellatedTriangleRows": retessellation,
            "nativeSelfPairs": len(native_self), "fixedExportSelfPairs": len(fixed_self),
            "firstNativeSelfWitnesses": native_self[:8], "firstFixedSelfWitnesses": fixed_self[:8],
            "contacts": contacts,
        }
    loss = np.linalg.norm(evaluated_positions["four"] - evaluated_positions["full"], axis=1)
    record["actualFullVsFourDeformationLoss"] = stats(loss)
    record["maximumLossVertex"] = int(np.argmax(loss))
    if loss.max() > worst["maxM"]:
        vertex = int(np.argmax(loss))
        worst = {
            "frame": frame["index"], "timeS": frame["timeS"], "vertex": vertex, "maxM": float(loss.max()),
            "nativeRestXYZ": rest[vertex].tolist(),
            "fullWorldXYZ": evaluated_positions["full"][vertex].tolist(),
            "fourWorldXYZ": evaluated_positions["four"][vertex].tolist(),
            "fullBoneWeights": {bone_names[i]: float(v) for i, v in enumerate(weights["full"][vertex]) if v},
            "fourBoneWeights": {bone_names[i]: float(v) for i, v in enumerate(weights["four"][vertex]) if v},
        }
        worst_arrays = (evaluated_positions["full"].copy(), evaluated_positions["four"].copy())
    if frame["endpoint"]:
        sample_ids.append(frame["index"])
        full_positions.append(evaluated_positions["full"])
        four_positions.append(evaluated_positions["four"])
    all_records.append(record)
    if frame["index"] % 24 == 0:
        print("NATIVE_DONOR_FOUR_MEASURE", frame["index"], "lossMm", round(loss.max() * 1000, 6),
              "fourLogical", record["variants"]["four"]["contacts"]["logicalBody"]["nativeTrianglePairs"],
              "fourSelf", record["variants"]["four"]["nativeSelfPairs"],
              "elapsedS", round(time.monotonic() - start, 1), flush=True)
summaries = {}
for key in variants:
    summaries[key] = {
        "maximumNativeSelfPairs": max(r["variants"][key]["nativeSelfPairs"] for r in all_records),
        "maximumFixedExportSelfPairs": max(r["variants"][key]["fixedExportSelfPairs"] for r in all_records),
        "nativeSelfContactFrames": sum(r["variants"][key]["nativeSelfPairs"] > 0 for r in all_records),
        "fixedSelfContactFrames": sum(r["variants"][key]["fixedExportSelfPairs"] > 0 for r in all_records),
        "maximumManualLBSParityM": max(r["variants"][key]["manualLBSParity"]["maxM"] for r in all_records),
        "targets": {
            target: {
                "maximumNativePairs": max(r["variants"][key]["contacts"][target]["nativeTrianglePairs"] for r in all_records),
                "maximumFixedExportPairs": max(r["variants"][key]["contacts"][target]["fixedExportTrianglePairs"] for r in all_records),
                "nativeContactFrames": sum(r["variants"][key]["contacts"][target]["nativeTrianglePairs"] > 0 for r in all_records),
                "fixedContactFrames": sum(r["variants"][key]["contacts"][target]["fixedExportTrianglePairs"] > 0 for r in all_records),
            } for target in targets
        },
    }
archive = out / "native-loss-witnesses.npz"
np.savez_compressed(
    archive, poseSkinMatricesNative=np.array(skin_matrices), rigWorldRows=world,
    sampledFrameIDs=np.array(sample_ids), fullActualWorld=np.array(full_positions, dtype=np.float32),
    fourActualWorld=np.array(four_positions, dtype=np.float32),
    worstFullActualWorld=worst_arrays[0], worstFourActualWorld=worst_arrays[1],
    worstLossFrame=np.array(worst["frame"]), boneNames=np.array(bone_names),
)
report = {
    "status": "UNACCEPTED full/four actual native continuous FK measurements; parent played proof pending",
    "pins": pins, "recipeSHA256": sha(__file__), "archiveSHA256": sha(archive),
    "sampleRateHz": 48, "measuredFrames": len(all_records), "elapsedS": time.monotonic() - start,
    "summaries": summaries, "worstActualFullVsFourLoss": worst, "frames": all_records,
    "limits": [
        "Actual evaluated Blender Armature full/four at every529 fixed48Hz synthetic FK sample. Native and frozen export-rest triangulations both measured, with logical body and protected display body/head/cheek kept separate. No mask exclusions or coverage waiver.",
        "Contacts are triangle witnesses, not signed depth/whole-volume containment or between-sample continuous collision proof. Surface fields inherit original body/head; this audit is garment contact, not Agent3 independent body/seam acceptance.",
        "Weight loss reported separately from actual posed deformation loss. Manual51bone LBS parity verifies actual evaluator consumption, not exported glTF or actual game consumption.",
        "No source save, pose/weight repair, geometry shrink/rebuild/recolor/inference/worker/Library/player promotion/publication. All24coverage/cuffs/played wearing/M0-M5/mobile and export-engine normals remain open.",
    ],
}
assert pins == {p: sha(p) for p in pins}
(out / "motion.json").write_text(json.dumps(report, indent=2) + "\n")
print("NATIVE_DONOR_FULL_FOUR_COMPLETE", json.dumps(summaries), "worstLossM", worst["maxM"], flush=True)
