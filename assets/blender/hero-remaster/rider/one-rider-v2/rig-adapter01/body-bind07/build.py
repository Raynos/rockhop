"""Constrained connected-edge weight smoothing; no mesh or joint edits."""
from pathlib import Path
import bpy,json,hashlib
import numpy as np
BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01');OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind07');RUN=BASE/'body-bind07';RUN.mkdir(exist_ok=True)
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
def smooth(t):u=np.clip(t,0,1);return u*u*(3-2*u)
x=np.abs(positions[:,0]);z=positions[:,2]
strength=smooth((z-.96)/.07)*smooth((1.51-z)/.07)*smooth((x-.13)/.06)
strength[protectedids]=0
edges=np.array([e.vertices[:] for e in body.data.edges],dtype=np.int64);src=np.r_[edges[:,0],edges[:,1]];dst=np.r_[edges[:,1],edges[:,0]];degree=np.bincount(src,minlength=len(seed));assert np.all(degree>0)
w=seed.copy()
for iteration in range(80):
 sums=np.zeros_like(w);np.add.at(sums,src,w[dst]);average=sums/degree[:,None]
 step=.55*w+.43*average+.02*seed;w=strength[:,None]*step+(1-strength[:,None])*seed
# Production GLB contract uses at most four influences. Record discarded mass.
keep=np.argsort(w,axis=1)[:,-4:];pruned=np.zeros_like(w);np.put_along_axis(pruned,keep,np.take_along_axis(w,keep,axis=1),axis=1);discarded=(w-pruned).sum(axis=1);w=pruned/pruned.sum(axis=1)[:,None]
w[protectedids]=seed[protectedids]
assert np.isfinite(w).all() and np.max(np.abs(w.sum(axis=1)-1))<1e-6
assert np.array_equal(w[protectedids],seed[protectedids])
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
(OUT/'weight-changes.json').write_text(json.dumps({'sourceHashes':before,'sourceUnchanged':True,'changedVertices':len(changed),'protectedVertices':len(protected),'iterations':80,'weightsStep':{'current':.55,'edgeNeighbourMean':.43,'originalRegularization':.02},'featherSelection':'Z.96..1.51 and absX>.13; original hood/gloves/cloth seam frozen','maxDiscardedInfluenceMass':float(discarded.max()),'restPositionsExact':True,'method':'Connected edges only, no proximity bridging across air gaps; not a biharmonic solver','limits':'Not appearance acceptance; all joints, protected materials and rig mappings unchanged'},indent=2)+'\n');print('CONSTRAINED_WEIGHT_DIFFUSION_EXPORTED',len(changed),flush=True)
