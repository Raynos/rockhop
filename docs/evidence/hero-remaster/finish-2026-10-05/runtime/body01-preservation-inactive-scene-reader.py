"""Independent read-only reopen of original objects, own51 and protected head fields."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
import numpy as np
p = argparse.ArgumentParser(description=__doc__)
for k in ['source', 'candidate', 'contract', 'fields', 'out']:
    p.add_argument('--' + k, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, candidate, contract_path, fields_path, out = [Path(getattr(a, k)).resolve() for k in ['source', 'candidate', 'contract', 'fields', 'out']]
assert not out.exists()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract = json.loads(contract_path.read_text())
assert sha(source) == contract['sourceSHA256']
pins = {str(p): sha(p) for p in [source, candidate, contract_path, fields_path]}
helper_path = source.parent.parent / 'verify_extended_protected_data.py'
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
text = helper_path.read_text()
exec(compile(text[text.index('def value('):text.index('before=snapshot(original)')], str(helper_path), 'exec'), helpers)

def mesh_state(o):
    return {'object': helpers['object_state'](o), 'mesh': helpers['mesh_extra'](o.data),
            'xyz': helpers['array_digest'](o.data.vertices, 'co', 3),
            'polygons': [list(p.vertices) for p in o.data.polygons],
            'groups': [g.name for g in o.vertex_groups],
            'weights': [[(m.group, m.weight) for m in v.groups] for v in o.data.vertices],
            'materials': [m.name if m else None for m in o.data.materials]}
def rig_state(o):
    return {'world': np.array(o.matrix_world).tolist(), 'scale': list(o.scale),
            'bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None, 'matrix': np.array(b.matrix_local).tolist(), 'head': list(b.head_local), 'tail': list(b.tail_local), 'deform': b.use_deform} for b in o.data.bones]}
def materials():
    return {m.name: {'properties': helpers['properties'](m), 'nodes': [{'name': n.name, 'type': n.bl_idname, 'properties': helpers['properties'](n), 'inputs': [(s.name, helpers['value'](s.default_value)) for s in n.inputs if hasattr(s, 'default_value')]} for n in m.node_tree.nodes] if m.node_tree else None, 'links': [(l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name) for l in m.node_tree.links] if m.node_tree else None} for m in bpy.data.materials}
def images():
    return {i.name: {'size': list(i.size), 'source': i.source, 'filepath': i.filepath, 'packed': hashlib.sha256(i.packed_file.data).hexdigest() if i.packed_file else None} for i in bpy.data.images}

bpy.ops.wm.open_mainfile(filepath=str(source))
original_names = [o.name for o in bpy.data.objects]
original = {o.name: mesh_state(o) if o.type == 'MESH' else helpers['object_state'](o) for o in bpy.data.objects}
rig_before = rig_state(bpy.data.objects[contract['rig']])
pose_before = {b.name: np.array(b.matrix_basis).tolist() for b in bpy.data.objects[contract['rig']].pose.bones}
material_before, images_before = materials(), images()
source_head = bpy.data.objects['Protected textured head above hidden neck interface'].data
head_xyz = np.array([v.co[:] for v in source_head.vertices], np.float32)
head_normals = np.array([v.vector[:] for v in source_head.corner_normals], np.float32)
head_corner_ids = np.array([l.vertex_index for l in source_head.loops])
head_uvs = [np.array([v.uv[:] for v in uv.data], np.float32) for uv in source_head.uv_layers]
protected = np.array(contract['scope']['headProtectedCompleteAliasIDs'], int)
fields = np.load(fields_path)
refs = fields['headCornerAttributeEdgeSources']
source_corners = refs[:, 0].astype(int)
valid = source_corners >= 0
mask = valid.copy(); mask[valid] = np.isin(head_corner_ids[source_corners[valid]], protected)

bpy.ops.wm.open_mainfile(filepath=str(candidate))
checks = {}
for name in original_names:
    o = bpy.data.objects[name]
    after = mesh_state(o) if o.type == 'MESH' else helpers['object_state'](o)
    checks[name] = original[name] == after
original_rig = bpy.data.objects[contract['rig']]
finish_rig = bpy.data.objects[contract['derivativeRig']]
assert len(finish_rig.data.bones) == 51
rig_original_exact = rig_state(original_rig) == rig_before
rig_copy_exact = rig_state(finish_rig) == rig_before
pose_original_exact = {b.name: np.array(b.matrix_basis).tolist() for b in original_rig.pose.bones} == pose_before
material_after, images_after = materials(), images()
materials_exact = all(material_after.get(n) == v for n, v in material_before.items())
images_exact = all(images_after.get(n) == v for n, v in images_before.items())
heads = {}
for label in ['FULL', 'FOUR']:
    mesh = bpy.data.objects['Finish head ' + label].data
    xyz = np.array([v.co[:] for v in mesh.vertices], np.float32)
    decoded = np.array([v.vector[:] for v in mesh.corner_normals], np.float32)
    assert len(refs) == len(decoded)
    expected = head_normals[source_corners[mask]]
    delta = np.linalg.norm(decoded[mask].astype(float) - expected.astype(float), axis=1)
    changed = np.flatnonzero(np.any(decoded[mask] != expected, axis=1))
    uvs = [np.array([v.uv[:] for v in uv.data], np.float32) for uv in mesh.uv_layers]
    uv_results = []
    assert len(uvs) == len(head_uvs)
    for before, after in zip(head_uvs, uvs):
        uv_results.append({'protectedExact': bool(np.array_equal(after[mask], before[source_corners[mask]])), 'maximumDelta': float(np.max(np.abs(after[mask] - before[source_corners[mask]])))})
    heads[label] = {'protectedXYZExact': bool(np.array_equal(xyz[protected], head_xyz[protected])), 'protectedCorners': int(mask.sum()), 'changedProtectedNormalCorners': int(len(changed)), 'maximumProtectedNormalVectorDelta': float(delta.max()), 'changedDerivativeCornerIDs': np.flatnonzero(mask)[changed].tolist(), 'changedOriginalSourceCornerIDs': source_corners[mask][changed].tolist(), 'protectedUVLayers': uv_results, 'nativeXYZMatchesAuthoredFields': bool(np.array_equal(xyz, fields['headRestXYZ'].astype(np.float32)))}
result = {'status': 'READ_ONLY_REOPEN_PRESERVATION_DIAGNOSTIC_UNACCEPTED', 'inputPins': pins, 'recipeSHA256': sha(__file__), 'readerHelperSHA256': sha(helper_path), 'blender': bpy.app.version_string,
          'originalObjectChecks': checks, 'originalObjectsExact': all(checks.values()), 'original51RigRestWorldScaleExact': rig_original_exact, 'copied51RigRestWorldScaleExact': rig_copy_exact, 'originalSavedPoseBasisExact': pose_original_exact, 'originalMaterialsExact': materials_exact, 'originalPackedImagesExact': images_exact, 'heads': heads,
          'limits': ['Read-only reopening: no pose assignment, evaluation, source save, normal rewrite or render.', 'Decoded head vectors compared through explicit construction corner ancestry; upper UV/positions measured separately.', 'No motion/parity/collision/coverage/art/device or promotion qualification.']}
assert pins == {x: sha(x) for x in pins}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['originalObjectsExact', 'original51RigRestWorldScaleExact', 'copied51RigRestWorldScaleExact', 'originalSavedPoseBasisExact', 'originalMaterialsExact', 'originalPackedImagesExact', 'heads']}), flush=True)
