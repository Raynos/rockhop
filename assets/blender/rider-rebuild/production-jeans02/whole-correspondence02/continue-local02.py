"""Continue saved whole correspondence; one local own-side crotch correction.
Original whole controls/pipeline are not rebuilt. Source only until parent lease.
"""
import hashlib
import json
import runpy
import sys
import traceback
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix
ROOT = Path(__file__).resolve().parents[5]
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024 * 1024): h.update(block)
    return h.hexdigest()
def pin(row):
    path = ROOT / row['path']
    assert path.is_file() and sha(path) == row['sha256'], ('Changed input', row)
    return path

def patch_right(proxy, cage, controls, pelvis_pairs, helpers, local):
    original_faces = set(controls['rightPatchOriginalReceiverFaces'])
    chosen = {int(v) for p in proxy.data.polygons if proxy.data.attributes['BakeOriginalFace'].data[p.index].value in original_faces for v in p.vertices}
    assert chosen and original_faces == {proxy.data.attributes['BakeOriginalFace'].data[p.index].value for p in proxy.data.polygons if any(v in chosen for v in p.vertices) and proxy.data.attributes['BakeOriginalFace'].data[p.index].value in original_faces}
    pinned = {obj.data.attributes['BakeOriginalVertex'].data[int(v)].value for pair in pelvis_pairs for obj in pair[2:4] for v in whole['used'](obj)}
    changed = []
    for obj in (proxy, cage):
        before = np.asarray([tuple(v.co) for v in obj.data.vertices], dtype=np.float32)
        changes = []; excluded_pelvis = []
        for index in sorted(chosen):
            vertex = obj.data.vertices[index]
            if vertex.co.x <= 0: continue
            original_id = obj.data.attributes['BakeOriginalVertex'].data[index].value
            if original_id in pinned:
                excluded_pelvis.append(original_id); continue
            scope = controls['rightPatchPositionBounds']
            assert all(lo < value < hi for lo,value,hi in zip(scope[0],vertex.co,scope[1])), tuple(vertex.co)
            old = list(vertex.co); vertex.co.x = -vertex.co.x
            assert (np.linalg.norm(np.asarray(vertex.co) - old) <= controls['maximumChangedVertexMetres'])
            changes.append({'vertex':index,'nativeVertex':original_id,'old':old,'new':list(vertex.co)})
        assert 0 < len(changes) <= controls['maximumChangedVertices']
        after = np.asarray([tuple(v.co) for v in obj.data.vertices], dtype=np.float32)
        untouched_ids = np.ones(len(before), dtype=bool); untouched_ids[[r['vertex'] for r in changes]] = False
        assert np.array_equal(before[untouched_ids], after[untouched_ids])
        assert all(obj.data.vertices[v].co.x <= 0 for v in chosen if obj.data.attributes['BakeOriginalVertex'].data[v].value not in pinned)
        obj.data.update(); obj.data.normals_split_custom_set([(0,0,0)] * len(obj.data.loops))
        obj['localOwnSideCorrectionControlsSHA256'] = sha(pin(intake['inputs']['localControls']))
        affected = {r['vertex'] for r in changes}
        incident_faces = sorted({obj.data.attributes['BakeOriginalFace'].data[p.index].value for p in obj.data.polygons if any(v in affected for v in p.vertices)})
        changed.append({'object':obj.name,'changes':changes,'otherPositionsExact':True,'excludedWorkingPelvisNativeVertexIDs':excluded_pelvis,'incidentOriginalReceiverFaces':incident_faces})
    assert local['topology'](proxy.data) == local['topology'](cage.data)
    assert local['uv_rows'](proxy) == local['uv_rows'](cage) and local['fields'](proxy) == local['fields'](cage)
    return changed

def capture(region, selected, proxy, cage, diag, intake, out):
    result, coverage, priority = whole['capture'](region, selected, proxy, cage, diag, intake, out)
    if region not in controls['rearUnderbody']: return result, coverage, priority
    path = ROOT / result['path']
    with np.load(path) as data: arrays = {key:data[key] for key in data.files}
    far = arrays['excessiveDistance']; allowed = np.zeros(len(far), dtype=bool)
    if far.any():
        known = controls['rearUnderbody'][region]
        index = np.flatnonzero(far); point, origin, hit = [arrays[k][index] for k in ('proxyPoint','cageOrigin','sourcePoint')]
        own = 1 if region == 'lower-L' else -1
        high = diag['mesh_arrays'](selected); source_ids = np.asarray([d.value for d in selected.data.attributes['BakeOriginalFace'].data])
        lookup = {int(source_ids[face]):i for i,face in enumerate(high['faces'])}
        triangles = high['vertices'][high['triangles'][[lookup[int(f)] for f in arrays['originalSourceFace'][index]]]]
        normal = np.cross(triangles[:,1]-triangles[:,0], triangles[:,2]-triangles[:,0]); normal /= np.linalg.norm(normal,axis=1)[:,None]
        normal_dot = np.sum(normal * arrays['rayDirection'][index], axis=1)
        approved = np.isin(arrays['receiverOriginalFace'][index],known['originalReceiverFaces']) & np.isin(arrays['originalSourceFace'][index],known['originalSourceFaces'])
        approved &= (point[:,0]*own>.01)&(point[:,0]*own<.03)&(point[:,1]>.115)&(point[:,1]<.14)&(point[:,2]>.805)&(point[:,2]<.835)
        approved &= (origin[:,1]>.14)&(origin[:,1]<.17)&(hit[:,0]*own>.01)&(hit[:,0]*own<.03)&(hit[:,1]>.05)&(hit[:,1]<.095)&(hit[:,2]>.80)&(hit[:,2]<.84)
        approved &= (normal[:,1]>.01)&(normal[:,2]<-.1)&(normal_dot<-.01)&(arrays['firstHitMetres'][index]<=controls['rearUnderbodyMaximumCaptureMetres'])
        allowed[index] = approved
    arrays['base80mmExceeded'] = far.copy(); arrays['semanticallyApprovedRearUnderbody'] = allowed
    arrays['excessiveDistance'] = far & ~allowed
    np.savez_compressed(path, **arrays)
    result.update(base80mmExceeded=int(far.sum()), semanticallyApprovedRearUnderbody=int(allowed.sum()), excessiveDistance=int(arrays['excessiveDistance'].sum()), sha256=sha(path),
        passed=not np.any(arrays['noHit']|arrays['oppositePhysicalRegion']|arrays['wrongSide']|arrays['excessiveDistance']))
    return result, coverage, priority

def main():
    global whole, controls, intake
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args)==2
    intake_path, out = [Path(p).resolve() for p in args]; intake = json.loads(intake_path.read_text())
    assert not intake['accepted'] and intake['resolution']==4096 and not out.exists()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/production-jeans02/whole-correspondence02')
    out.mkdir(parents=True)
    report = {'accepted':False,'status':'LOCAL_CONTINUATION_PREFLIGHT','authorSHA256':sha(__file__),'intakeSHA256':sha(intake_path),'capture':[],'regionalBakes':[],'maps':{},'limits':intake['limits']}
    write = lambda: (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    try:
        paths = {key:pin(row) for key,row in intake['inputs'].items()}
        whole = runpy.run_path(str(paths['wholeAuthor'])); controls = json.loads(paths['localControls'].read_text())
        assert not controls['accepted']; probe_intake = json.loads(paths['probeIntake'].read_text())
        for row in list(probe_intake['helpers'].values())+list(probe_intake['maps'].values()): pin(row)
        helpers=runpy.run_path(str(pin(probe_intake['helpers']['pbr']))); local=runpy.run_path(str(pin(probe_intake['helpers']['localAuthor']))); original=runpy.run_path(str(pin(probe_intake['helpers']['originalAuthor'])))
        old=runpy.run_path(str(paths['successfulAuthor'])); diag=runpy.run_path(str(paths['diagnosticSource']))
        prior=json.loads(paths['failedWholeReport'].read_text()); assert prior['authoredNative']==intake['inputs']['native'] and not prior['regionalBakes']
        bpy.ops.wm.open_mainfile(filepath=str(paths['native'])); assert list(bpy.app.version)==[5,2,1]
        target, source, body, rig = [bpy.data.objects[n] for n in ('RiderJeans','AlignedSelectedDenseJeans','RiderBody','RiderSkeleton')]
        assert all(obj.matrix_world==Matrix.Identity(4) for obj in (target,source,body,rig))
        before=[helpers['shape'](obj,local) for obj in (target,source)]; body_before=original['signature'](body,rig)
        assert before==prior['wearingTargetSourceStateSHA256'] and body_before==prior['body75StateSHA256']
        maps=helpers['selected_maps'](source,probe_intake); assert len(body.data.vertices)==10582 and len(rig.data.bones)==75
        scene=bpy.context.scene; scene.frame_set(1); scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=1; scene.render.threads_mode,scene.render.threads='FIXED',2
        pairs=[]
        for label,prefix in [('pelvis-front','Front'),('pelvis-rear','Rear'),('lower-L','LLower'),('lower-R','RLower')]:
            selected,proxy,cage,receiver=[bpy.data.objects[prefix+suffix] for suffix in ('OriginalSelectedSource','ProjectionReceiver','AuthoredCage','OriginalReceiverUVReference')]
            pairs.append((label,selected,proxy,cage,receiver))
        pelvis_before=[[helpers['shape'](obj,local) for obj in pair[1:]] for pair in pairs[:2]]
        unaffected_before=[[helpers['shape'](obj,local) for obj in pair[1:]] for pair in pairs[:3]]
        right_source_receiver_before=[helpers['shape'](pairs[3][i],local) for i in (1,4)]
        changes=patch_right(pairs[3][2],pairs[3][3],controls,pairs[:2],helpers,local)
        assert [[helpers['shape'](obj,local) for obj in pair[1:]] for pair in pairs[:3]]==unaffected_before
        assert [helpers['shape'](pairs[3][i],local) for i in (1,4)]==right_source_receiver_before
        assert [helpers['shape'](obj,local) for obj in (target,source)]==before and original['signature'](body,rig)==body_before
        editable=[bpy.data.objects[n] for n in ('JeansLowerProjectionControls','JeansLowerCaptureControls')]
        reference=bpy.data.objects['OriginalSelectedWholeJeansReference']
        path=out/'local-whole-correspondence-before-maps.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(path))
        report.update(status='LOCAL_EDITABLE_NATIVE_SAVED_BEFORE_GATE_MAPS', authoredNative={'path':str(path.relative_to(ROOT)),'sha256':sha(path)}, wearingTargetSourceStateSHA256=before,body75StateSHA256=body_before,localPairedOwnSideCorrection=changes,sourceGeometryUnchanged=True,workingPelvisGeometryExact=True)
        write(); coverages=[]; priorities=[]
        for label,selected,proxy,cage,_ in pairs:
            result,coverage,priority=capture(label,selected,proxy,cage,diag,intake,out)
            report['capture'].append(result);coverages.append(coverage);priorities.append(priority);write()
        assert all(row['passed'] for row in report['capture']), 'Local whole continuation capture rejected; no maps'
        owners_with_native_priority=whole['owners_with_native_priority']; matched_whole=whole['matched_whole']
        owners, multiplicity = owners_with_native_priority(coverages, priorities, old)
        report['UVAtlas'] = {'coveredPixels': int((multiplicity > 0).sum()), 'overlapPixels': int((multiplicity > 1).sum()), 'maximumMultiplicity': int(multiplicity.max()), 'policy': 'Original UV retained. Highest original face ID owns conflicts, matching ordinary last-face atlas writes. Raw regional maps and exact conflict mask persist; no UV/material acceptance inferred.'}
        np.savez_compressed(out / 'whole-atlas-ownership.npz', owners=owners, nativeUVSampleMultiplicity=multiplicity)
        material = source.data.materials[0].copy()
        sn, sl = (material.node_tree.nodes, material.node_tree.links)
        output, principled = (sn.get('Material Output'), sn.get('Principled BSDF'))
        emission = sn.new('ShaderNodeEmission')
        copied_maps = {label: sn[node.name] for label, node in maps.items()}
        for _, selected, _, _, _ in pairs:
            selected.data.materials.clear()
            selected.data.materials.append(material)
        destination = bpy.data.materials.new('OriginalSelectedWholeJeansPBR4K')
        destination.use_nodes = True
        dn, dl = (destination.node_tree.nodes, destination.node_tree.links)
        image_node = dn.new('ShaderNodeTexImage')
        dn.active = image_node
        for _, _, proxy, _, _ in pairs:
            proxy.data.materials.clear()
            proxy.data.materials.append(destination)
        settings = scene.render.bake
        settings.use_selected_to_active = True
        settings.use_cage = True
        settings.cage_extrusion = 0.018
        settings.max_ray_distance = 0
        settings.margin = 16
        settings.normal_space = 'TANGENT'
        report['actualBakeSettings'] = {'useCage': True, 'maximumRayMetres': 0, 'explicitSemanticCaptureGateMetres': intake['maximumCaptureMetres'], 'localKnownRearUnderbodyGateMetres':controls['rearUnderbodyMaximumCaptureMetres'], 'localGateMeaning':'Measured legitimate own-side first hits, frozen receiver/source faces, position and outward-normal checks; not Blender max_ray_distance.', 'marginPixels': 16}
        baked = {}
        size = intake['resolution']
        for label, kind in [('albedo', 'EMIT'), ('metallicRoughness', 'EMIT'), ('normal', 'NORMAL')]:
            if kind == 'EMIT':
                sl.new(copied_maps[label].outputs['Color'], emission.inputs['Color'])
                sl.new(emission.outputs[0], output.inputs['Surface'])
            else:
                sl.new(principled.outputs[0], output.inputs['Surface'])
            merged = np.zeros((size, size, 4), dtype=np.float32)
            for index, (region, selected, proxy, cage, _) in enumerate(pairs, 1):
                image = bpy.data.images.new('WholeSelected_' + region + '_' + label, width=size, height=size, alpha=True)
                image.colorspace_settings.name = 'sRGB' if label == 'albedo' else 'Non-Color'
                image_node.image = image
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        obj.hide_render = obj not in (body, selected, proxy, cage)
                bpy.ops.object.select_all(action='DESELECT')
                proxy.hide_set(False)
                selected.hide_set(False)
                proxy.select_set(True)
                selected.select_set(True)
                bpy.context.view_layer.objects.active = proxy
                settings.cage_object = cage
                settings.use_clear = True
                bpy.ops.object.bake(type=kind)
                path = out / (region + '-' + label + '.png')
                image.filepath_raw, image.file_format = (str(path), 'PNG')
                image.save()
                image.pack()
                pixels = diag['image_pixels'](image)
                chosen = owners == index
                merged[chosen] = pixels[chosen]
                report['regionalBakes'].append({'region': region, 'map': label, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'coveredNearZeroRGB': int(((coverages[index - 1] > 0) & (np.max(np.abs(pixels[:, :, :3]), 2) < 1e-07)).sum())})
                write()
                bpy.ops.wm.save_as_mainfile(filepath=str(out / 'partial-whole-selected.blend'))
            image = bpy.data.images.new('WholeSelectedCombined_' + label, width=size, height=size, alpha=True)
            image.colorspace_settings.name = 'sRGB' if label == 'albedo' else 'Non-Color'
            image.pixels.foreach_set(merged.ravel())
            image.update()
            path = out / (label + '.png')
            image.filepath_raw, image.file_format = (str(path), 'PNG')
            image.save()
            image.pack()
            baked[label] = image
            report['maps'][label] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'size': size, 'coveredNearZeroRGB': int(((multiplicity > 0) & (np.max(np.abs(merged[:, :, :3]), 2) < 1e-07)).sum())}
            write()
        sl.new(principled.outputs[0], output.inputs['Surface'])
        target.data.materials.clear()
        target.data.materials.append(destination)
        bs = dn.get('Principled BSDF')
        image_node.image = baked['albedo']
        dl.new(image_node.outputs['Color'], bs.inputs['Base Color'])
        mr = dn.new('ShaderNodeTexImage')
        mr.image = baked['metallicRoughness']
        split = dn.new('ShaderNodeSeparateColor')
        dl.new(mr.outputs[0], split.inputs[0])
        dl.new(split.outputs['Green'], bs.inputs['Roughness'])
        dl.new(split.outputs['Blue'], bs.inputs['Metallic'])
        normal = dn.new('ShaderNodeTexImage')
        normal.image = baked['normal']
        convert = dn.new('ShaderNodeNormalMap')
        dl.new(normal.outputs[0], convert.inputs['Color'])
        dl.new(convert.outputs[0], bs.inputs['Normal'])
        assert [helpers['shape'](obj, local) for obj in (target, source)] == before
        assert original['signature'](body, rig) == body_before
        assert [[helpers['shape'](obj, local) for obj in pair[1:]] for pair in pairs[:2]] == pelvis_before
        assert [[helpers['shape'](obj,local) for obj in pair[1:]] for pair in pairs[:3]] == unaffected_before
        assert [helpers['shape'](pairs[3][i],local) for i in (1,4)] == right_source_receiver_before
        helpers['selected_maps'](source, probe_intake)
        armature = [m for m in target.modifiers if m.type == 'ARMATURE']
        assert len(armature) == 1 and armature[0].object == rig
        assert all((0 < sum((g.weight > 0 for g in v.groups)) <= 4 for v in target.data.vertices))
        target['wholeSelectedPBRTransferUnaccepted'] = True
        for obj in scene.objects:
            if obj.type == 'MESH':
                obj.hide_render = obj not in (body, target)
        body.hide_render = False
        target.hide_render = False
        path = out / 'whole-selected-jeans.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
        fields = out / 'production-jeans-fields.npz'
        fields.write_bytes(paths['nativeFields'].read_bytes())
        native_row = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}
        report.update(status='WHOLE_ACTUAL_SELECTED_PBR_NATIVE_SAVED_BEFORE_CONTEXT', resultNative=native_row, finishedGarment={'object': target.name, 'vertices': len(target.data.vertices), 'polygons': len(target.data.polygons), 'stateSHA256': before[0], 'material': destination.name, 'packedMapSHA256': {k: v['sha256'] for k, v in report['maps'].items()}, 'modifier': {'name': armature[0].name, 'type': 'ARMATURE', 'target': rig.name, 'bones': len(rig.data.bones), 'preserveVolume': armature[0].use_deform_preserve_volume}, 'fields': {'path': str(fields.relative_to(ROOT)), 'sha256': sha(fields)}}, wearingGeometryUVFullFourAnd75Exact=True, originalSelectedSourceGeometryUVMapsExact=True, workingPelvisGeometryExact=True, dressedContext=intake['dressedContext'])
        unit = {'part': 'Jeans', 'native': native_row, 'visible': [target.name], 'reference': [source.name, reference.name], 'editingAids': [obj.name for obj in editable] + [obj.name for pair in pairs for obj in pair[2:4]], 'expectedPBRHashes': [v['sha256'] for v in report['maps'].values()], 'status': 'First whole selected4KPBR correspondence; actual parent art/fit/motion/device review pending'}
        (out / 'context-unit.json').write_text(json.dumps(unit, indent=2) + '\n')
        write()
        matched_whole(scene, body, target, reference, out, report, helpers)
        assert [helpers['shape'](obj, local) for obj in (target, source)] == before
        assert original['signature'](body, rig) == body_before
        for row in intake['inputs'].values():
            pin(row)
        report['status'] = 'ONE_WHOLE_SELECTED4K_CORRESPONDENCE_PARENT_REVIEW_PENDING'
        write()
    except BaseException as error:
        report.update(status='FAILED_ACTUAL_LOCAL_CONTINUATION_NO_RETRY', error=repr(error),traceback=traceback.format_exc());write();raise
if __name__=='__main__':main()
