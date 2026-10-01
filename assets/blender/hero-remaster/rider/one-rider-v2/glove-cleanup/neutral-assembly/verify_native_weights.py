"""Read-only native weight and full polygon proof for the sewn neutral master."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop')
OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly'
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/neutral-assembly')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((OUT/'report.json').read_text());master=RUN/'body-neutral-hands.blend';before=sha(master)
bpy.ops.wm.open_mainfile(filepath=str(master));body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
source_limit=report['sourceVertexPrefixCount'];offset=source_limit;rows=[]
for patch in report['patches']:
    data=np.load(patch['neutralCageSource']);count=len(data['vertices']);names=data['nativeBoneNames'].tolist();expected=data['nativeBoneWeights']
    actual=np.zeros_like(expected);columns={str(name):i for i,name in enumerate(names)}
    for i in range(count):
        for g in body.data.vertices[offset+i].groups:
            name=body.vertex_groups[g.group].name
            if name in columns:actual[i,columns[name]]=g.weight
    assert np.allclose(actual,expected,atol=1e-8,rtol=0),'Native weights changed'
    native_faces=len(data['polygonOffsets'])-1
    imported_faces=[p for p in body.data.polygons if all(offset<=v<offset+count for v in p.vertices)]
    assert len(imported_faces)==native_faces==1656
    transform=np.array(patch['rigidAlignmentMatrix']);translation=np.array(patch['translation'])
    expected_positions=(transform@data['vertices'].T).T+translation
    actual_positions=np.array([body.data.vertices[offset+i].co[:] for i in range(count)])
    assert np.allclose(actual_positions,expected_positions,atol=1e-7,rtol=0)
    rows.append({'side':patch['nativeSide'],'nativeCageSHA256':sha(Path(patch['neutralCageSource'])),'firstNativeVertexIndex':offset,'nativeVertices':count,'nativePolygons':len(imported_faces),'maximumAbsoluteWeightError':float(np.max(abs(actual-expected))),'maximumRigidMappingPositionErrorM':float(np.max(abs(actual_positions-expected_positions))),'nativeWeightSums':[float(actual.sum(1).min()),float(actual.sum(1).max())]})
    offset+=count+patch['sharedTransitionRingVertices']
assert offset==len(body.data.vertices)
assert before==sha(master)
(OUT/'native-weight-proof.json').write_text(json.dumps({'status':'Native neutral topology/weights retained in Blender master; no final rig','master':str(master),'masterSHA256Before':before,'masterSHA256After':sha(master),'hands':rows,'staticGLB':'GLB has no armature or skin; retained weights are in the master and sourceNPZs','recipeSHA256':sha(Path(__file__))},indent=2)+'\n')
print('NATIVE_NEUTRAL_WEIGHTS_AND_POLYGONS_VERIFIED')
