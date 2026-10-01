"""CPU-only native semantic garment fitting to freshC19anatomical landmarks."""
import bpy,sys,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
repo=Path('/Users/raynos/projects/games/rockhop');run=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01');out=repo/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/fit01';out.mkdir(exist_ok=True)
instrument='--instrument-full' in sys.argv
if instrument:out=out.parent/'fullskin-instrument01';out.mkdir(exist_ok=True)
else:assert not (run/'fit01.npz').exists(),'Preserve frozen fit01; use an owned reproduction directory for another fit'
bpy.ops.wm.read_factory_settings(use_empty=True)
addon=Path.home()/'Library/Application Support/Blender/5.1/extensions/user_default';bpy.context.preferences.extensions.repos.new(name='Garment source read-only',module='garment_mpfb',custom_directory=str(addon))
import addon_utils
addon_utils.enable('bl_ext.garment_mpfb.mpfb',default_set=True,persistent=False)
from bl_ext.garment_mpfb.mpfb.services.humanservice import HumanService
from bl_ext.garment_mpfb.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.4,muscle=.68,weight=.58,proportions=.65,height=.52);macro['race']={'asian':.25,'caucasian':.35,'african':.4}
base=HumanService.create_human(mask_helpers=True,feet_on_ground=True,scale=.1,macro_detail_dict=macro);base.name='Hidden_native_anatomical_correspondence';HumanService.add_builtin_rig(base,'default',import_weights=True)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');bones={b.name:(b.head_local.copy(),b.tail_local.copy()) for b in arm.data.bones}
clothes=HumanService.add_mhclo_asset(str(run/'source/male_casualsuit02.mhclo'),base,subdiv_levels=0,material_type='NONE',set_up_rigging=True,interpolate_weights=True,import_subrig=False,import_weights=True)
assert len(clothes.data.vertices)==2136 and len(clothes.data.polygons)==2060
canonical=['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','forearm.L','hand.L','shoulder.R','upperArm.R','forearm.R','hand.R','thigh.L','shin.L','foot.L','thigh.R','shin.R','foot.R']
manifest=json.loads((repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu/pose-manifest.json').read_text());T={name:np.array(b['sourceWorld']) for name,b in zip(canonical,manifest['primitives'][0]['inverseBindOriginPositions'])}
core={'pelvis':'spine05','spine':'spine04','chest':'spine02','neck':'neck01','head':'head'}
for side in ['L','R']:
 core.update({'shoulder.'+side:'clavicle.'+side,'upperArm.'+side:'upperarm01.'+side,'forearm.'+side:'lowerarm01.'+side,'hand.'+side:'wrist.'+side,'thigh.'+side:'upperleg01.'+side,'shin.'+side:'lowerleg01.'+side,'foot.'+side:'foot.'+side})
def game(p):return np.array([-p.y,p.z,p.x])
S={name:game(bones[n][0]) for name,n in core.items()}
child={'pelvis':'spine','spine':'chest','chest':'neck','neck':'head'}
for side in ['L','R']:child.update({'shoulder.'+side:'upperArm.'+side,'upperArm.'+side:'forearm.'+side,'forearm.'+side:'hand.'+side,'thigh.'+side:'shin.'+side,'shin.'+side:'foot.'+side})
M={};mapping=[]
for name in canonical:
 if name in child:
  ds=S[child[name]]-S[name];dt=T[child[name]]-T[name];ratio=np.linalg.norm(dt)/np.linalg.norm(ds);u=ds/np.linalg.norm(ds);R=np.array(Vector(ds).rotation_difference(Vector(dt)).to_matrix());linear=R@(np.eye(3)+(ratio-1)*np.outer(u,u))
 else:linear=np.eye(3);ratio=1.
 M[name]=(linear,T[name]-linear@S[name]);mapping.append({'bone':name,'nativeHeadGame':S[name].tolist(),'freshHeadGame':T[name].tolist(),'lengthRatio':float(ratio),'linearDeterminant':float(np.linalg.det(linear))})
def role(name):
 if name not in bones:return None
 side=name.split('.')[-1] if '.' in name else None
 if name=='root' or name.startswith(('pelvis','spine05')):return 'pelvis'
 if name.startswith(('spine04','spine03')):return 'spine'
 if name.startswith(('spine02','spine01','breast')):return 'chest'
 if name.startswith('neck'):return 'neck'
 if name.startswith(('clavicle','shoulder01')):return 'shoulder.'+side
 if name.startswith('upperarm'):return 'upperArm.'+side
 if name.startswith('lowerarm'):return 'forearm.'+side
 if name.startswith(('wrist','finger','metacarpal')):return 'hand.'+side
 if name.startswith('upperleg'):return 'thigh.'+side
 if name.startswith('lowerleg'):return 'shin.'+side
 if name.startswith(('foot','toe')):return 'foot.'+side
 return 'head'
W=[];P=[];FullW=[];maxDiscarded=0.;groups=list(clothes.vertex_groups.keys())
for v in clothes.data.vertices:
 weights={}
 for g in v.groups:
  name=role(groups[g.group])
  if name:weights[name]=weights.get(name,0)+g.weight
 assert sum(weights.values())>0,(v.index,'no anatomical skin')
 total=sum(weights.values());allW={name:w/total for name,w in weights.items()};FullW.append([allW.get(name,0.) for name in canonical]);ranked=sorted(allW.items(),key=lambda x:(-x[1],canonical.index(x[0])));maxDiscarded=max(maxDiscarded,sum(w for _,w in ranked[4:]));kept=ranked[:4];total=sum(w for _,w in kept);weights={name:w/total for name,w in kept};point=game(clothes.matrix_world@v.co)
 P.append(sum(w*(M[name][0]@point+M[name][1]) for name,w in weights.items()));W.append([weights.get(name,0.) for name in canonical])
P=np.array(P);W=np.array(W);assert np.isfinite(P).all() and np.max(abs(W.sum(1)-1))<1e-12
# Game conversion reflects native anatomical left axis; reverse winding and UVloops together.
faces=[list(reversed(list(f.vertices))) for f in clothes.data.polygons];uv=[]
for f in clothes.data.polygons:uv.extend([list(clothes.data.uv_layers.active.data[i].uv) for i in reversed(list(f.loop_indices))])
field=run/('fullskin-instrument01.npz' if instrument else 'fit01.npz')
if instrument:
 frozen=np.load(run/'fit01.npz');assert np.array_equal(P,frozen['positions']) and np.array_equal(W,frozen['weights']) and np.array_equal(np.array(faces),frozen['quads'])
np.savez_compressed(field,positions=P,weights=W,fullWeights=np.array(FullW),quads=np.array(faces),uvLoops=np.array(uv))
mesh=bpy.data.meshes.new('Clean_garment_topology_fit01');mesh.from_pydata([(p[0],-p[2],p[1]) for p in P],[],faces);mesh.update();obj=bpy.data.objects.new('NEW_clean_garment_fit01_UNACCEPTED',mesh);bpy.context.collection.objects.link(obj);layer=mesh.uv_layers.new(name='Native_garment_bake_UV')
for loop,tex in zip(layer.data,uv):loop.uv=tex
for name in canonical:obj.vertex_groups.new(name=name)
for i,weights in enumerate(W):
 for j,w in enumerate(weights):
  if w>0:obj.vertex_groups[j].add([i],float(w),'REPLACE')
for old in [base,clothes,arm]:bpy.data.objects.remove(old,do_unlink=True)
# Save an editable CPU geometry master, no renderer, new source rig or asset promotion.
master=run/('fullskin-instrument01.blend' if instrument else 'fit01.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(master),compress=True)
report={'status':'CPU clean garment anatomical correspondence fit, unaccepted','nativeSource':str(run/'source/male_casualsuit02.obj'),'nativeSourceSHA256':hashlib.sha256((run/'source/male_casualsuit02.obj').read_bytes()).hexdigest(),'vertices':len(P),'quads':len(faces),'nativeMacroHiddenCorrespondenceOnly':macro,'mapping':mapping,'maximumDiscardedSkinProbability':maxDiscarded,'boundToFreshRig':False,'fitFields':str(field),'fitFieldsSHA256':hashlib.sha256(field.read_bytes()).hexdigest(),'master':str(master),'frozenFitGeometryAndTop4WeightsExact':instrument,'limits':['Hidden newly instantiated anatomical base supplies native clothing skin correspondence only; no visible body/head/rider assets inherited.','Fresh source landmark affine length fit; sourceH21shape/silhouette projection and protected hood/glove/shoe stitches remain pending.','No texture bake, new complete GLB, physics motion, rig contract or appearance pass.','No nativePreserveVolume/DQ reliance;19scalar skin roles retained for actual LBS later.']}
(out/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'vertices':len(P),'quads':len(faces),'maximumDiscardedSkinProbability':maxDiscarded,'fieldSHA256':report['fitFieldsSHA256']}))
