"""Create NEW installed CC0 MPFB anatomical source; no rider imports."""
import bpy,sys,json,hashlib
from pathlib import Path
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/mpfb-trial2')
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2')
OUT.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True)
if (RUN/'fresh-anatomical-source.blend').exists():raise RuntimeError('Fresh source already frozen')
addon=Path.home()/'Library/Application Support/Blender/5.1/extensions/user_default'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.extensions.repos.new(name='Fresh anatomical hand source',module='fresh_hand_mpfb',custom_directory=str(addon))
import addon_utils
addon_utils.enable('bl_ext.fresh_hand_mpfb.mpfb',default_set=True,persistent=False)
from bl_ext.fresh_hand_mpfb.mpfb.services.humanservice import HumanService
from bl_ext.fresh_hand_mpfb.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict()
macro.update(gender=1.,age=.40,muscle=.50,weight=.50,proportions=.50,height=.50)
macro['race']={'asian':.25,'caucasian':.35,'african':.40}
base=HumanService.create_human(mask_helpers=True,feet_on_ground=True,scale=.1,macro_detail_dict=macro)
base.name='NEW anatomical hand source; no historical donor'
arm=HumanService.add_builtin_rig(base,'default',import_weights=True)
bpy.context.view_layer.update()
data={'status':'NEW unaccepted anatomical source, not rider asset','macro':macro,'baseOBJ':str(addon/'mpfb/data/3dobjs/base.obj'),'baseOBJSHA256':hashlib.sha256((addon/'mpfb/data/3dobjs/base.obj').read_bytes()).hexdigest(),
 'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(row) for row in b.matrix_local]} for b in arm.data.bones if 'finger' in b.name or 'metacarpal' in b.name or 'wrist' in b.name or 'lowerarm' in b.name},
 'meshVertices':len(base.data.vertices),'groups':list(base.vertex_groups.keys()),'blender':bpy.app.version_string}
(OUT/'fresh-source.json').write_text(json.dumps(data,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'fresh-anatomical-source.blend'))
print('FRESH_ANATOMICAL_SOURCE_FROZEN',flush=True)
