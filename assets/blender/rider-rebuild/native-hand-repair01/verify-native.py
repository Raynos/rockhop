"""Independent saved-native/export, real-skin signs and moving field receipts.

Requires a fresh Blender process under the parent's guard. No art acceptance.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'docs/evidence/rider-rebuild/glove-charts01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==1
    out=Path(args[0]).resolve()
    report=json.loads((out/'report.json').read_text())
    assert sha(report['native']['path'])==report['native']['sha256']
    assert sha(report['glb']['path'])==report['glb']['sha256']
    for record in report['sourcePins']:assert sha(ROOT/record['path'])==record['sha256']
    bpy.ops.wm.open_mainfile(filepath=report['native']['path'])
    body,rig=bpy.data.objects['RiderBody'],bpy.data.objects['RiderSkeleton']
    assert {o.name for o in bpy.data.objects}=={'RiderBody','RiderSkeleton'}
    assert len(rig.data.bones)==75 and len(body.data.vertices)==10582
    assert all(not pb.constraints for pb in rig.pose.bones) and rig.animation_data is None
    assert len(body.modifiers)==len(report['bodyModifierOperators'])
    for record in report['bodyModifierOperators']:
        modifier=body.modifiers[record['index']]
        assert modifier.name==record['name'] and modifier.type==record['type']
        assert all(getattr(modifier,key)==value for key,value in record['options'].items())
    assert sha(out/'native-body.npz')==report['nativeTriangulationLineage']['arrays']['sha256']
    arrays=dict(np.load(out/'native-body.npz'));names=arrays['jointNames'].tolist();lookup={n:i for i,n in enumerate(names)}
    builder=load_module('native_builder',Path(__file__).with_name('build-native.py'))
    assert builder.geometry(body)==report['geometryAndSourceIDSHA256']
    assert np.array_equal(np.array([list(v.co) for v in body.data.vertices],dtype=np.float32),arrays['vertices'])
    native=builder.coefficients(body,names)
    assert np.array_equal(native,arrays['nativeCoefficients'])
    alpha=arrays['newFieldBlendAlpha'];changed=alpha>0
    assert np.array_equal(native[~changed],arrays['originalNativeCoefficients'][~changed])
    full=json.loads((out/'weights-full.json').read_text());four=json.loads((out/'weights-four.json').read_text())
    original_full=json.loads((ROOT/'harness/out/rider-rebuild/construction01/rig04/weights-full.json').read_text())
    original_four=json.loads((ROOT/'harness/out/rider-rebuild/construction01/rig04/weights-four.json').read_text())
    for i in np.flatnonzero(~changed):assert full[i]==original_full[i] and four[i]==original_four[i]
    native_rest=builder.rest(rig);rest={row['name']:row for row in native_rest}
    for i,name in enumerate(names):
        row=rest[name]
        assert np.array_equal(row['head'],arrays['jointHeads'][i])
        assert np.array_equal(row['tail'],arrays['jointTails'][i])
        assert np.array_equal(row['matrix'],arrays['jointMatrices'][i])
    geom=load_module('geometry_checks',ROOT/'assets/blender/rider-rebuild/glove-charts01/geometry-checks.py')
    certificates=[]
    for side in ('L','R'):
        hand=dict(np.load(BASE/('target01/native-hand-'+side+'.npz')))
        hv,hf=geom.close_planar_cuff(hand['vertices'],hand['faces'])
        for stem in ('thumb','f_index','f_middle','f_ring','f_pinky'):
            for segment in (1,2,3):
                name='DEF-'+stem+'.%02d.'%segment+side
                a,b=np.array(rest[name]['head']),np.array(rest[name]['tail'])
                p=a+np.linspace(0,1,65)[:,None]*(b-a)
                query=geom.signed_distances(p,hv,hf)
                assert not query['ambiguous'].any() and np.max(query['signedDistance'])<0
                bound=float(-query['signedDistance'].max()-np.linalg.norm(b-a)/128)
                assert bound>0,(name,bound)
                certificates.append({'joint':name,'continuousClearanceLowerBoundM':bound})
    prepare=load_module('target_reader',ROOT/'assets/blender/rider-rebuild/glove-charts01/prepare-target.py')
    document,accessor=prepare.glb(out/'native-body.glb')
    node=next(n for n in document['nodes'] if n.get('name')=='RiderBody')
    exported_names=[document['nodes'][i]['name'] for i in document['skins'][node['skin']]['joints']]
    assert set(exported_names)==set(names) and len(exported_names)==75
    primitive=document['meshes'][node['mesh']]['primitives'];assert len(primitive)==1
    primitive=primitive[0]
    ids=accessor(primitive['attributes']['_SOURCE_VERTEX_ID']).ravel().astype(int)
    assert np.array_equal(np.unique(ids),np.arange(10582))
    position=accessor(primitive['attributes']['POSITION']).astype(float)[:,[0,2,1]]*np.array([1,-1,1])
    export_pos_error=float(np.max(abs(position-arrays['vertices'][ids])))
    assert export_pos_error<2e-7,export_pos_error
    export_indices=accessor(primitive['indices']).ravel().astype(int).reshape(-1,3)
    export_triangles=ids[export_indices]
    assert len(export_triangles)==len(arrays['faces'])
    def canonical(triangle):
        offset=int(np.argmin(triangle));return tuple(np.roll(triangle,-offset)),offset
    native_triangle_lookup={canonical(triangle)[0]:(row,canonical(triangle)[1]) for row,triangle in enumerate(arrays['faces'])}
    assert len(native_triangle_lookup)==len(arrays['faces'])
    source_uv=accessor(primitive['attributes']['TEXCOORD_0']).astype(float)
    source_uv[:,1]=1-source_uv[:,1]
    seen=set();uv_error=0.
    for triangle,indices in zip(export_triangles,export_indices):
        key,offset=canonical(triangle);assert key in native_triangle_lookup and key not in seen
        seen.add(key);row,native_offset=native_triangle_lookup[key]
        polygon=body.data.polygons[int(arrays['sourcePolygonRows'][row])]
        loops=arrays['sourceLoopRows'][row]
        assert all(int(loop) in polygon.loop_indices for loop in loops)
        assert np.array_equal([body.data.loops[int(loop)].vertex_index for loop in loops],arrays['faces'][row])
        expected_uv=np.roll(arrays['triangleCornerUV'][row],-native_offset,axis=0)
        actual_uv=np.roll(source_uv[indices],-offset,axis=0)
        uv_error=max(uv_error,float(np.max(abs(expected_uv-actual_uv))))
    assert len(seen)==len(native_triangle_lookup) and uv_error<2e-7,uv_error
    joints=accessor(primitive['attributes']['JOINTS_0']).astype(int)
    weights=accessor(primitive['attributes']['WEIGHTS_0']).astype(float)
    export_field=np.zeros((len(ids),75))
    for slot in range(4):
        mapped=np.array([lookup[exported_names[j]] for j in joints[:,slot]])
        export_field[np.arange(len(ids)),mapped]+=weights[:,slot]
    # Native float32 fields are normalized by glTF export; measure the exact
    # documented normalization rather than claiming unnormalized byte parity.
    source_export=native[ids].astype(float)
    cutoff=.0001
    removed_cutoff_mass=np.where(source_export<=cutoff,source_export,0).sum(1)
    expected=np.where(source_export>cutoff,source_export,0)
    assert np.all(expected.sum(1)>0)
    expected/=expected.sum(1)[:,None]
    maximum_named_delta=float(np.max(abs(export_field-source_export)))
    export_field_error=float(np.max(abs(export_field-expected)))
    assert export_field_error<2e-7,export_field_error
    inverse_bind=accessor(document['skins'][node['skin']]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    convert=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],dtype=float)
    inverse_error=0.
    for i,name in enumerate(exported_names):
        # Blender's bone-local axes remain in the authored native basis; only
        # the world/input point basis is converted to glTF Y-up. Conjugating
        # both sides would introduce a spurious bone-local 90-degree rotation.
        expected_inverse=np.linalg.inv(np.array(rest[name]['matrix']))@convert.T
        inverse_error=max(inverse_error,float(np.max(abs(inverse_bind[i]-expected_inverse))))
    assert inverse_error<2e-6,inverse_error
    controls=json.loads((out/'digit-controls.json').read_text())
    assert controls['rigNativeSHA256']==report['native']['sha256']
    points=arrays['vertices'].astype(float)
    homogeneous=np.column_stack((points,np.ones(len(points))))
    full_matrix=np.zeros_like(native,dtype=float)
    for i,row in enumerate(full):
        for name,weight in row:full_matrix[i,lookup[name]]=weight
    # FULL outside domain is immutable and historically unnormalized. Normalize
    # the diagnostic evaluator only; neither stored row nor native FOUR changes.
    full_matrix/=full_matrix.sum(1)[:,None]
    four_matrix=native.astype(float);four_matrix/=four_matrix.sum(1)[:,None]
    inverse=np.linalg.inv(arrays['jointMatrices'])

    def reset():
        for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)

    def pose(rotations):
        reset()
        for name,axis,angle in rotations:
            pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(Vector(axis),angle)
        bpy.context.view_layer.update()
        transforms=np.array([[list(r) for r in rig.pose.bones[name].matrix] for name in names])@inverse
        deformed=np.einsum('kij,nj->nki',transforms,homogeneous)[:,:,:3]
        four_points=np.einsum('nk,nkj->nj',four_matrix,deformed)
        full_points=np.einsum('nk,nkj->nj',full_matrix,deformed)
        evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        actual=np.array([list(v.co) for v in evaluated.data.vertices])
        parity=float(np.max(np.linalg.norm(actual-four_points,axis=1)))
        assert parity<3e-6,parity
        return four_points,full_points,parity

    edges=np.unique(np.sort(np.concatenate([arrays['faces'][:,[0,1]],arrays['faces'][:,[1,2]],arrays['faces'][:,[2,0]]]),axis=1),axis=0)
    boundary_edges=edges[changed[edges[:,0]]!=changed[edges[:,1]]]
    assert len(boundary_edges)>0
    boundary_lengths=np.linalg.norm(points[boundary_edges[:,1]]-points[boundary_edges[:,0]],axis=1)
    assert boundary_lengths.min()>0
    audit=json.loads((BASE/'anatomy-audit01/anatomy-audit.json').read_text())
    # These values are sourceHandBranchSeeds' audited geometric label order,
    # not the runtime control dictionary order or an old heat-field label.
    digit_order=['pinky','ring','middle','index','thumb'];motions=[];signs=[];tests=[];phalanx_response=[]
    for side,label in [('L','left'),('R','right')]:
        whole_curl=[];whole_spread=[]
        palm=np.array(controls['measuredPalmNormals'][side])
        hand=dict(np.load(BASE/('target01/native-hand-'+side+'.npz')))
        branch=np.load(ROOT/audit['sides'][side]['output']['path'])['sourceHandBranchSeeds']
        ancestry=hand['sourceEdgeAncestry']
        for d,digit in enumerate(digit_order):
            source_ids=ancestry[(branch==d)&(ancestry[:,0]==ancestry[:,1]),0].astype(int)
            assert len(source_ids)>10,(side,digit,len(source_ids))
            stem='thumb' if digit=='thumb' else 'f_'+digit
            chain=['DEF-'+stem+'.%02d.'%s+side for s in (1,2,3)]
            for segment,name in enumerate(chain,1):
                moved,_,parity=pose([(name,controls['digitFlex'][label][name]['axisLocal'],.08)])
                displacement=np.linalg.norm(moved[source_ids]-points[source_ids],axis=1)
                own_four=native[source_ids,lookup[name]];own_full=full_matrix[source_ids,lookup[name]]
                phalanx_response.append({'side':side,'digit':digit,'segment':segment,'joint':name,
                    'actualGeometricBranchVertices':len(source_ids),'usefulWeightThreshold':.05,
                    'fourUsefulVertices':int(np.sum(own_four>.05)),'fullUsefulVertices':int(np.sum(own_full>.05)),
                    'fourOwnBranchWeightSum':float(own_four.sum()),'fullOwnBranchWeightSum':float(own_full.sum()),
                    'fourOwnBranchMaximumWeight':float(own_four.max()),'fullOwnBranchMaximumWeight':float(own_full.max()),
                    'singleJointSmallSkinMaximumM':float(displacement.max()),
                    'singleJointSmallSkinRMSM':float(np.sqrt(np.mean(displacement**2))),
                    'singleJointSmallSkinMovingVerticesAbove1Micrometre':int(np.sum(displacement>1e-6)),
                    'nativeFourVsLinearEvaluatorMaximumM':parity})
            small=[(n,controls['digitFlex'][label][n]['axisLocal'],.08) for n in chain]
            bent,_,_=pose(small)
            toward=float(np.mean((bent[source_ids]-points[source_ids])@palm))
            assert toward>0,(side,digit,toward)
            signs.append({'side':side,'digit':digit,'actualGeometricBranchVertices':len(source_ids),
                          'smallCurlMeanSkinDisplacementTowardPalmM':toward})
            tests.append((side+'-'+digit+'-curl',[(n,controls['digitFlex'][label][n]['axisLocal'],angle)
                for n,angle in zip(chain,(.55,.7,.45))]))
            whole_curl.extend([(n,controls['digitFlex'][label][n]['axisLocal'],angle)
                for n,angle in zip(chain,(.55,.7,.45))])
            if digit!='thumb':
                root=rest[chain[0]];direction=np.array(root['tail'])-root['head'];direction/=np.linalg.norm(direction)
                reference=np.array(rest['DEF-f_middle.01.'+side]['head'])
                outward=np.array(root['head'])-reference
                if digit=='middle':outward=np.array(rest['DEF-f_index.01.'+side]['head'])-reference
                outward-=direction*np.dot(outward,direction);outward-=palm*np.dot(outward,palm)
                outward/=np.linalg.norm(outward);world=np.cross(direction,outward);world/=np.linalg.norm(world)
                local=np.array(root['matrix'])[:3,:3].T@world
                spread,_,_=pose([(chain[0],local.tolist(),.08)])
                proof=float(np.mean((spread[source_ids]-points[source_ids])@outward))
                assert proof>0,(side,digit,proof)
                signs.append({'side':side,'digit':digit+'-spread','smallSkinDisplacementOutwardM':proof})
                tests.append((side+'-'+digit+'-spread',[(chain[0],local.tolist(),.18)]))
                whole_spread.append((chain[0],local.tolist(),.18))
            else:
                root=rest[chain[0]];direction=np.array(root['tail'])-root['head'];direction/=np.linalg.norm(direction)
                toward_index=np.array(rest['DEF-f_index.01.'+side]['head'])-points[source_ids].mean(0)
                toward_index-=direction*np.dot(toward_index,direction);toward_index/=np.linalg.norm(toward_index)
                axis=np.cross(direction,toward_index);axis/=np.linalg.norm(axis)
                local=np.array(root['matrix'])[:3,:3].T@axis
                opposed,_,_=pose([(chain[0],local.tolist(),.08)])
                proof=float(np.mean((opposed[source_ids]-points[source_ids])@toward_index))
                assert proof>0,proof
                signs.append({'side':side,'digit':'thumb-opposition','smallMotionTowardIndexM':proof,
                              'axisLocal':local.tolist(),'metacarpalJoint':chain[0]})
                tests.append((side+'-thumb-opposition',[(chain[0],local.tolist(),.35)]))
        tests.append((side+'-whole-hand-curl',whole_curl))
        tests.append((side+'-whole-hand-spread',whole_spread))
        for axis_index in (0,1,2):
            axis=np.eye(3)[axis_index].tolist()
            tests.append((side+'-wrist-'+str(axis_index),[('DEF-hand.'+side,axis,.35)]))
    reset()
    for title,rotations in tests:
        a,b,parity=pose(rotations);difference=np.linalg.norm(a-b,axis=1)
        boundary_ratios=np.linalg.norm(a[boundary_edges[:,1]]-a[boundary_edges[:,0]],axis=1)/boundary_lengths
        motions.append({'pose':title,'nativeFourVsLinearEvaluatorMaximumM':parity,
            'handFullVsFourMaximumM':float(difference[changed].max()),
            'handFullVsFourRMSM':float(np.sqrt(np.mean(difference[changed]**2))),
            'transitionFullVsFourMaximumM':float(difference[(alpha>0)&(alpha<1)].max()),
            'movingHandMaximumM':float(np.linalg.norm(a-points,axis=1)[changed].max()),
            'handDomainBoundaryEdges':len(boundary_edges),'boundaryEdgeLengthRatioMinimum':float(boundary_ratios.min()),
            'boundaryEdgeLengthRatioMaximum':float(boundary_ratios.max()),
            'rotations':[{'joint':n,'axisLocal':list(axis),'radians':angle} for n,axis,angle in rotations]})
    reset();bpy.context.view_layer.update()
    proof={'acceptedArt':False,'status':'INDEPENDENT_NATIVE_EXPORT_AND_DYNAMIC_MEASUREMENT_ONLY',
        'native':report['native'],'glb':report['glb'],'independentRecipeSHA256':sha(__file__),
        'exactSourceGeometryIDsAndOutsideFields':True,'jointCount':75,
        'continuousSegments':certificates,'minimumContinuousSegmentClearanceM':min(r['continuousClearanceLowerBoundM'] for r in certificates),
        'exportPositionMaximumM':export_pos_error,'exportNormalizedCoefficientMaximum':export_field_error,
        'exportTriangleWindingAndOriginalPolygonLoopCornerLineageExact':True,
        'exportOriginalUVCornerMaximum':uv_error,'nativeTriangulationLineage':report['nativeTriangulationLineage'],
        'bodyModifierOperators':report['bodyModifierOperators'],
        'exportCutoff':cutoff,'exportCutoffComparison':'DROP coefficient <= cutoff, normalize retained native float32 named coefficients',
        'maximumRemovedExportCutoffMass':float(removed_cutoff_mass.max()),
        'maximumNativeVsDecodedNamedCoefficientDelta':maximum_named_delta,
        'exportInverseBindMaximum':inverse_error,'smallCurlSkinSigns':signs,'movingFields':motions,
        'individualPhalanxOwnBranchFieldsAndActualSkinResponse':phalanx_response,
        'limits':['Measured positive small skin curl/opposition confirms control sign only; anatomical motion remains parent played review.',
                  'FULL/FOUR loss and wrist motion are measured, not automatically accepted.',
                  'No glove, art, socket calibration, engine or physical-phone qualification.']}
    (out/'independent-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    controls['qualification']='INDEPENDENT_SMALL_SKIN_CURL_SIGN_VERIFIED_MOVING_ART_PENDING'
    controls['smallCurlSignProof']={'path':str(out/'independent-verification.json'),'sha256':sha(out/'independent-verification.json')}
    controls['thumbOpposition']={r['side']:r for r in signs if r['digit']=='thumb-opposition'}
    (out/'digit-controls.json').write_text(json.dumps(controls,indent=2)+'\n')
    assert sha(report['native']['path'])==report['native']['sha256']
    for record in report['sourcePins']:assert sha(ROOT/record['path'])==record['sha256']
    print(json.dumps({'status':proof['status'],'segments':len(certificates),'movingPoses':len(motions),
        'smallSkinSigns':len(signs),'continuousClearanceM':proof['minimumContinuousSegmentClearanceM']}))


if __name__=='__main__':main()
