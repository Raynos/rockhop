"""One frozen cuff sculpt, actual saved dense binding, then shape-only merge.

Parent serialized CPU2 only. No bind, weights, rig, UV/PBR or other-part edit.
blender -b -t 2 --python-exit-code 1 --python author.py -- CONTROLS FRESH_OUT
"""
import hashlib
import json
import runpy
import struct
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
EXPECTED = {'RiderBody','RiderHoodie','RiderJeans','ActualSelectedGlove.L','ActualSelectedGlove.R','ActualSelectedBoot.L','ActualSelectedBoot.R'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']; assert sha(path) == row['sha256'], ('Changed input',row); return path


def fixed(obj):
    """Exact topology/UV/PBR/fields digest deliberately excluding positions."""
    h = hashlib.sha256(); h.update(json.dumps([g.name for g in obj.vertex_groups]).encode())
    for v in obj.data.vertices:
        for g in v.groups: h.update(struct.pack('<If',g.group,g.weight))
    for p in obj.data.polygons:
        h.update(struct.pack('<II',p.material_index,len(p.vertices)))
        h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    for uv in obj.data.uv_layers:
        h.update(uv.name.encode())
        values = np.empty(len(uv.data)*2,dtype=np.float32); uv.data.foreach_get('uv',values); h.update(values.tobytes())
    for mat in obj.data.materials:
        assert mat and mat.use_nodes
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                assert node.image.packed_file; h.update(hashlib.sha256(node.image.packed_file.data).digest())
    return h.hexdigest()


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    controls_path, out = (Path(p).resolve() for p in args); control = json.loads(controls_path.read_text())
    assert control['acceptedArt'] is False and not out.exists()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/glove-cuff-fit05')
    for key in ('master','fullGloves','sourceGLB','placement','guideHelpers','fingerprintHelper','restHelper','sourceGuide','localControls','diagnosis'): pin(control[key])
    for row in control['hands'].values(): pin(row['offsets']); pin(row['previousLocalOffsets'])
    helper = runpy.run_path(str(pin(control['guideHelpers']))); rest = runpy.run_path(str(pin(control['restHelper'])))['rest']
    geometry = runpy.run_path(str(pin(control['fingerprintHelper'])))['geometry']
    placement = json.loads(pin(control['placement']).read_text()); dense = np.load(pin(placement['pins']['denseSelected']))
    bpy.ops.wm.open_mainfile(filepath=str(pin(control['fullGloves']))); old_rig = bpy.data.objects['RiderSkeleton']
    assert len(old_rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in old_rig.pose.bones)
    original_rest = rest(old_rig); guides = {}; full = {}; full_positions = {}; full_fixed = {}
    for side in ('L','R'):
        arrays = np.load(pin(control['hands'][side]['offsets'])); guide = bpy.data.objects['Gloves__LocalAnatomicalGuide04.'+side]
        assert np.array_equal(helper['points'](guide.data),arrays['original'].astype(np.float32))
        assert not guide.modifiers and len(guide.data.vertices) == 8000
        full[side] = bpy.data.objects['Gloves__LocallySculptedSelected04.'+side]
        full_positions[side] = helper['points'](full[side].data); full_fixed[side] = fixed(full[side])
        guide.data.vertices.foreach_set('co',arrays['corrected'].astype(np.float32).ravel()); guide.data.update()
        actual = helper['points'](guide.data); faces = arrays['faces']
        helper['positive_cotangent_geometry'](actual,faces)
        before_normals=np.cross(arrays['original'][faces[:,1]]-arrays['original'][faces[:,0]],arrays['original'][faces[:,2]]-arrays['original'][faces[:,0]])
        after_normals=np.cross(actual[faces[:,1]]-actual[faces[:,0]],actual[faces[:,2]]-actual[faces[:,0]])
        assert np.all(np.einsum('ij,ij->i',before_normals,after_normals)>0), 'Actual float32 guide reverses an original triangle'
        guides[side] = guide
    source = bpy.data.objects['Gloves__UntouchedSelectedDenseTransfer.R']; driver = bpy.data.objects['Gloves__SelectedGuideTransferDriver.R']
    source_name, driver_name = source.name, driver.name
    assert source.modifiers['ActualSelectedDenseSurfaceDeform'].is_bound
    assert source.modifiers['ActualSelectedDenseSurfaceDeform'].target == driver
    assert source.matrix_world == driver.matrix_world
    out.mkdir(parents=True); checkpoint = out/'editable-cuff-guides-before-transfer.blend'
    # Include actual bound stock and unchanged original full fields. No dense
    # evaluation has happened; the selected guides are already editable here.
    bpy.data.libraries.write(str(checkpoint),set(guides.values())|set(full.values())|{source,driver},fake_user=True,compress=True)
    report = {'acceptedArt':False,'operation':control['operation'],'recipeSHA256':sha(__file__),'controlsSHA256':sha(controls_path),
        'sourceMaster':control['master'],'parentNative':control['master'],'sourceFullGloves':control['fullGloves'],
        'changedPositionObjects':['ActualSelectedGlove.L','ActualSelectedGlove.R'],
        'guidesSavedBeforeDenseTransfer':{'path':str(checkpoint.relative_to(ROOT)),'sha256':sha(checkpoint)},
        'newBindCalls':0,'newWeightComputations':0,'bakesExecuted':0,'hands':{},
        'limits':['Unaccepted bilateral cuff source; parent judges actual Garage and wrist/grip motion.','Nearest surface signs are local diagnostics, not a universal containment or device gate.']}
    (out/'guide-checkpoint.json').write_text(json.dumps(report,indent=2)+'\n')
    deltas = {}
    for side in ('L','R'):
        arrays = np.load(pin(control['hands'][side]['offsets']))
        copied_driver = driver.copy(); copied_driver.data = driver.data.copy(); bpy.context.collection.objects.link(copied_driver)
        copied_source = source.copy(); copied_source.data = source.data.copy(); bpy.context.collection.objects.link(copied_source)
        transfer = copied_source.modifiers['ActualSelectedDenseSurfaceDeform']; transfer.target = copied_driver
        assert transfer.is_bound and copied_source.matrix_world == copied_driver.matrix_world == source.matrix_world
        copied_driver.hide_set(False); helper['active'](copied_source)
        results = []
        for label, points in [('before',arrays['original']),('after',arrays['corrected'])]:
            copied_driver.data.vertices.foreach_set('co',points.astype(np.float32).ravel()); copied_driver.data.update()
            with helper['modifier_log'](out/f'transfer-{side}-{label}.log'):
                evaluated = helper['evaluated_mesh'](copied_source); helper['check_error'](transfer)
            results.append(helper['points'](evaluated)); bpy.data.meshes.remove(evaluated)
        assert len(results[0]) == len(results[1]) == len(dense['vertices']) and np.isfinite(results[1]).all()
        delta = results[1]-results[0]
        assert np.array_equal(delta[dense['vertices'][:,1]>=-.52],np.zeros_like(delta[dense['vertices'][:,1]>=-.52])), 'Non-cuff source moved'
        linear = np.asarray(placement['hands'][side]['initialPlacement']['linear']); deltas[side] = delta@linear.T
        assert np.any(deltas[side] != 0)
        report['hands'][side] = {'guide':control['hands'][side], 'denseMovedVertices':int(np.count_nonzero(np.linalg.norm(delta,axis=1))),
            'maximumDenseWorldOffsetM':float(np.linalg.norm(deltas[side],axis=1).max()),'nonCuffDensePositionsExactlyUnchanged':True,
            'fullFieldsTopologyUVPBRDigest':full_fixed[side]}
    bpy.ops.wm.open_mainfile(filepath=str(pin(control['master']))); scene = bpy.context.scene; rig = bpy.data.objects['RiderSkeleton']
    assert rest(rig) == original_rest and rig.animation_data is None
    assert {o.name for o in scene.objects if o.type == 'MESH' and not o.hide_render} == EXPECTED
    protected = [o for o in scene.objects if o.name in EXPECTED-{'ActualSelectedGlove.L','ActualSelectedGlove.R'} or o.name == 'RiderBody__FullAnatomyReference']
    protected_before = {o.name:geometry(o) for o in protected}; rig_before = rest(rig)
    render_fixed = {side:fixed(bpy.data.objects['ActualSelectedGlove.'+side]) for side in ('L','R')}
    names = ['Gloves__LocalAnatomicalGuide04.'+s for s in ('L','R')]+['Gloves__LocallySculptedSelected04.'+s for s in ('L','R')]+[source_name,driver_name]
    # The saved checkpoint supplies the permanent edited guides, actual stock
    # transfer binding and original FULL fields; all imported aids remain hidden.
    # Blender replaces requested strings with loaded datablocks in-place.
    # Keep the immutable name list separate from that mutable request list.
    with bpy.data.libraries.load(str(checkpoint),link=False) as (_,loaded): loaded.objects = list(names)
    imported = dict(zip(names,loaded.objects)); imported_rigs = set()
    for old_name, obj in imported.items():
        assert obj is not None; scene.collection.objects.link(obj); obj.hide_render=True; obj.hide_set(True)
        if old_name.startswith('Gloves__LocalAnatomicalGuide04.'):
            obj.name='Gloves__CuffFit05Guide.'+old_name[-1]
        elif old_name.startswith('Gloves__LocallySculptedSelected04.'):
            side=old_name[-1]; obj.name='Gloves__CuffFit05FullFieldReference.'+side
            for arm in [m for m in obj.modifiers if m.type=='ARMATURE']:
                assert rest(arm.object) == rig_before; imported_rigs.add(arm.object); arm.object=rig
            world=obj.matrix_world.copy(); obj.parent=rig; obj.matrix_world=world
            obj.data.vertices.foreach_set('co',(full_positions[side]+deltas[side]).astype(np.float32).ravel()); obj.data.update()
            assert fixed(obj)==full_fixed[side]
        else: obj.name='Gloves__CuffFit05Bound'+('DenseSource.R' if old_name==source_name else 'Driver.R')
    for imported_rig in imported_rigs:
        assert imported_rig != rig; bpy.data.objects.remove(imported_rig,do_unlink=True)
    hood=bpy.data.objects['RiderHoodie']; hood.data.calc_loop_triangles()
    tree=BVHTree.FromPolygons([v.co.copy() for v in hood.data.vertices],[tuple(t.vertices) for t in hood.data.loop_triangles],all_triangles=True)
    for side, witness in [('L',199533),('R',199531)]:
        obj=bpy.data.objects['ActualSelectedGlove.'+side]
        before=helper['points'](obj.data); assert np.array_equal(before,full_positions[side])
        obj.data.vertices.foreach_set('co',(before+deltas[side]).astype(np.float32).ravel()); obj.data.update()
        assert fixed(obj)==render_fixed[side]
        point=obj.data.vertices[witness].co; nearest,normal,face,distance=tree.find_nearest(point)
        signed=(point-nearest).dot(normal); report['hands'][side]['denseCuffWitnessAfter']={'nativeVertex':witness,'point':list(point),'nearestHoodie':list(nearest),'signedNormalDistanceM':signed,'distanceM':distance}
        assert signed <= 0., ('Demonstrated exposed dense cuff witness still outside',side,signed)
    assert rest(rig)==rig_before and protected_before=={o.name:geometry(o) for o in protected}
    assert {o.name for o in scene.objects if o.type=='MESH' and not o.hide_render}==EXPECTED
    native=out/'complete-selected-cuff-fit05.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    report.update(native={'path':str(native.relative_to(ROOT)),'sha256':sha(native)},visibleMeshes=sorted(EXPECTED),
        protectedPartFingerprints=protected_before,renderGloveTopologyUVPBRAndDeliveryFieldsUnchanged=render_fixed,
        exact75RestUnchanged=True,status='ACTUAL_SELECTED_CUFF_NATIVE_SAVED_PLAYED_REVIEW_PENDING')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'native':report['native'],'hands':{s:r['denseCuffWitnessAfter'] for s,r in report['hands'].items()}}),flush=True)


if __name__ == '__main__': main()
