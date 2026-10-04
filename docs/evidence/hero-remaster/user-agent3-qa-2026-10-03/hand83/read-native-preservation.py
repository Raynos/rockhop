"""Immutable saved source/derivative fields; no posing/evaluation/save/render."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
out=Path(__file__).resolve().parent;qa=out.parent;root=Path.cwd();ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'hand82/preparation.json').read_text());scope=json.loads((ev/'hand-grip104/scope.json').read_text());control=json.loads((ev/'hand-grip104/immutable-control.json').read_text());n=np.load(ev/'hand-grip104/source-fields.npz');f=np.load(ev/'hand-grip106/candidate-fields.npz');names=n['boneNames'].tolist();allowed=[names.index(s) for s in scope['scope']['weightBoneNames']];outside=np.setdiff1d(np.arange(51),allowed);helper=(qa/'neck62/read-native.py').read_text();ns={'bpy':bpy,'np':np,'hashlib':hashlib};exec(compile(helper[helper.index('def digest('):helper.index('for label,path in paths.items():')],'immutable-field-reader','exec'),ns);state=ns['state'];flat=ns['flat'];arrays={}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
bpy.ops.wm.open_mainfile(filepath=str(root/scope['immutableControl']['path']));baseNames=list(bpy.data.objects.keys());base={s:state(bpy.data.objects[s]) for s in baseNames};assert base==control['objects'];assert ns['materials']()==control['materials'];materials=ns['materials']();images={im.name:{'packedSHA256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None,'size':list(im.size),'colour':im.colorspace_settings.name,'filepath':im.filepath} for im in bpy.data.images};rig=bpy.data.objects['Independent anatomical foundation rig'];baseRig=state(rig);glovebase=state(bpy.data.objects[scope['objects']['glove']['object']]);native=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/hand-grip01/bounded-full-four-scale-exact.blend';bpy.ops.wm.open_mainfile(filepath=str(native));checks={s:state(bpy.data.objects[s])==b for s,b in base.items()};assert all(checks.values());assert ns['materials']()==materials;assert images=={im.name:{'packedSHA256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None,'size':list(im.size),'colour':im.colorspace_settings.name,'filepath':im.filepath} for im in bpy.data.images};newrig=bpy.data.objects['Bounded actual-grip01 original51 rig, unaccepted'];actual=state(newrig);assert list(newrig.data.bones.keys())==names;rest=np.array([np.array(b.matrix_local) for b in newrig.data.bones]);assert np.array_equal(rest,n['rigRest']);assert np.array_equal(np.array(newrig.matrix_world),n['rigWorld']);bonechecks={}
for j,s in enumerate(names):
 a=baseRig['armature']['pose'][s];b=actual['armature']['pose'][s];assert a['properties']['scale']==b['properties']['scale'];assert baseRig['armature']['bones'][s]==actual['armature']['bones'][s];outsidePose=(j not in allowed);assert not outsidePose or a==b;bonechecks[s]={'restAndBindBoneDefinitionsExact':True,'poseScaleExact':True,'outsidePoseExact':True if outsidePose else None};assert list(newrig.pose.bones[s].constraints)==[] or a['constraints']==b['constraints']
arrays.update({'savedCandidateRigRest':rest,'savedCandidateRigWorld':np.array(newrig.matrix_world),'savedCandidatePoseMatrices':np.array([np.array(newrig.pose.bones[s].matrix) for s in names]),'savedCandidatePoseBasis':np.array([np.array(newrig.pose.bones[s].matrix_basis) for s in names])});parts=[]
for label in ['full','four']:
 o=bpy.data.objects['Bounded actual-grip01 glove '+label+', unaccepted'];s=state(o);m=o.data;m.calc_loop_triangles();P=flat(m.vertices,'co',3,np.float32);T=np.array([t.vertices[:] for t in m.loop_triangles],np.int32);weights=np.zeros((len(P),51),np.float32);aux=[]
 for v in m.vertices:
  for member in v.groups:
   gn=o.vertex_groups[member.group].name
   if gn in names:weights[v.index,names.index(gn)]=member.weight
   else:aux.append([v.index,gn,member.weight])
 assert np.array_equal(P,n['gloveXYZ']) and np.array_equal(T,n['gloveTriangles']) and np.array_equal(weights,f[label+'Weights']);assert np.array_equal(weights[:,outside],n['gloveWeights'][:,outside]);assert np.array_equal(np.array(o.matrix_world),n['gloveWorld']);assert o.parent==bpy.data.objects[scope['objects']['glove']['object']].parent;mods=s['modifiers'];oldmods=glovebase['modifiers'];assert len(mods)==len(oldmods)
 for a,b in zip(oldmods,mods):
  a=json.loads(json.dumps(a));b=json.loads(json.dumps(b));ap=a['properties'].pop('object',None);bp=b['properties'].pop('object',None);assert a==b;assert ap is None or bp==['Object',newrig.name,None]
 for field in ['positions','polygons','loops','edges','materials','smooth','materialIndices','groups','attributes','hasCustomNormals','cornerNormals','shapeKeys']:assert s['mesh'][field]==glovebase['mesh'][field],(label,field)
 oldaux=[]
 for v in bpy.data.objects[scope['objects']['glove']['object']].data.vertices:
  for mem in v.groups:
   gn=bpy.data.objects[scope['objects']['glove']['object']].vertex_groups[mem.group].name
   if gn not in names:oldaux.append([v.index,gn,mem.weight])
 assert aux==oldaux;arrays[label+'NativeWeights']=weights;parts.append({'field':label,'object':o.name,'positionsTopologyRawNormalsUVMaterialsAndGroupsExact':True,'outside19WeightColumnsAndAuxiliaryMembershipsExact':True,'nativeWeightsByteExactToCandidateFields':True,'onlyArmatureModifierObjectRetargetedToCopiedOriginal51Rig':True,'armatureModifiers':[a for a in mods if a['kind']=='ARMATURE'],'positiveInfluenceMaximum':int((weights>0).sum(1).max()),'auxiliaryMemberships':len(aux),'hiddenByDefault':o.hide_get() and o.hide_render})
# Read original full anatomy donor as an additional control, without changing it.
o=bpy.data.objects.get('Full native diagnostic body');fullBody=None
if o:
 weights=np.zeros((len(o.data.vertices),51),np.float32)
 for v in o.data.vertices:
  for member in v.groups:
   gn=o.vertex_groups[member.group].name
   if gn in names:weights[v.index,names.index(gn)]=member.weight
 arrays['originalFullBodyNativeWeights']=weights;fullBody={'object':o.name,'vertices':len(weights),'distalPositiveRows':{s:int((weights[:,j]>0).sum()) for j,s in enumerate(names) if '_03.' in s}}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
np.savez_compressed(out/'native-fields.npz',**arrays);r={'status':'READ_ONLY_FROZEN_HAND_NATIVE_PRESERVATION_VERIFIED','recipeSHA256':sha(__file__),'blender':bpy.app.version_string,'originalObjectChecks':checks,'allOriginalObjectsExact':True,'originalImagesMaterialGraphsExact':True,'rigBoneChecks':bonechecks,'parts':parts,'originalFullBodyControl':fullBody,'fieldsSHA256':sha(out/'native-fields.npz'),'pinsUnchangedAfter':True,'limits':['Immutable saved fields only; no pose assignment, new geometry/weight/normal, evaluation/render/capture/save or candidate.','Full/four native preservation and own51rest/bind do not establish anatomical segmentation, contact, parity, art or candidate-engine consumption.']};(out/'native-preservation.json').write_text(json.dumps(r,indent=2)+'\n');print('ORIGINAL_OBJECTS',len(checks),'NATIVE_FULL_FOUR_RIG_SCALE_AND_FIELDS_EXACT',flush=True)
