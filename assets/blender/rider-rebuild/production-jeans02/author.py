"""Direct local gusset reconstruction on the actual author04 native jeans.
No projection, whole-ring expansion, skin rewrite, material bake or body edit.
Parent authorizes one bounded CPU2 job; save an editable native before maps.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(row):
    path = ROOT / row['path']
    assert path.is_file() and sha(path) == row['sha256'], ('Changed input', row)
    return path


def cage_rows(count=48, levels=14):
    """Exact original procedural vertex lineage; native topology is checked."""
    result, shared, next_id = {}, {}, 0
    for side in ('L', 'R'):
        result[side] = []
        for level in range(levels):
            ids = []
            for k in range(count):
                if level == levels - 1 and 18 <= k <= 30:
                    if k in shared:
                        ids.append(shared[k])
                        continue
                    shared[k] = next_id
                ids.append(next_id)
                next_id += 1
            result[side].append(ids)
    return result


def sculpt_controls(vertices, controls):
    """Connected upper-medial patch only, retaining the exterior boundary."""
    result = np.asarray(vertices, dtype=np.float64).copy()
    rows = cage_rows()
    for side, sign in (('L', 1), ('R', -1)):
        for row in controls['supportStrips']:
            for k, (own_x, y, z) in zip(range(18, 31), row['points']):
                result[rows[side][row['level']][k]] = (sign * own_x, y, z)
    for k, (y, z) in zip(range(18, 25), controls['anteriorSeamYZ']):
        result[rows['L'][13][k]] = (0, y, z)
    # k25..30 are the actual old posterior path and are deliberately untouched.
    return result


def topology(mesh):
    return [tuple(p.vertices) for p in mesh.polygons]


def fields(obj):
    groups = {g.index: g.name for g in obj.vertex_groups}
    weights = [[[groups[g.group], g.weight] for g in v.groups] for v in obj.data.vertices]
    full = {a.name: [d.value for d in a.data] for a in obj.data.attributes
            if a.name.startswith('FULL::')}
    return json.dumps({'weights': weights, 'full': full,
                       'names': obj.get('full_field_joint_names')}, separators=(',', ':'))


def uv_rows(obj):
    return [[layer.name, [[d.uv.x, d.uv.y] for d in layer.data]]
            for layer in obj.data.uv_layers]


def template_surface(namespace, old_spec, name):
    obj = namespace['production_surface'](old_spec)
    obj.name = name
    mod = obj.modifiers.new('Editable gusset subdivision', 'SUBSURF')
    mod.levels = 2
    mod.render_levels = 2
    return obj


def evaluated_mesh(obj):
    graph = bpy.context.evaluated_depsgraph_get()
    return bpy.data.meshes.new_from_object(obj.evaluated_get(graph), depsgraph=graph)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 2
    control_path = Path(args[0]).resolve()
    controls = json.loads(control_path.read_text())
    out = Path(args[1]).resolve()
    assert controls['accepted'] is False and not out.exists()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-jeans02')
    native = pin(controls['native'])
    old_recipe = pin(controls['oldRecipe'])
    old_author = pin(controls['oldAuthor'])
    inherited_fields = pin(controls['nativeFields'])
    pin(controls['bodySagittalAuthority'])
    old_spec = json.loads(old_recipe.read_text())
    for row in [old_spec[k] for k in ('native', 'body', 'dense', 'reference')] + list(old_spec['maps'].values()):
        pin(row)
    bpy.ops.wm.open_mainfile(filepath=str(native))
    target, body, rig = [bpy.data.objects[n] for n in ('RiderJeans', 'RiderBody', 'RiderSkeleton')]
    assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
    assert not body.hide_get() and not body.hide_render
    namespace = runpy.run_path(str(old_author))
    body_before = namespace['signature'](body, rig)
    native_topology, skin_before, uv_before = topology(target.data), fields(target), uv_rows(target)
    actual_before = np.asarray([tuple(v.co) for v in target.data.vertices], dtype=np.float64)
    materials_before = [m.as_pointer() for m in target.data.materials]
    assert all(0 < len([g for g in v.groups if g.weight > 0]) <= 4 for v in target.data.vertices)
    old_cage = template_surface(namespace, old_spec, 'Jeans02GussetControlReference')
    new_cage = template_surface(namespace, old_spec, 'Jeans02GussetEditableCage')
    before_cage = np.asarray([tuple(v.co) for v in new_cage.data.vertices])
    after_cage = sculpt_controls(before_cage, controls)
    changed_cage = np.flatnonzero(np.any(after_cage != before_cage, axis=1))
    for vertex in changed_cage:
        new_cage.data.vertices[int(vertex)].co = after_cage[vertex]
    new_cage.data.update()
    bpy.context.view_layer.update()
    old_mesh, new_mesh = evaluated_mesh(old_cage), evaluated_mesh(new_cage)
    assert topology(old_mesh) == topology(new_mesh) == native_topology, 'Native/cage subdivision lineage differs'
    old_points = np.asarray([tuple(v.co) for v in old_mesh.vertices], dtype=np.float64)
    new_points = np.asarray([tuple(v.co) for v in new_mesh.vertices], dtype=np.float64)
    assert old_points.shape == new_points.shape == actual_before.shape
    delta = new_points - old_points
    changed = np.flatnonzero(np.any(delta != 0, axis=1))
    assert len(changed) and len(changed) < len(actual_before) // 4, 'Unexpected nonlocal patch support'
    for vertex in changed:
        target.data.vertices[int(vertex)].co = actual_before[vertex] + delta[vertex]
    target.data.update()
    actual_after = np.asarray([tuple(v.co) for v in target.data.vertices], dtype=np.float64)
    unchanged = np.ones(len(actual_before), dtype=bool)
    unchanged[changed] = False
    assert np.array_equal(actual_after[unchanged], actual_before[unchanged])
    assert fields(target) == skin_before and uv_rows(target) == uv_before
    assert topology(target.data) == native_topology
    assert [m.as_pointer() for m in target.data.materials] == materials_before
    assert namespace['signature'](body, rig) == body_before
    for obj in (old_cage, new_cage):
        obj.hide_render = True
        obj.hide_set(True)
        obj['unaccepted'] = True
    new_cage['gusset_control_recipe'] = json.dumps(controls)
    target['productionJeansRecipe'] = 'rockhop-native-local-gusset-v2'
    target['unaccepted'] = True
    target['local_gusset_source_sha256'] = controls['native']['sha256']
    target['local_gusset_changed_vertex_ids'] = json.dumps(changed.tolist())
    bpy.data.meshes.remove(old_mesh)
    bpy.data.meshes.remove(new_mesh)
    out.mkdir(parents=True)
    saved = out / 'production-jeans.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(saved))
    # Actual native is safely saved before maps or any later evidence operation.
    (out / 'production-jeans-fields.npz').write_bytes(inherited_fields.read_bytes())
    np.savez_compressed(out / 'local-gusset-delta.npz', changedVertexIds=changed,
                        oldPositions=actual_before[changed], newPositions=actual_after[changed],
                        changedCageVertexIds=changed_cage, oldCage=before_cage, newCage=after_cage)
    report = {'accepted': False, 'stage': 'LOCAL_EDITABLE_GUSSET_SAVED_BEFORE_MAPS',
              'native': {'path': str(saved.relative_to(ROOT)), 'sha256': sha(saved)},
              'sourceNative': controls['native'], 'controlSHA256': sha(control_path),
              'authorSHA256': sha(__file__), 'vertices': len(actual_after),
              'changedVertices': len(changed), 'changedCageVertices': len(changed_cage),
              'outsidePatchPositionsExact': True, 'bodyAnd75RestUntouched': True,
              'nativeFullFourFieldsExact': True, 'nativeFields': controls['nativeFields'],
              'originalUVTopologyAndMaterialsExact': True, 'posteriorSeamControlsUnchanged': True,
              'denseMapsAndLattice': 'Actual author04 selected sources retained untouched in native',
              'limits': ['Actual front/back/profile fit review pending parent.',
                         'No bake or art acceptance. FULL/FOUR movement loss unmeasured.',
                         'Unchanged native garment fields are inherited controls, not a new motion qualification.']}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('LOCAL_GUSSET_NATIVE_SAVED', str(saved), flush=True)


if __name__ == '__main__':
    main()
