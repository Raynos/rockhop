"""Retained actual selected R + own-side selected L, unchanged native75 wearer.
Parent CPU2 only. No new cavity, fitting sweep, inflation, bake or render.
Canonical body remains whole for the parent's separate covered-face mask stage.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback

import bpy
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CONFIG=HERE/'pair-inputs.json'
C=json.loads(CONFIG.read_text())
M=None


def load_helpers():
    row=C['sculptHelpers'];path=ROOT/row['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    spec=importlib.util.spec_from_file_location('boot04_frozen_paired_sculpt_helpers',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def pins(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:yield value
        else:
            for child in value.values():yield from pins(child)
    elif isinstance(value,list):
        for child in value:yield from pins(child)


def pair_reviews(report,body,rig):
    focus=np.array([0.,-.035,.055])
    views={name:(focus+np.array(offset)).tolist() for name,offset in [
        ('front',[0.,-1.2,.35]),('rear',[0.,1.2,.35]),('left',[-1.2,0.,.35]),
        ('right',[1.2,0.,.35]),('toe-threequarter',[.8,-1.1,.65]),('top',[0.,0.,1.3])]}
    for role,key in [('original-selected-pair','source'),('sculpted-selected-pair','target')]:
        if not all(key in report['sides'].get(side,{}) for side in ('R','L')):continue
        spec=dict(accepted=False,native=report['native'],mode='stills',
            objects=[report['sides'][side][key] for side in ('R','L')],bodyObject=body.name,rigObject=rig.name,
            focus=focus.tolist(),orthoScale=.72,views=views,
            limits=[C['previewBodyPolicy'],C['pendingGates']])
        (M.RUN['out']/(role+'-review.json')).write_text(json.dumps(spec,indent=2)+'\n')


def main():
    global M
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==1
    out=Path(args[0]).resolve();assert out.is_relative_to(ROOT/C['outputRoot']) and not out.exists()
    M=load_helpers()
    for row in pins(C):M.pin(row)
    old=M.module(C['legacyHelpers'],'boot04_frozen_bind_helpers')
    h=M.module(C['readOnlyHelpers'],'boot04_read_only_pair_helpers')
    extracted=json.loads(M.pin(C['extraction']).read_text())
    sections={side:json.loads(M.pin(row).read_text()) for side,row in C['sections'].items()}
    prior=json.loads(M.pin(C['retainedReport']).read_text())
    assert prior['native']==C['retainedNative']
    bpy.ops.wm.open_mainfile(filepath=str(M.pin(C['retainedNative'])))
    body,rig=(bpy.data.objects[C['objects'][k]] for k in ('body','rig'))
    assert len(rig.data.bones)==75 and rig.animation_data is None and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    before_body=old.body_signature(body,rig)
    out.mkdir(parents=True)
    report=dict(accepted=False,status='SELECTED_SCULPT_PAIR_BINDING_IN_PROGRESS',inputs=C,
        recipeSHA256=M.sha(__file__),controlsSHA256=M.sha(CONFIG),sides={},
        coveredBodyFaceMaskPending=True,canonicalWholeBodyPreserved=True,
        priorCavityFailureRetainedAsDiagnostic=C['retainedReport'])
    M.RUN.update(report=report,out=out,native=out/'paired-selected-boots.blend',body=body,rig=rig,
        old=old,beforeBody=before_body,sections=sections)
    def checkpoint(stage):
        report['status']=stage;assert old.body_signature(body,rig)==before_body
        bpy.ops.wm.save_as_mainfile(filepath=str(M.RUN['native']),compress=True)
        M.write_receipt();M.reviews(report,body,rig,sections);pair_reviews(report,body,rig)
    previous_target=bpy.data.objects[prior['sides']['R']['target']]
    previous_target.hide_render=True;previous_target.hide_set(True)
    for side in ('R','L'):
        source=bpy.data.objects[C['objects']['boots'][side]]
        frame,origin=np.array(sections[side]['footFrame']),np.array(sections[side]['footOrigin'])
        receipt=dict(source=source.name,side=side,medialLocalTSign=1 if side=='R' else -1,
            acceptedArt=False,bodyCoveredFaceMaskPending=True)
        report['sides'][side]=receipt
        if side=='R':
            base=bpy.data.objects[C['pairedRSource']]
            assert base.name==prior['sides']['R']['sculptObject']
            assert len(base.data.vertices)==prior['sides']['R']['denseSculpt']['vertices']==305453
            assert len(base.data.polygons)==prior['sides']['R']['denseSculpt']['faces']==610934
            receipt['retainedActualSelectedSculpt']=dict(native=C['retainedNative'],object=base.name,
                noAdditionalGeometryChange=True)
        else:
            assert json.loads(json.dumps(h.state(source)))==extracted['sides'][side]['sourceState']
            base=M.sculpture(source,side,frame,origin,receipt,old,checkpoint)
        target=M.duplicate(base,'Boot04PairedSelected.'+side)
        receipt['target'],receipt['sculptObject']=target.name,target.name
        # Reuse the already supported own-side native75 binding; full wearer is untouched.
        old.bind(target,frame,origin,side,rig)
        target['acceptedArt']=False;target['selectedOriginalSHA256']=C['selectedOriginal']['sha256']
        target['derivativeGeometryAncestor']=base.name;target['method']=C['method']
        target['coveredBodyFaceMaskPending']=True
        target.hide_render=False
        for obj in (base,source):obj.hide_render=True;obj.hide_set(True)
        checkpoint('UNACCEPTED_ACTUAL_SELECTED_SCULPT_BOUND_SAVED_'+side)
        receipt['topology']=M.topology(target.data);M.write_receipt();M.require_topology(receipt['topology'])
        assert np.array_equal(old.mesh_points(target.data),old.mesh_points(base.data))
        assert [tuple(d.uv) for d in target.data.uv_layers.active.data]==[tuple(d.uv) for d in base.data.uv_layers.active.data]
        group_names=[g.name for g in target.vertex_groups]
        maximum_weight_error=max(abs(sum(g.weight for g in vertex.groups)-1.) for vertex in target.data.vertices)
        receipt['binding']=dict(sharedRig=rig.name,nativeBones=len(rig.data.bones),groups=group_names,
            maximumWeightSumError=float(maximum_weight_error),
            maximumInfluences=max(len(v.groups) for v in target.data.vertices),
            geometryAndUVUnchangedByBind=True)
        assert set(group_names)=={'DEF-foot.'+side,'DEF-toe.'+side,'DEF-shin.'+side+'.001'}
        assert maximum_weight_error<2e-6 and receipt['binding']['maximumInfluences']<=3
        checkpoint('UNACCEPTED_VERIFIED_SELECTED_SCULPT_BOUND_'+side)
    for row in pins(C):M.pin(row)
    checkpoint('UNACCEPTED_SAVED_SELECTED_WHOLE_PAIR_MASKED_REVIEW_AND_PLAYED_GATES_PENDING')
    print(json.dumps(dict(status=report['status'],native=report['native'],noBakeRenderOrCavity=True)),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as error:
        if M is not None and M.RUN['report'] is not None:
            report=M.RUN['report'];report['failedStage']=report['status'];report['status']='FAILED_UNACCEPTED_SELECTED_PAIR_RECEIPTS_PERSISTED'
            report['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
            try:
                assert M.RUN['old'].body_signature(M.RUN['body'],M.RUN['rig'])==M.RUN['beforeBody']
                failed=M.RUN['out']/'failed-in-memory.blend';bpy.ops.wm.save_as_mainfile(filepath=str(failed),compress=True)
                report['failedInMemoryNative']=dict(path=str(failed.relative_to(ROOT)),sha256=M.sha(failed))
            except Exception as save_error:report['failedInMemorySaveError']=str(save_error)
            M.write_receipt();(M.RUN['out']/'failure.json').write_text(json.dumps(report,indent=2)+'\n')
            if 'native' in report:M.reviews(report,M.RUN['body'],M.RUN['rig'],M.RUN['sections']);pair_reviews(report,M.RUN['body'],M.RUN['rig'])
        raise
