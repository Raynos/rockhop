"""Read back every volume witness of the failed frozen candidate; no construction."""
import hashlib
import json
import sys
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[4]
recipe = root / "assets/blender/rider-rebuild/donor-hand-foot01/build-selected-glove.py"
expected = "3c67ed274a934ec6fbf46fbe48d8dc6a57ad94db0169b581f765be4ec2fccf62"
assert hashlib.sha256(recipe.read_bytes()).hexdigest() == expected
native = root / "harness/out/rider-rebuild/construction01/combined04/rider-assembled.blend"
assert hashlib.sha256(native.read_bytes()).hexdigest() == "26cd01d4ba02be3fbf0f3a5b290c99445ef34d7d18d90012d2ef44913ef06d1d"
out = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
out.mkdir(parents=True, exist_ok=False)
source = recipe.read_text()
gate = '            assert max(scales) <= 2.5, "Selected branch cannot faithfully enclose actual hand volume"'
replacement = '            diagnostic_failures.append({"region": int(region), "digit": digit or "palm/wrist", "station": float(station), "selectedRadiiM": selected_radii, "actualSkinRadiiM": wearer_radii, "requiredScales": scales, "failsOriginalMaximum2_5": max(scales) > 2.5})'
assert source.count(gate) == 1
source = source.replace(gate, replacement)
marker = '    source_points = [Vector(point) for point in fitted]'
assert source.count(marker) == 1
source = source.replace(marker, '    raise DiagnosticComplete()\n' + marker)
class DiagnosticComplete(Exception):
    pass
namespace = {"__file__": str(recipe), "diagnostic_failures": [], "DiagnosticComplete": DiagnosticComplete}
exec(compile(source, str(recipe), "exec"), namespace)
bpy.ops.wm.open_mainfile(filepath=str(native))
body, rig = bpy.data.objects["RiderBody"], bpy.data.objects["RiderSkeleton"]
before = [(tuple(vertex.co), [(group.group, group.weight) for group in vertex.groups]) for vertex in body.data.vertices]
try:
    namespace["buildSelectedGloves"](body, rig, out)
    raise AssertionError("Diagnostic must stop before exterior projection or bake")
except DiagnosticComplete:
    pass
assert before == [(tuple(vertex.co), [(group.group, group.weight) for group in vertex.groups]) for vertex in body.data.vertices]
report = {"accepted": False, "diagnosticOnly": True, "sameFailedCandidateRecipeSHA256": expected,
          "originalProductionLimitUnchanged": 2.5, "bodyUnchanged": True,
          "projectionCavityAndBakeNotExecuted": True,
          "witnesses": namespace["diagnostic_failures"],
          "failures": [row for row in namespace["diagnostic_failures"] if row["failsOriginalMaximum2_5"]],
          "limits": ["Only the early assertion is recorded instead of aborting immediately; all source registration and section measurements are identical",
                     "No bound is relaxed and no production reconstruction is retried or saved"]}
(out / "all-volume-witnesses.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"diagnosticOnly": True, "witnesses": len(report["witnesses"]), "failures": report["failures"]}))
