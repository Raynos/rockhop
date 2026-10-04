"""Read canonical rest fields from frozen native19; no posing, export or save."""
import hashlib, json, sys
from pathlib import Path
import bpy
import numpy as np

root = Path.cwd()
out = Path(__file__).resolve().parent
source = root / 'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie19/profile-fit.blend'
old = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/diagnostic02'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected = 'b545229e52c4fc5bcb97b4fbc81ccc3a0e5a2f9c87fe3c7338691317d965e449'
assert sha(source) == expected and not (out / 'native-fields.npz').exists()
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
names = [b.name for b in rig.data.bones]
assert len(names) == 51
driver = json.loads((old / 'driver.json').read_text())
assert names == driver['jointOrderNative']
weights = json.loads((old / 'weights.json').read_text())['rows'][0]
objects = {'canonicalFour': 'Canonical anatomical body, baked adult hm08',
           'originalFull': 'Full native diagnostic body',
           'renderedBody': 'Canonical body with hidden head interface',
           'boxers': 'Opaque boxer fitting garment',
           'protectedHead': 'Protected textured head above hidden neck interface',
           'cheek': 'Protected coherent cheek patch'}
arrays = {'rigRest': np.array([np.array(b.matrix_local) for b in rig.data.bones]),
          'rigWorld': np.array(rig.matrix_world), 'boneNames': np.array(names)}
report = {'status': 'READ_ONLY_FROZEN_CURRENT_WHOLE_BODY_REST_FIELDS',
          'source': str(source.relative_to(root)), 'sourceSHA256': expected,
          'driverSHA256': sha(old / 'driver.json'), 'weightsSHA256': sha(old / 'weights.json'),
          'recipeSHA256': sha(__file__), 'blenderVersion': bpy.app.version_string,
          'canonicalRestDefinition': 'Raw immutable mesh coordinates transformed by object matrix_world; action-off identity pose_basis on all51 bones, shape-key defaults separately listed. No current scene pose or runtime riding tick0 used as rest.',
          'axes': 'Native +Xforward/+Zup/-Yleft, metres; file root X+.65 retained once.',
          'meshFields': {}, 'rig': {'names': names, 'parents': [b.parent.name if b.parent else None for b in rig.data.bones],
                                  'constraints': {b.name: [c.type for c in rig.pose.bones[b.name].constraints] for b in rig.data.bones},
                                  'action': rig.animation_data.action.name if rig.animation_data and rig.animation_data.action else None},
          'limits': ['Read-only field extraction, no new rig/export/render capture, no file save or field edit.',
                     'Canonical rest is explicitly defined; Blender current scene action/pose is not adopted implicitly.',
                     'Separate generated head interface and fitting full-body coverage must not be conflated.']}
for label, name in objects.items():
    obj = bpy.data.objects[name]; mesh = obj.data; mesh.calc_loop_triangles()
    xyz = np.array([list(v.co) for v in mesh.vertices], dtype='<f8')
    tris = np.array([list(t.vertices) for t in mesh.loop_triangles], dtype='<i4')
    polys = [list(f.vertices) for f in mesh.polygons]
    membership = np.zeros((len(xyz), 51), dtype='<f8')
    for v in mesh.vertices:
        for m in v.groups:
            n = obj.vertex_groups[m.group].name
            if n in names: membership[v.index, names.index(n)] = m.weight
    source_ids = np.array([x.value for x in mesh.attributes['_SOURCE_ID'].data], dtype='<f8') if '_SOURCE_ID' in mesh.attributes else np.array([], dtype='<f8')
    arrays.update({label + 'XYZ': xyz, label + 'Triangles': tris, label + 'Weights': membership,
                   label + 'World': np.array(obj.matrix_world), label + 'SourceIDs': source_ids})
    record = {'name': name, 'vertices': len(xyz), 'polygons': len(polys), 'triangles': len(tris),
              'positionsSHA256': hashlib.sha256(xyz.tobytes()).hexdigest(),
              'polygonCyclesSHA256': hashlib.sha256(json.dumps(polys).encode()).hexdigest(),
              'triangleSHA256': hashlib.sha256(tris.tobytes()).hexdigest(),
              'membershipSHA256': hashlib.sha256(membership.tobytes()).hexdigest(),
              'maximumPositiveDeformInfluences': int((membership > 0).sum(1).max()),
              'unweightedVertices': int((membership.sum(1) == 0).sum()),
              'worldRows': np.array(obj.matrix_world).tolist(), 'visible': not obj.hide_render,
              'shapeKeys': [(k.name, k.value) for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],
              'modifiers': [{'type': m.type, 'enabledViewport': m.show_viewport, 'enabledRender': m.show_render,
                             'preserveVolume': m.use_deform_preserve_volume if m.type == 'ARMATURE' else None} for m in obj.modifiers]}
    if label in ['originalFull', 'canonicalFour']:
        assert record['positionsSHA256'] == weights['geometryPositionsSHA256']
        assert record['polygonCyclesSHA256'] == weights['facesSHA256']
        field = 'nativeSparseWeights' if label == 'originalFull' else 'conditionedSparseWeights'
        reference = np.zeros_like(membership)
        for i, row in enumerate(weights[field]):
            for n, w in row: reference[i, names.index(n)] = w
        record['existingStreamGeometryAndTopologyExact'] = True
        record['existingMembershipMaxAbsError'] = float(np.abs(reference - membership).max())
        assert record['existingMembershipMaxAbsError'] < 1e-7
    report['meshFields'][label] = record
for kind in ['full', 'four']:
    name = 'body-native-' + kind + '.f64'; p = old / name
    assert p.stat().st_size == driver['pins'][name]['bytes'] and sha(p) == driver['pins'][name]['sha256']
report['existingBodyStreams'] = {kind: driver['pins']['body-native-' + kind + '.f64'] for kind in ['full', 'four']}
assert sha(source) == expected
np.savez_compressed(out / 'native-fields.npz', **arrays)
report['nativeFieldsSHA256'] = sha(out / 'native-fields.npz')
(out / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: {a: v[a] for a in ['vertices', 'triangles', 'maximumPositiveDeformInfluences', 'visible']} for k, v in report['meshFields'].items()}), flush=True)
