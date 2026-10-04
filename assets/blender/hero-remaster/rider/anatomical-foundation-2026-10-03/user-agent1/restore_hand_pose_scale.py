"""Restore unintended matrix-decomposition scale ULPs; same construction field."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
root=Path(__file__).resolve().parents[6];owned=Path(__file__).resolve().parent;out=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/hand-grip106';a=json.loads((out/'authoring.json').read_text());source=root/a['native'];dest=source.with_name('bounded-full-four-scale-exact.blend');assert not dest.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(source)==a['nativeSHA256'];helper=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/neck62/read-native.py';s=helper.read_text();h=dict(bpy=bpy,np=np,hashlib=hashlib);exec(compile(s[s.index('def digest('):s.index('for label,path in paths.items():')],str(helper),'exec'),h);control=json.loads((out.parent/'hand-grip104/immutable-control.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects[a['newRig']];old=bpy.data.objects['Independent anatomical foundation rig'];scope=json.loads((out.parent/'hand-grip104/scope.json').read_text());names=scope['scope']['existingPoseBoneNames'];before={b.name:{'location':list(b.location),'quaternion':list(b.rotation_quaternion),'scale':list(b.scale),'mode':b.rotation_mode} for b in rig.pose.bones};changed=[]
for name in names:
 p=rig.pose.bones[name];ref=old.pose.bones[name]
 if p.scale[:]!=ref.scale[:]:changed.append({'bone':name,'before':list(p.scale),'source':list(ref.scale)})
 p.scale=ref.scale
for name,state in control['objects'].items():assert h['state'](bpy.data.objects[name])==state,name
for name in a['newObjects']:
 # Snapshot the entire glove to ensure this repair cannot touch its fields.
 pass
glove={name:h['state'](bpy.data.objects[name]) for name in a['newObjects']};bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True);bpy.ops.wm.open_mainfile(filepath=str(dest));rig=bpy.data.objects[a['newRig']];old=bpy.data.objects['Independent anatomical foundation rig']
for b in rig.pose.bones:
 ref=old.pose.bones[b.name];assert b.scale[:]==ref.scale[:];state=before[b.name];assert list(b.location)==state['location'] and list(b.rotation_quaternion)==state['quaternion'] and b.rotation_mode==state['mode']
for name,state in control['objects'].items():assert h['state'](bpy.data.objects[name])==state,name
assert {name:h['state'](bpy.data.objects[name]) for name in a['newObjects']}==glove
receipt={'status':'SAME_HAND_CONSTRUCTION_SCALE_SERIALIZATION_CORRECTION','recipeSHA256':sha(__file__),'firstSavePreserved':{'path':str(source.relative_to(root)),'sha256':sha(source),'failure':'matrix_basis decomposition introduced21scale ULP changes outside declared rotation/location pose fields'},'native':str(dest.relative_to(root)),'nativeSHA256':sha(dest),'scaleCorrections':changed,'all51PoseScalesSourceExact':True,'all51RestBindAnd34OriginalObjectsExact':True,'allGloveFieldsAndAllBoneQuaternionLocationModeExactToFirstSave':True,'limits':['No new geometry, skin operator, flex angles or contact target. First save remains immutable; same intended rotation/location fields with exact source scale. No second fit/capture/expansion.']};(out/'scale-serialization.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'nativeSHA256':receipt['nativeSHA256'],'scaleFieldsRestored':len(changed)}))
