"""Independent frozen-file source polygon/corner audit outside actual collar band."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils.kdtree import KDTree
from collections import Counter
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/neck-native/trial01')
source=R/'glove-cleanup/neutral-assembly/body-neutral-hands.blend';trial=R/'neck-native/trial01/body-head.blend';mask=R/'collar-trial1/collar-selection.npz'
if (O/'outside-band-audit.json').exists():raise RuntimeError('Frozen outside-band audit exists')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in [source,trial,mask]}
d=np.load(mask);v=d['verticesBlender'];f=d['faces'];keep=d['retainedFaceMask'];boundary=d['boundaryVertices'];bt=KDTree(len(boundary));ft=KDTree(len(f))
for i,p in enumerate(boundary):bt.insert(p,i)
bt.balance()
for i,ids in enumerate(f):ft.insert(v[ids].mean(0),i)
ft.balance()
def record(o,protected=False):
 uv=o.data.uv_layers.active;rows=[];mats=[]
 for face in o.data.polygons:
  points=[o.matrix_world@o.data.vertices[i].co for i in face.vertices]
  if protected:
   if any(bt.find(p)[2]<.0350002 for p in points):continue
   if len(points)==3:
    co,i,distance=ft.find(np.array(points).mean(0))
    if distance<2e-6 and not keep[i] and max(min(np.linalg.norm(np.array(q)-p) for p in v[f[i]]) for q in points)<2e-6:continue
  key=tuple(sorted(tuple(round(float(x),7) for x in list(p)+list(uv.data[li].uv)) for p,li in zip(points,face.loop_indices)))
  rows.append(key);mats.append((face.material_index,key))
 return Counter(rows),Counter(mats)
bpy.ops.wm.open_mainfile(filepath=str(source));original=next(o for o in bpy.context.scene.objects if o.type=='MESH');expected,expectedMaterials=record(original,True)
bpy.ops.wm.open_mainfile(filepath=str(trial));actual=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'collar' in o.name);observed,observedMaterials=record(actual)
missing=sum((expected-observed).values());missingMaterials=sum((expectedMaterials-observedMaterials).values())
report={'status':'UNACCEPTED independent frozen-file preservation check','inputSHA256':before,'recipeSHA256':sha(Path(__file__)),'protectedOriginalPolygons':sum(expected.values()),'missingOrChangedPositionAndCornerUVPolygons':missing,'protectedOriginalPositionsAndUVPreserved':missing==0,'originalProtectedMaterialAssignmentsMissing':missingMaterials,'actualMaterialPreservationAccepted':False,'precision':'Source polygon degree + all world-position/loopUV corners rounded1e-7; no triangle triangulation guess','bandExclusionRadiusM':.0350002,'historicalHeadExclusion':'Exact retained source mask + triangle-center and corner agreement within2µm','limits':['Normals are not certified.','Actual saved trial material0 reset remains failed, regardless of geometry/UV match.','Native head and neck movement/rig are not certified.']}
report['inputSHA256After']={p:sha(Path(p)) for p in before};assert before==report['inputSHA256After'];assert missing==0
(O/'outside-band-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('OUTSIDE_BAND',json.dumps(report),flush=True)
