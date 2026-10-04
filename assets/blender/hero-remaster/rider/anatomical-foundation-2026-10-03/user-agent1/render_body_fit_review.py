"""Inspect frozen source24 on the unchanged protected wearer and underwear."""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

parser = argparse.ArgumentParser(description=__doc__)
for name in ["source", "reuse-review", "coverage", "out"]:
    parser.add_argument("--" + name, required=True)
parser.add_argument("--prepare-only", action="store_true")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
source, reuse, coverage, out = [
    Path(getattr(args, name.replace("-", "_"))).resolve()
    for name in ["source", "reuse-review", "coverage", "out"]
]
digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
old = json.loads(reuse.read_text())
witnesses = json.loads(coverage.read_text())["allCoverageMissWitnesses"]
assert len(witnesses) == 24
setup = Path(__file__).with_name("render_actual_donor_rest_review.py")
assert digest(setup) == old["recipeSHA256"]
assert digest(source) == old["nativeCandidateSHA256"]
assert all(digest(path) == expected for path, expected in old["pins"].items())
registration = next(Path(p) for p in old["pins"] if p.endswith("/construct_selected_hoodie.py"))
transfer = next(Path(p) for p in old["pins"] if p.endswith("/repair_selected_texture_transfer.py"))
extended = Path(__file__).with_name("verify_extended_protected_data.py")
definitions = extended.read_text()
namespace = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(definitions[definitions.index("def value("):definitions.index("before=snapshot(original)")], str(extended), "exec"), namespace)
bpy.ops.wm.open_mainfile(filepath=str(source))
protected_names = [
    "Canonical anatomical body, baked adult hm08",
    "Canonical body with hidden head interface",
    "Full native diagnostic body",
    "Protected textured head above hidden neck interface",
    "Protected coherent cheek patch",
    "Protected mustard hood on own rig",
    "Opaque boxer fitting garment",
]
def state(obj):
    return {
        "object": namespace["object_state"](obj),
        "mesh": namespace["mesh_extra"](obj.data),
        "positions": namespace["array_digest"](obj.data.vertices, "co", 3),
        "polygonVertices": [list(p.vertices) for p in obj.data.polygons],
        "materials": [m.name if m else None for m in obj.data.materials],
    }
before = {name: state(bpy.data.objects[name]) for name in protected_names}
rig_name = "Independent anatomical foundation rig"
pose_before = {b.name: [list(row) for row in b.matrix] for b in bpy.data.objects[rig_name].pose.bones}
cheek_visible = not bpy.data.objects["Protected coherent cheek patch"].hide_render
# Reuse only the frozen neutral studio setup, never its render loop/save.
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [
    "--source", str(source), "--registration-recipe", str(registration),
    "--transfer-recipe", str(transfer), "--out", str(out),
]
code = setup.read_text()
exec(compile(code[:code.index("for index in range(48):")], str(setup), "exec"))
pins = {str(p): digest(p) for p in [source, reuse, coverage, setup, registration, transfer, extended]}
wearer_names = [
    "Canonical body with hidden head interface",
    "Protected textured head above hidden neck interface",
    "Opaque boxer fitting garment",
]
if cheek_visible:
    wearer_names.append("Protected coherent cheek patch")
wearer = [bpy.data.objects[name] for name in wearer_names]
display_body = wearer[0]
evaluations = {}
for obj in wearer + [actual]:
    obj.hide_set(False)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
for obj in wearer + [actual]:
    mesh = obj.evaluated_get(depsgraph).to_mesh()
    assert len(mesh.vertices) == len(obj.data.vertices)
    original_xyz = np.array([v.co[:] for v in obj.data.vertices])
    evaluated_xyz = np.array([v.co[:] for v in mesh.vertices])
    error = float(np.max(np.linalg.norm(original_xyz - evaluated_xyz, axis=1)))
    assert error < 1e-6, (obj.name, error)
    evaluations[obj.name] = {"vertices": len(mesh.vertices), "evaluatedRestMaxErrorM": error}
    obj.evaluated_get(depsgraph).to_mesh_clear()
display_xyz = np.array([v.co[:] for v in display_body.data.vertices])
logical_xyz = np.array([v.co[:] for v in body.data.vertices])
anchors = []
marker_objects = []
for witness in witnesses:
    point = np.array(witness["bodyXYZ"])
    assert np.array_equal(logical_xyz[witness["bodyVertex"]], point)
    distances = np.linalg.norm(display_xyz - point, axis=1)
    nearest = int(np.argmin(distances))
    assert distances[nearest] < 1e-6
    normal = np.array(witness["bodyNormal"])
    center = point + normal * .003
    world = display_body.matrix_world @ Vector(center)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=.0025, location=world)
    marker = bpy.context.object
    marker.name = "Coverage reference anchor " + str(witness["bodyVertex"])
    marker.data.materials.append(white)
    marker.hide_render = True
    marker_objects.append(marker)
    anchors.append({
        **witness, "protectedDisplayBodyVertex": nearest,
        "displayMappingErrorM": float(distances[nearest]),
        "markerCenterNativeXYZ": center.tolist(),
        "markerRadiusM": .0025, "markerNormalOffsetM": .003,
    })
variants = [
    {"key": "wearerReference", "label": "PROTECTED WEARER / OPAQUE UNDERWEAR", "markerOverlay": True},
    {"key": "fitted24", "label": "FROZEN FIT24 / SAME WEARER + UNDERWEAR", "markerOverlay": False},
]
for variant in variants:
    (out / variant["key"]).mkdir(exist_ok=True)
assert all(before[name] == state(bpy.data.objects[name]) for name in protected_names)
assert pose_before == {b.name: [list(row) for row in b.matrix] for b in rig.pose.bones}
assert len(pose_before) == 51
preparation = {
    "wearerObjects": wearer_names, "protectedMeshesExact": len(protected_names),
    "poseBonesExact": 51, "evaluatedRestGeometry": evaluations,
    "all24CoverageWitnesses": anchors, "sourcePins": pins,
}
(out / "preparation.json").write_text(json.dumps(preparation, indent=2) + "\n")
if args.prepare_only:
    print("BODY_FIT_PREPARATION_PASS", len(anchors), evaluations, flush=True)
    raise SystemExit(0)
frames = []
started = time.monotonic()
for index in range(48):
    old_frame = old["frames"][index]
    yaw = old_frame["yawRadians"]
    camera.location = target + Vector((4 * math.cos(yaw), 4 * math.sin(yaw), .30))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    assert np.array_equal(np.array([list(row) for row in camera.matrix_world]), np.array(old_frame["cameraWorldRows"]))
    projections = []
    for anchor in anchors:
        world = display_body.matrix_world @ Vector(anchor["bodyXYZ"])
        projected = world_to_camera_view(scene, camera, world)
        assert 0 <= projected.x <= 1 and 0 <= projected.y <= 1 and projected.z > 0
        projections.append({
            "bodyVertex": anchor["bodyVertex"],
            "referenceColumnPixelXY": [float(projected.x * 640), float((1 - projected.y) * 640)],
            "insideCameraFrame": True,
        })
    views = []
    for variant in variants:
        for obj in wearer:
            obj.hide_render = False
        actual.hide_render = variant["key"] != "fitted24"
        for marker in marker_objects:
            marker.hide_render = not variant["markerOverlay"]
        font.body = variant["label"] + (
            "\n24 WHITE REFERENCE ANCHORS / COVERAGE OPEN"
            if variant["markerOverlay"] else "\nCURRENT FLAT NORMALS / UNMARKED GARMENT"
        )
        scene.render.filepath = str(out / variant["key"] / f"{index:04d}.png")
        bpy.ops.render.render(write_still=True)
        views.append({"variant": variant["key"], "PNG_SHA256": digest(scene.render.filepath)})
    frames.append({
        "index": index, "yawRadians": yaw,
        "cameraWorldRows": [list(row) for row in camera.matrix_world],
        "all24WitnessProjections": projections, "views": views,
    })
    if index % 4 == 0:
        print("BODY_FIT_REVIEW", index, "elapsedS", round(time.monotonic() - started, 1), flush=True)
assert all(before[name] == state(bpy.data.objects[name]) for name in protected_names)
assert pose_before == {b.name: [list(row) for row in b.matrix] for b in rig.pose.bones}
assert pins == {p: digest(p) for p in pins}
record = {
    "status": "UNACCEPTED frozen source24 rest fit on protected wearer",
    "pins": pins, "recipeSHA256": digest(__file__),
    **preparation, "variants": variants, "frames": frames,
    "movieFrameSequence": old["movieFrameSequence"],
    "sourceFramesPerSecond": old["sourceFramesPerSecond"],
    "durationS": old["durationS"],
    "currentFlatGarmentFaces": len(actual.data.polygons),
    "garmentSmoothFaces": sum(p.use_smooth for p in actual.data.polygons),
    "render": "Exact85 camera/studio/CyclesCPU2threads8samples/AgX/640square; all48angles. Current flat24 original UV/PBR. Same assembled body/head/visible source cheek and opaque boxers in both columns.",
    "limits": [
        "All1937 historical rays and24misses remain unchanged/open. White spheres identify all24 exact body vertices in reference only; natural occlusion retained, not x-ray and not a claim each marker is visible at each angle. All24 in every camera frame.",
        "Reference markers are separate diagnostic geometry, 2.5mm radius and3mm outward normal offset. Fitted column has no markers/material recolor or geometry/normal adoption.",
        "Rest contextual appearance only; no sleeve shrink or clearance/ease acceptance. No source save, new body/rig/weights/motion/inference/worker/Library/player promotion/publication. Parent alone judges; allM0-M5/mobile open.",
        "Frame includes entire hoodie/head/underwear; lower legs outside garment framing. Logical full collision body is hidden; no duplicate logical head.",
    ],
}
(out / "review.json").write_text(json.dumps(record, indent=2) + "\n")
print("BODY_FIT_REVIEW_READY", flush=True)
