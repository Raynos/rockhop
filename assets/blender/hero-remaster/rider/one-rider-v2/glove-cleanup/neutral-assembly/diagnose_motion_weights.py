"""Read-only diagnosis of first failed temporary seam motion, no weight fix."""
import hashlib,json
from collections import Counter
from pathlib import Path
import bpy,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop')
OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly/motion-failure01'
OUT.mkdir(exist_ok=True)
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/neutral-assembly')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
master=RUN/'temporary-wrist-diagnostic.blend';clean=RUN/'body-neutral-hands.blend'
before={str(p):sha(p) for p in [master,clean]}
proof=json.loads((OUT.parent/'native-weight-proof.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(clean));body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
clean_materials=dict(Counter(p.material_index for p in body.data.polygons))
clean_semantic={i for p in body.data.polygons if p.material_index==1 for i in p.vertices}
clean_group_names={g.index:g.name for g in body.vertex_groups}
source_limit=min(r['firstNativeVertexIndex'] for r in proof['hands'])
source_wrist={side:[v.index for v in body.data.vertices[:source_limit] if any(clean_group_names[g.group]=='wrist.'+side and g.weight>.999 for g in v.groups)] for side in ['L','R']}
bpy.ops.wm.open_mainfile(filepath=str(master));body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
materials=dict(Counter(p.material_index for p in body.data.polygons));mask={i for p in body.data.polygons if p.material_index==1 for i in p.vertices}
group_names={g.index:g.name for g in body.vertex_groups};bone_names=set(arm.data.bones.keys())
rest=np.array([v.co[:] for v in body.data.vertices]);rows=[];allwrong=set()
for hand in proof['hands']:
    side=hand['side'];sign=1 if side=='L' else -1;first=hand['firstNativeVertexIndex'];count=hand['nativeVertices']
    wanted=f'diagnosticHand{sign}';weights=[];wrong=[];dominants=Counter()
    cage=np.load(Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete')/f'neutral-complete-{side}.npz')
    native_names=cage['nativeBoneNames'].tolist();native_actual=np.zeros_like(cage['nativeBoneWeights'])
    for index in range(first,first+count):
        v=body.data.vertices[index];deform={group_names[g.group]:float(g.weight) for g in v.groups if group_names[g.group] in bone_names and g.weight>0}
        dominant=max(deform,key=deform.get);dominants[dominant]+=1
        if deform.get(wanted,0)<.999999:
            native_dominant=str(native_names[int(cage['nativeBoneWeights'][index-first].argmax())])
            wrong.append({'vertex':index,'nativeCageVertex':index-first,'rest':rest[index].tolist(),'diagnosticWeights':deform,'nativeDominantBone':native_dominant})
            allwrong.add(index)
        for g in v.groups:
            name=group_names[g.group]
            if name in native_names:native_actual[index-first,native_names.index(name)]=g.weight
    assert np.array_equal(native_actual,cage['nativeBoneWeights'])
    rows.append({'side':side,'nativeVertices':count,'semanticWristSourceVertices':len(source_wrist[side]),'nativeWeightsMaximumAbsoluteError':float(abs(native_actual-cage['nativeBoneWeights']).max()),'diagnosticDominantGroups':dict(dominants),'wrongNativeFingerVertices':len(wrong),'wrongNativeDominantBones':dict(Counter(r['nativeDominantBone'] for r in wrong)),'wrongVertexDetails':wrong})
frame_metrics=[]
for frame in [0,9,10,18,26]:
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=np.array([v.co[:] for v in mesh.vertices])
    edges=[]
    for edge in mesh.edges:
        a,b=edge.vertices
        if (a in allwrong)!=(b in allwrong):
            old=float(np.linalg.norm(rest[a]-rest[b]));new=float(np.linalg.norm(posed[a]-posed[b]));edges.append({'vertices':[int(a),int(b)],'restLengthM':old,'posedLengthM':new,'ratio':new/max(old,1e-12)})
    edges.sort(key=lambda r:r['posedLengthM'],reverse=True)
    frame_metrics.append({'frame':frame,'weightBoundaryEdgeCount':len(edges),'maximumWeightBoundaryEdgeLengthM':edges[0]['posedLengthM'] if edges else 0,'mostStretchedEdges':edges[:8]})
    ev.to_mesh_clear()
assert before=={str(p):sha(Path(p)) for p in before}
report={'status':'FAIL first temporary diagnostic deformation: two fingers form spikes; static geometry approval only','failureCount':1,'sourceFilesSHA256Before':before,'sourceFilesSHA256After':{str(p):sha(Path(p)) for p in before},'cleanPolygonMaterialCounts':clean_materials,'diagnosticPolygonMaterialCounts':materials,'cleanSemanticGloveVertices':len(clean_semantic),'diagnosticMaterialGloveVertices':len(mask),'hands':rows,'frames':frame_metrics,'cause':'mesh.materials.clear() reset polygon material indices to0 before semantic mask was built; empty glove mask then excluded distal nativefinger vertices atZ<=0.70 from spatial branch and assigned diagnosticRoot. Adjacent vertices follow hand; resulting edge stretching creates spikes. Native anatomy weights unchanged.','specificFixProposedOnly':'Capture immutable original native-hand vertex ranges plus actual seam/sourcewrist sets before any material changes. Set all nativehand vertices to their own diagnosticHand with totaldiagnostic weight1; derive cuff/seam blending from semantic sourcewrist sets/native anatomical influence and forearm connectivity. Assert no nativefinger vertex belongs to root/oppositehand and sums1. Preserve native groups. Use separate material_override for gray rendering or restore original polygon materialindices explicitly. Rerender matched36frames only after parent checkpoint authorisation.','noFixOrBakePerformed':True,'recipeSHA256':sha(Path(__file__))}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('DIAGNOSTIC_NATIVE_HAND_WEIGHT_FAILURE',json.dumps([{'side':r['side'],'wrong':r['wrongNativeFingerVertices'],'groups':r['diagnosticDominantGroups']} for r in rows]),flush=True)
