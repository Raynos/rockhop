"""Derive a pelvis/thigh boxer shell; exclude A-rest hands by skin semantics.

The frozen body02 neck/body/cheek and own51 bindings remain unchanged.
Original canonical ancestry is captured before mesh deletion/reindexing.
"""
import hashlib
import json
from pathlib import Path
import bmesh
import bpy
import numpy as np

owned = Path(__file__).resolve().parent
root = owned.parents[5]
out = owned / 'body03'
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body03'
out.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
native = out / 'natural-foundation.blend'
assert not native.exists(), 'Never overwrite a frozen native candidate'
source = owned / 'body02/natural-foundation.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source) == '01574c250a3a4b693d17ff373501574ec0e7db5615bcdc0e6b68adcf169e1bc3'
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.data.scenes['Finish natural wearer diagnostic']
bpy.context.window.scene = scene
rig = bpy.data.objects['Finish rig']
canonical = bpy.data.objects['Canonical anatomical body, baked adult hm08']
names = [b.name for b in rig.data.bones]
roles = {'pelvis', 'spine', 'chest', 'thigh.R', 'thigh.L', 'shin.R', 'shin.L'}
weights = np.zeros((len(canonical.data.vertices), len(names)), np.float32)
for v in canonical.data.vertices:
    for g in v.groups:
        name = canonical.vertex_groups[g.group].name
        if name in names:
            weights[v.index, names.index(name)] = g.weight
xyz = np.array([v.co[:] for v in canonical.data.vertices], np.float32)
semantic = weights[:, [names.index(x) for x in roles]].sum(axis=1)
total = weights.sum(axis=1)
height = (xyz[:, 2] >= .665) & (xyz[:, 2] <= 1.06)
admitted = height & (semantic >= total - 1e-6)
# Retain only the pelvis-connected component, including both thigh openings.
adj = [set() for _ in canonical.data.vertices]
for edge in canonical.data.edges:
    a, b = edge.vertices
    if admitted[a] and admitted[b]:
        adj[a].add(b)
        adj[b].add(a)
seed = int(np.argmax(np.where(admitted, weights[:, names.index('pelvis')], -1)))
keep = {seed}
queue = [seed]
while queue:
    a = queue.pop()
    for b in adj[a]:
        if b not in keep:
            keep.add(b)
            queue.append(b)
assert len(keep) > 500
assert np.max(np.abs(xyz[list(keep), 1])) < .25
rows = []
arrays = {'boneNames': np.array(names)}
for label in ['FULL', 'FOUR']:
    old = bpy.data.objects['Finish boxer ' + label]
    material = old.data.materials[0]
    parent = old.parent
    collections = list(old.users_collection)
    bpy.data.objects.remove(old, do_unlink=True)
    boxer = canonical.copy()
    boxer.data = canonical.data.copy()
    boxer.name = 'Finish boxer ' + label
    for collection in collections:
        collection.objects.link(boxer)
    boxer.parent = parent
    bm = bmesh.new()
    bm.from_mesh(boxer.data)
    ancestry = bm.verts.layers.int.new('_CANONICAL_ANCESTRY_ID')
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        v[ancestry] = v.index
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[ancestry] not in keep], context='VERTS')
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * .009
    bm.to_mesh(boxer.data)
    bm.free()
    if boxer.data.attributes.get('custom_normal'):
        boxer.data.attributes.remove(boxer.data.attributes['custom_normal'])
    boxer.data.update()
    boxer.data.materials.clear()
    boxer.data.materials.append(material)
    for mod in boxer.modifiers:
        if mod.type == 'ARMATURE':
            mod.object = rig
            mod.use_deform_preserve_volume = False
    for v in boxer.data.vertices:
        ww = {boxer.vertex_groups[g.group].name: g.weight for g in v.groups
              if boxer.vertex_groups[g.group].name in names and g.weight > 0}
        assert set(ww) <= roles
        selected = sorted(ww, key=lambda x: (-ww[x], names.index(x)))[:4] if label == 'FOUR' else list(ww)
        for name in ww:
            boxer.vertex_groups[name].remove([v.index])
        s = sum(ww[name] for name in selected)
        for name in selected:
            boxer.vertex_groups[name].add([v.index], ww[name] / s, 'REPLACE')
    for name, values in [('_NATIVE_ID', np.arange(len(boxer.data.vertices), dtype=np.int32)),
                         ('_SOURCE_ID', np.full(len(boxer.data.vertices), -1, np.int32))]:
        attr = boxer.data.attributes.get(name) or boxer.data.attributes.new(name, 'INT', 'POINT')
        attr.data.foreach_set('value', values)
    ids = np.empty(len(boxer.data.vertices), np.int32)
    boxer.data.attributes['_CANONICAL_ANCESTRY_ID'].data.foreach_get('value', ids)
    derived = np.array([v.co[:] for v in boxer.data.vertices], np.float32)
    assert len(np.unique(ids)) == len(ids)
    assert set(ids) == keep
    assert np.max(np.linalg.norm(derived - xyz[ids], axis=1)) < .009001
    boxer.data.calc_loop_triangles()
    triangles = np.array([t.vertices[:] for t in boxer.data.loop_triangles], np.int32)
    boxer.hide_set(label == 'FULL')
    boxer.hide_render = label == 'FULL'
    arrays[label + 'XYZ'] = derived
    arrays[label + 'Triangles'] = triangles
    arrays[label + 'CanonicalAncestryIDs'] = ids
    rows.append({'label': label, 'vertices': len(ids), 'triangles': len(triangles),
                 'boundsMin': derived.min(axis=0).tolist(), 'boundsMax': derived.max(axis=0).tolist(),
                 'canonicalAncestryUnique': True, 'fingerArmWeightVertices': 0,
                 'nativeIDsUnique': True, 'sourceIDs': 'All -1: positions are displaced derivatives'})
assert np.array_equal(arrays['FULLXYZ'], arrays['FOURXYZ'])
assert np.array_equal(arrays['FULLTriangles'], arrays['FOURTriangles'])
np.savez_compressed(out / 'authored-boxer-fields.npz', **arrays)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
report = {'status': 'UNACCEPTED_SEMANTIC_BOXER_REQUIRES_INDEPENDENT_CONTACT_AND_MOTION_QA',
          'source': str(source.relative_to(root)), 'sourceSHA256': sha(source),
          'recipeSHA256': sha(__file__), 'native': str(native.relative_to(root)),
          'nativeSHA256': sha(native), 'fieldsSHA256': sha(out / 'authored-boxer-fields.npz'),
          'method': 'Pelvis/thigh semantic field and pelvis-connected component, height crop, 9mm derived normal shell.',
          'roles': sorted(roles), 'heightSelectedCanonicalVertices': int(height.sum()),
          'semanticAdmittedCanonicalVertices': int(admitted.sum()), 'connectedRetainedCanonicalVertices': len(keep),
          'excludedHeightSelectedIDs': np.flatnonzero(height & ~np.isin(np.arange(len(xyz)), list(keep))).tolist(),
          'rows': rows, 'limits': ['Head self crossings and neck FULL-to-FOUR loss unchanged; body02 failed neck retained.',
                                  'Shell offset, clearance, self intersections, opening quality and motion remain unaccepted.',
                                  'No wardrobe or natural grounded animation acceptance.']}
(evidence / 'authoring.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['status', 'nativeSHA256', 'connectedRetainedCanonicalVertices', 'rows']}), flush=True)
