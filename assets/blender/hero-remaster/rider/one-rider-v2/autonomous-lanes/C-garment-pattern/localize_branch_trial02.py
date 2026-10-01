"""Read-only localization of failed pinch to exact original source face IDs."""
import bpy,bmesh,json,hashlib
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial02')
source=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';witness=R/'autonomous-lanes/C-garment-pattern/trial02/failed-mask-witness.blend'
def key(points):return tuple(sorted(tuple(round(float(x),6) for x in p) for p in points))
bpy.ops.wm.open_mainfile(filepath=str(source));s=next(o for o in bpy.context.scene.objects if o.type=='MESH');lookup={key([s.data.vertices[i].co for i in q.vertices]):q.index for q in s.data.polygons}
bpy.ops.wm.open_mainfile(filepath=str(witness));w=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('FAILED C'));b=bmesh.new();b.from_mesh(w.data)
vs=set(v for e in b.edges if e.is_boundary for v in e.verts);records=[]
for v in vs:
 degree=sum(e.is_boundary for e in v.link_edges)
 if degree!=2:records.append({'position':list(v.co),'boundaryDegree':degree,'remainingOriginalSourceFaceIds':[lookup[key([x.co for x in q.verts])] for q in v.link_faces],'remainingIncidentFaceCoordinates':[[list(x.co) for x in q.verts] for q in v.link_faces]})
assert len(records)==1 and len(records[0]['remainingOriginalSourceFaceIds'])==2
report={'status':'Read-only exact pinch diagnosis, no fix applied','records':records,'proposedNextCorrection':'After parent checkpoint, remove only these TWO original collar triangles from this same derivative and rebuild the planned curved panel. No broad threshold widening, source head change or accepted output implied.','witnessSHA256':hashlib.sha256(witness.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest()}
(O/'pinch-source-face-localization.json').write_text(json.dumps(report,indent=2)+'\n');print('PINCH_SOURCE_IDS',records[0]['remainingOriginalSourceFaceIds'],flush=True)
