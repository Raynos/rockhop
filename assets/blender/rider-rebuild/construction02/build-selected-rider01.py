"""Fit real clothing to the original wearer, then construct the real neck join."""
import hashlib
import json
import math
import runpy
import struct
from pathlib import Path

# Deliberately unset until a verified actual glove checkpoint is available.
# The source unit's receipt and SHA are the authority, never an old proxy.
GLOVE_SOURCE = None
AUTHOR_OBJECTS = {'RiderBody', 'RiderHoodie', 'RiderJeans',
                  'ActualSelectedGlove.L', 'ActualSelectedGlove.R',
                  'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}


def geometryFingerprint(obj):
    digest = hashlib.sha256()
    for vertex in obj.data.vertices: digest.update(struct.pack('<3f', *vertex.co))
    for polygon in obj.data.polygons:
        digest.update(struct.pack('<2I', len(polygon.vertices), polygon.material_index))
        digest.update(struct.pack('<' + 'I' * len(polygon.vertices), *polygon.vertices))
    for normal in obj.data.corner_normals: digest.update(struct.pack('<3f', *normal.vector))
    for layer in obj.data.uv_layers:
        for value in layer.data: digest.update(struct.pack('<2f', *value.uv))
    source = obj.data.attributes.get('_SOURCE_VERTEX_ID')
    if source:
        for value in source.data: digest.update(struct.pack('<i', value.value))
    return digest.hexdigest()


def canonicalizeSelectedFields(objects, rig, out):
    import numpy as np

    exporter = Path('/Applications/Blender.app/Contents/Resources/5.2/scripts/addons_core/io_scene_gltf2/blender/exp')
    pins = {'primitive_extract.py': '55e14cbe849b0c4ec5545c85a1aae3d8c2c7d65eade67de43eb1a43b05738684',
            'primitive_attributes.py': '815331d39cdf06e73ae110e9921ebfc8cb37825290843cbcbf4d1a7559899e5d'}
    assert all(hashlib.sha256((exporter / name).read_bytes()).hexdigest() == digest for name, digest in pins.items())
    cutoff = .0001; grid = 1 << 24; minimum = math.floor(cutoff * grid) + 1
    source_objects, measurements = {}, {}
    for obj in sorted(objects, key=lambda obj: obj.name):
        before = geometryFingerprint(obj)
        names = {group.index: group.name for group in obj.vertex_groups}
        originals = [[(names[g.group], g.weight) for g in vertex.groups if g.weight > 0]
                     for vertex in obj.data.vertices]
        finals, dropped_rows, max_removed, max_delta, max_rounding, changed, floor_corrections = [], 0, 0., 0., 0., 0, 0
        for row in originals:
            assert 1 <= len(row) <= 4 and all(name in rig.data.bones for name, _ in row)
            assert all(math.isfinite(weight) and weight > 0 for _, weight in row)
            assert abs(sum(weight for _, weight in row) - 1) < 2e-5, 'Malformed source field cannot be hidden by canonicalization'
            source = dict(row); kept = sorted((name, weight) for name, weight in row if weight > cutoff)
            assert 1 <= len(kept) <= 4
            total = sum(weight for _, weight in kept)
            ideal = [weight / total * grid for _, weight in kept]
            counts = [max(minimum, math.floor(value)) for value in ideal]
            remainder = grid - sum(counts)
            if remainder > 0:
                for i in sorted(range(len(kept)), key=lambda i: (-(ideal[i] - counts[i]), kept[i][0]))[:remainder]:
                    counts[i] += 1
            elif remainder < 0:
                i = max(range(len(kept)), key=lambda i: (counts[i], kept[i][0]))
                counts[i] += remainder; floor_corrections += 1
            assert sum(counts) == grid and all(count >= minimum for count in counts)
            final = {name: count / grid for (name, _), count in zip(kept, counts)}
            values = np.zeros(4, dtype=np.float32)
            values[:len(final)] = [weight for _, weight in sorted(final.items(), key=lambda item: -item[1])]
            assert values.sum(dtype=np.float32) == 1
            assert np.array_equal(values, values / values.sum(dtype=np.float32))
            removed = sum(weight for _, weight in row if weight <= cutoff)
            dropped_rows += bool(removed); max_removed = max(max_removed, removed)
            delta = max(abs(source.get(name, 0) - final.get(name, 0)) for name in set(source) | set(final))
            max_delta = max(max_delta, delta); changed += bool(delta)
            max_rounding = max(max_rounding, max(abs(weight / total - final[name]) for name, weight in kept))
            finals.append(final)
        obj.vertex_groups.clear()
        groups = {name: obj.vertex_groups.new(name=name) for name in sorted({name for row in finals for name in row})}
        for index, row in enumerate(finals):
            for name, weight in row.items(): groups[name].add([index], weight, 'REPLACE')
        identity = obj.data.attributes.get('_NATIVE_ID') or obj.data.attributes.new('_NATIVE_ID', 'INT', 'POINT')
        identity.data.foreach_set('value', list(range(len(obj.data.vertices))))
        assert geometryFingerprint(obj) == before, ('Skin finishing changed geometry/source identities', obj.name)
        measurements[obj.name] = {'vertices': len(finals), 'cutoffAffectedRows': dropped_rows,
                                  'maximumRemovedMass': max_removed, 'maximumNamedWeightDelta': max_delta,
                                  'quantizationMaximumAbsoluteDelta': max_rounding, 'changedRows': changed,
                                  'minimumFloorCorrectionRows': floor_corrections, 'geometryAndSourceIDSHA256': before}
        source_objects[obj.name] = {'geometryAndSourceIDSHA256': before, 'preCanonicalNamedFields': originals}
    source_path = Path(out) / 'selected-field-source01.json'
    source_path.write_text(json.dumps({'accepted': False, 'cutoff': cutoff, 'gridDenominator': grid,
                                      'minimumRetainedGridCount': minimum, 'objects': source_objects}, separators=(',', ':')) + '\n')
    return {'accepted': False, 'cutoff': cutoff, 'comparison': 'drop weight <= cutoff', 'gridDenominator': grid,
            'minimumRetainedGridCount': minimum, 'installedExporterPins': pins, 'objects': measurements,
            'preCanonicalFields': {'path': str(source_path), 'sha256': hashlib.sha256(source_path.read_bytes()).hexdigest()},
            'geometrySourceIDsAnd75RestPreserved': True,
            'limits': ['Explicit final skin derivative; source fields/masters remain unchanged.',
                       'Exact native/export field readback and played deformation require independent checks.']}


def appendSelectedGloves(rig, source):
    import bpy
    from mathutils import Matrix

    receipt_path = Path(source['receiptPath']).resolve()
    digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert digest(receipt_path) == source['receiptSHA256']
    receipt = json.loads(receipt_path.read_text())
    assert receipt['originalBodyPositionsFieldsAnd75RestUnchanged'] is True
    native = Path(receipt['native']['path']).resolve()
    assert digest(native) == receipt['native']['sha256']
    expected = ['ActualSelectedGlove.L', 'ActualSelectedGlove.R']
    with bpy.data.libraries.load(str(native), link=False) as (available, selected):
        assert set(expected) <= set(available.objects)
        selected.objects = expected
    objects, materials = [], []
    for obj in selected.objects:
        assert obj.type == 'MESH' and obj.name in expected
        assert obj.matrix_world.is_identity
        arms = [m for m in obj.modifiers if m.type == 'ARMATURE']
        assert len(arms) == 1 and len(obj.modifiers) == 1
        old = arms[0].object
        assert old is not None and len(old.data.bones) == len(rig.data.bones) == 75
        for bone in old.data.bones:
            new = rig.data.bones[bone.name]
            assert (bone.parent.name if bone.parent else None) == (new.parent.name if new.parent else None)
            if not bone.name.startswith('SoleSocket.'):
                assert bone.matrix_local == new.matrix_local
                assert bone.head_local == new.head_local and bone.tail_local == new.tail_local
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = rig
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_world = Matrix.Identity(4)
        arms[0].object = rig
        arms[0].use_deform_preserve_volume = False
        obj.hide_viewport = False; obj.hide_render = False; obj.hide_set(False)
        for mat in obj.data.materials:
            assert mat is not None and mat.use_nodes
            images = [n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
            assert images and all(image.packed_file for image in images)
            if mat not in materials: materials.append(mat)
        objects.append(obj)
    return {'objects': objects, 'materials': materials,
            'report': {'accepted': False, 'verifiedSource': source, 'native': receipt['native'],
                       'construction': receipt['construction'], 'rebaked': False,
                       'shared75NonSoleRestExactlyEqual': True}}


def buildWardrobe(body, rig, out):
    import bpy
    assert GLOVE_SOURCE is not None, 'Verified actual glove source required; incomplete outfit cannot export'
    root = Path(__file__).resolve().parents[4]
    actual_clothes = root / 'assets/blender/rider-rebuild/donor-wardrobe01/build-wardrobe.py'
    actual_boots = root / 'assets/blender/rider-rebuild/donor-hand-foot01/build-hand-foot.py'
    actual_face = Path(__file__).with_name('build-selected-face01.py')
    assert hashlib.sha256(actual_clothes.read_bytes()).hexdigest() == '7ded4e43a627e23b3a7bfecb8327eb11025b399081b2d023a3f7f472898ec7b0'
    assert hashlib.sha256(actual_boots.read_bytes()).hexdigest() == '2dfbe2b64c19d4b1b592ae4eed67087a6f3faf3d187af7559e05da5ea6b45c01'
    assert hashlib.sha256(actual_face.read_bytes()).hexdigest() == 'c58e38f94db9c66d29763c679a3f205096b4ab8493eb52f543650b469f89d8cd'
    assert len(body.data.vertices) == 10582
    clothes = runpy.run_path(str(actual_clothes))['buildWardrobe'](body, rig, out)
    boots = runpy.run_path(str(actual_boots))['buildHandFoot'](body, rig, out)
    gloves = appendSelectedGloves(rig, GLOVE_SOURCE)
    assert len(body.data.vertices) == 10582
    face = runpy.run_path(str(actual_face))['buildFace'](body, rig, out)
    records = [clothes, boots, gloves, face]
    actual = {obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj.parent == rig}
    assert actual == AUTHOR_OBJECTS, ('Exactly seven actual author objects required', actual)
    rest = [(bone.name, tuple(bone.head_local), tuple(bone.tail_local), tuple(tuple(row) for row in bone.matrix_local))
            for bone in rig.data.bones]
    canonical = canonicalizeSelectedFields([obj for obj in bpy.context.scene.objects if obj.name in actual], rig, out)
    assert rest == [(bone.name, tuple(bone.head_local), tuple(bone.tail_local), tuple(tuple(row) for row in bone.matrix_local))
                    for bone in rig.data.bones]
    return {'objects': [obj for record in records for obj in record['objects']],
            'materials': [mat for record in records for mat in record['materials']],
            'report': {'accepted': False, 'selectedClothes': clothes['report'],
                       'selectedBoots': boots['report'], 'selectedGloves': gloves['report'],
                       'selectedFace': face['report'], 'completeAuthorObjects': sorted(actual),
                       'canonicalFinalFields': canonical,
                       'limits': ['Complete source transport only; parent moving art/contact review required.']},
            'reportPath': str(Path(out) / 'report.json')}
