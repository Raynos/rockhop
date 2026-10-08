"""One ordinary selected-surface anatomical sculpt; parent runs guarded CPU2 only.

Guide-only simplification conditions Blender's Laplacian solve. Dense selected
exterior, maps and corner UV survive. Continuous canonical-foot cavity follows
an actual saved sculpt. No exterior UNION, rectangular loft, fit sweep or fallback.
"""
from contextlib import contextmanager
import ctypes
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import sys
import traceback

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONFIG_PATH = HERE/'sculpt-inputs.json'
C = json.loads(CONFIG_PATH.read_text())
RUN = {'report': None, 'out': None, 'native': None}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024*1024):
            digest.update(block)
    return digest.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], ('Changed input', row['path'])
    return path


def module(row, name):
    spec = importlib.util.spec_from_file_location(name, pin(row))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def duplicate(source, name):
    result = source.copy()
    result.data = source.data.copy()
    result.name = name
    bpy.context.scene.collection.objects.link(result)
    for modifier in list(result.modifiers):
        result.modifiers.remove(modifier)
    result.hide_render = True
    result.hide_set(False)
    result['acceptedArt'] = False
    return result


def topology(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    pending_vertices = set(bm.verts)
    components = 0
    while pending_vertices:
        pending = [pending_vertices.pop()]
        components += 1
        while pending:
            vertex = pending.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in pending_vertices:
                    pending_vertices.remove(other)
                    pending.append(other)
    result = dict(vertices=len(bm.verts), faces=len(bm.faces), connectedComponents=components,
                  boundaryEdges=sum(e.is_boundary for e in bm.edges),
                  nonManifoldEdges=sum(not e.is_manifold for e in bm.edges),
                  zeroAreaFaces=sum(f.calc_area() < 1e-18 for f in bm.faces))
    bm.free()
    return result


def require_topology(receipt):
    assert receipt['connectedComponents'] == 1, 'Disconnected source-derived sculpture'
    assert not any(receipt[k] for k in ('boundaryEdges', 'nonManifoldEdges', 'zeroAreaFaces'))


def write_receipt():
    if RUN['report'] is not None:
        if RUN['native'].exists():
            RUN['report']['native'] = dict(path=str(RUN['native'].relative_to(ROOT)), sha256=sha(RUN['native']))
        (RUN['out']/'report.json').write_text(json.dumps(RUN['report'], indent=2)+'\n')



@contextmanager
def native_modifier_log(stage, receipt):
    """Capture real C stdout/stderr as well as Python reports for one operation."""
    log_path=RUN['out']/(stage+'.native-modifier.log')
    sys.stdout.flush()
    sys.stderr.flush()
    libc=ctypes.CDLL(None)
    libc.fflush(None)
    saved=[os.dup(1),os.dup(2)]
    descriptor=os.open(str(log_path),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    try:
        os.dup2(descriptor,1)
        os.dup2(descriptor,2)
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        libc.fflush(None)
        for destination,original in zip((1,2),saved):
            os.dup2(original,destination)
            os.close(original)
        os.close(descriptor)
        text=log_path.read_text(errors='replace')
        warning_pattern=r'(?i)\b(error|warning|failed|failure|singular|invalid)\b|did not find|could not|cannot'
        warnings=[line for line in text.splitlines() if re.search(warning_pattern,line)]
        receipt.setdefault('nativeModifierLogs',[]).append(dict(stage=stage,
            path=str(log_path.relative_to(ROOT)),sha256=sha(log_path),bytes=log_path.stat().st_size,
            warningOrErrorLines=warnings))
        # Replay the actual captured lines to the parent guard's worker log too.
        print('BOOT04_NATIVE_MODIFIER_LOG',stage,flush=True)
        if text:
            print(text,end='' if text.endswith('\n') else '\n',flush=True)
        write_receipt()


def reject_modifier_warnings(receipt):
    warnings=[dict(stage=row['stage'],line=line) for row in receipt.get('nativeModifierLogs',[])
              for line in row['warningOrErrorLines']]
    receipt['nativeModifierWarnings']=warnings
    write_receipt()
    assert not warnings, ('Actual native modifier warning/error',warnings)

def sculpture(source, side, frame, origin, receipt, old, checkpoint):
    dense = duplicate(source, 'Boot04SelectedSurfaceSculpt.'+side)
    guide = duplicate(source, 'Boot04SelectedSourceLaplacianGuide.'+side)
    guide['productionAuthoringTool'] = True
    guide['selectedSourceGeometryAncestry'] = source.name
    # Recover documented original selected source units, including handedness.
    # Object transform keeps the guide in the same world frame as the dense boot.
    source_spec=json.loads(pin(C['sourceUnitAffineControls']).read_text())['sides'][side]
    scales=np.array(source_spec['scales'])*np.array([1.,1.,source_spec['mirrorWidth']])
    affine=np.eye(4)
    affine[:3,:3]=frame*scales[None,:]
    affine[:3,3]=origin+frame@np.array(source_spec['offset'])
    inverse=np.linalg.inv(affine)
    source_world=old.mesh_points(guide.data)
    guide_coords=(source_world-affine[:3,3])@inverse[:3,:3].T
    for vertex,point in zip(guide.data.vertices,guide_coords):
        vertex.co=point
    guide.matrix_world=Matrix(affine.tolist())
    guide.data.update()
    def guide_world(mesh):
        return old.mesh_points(mesh)@affine[:3,:3].T+affine[:3,3]
    receipt['sourceUnitGuideAffine']=dict(sourceScale=source_spec['scales'],mirrorWidth=source_spec['mirrorWidth'],
        maximumRestRoundTripErrorM=float(np.abs(guide_world(guide.data)-source_world).max()))
    assert receipt['sourceUnitGuideAffine']['maximumRestRoundTripErrorM'] < 1e-6
    active(guide)
    dec = guide.modifiers.new('Guide only source-derived condition', 'DECIMATE')
    dec.decimate_type, dec.ratio, dec.use_collapse_triangulate = 'COLLAPSE', C['guideRatio'], True
    with native_modifier_log(side+'-guide-decimate',receipt):
        bpy.ops.object.modifier_apply(modifier=dec.name)
    reject_modifier_warnings(receipt)
    receipt['guideTopology'] = topology(guide.data)
    write_receipt()
    require_topology(receipt['guideTopology'])
    assert len(guide.data.vertices) <= C['maxGuideVertices']
    assert all(len(p.vertices) == 3 for p in guide.data.polygons)
    local = (guide_world(guide.data)-origin) @ frame
    semantic = local.copy()
    medial = 1 if side == 'R' else -1
    semantic[:, 2] *= medial
    hold = local[:, 1] <= C['protectedSoleThroughHeightM']
    total = np.zeros_like(local)
    count = np.zeros_like(local)
    receipt['handles'] = []
    for row in C['handles']:
        center, radius, delta = (np.array(row[k], dtype=float) for k in ('center', 'radius', 'delta'))
        selected = (np.sum(((semantic-center)/radius)**2, axis=1) <= 1.) & ~hold
        ids = np.where(selected)[0]
        if len(ids):
            handle_group=guide.vertex_groups.new(name='Anatomical handle '+row['name'])
            handle_group.add(ids.tolist(),1.,'REPLACE')
        receipt['handles'].append(dict(name=row['name'], guideVertices=len(ids),
                                       semanticCenterM=center.tolist(), semanticDeltaM=delta.tolist(), axes=row['axes']))
        write_receipt()
        assert len(ids) >= 3, ('Empty anatomical handle', side, row['name'])
        for axis in row['axes']:
            total[selected, axis] += delta[axis]*(medial if axis == 2 else 1)
            count[selected, axis] += 1
    anchor = hold | np.any(count > 0, axis=1)
    displacement = np.divide(total, count, out=np.zeros_like(total), where=count > 0)
    displacement[hold] = 0
    targets_world = guide_world(guide.data)+displacement @ frame.T
    targets = (targets_world-affine[:3,3])@inverse[:3,:3].T
    # Blender cotangent_tri_weight_v3 disables triangles at cross magnitude <=
    # FLT_EPSILON. Measure the actual source-unit guide before binding.
    coordinates=old.mesh_points(guide.data).astype(np.float32)
    triangles=np.array([p.vertices[:] for p in guide.data.polygons])
    corners=coordinates[triangles]
    cross=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0])
    active_triangles=np.linalg.norm(cross,axis=1)>np.finfo(np.float32).eps
    incident=np.bincount(triangles[active_triangles].reshape(-1),minlength=len(coordinates))
    receipt['cotangentConditioning']=dict(sourceUnitTriangles=len(triangles),
        inactiveTriangles=int(np.sum(~active_triangles)),unanchoredZeroActiveIncidentVertices=int(np.sum((incident==0)&~anchor)),
        FLTEpsilon=float(np.finfo(np.float32).eps))
    write_receipt()
    assert not np.any((incident==0)&~anchor), 'Guide contains singular unanchored cotangent columns'
    group = guide.vertex_groups.new(name='Complete anatomical sculpture anchors')
    group.add(np.where(anchor)[0].tolist(), 1., 'REPLACE')
    lap = guide.modifiers.new('Selected curvature anatomical sculpture', 'LAPLACIANDEFORM')
    lap.vertex_group, lap.iterations = group.name, C['laplacianIterations']
    active(guide)
    with native_modifier_log(side+'-laplacian-bind',receipt):
        lap_result=bpy.ops.object.laplaciandeform_bind(modifier=lap.name)
    assert lap_result == {'FINISHED'}
    assert lap.is_bind
    # Surface bind sees the unchanged actual source-derived guide, before anchors move.
    old_points = old.mesh_points(dense.data)
    dense_local = (old_points-origin) @ frame
    exact_sole = dense_local[:, 1] <= C['protectedSoleThroughHeightM']
    influence = np.clip((dense_local[:, 1]-C['protectedSoleThroughHeightM']) /
                        (C['sourceUpperBlendHeightM']-C['protectedSoleThroughHeightM']), 0., 1.)
    deform_group = dense.vertex_groups.new(name='Selected upper sculpt influence')
    for index in np.where(influence > 0)[0]:
        deform_group.add([int(index)], float(influence[index]), 'REPLACE')
    surface = dense.modifiers.new('Actual selected dense detail follows guide', 'SURFACE_DEFORM')
    surface.target, surface.vertex_group = guide, deform_group.name
    surface.use_sparse_bind = True
    active(dense)
    with native_modifier_log(side+'-surface-bind',receipt):
        surface_result=bpy.ops.object.surfacedeform_bind(modifier=surface.name)
    assert surface_result == {'FINISHED'}
    assert surface.is_bound
    guide_before = guide_world(guide.data)
    for index in np.where(anchor)[0]:
        guide.data.vertices[int(index)].co = targets[index]
    guide.data.update()
    with native_modifier_log(side+'-laplacian-evaluate',receipt):
        bpy.context.view_layer.update()
        depsgraph=bpy.context.evaluated_depsgraph_get()
        evaluated=guide.evaluated_get(depsgraph)
        solved=guide_world(evaluated.data)
    free=~anchor
    moved=np.linalg.norm(solved-guide_before,axis=1)
    anchor_errors=np.linalg.norm(solved[anchor]-targets_world[anchor],axis=1)
    # This threshold distinguishes a genuine free solve from float roundoff,
    # rather than declaring an anatomical fit or anchor-convergence tolerance.
    numeric_movement_floor=32.*np.finfo(np.float32).eps*float(np.ptp(guide_before,axis=0).max())
    moved_free=int(np.sum(moved[free]>numeric_movement_floor))
    receipt['laplacianSolveWitness']=dict(boundFlag=bool(lap.is_bind),anchors=int(anchor.sum()),
        freeVertices=int(free.sum()),freeVerticesMovedAboveRoundoff=moved_free,
        numericalMovementFloorM=numeric_movement_floor,maxDisplacementM=float(moved.max()),
        maxAnchorTargetErrorM=float(anchor_errors.max()),
        anchorTargetErrorQuantilesM=np.quantile(anchor_errors,[0.,.5,.95,1.]).tolist(),
        anchorResidualPolicy='Report-only least-squares residual; parent judges actual anatomical guide and dense sculpt. No microscopic fit guard.',
        allFinite=bool(np.all(np.isfinite(solved))))
    write_receipt()
    assert np.all(np.isfinite(solved)), 'Non-finite Laplacian result'
    assert moved_free > 0, 'Laplacian bound flag without free-surface movement above roundoff'
    # Freeze the actual evaluated result before solver-warning, residual,
    # solved-topology or dense-transfer gates. This survives every later failure.
    snapshot_mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=depsgraph)
    snapshot=bpy.data.objects.new('Boot04ActualSolvedGuideSnapshot.'+side,snapshot_mesh)
    bpy.context.scene.collection.objects.link(snapshot)
    snapshot.matrix_world=guide.matrix_world.copy()
    snapshot.hide_render=True
    snapshot.hide_set(True)
    snapshot['acceptedArt']=False
    snapshot['actualEvaluatedSelectedGuide']=True
    receipt['solvedGuideObject'],receipt['guideObject']=snapshot.name,guide.name
    checkpoint('UNACCEPTED_ACTUAL_FINITE_MOVING_GUIDE_SAVED_'+side)
    receipt['solvedGuideTopology']=topology(snapshot_mesh)
    write_receipt()
    reject_modifier_warnings(receipt)
    require_topology(receipt['solvedGuideTopology'])
    # Keep the bound guide and named anatomical handles editable in the native.
    # Surface Deform captures its evaluated sculpt into the dense derivative.
    active(dense)
    with native_modifier_log(side+'-surface-apply',receipt):
        bpy.ops.object.modifier_apply(modifier=surface.name)
    actual = old.mesh_points(dense.data)
    receipt['denseSculpt'] = dict(vertices=len(dense.data.vertices), faces=len(dense.data.polygons),
        exactSoleVertices=int(exact_sole.sum()), maxProtectedSoleDisplacementM=float(np.linalg.norm(actual[exact_sole]-old_points[exact_sole],axis=1).max()),
        maxSelectedDisplacementM=float(np.linalg.norm(actual-old_points,axis=1).max()), UVExact=False)
    receipt['sculptObject']=dense.name
    dense.hide_render=False
    source.hide_render=True
    source.hide_set(True)
    checkpoint('UNACCEPTED_ACTUAL_DENSE_TRANSFER_SAVED_'+side)
    reject_modifier_warnings(receipt)
    # Excluded sole must be byte-exact, including real tread; no assertion weakening.
    assert np.array_equal(actual[exact_sole], old_points[exact_sole]), 'Excluded original sole geometry changed'
    assert np.array_equal(np.array([p.vertices[:] for p in dense.data.polygons]),
                          np.array([p.vertices[:] for p in source.data.polygons]))
    assert [tuple(d.uv) for d in dense.data.uv_layers.active.data] == [tuple(d.uv) for d in source.data.uv_layers.active.data]
    receipt['denseSculpt']['UVExact'] = True
    dense.data.attributes.new('Boot04SourceFaceRowPlusOne', 'INT', 'FACE').data.foreach_set(
        'value', np.arange(1,len(dense.data.polygons)+1,dtype=np.int32))
    for polygon in dense.data.polygons:
        polygon.use_smooth = True
    guide.hide_render = True
    guide.hide_set(True)
    source.hide_render = True
    source.hide_set(True)
    dense.hide_render = False
    dense['selectedOriginalSHA256'] = C['selectedOriginal']['sha256']
    dense['method'] = C['method']
    receipt['sculptObject'], receipt['guideObject'] = dense.name, guide.name
    checkpoint('UNACCEPTED_ACTUAL_SELECTED_SCULPT_SAVED_'+side)
    return dense


def map_lining(target, sculpt, original, frame, origin, receipt, old):
    """All exterior remains actual selected charts; new cavity borrows inner-quarter chart."""
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import barycentric_transform
    mesh, donor = target.data, sculpt.data
    donor_points = old.mesh_points(donor)
    local = (donor_points-origin) @ frame
    centers = (np.array([tuple(p.center) for p in donor.polygons])-origin) @ frame
    normals = np.array([tuple(p.normal) for p in donor.polygons]) @ frame
    medial = 1 if frame[0,0] > 0 else -1
    radial = centers[:,[0,2]]-np.array([-.015,-.010*medial])
    inner_ids = np.where((centers[:,0]>-.080)&(centers[:,0]<.055)&
                         (centers[:,1]>.035)&(centers[:,1]<.105)&
                         (np.sum(normals[:,[0,2]]*radial,axis=1)<-.004))[0]
    receipt.update(selectedInnerQuarterDonorTriangles=len(inner_ids),
        unchangedSelectedSculptTrianglesExactUV=0, splitSelectedSculptTriangles=0,
        authoredCavityFaces=0, authoredExteriorFaces=0, mappedInnerCorners=0,
        maxInnerDonorDistanceM=0., mappingComplete=False,
        UVPolicy='Surviving sculpt corners keep exact original selected UV. Boolean split faces interpolate the same original chart. Genuinely authored cavity borrows actual same-side sculpted original inner-quarter PBR; every new corner records original selected source triangle and distance. No exterior paint synthesis or bake.')
    write_receipt()
    assert len(inner_ids), 'Selected original inner-quarter chart unavailable'
    inner_tree = BVHTree.FromPolygons([v.co for v in donor.vertices], [donor.polygons[int(i)].vertices for i in inner_ids])
    uv, old_uv = mesh.uv_layers.active, donor.uv_layers.active
    source_ids = mesh.attributes['Boot04SourceFaceRowPlusOne']
    corner_ids = mesh.attributes.new('Boot04CornerSourceTriangle','INT','CORNER')
    distance_attr = mesh.attributes.new('Boot04CornerSourceDistanceM','FLOAT','CORNER')
    kinds = mesh.attributes.new('Boot04SurfaceKind','INT','FACE')
    unchanged = set()
    for polygon in mesh.polygons:
        receipt['lastMappedPolygon'] = polygon.index
        kind = polygon.material_index
        assert kind in (0,2), ('Manufactured exterior forbidden',kind)
        kinds.data[polygon.index].value=kind
        if kind == 0:
            ancestor = int(source_ids.data[polygon.index].value)-1
            assert 0 <= ancestor < len(donor.polygons), 'Lost selected triangle ancestry'
            old_face=donor.polygons[ancestor]
            lookup={tuple(donor.vertices[v].co):tuple(old_uv.data[l].uv)
                    for v,l in zip(old_face.vertices,old_face.loop_indices)}
            points=[tuple(mesh.vertices[v].co) for v in polygon.vertices]
            exact=len(points)==3 and set(points)==set(lookup)
            for point,loop in zip(points,polygon.loop_indices):
                corner_ids.data[loop].value=ancestor
                if exact:
                    assert tuple(uv.data[loop].uv)==lookup[point], 'Surviving selected UV changed'
            if exact:
                unchanged.add(ancestor)
                receipt['unchangedSelectedSculptTrianglesExactUV']+=1
            else:
                receipt['splitSelectedSculptTriangles']+=1
        else:
            receipt['authoredCavityFaces']+=1
            for loop in polygon.loop_indices:
                point=mesh.vertices[mesh.loops[loop].vertex_index].co
                location,normal,inner_index,distance=inner_tree.find_nearest(point)
                assert location is not None
                ancestor=int(inner_ids[inner_index])
                old_face=donor.polygons[ancestor]
                tri=[donor.vertices[v].co for v in old_face.vertices]
                texture=[Vector((*old_uv.data[l].uv,0.)) for l in old_face.loop_indices]
                uv.data[loop].uv=barycentric_transform(location,*tri,*texture)[:2]
                corner_ids.data[loop].value=ancestor
                distance_attr.data[loop].value=distance
                receipt['mappedInnerCorners']+=1
                receipt['maxInnerDonorDistanceM']=max(receipt['maxInnerDonorDistanceM'],float(distance))
        polygon.use_smooth=True
    # Directly verify real original protected triangles, not only inherited IDs.
    source_local=(old.mesh_points(original.data)-origin) @ frame
    source_faces=np.array([p.vertices[:] for p in original.data.polygons])
    protected=np.where(np.max(source_local[source_faces][:,:,1],axis=1)<-.012)[0]
    missed=set(map(int,protected))-unchanged
    moved=[]
    for row in protected:
        face=sculpt.data.polygons[int(row)]
        original_face=original.data.polygons[int(row)]
        if [tuple(sculpt.data.vertices[v].co) for v in face.vertices] != [tuple(original.data.vertices[v].co) for v in original_face.vertices]:
            moved.append(int(row))
    receipt.update(mappingComplete=True, protectedOriginalLowerTreadTriangles=len(protected),
        protectedTreadNotUnchangedFaceRows=sorted(missed), protectedTreadSculptMovedFaceRows=moved)
    write_receipt()
    assert not missed and not moved, 'Original protected tread triangle geometry/identity changed'
    assert receipt['authoredCavityFaces'] > 0, 'Continuous cavity produced no new topology'


def reviews(report, body, rig, sections):
    for side, row in report['sides'].items():
        frame,origin=np.array(sections[side]['footFrame']),np.array(sections[side]['footOrigin'])
        focus=origin+frame@np.array([-.095,.058,0.])
        medial=1 if side=='R' else -1
        views={name:(focus+frame@np.array(offset)).tolist() for name,offset in [
            ('anatomical-lateral',[0,.12,-.65*medial]),('anatomical-medial',[0,.12,.65*medial]),
            ('toe-threequarter',[-.50,.30,.36*medial]),('heel-threequarter',[.50,.25,.32*medial]),('top',[-.03,.70,0])]}
        for role,key in [('selected-source','source'),('solved-guide','solvedGuideObject'),('selected-sculpt','sculptObject'),('cavity-result','target')]:
            if key not in row:
                continue
            spec=dict(accepted=False,native=report['native'],mode='stills',objects=[row[key]],bodyObject=body.name,
                rigObject=rig.name,focus=focus.tolist(),orthoScale=.38,views=views,
                limits=['Actual original selected PBR; rest diagnostics reject only.','Parent must play full outfit ankle/toe and bike motion; no accepted art claim.'])
            (RUN['out']/(side+'-'+role+'-review.json')).write_text(json.dumps(spec,indent=2)+'\n')


def main():
    args=sys.argv[sys.argv.index('--')+1:]
    assert len(args)==1
    out=Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/C['outputRoot']) and not out.exists()
    pins=[C[key] for key in ('workingOutfit','canonicalArrays','selectedOriginal','extraction',
                            'readOnlyHelpers','readOnlyInputs','reviewRenderer','legacyHelpers','sourceUnitAffineControls')]
    pins+=list(C['sections'].values())+list(C['selectedMaps'].values())
    for row in pins:
        pin(row)
    old=module(C['legacyHelpers'],'boot04_frozen_cavity_helpers')
    old.C=C
    h=module(C['readOnlyHelpers'],'boot04_read_only')
    extracted=json.loads(pin(C['extraction']).read_text())
    sections={side:json.loads(pin(row).read_text()) for side,row in C['sections'].items()}
    native=dict(np.load(pin(C['canonicalArrays'])))
    bpy.ops.wm.open_mainfile(filepath=str(pin(C['workingOutfit'])))
    body,rig=(bpy.data.objects[C['objects'][k]] for k in ('body','rig'))
    assert len(rig.data.bones)==75 and rig.animation_data is None
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    before_body=old.body_signature(body,rig)
    out.mkdir(parents=True)
    report=dict(accepted=False,status='SELECTED_SURFACE_SCULPT_IN_PROGRESS',inputs=C,
                recipeSHA256=sha(__file__),controlsSHA256=sha(CONFIG_PATH),sides={})
    RUN.update(report=report,out=out,native=out/'anatomical-selected-boots.blend',body=body,rig=rig,old=old,
               beforeBody=before_body,sections=sections)

    def checkpoint(stage):
        report['status']=stage
        assert old.body_signature(body,rig)==before_body
        bpy.ops.wm.save_as_mainfile(filepath=str(RUN['native']),compress=True)
        write_receipt()
        reviews(report,body,rig,sections)

    for side,source_name in C['objects']['boots'].items():
        source=bpy.data.objects[source_name]
        assert json.loads(json.dumps(h.state(source)))==extracted['sides'][side]['sourceState']
        frame,origin=np.array(sections[side]['footFrame']),np.array(sections[side]['footOrigin'])
        receipt=dict(source=source.name,side=side,medialLocalTSign=1 if side=='R' else -1,
                     parentArtAcceptance=False,cavityEaseM=C['innerEaseM'])
        report['sides'][side]=receipt
        sculpt=sculpture(source,side,frame,origin,receipt,old,checkpoint)
        target=duplicate(sculpt,'Boot04SelectedAnatomical.'+side)
        receipt['target']=target.name
        assert len(target.data.materials)==1
        material=target.data.materials[0]
        lining=material.copy()
        lining.name='Boot04SelectedActualInnerQuarterLining.'+side
        target.data.materials.append(material)
        target.data.materials.append(lining)
        cavity,mask=old.cavity_last(side,frame,origin,tuple(target.data.materials),native)
        for face in cavity.data.polygons:
            face.use_smooth=True
        receipt['cavityBoolean']=old.apply_boolean(target,cavity,'DIFFERENCE')
        old.bind(target,frame,origin,side,rig)
        target.hide_render=False
        sculpt.hide_render=True
        sculpt.hide_set(True)
        cavity.hide_render=True
        cavity.hide_set(True)
        checkpoint('UNACCEPTED_ACTUAL_SELECTED_SCULPT_CAVITY_SAVED_'+side)
        receipt['topology']=topology(target.data)
        write_receipt()
        require_topology(receipt['topology'])
        points=native['vertices'][mask]
        foot_faces=native['faces'][np.all(mask[native['faces']],axis=1)]
        samples=np.vstack((points,native['vertices'][foot_faces].mean(1)))
        tree=old.bvh(target.data)
        witness=dict(verticesAndTriangleCentroids=len(samples),insideLeatherSampleRows=[],minimumDistanceM=None,
                     interpretation='Empty eased cavity witness only; actual original-PBR views and played motion determine enclosure/appearance.')
        receipt['actualFootSurfaceWitness']=witness
        for index,point in enumerate(samples):
            if old.inside(tree,point):
                witness['insideLeatherSampleRows'].append(index)
            _,_,_,distance=tree.find_nearest(Vector(point))
            witness['minimumDistanceM']=float(distance) if witness['minimumDistanceM'] is None else min(witness['minimumDistanceM'],float(distance))
            witness['lastSampleRow']=index
        write_receipt()
        receipt['materialAncestry']={}
        map_lining(target,sculpt,source,frame,origin,receipt['materialAncestry'],old)
        target['selectedOriginalSHA256']=C['selectedOriginal']['sha256']
        target['method']=C['method']
        target['authoredInnerLiningPBRRequiresParentReview']=True
        checkpoint('UNACCEPTED_ACTUAL_SELECTED_SCULPT_PBR_SAVED_'+side)
        assert not witness['insideLeatherSampleRows']
        assert witness['minimumDistanceM'] >= C['minimumMeasuredClearanceM']
    for row in pins:
        pin(row)
    checkpoint('UNACCEPTED_BILATERAL_SELECTED_SCULPT_REST_AND_PLAYED_REVIEW_PENDING')
    print(json.dumps(dict(status=report['status'],native=report['native'],noBakeOrRender=True)),flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        if RUN['report'] is not None:
            RUN['report']['failedStage']=RUN['report']['status']
            RUN['report']['status']='FAILED_UNACCEPTED_ACTUAL_SCULPT_RECEIPTS_PERSISTED'
            RUN['report']['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
            # Preserve last successful native checkpoint; separately capture current
            # actual in-memory geometry/UV, including partially completed mapping.
            try:
                assert RUN['old'].body_signature(RUN['body'],RUN['rig'])==RUN['beforeBody']
                failure_native=RUN['out']/'failed-in-memory.blend'
                bpy.ops.wm.save_as_mainfile(filepath=str(failure_native),compress=True)
                RUN['report']['failedInMemoryNative']=dict(path=str(failure_native.relative_to(ROOT)),sha256=sha(failure_native))
            except Exception as save_error:
                RUN['report']['failedInMemorySaveError']=str(save_error)
            write_receipt()
            (RUN['out']/'failure.json').write_text(json.dumps(RUN['report'],indent=2)+'\n')
            if 'native' in RUN['report']:
                reviews(RUN['report'],RUN['body'],RUN['rig'],RUN['sections'])
        raise
