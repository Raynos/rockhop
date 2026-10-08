"""Final connected cuff-sector sculpt, reused saved binding, shape-only merge.

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
    assert control['acceptedArt'] is False and control['ready'] is True and not out.exists()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/glove-cuff-fit06')
    for key in ('master','fullGloves','sourceGLB','placement','guideHelpers','fingerprintHelper','restHelper','sourceGuide','localControls','diagnosis','parentReceipt'): pin(control[key])
    for row in control['hands'].values(): pin(row['offsets']); pin(row['previousLocalOffsets'])
    helper = runpy.run_path(str(pin(control['guideHelpers']))); rest = runpy.run_path(str(pin(control['restHelper'])))['rest']
    geometry = runpy.run_path(str(pin(control['fingerprintHelper'])))['geometry']
    placement = json.loads(pin(control['placement']).read_text()); dense = np.load(pin(placement['pins']['denseSelected']))
    bpy.ops.wm.open_mainfile(filepath=str(pin(control['fullGloves']))); old_rig = bpy.data.objects['RiderSkeleton']
    assert len(old_rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in old_rig.pose.bones)
    original_rest = rest(old_rig); guides = {}; full = {}; full_positions = {}; full_fixed = {}
    for side in ('L','R'):
        arrays = np.load(pin(control['hands'][side]['offsets'])); guide = bpy.data.objects[control['sourceObjects']['guides'][side]]
        assert np.array_equal(helper['points'](guide.data),arrays['original'].astype(np.float32))
        assert not guide.modifiers and len(guide.data.vertices) == 8000
        full[side] = bpy.data.objects[control['sourceObjects']['fullFields'][side]]
        full_positions[side] = helper['points'](full[side].data); full_fixed[side] = fixed(full[side])
        guide.data.vertices.foreach_set('co',arrays['corrected'].astype(np.float32).ravel()); guide.data.update()
        actual = helper['points'](guide.data); faces = arrays['faces']
        helper['positive_cotangent_geometry'](actual,faces)
        before_normals=np.cross(arrays['original'][faces[:,1]]-arrays['original'][faces[:,0]],arrays['original'][faces[:,2]]-arrays['original'][faces[:,0]])
        after_normals=np.cross(actual[faces[:,1]]-actual[faces[:,0]],actual[faces[:,2]]-actual[faces[:,0]])
        assert np.all(np.einsum('ij,ij->i',before_normals,after_normals)>0), 'Actual float32 guide reverses an original triangle'
        protected = arrays['protectedGuideIds']
        assert np.array_equal(actual[protected], arrays['original'][protected]), 'Protected prior anatomy or lip anchor moved'
        guides[side] = guide
    source = bpy.data.objects[control['sourceObjects']['boundDense']]; driver = bpy.data.objects[control['sourceObjects']['boundDriver']]
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
        faces = dense['faces']
        before_tri, after_tri = results[0][faces].astype(float), results[1][faces].astype(float)
        before_normals = np.cross(before_tri[:,1]-before_tri[:,0], before_tri[:,2]-before_tri[:,0])
        after_normals = np.cross(after_tri[:,1]-after_tri[:,0], after_tri[:,2]-after_tri[:,0])
        dots = np.einsum('ij,ij->i', before_normals, after_normals)
        affected_faces = np.any(np.any(before_tri != after_tri, axis=2), axis=1)
        assert np.all(dots[affected_faces] > 0), ('Final mechanism has a dense orientation reversal; stop', side, int(np.sum(dots[affected_faces] <= 0)))
        delta = results[1]-results[0]
        assert np.array_equal(delta[dense['vertices'][:,1]>=-.52],np.zeros_like(delta[dense['vertices'][:,1]>=-.52])), 'Non-cuff source moved'
        linear = np.asarray(placement['hands'][side]['initialPlacement']['linear']); deltas[side] = delta@linear.T
        assert np.any(deltas[side] != 0)
        report['hands'][side] = {'guide':control['hands'][side], 'denseMovedVertices':int(np.count_nonzero(np.linalg.norm(delta,axis=1))),
            'maximumDenseWorldOffsetM':float(np.linalg.norm(deltas[side],axis=1).max()),'nonCuffDensePositionsExactlyUnchanged':True,
            'fullFieldsTopologyUVPBRDigest':full_fixed[side],
            'affectedDenseTriangles':int(affected_faces.sum()),'affectedDenseTriangleOrientationPreserved':True}
    bpy.ops.wm.open_mainfile(filepath=str(pin(control['master']))); scene = bpy.context.scene; rig = bpy.data.objects['RiderSkeleton']
    assert rest(rig) == original_rest and rig.animation_data is None
    assert {o.name for o in scene.objects if o.type == 'MESH' and not o.hide_render} == EXPECTED
    protected = [o for o in scene.objects if o.name in EXPECTED-{'ActualSelectedGlove.L','ActualSelectedGlove.R'} or o.name == 'RiderBody__FullAnatomyReference']
    protected_before = {o.name:geometry(o) for o in protected}; rig_before = rest(rig)
    render_fixed = {side:fixed(bpy.data.objects['ActualSelectedGlove.'+side]) for side in ('L','R')}
    names = [control['sourceObjects']['guides'][s] for s in ('L','R')]+[control['sourceObjects']['fullFields'][s] for s in ('L','R')]+[source_name,driver_name]
    # The saved checkpoint supplies the permanent edited guides, actual stock
    # transfer binding and original FULL fields; all imported aids remain hidden.
    # Blender replaces requested strings with loaded datablocks in-place.
    # Keep the immutable name list separate from that mutable request list.
    with bpy.data.libraries.load(str(checkpoint),link=False) as (_,loaded): loaded.objects = list(names)
    imported = dict(zip(names,loaded.objects)); imported_rigs = set()
    for old_name, obj in imported.items():
        assert obj is not None; scene.collection.objects.link(obj); obj.hide_render=True; obj.hide_set(True)
        if old_name in control['sourceObjects']['guides'].values():
            obj.name='Gloves__CuffFit06Guide.'+old_name[-1]
        elif old_name in control['sourceObjects']['fullFields'].values():
            side=old_name[-1]; obj.name='Gloves__CuffFit06FullFieldReference.'+side
            for arm in [m for m in obj.modifiers if m.type=='ARMATURE']:
                assert rest(arm.object) == rig_before; imported_rigs.add(arm.object); arm.object=rig
            world=obj.matrix_world.copy(); obj.parent=rig; obj.matrix_world=world
            obj.data.vertices.foreach_set('co',(full_positions[side]+deltas[side]).astype(np.float32).ravel()); obj.data.update()
            assert fixed(obj)==full_fixed[side]
        else: obj.name='Gloves__CuffFit06Bound'+('DenseSource.R' if old_name==source_name else 'Driver.R')
    for imported_rig in imported_rigs:
        assert imported_rig != rig; bpy.data.objects.remove(imported_rig,do_unlink=True)
    hood=bpy.data.objects['RiderHoodie']; hood.data.calc_loop_triangles()
    tree=BVHTree.FromPolygons([v.co.copy() for v in hood.data.vertices],[tuple(t.vertices) for t in hood.data.loop_triangles],all_triangles=True)
    for side, witness in [('L',199533),('R',199531)]:
        obj=bpy.data.objects['ActualSelectedGlove.'+side]
        before=helper['points'](obj.data); assert np.array_equal(before,full_positions[side])
        obj.data.vertices.foreach_set('co',(before+deltas[side]).astype(np.float32).ravel()); obj.data.update()
        assert fixed(obj)==render_fixed[side]
        obj.data.calc_loop_triangles()
        surface_faces = np.asarray([tuple(triangle.vertices) for triangle in obj.data.loop_triangles], dtype=np.int32)
        actual_after = helper['points'](obj.data)
        a, b = before[surface_faces].astype(float), actual_after[surface_faces].astype(float)
        na = np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]); nb = np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0])
        affected = np.any(np.any(a != b,axis=2),axis=1)
        assert np.all(np.einsum('ij,ij->i',na,nb)[affected] > 0), ('Actual paired delivery surface reverses a triangle; stop final mechanism',side)
        report['hands'][side]['actualPairedDeliveryTriangleOrientationPreserved'] = True
        def measure(index):
            point = obj.data.vertices[index].co
            nearest, normal, face, distance = tree.find_nearest(point)
            return {'nativeVertex':int(index),'point':list(point),'nearestHoodie':list(nearest),
                    'signedNormalDistanceM':float((point-nearest).dot(normal)),'distanceM':float(distance)}
        witnesses = [120752,120746,119253,143964,144364,144043,witness]
        measurements = [measure(index) for index in witnesses]
        report['hands'][side]['denseCuffWitnessAfter'] = measurements
        assert all(row['signedNormalDistanceM'] <= 0. for row in measurements), ('Final mechanism leaves a demonstrated fragment or old lip outside; stop',side,measurements)
        moved = np.flatnonzero(np.any(deltas[side] != 0, axis=1))
        sector = [measure(int(index)) for index in moved]
        signed = np.asarray([row['signedNormalDistanceM'] for row in sector])
        report['hands'][side]['fullAffectedDenseSector'] = {
            'vertices':len(sector),'maximumSignedHoodieDistanceM':float(signed.max()),
            'minimumSignedHoodieDistanceM':float(signed.min()),'outsideVertexCount':int(np.sum(signed>0)),
            'quantilesM':np.quantile(signed,[0,.25,.5,.75,1]).tolist(),
            'limits':'The feathered sector can include normally exposed glove surface; all measured fragment/old lip witnesses must be inside. Parent judges the complete live silhouette.'}
        (out/f'affected-sector-{side}.json').write_text(json.dumps(sector,indent=2)+'\n')
    assert rest(rig)==rig_before and protected_before=={o.name:geometry(o) for o in protected}
    assert {o.name for o in scene.objects if o.type=='MESH' and not o.hide_render}==EXPECTED
    native=out/'complete-selected-cuff-fit06.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    report.update(native={'path':str(native.relative_to(ROOT)),'sha256':sha(native)},visibleMeshes=sorted(EXPECTED),
        protectedPartFingerprints=protected_before,renderGloveTopologyUVPBRAndDeliveryFieldsUnchanged=render_fixed,
        exact75RestUnchanged=True,status='ACTUAL_SELECTED_CUFF_NATIVE_SAVED_PLAYED_REVIEW_PENDING')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'native':report['native'],'hands':{s:r['denseCuffWitnessAfter'] for s,r in report['hands'].items()}}),flush=True)


if __name__ == '__main__': main()
