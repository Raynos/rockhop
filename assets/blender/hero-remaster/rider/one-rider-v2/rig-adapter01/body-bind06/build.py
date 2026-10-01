"""Correct two proven skin-weight discontinuities on untouched body05."""
from pathlib import Path
import bpy,json,hashlib,math
from mathutils import Vector
BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind06');RUN=BASE/'body-bind06';RUN.mkdir(exist_ok=True)
SOURCE=BASE/'body-bind05/rider.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
rig=next(o for o in scene.objects if o.type=='ARMATURE');body=next(o for o in scene.objects if o.type=='MESH' and 'protected' in o.name.lower())
assert len(rig.data.bones)==19
positions=[tuple(v.co) for v in body.data.vertices];shapes={k.name:[tuple(v.co) for v in k.data] for k in body.data.shape_keys.key_blocks};groups={g.name:g for g in body.vertex_groups}
smooth=lambda t:(lambda u:u*u*(3-2*u))(max(0,min(1,t)))
def mix(a,b,t):return {a:1-t,b:t}
def torso(z):
 if z<1.05:return mix('pelvis','spine',smooth((z-.93)/.12))
 if z<1.24:return mix('spine','chest',smooth((z-1.12)/.12))
 return {'chest':1}
protected={i for poly in body.data.polygons if poly.material_index in [1,2] for i in poly.vertices}
rows=[]
for v in body.data.vertices:
 if v.index in protected:continue
 old={body.vertex_groups[g.group].name:g.weight for g in v.groups};p=v.co;sd='R' if p.x>0 else 'L';w=None;reason=None
 # Protect NEW native hands, retaining their independent grip morph contract.
 if any(n.startswith('hand.') and a>.999 for n,a in old.items()):continue
 if .78<=p.z<.85:
  w=mix('thigh.'+sd,'pelvis',smooth((p.z-.735)/.10));reason='Continue existing hip smoothstep to completion; then pure pelvis'
 elif 1.40<=p.z<1.47:
  threshold=.20-(p.z-1.2)*.20;aw=smooth((abs(p.x)-threshold)/.06)*smooth((1.47-p.z)/.07)
  sh=rig.data.bones['upperArm.'+sd].head_local;el=rig.data.bones['forearm.'+sd].head_local;wr=rig.data.bones['hand.'+sd].head_local
  d=(p-el).dot((sh-wr).normalized());arm=mix('forearm.'+sd,'upperArm.'+sd,smooth((d+.045)/.09));w={n:a*(1-aw) for n,a in torso(p.z).items()}
  for n,a in arm.items():w[n]=w.get(n,0)+a*aw
  reason='Continuous shoulder fade; no abrupt chest switch at Z1.43'
 if w is None:continue
 w={n:a for n,a in w.items() if a>1e-8};total=sum(w.values());w={n:a/total for n,a in w.items()};assert len(w)<=4 and abs(sum(w.values())-1)<1e-6
 if old==w:continue
 for g in body.vertex_groups:g.remove([v.index])
 for n,a in w.items():groups[n].add([v.index],a,'REPLACE')
 rows.append({'vertex':v.index,'position':list(p),'before':old,'after':w,'reason':reason})
assert positions==[tuple(v.co) for v in body.data.vertices]
assert shapes=={k.name:[tuple(v.co) for v in k.data] for k in body.data.shape_keys.key_blocks}
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'rider.blend'));bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in scene.objects:
 if o.type in ['MESH','EMPTY']:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(RUN/'rider-export.glb'),export_format='GLB',use_selection=True,export_animations=True,export_skins=True,export_force_sampling=True,export_extras=True,export_morph=True)
assert sha(SOURCE)==before
(OUT/'weight-changes.json').write_text(json.dumps({'sourceSHA256':before,'sourceUnchanged':True,'boneCount':19,'restPositionsExact':True,'allMorphPositionsExact':True,'changedVertices':len(rows),'rows':rows,'limits':'Localized weights only; armpit/other influences unchanged; not accepted until actual replay comparison'},indent=2)+'\n')
print('LOCALIZED_WEIGHT_FIX_EXPORTED',len(rows),flush=True)
