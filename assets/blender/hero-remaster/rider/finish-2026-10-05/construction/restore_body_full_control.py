"""Restore the retained FULL body control outside the authored neck seam.

No geometry, topology, material, normals, rest/binds or head weights change.
Source body04c records its mistaken conditioned canonical control separately.
"""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

owned = Path(__file__).resolve().parent
root = owned.parents[5]
source = owned / 'body04c/natural-foundation.blend'
fields = owned / 'body04c/authored-neck-fields.npz'
control = owned / 'body02/authored-neck-fields.npz'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source) == '1cdeb0fac48a16431dfb9f2f21e55d60c4ecc1ab7f5f82d948a49764e83db16a'
assert sha(fields) == '42a77a018bb62cf0a78262713b8a9f0294346c414b6a2614f467bec0d7ffe812'
assert sha(control) == '337c97875e39c4bc0f738a4886dbfd1c5a5b5b757cbc5965f120d43a4247271e'
out = owned / 'body04d'
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body04d'
native = out / 'natural-foundation.blend'
assert not native.exists()
n = dict(np.load(fields))
old = np.load(control)
original_count = 9037
seam = n['bodySeamPhysicalIDs'] >= 0
full = n['bodyFullWeights'].copy()
full[:original_count] = old['bodyFullWeights'][:original_count]
full[seam] = n['bodyFourWeights'][seam]
assert np.array_equal(full[:original_count][~seam[:original_count]], old['bodyFullWeights'][:original_count][~seam[:original_count]])
assert np.array_equal(full[seam], n['bodyFourWeights'][seam])
assert not np.array_equal(full, n['bodyFourWeights'])
bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.window.scene = bpy.data.scenes['Finish natural wearer diagnostic']
rig = bpy.data.objects['Finish rig']
names = [b.name for b in rig.data.bones]
obj = bpy.data.objects['Finish body FULL']
assert len(full) == len(obj.data.vertices)
before_xyz = np.array([v.co[:] for v in obj.data.vertices], np.float32)
before_normals = np.array([v.vector[:] for v in obj.data.corner_normals], np.float32)
for name in names:
    obj.vertex_groups[name].remove(list(range(len(full))))
for i, row in enumerate(full):
    for j in np.flatnonzero(row > 0):
        obj.vertex_groups[names[j]].add([i], float(row[j]), 'REPLACE')
assert np.array_equal(before_xyz, np.array([v.co[:] for v in obj.data.vertices], np.float32))
assert np.array_equal(before_normals, np.array([v.vector[:] for v in obj.data.corner_normals], np.float32))
read = np.zeros_like(full)
for v in obj.data.vertices:
    for group in v.groups:
        name = obj.vertex_groups[group.group].name
        if name in names:
            read[v.index, names.index(name)] = group.weight
assert np.array_equal(read, full)
n['bodyFullWeights'] = full
out.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
np.savez_compressed(out / 'authored-neck-fields.npz', **n)
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
report = {'status': 'UNACCEPTED_BODY04D_FULL_CONTROL_RESTORED_REQUIRES_QA', 'sourceSHA256': sha(source), 'native': str(native.relative_to(root)), 'nativeSHA256': sha(native), 'fieldsSHA256': sha(out / 'authored-neck-fields.npz'), 'recipeSHA256': sha(__file__), 'controlSHA256': sha(control), 'originalBodyRows': original_count, 'authoredOriginalSeamRows': int(seam[:original_count].sum()), 'originalFullControlOutsideSeamExact': True, 'geometryAndDecodedBodyNormalsUnchanged': True, 'bodyFullVersusFourDifferentRows': int(np.any(full != n['bodyFourWeights'], axis=1).sum()), 'headGeometryFieldsNormalsUnchanged': True, 'limits': ['No independent reopen/native manual parity/contact/art acceptance yet.', 'The unchanged body03 boxer clearance and source shoulder/hip faults remain open.', 'Restored FULL control is retained reference; production FOUR field remains unchanged.']}
(evidence / 'authoring.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
