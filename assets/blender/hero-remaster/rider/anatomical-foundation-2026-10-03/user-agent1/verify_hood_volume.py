"""Verify scoped hood change and report rest intersections before any promotion."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'candidate', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, candidate, output = [Path(getattr(a, n)).resolve() for n in ['source', 'candidate', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(file):
    bpy.ops.wm.open_mainfile(filepath=str(file))
    rig = bpy.data.objects['Independent anatomical foundation rig']
    bind = [(b.name, b.parent.name if b.parent else None, [list(r) for r in b.matrix_local]) for b in rig.data.bones]
    rows = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        mesh = o.data
        rows[o.name] = {'vertices': [list(v.co) for v in mesh.vertices], 'faces': [list(p.vertices) for p in mesh.polygons],
            'uv': [[[float(x) for x in d.uv] for d in l.data] for l in mesh.uv_layers], 'weights': [[(o.vertex_groups[g.group].name, g.weight) for g in v.groups] for v in mesh.vertices],
            'keys': {k.name: [list(v.co) for v in k.data] for k in mesh.shape_keys.key_blocks} if mesh.shape_keys else {},
            'materialNames': [m.name for m in mesh.materials]}
    hoodie = bpy.data.objects['Sewn clean hoodie with dropped hood']; hoodie.data.calc_loop_triangles()
    faces = [list(t.vertices) for t in hoodie.data.loop_triangles if any(1250 <= i < 1340 for i in t.vertices)]
    tree = BVHTree.FromPolygons([v.co.copy() for v in hoodie.data.vertices], faces, all_triangles=True)
    body = bpy.data.objects['Canonical anatomical body, baked adult hm08']; body.data.calc_loop_triangles()
    body_tree = BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices], [list(t.vertices) for t in body.data.loop_triangles], all_triangles=True)
    self_pairs = [(i, j) for i, j in tree.overlap(tree) if i < j and not set(faces[i]) & set(faces[j])]
    contacts = tree.overlap(body_tree)
    return bind, rows, {'bodyPairs': len(contacts), 'selfPairs': len(self_pairs), 'firstSelfPairs': [{'triangleIDs': [i, j], 'vertices': [faces[i], faces[j]]} for i, j in self_pairs[:16]],
        'firstBodyPairs': [{'hoodTriangle': i, 'hoodVertices': faces[i], 'bodyTriangle': j} for i, j in contacts[:12]]}
before, after = capture(source), capture(candidate)
assert before[0] == after[0]
hoodie_name = 'Sewn clean hoodie with dropped hood'
fixed = {}
for name, row in before[1].items():
    if name == hoodie_name:
        continue
    assert row == after[1][name], name
    fixed[name] = hashlib.sha256(json.dumps(row).encode()).hexdigest()
old, new = before[1][hoodie_name], after[1][hoodie_name]
for key in ['faces', 'uv', 'weights', 'materialNames']:
    assert old[key] == new[key], key
ov, nv = np.array(old['vertices']), np.array(new['vertices']); unchanged = list(range(1250)) + list(range(1340, 1385))
assert np.array_equal(ov[unchanged], nv[unchanged])
delta_error = max(float(np.abs((np.array(new['keys'][name]) - np.array(new['keys']['Basis'])) - (np.array(old['keys'][name]) - np.array(old['keys']['Basis']))).max()) for name in old['keys'])
basis_error = float(np.abs(nv - np.array(new['keys']['Basis'])).max())
assert delta_error < 3e-7 and basis_error < 2e-7, (delta_error, basis_error)
report = {'status': 'REJECTED rest hood/body or self intersections; scoped source preservation verified' if after[2]['bodyPairs'] or after[2]['selfPairs'] else 'UNACCEPTED rest hood intersection proxy passes; moving review pending',
    'sourceSHA256': sha(source), 'candidateSHA256': sha(candidate), 'verifierSHA256': sha(__file__), 'all51NativeBindExact': True,
    'allNonHoodieVisibleMeshFieldsExact': fixed, 'original1250ShirtAnd45PocketBasisExact': True, 'hoodTopologyUVWeightsMaterialNamesExact': True,
    'maximumMorphDeltaRoundoffM': delta_error, 'hoodieMeshVsBasisMaximumM': basis_error, 'source05RestHood': before[2], 'candidateRestHood': after[2],
    'limits': ['Rest triangle intersections are proxies; source05 may already fail. No moving or complete signed-clearance pass.',
        'Dimensional hood shape is a source checkpoint, not art or engine acceptance. Original05 remains frozen.']}
output.write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps({k: report[k] for k in ['status', 'maximumMorphDeltaRoundoffM', 'hoodieMeshVsBasisMaximumM', 'source05RestHood', 'candidateRestHood']}))
