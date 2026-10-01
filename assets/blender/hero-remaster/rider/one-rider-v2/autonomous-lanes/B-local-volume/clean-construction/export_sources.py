"""Clean lineage fresh read-only whole-body sizing audit and raw CPU geometry export."""
import bpy,numpy as np,json,hashlib,sys,platform,resource
from pathlib import Path
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
RUN=ROOT/'autonomous-lanes/B-local-volume/clean-construction/trial01';RUN.mkdir(parents=True,exist_ok=True)
body_path=ROOT/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend'
head_path=ROOT/'head-cleanup/mpfb-v8-palette/african/head.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(p):sha(p) for p in [body_path,head_path]}
bpy.ops.wm.open_mainfile(filepath=str(body_path))
body=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
body.data.calc_loop_triangles();uv=body.data.uv_layers.active.data
v=np.array([body.matrix_world@x.co for x in body.data.vertices],dtype=np.float32)
f=np.array([t.vertices[:] for t in body.data.loop_triangles],dtype=np.int32)
triuv=np.array([[uv[i].uv[:] for i in t.loops] for t in body.data.loop_triangles],dtype=np.float32)
mi=np.array([body.data.polygons[t.polygon_index].material_index for t in body.data.loop_triangles],dtype=np.int32)
all_uv=np.array([[[layer.data[i].uv[:] for i in t.loops] for t in body.data.loop_triangles] for layer in body.data.uv_layers],dtype=np.float32)
np.savez(RUN/'body-source.npz',vertices=v,faces=f,triangleUV=triuv,allTriangleUV=all_uv,materialIndex=mi)
report=dict(status='Fresh clean construction source export; no retired collar masks or seams used',sources=before,
    bodyObject=body.name,bodyVertices=len(v),bodyTriangles=len(f),bodyBounds=[v.min(0).tolist(),v.max(0).tolist()],
    materials=[m.name if m else None for m in body.data.materials],materialFaceCounts={str(i):int(np.sum(mi==i)) for i in np.unique(mi)},
    blenderVersion=bpy.app.version_string,embeddedPython=sys.version,sourceUVLayers=[u.name for u in body.data.uv_layers],
    maxRSSNativeUnits=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
with bpy.data.libraries.load(str(head_path),link=False) as (src,dst):dst.objects=list(src.objects)
native=[o for o in dst.objects if o and o.type=='MESH'];head=max(native,key=lambda o:len(o.data.vertices))
h=np.array([head.matrix_world@x.co for x in head.data.vertices],dtype=np.float32)*.42+[0,0,1.59338]
head.data.calc_loop_triangles();hf=np.array([t.vertices[:] for t in head.data.loop_triangles],dtype=np.int32)
np.savez(RUN/'head-source.npz',vertices=h.astype(np.float32),faces=hf)
report['headWorldBounds']=[h.min(0).tolist(),h.max(0).tolist()]
report['sourcesAfter']={p:sha(p) for p in before};assert before==report['sourcesAfter']
(RUN/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
