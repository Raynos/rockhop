"""Independent read-only verification of every corrected diagnostic frame."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE='one-rider-v2/glove-cleanup/neutral-assembly'
OUT=ROOT/'docs/evidence/hero-remaster'/BASE/'motion-correction01'
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE/'motion-correction01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
master=RUN/'semantic-wrist-diagnostic.blend';before=sha(master);report=json.loads((OUT/'report.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(master));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');rest=np.array([v.co[:] for v in body.data.vertices]);group_names={g.index:g.name for g in body.vertex_groups}
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');names=set(arm.data.bones.keys());semantic=[]
for hand in report['semantics']:
    side=hand['side'];sign=1 if side=='L' else -1;first,last=hand['nativeVertexRange'];ids=set(range(first,last+1));edges=np.array([e.vertices[:] for e in body.data.edges if all(int(i) in ids for i in e.vertices)])
    cage=np.load(Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete')/f'neutral-complete-{side}.npz');native_names=cage['nativeBoneNames'].tolist();native=np.zeros_like(cage['nativeBoneWeights'])
    for index in ids:
        deform={group_names[g.group]:float(g.weight) for g in body.data.vertices[index].groups if group_names[g.group] in names and g.weight>0}
        assert deform=={f'diagnosticHand{sign}':1.0},'Root/oppositehand contamination'
        for g in body.data.vertices[index].groups:
            name=group_names[g.group]
            if name in native_names:native[index-first,native_names.index(name)]=g.weight
    assert np.array_equal(native,cage['nativeBoneWeights'])
    lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
    seam_ids=set(hand['sourceWristVertices']+hand['transitionVertices']+[first+int(i) for i in cage['wristLoop']])
    seam_edges=np.array([e.vertices[:] for e in body.data.edges if all(int(i) in seam_ids for i in e.vertices)])
    seam_lengths=np.linalg.norm(rest[seam_edges[:,0]]-rest[seam_edges[:,1]],axis=1)
    semantic.append((side,edges,lengths,seam_edges,seam_lengths))
checks=[]
for frame in range(36):
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=np.array([v.co[:] for v in mesh.vertices])
    for side,edges,lengths,seam_edges,seam_lengths in semantic:
        current=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1);valid=lengths>.001;error=float(abs(current-lengths).max());ratio=float((current[valid]/lengths[valid]).max())
        assert error<1e-6 and ratio<1.001
        seam_current=np.linalg.norm(posed[seam_edges[:,0]]-posed[seam_edges[:,1]],axis=1);seam_valid=seam_lengths>.001
        checks.append({'frame':frame,'side':side,'edges':len(edges),'maximumAbsoluteEdgeLengthErrorM':error,'maximumRatioForEdgesOver1mm':ratio,'seamEdgeCount':len(seam_edges),'seamMaximumAbsoluteLengthChangeM':float(abs(seam_current-seam_lengths).max()),'seamMinimumRatioForEdgesOver1mm':float((seam_current[seam_valid]/seam_lengths[seam_valid]).min()),'seamMaximumRatioForEdgesOver1mm':float((seam_current[seam_valid]/seam_lengths[seam_valid]).max()),'seamMaximumDeformedEdgeLengthM':float(seam_current.max())})
    ev.to_mesh_clear()
assert before==sha(master)
(OUT/'independent-edge-verification.json').write_text(json.dumps({'status':'All36pairedframes numerically preserve nativehand shapes; parent moving appearance judgment pending','masterSHA256Before':before,'masterSHA256After':sha(master),'nativeWeightsMaximumAbsoluteError':0,'nativeHandVerticesAssignedRootOrOppositeHand':0,'checkedNativeHandVertices':3336,'allNativeHandDiagnosticWeightsExactly1':True,'checkedFrames':36,'checks':checks,'scope':'Nativehand edge lengths only; does not claim cuff deformation quality/collision/gameplay contacts','recipeSHA256':sha(Path(__file__))},indent=2)+'\n')
print('INDEPENDENT36FRAME_HAND_EDGE_VERIFICATION_COMPLETE')
