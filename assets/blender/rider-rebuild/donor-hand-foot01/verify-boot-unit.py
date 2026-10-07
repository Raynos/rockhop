"""One bounded selected-source boot checkpoint; never a player export."""
import hashlib
import json
import runpy
import sys
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[4]
native = root / "harness/out/rider-rebuild/construction01/combined04/rider-assembled.blend"
assert hashlib.sha256(native.read_bytes()).hexdigest() == "26cd01d4ba02be3fbf0f3a5b290c99445ef34d7d18d90012d2ef44913ef06d1d"
out = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
out.mkdir(parents=True, exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(native))
body, rig = bpy.data.objects["RiderBody"], bpy.data.objects["RiderSkeleton"]
before = [(tuple(v.co), [(g.group, g.weight) for g in v.groups]) for v in body.data.vertices]
before_rest = [(b.name, b.parent.name if b.parent else None, tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones]
helper = root / "assets/blender/rider-rebuild/donor-hand-foot01/build-hand-foot.py"
unit = runpy.run_path(str(helper))["buildHandFoot"](body, rig, out)
assert before == [(tuple(v.co), [(g.group, g.weight) for g in v.groups]) for v in body.data.vertices]
assert before_rest == [(b.name, b.parent.name if b.parent else None, tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones]
rows = []
for obj in unit["objects"]:
    fields = [[g.weight for g in vertex.groups] for vertex in obj.data.vertices]
    assert all(1 <= len(row) <= 4 and abs(sum(row) - 1) < 2e-6 for row in fields)
    assert obj.parent == rig and len([m for m in obj.modifiers if m.type == "ARMATURE" and m.object == rig]) == 1
    obj.data.calc_loop_triangles()
    rows.append({"name": obj.name, "vertices": len(obj.data.vertices), "triangles": len(obj.data.loop_triangles),
                 "fieldSumResidual": max(abs(sum(row) - 1) for row in fields),
                 "bounds": [[min(v.co[k] for v in obj.data.vertices), max(v.co[k] for v in obj.data.vertices)] for k in range(3)],
                 "UVLoops": len(obj.data.uv_layers.active.data)})
bpy.ops.wm.save_as_mainfile(filepath=str(out / "selected-boot-checkpoint.blend"))
report = {"accepted": False, "helperSHA256": hashlib.sha256(helper.read_bytes()).hexdigest(),
          "sourceNativeSHA256": hashlib.sha256(native.read_bytes()).hexdigest(),
          "originalBodyPositionsAndFieldsUnchanged": True, "original75RestHierarchyUnchanged": True,
          "objects": rows, "native": {"path": str(out / "selected-boot-checkpoint.blend"),
              "sha256": hashlib.sha256((out / "selected-boot-checkpoint.blend").read_bytes()).hexdigest()},
          "limits": ["Existing previous wardrobe remains in the control native; no combined candidate export or moving art claim",
                     "Glove source requires its own structural repair before production integration"]}
(out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
