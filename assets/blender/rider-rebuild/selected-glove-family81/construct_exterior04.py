"""Single selected41 RIGHT authored exterior. Original CPU2 guard required.

Blender -b -t 2 --python-exit-code 1 --python construct_exterior04.py -- CPU_CHECK FRESH_OUT
No optimizer, retry, atlas, bake, field pruning or accepted native output.
"""
import json
import os
from pathlib import Path
import runpy
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from extract import ROOT, BASE, RECEIPT, WITNESS, checked, pin, canonical
from construct_surface03 import SURFACE_PROOF

CPU_PIN = {'path': 'harness/out/rider-rebuild/selected-glove-family81/extract01/cpu-check.json',
           'sha256': '4c593323090894014d301b5a6835b9f0f916cc95b6a6168d46203bc03550bf60'}
TARGET = 'UNACCEPTED_SelectedDerivedGloveExterior04.R'


def transport(a, face_ids, bary):
    """Ordered union of every membership on contributing corners, including zero weights.

    Interpolation and one float32 storage conversion are explicit. No row normalization,
    threshold, support limit, palette pruning or alteration of admitted source CSR.
    """
    offsets, indices, weights = [0], [], []
    for face, coefficients in zip(face_ids, bary):
        row = {}
        for parent, coefficient in zip(a['triangles'][face], coefficients):
            if coefficient == 0: continue
            lo, hi = a['fieldOffsets'][parent:parent+2]
            for group, weight in zip(a['fieldIndices'][lo:hi], a['fieldWeights'][lo:hi]):
                group = int(group)
                row[group] = row.get(group, 0.)+float(coefficient)*float(weight)
        indices.extend(row); weights.extend(row.values()); offsets.append(len(indices))
    return {'fieldOffsets':np.asarray(offsets,np.int64),'fieldIndices':np.asarray(indices,np.int32),
            'fieldWeights':np.asarray(weights,np.float32)}


def main(cpu_file, output):
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Original parent guard required'
    import bpy
    from exterior04 import construct
    started=time.monotonic(); output=Path(output).resolve()
    assert output.is_relative_to(BASE) and output != BASE and not output.exists()
    assert Path(cpu_file).resolve() == checked(CPU_PIN)
    cpu=json.loads(checked(CPU_PIN).read_text())
    assert cpu['status']=='INDEPENDENT_CPU_ACTUAL41_CACHE_IDENTITY_PASSED_UNACCEPTED' and not cpu['acceptedArt']
    checked(cpu['checker']); e=json.loads(checked(cpu['extraction']).read_text())
    assert e['sourceReceipt']==RECEIPT and e['sourceWitnessUnchanged'] and e['dependencyWitnessUnchanged']
    checked(e['recipe']); qualified=json.loads(checked(RECEIPT).read_text())
    assert e['native']==qualified['native'] and qualified['nativeStorage']['reopenVerified']
    proof=json.loads(checked(SURFACE_PROOF).read_text())
    assert proof['extraction']==cpu['extraction'] and not proof['acceptedArt']
    for key in ('recipe','selector','frozenPriorSelector'): checked(proof[key])
    row=e['objects']['ActualSelectedGlove.R']; landmarks=proof['sides']['R']
    assert landmarks['sourceArrays']==row['arrays'] and landmarks['sourceAncestry']==row['ancestry']
    assert len(row['groupNames'])==75
    with np.load(checked(row['arrays']),allow_pickle=False) as raw: a={k:raw[k] for k in raw.files}
    with np.load(checked(row['ancestry']),allow_pickle=False) as raw: ancestry={k:raw[k] for k in raw.files}
    output.mkdir(parents=True)
    report={'status':'AUTHORED_RIGHT_EXTERIOR04_STARTED_UNACCEPTED','acceptedArt':False,
        'recipe':pin(__file__),'geometryRecipe':pin(HERE/'exterior04.py'),'cpuAdmission':CPU_PIN,
        'extraction':cpu['extraction'],'sourceReceipt':RECEIPT,'nativeSource':e['native'],
        'surfaceLandmarks':SURFACE_PROOF,'sourceArrays':row['arrays'],'sourceAncestry':row['ancestry'],
        'groupNames':row['groupNames'],'sourceMaterialWitness':e['sourceWitness']['materials'],
        'policy':{'maximumAttempts':1,'optimizerCalls':0,'maximumSurfaceErrorM':.0005,'cageM':.001,'minimumNormalDot':.25},
        'fieldPolicy':'Full raw named source-field barycentric transport; ordered union including zero memberships; no normalization or pruning.',
        'visibilityLimit':'Retained selected donors and the unbaked derivative coexist; protected donor visibility is unchanged. A later moving recipient must hide retained donors and show only the baked derivative, without overlapping original or gray garments.',
        'limits':'Source-derived unbaked geometry only. Full bidirectional surface, grip/contact, rig/lean, texture bake, whole-rider moving art and device checks pending.'}
    def write():
        report['elapsedSeconds']=time.monotonic()-started
        (output/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
    def snapshot(stage,net,detail):
        face_ids=np.asarray([s[0] for s in net.samples],np.int32)
        bary=np.asarray([s[1] for s in net.samples],np.float64)
        data={'sourceFaceIds':face_ids,'barycentric':bary,
              'positions':np.einsum('ij,ijk->ik',bary,a['positions'][a['triangles'][face_ids]].astype(np.float64)).astype(np.float32),
              'triangles':np.asarray(net.faces,np.int32),'parts':np.asarray(net.parts),
              'labels':np.asarray(net.labels)}
        path=output/(stage+'.npz'); np.savez(path,**data)
        report['lastCompletedStage']={'stage':stage,'arrays':pin(path),**detail}; write()
        print('GLOVE81_EXTERIOR04 '+stage,flush=True)
        return data
    write()
    try:
        net,design=construct(a,ancestry,e['sourceWitness']['rig']['bones'],landmarks,snapshot)
        data=snapshot('authored-net',net,design)
        data.update(transport(a,data['sourceFaceIds'],data['barycentric']))
        data['expectedOpenBoundaryVertices']=np.asarray(design['expectedOpenBoundaryVertices'],np.int32)
        # Actual same-wall centroid witnesses, never the nearest opposing thin sheet.
        centroid_faces=[]; centroid_weights=[]; walls=[]
        for triangle,part in zip(data['triangles'],net.parts):
            wall='rim' if part=='cuff-return' else 'inner' if part=='cuff-lining' else 'outer'
            sample=net.surface.nearest(data['positions'][triangle].astype(np.float64).mean(0),wall)
            centroid_faces.append(sample[0]); centroid_weights.append(sample[1]); walls.append(wall)
        data.update(centroidSourceFaceIds=np.asarray(centroid_faces,np.int32),
                    centroidBarycentric=np.asarray(centroid_weights,np.float64),centroidWalls=np.asarray(walls))
        # Preserve source UV correspondence as data only, not a fake destination atlas.
        for i in range(len(row['uvLayerNames'])):
            data['sourceSampleUV'+str(i)]=np.einsum('ij,ijk->ik',data['barycentric'],a['uvLayer'+str(i)][a['triangleLoopIds'][data['sourceFaceIds']]]).astype(np.float32)
        candidate=output/'candidate.npz'; np.savez(candidate,**data); report['candidate']=pin(candidate)
        report.update(status='AUTHORED_RIGHT_EXTERIOR04_ARRAYS_UNACCEPTED',vertices=len(data['positions']),
                      triangles=len(data['triangles']),memberships=len(data['fieldWeights']),design=design)
        write()
        # Preserve the exact selected donor, full PBR and actual shared75 rig in the native.
        assert bpy.ops.wm.open_mainfile(filepath=str(checked(e['native'])),use_scripts=False)=={'FINISHED'}
        witness=runpy.run_path(str(checked(WITNESS))); sources={n:bpy.data.objects[n] for n in e['objects']}
        rig=bpy.data.objects['RiderSkeleton']; before=canonical(witness['retained'](sources,rig))
        visibility=lambda objects:{name:{'hideViewport':obj.hide_viewport,'hideRender':obj.hide_render,'hideInViewLayer':obj.hide_get()} for name,obj in objects.items()}
        donor_visibility=visibility(sources)
        assert before==e['sourceWitness'] and all(b.matrix_basis.is_identity for b in rig.pose.bones)
        source=sources['ActualSelectedGlove.R']; mesh=bpy.data.meshes.new(TARGET)
        mesh.from_pydata(data['positions'].tolist(),[],data['triangles'].tolist()); mesh.update()
        obj=bpy.data.objects.new(TARGET,mesh); bpy.context.scene.collection.objects.link(obj)
        obj.parent=source.parent; obj.matrix_parent_inverse=source.matrix_parent_inverse.copy(); obj.matrix_world=source.matrix_world.copy()
        for name in row['groupNames']: obj.vertex_groups.new(name=name)
        for vertex in range(len(data['positions'])):
            lo,hi=data['fieldOffsets'][vertex:vertex+2]
            for group,weight in zip(data['fieldIndices'][lo:hi],data['fieldWeights'][lo:hi]):
                obj.vertex_groups[int(group)].add([vertex],float(weight),'REPLACE')
        source_armature=next(m for m in source.modifiers if m.type=='ARMATURE')
        modifier=obj.modifiers.new('OnlySharedNative75','ARMATURE'); modifier.object=rig
        for name in ('use_bone_envelopes','use_vertex_groups','use_deform_preserve_volume','use_multi_modifier','vertex_group','invert_vertex_group'):
            setattr(modifier,name,getattr(source_armature,name))
        material=bpy.data.materials.new('UNACCEPTED04_Unbaked_Geometry'); material.use_nodes=True
        material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.22,.22,.22,1)
        mesh.materials.append(material)
        for face in mesh.polygons: face.use_smooth=True
        for key,values,domain in (('Source41Face',data['sourceFaceIds'],'POINT'),('Source41Barycentric',data['barycentric'],'POINT')):
            vector=values.ndim==2; attribute=mesh.attributes.new(key,'FLOAT_VECTOR' if vector else 'INT',domain)
            attribute.data.foreach_set('vector' if vector else 'value',values.astype(np.float32 if vector else np.int32).ravel())
        obj['acceptedArt']=False; obj['source41NativeSHA256']=e['native']['sha256']; obj['rawAncestryArrays']=str(candidate.relative_to(ROOT))
        assert canonical(witness['retained'](sources,rig))==before
        assert visibility(sources)==donor_visibility
        report['nativeVisibility']={'retainedDonors':donor_visibility,'unbakedDerivative':visibility({TARGET:obj})}
        stored=np.empty_like(data['positions']); mesh.vertices.foreach_get('co',stored.ravel()); assert np.array_equal(stored,data['positions'])
        actual=[]
        for vertex in mesh.vertices: actual.append([(g.group,g.weight) for g in vertex.groups])
        for v,groups in enumerate(actual):
            lo,hi=data['fieldOffsets'][v:v+2]
            assert dict(groups)==dict(zip(data['fieldIndices'][lo:hi].tolist(),data['fieldWeights'][lo:hi].tolist()))
        native=output/'UNACCEPTED-selected-derived-right-exterior04.blend'
        bpy.context.preferences.filepaths.save_version=0
        assert bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=False)=={'FINISHED'}
        report.update(status='AUTHORED_RIGHT_EXTERIOR04_NATIVE_UNACCEPTED_INDEPENDENT_INSPECTION_PENDING',
            native=pin(native),sourceWitnessUnchanged=True,nativeFieldsAndPositionsExact=True,
            nativeReopened=False,geometryModifierOnlyShared75=True,detailBaked=False)
        write()
    except BaseException as error:
        report.update(status='AUTHORED_RIGHT_EXTERIOR04_FAILED_UNACCEPTED',failure=repr(error),traceback=traceback.format_exc())
        write(); raise


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]; assert len(args)==2
    main(*args)
