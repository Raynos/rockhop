"""One fixed dimensional dropped-hood repair, preserving source05 rig and wardrobe."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'construction', 'optional-handoff', 'out', 'evidence']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, construction, handoff, out, evidence = [Path(getattr(a, n.replace('-', '_'))).resolve() for n in ['source', 'construction', 'optional-handoff', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins = {str(p): sha(p) for p in [source, construction, handoff]}
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out / 'rider.blend').exists():
    raise RuntimeError('Frozen volume successor exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
root = bpy.data.objects['Foundation file frame, game x0.65']; rig = bpy.data.objects['Independent anatomical foundation rig']
hoodie = bpy.data.objects['Sewn clean hoodie with dropped hood']; mesh = hoodie.data
assert len(mesh.vertices) == 1385
record = json.loads(construction.read_text()); arc = record['sharedAttachmentArcIDs']; assert len(arc) == 17
neck = record['nativeNecklineVertices']; base = np.array([v.co[:] for v in mesh.vertices]); center = base[neck].mean(0)
angle = lambda i: math.atan2(base[i][1] - center[1], base[i][0] - center[0]) % (2 * math.pi)
first, last = angle(arc[0]), angle(arc[-1]); changes = []; index = 1250
# A dimensional open pouch: the middle cross-section hangs below the raised
# outer rim, giving a real concavity. This is one fixed authored profile.
for row in range(1, 7):
    t = row / 6
    for col, seam_id in enumerate(arc):
        if col in [0, len(arc) - 1]:
            continue
        phi = angle(seam_id); back = math.sin(math.pi * (phi - first) / (last - first))
        p = base[seam_id].copy()
        p[0] -= back * (.240 * t + .100 * math.sin(math.pi * t))
        p[1] += math.copysign((.035 * t + .035 * math.sin(math.pi * t)) * back, p[1]) if abs(p[1]) > 1e-5 else 0
        p[2] -= back * (.120 * t + .120 * math.sin(math.pi * t))
        delta = Vector(p - base[index]); changes.append({'vertexID': index, 'seamSourceID': seam_id, 'row': row, 'beforeNativeM': base[index].tolist(), 'afterNativeM': p.tolist()})
        mesh.vertices[index].co = Vector(p)
        for key in mesh.shape_keys.key_blocks:
            key.data[index].co += delta
        index += 1
assert index == 1340 and len(changes) == 90
for key in mesh.shape_keys.key_blocks:
    key.value = 0
mesh.update(); bpy.context.view_layer.update()
current = np.array([v.co[:] for v in mesh.vertices]); unchanged = list(range(1250)) + list(range(1340, 1385))
assert np.array_equal(base[unchanged], current[unchanged])
hood_triangles = []
mesh.calc_loop_triangles()
for tri in mesh.loop_triangles:
    if any(1250 <= i < 1340 for i in tri.vertices):
        hood_triangles.append(list(tri.vertices))
tree = BVHTree.FromPolygons([Vector(p) for p in current], hood_triangles, all_triangles=True)
self_pairs = [(i, j) for i, j in tree.overlap(tree) if i < j and not set(hood_triangles[i]) & set(hood_triangles[j])]
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']; body.data.calc_loop_triangles()
body_tree = BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices], [list(t.vertices) for t in body.data.loop_triangles], all_triangles=True)
contacts = tree.overlap(body_tree)
root['rockhopAppearanceCandidate'] = 'unaccepted appearance06 dimensional dropped hood'
hoodie['appearanceConstruction'] = 'unaccepted06 dimensional recessed hood; original05 field/keys/UV/weights preserved'
for o in bpy.data.objects:
    o.select_set(False)
selected = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render] + [root, rig]
for o in selected:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'rider.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out / 'rider.glb'), export_format='GLB', use_selection=True, export_yup=True,
    export_animations=False, export_attributes=True, export_extras=True, export_morph=True)
controller = json.loads((source.parent / 'source-normals-controller.json').read_text())
controller.update(status='UNACCEPTED06 dimensional hood; original garment controller and zero defaults retained',
    candidateMasterSHA256=sha(out / 'rider.blend'), candidateGLBSHA256=sha(out / 'rider.glb'), parentAppearanceMasterSHA256=sha(source))
(out / 'corrective-driver.json').write_text(json.dumps(controller, indent=2) + '\n')
assert pins == {str(p): sha(p) for p in [source, construction, handoff]}
report = {'status': 'UNACCEPTED fixed dimensional hood source checkpoint, matched moving review next', 'pins': pins,
    'recipeSHA256': sha(__file__), 'masterSHA256': sha(out / 'rider.blend'), 'quantizedGLBSHA256': sha(out / 'rider.glb'),
    'changedVertices': changes, 'addedVertices': 0, 'newHoodBoundsNativeM': [current[1250:1340].min(0).tolist(), current[1250:1340].max(0).tolist()],
    'oldHoodBoundsNativeM': [base[1250:1340].min(0).tolist(), base[1250:1340].max(0).tolist()],
    'maximumAuthoredDisplacementM': float(np.linalg.norm(current - base, axis=1).max()),
    'original1250ShirtAnd45PocketBasisUnchanged': True, 'hoodTriangles': len(hood_triangles),
    'hoodNonadjacentRestSelfPairs': len(self_pairs), 'hoodRestBodyTrianglePairs': len(contacts),
    'firstHoodBodyPairs': contacts[:12], 'firstSelfPairs': self_pairs[:12], 'morphDefaults': [k.value for k in mesh.shape_keys.key_blocks if k.name != 'Basis'],
    'optionalShapeReference': {'handoffSHA256': pins[str(handoff)], 'use': 'Root-played rounded hood/recessed entrance informed authored pouch; no donor vertices/UV/rig/weights imported. Native donor scale/fit unresolved.'},
    'limits': ['Only90 existing added hood vertices move; all morph vectors move with the basis, preserving their deltas. Original shirt/pocket fields and seam indices remain fixed.',
        'Original51 rig, protected face/PBR, mustard cotton, body/jeans/gloves/boots and garment topology/UV/weights retained; independent verification follows.',
        'One fixed profile; no density/gap/globalweight optimization or donor replacement.', 'Hood-rest counts are triangle contact diagnostics, not signed clearance/whole garment or moving acceptance.',
        'Protected NORMAL derivative still required after native quantized export; actual engine/fit/bike/device and M0-M5 stay open.']}
(evidence / 'construction.json').write_text(json.dumps(report, indent=2) + '\n')
print('DIMENSIONAL_HOOD_READY', report['masterSHA256'], 'rest body/self', len(contacts), len(self_pairs), flush=True)
