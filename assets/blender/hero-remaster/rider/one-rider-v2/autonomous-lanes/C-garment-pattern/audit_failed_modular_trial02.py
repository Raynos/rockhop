"""Independent exact failed-mask source polygon/UV/material/native weight audit."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=R/'autonomous-lanes/C-garment-pattern/trial02';O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial02')
source=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';witness=RUN/'failed-mask-witness.blend';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p) for p in [source,witness]};mask=np.load(RUN/'failed-source-mask.npz');protected=set(mask['protectedSourceFaceIds'].tolist())
def records(o,ids=None):
 m=o.data;out=[]
 for q in m.polygons:
  if ids is not None and q.index not in ids:continue
  corners=[tuple(float(x) for x in list(m.vertices[m.loops[li].vertex_index].co)+sum((list(u.data[li].uv) for u in m.uv_layers),[])) for li in q.loop_indices];out.append((q.material_index,tuple(sorted(corners))))
 return Counter(out)
def weights(o):
 d=defaultdict(list)
 for v in o.data.vertices:d[tuple(float(x) for x in v.co)].append(tuple(sorted((o.vertex_groups[g.group].name,float(g.weight)) for g in v.groups)))
 return {k:sorted(v) for k,v in d.items()}
bpy.ops.wm.open_mainfile(filepath=str(source));s=next(o for o in bpy.context.scene.objects if o.type=='MESH');before=records(s,protected);sw=weights(s)
bpy.ops.wm.open_mainfile(filepath=str(witness));w=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('FAILED C'));after=records(w);ww=weights(w);mismatch=[k for k,v in ww.items() if sw.get(k)!=v]
report={'status':'FAILED MASK source retention proof ONLY; no new garment/rig acceptance','protectedSourcePolygons':sum(before.values()),'actualRetainedWitnessPolygons':sum(after.values()),'missingPositionAllUVLayersMaterialPolygons':sum((before-after).values()),'extraWitnessPolygons':sum((after-before).values()),'retainedNativeWeightMismatchCount':len(mismatch),'precision':'Exact stored Python float values, no rounding','inputs':inputs,'inputsAfter':{p:sha(p) for p in inputs},'actualSourcesUnmodified':True};assert inputs==report['inputsAfter'];(O/'source-retention-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('RETAINED_SOURCE',json.dumps(report),flush=True)
