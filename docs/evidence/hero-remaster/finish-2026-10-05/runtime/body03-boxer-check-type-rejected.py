"""Read-only semantic boxer ancestry and body03 scope check; no pose/save."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
for name in ['control', 'candidate', 'fields', 'out']:
    p.add_argument('--' + name, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
control, candidate, fields_path, out = [Path(getattr(a, name)).resolve() for name in ['control', 'candidate', 'fields', 'out']]
assert not out.exists()
sha = lambda x: hashlib.sha256(Path(x).read_bytes()).hexdigest()
pins = {str(x): sha(x) for x in [control, candidate, fields_path]}
fields = np.load(fields_path)

def digest(o):
    o.data.calc_loop_triangles()
    data = {'xyz': [list(v.co) for v in o.data.vertices],
            'faces': [list(t.vertices) for t in o.data.loop_triangles],
            'normals': [list(n.vector) for n in o.data.corner_normals],
            'uv': [[[v.uv.x, v.uv.y] for v in layer.data] for layer in o.data.uv_layers],
            'groups': [g.name for g in o.vertex_groups],
            'weights': [[(g.group, g.weight) for g in v.groups] for v in o.data.vertices],
            'world': np.array(o.matrix_world).tolist(),
            'modifier': [(m.type, m.object.name, m.use_deform_preserve_volume) for m in o.modifiers if m.type == 'ARMATURE']}
    return hashlib.sha256(json.dumps(data, separators=(',', ':')).encode()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(control))
bpy.context.window.scene = bpy.data.scenes['Finish natural wearer diagnostic']
bpy.context.view_layer.update()
protected_names = ['Finish body FULL', 'Finish body FOUR', 'Finish head FULL', 'Finish head FOUR', 'Finish coherent cheek']
protected = {name: digest(bpy.data.objects[name]) for name in protected_names}
bpy.ops.wm.open_mainfile(filepath=str(candidate))
bpy.context.window.scene = bpy.data.scenes['Finish natural wearer diagnostic']
bpy.context.view_layer.update()
checks = {name: digest(bpy.data.objects[name]) == protected[name] for name in protected_names}
rig = bpy.data.objects['Finish rig']
names = [b.name for b in rig.data.bones]
canonical = bpy.data.objects['Canonical anatomical body, baked adult hm08']
canonical_xyz = np.array([v.co[:] for v in canonical.data.vertices])
canonical_weights = np.zeros((len(canonical_xyz), len(names)))
for v in canonical.data.vertices:
    for group in v.groups:
        name = canonical.vertex_groups[group.group].name
        if name in names:
            canonical_weights[v.index, names.index(name)] = group.weight
roles = {'pelvis', 'spine', 'chest', 'thigh.L', 'thigh.R', 'shin.L', 'shin.R'}
rows = {}
for label in ['FULL', 'FOUR']:
    o = bpy.data.objects['Finish boxer ' + label]
    def attr(name):
        value = o.data.attributes[name]
        assert value.domain == 'POINT' and value.data_type == 'INT'
        return np.array([x.value for x in value.data], dtype=int)
    ancestry, native_ids, source_ids = [attr(name) for name in ['_CANONICAL_ANCESTRY_ID', '_NATIVE_ID', '_SOURCE_ID']]
    xyz = np.array([v.co[:] for v in o.data.vertices])
    observed = np.zeros((len(xyz), len(names)))
    for v in o.data.vertices:
        for group in v.groups:
            name = o.vertex_groups[group.group].name
            if name in names:
                observed[v.index, names.index(name)] = group.weight
    expected = canonical_weights[ancestry].copy()
    if label == 'FOUR':
        for row in expected:
            order = np.argsort(-row, kind='stable')
            row[order[4:]] = 0
    expected /= expected.sum(axis=1)[:, None]
    delta = np.abs(expected - observed)
    nonroles = [i for i, name in enumerate(names) if name not in roles]
    o.data.calc_loop_triangles()
    triangles = np.array([t.vertices[:] for t in o.data.loop_triangles], dtype=int)
    rows[label] = {'vertices': len(xyz), 'triangles': len(triangles),
        'canonicalAncestryUnique': len(np.unique(ancestry)) == len(ancestry),
        'canonicalAncestryInRange': bool(np.all((ancestry >= 0) & (ancestry < len(canonical_xyz)))),
        'nativeIdentityContiguous': bool(np.array_equal(native_ids, np.arange(len(xyz)))),
        'sourceIDsDeclareDerived': bool(np.all(source_ids == -1)),
        'fingerArmInfluenceVertices': int(np.any(observed[:, nonroles] > 0, axis=1).sum()),
        'weightMaximumCanonicalDifference': float(delta.max()),
        'normalizedWeightMaximumError': float(np.max(np.abs(observed.sum(axis=1)-1))),
        'maximumNonzeroInfluences': int((observed > 0).sum(axis=1).max()),
        'maxCanonicalDisplacementM': float(np.linalg.norm(xyz-canonical_xyz[ancestry], axis=1).max()),
        'nativeXYZMatchesFields': bool(np.array_equal(xyz.astype(np.float32), fields[label+'XYZ'])),
        'nativeTopologyMatchesFields': bool(np.array_equal(triangles, fields[label+'Triangles'])),
        'nativeAncestryMatchesFields': bool(np.array_equal(ancestry, fields[label+'CanonicalAncestryIDs']))}
result = {'status': 'UNACCEPTED_READ_ONLY_SEMANTIC_BOXER_SCOPE_DIAGNOSTIC', 'inputPins': pins,
          'recipeSHA256': sha(__file__), 'blender': bpy.app.version_string,
          'unchangedDerivedParts': checks, 'parts': rows,
          'limits': ['Canonical ancestry is explicit; derivative native identity never substitutes for source ancestry.',
                     'Static scope/field checks only; surface contact, support, skin parity, art and device acceptance are separate.']}
assert pins == {x: sha(x) for x in pins}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result), flush=True)
