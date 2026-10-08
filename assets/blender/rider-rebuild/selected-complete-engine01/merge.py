"""Complete selected outfit on its unchanged native75, source-only until parent lease.

blender -b -t 2 --python-exit-code 1 --python merge.py -- MANIFEST FRESH_OUT
No render, geometry fitting, decimation, bake, generation or normal-player export.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parents[4]
EXPECTED = {'RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L',
            'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024*1024): h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert path.is_file() and sha(path) == row['sha256'], ('Changed source', row)
    return path


def pins(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value: yield value
        else:
            for child in value.values(): yield from pins(child)
    elif isinstance(value, list):
        for child in value: yield from pins(child)


def mesh_four(obj, rig, require_four=True):
    names = {g.index: g.name for g in obj.vertex_groups}
    rows = []
    for vertex in obj.data.vertices:
        row = [(names[g.group], g.weight) for g in vertex.groups if g.weight > 0]
        assert row and (not require_four or len(row) <= 4) and abs(sum(w for _, w in row)-1) < 2e-5, (obj.name, vertex.index, len(row), sum(w for _, w in row))
        assert all(name in rig.data.bones and not name.startswith(('PalmSocket.', 'SoleSocket.')) for name, _ in row)
        rows.append(row)
    return rows


def limit_four(obj, rig):
    """Conventional delivery fields on a copied render body, never full anatomy."""
    before = mesh_four(obj, rig, require_four=False)
    groups = {g.name: g for g in obj.vertex_groups}
    changed, removed_mass = 0, 0.
    for index, row in enumerate(before):
        four = sorted(row, key=lambda item: (-item[1], item[0]))[:4]
        total = sum(w for _, w in four)
        if len(row) > 4: changed += 1
        removed_mass = max(removed_mass, max(0., sum(w for _, w in row)-total))
        for name, _ in row: groups[name].remove([index])
        for name, weight in four: groups[name].add([index], weight/total, 'REPLACE')
    mesh_four(obj, rig)
    return {'method': 'Largest FOUR source coefficients, normalized on render derivative only',
            'sourceMaximumPositiveInfluences': max(map(len, before)),
            'sourceRowsAboveFour': changed, 'maximumRemovedMass': removed_mass,
            'fullAnatomyReferenceChanged': False}


def bind_hoodie(obj, source, body, rig):
    """Nearest native-body face interpolation within selected-source ownership.

    The temporary source rig supplies seven domain labels, never final weights,
    transforms or bones. No fitted positions or original map/UV values are edited.
    """
    assert len(obj.data.vertices) == len(source.data.vertices)
    assert not obj.modifiers and not obj.vertex_groups
    roles = ['AUTHOR_Chest'] + [f'AUTHOR_{role}.{side}' for side in ('L', 'R')
                               for role in ('ShoulderBridge', 'UpperArm', 'Forearm')]
    source_names = {g.index: g.name for g in source.vertex_groups}
    ownership = np.zeros((len(source.data.vertices), len(roles)), dtype=np.float32)
    for vertex in source.data.vertices:
        row = [(source_names[g.group], g.weight) for g in vertex.groups if g.weight > 0]
        assert row and all(name in roles for name, _ in row)
        assert abs(sum(w for _, w in row)-1) < 1e-6
        for name, weight in row: ownership[vertex.index, roles.index(name)] = weight
    fields = mesh_four(body, rig, require_four=False)
    chest = {f'DEF-spine{suffix}' for suffix in ('', '.001', '.002', '.003', '.004', '.005', '.006')}
    body.data.calc_loop_triangles()
    body_points = [v.co.copy() for v in body.data.vertices]
    triangles = [tuple(t.vertices) for t in body.data.loop_triangles]
    names = sorted({n for row in fields for n, _ in row})
    lookup = {name: i for i, name in enumerate(names)}
    groups = {name: obj.vertex_groups.new(name=name) for name in names}
    blended = np.zeros((len(obj.data.vertices), len(names)), dtype=np.float32)
    distances = np.empty(len(obj.data.vertices), dtype=np.float32)
    diagnostics = []
    for domain, role in enumerate(roles):
        selected = np.flatnonzero(ownership[:, domain] > 0)
        if not len(selected): continue
        if role == 'AUTHOR_Chest': allowed, sign = chest, 0
        else:
            part, side = role.removeprefix('AUTHOR_').split('.')
            sign = 1 if side == 'L' else -1
            stems = {'ShoulderBridge': ('shoulder', 'upper_arm'),
                     'UpperArm': ('shoulder', 'upper_arm'),
                     'Forearm': ('forearm', 'hand')}[part]
            allowed = {f'DEF-{stem}.{side}{suffix}' for stem in stems for suffix in ('', '.001')}
            if part == 'ShoulderBridge': allowed |= {'DEF-spine.002', 'DEF-spine.003'}
        mass = [sum(w for name, w in row if name in allowed) for row in fields]
        candidates = [tri for tri in triangles
                      if (not sign or all(body_points[i].x*sign > 0 for i in tri))
                      and sum(mass[i] for i in tri)/3 >= .5]
        assert candidates, ('Empty anatomical donor domain', role)
        tree = BVHTree.FromPolygons(body_points, candidates, all_triangles=True)
        for index in selected:
            point, _, face, distances[index] = tree.find_nearest(obj.data.vertices[int(index)].co)
            assert point is not None
            tri = candidates[face]
            bary = barycentric_transform(point, *(body_points[i] for i in tri),
                                         Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1)))
            bary = [max(0, float(w)) for w in bary]
            total = sum(bary); assert total > 0
            for vertex, coefficient in zip(tri, bary):
                for name, weight in fields[vertex]:
                    blended[index, lookup[name]] += weight*coefficient/total*ownership[index, domain]
        diagnostics.append({'sourceDomain': role, 'garmentVertices': len(selected),
                            'bodyDonorTriangles': len(candidates),
                            'nearestBodyDistanceMetres': {'maximum': float(distances[selected].max()),
                                'median': float(np.median(distances[selected]))}})
    assert np.max(abs(blended.sum(1)-1)) < 2e-5 and np.isfinite(blended).all()
    strongest = np.argsort(blended, axis=1, kind='stable')[:, -4:]
    coefficients = np.take_along_axis(blended, strongest, axis=1)
    loss = 1-coefficients.sum(1)
    coefficients /= coefficients.sum(1)[:, None]
    for index, (columns, values) in enumerate(zip(strongest, coefficients)):
        for column, weight in zip(columns, values):
            if weight > 0: groups[names[column]].add([index], float(weight), 'REPLACE')
    arm = obj.modifiers.new('SelectedHoodieSemanticNative75', 'ARMATURE')
    arm.object = rig
    arm.use_deform_preserve_volume = False
    arm.use_bone_envelopes = False
    obj.parent = rig
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = Matrix.Identity(4)
    mesh_four(obj, rig)
    return {'method': 'Nearest native-body face barycentric fields blended by all seven original source-role weights; prune FOUR and normalize',
            'sourceBodyWeightsUnchanged': True, 'garmentWeightsQuantized': False,
            'sourceBodyMaximumPositiveInfluences': max(map(len, fields)),
            'maximumRemovedGarmentMassAtFourPrune': float(loss.max()),
            'distanceIsDiagnosticOnly': True, 'domains': diagnostics}


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 2
    manifest_path, out = (Path(value).resolve() for value in args)
    manifest = json.loads(manifest_path.read_text())
    assert manifest['accepted'] is False and manifest.get('ready') is True and not out.exists()
    targets = [name for unit in manifest['units'] for name in unit['objects'].values()]
    assert len(targets) == len(set(targets)) and set(targets) == EXPECTED-{'RiderBody', 'RiderHoodie'}
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-complete-engine01')
    for row in pins(manifest): pin(row)
    for unit in manifest['units']:
        if 'contextUnit' in unit:
            actual = json.loads(pin(unit['contextUnit']).read_text())
            assert actual['native'] == unit['native'] and set(actual['visible']) == set(unit['objects'])
            assert actual['expectedPBRHashes'] == unit['expectedPBRHashes']
    assembly = runpy.run_path(str(pin(manifest['assemblyHelper'])))
    shape = runpy.run_path(str(pin(manifest['shapeHelper'])))
    signature = runpy.run_path(str(pin(manifest['bodySignatureHelper'])))['signature']
    bpy.ops.wm.open_mainfile(filepath=str(pin(manifest['native'])))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert body.matrix_world.is_identity and rig.matrix_world.is_identity
    assert len(body.data.vertices) == manifest['bodyVertices'] and len(rig.data.bones) == 75
    assert rig.animation_data is None and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    before_body = signature(body, rig)
    canonical_rest = assembly['rest'](rig)
    with bpy.data.libraries.load(str(pin(manifest['canonical'])), link=False) as (_, selected):
        selected.objects = ['RiderSkeleton']
    canonical = selected.objects[0]
    assert assembly['rest'](canonical) == canonical_rest
    bpy.data.objects.remove(canonical, do_unlink=True)
    hoodie = bpy.data.objects[manifest['hoodie']['object']]
    source = bpy.data.objects[manifest['hoodie']['semanticSource']]
    assert len(hoodie.data.vertices) == 716971
    hoodie_before = shape['geometry_uv_signature'](hoodie.data, positions=False)
    # Save the posed derivative's existing object affine in its local positions
    # before native75 binding; this preserves world geometry and all UV/topology.
    affine = hoodie.matrix_world.copy()
    world_before = np.empty(len(hoodie.data.vertices)*3, dtype=np.float32)
    hoodie.data.vertices.foreach_get('co', world_before)
    world_before = world_before.reshape((-1,3)).astype(float)@np.asarray(affine.to_3x3()).T+np.asarray(affine.translation)
    hoodie.data.transform(affine)
    hoodie.matrix_world = Matrix.Identity(4)
    hoodie.data.update()
    world_after = np.empty(len(hoodie.data.vertices)*3, dtype=np.float32)
    hoodie.data.vertices.foreach_get('co', world_after)
    affine_error = float(np.max(np.linalg.norm(world_after.reshape((-1,3))-world_before, axis=1)))
    assert affine_error < 1e-6
    hoodie_positions = shape['geometry_uv_signature'](hoodie.data)
    hoodie_maps = assembly['packed_maps'](hoodie)
    assert set(manifest['hoodie']['expectedPBRHashes']) <= {v['sha256'] for v in hoodie_maps.values()}
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH' and obj not in (body, hoodie):
            obj.hide_render = True; obj.hide_set(True)
            if obj.name in EXPECTED: obj.name = 'BeforeCompleteMerge__'+obj.name
    hoodie.name = 'RiderHoodie'
    binding = bind_hoodie(hoodie, source, body, rig)
    assert shape['geometry_uv_signature'](hoodie.data, positions=False) == hoodie_before
    assert shape['geometry_uv_signature'](hoodie.data) == hoodie_positions
    assert assembly['packed_maps'](hoodie) == hoodie_maps
    garments, records = [hoodie], []
    for unit in manifest['units']:
        with bpy.data.libraries.load(str(pin(unit['native'])), link=False) as (available, selected):
            assert set(unit['objects']) <= set(available.objects)
            selected.objects = list(unit['objects'])
        for original, obj in zip(unit['objects'], selected.objects):
            assert obj.type == 'MESH' and obj.matrix_world.is_identity
            assert all(m.type in ('ARMATURE', 'TRIANGULATE') for m in obj.modifiers)
            arms = [m for m in obj.modifiers if m.type == 'ARMATURE']
            assert len(arms) == 1 and assembly['rest'](arms[0].object) == canonical_rest
            assert arms[0].object.matrix_world.is_identity
            assert all(b.matrix_basis.is_identity for b in arms[0].object.pose.bones)
            mesh_four(obj, rig, require_four=False)
            # Preserve the original full-field native; condition only this
            # appended delivery derivative for the engine FOUR contract.
            conditioning = limit_four(obj, rig)
            maps = assembly['packed_maps'](obj)
            assert maps and set(unit['expectedPBRHashes']) <= {v['sha256'] for v in maps.values()}
            bpy.context.scene.collection.objects.link(obj)
            obj.name = unit['objects'][original]
            obj.parent = rig; obj.matrix_parent_inverse = Matrix.Identity(4)
            obj.matrix_world = Matrix.Identity(4)
            arms[0].object = rig; arms[0].use_deform_preserve_volume = False
            arms[0].show_viewport = arms[0].show_render = True
            obj.hide_render = obj.hide_viewport = False; obj.hide_set(False)
            garments.append(obj)
            records.append({'source': unit['native'], 'sourceObject': original, 'object': obj.name,
                            'vertices': len(obj.data.vertices), 'polygons': len(obj.data.polygons),
                            'actualSelectedPackedMaps': maps, 'fourAndExact75Rest': True,
                            'deliveryFourConditioning': conditioning})
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and obj != rig:
            obj.hide_render = True
            if obj.name in bpy.context.scene.objects: obj.hide_set(True)
    for obj in [body]+garments:
        obj['acceptedArt'] = False; obj['privateSelectedCompleteReview'] = True
        obj.hide_render = obj.hide_viewport = False; obj.hide_set(False)
    assert {o.name for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render} == EXPECTED
    assert signature(body, rig) == before_body and assembly['rest'](rig) == canonical_rest
    out.mkdir(parents=True)
    native = out/'complete-selected-native75.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    report = {'accepted': False, 'status': 'COMPLETE_SELECTED_NATIVE75_SAVED_PLAYED_REVIEW_PENDING',
              'native': {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)},
              'recipeSHA256': sha(__file__), 'manifestSHA256': sha(manifest_path),
              'bodyAnd75BeforeAfterExact': before_body, 'bodyVertices': len(body.data.vertices),
              'hoodieWorldGeometryPreservedByObjectAffineFreezeMaximumM': affine_error,
              'hoodieSourceObjectAffine': [list(row) for row in affine],
              'hoodieTopologyUVAndOriginalPBRExact': True, 'hoodieBinding': binding,
              'hoodiePackedMaps': hoodie_maps, 'garments': records, 'visibleMeshes': sorted(EXPECTED),
              'limits': ['All R0-R5 open. Parent alone judges moving appearance.',
                         'Full immutable anatomy reference retained; equipped mask is a render derivative.',
                         'No normal-player assets or delivery gate promoted.']}
    for row in pins(manifest): pin(row)
    (out/'merge.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'native': report['native'], 'visibleMeshes': report['visibleMeshes']}), flush=True)


if __name__ == '__main__': main()
