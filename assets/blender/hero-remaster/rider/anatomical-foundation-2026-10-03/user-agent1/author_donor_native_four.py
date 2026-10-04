"""Author a measured cage attachment field and explicit native-four candidate.

This is an unaccepted skin experiment: immutable structural cage ancestry,
full-influence native control, and actual four-membership native derivative.
No geometry repair, nearest-body sweep, or hidden runtime weight truncation.
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

parser = argparse.ArgumentParser(description=__doc__)
for name in ["source", "out", "evidence"]:
    parser.add_argument("--" + name, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
source, out, evidence = [Path(getattr(args, name)).resolve() for name in ["source", "out", "evidence"]]
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(source) == "c732d98076f6b9b1a209a45e8a0cddf793484807ea8b3ae9011fa4f82c151df0"
out.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
native = out / "native-four-with-full-control.blend"
assert not native.exists()
extended = Path(__file__).with_name("verify_extended_protected_data.py")
definitions = extended.read_text()
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(definitions[definitions.index("def value("):definitions.index("before=snapshot(original)")], str(extended), "exec"), helpers)
pins = {str(p): sha(p) for p in [source, extended]}
bpy.ops.wm.open_mainfile(filepath=str(source))
original = bpy.data.objects["Actual selected donor, compact interior flow, unaccepted"]
pattern = bpy.data.objects["Separate fitted sweatshirt control, hood not constructed"]
rig = bpy.data.objects["Independent anatomical foundation rig"]
bone_names = [bone.name for bone in rig.data.bones]
assert len(bone_names) == 51
protected_names = [
    "Canonical anatomical body, baked adult hm08", "Canonical body with hidden head interface",
    "Full native diagnostic body", "Protected textured head above hidden neck interface",
    "Protected coherent cheek patch", "Protected mustard hood on own rig",
    "Opaque boxer fitting garment", pattern.name,
]
def state(obj):
    return {
        "object": helpers["object_state"](obj), "mesh": helpers["mesh_extra"](obj.data),
        "positions": helpers["array_digest"](obj.data.vertices, "co", 3),
        "polygons": [list(p.vertices) for p in obj.data.polygons],
        "weights": [[[obj.vertex_groups[g.group].name, float(g.weight)] for g in v.groups] for v in obj.data.vertices],
        "materials": [m.name if m else None for m in obj.data.materials],
    }
def protected():
    return {
        "objects": {name: state(bpy.data.objects[name]) for name in protected_names},
        "rigObject": helpers["object_state"](rig),
        "rigData": helpers["properties"](rig.data),
        "pose": {
            b.name: {"matrix": helpers["value"](b.matrix), "basis": helpers["value"](b.matrix_basis),
                     "properties": helpers["properties"](b), "constraints": [helpers["properties"](c) for c in b.constraints]}
            for b in rig.pose.bones
        },
    }
before = protected()
original_state = state(original)
assert not original.vertex_groups and not original.modifiers
rest = np.array([v.co[:] for v in original.data.vertices])
pattern_xyz = np.array([v.co[:] for v in pattern.data.vertices])
pattern.data.calc_loop_triangles()
pattern_faces = np.array([t.vertices[:] for t in pattern.data.loop_triangles])
# Both native meshes already use the same immutable rig/file frame.
assert np.array_equal(np.array(original.matrix_world), np.array(pattern.matrix_world))
cage = np.zeros((len(pattern_xyz), 51), dtype=np.float64)
for vertex in pattern.data.vertices:
    for membership in vertex.groups:
        name = pattern.vertex_groups[membership.group].name
        if name in bone_names and rig.data.bones[name].use_deform and membership.weight > 0:
            cage[vertex.index, bone_names.index(name)] = membership.weight
assert np.min(cage.sum(1)) > 0
cage /= cage.sum(1)[:, None]
tree = BVHTree.FromPolygons([Vector(point) for point in pattern_xyz], pattern_faces.tolist(), all_triangles=True)
ancestry, barycentrics, distances = [], [], []
full = np.zeros((len(rest), 51), dtype=np.float64)
for i, point in enumerate(rest):
    nearest, normal, triangle, distance = tree.find_nearest(Vector(point))
    ids = pattern_faces[triangle]
    positions = pattern_xyz[ids]
    uv = np.linalg.lstsq(np.column_stack([positions[1] - positions[0], positions[2] - positions[0]]), np.array(nearest) - positions[0], rcond=None)[0]
    bary = np.clip([1 - uv.sum(), uv[0], uv[1]], 0, 1)
    bary /= bary.sum()
    full[i] = bary @ cage[ids]
    ancestry.append(int(triangle))
    barycentrics.append(bary)
    distances.append(float(distance))
assert np.min(full.sum(1)) > 0 and np.isfinite(full).all()
full /= full.sum(1)[:, None]
four = np.zeros_like(full)
removed = []
for i, weights in enumerate(full):
    ordered = sorted(np.flatnonzero(weights > 0), key=lambda joint: (-weights[joint], joint))
    chosen = ordered[:4]
    removed.append(float(weights[ordered[4:]].sum()))
    four[i, chosen] = weights[chosen] / weights[chosen].sum()
candidates = []
actual_fields = []
for label, name, weights in [
    ("full", "Actual donor full-influence cage control, unaccepted", full),
    ("four", "Actual donor explicit native-four skin, unaccepted", four),
]:
    obj = original.copy()
    obj.data = original.data.copy()
    obj.name = name
    bpy.context.collection.objects.link(obj)
    groups = [obj.vertex_groups.new(name=bone) for bone in bone_names]
    for i, row in enumerate(weights):
        for joint in np.flatnonzero(row > 0):
            groups[joint].add([i], float(row[joint]), "REPLACE")
    actual_weights = np.zeros_like(weights, dtype=np.float32)
    for vertex in obj.data.vertices:
        for member in vertex.groups:
            actual_weights[vertex.index, member.group] = member.weight
    assert np.max(np.abs(actual_weights.sum(1) - 1)) < 1e-6
    if label == "four":
        assert np.max((actual_weights > 0).sum(1)) <= 4
    skin = obj.modifiers.new("Authored actual donor " + label + " influence skin", "ARMATURE")
    skin.object = rig
    skin.use_deform_preserve_volume = False
    assert np.array_equal(np.array([v.co[:] for v in obj.data.vertices]), rest)
    assert helpers["mesh_extra"](obj.data) == original_state["mesh"]
    assert [list(p.vertices) for p in obj.data.polygons] == original_state["polygons"]
    assert tuple(obj.data.materials) == tuple(original.data.materials)
    obj.hide_render = label != "four"
    obj.hide_set(label != "four")
    candidates.append({"label": label, "object": obj.name})
    actual_fields.append(actual_weights)
original.hide_render = True
original.hide_set(True)
assert protected() == before
assert state(original) == original_state
field_path = out / "authored-fields.npz"
original.data.calc_loop_triangles()
triangles = np.array([t.vertices[:] for t in original.data.loop_triangles])
np.savez_compressed(
    field_path, nativeRestXYZ=rest, triangles=triangles, boneNames=np.array(bone_names),
    fullWeights=actual_fields[0], fourWeights=actual_fields[1],
    patternTriangleID=np.array(ancestry), patternBarycentric=np.array(barycentrics),
    patternDistanceM=np.array(distances), removedWeightMass=np.array(removed),
    patternNativeXYZ=pattern_xyz, patternTriangles=pattern_faces, patternFullWeights=cage,
)
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
candidate_sha = sha(native)
# Reopen actual saved native memberships and verify the full/four contract.
bpy.ops.wm.open_mainfile(filepath=str(native))
rig = bpy.data.objects["Independent anatomical foundation rig"]
original = bpy.data.objects["Actual selected donor, compact interior flow, unaccepted"]
assert protected() == before
assert state(original) == original_state
for candidate, expected in zip(candidates, actual_fields):
    obj = bpy.data.objects[candidate["object"]]
    measured = np.zeros_like(expected)
    for vertex in obj.data.vertices:
        for member in vertex.groups:
            measured[vertex.index, member.group] = member.weight
    assert np.array_equal(measured, expected)
    assert np.array_equal(np.array([v.co[:] for v in obj.data.vertices]), rest)
    assert helpers["mesh_extra"](obj.data) == original_state["mesh"]
assert pins == {p: sha(p) for p in pins}
l1 = np.abs(actual_fields[0].astype(np.float64) - actual_fields[1]).sum(1)
report = {
    "status": "UNACCEPTED authored cage-field native full-control/four candidate; moving qualification pending",
    "pins": pins, "recipeSHA256": sha(__file__), "candidate": str(native),
    "candidateSHA256": candidate_sha, "field": str(field_path), "fieldSHA256": sha(field_path),
    "objects": candidates, "vertices": len(rest), "triangles": len(triangles),
    "fullInfluenceHistogram": dict(collections.Counter(map(int, (actual_fields[0] > 0).sum(1)))),
    "fourInfluenceHistogram": dict(collections.Counter(map(int, (actual_fields[1] > 0).sum(1)))),
    "removedWeightMassPercentiles": np.percentile(removed, [0, 50, 95, 100]).tolist(),
    "actualFullVsFourWeightL1Percentiles": np.percentile(l1, [0, 50, 95, 100]).tolist(),
    "patternAncestryDistancePercentilesM": np.percentile(distances, [0, 50, 95, 100]).tolist(),
    "protectedMeshesIncludingCageExact": len(protected_names), "protectedPoseBonesExact": 51,
    "source25GeometryNormalsUVMaterialExact": True, "nativeSavedReopenedMembershipsExact": True,
    "construction": "One fixed nearest-triangle barycentric attachment to immutable1250vertex structural garment cage, not nearest body. Capture all three cage vertices/weights as full field, then stable weight-descending/bone-order top4 and normalize. Native memberships stored Float32 and verified after actual reopen.",
    "limits": [
        "Cage attachment is a provisional authored field, not accepted legacy template skin. No geometry from failed13/14 is reused. Hood/armhole/cuff behavior must be judged and measured; spatial nearest cage can misattach surfaces and is not a wearing certificate.",
        "Weight-mass/L1 loss only here; actual deformation full-versus-four loss across529native pose samples and native body/self/coverage/played proof are next, before independentAgent3actual-engine verification.",
        "All24coverage/cuffs/moving appearance/M0-M5/mobile and actual export-engine normals remain open. Parentrest89allows this bounded qualification, not art acceptance.",
        "Source24flat/source25normals/all originals/body-head-original51bind preserved. No geometry shrink/rebuild/recolor/newbody/inference/worker/Library upload/player promotion/publication.",
    ],
}
(evidence / "skin.json").write_text(json.dumps(report, indent=2) + "\n")
print("DONOR_NATIVE_FOUR_AUTHORED", candidate_sha, report["fullInfluenceHistogram"], report["fourInfluenceHistogram"], report["removedWeightMassPercentiles"], flush=True)
