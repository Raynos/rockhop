"""Read-only independent protected corners/UV/material/native weight audit."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
from collections import Counter,defaultdict
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial01')
source=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';master=R/'autonomous-lanes/C-garment-pattern/trial01/character.blend';glb=master.with_suffix('.glb')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs={str(p):sha(p) for p in [source,master,glb]}
def rows(o,only_protected):
 m=o.data;m.calc_loop_triangles();u=m.uv_layers.get('NativeGloveAtlas') or m.uv_layers.active;out=[]
 for t in m.loop_triangles:
  p=m.polygons[t.polygon_index]
  if only_protected and min(m.vertices[i].co.z for i in p.vertices)>1.45:continue
  corners=[tuple(round(float(x),6) for x in list(o.matrix_world@m.vertices[m.loops[li].vertex_index].co)+list(u.data[li].uv)) for li in t.loops]
  out.append((m.materials[t.material_index].name,tuple(sorted(corners))))
 return Counter(out)
def weights(o,protected):
 out=defaultdict(list)
 for v in o.data.vertices:
  if protected and v.co.z>1.45:continue
  out[tuple(round(float(x),7) for x in v.co)].append(tuple(sorted((o.vertex_groups[g.group].name,round(g.weight,7)) for g in v.groups)))
 return {k:sorted(v) for k,v in out.items()}
bpy.ops.wm.open_mainfile(filepath=str(source));s=next(o for o in bpy.context.scene.objects if o.type=='MESH');source_rows=rows(s,True);sw=weights(s,True)
bpy.ops.wm.open_mainfile(filepath=str(master));m=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('UNACCEPTED C'));master_rows=rows(m,False);mw=weights(m,False)
missing_master=sum((source_rows-master_rows).values());weight_bad=[k for k,v in sw.items() if mw.get(k)!=v]
explicit={'slots':[mat.name for mat in m.data.materials],'polygonMaterialCounts':dict(Counter(p.material_index for p in m.data.polygons)),'polygonMaterialArraySHA256':hashlib.sha256(np.asarray([p.material_index for p in m.data.polygons],dtype=np.int32).tobytes()).hexdigest()}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb));bpy.context.view_layer.update();gr=Counter()
for o in bpy.context.scene.objects:
 if o.type=='MESH':gr.update(rows(o,False))
missing_reimport=sum((source_rows-gr).values())
report={'status':'UNACCEPTED independent source protection evidence, no appearance/rig pass','inputs':inputs,'recipeSHA256':sha(__file__),'protectedSourceTriangles':sum(source_rows.values()),'missingMasterSourcePositionUVMaterialTriangles':missing_master,'missingGLBReimportSourcePositionUVMaterialTriangles':missing_reimport,'precision':'Coordinates and rendered atlas UV rounded1e-6; native group weights rounded1e-7','protectedSourceVertexKeysBelow1_45m':len(sw),'protectedNativeWeightMismatchVertexCount':len(weight_bad),'mismatchVertexSamples':weight_bad[:10],'explicitMaterialAssignment':explicit,'normalContinuity':'Visible hard seam; not accepted. New cloth and source normals are not claimed seamless.','inputsAfter':{p:sha(p) for p in inputs}}
assert inputs==report['inputsAfter'];(O/'independent-source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('SOURCE_AUDIT',json.dumps({k:report[k] for k in ['protectedSourceTriangles','missingMasterSourcePositionUVMaterialTriangles','missingGLBReimportSourcePositionUVMaterialTriangles','protectedNativeWeightMismatchVertexCount']}),flush=True)
