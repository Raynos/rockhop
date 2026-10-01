"""Keep accepted waist correction; restore original WHITE shoulder weights."""
from pathlib import Path
import bpy,json,hashlib
import numpy as np
BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01');OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind08');RUN=BASE/'body-bind08';RUN.mkdir(exist_ok=True)
SOURCE=BASE/'body-bind06/rider.blend';ORIGINAL=BASE/'body-bind05/rider.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in [SOURCE,ORIGINAL]};bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
rig=next(o for o in scene.objects if o.type=='ARMATURE');body=next(o for o in scene.objects if o.type=='MESH' and 'protected' in o.name.lower());names=[g.name for g in body.vertex_groups];assert len(names)==19
with bpy.data.libraries.load(str(ORIGINAL),link=False) as (src,dst):dst.objects=[n for n in src.objects if 'protected' in n.lower()]
original=dst.objects[0];assert len(body.data.vertices)==len(original.data.vertices)
positions=np.array([v.co for v in body.data.vertices],dtype=np.float64);assert np.array_equal(positions,np.array([v.co for v in original.data.vertices]))
def weights(obj):
 result=np.zeros((len(obj.data.vertices),len(names)),dtype=np.float64)
 for v in obj.data.vertices:
  for g in v.groups:result[v.index,names.index(obj.vertex_groups[g.group].name)]=g.weight
 return result
existing=weights(body);seed=existing.copy();old=weights(original)
# Discard rejected height-only shoulder edits; retain completed hip blend.
seed[positions[:,2]>=1.38]=old[positions[:,2]>=1.38]
protected={i for poly in body.data.polygons if poly.material_index in [1,2] for i in poly.vertices}
protectedids=np.array(sorted(protected),dtype=np.int64);assert np.array_equal(seed[protectedids],existing[protectedids])
w=seed.copy()
changed=np.flatnonzero(np.max(np.abs(w-existing),axis=1)>1e-7)
for i in changed:
 for group in body.vertex_groups:group.remove([int(i)])
 for lane,value in enumerate(w[i]):
  if value>1e-8:body.vertex_groups[lane].add([int(i)],float(value),'REPLACE')
assert np.array_equal(positions,np.array([v.co for v in body.data.vertices]))
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'rider.blend'));bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in scene.objects:
 if o.type in ['MESH','EMPTY']:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(RUN/'rider-export.glb'),export_format='GLB',use_selection=True,export_animations=True,export_skins=True,export_force_sampling=True,export_extras=True,export_morph=True)
assert all(sha(Path(p))==h for p,h in before.items())
(OUT/'weight-changes.json').write_text(json.dumps({'sourceHashes':before,'sourceUnchanged':True,'changedVertices':len(changed),'protectedVertices':len(protected),'method':'Retain06completedwaistblend; resetshoulder05. Private runtime source-rim reconciliation is a separate opt-in flag','restPositionsExact':True,'limits':'Only source weights; no geometry/joint/PBR/morph changes or appearance acceptance'},indent=2)+'\n');print('WAIST_ONLY_SHOULDER_RESET_EXPORTED',len(changed),flush=True)
