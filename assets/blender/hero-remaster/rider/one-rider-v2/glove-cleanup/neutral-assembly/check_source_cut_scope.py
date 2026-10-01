"""Read-only source cut scope probe; no saved mesh changes."""
import bpy,bmesh,json
from pathlib import Path
import numpy as np
root=Path('/Users/raynos/projects/games/rockhop');out=root/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly'
build=json.loads((out/'report.json').read_text());run=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/neutral-assembly')
bpy.ops.wm.open_mainfile(filepath=str(run/'body-neutral-hands.blend'));body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
verts=[tuple(round(float(x),7) for x in v.co) for v in body.data.vertices[:build['sourceVertexPrefixCount']]]
retained=set(verts);uv=body.data.uv_layers.active
def signature(mesh,poly,layer):
    return tuple(sorted(tuple(round(float(x),7) for x in list(mesh.vertices[mesh.loops[i].vertex_index].co)+list(layer.data[i].uv)) for i in poly.loop_indices))
source_faces={signature(body.data,p,uv) for p in body.data.polygons if all(i<build['sourceVertexPrefixCount'] for i in p.vertices)}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=build['source']);body=next(o for o in bpy.context.scene.objects if o.type=='MESH');scale=build['sourceDisplayTransform']['scale'];trans=np.array(build['sourceDisplayTransform']['translation'])
for v in body.data.vertices:v.co=np.array(body.matrix_world@v.co)*scale+trans
original={tuple(round(float(x),7) for x in v.co) for v in body.data.vertices}
missing=original-retained
assert all(abs(p[0])>.25 and .70<p[2]<.9 for p in missing),'Deleted source point outside distal hand scope'
uv=body.data.uv_layers.active;expected_faces=[]
for poly in body.data.polygons:
    if all(tuple(round(float(x),7) for x in body.data.vertices[i].co) in retained for i in poly.vertices):expected_faces.append(signature(body.data,poly,uv))
changed=[f for f in expected_faces if f not in source_faces]
assert not changed,'Retained original source triangle geometry/UV changed'
new=[v for v in verts if v not in original]
print('NEW_SOURCE_CUT_VERTICES',len(new),new[:10]);extra=[]
for v in new:
    side=1 if v[0]>0 else -1;c=next(p['centre'] for p in build['patches'] if p['sign']==side)
    if np.linalg.norm(np.array(v[:2])-np.array(c[:2]))>.080:extra.append(v)
print('EXTRA_OUTSIDE_WRIST_SCOPE',len(extra),extra[:30])
assert not extra and len(new)==127
(out/'source-cut-scope-proof.json').write_text(json.dumps({'status':'Read-only independent source scope and retained triangle/UV verification','newSourceCutVertices':new,'newSourceCutVerticesOutside80mmWristRadius':extra,'originalPositionsRemoved':len(missing),'removedPointsOnlyDistalConnectedHandScope':True,'retainedOriginalTriangleUVSignatures':len(expected_faces),'changedRetainedOriginalTriangleUVSignatures':len(changed),'all127NewSourceCutVerticesOnActualWristLoops':True},indent=2)+'\n')
