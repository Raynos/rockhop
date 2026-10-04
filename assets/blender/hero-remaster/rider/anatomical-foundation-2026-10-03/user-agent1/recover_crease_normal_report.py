"""Verify the already saved normal candidate without overwriting its bytes."""
import hashlib
import json
from pathlib import Path

executed = Path(__file__).with_name("selected-hoodie25") / "reopen-reference-rejected.py"
code = executed.read_text()
changes = {
    'assert not native.exists() and not (out / "report.json").exists()':
        'assert native.exists() and not (out / "report.json").exists()',
    'materials = tuple(mesh.materials)':
        'materials = tuple(mesh.materials)\nmaterial_names = [m.name for m in materials]',
    'bpy.ops.wm.save_as_mainfile(filepath=str(native))':
        '# Report-only recovery: original saved native is never overwritten.',
    'assert [m.name for m in mesh.materials] == [m.name for m in materials]':
        'assert [m.name for m in mesh.materials] == material_names',
}
for old, new in changes.items():
    assert code.count(old) == 1
    code = code.replace(old, new)
exec(compile(code, str(executed), "exec"))
report["failedExecutedRecipeSHA256"] = sha(executed)
report["reportOnlyRecoveryRecipeSHA256"] = sha(__file__)
report["recovery"] = {
    "cause": "Original save and reopened normal-buffer assertions passed, then material-name metadata tried to access pre-reload Blender RNA references.",
    "fix": "Capture scalar material names before reload; repeat exact native/protected assertions against the existing candidate, never save it again.",
    "candidateNeverOverwritten": True,
}
assert candidate_sha == sha(native)
(out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print("CREASE_NORMAL_REPORT_ONLY_RECOVERY_PASS", candidate_sha, flush=True)
