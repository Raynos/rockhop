"""Apply one frozen local anatomical guide sculpt through actual saved binding.

Parent CPU2 only. Original dense selected topology/UV/PBR and all originals
remain; six compact selected-guide Inflate edits are the sole shape change.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
ACTUAL=ROOT/'harness/out/rider-rebuild/glove-anatomical04/guide02'
NATIVE_SHA='ce50929296c718dad592b6e320587b1de852187583003b4f74004f46222cc329'
CONTROLS_SHA='554c62be5670fabac22f8d98b48a6cd8db79d1dd39ec525b390d86a26073c9b9'
HELPER_SHA='4a1bd17b7dd3c766749419bf8d5d4e0d0f4b478bcd2b6ffa00eb6fed9bc13851'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def polygons(mesh):
    value=np.empty((len(mesh.polygons),3),dtype=np.int32)
    assert all(len(p.vertices)==3 for p in mesh.polygons)
    mesh.polygons.foreach_get('vertices',value.ravel())
    return value


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==1
    out=Path(args[0]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/glove-anatomical04')
    source_native=ACTUAL/'guide-sculpt-L.blend';assert sha(source_native)==NATIVE_SHA
    controls_path=HERE/'local-controls04.json';assert sha(controls_path)==CONTROLS_SHA
    assert sha(HERE/'author_guide02.py')==HELPER_SHA
    edits=json.loads(controls_path.read_text());assert edits['acceptedArt'] is False
    guide_helpers=runpy.run_path(str(HERE/'author_guide02.py'))
    frozen=json.loads((HERE/'guide-controls02.json').read_text())
    assert sha(ROOT/frozen['previousAuthorHelpers']['path'])==frozen['previousAuthorHelpers']['sha256']
    core=runpy.run_path(str(ROOT/frozen['previousAuthorHelpers']['path']))
    control=json.loads((HERE/'controls-orientation02.json').read_text())
    assert sha(HERE/'controls-orientation02.json')==frozen['sourceControls']['sha256']
    for pin in control['pins'].values():assert sha(ROOT/pin['path'])==pin['sha256']
    for row in edits['hands'].values():
        for key in ('actualGuide','offsets'):
            assert sha(ROOT/row[key]['path'])==row[key]['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source_native))
    body,rig=bpy.data.objects['RiderBody'],bpy.data.objects['RiderSkeleton']
    before=core['signature'](body,rig);assert len(rig.data.bones)==75
    dense=np.load(ROOT/control['pins']['denseSelected']['path'])
    selected_guide=np.load(ROOT/frozen['selectedGuide']['path'])
    source_r=bpy.data.objects['Gloves__UntouchedSelectedDenseTransfer.R']
    driver_r=bpy.data.objects['Gloves__SelectedGuideTransferDriver.R']
    bound=source_r.modifiers['ActualSelectedDenseSurfaceDeform']
    assert bound.is_bound and bound.target==driver_r
    assert source_r.matrix_world==driver_r.matrix_world
    actual_r=np.load(ROOT/edits['hands']['R']['actualGuide']['path'])
    assert np.array_equal(np.asarray(source_r.matrix_world),actual_r['objectMatrix'])
    assert np.array_equal(guide_helpers['points'](source_r.data),dense['vertices'].astype(np.float32))
    assert np.array_equal(polygons(source_r.data),dense['faces'][:,::-1])
    assert np.array_equal(polygons(driver_r.data),selected_guide['faces'][:,::-1])
    expected_uv=dense['originalCornerUV'][:,::-1].copy();expected_uv[:,:,1]=1-expected_uv[:,:,1]
    assert core['uv_bytes'](source_r.data)==expected_uv.astype(np.float32).reshape(-1,2).tobytes()
    out.mkdir(parents=True)
    report={'acceptedArt':False,'operation':'SIX_LOCAL_SELECTED_GUIDE_INFLATE_EDITS_WITH_EXISTING_REST_BINDING',
            'controlsSHA256':frozen['sourceControls']['sha256'],'localControlsSHA256':sha(controls_path),
            'recipeSHA256':sha(__file__),'bodyAndMasterBefore':before,'hands':{},
            'newBindCalls':0,'solverParametersChanged':0,'bakesExecuted':0,'newPlayerAssets':0,
            'exactSuccessfulRestSourceTopologyAndFrameVerified':True,
            'limits':['Local authored geometry is unaccepted until parent actual PBR and clothed grip judgment.']}
    local_guides={}
    for side in ('R','L'):
        arrays=np.load(ROOT/edits['hands'][side]['offsets']['path'])
        actual=np.load(ROOT/edits['hands'][side]['actualGuide']['path'])
        assert np.array_equal(arrays['original'],actual['vertices'])
        assert np.array_equal(arrays['faces'],actual['faces'])
        assert np.isfinite(arrays['corrected']).all()
        guide_helpers['positive_cotangent_geometry'](arrays['corrected'],arrays['faces'])
        uv=selected_guide['uv'][arrays['faces']].copy();uv[:,:,1]=1-uv[:,:,1]
        guide=guide_helpers['mesh_object']('Gloves__LocalAnatomicalGuide04.'+side,
            arrays['corrected'],arrays['faces'],uv,source_r.data.materials,Matrix(actual['objectMatrix'].tolist()))
        guide['role']='EDITABLE_SELECTED_MODELING_GUIDE_ONLY_NOT_FINAL_APPEARANCE'
        guide['acceptedArt']=False;guide.hide_render=True;local_guides[side]=guide
    # Save both actual local selected guides before any dense evaluation/rigging.
    for side in ('R','L'):
        old_guide=bpy.data.objects['Gloves__SelectedGuideSculpt.'+side]
        old_guide.hide_render=True;old_guide.hide_set(True)
    guide_native=out/'paired-local-selected-guides.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(guide_native),compress=True)
    report['guidesSavedBeforeDenseTransferOrRig']={'path':str(guide_native.relative_to(ROOT)),
                                                'sha256':sha(guide_native)}
    (out/'guide-checkpoint.json').write_text(json.dumps(report,indent=2)+'\n')
    native_arrays=np.load(ROOT/control['pins']['nativeArrays']['path'])
    for side in ('R','L'):
        driver=driver_r.copy();driver.data=driver_r.data.copy()
        driver.name='Gloves__Local04BoundDriver.'+side;bpy.context.collection.objects.link(driver)
        source=source_r.copy();source.data=source_r.data.copy()
        source.name='Gloves__Local04BoundDense.'+side;bpy.context.collection.objects.link(source)
        transfer=source.modifiers['ActualSelectedDenseSurfaceDeform'];assert transfer.is_bound
        transfer.target=driver
        assert transfer.is_bound, "Copied binding lost when assigning identical-frame driver"
        assert source.matrix_world==source_r.matrix_world==driver.matrix_world
        assert np.array_equal(polygons(driver.data),selected_guide['faces'][:,::-1])
        # Copied successful binding sees its exact original selected indexing and
        # frame. Left final winding is restored only after modeling evaluation.
        solved=guide_helpers['points'](local_guides[side].data)
        driver.data.vertices.foreach_set('co',solved.astype(np.float32).ravel());driver.data.update()
        driver.hide_set(False);guide_helpers['active'](source)
        log=out/('dense-local-'+side+'.log')
        with guide_helpers['modifier_log'](log):
            evaluated=guide_helpers['evaluated_mesh'](source)
            diagnostics=guide_helpers['check_error'](transfer)
        points=guide_helpers['points'](evaluated)
        assert np.isfinite(points).all() and len(points)==len(dense['vertices'])
        dense_displacement=np.linalg.norm(points-dense['vertices'],axis=1)
        assert np.any(dense_displacement>np.finfo(np.float32).eps), 'Copied dense binding did not execute'
        assert np.array_equal(polygons(evaluated),dense['faces'][:,::-1])
        assert core['uv_bytes'](evaluated)==core['uv_bytes'](source_r.data)
        placement=control['hands'][side]['initialPlacement']
        world=np.einsum('ij,kj->ik',points,np.asarray(placement['linear']))+placement['translation']
        faces=dense['faces'].copy();uv=dense['originalCornerUV'].copy()
        if placement['reflectionFromSelectedSource']:faces=faces[:,::-1];uv=uv[:,::-1]
        uv[:,:,1]=1-uv[:,:,1]
        result=guide_helpers['mesh_object']('Gloves__LocallySculptedSelected04.'+side,world,faces,uv,
                                           source_r.data.materials,Matrix.Identity(4))
        result['acceptedArt']=False;result['originalSelectedUVAndMaterialAncestry']=True
        binding=core['bind_native'](result,dense['vertices'],native_arrays,
            np.load(ROOT/control['pins']['hand'+side]['path']),control,side,rig)
        for name in ('Gloves__SelectedFittedSource.'+side,'Gloves__AnatomicallySculptedSelected.'+side):
            old=bpy.data.objects.get(name)
            if old:old.hide_render=True;old.hide_set(True)
        for aid in (driver,source,local_guides[side]):aid.hide_render=True;aid.hide_set(True)
        assert core['signature'](body,rig)==before
        report['hands'][side]={'object':result.name,'localEdit':edits['hands'][side],
            'vertexCount':len(world),'triangleCount':len(faces),'binding':binding,
            'denseTransferModifierDiagnostics':diagnostics,'modifierLogSHA256':sha(log),
            'denseSourceDisplacementRMS':float(np.sqrt(np.mean(dense_displacement**2))),
            'denseMovedVertexCount':int(np.count_nonzero(dense_displacement>np.finfo(np.float32).eps)),
            'originalSelectedUVAndFaceAncestry':True,
            'reflectionFromSelectedSource':placement['reflectionFromSelectedSource'],
            'bounds':[world.min(0).tolist(),world.max(0).tolist()]}
        native=out/'editable-selected-bilateral-gloves.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
        report['native']={'path':str(native.relative_to(ROOT)),'sha256':sha(native)}
        (out/('checkpoint-'+side+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    report['bodyAndMasterAfter']=core['signature'](body,rig)
    expected=sorted(['RiderBody','Boots__LocallyRepairedSelectedDenseBoot.L',
        'Boots__LocallyRepairedSelectedDenseBoot.R','Gloves__LocallySculptedSelected04.L',
        'Gloves__LocallySculptedSelected04.R','Hoodie__ActualOriginalDensePBR_FrozenFitContext',
        'Jeans__AlignedSelectedDenseJeans'])
    visible=sorted(obj.name for obj in bpy.context.scene.objects
                   if obj.type=='MESH' and not obj.hide_render and obj.visible_get())
    assert visible==expected,('Unexpected visible final meshes',visible,expected)
    report['visibleMeshNames']=visible
    report['exactSevenSelectedOutfitMeshesVisible']=True
    report['status']='BILATERAL_SELECTED_SCULPT_SAVED_BEFORE_PARENT_PBR_REVIEW'
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
