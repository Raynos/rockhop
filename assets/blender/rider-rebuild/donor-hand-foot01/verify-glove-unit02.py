"""One bounded intended-final selected glove reconstruction; never player export."""
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
before = [(tuple(vertex.co), [(group.group, group.weight) for group in vertex.groups]) for vertex in body.data.vertices]
rest = [(bone.name, bone.parent.name if bone.parent else None, tuple(bone.head_local), tuple(bone.tail_local)) for bone in rig.data.bones]
helper = root / "assets/blender/rider-rebuild/donor-hand-foot01/build-selected-glove02.py"
unit = runpy.run_path(str(helper))["buildSelectedGloves"](body, rig, out)
assert before == [(tuple(vertex.co), [(group.group, group.weight) for group in vertex.groups]) for vertex in body.data.vertices]
assert rest == [(bone.name, bone.parent.name if bone.parent else None, tuple(bone.head_local), tuple(bone.tail_local)) for bone in rig.data.bones]
bpy.ops.wm.save_as_mainfile(filepath=str(out / "selected-glove-checkpoint.blend"))
report = {"accepted": False, "helperSHA256": hashlib.sha256(helper.read_bytes()).hexdigest(),
          "originalBodyPositionsFieldsAnd75RestUnchanged": True, "construction": unit["report"],
          "native": {"path": str(out / "selected-glove-checkpoint.blend"),
              "sha256": hashlib.sha256((out / "selected-glove-checkpoint.blend").read_bytes()).hexdigest()},
          "limits": ["Existing previous wardrobe remains only as native control; no candidate engine export or art acceptance"]}
(out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"accepted": False, "native": report["native"], "objects": unit["report"]["objects"]}))
