"""Save the fitted actual original selected PBR donor BEFORE views or bake.

Source only until parent checkpoints this file and grants a serial CPU2 lease.
blender -b -t 2 --python-exit-code 1 --python prepare_dense.py -- controls.json OUT
OUT is a fresh production-hoodie02 harness leaf. No render, bake or target edit.
"""
import hashlib
import json
import runpy
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[4]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gltf_intake(path):
    with path.open('rb') as handle:
        magic, version, total, size, kind = struct.unpack('<5I', handle.read(20))
        assert magic == 0x46546C67 and version == 2 and kind == 0x4E4F534A
        doc = json.loads(handle.read(size))
    assert total == path.stat().st_size
    assert len(doc['nodes']) == len(doc['meshes']) == 1
    node = doc['nodes'][0]
    assert node['mesh'] == 0 and not any(k in node for k in ('matrix', 'rotation', 'translation', 'scale', 'skin'))
    primitive = doc['meshes'][0]['primitives']
    assert len(primitive) == 1
    position = doc['accessors'][primitive[0]['attributes']['POSITION']]
    return {'positionAccessor': position, 'node': node,
            'materials': doc['materials'], 'images': doc['images']}


def bounds(points):
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]


def pbr_state(objects):
    """Hashes channel connections, source image bytes and UVs; no new maps."""
    materials = {}
    for obj in objects:
        for material in obj.data.materials:
            assert material and material.use_nodes
            nodes = []
            for node in material.node_tree.nodes:
                record = {'name': node.name, 'type': node.type,
                          'inputs': {s.name: list(s.default_value) if hasattr(s.default_value, '__len__') else s.default_value
                                     for s in node.inputs if hasattr(s, 'default_value')
                                     and (isinstance(s.default_value, (float, int, str))
                                          or hasattr(s.default_value, '__len__'))}}
                if node.type == 'TEX_IMAGE' and node.image:
                    image = node.image
                    assert image.packed_file, 'Original imported image bytes must remain packed'
                    record['image'] = {'name': image.name, 'size': list(image.size),
                                       'colorspace': image.colorspace_settings.name,
                                       'packedSHA256': hashlib.sha256(image.packed_file.data).hexdigest()}
                nodes.append(record)
            links = sorted((l.from_node.name, l.from_socket.identifier,
                            l.to_node.name, l.to_socket.identifier) for l in material.node_tree.links)
            materials[material.name] = {'nodes': nodes, 'links': links}
    uv = {o.name: hashlib.sha256(json.dumps(
        {layer.name: [list(item.uv) for item in layer.data] for layer in o.data.uv_layers},
        separators=(',', ':')).encode()).hexdigest() for o in objects}
    state = {'materials': materials, 'uvSHA256': uv}
    return state, hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def target_state(obj, geometry):
    # Target fields, UVs, material bindings and modifiers remain frozen too.
    state = {'geometry': geometry(obj), 'matrix': [list(r) for r in obj.matrix_world],
             'materials': [m.name if m else None for m in obj.data.materials],
             'faceMaterials': [f.material_index for f in obj.data.polygons],
             'uv': {u.name: [list(v.uv) for v in u.data] for u in obj.data.uv_layers},
             'groups': [g.name for g in obj.vertex_groups],
             'weights': [[[g.group, g.weight] for g in v.groups] for v in obj.data.vertices],
             'modifiers': [(m.name, m.type, m.show_render, m.show_viewport,
                            m.object.name if m.type == 'ARMATURE' and m.object else None)
                           for m in obj.modifiers]}
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 2
    controls_path, out = (Path(a).resolve() for a in args)
    controls = json.loads(controls_path.read_text())
    assert out.is_relative_to(ROOT/controls['outputRoot']) and not out.exists()
    pins = controls['pins']
    for key, pin in pins.items():
        assert sha(ROOT/pin['path']) == pin['sha256'], ('Changed intake', key)
    spec = json.loads((ROOT/pins['frozenInputs']['path']).read_text())
    helpers = runpy.run_path(str(ROOT/pins['baseAuthor']['path']))
    for key in helpers['SOURCE_KEYS']:
        assert sha(ROOT/spec[key]['path']) == spec[key]['sha256'], ('Changed selected source', key)
    receipt = json.loads((ROOT/pins['authorReceipt']['path']).read_text())
    assert receipt['recipeSHA256'] == pins['repairAuthor']['sha256']
    assert receipt['native']['sha256'] == pins['authoredNative']['sha256']
    assert Path(receipt['native']['path']).resolve() == (ROOT/pins['authoredNative']['path']).resolve()
    assert {k: v for k, v in receipt['inputs'].items() if k != 'targetHemZ'} == spec
    spec['targetHemZ'] = receipt['inputs']['targetHemZ']
    original = ROOT/spec['originalDensePaint']['path']
    intake = gltf_intake(original)
    assert intake['positionAccessor']['count'] == controls['originalPositionVertices']
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/pins['authoredNative']['path']))
    body, rig, target = (bpy.data.objects[n] for n in ('RiderBody', 'RiderSkeleton', controls['targetObjectName']))
    assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
    signature, geometry = helpers['signature'], helpers['hoodie_geometry']
    before = signature(body, rig)
    assert before == receipt['bodyAnd75RigSignature']
    assert geometry(target) == receipt['targetGeometrySHA256']
    assert target['productionHoodieRecipeSHA256'] == pins['repairAuthor']['sha256']
    frozen_target = target_state(target, geometry)
    prior = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(original))
    dense = [o for o in bpy.data.objects if o not in prior and o.type == 'MESH']
    assert len(dense) == 1
    donor = dense[0]
    donor.name = controls['denseObjectName']
    assert donor.name == controls['denseObjectName']
    assert len(donor.data.vertices) == controls['originalPositionVertices']
    assert len(donor.data.polygons) > 500000
    pbr_before, pbr_sha = pbr_state(dense)
    image_records = [n['image'] for m in pbr_before['materials'].values()
                     for n in m['nodes'] if 'image' in n]
    assert image_records and all(r['size'] == controls['originalImagesExpectedPixels'] for r in image_records)
    points = [donor.matrix_world @ v.co for v in donor.data.vertices]
    imported_bounds = bounds(points)
    # Identity glTF node: world coordinates must equal standard Y-up conversion.
    axis = Matrix(controls['gltfToBlenderRows'])
    acc = intake['positionAccessor']
    expected_bounds = bounds([axis @ Vector((x, y, z))
                              for x in (acc['min'][0], acc['max'][0])
                              for y in (acc['min'][1], acc['max'][1])
                              for z in (acc['min'][2], acc['max'][2])])
    axis_error = max(abs(a-b) for row_a, row_b in zip(imported_bounds, expected_bounds)
                     for a, b in zip(row_a, row_b))
    assert axis_error < 1e-5, ('Importer axes differ from frozen dense controls', axis_error)
    donor.parent = None
    donor.matrix_world = Matrix.Identity(4)
    targets = helpers['target_arms'](rig)
    for vertex, point in zip(donor.data.vertices, points):
        vertex.co = helpers['fit_point'](point, spec, targets, dense=True)[0]
    donor.data.update()
    donor.hide_render = False
    donor.hide_viewport = False
    donor.hide_set(False)
    donor['unaccepted'] = True
    donor['actualSelectedOriginalDenseSHA256'] = spec['originalDensePaint']['sha256']
    donor['frozenFitHelperSHA256'] = pins['baseAuthor']['sha256']
    donor['fitStage'] = 'PREBAKE_ACTUAL_ORIGINAL_PBR_FOR_PARENT_INSPECTION'
    assert pbr_state(dense)[1] == pbr_sha, 'Original donor PBR or UV changed'
    assert signature(body, rig) == before
    assert target_state(target, geometry) == frozen_target
    assert not body.hide_render and not body.hide_viewport and not body.hide_get()
    out.mkdir(parents=True)
    native = out/'fitted-original-dense-pbr.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    report = {'accepted': False, 'stage': 'FITTED_ACTUAL_ORIGINAL_DENSE_PBR_SAVED_BEFORE_VIEWS_OR_BAKE',
              'recipeSHA256': sha(__file__), 'controlsSHA256': sha(controls_path),
              'pins': pins, 'originalDenseSHA256': spec['originalDensePaint']['sha256'],
              'native': {'path': str(native), 'sha256': sha(native)},
              'targetObject': target.name, 'denseObjects': [donor.name],
              'originalIntake': intake, 'importedBoundsM': imported_bounds,
              'expectedImportedBoundsM': expected_bounds, 'axisMaximumErrorM': axis_error,
              'fittedBoundsM': bounds([v.co for v in donor.data.vertices]),
              'originalPBRAndUV': pbr_before, 'originalPBRAndUVSHA256': pbr_sha,
              'originalPBRAndUVUnchanged': True, 'targetUnchangedSHA256': frozen_target,
              'targetGeometrySHA256': geometry(target), 'bodyAnd75RigSignature': before,
              'completeBodyVisible': True, 'bodyAnd75RigUnchanged': True,
              'noAtlasOrBakeExecuted': True, 'limits': controls['limits']}
    (out/'prepare.json').write_text(json.dumps(report, indent=2)+'\n')
    for key, pin in pins.items():
        assert sha(ROOT/pin['path']) == pin['sha256'], ('Original intake changed', key)
    print('ACTUAL_ORIGINAL_DENSE_FITTED_PREBAKE', str(native), flush=True)


if __name__ == '__main__':
    main()
