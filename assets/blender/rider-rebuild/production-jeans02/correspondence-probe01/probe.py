"""One pelvis-only selected-to-active correspondence sample, three 1024 maps.
Original aligned donor and enclosing production target remain unchanged.
"""
import hashlib
import json
import runpy
import sys
import traceback
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[5]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(row):
    path = ROOT / row['path']
    assert path.is_file() and sha(path) == row['sha256'], ('Changed input', row)
    return path


def matched_views(scene, body, receiver, source, out, report, helpers):
    scene.cycles.samples = 8; scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100; scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('PelvisCorrespondenceWorld'); world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .24, .28, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .55; scene.world = world
    aim = helpers['aim']
    for label, position, energy in [('Key', (2, -3, 4), 650), ('Fill', (-3, -2, 2), 450), ('Rim', (0, 3, 3), 700)]:
        data = bpy.data.lights.new('Probe' + label, 'AREA'); data.energy, data.size = energy, 3
        obj = bpy.data.objects.new(data.name, data); scene.collection.objects.link(obj)
        obj.location = position; aim(obj, (0, 0, .925))
    camera = bpy.data.objects.new('PelvisCorrespondenceCamera', bpy.data.cameras.new('PelvisCorrespondenceCamera'))
    scene.collection.objects.link(camera); scene.camera = camera
    camera.data.type, camera.data.ortho_scale = 'ORTHO', .52
    report['photos'] = []
    for label, garment in [('mappedPelvis', receiver), ('originalSelectedPelvis', source)]:
        for obj in scene.objects:
            if obj.type == 'MESH': obj.hide_render = obj not in (body, garment)
        body.hide_render = False; garment.hide_render = False; garment.hide_set(False)
        for view, location in [('front', (1.1, -3, 1)), ('back', (-1.1, 3, 1)), ('profile', (3, 0, 1))]:
            camera.location = location; aim(camera, (0, 0, .925))
            path = out / (label + '-' + view + '.png'); scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            report['photos'].append({'variant': label, 'view': view, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})
            helpers['write'](out, report)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 2
    intake_path = Path(args[0]).resolve(); intake = json.loads(intake_path.read_text())
    out = Path(args[1]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-jeans02/correspondence-probe01')
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'PREFLIGHT', 'native': intake['native'],
              'probeSHA256': sha(__file__), 'intakeSHA256': sha(intake_path), 'maps': {}, 'photos': [],
              'coverage': 'Pelvis only: receiver centres Z>.84; original selected source centres Z>.80',
              'unprobed': ['Left leg', 'Right leg', 'Underbody saddle belowZ.84'],
              'limits': ['First correspondence sample only; no whole-garment/PBR/fit/motion/player acceptance.',
                         'Dense-source body enclosure is not a selected-to-active prerequisite.',
                         'Configured rays remain unproved; no geometry/cage/ray escalation or retry.']}
    write = lambda: (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    try:
        assert intake['accepted'] is False and intake['resolution'] == 1024 and intake['region'] == 'pelvis'
        assert intake['bakeSettings'] == {'selectedToActive': True, 'useCage': False,
            'extrusionMetres': .018, 'maximumRayMetres': .045, 'marginPixels': 16, 'normalSpace': 'TANGENT'}
        for row in [intake[k] for k in ('native', 'nativeFields', 'dense', 'matchedInspection')] + list(intake['helpers'].values()) + list(intake['maps'].values()): pin(row)
        inspected = json.loads(pin(intake['matchedInspection']).read_text())
        assert inspected['native'] == intake['native'] and len(inspected['photos']) == 6
        for photo in inspected['photos']: pin(photo)
        bpy.ops.wm.open_mainfile(filepath=str(pin(intake['native'])))
        target, source, body, rig = [bpy.data.objects[n] for n in ('RiderJeans', 'AlignedSelectedDenseJeans', 'RiderBody', 'RiderSkeleton')]
        assert target.get('productionJeansRecipe') == 'rockhop-native-local-gusset-v2'
        assert target.get('selectedAppearanceAuthority') == intake['dense']['sha256']
        assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75 and not body.hide_get() and not body.hide_render
        helpers = runpy.run_path(str(pin(intake['helpers']['pbr'])))
        local = runpy.run_path(str(pin(intake['helpers']['localAuthor'])))
        original = runpy.run_path(str(pin(intake['helpers']['originalAuthor'])))
        target_before = helpers['shape'](target, local); source_before = helpers['shape'](source, local)
        body_before = original['signature'](body, rig)
        maps = helpers['selected_maps'](source, intake)
        scene = bpy.context.scene; scene.frame_set(1); scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
        scene.cycles.samples = 1; scene.render.threads_mode, scene.render.threads = 'FIXED', 2
        settings = scene.render.bake
        settings.use_selected_to_active = True; settings.use_cage = False
        settings.cage_extrusion = .018; settings.max_ray_distance = .045; settings.margin = 16
        settings.normal_space = 'TANGENT'
        report['actualBakeSettings'] = {'useSelectedToActive': settings.use_selected_to_active,
            'useCage': settings.use_cage, 'extrusionMetres': settings.cage_extrusion,
            'maximumRayMetres': settings.max_ray_distance, 'marginPixels': settings.margin}
        graph = bpy.context.evaluated_depsgraph_get()
        evaluated = source.copy(); evaluated.data = bpy.data.meshes.new_from_object(source.evaluated_get(graph), depsgraph=graph)
        scene.collection.objects.link(evaluated)
        for modifier in list(evaluated.modifiers): evaluated.modifiers.remove(modifier)
        selected = helpers['regional_copy'](evaluated, 'OriginalSelectedPelvisProbe', lambda p: p.z > .80)
        receiver = helpers['regional_copy'](target, 'MappedPelvisCorrespondenceProbe', lambda p: p.z > .84)
        data = evaluated.data; bpy.data.objects.remove(evaluated, do_unlink=True); bpy.data.meshes.remove(data)
        material = source.data.materials[0].copy(); selected.data.materials.clear(); selected.data.materials.append(material)
        sn, sl = material.node_tree.nodes, material.node_tree.links
        output, principled = sn.get('Material Output'), sn.get('Principled BSDF')
        emission = sn.new('ShaderNodeEmission'); copied_maps = {label: sn[node.name] for label, node in maps.items()}
        destination = bpy.data.materials.new('ActualSelectedPelvisProbePBR'); destination.use_nodes = True
        receiver.data.materials.clear(); receiver.data.materials.append(destination)
        dn, dl = destination.node_tree.nodes, destination.node_tree.links
        image_node = dn.new('ShaderNodeTexImage'); dn.active = image_node
        report.update(status='PELVIS_THREE_MAP_PROBE_RUNNING', sourceFaces=len(selected.data.polygons), receiverFaces=len(receiver.data.polygons), regionalBakes=[])
        bpy.ops.wm.save_as_mainfile(filepath=str(out / 'pre-probe-native.blend')); write()
        baked = {}
        for label, kind in [('albedo', 'EMIT'), ('metallicRoughness', 'EMIT'), ('normal', 'NORMAL')]:
            image = bpy.data.images.new('PelvisProbe_' + label, width=1024, height=1024, alpha=True)
            image.colorspace_settings.name = 'sRGB' if label == 'albedo' else 'Non-Color'
            image_node.image = image
            if kind == 'EMIT':
                sl.new(copied_maps[label].outputs['Color'], emission.inputs['Color']); sl.new(emission.outputs[0], output.inputs['Surface'])
            else: sl.new(principled.outputs[0], output.inputs['Surface'])
            bpy.ops.object.select_all(action='DESELECT'); receiver.select_set(True); selected.select_set(True)
            bpy.context.view_layer.objects.active = receiver; settings.use_clear = True
            bpy.ops.object.bake(type=kind)
            path = out / (label + '.png'); image.filepath_raw, image.file_format = str(path), 'PNG'; image.save(); image.pack()
            pixels = np.empty(1024 * 1024 * 4, dtype=np.float32); image.pixels.foreach_get(pixels)
            pixels = pixels.reshape(-1, 4)
            report['maps'][label] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'size': 1024,
                'rawAlphaBelowHalfPixels': int((pixels[:, 3] < .5).sum()),
                'rawNearZeroRGBPixels': int((np.max(np.abs(pixels[:, :3]), axis=1) < 1e-7).sum()),
                'statisticsMeaning': 'Raw atlas diagnostics include intentionally unbaked leg UV/background; not global ray-hit or failure counts'}
            report['regionalBakes'].append({'region': 'pelvis', 'map': label, 'kind': kind}); baked[label] = image
            write(); bpy.ops.wm.save_as_mainfile(filepath=str(out / 'partial-probe.blend'))
        bs = dn.get('Principled BSDF'); image_node.image = baked['albedo']; dl.new(image_node.outputs['Color'], bs.inputs['Base Color'])
        mr = dn.new('ShaderNodeTexImage'); mr.image = baked['metallicRoughness']
        split = dn.new('ShaderNodeSeparateColor'); dl.new(mr.outputs[0], split.inputs[0]); dl.new(split.outputs['Green'], bs.inputs['Roughness']); dl.new(split.outputs['Blue'], bs.inputs['Metallic'])
        normal = dn.new('ShaderNodeTexImage'); normal.image = baked['normal']; convert = dn.new('ShaderNodeNormalMap')
        dl.new(normal.outputs[0], convert.inputs['Color']); dl.new(convert.outputs[0], bs.inputs['Normal'])
        sl.new(principled.outputs[0], output.inputs['Surface'])
        assert helpers['shape'](target, local) == target_before and helpers['shape'](source, local) == source_before
        assert original['signature'](body, rig) == body_before
        helpers['selected_maps'](source, intake)
        for obj in scene.objects:
            if obj.type == 'MESH': obj.hide_render = obj not in (body, receiver)
        body.hide_render = False; receiver.hide_render = False
        receiver['correspondenceProbeOnly'] = True; receiver['coveredRegion'] = 'pelvis only; original receiver UV preserved'
        path = out / 'pelvis-correspondence-probe.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(path))
        report.update(status='MAPPED_PELVIS_SAVED_BEFORE_CLOSE_VIEWS', resultNative={'path': str(path.relative_to(ROOT)), 'sha256': sha(path)},
            targetGeometryUVFullFourExact=True, originalSourceGeometryUVFieldsMapsExact=True, bodyAnd75RestUntouched=True,
            targetStateSHA256=target_before, originalSourceStateSHA256=source_before, body75StateSHA256=body_before)
        write(); matched_views(scene, body, receiver, selected, out, report, helpers)
        assert helpers['shape'](target, local) == target_before and helpers['shape'](source, local) == source_before
        assert original['signature'](body, rig) == body_before and sha(pin(intake['native'])) == intake['native']['sha256']
        report['status'] = 'PELVIS_ONLY_ACTUAL_PBR_PROBE_AND_MATCHED_VIEWS_SAVED_PARENT_REVIEW_PENDING'; write()
    except BaseException as error:
        report.update(status='FAILED_ACTUAL_PELVIS_PROBE_NO_RETRY', error=repr(error), traceback=traceback.format_exc()); write()
        if (out / 'pre-probe-native.blend').exists():
            try:
                for image in bpy.data.images:
                    if image.name.startswith('PelvisProbe_'): image.pack()
                bpy.ops.wm.save_as_mainfile(filepath=str(out / 'failed-probe.blend'))
            except BaseException as save_error:
                report['failedCheckpointError'] = repr(save_error); write()
        raise


if __name__ == '__main__': main()
