"""Generate a new CC0 adult base using installed MPFB; never imports rider meshes."""
import bpy,sys,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
addon=Path.home()/'Library/Application Support/Blender/5.1/extensions/user_default'
bpy.ops.wm.read_factory_settings(use_empty=True)
repo=bpy.context.preferences.extensions.repos.new(name='Restart MPFB read-only',module='restart_mpfb',custom_directory=str(addon))
import addon_utils
addon_utils.enable('bl_ext.restart_mpfb.mpfb',default_set=True,persistent=False)
from bl_ext.restart_mpfb.mpfb.services.humanservice import HumanService
from bl_ext.restart_mpfb.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict()
macro.update(gender=1.0,age=.40,muscle=.68,weight=.58,proportions=.65,height=.52)
macro['race']={'asian':.25,'caucasian':.35,'african':.4}
base=HumanService.create_human(mask_helpers=True,feet_on_ground=True,scale=.1,macro_detail_dict=macro)
base.name='Fresh_adult_MakeHuman_base'
HumanService.add_builtin_rig(base,'default',import_weights=True)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
report={'status':'unaccepted fresh source base; not a complete rider','macro':macro,'vertices':len(base.data.vertices),'polygons':len(base.data.polygons),'materials':list(base.data.materials.keys()),'groups':list(base.vertex_groups.keys()),'bounds':[[min(v.co[i] for v in base.data.vertices),max(v.co[i] for v in base.data.vertices)] for i in range(3)],'bones':{b.name:[list(b.head_local),list(b.tail_local)] for b in arm.data.bones},'addonPath':str(addon/'mpfb'),'freshSourceSha256':hashlib.sha256((addon/'mpfb/data/3dobjs/base.obj').read_bytes()).hexdigest()}
(P/'fresh-base-probe.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'fresh-base.blend'),compress=True)
print(json.dumps({k:v for k,v in report.items() if k not in ('bones','groups')}))
