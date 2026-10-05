"""Paired PBR source context, exact thin cycle guides; no source editing or fit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def display(points):
    result = np.asarray(points)[..., [0, 2, 1]].copy()
    result[..., 1] *= -1
    return result


def smooth(t):
    return t * t * (3 - 2 * t)


def main():
    parser = argparse.ArgumentParser()
    for name in ['opening', 'opening-sha256', 'localization', 'localization-sha256', 'preparation', 'preparation-sha256', 'out']:
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    pins = [(args.opening, args.opening_sha256), (args.localization, args.localization_sha256), (args.preparation, args.preparation_sha256)]
    assert all(sha(path) == expected for path, expected in pins)
    opening = json.loads(Path(args.opening).read_text())
    localization = json.loads(Path(args.localization).read_text())
    preparation = json.loads(Path(args.preparation).read_text())
    donor = next(row for row in preparation['items'] if row['item'] == 'gloves')
    source_pin = opening['candidate']
    assert source_pin == localization['source']
    assert source_pin['sha256'] == '8379004e394bbae110f495c13bfc12a205977061d13cefdcc8ee24c6e5343782'
    assert sha(source_pin['path']) == source_pin['sha256']
    source = np.load(source_pin['path'])
    xyz, faces, uv = source['vertices'], source['faces'], source['cornerUVPrototype']
    assert len(xyz) == 8000 and len(faces) == 14543
    assert np.array_equal(uv, source['uv'][faces])
    assert not opening['accepted'] and not localization['acceptedWearable']
    for pin in opening['maps'].values():
        assert sha(pin['path']) == pin['sha256']
    assert donor['originalPBR']['roughnessFactor'] == 1 and donor['originalPBR']['metallicFactor'] == 1
    assert sha(donor['source']['path']) == donor['source']['sha256']
    # Material metadata is parsed only from immutable donor JSON, never imported
    # as source geometry. Any unhandled texture transform/material channel stops.
    payload = Path(donor['source']['path']).read_bytes()
    json_size = int.from_bytes(payload[12:16], 'little')
    gltf = json.loads(payload[20:20 + json_size])
    primitive = gltf['meshes'][0]['primitives'][0]
    assert 'NORMAL' not in primitive['attributes']
    donor_material = gltf['materials'][primitive['material']]
    assert donor_material['pbrMetallicRoughness'] == donor['originalPBR']
    assert not any(key in donor_material for key in ['normalTexture', 'occlusionTexture', 'emissiveTexture', 'extensions'])
    assert donor_material.get('alphaMode', 'OPAQUE') == 'OPAQUE'
    assert donor_material.get('emissiveFactor', [0, 0, 0]) == [0, 0, 0]
    assert donor['originalPBR'].get('baseColorFactor', [1, 1, 1, 1]) == [1, 1, 1, 1]
    assert all(set(donor['originalPBR'][key]) <= {'index', 'texCoord'} and donor['originalPBR'][key].get('texCoord', 0) == 0 for key in ['baseColorTexture', 'metallicRoughnessTexture'])
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    mesh = bpy.data.meshes.new('All retained source08 triangles')
    mesh.from_pydata(display(xyz).tolist(), [], faces.tolist())
    mesh.update()
    source_object = bpy.data.objects.new('Immutable open source08 PBR context', mesh)
    bpy.context.collection.objects.link(source_object)
    layer = mesh.uv_layers.new(name='Donor UV0 display mapping')
    display_uv = uv.copy()
    display_uv[..., 1] = 1 - display_uv[..., 1]
    layer.data.foreach_set('uv', display_uv.astype(np.float32).reshape(-1))
    material = bpy.data.materials.new('Immutable donor basecolor plus metallic roughness')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes['Principled BSDF']
    base = nodes.new('ShaderNodeTexImage')
    base.image = bpy.data.images.load(opening['maps']['baseColor']['path'], check_existing=False)
    base.image.colorspace_settings.name = 'sRGB'
    base.interpolation = 'Linear'
    packed = nodes.new('ShaderNodeTexImage')
    packed.image = bpy.data.images.load(opening['maps']['metallicRoughness']['path'], check_existing=False)
    packed.image.colorspace_settings.name = 'Non-Color'
    packed.interpolation = 'Linear'
    separated = nodes.new('ShaderNodeSeparateColor')
    separated.mode = 'RGB'
    links.new(base.outputs['Color'], principled.inputs['Base Color'])
    links.new(packed.outputs['Color'], separated.inputs['Color'])
    links.new(separated.outputs['Green'], principled.inputs['Roughness'])
    links.new(separated.outputs['Blue'], principled.inputs['Metallic'])
    principled.inputs['Alpha'].default_value = 1
    principled.inputs['Transmission Weight'].default_value = 0
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = False
    guides, guide_scope = [], []
    for cycle, color in zip(localization['localizedCycles'][:2], [(0.02, 0.9, 1., 1), (1., .38, .03, 1)]):
        ids = cycle['sourceVertexIds']
        assert np.array_equal(xyz[ids], np.array(cycle['sourceXYZ']))
        curve = bpy.data.curves.new('Exact source homology cycle', type='CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth = .0004
        curve.bevel_resolution = 0
        curve.resolution_u = 1
        spline = curve.splines.new('POLY')
        spline.points.add(len(ids) - 1)
        spline.use_cyclic_u = True
        for point, position in zip(spline.points, display(xyz[ids])):
            point.co = (*position, 1)
        guide = bpy.data.objects.new('Thin cycle class' + str(cycle['homologyClass']), curve)
        bpy.context.collection.objects.link(guide)
        guide.visible_shadow = False
        guide_material = bpy.data.materials.new('Semitransparent source edge guide')
        guide_material.use_nodes = True
        gnodes, glinks = guide_material.node_tree.nodes, guide_material.node_tree.links
        gnodes.clear()
        transparent = gnodes.new('ShaderNodeBsdfTransparent')
        emission = gnodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = color
        emission.inputs['Strength'].default_value = 1
        mix = gnodes.new('ShaderNodeMixShader')
        mix.inputs[0].default_value = .65
        output = gnodes.new('ShaderNodeOutputMaterial')
        glinks.new(transparent.outputs[0], mix.inputs[1])
        glinks.new(emission.outputs[0], mix.inputs[2])
        glinks.new(mix.outputs[0], output.inputs['Surface'])
        curve.materials.append(guide_material)
        guides.append(guide)
        guide_scope.append({'class': cycle['homologyClass'], 'sourceVertexIds': ids, 'bevelRadiusSourceUnits': .0004, 'emissionMixtureFraction': .65, 'depthTestedNotXray': True, 'sourceEdgeCenterlineExact': True})
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 6
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.use_persistent_data = True
    scene.view_settings.view_transform = 'Standard'
    scene.world.color = (.16, .16, .16)
    for location, power in [((2, -3, 4), 500), ((-3, -2, 2), 350), ((1, 3, 3), 500), ((0, 1, -3), 220)]:
        light = bpy.data.lights.new('Silent area', 'AREA')
        light.energy, light.size = power, 4
        lamp = bpy.data.objects.new('Silent area', light)
        bpy.context.collection.objects.link(lamp)
        lamp.location = location
        lamp.rotation_euler = (Vector((0, 0, 0)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data = bpy.data.cameras.new('Continuous source camera')
    camera_data.type = 'ORTHO'
    camera_data.clip_start, camera_data.clip_end = .001, 100
    camera = bpy.data.objects.new('Continuous source camera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    whole = (xyz.min(0) + xyz.max(0)) / 2
    cycle_ids = sorted(set(sum([c['sourceVertexIds'] for c in localization['localizedCycles'][:2]], [])))
    region = xyz[cycle_ids].mean(0)
    paths = []
    for index in range(20):
        angle = 2 * np.pi * index / 19
        location = whole + np.array([3 * np.sin(angle), .4, 3 * np.cos(angle)])
        paths.append({'stage': 'full source moving orbit', 'sourceLocation': location.tolist(), 'sourceTarget': whole.tolist(), 'orthoScale': 2.7})
    for index in range(20):
        t = smooth((index + 1) / 20)
        angle, radius = 2 * np.pi + np.pi * t, 3 + (.7 - 3) * t
        target = whole + (region - whole) * t
        location = target + np.array([radius * np.sin(angle), .4 + (.12 - .4) * t, radius * np.cos(angle)])
        paths.append({'stage': 'continuous travel to cuff source feature', 'sourceLocation': location.tolist(), 'sourceTarget': target.tolist(), 'orthoScale': 2.7 + (.28 - 2.7) * t})
    for index in range(20):
        angle = 3 * np.pi + .2 * np.pi * (index + 1) / 20
        location = region + np.array([.7 * np.sin(angle), .12, .7 * np.cos(angle)])
        paths.append({'stage': 'close cuff feature moving arc', 'sourceLocation': location.tolist(), 'sourceTarget': region.tolist(), 'orthoScale': .28})
    assert len(paths) == 60 and all(paths[i]['sourceLocation'] != paths[i - 1]['sourceLocation'] for i in range(1, 60))
    assert all(not ((np.array(pose['sourceLocation']) >= xyz.min(0) - .01) & (np.array(pose['sourceLocation']) <= xyz.max(0) + .01)).all() for pose in paths)
    original = np.empty(len(xyz) * 3, np.float32)
    mesh.vertices.foreach_get('co', original)
    assert np.array_equal(original.reshape(-1, 3), display(xyz))
    assert np.array_equal(np.array([polygon.vertices[:] for polygon in mesh.polygons]), faces)
    uv_readback = np.empty(len(faces) * 6, np.float32)
    layer.data.foreach_get('uv', uv_readback)
    assert np.array_equal(uv_readback.reshape(-1, 3, 2), display_uv.astype(np.float32))
    frames = {panel: out / panel for panel in ['plain', 'marked']}
    for folder in frames.values():
        folder.mkdir()
    records = []
    for index, pose in enumerate(paths):
        camera.location = display(np.array(pose['sourceLocation']))
        target = display(np.array(pose['sourceTarget']))
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera_data.ortho_scale = pose['orthoScale']
        bpy.context.view_layer.update()
        record = {'index': index, 'assignedSourcePose': pose, 'actualCameraWorld': [list(row) for row in camera.matrix_world], 'actualOrthoScale': float(camera_data.ortho_scale), 'panels': {}}
        for panel in ['plain', 'marked']:
            for guide in guides:
                guide.hide_render = panel == 'plain'
            assert not source_object.hide_render and not source_object.hide_viewport
            file = frames[panel] / f'{index:03}.png'
            scene.render.filepath = str(file)
            bpy.ops.render.render(write_still=True)
            record['panels'][panel] = {'path': str(file), 'sha256': sha(file), 'actualCameraWorld': [list(row) for row in camera.matrix_world]}
        assert record['panels']['plain']['actualCameraWorld'] == record['panels']['marked']['actualCameraWorld']
        records.append(record)
    final = np.empty_like(original)
    mesh.vertices.foreach_get('co', final)
    assert np.array_equal(final, original)
    assert np.array_equal(np.array([polygon.vertices[:] for polygon in mesh.polygons]), faces)
    assert all(sha(path) == expected for path, expected in pins) and sha(source_pin['path']) == source_pin['sha256']
    assert all(sha(pin['path']) == pin['sha256'] for pin in opening['maps'].values())
    report = {'acceptedWearable': False, 'status': 'PAIRED_PBR_SOURCE_CONTEXT_RENDERED_PLAYED_PARENT_REVIEW_PENDING', 'recipeSHA256': sha(__file__), 'source': source_pin, 'maps': opening['maps'], 'originalPBR': donor['originalPBR'], 'sourceTrianglesPresent': len(faces), 'sourceHiddenTriangles': 0, 'sourceGeometryBeforeAfterExact': True, 'sourceUVFloat32DisplayReadbackExact': True, 'uvFloat64ToFloat32MaximumResidual': float(abs(display_uv - display_uv.astype(np.float32)).max()), 'gltfImageConvention': 'Blender loop V=1-sourceV; source UV array unmodified.', 'normalPolicy': 'Flat actual triangle normals. Original donor declares no NORMAL; no smooth/custom normal or geometry edit.', 'guideScope': guide_scope, 'cameraPaths': paths, 'frames': records, 'fps': 12, 'cameraPositionsOutsideWholeSourceAABB': True, 'limits': ['Full retained source08 rest geometry with immutable donor PBR maps and prior prototype UV projection; UV seams/bake and engine material parity unqualified.', 'Unmarked/marked same-camera panels preserve unobscured interpretation. Thin semitransparent source-edge guides are depth-tested, not X-ray or new mesh cuts.', 'Genus1 is not itself a defect. Played source context may reveal legitimate cuff strap/detail/passage or unresolved morphology; source interpretation belongs to parent.', 'No geometric cavity clearance/free-volume/mouth traversal/fit/skin/grip/native-rider/engine/device acceptance. No source object mutation, source concealment or further removal.']}
    (out / 'render.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
