"""Play the failed native-four candidate under the measured FK driver."""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

parser = argparse.ArgumentParser(description=__doc__)
for name in ["source", "field", "driver", "measurement", "out"]:
    parser.add_argument("--" + name, required=True)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
source, field_path, driver_path, measurement, out = [
    Path(getattr(args, n)).resolve() for n in ["source", "field", "driver", "measurement", "out"]
]
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
measured = json.loads(measurement.read_text())
pins = {str(p): sha(p) for p in [source, field_path, driver_path, measurement]}
assert all(measured["pins"][p] == digest for p, digest in pins.items() if p != str(measurement))
out.mkdir(parents=True, exist_ok=True)
assert not (out / "review.json").exists()
driver = json.loads(driver_path.read_text())
field = np.load(field_path)
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.context.scene
rig = bpy.data.objects["Independent anatomical foundation rig"]
garment = bpy.data.objects["Actual donor explicit native-four skin, unaccepted"]
wearer = [
    bpy.data.objects[n] for n in [
        "Canonical body with hidden head interface",
        "Protected textured head above hidden neck interface",
        "Protected coherent cheek patch", "Opaque boxer fitting garment",
    ]
]
for obj in scene.objects:
    if obj.type in ["MESH", "LIGHT", "FONT"]:
        obj.hide_render = True
for obj in [rig, garment] + wearer:
    obj.hide_set(False)
for obj in [garment] + wearer:
    obj.hide_render = False
world = bpy.data.worlds.new("Native donor proof neutral studio")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (.075, .075, .075, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = .65
scene.world = world
target = Vector((.65, 0, 1.30))
for name, position, energy in [("Key", (4, -4, 5), 700), ("Fill", (-3, 4, 4), 600), ("Top", (.65, 0, 5), 400)]:
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size = energy, 4
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
camera_data = bpy.data.cameras.new("Native donor proof fixed camera")
camera_data.type, camera_data.ortho_scale = "ORTHO", 2.8
camera = bpy.data.objects.new(camera_data.name, camera_data)
bpy.context.collection.objects.link(camera)
scene.camera = camera
white = bpy.data.materials.new("Native proof legend")
white.use_nodes = True
nodes = white.node_tree.nodes
nodes.clear()
emission = nodes.new("ShaderNodeEmission")
emission.inputs[0].default_value = (1, 1, 1, 1)
output = nodes.new("ShaderNodeOutputMaterial")
white.node_tree.links.new(emission.outputs[0], output.inputs["Surface"])
font = bpy.data.curves.new("Native proof legend", "FONT")
font.size = .036
font.materials.append(white)
legend = bpy.data.objects.new(font.name, font)
bpy.context.collection.objects.link(legend)
legend.parent = camera
legend.location = (-1.32, 1.30, -2)
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 8
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = "FIXED", 2
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
variants = [
    {"key": "front", "label": "FRONT", "yaw": 0},
    {"key": "side", "label": "SIDE", "yaw": -math.pi / 2},
    {"key": "rear", "label": "REAR", "yaw": math.pi},
]
for variant in variants:
    (out / variant["key"]).mkdir(exist_ok=True)
bone_names = field["boneNames"].tolist()
weights = field["fourWeights"].astype(np.float64)
weights /= weights.sum(1)[:, None]
rest_h = np.column_stack([field["nativeRestXYZ"], np.ones(len(weights))])
world_rows = np.array(rig.matrix_world)
frame_ids = list(range(0, 529, 4))
assert frame_ids[-1] == 528
frames = []
started = time.monotonic()
for display_index, frame_id in enumerate(frame_ids):
    row = driver["frames"][frame_id]
    record = measured["frames"][frame_id]
    for name, trs in row["poseBasisBlender"].items():
        bone = rig.pose.bones[name]
        bone.rotation_mode = "QUATERNION"
        bone.location, bone.rotation_quaternion, bone.scale = trs["location"], trs["quaternionWXYZ"], trs["scale"]
    bpy.context.view_layer.update()
    skin = np.array([np.array(rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()) for n in bone_names])
    manual = (np.einsum("vj,jab,vb->va", weights, skin, rest_h, optimize=True) @ world_rows.T)[:, :3]
    evaluated = garment.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    actual_world = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    evaluated.to_mesh_clear()
    parity = float(np.linalg.norm(manual - actual_world, axis=1).max())
    assert parity < 3e-6
    views = []
    for variant in variants:
        yaw = variant["yaw"]
        camera.location = target + Vector((4 * math.cos(yaw), 4 * math.sin(yaw), .30))
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        phase = row["endpoint"] or " TO ".join(row["segment"])
        four = record["variants"]["four"]
        font.body = (
            f"FAILED NATIVE FOUR / {variant['label']} / FK {frame_id}/528\n"
            f"{phase.upper()} / {row['timeS']:.3f}s\n"
            f"BODY {four['contacts']['logicalBody']['nativeTrianglePairs']} / HEAD {four['contacts']['protectedHead']['nativeTrianglePairs']} / SELF {four['nativeSelfPairs']}\n"
            "PARENT JUDGES / COVERAGE+MOVING GATES OPEN"
        )
        scene.render.filepath = str(out / variant["key"] / f"{display_index:04d}.png")
        bpy.ops.render.render(write_still=True)
        views.append({
            "variant": variant["key"], "PNG_SHA256": sha(scene.render.filepath),
            "cameraWorldRows": [list(r) for r in camera.matrix_world],
        })
    frames.append({
        "index": display_index, "driverFrame": frame_id, "timeS": row["timeS"],
        "endpoint": row["endpoint"], "segment": row["segment"], "manualLBSParityMaxM": parity,
        "garmentWorldBounds": [actual_world.min(0).tolist(), actual_world.max(0).tolist()], "views": views,
    })
    if display_index % 8 == 0:
        print("NATIVE_DONOR_PLAYED_PROOF", display_index, "driver", frame_id, "elapsedS", round(time.monotonic() - started, 1), flush=True)
report = {
    "status": "UNACCEPTED failed native-four played FK proof; parent alone judges",
    "pins": pins, "recipeSHA256": sha(__file__), "variants": variants, "frames": frames,
    "movieFrameSequence": list(range(len(frames))), "sourceFramesPerSecond": 12,
    "durationS": len(frames) / 12,
    "render": "Actual evaluated Blender native-four skin/immutable protected body-head-cheek/opaque underwear; original donor UV/PBR/tested30degree normals. Fixed front/side/rear640square neutralstudio/CyclesCPU2threads8samples/AgX/orthographic2.8m/targetZ1.30. No source save or posed substitute.",
    "limits": [
        "Failed native measurements visible via white text only, no body/garment recolor or corrective trajectory. Head counts are raw contact witnesses, not body/seam diagnoses.",
        "Every fourth52948Hz sample rendered at12fps; measurement still covers every529sample. No motion interpolation or artificial pose holds. Synthetic FK, not actual bike controller/support input.",
        "Full control preserved with quantitative loss report; clip shows only native-four from three fixed angles. All24coverage/cuffs/appearance/M0-M5/mobile and export-engine normal consumption remain open.",
        "No rest recapture/gallery, geometry/weight retry, new body, inference, worker, Library/player promotion/publication. Parent must play before any next field decision.",
    ],
}
assert pins == {p: sha(p) for p in pins}
(out / "review.json").write_text(json.dumps(report, indent=2) + "\n")
print("NATIVE_DONOR_PLAYED_PROOF_READY", flush=True)
