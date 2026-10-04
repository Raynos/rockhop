"""Read-only auxiliary/group parity check at exactly three frozen witnesses."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix
out=Path(__file__).resolve().parent;root=out.parents[4];qa=out.parent;asset=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1';ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck64/preparation.json').read_text())
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
# Reuse this owner's pinned, already independently validated RNA reader only.
helper=qa/'neck62/read-native.py';text=helper.read_text();reader=dict(bpy=bpy,np=np,hashlib=hashlib);exec(compile(text[text.index('def digest('):text.index('for label,path in paths.items():')],str(helper),'exec'),reader)
state,flat,materials=reader['state'],reader['flat'],reader['materials'];digest=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest();json_digest=lambda d:hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest();archive=json.loads((qa/'neck62/native-read.json').read_text());f=dict(np.load(asset/'neck-interface27/triangulated-neck-fields.npz'));arrays={}
def definitions(obj):return [{'name':g.name,'lockWeight':bool(g.lock_weight)} for g in obj.vertex_groups]
def memberships(obj,bones,is_bone):return sorted([[v.index,obj.vertex_groups[g.group].name,float(g.weight)] for v in obj.data.vertices for g in v.groups if (obj.vertex_groups[g.group].name in bones)==is_bone],key=lambda x:(x[0],x[1]))
def non_group_state(obj):
 d=state(obj);d['mesh'].pop('groups');d['mesh'].pop('weights');return d
def snapshot():
 return {'objects':{o.name:state(o) for o in bpy.data.objects},'definitions':{o.name:definitions(o) for o in bpy.data.objects if o.type=='MESH'},'materials':materials(),'images':{im.name:{'packed':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None,'size':list(im.size),'colour':im.colorspace_settings.name,'filepath':im.filepath} for im in bpy.data.images}}
# Fresh source read supplies lock flags absent from the historical QA snapshot.
bpy.ops.wm.open_mainfile(filepath=str(asset/'selected-hoodie26/native-four-with-full-control.blend'))
bones=list(bpy.data.objects['Independent anatomical foundation rig'].data.bones.keys());assert len(bones)==51
source=bpy.data.objects['Canonical body with hidden head interface'];source_defs=definitions(source);source_aux=memberships(source,set(bones),False);assert len(source_defs)==204 and len([x for x in source_defs if x['name'] not in bones])==153
assert [x['name'] for x in source_defs]==archive['snapshots']['baseline']['objects'][source.name]['mesh']['groups']
assert source_aux==sorted(archive['snapshots']['baseline']['domains']['body_source']['nonBoneAssignments'],key=lambda x:(x[0],x[1]));assert len(source_aux)==21782
scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin'];outside=set(range(9037))-set(scope['bodyExistingRenderedNativeVertices']);outside_aux=[x for x in source_aux if x[0] in outside and x[2]>0];assert len(outside)==8877 and len(outside_aux)==21424
print('SOURCE_DEFINITIONS_MEMBERSHIPS_EXACT',len(source_defs),len(source_aux),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(asset/'neck-interface27/bounded-neck-join-triangulated.blend'))
old_snapshot=snapshot();assert old_snapshot['objects']==archive['snapshots']['candidate']['objects'];assert old_snapshot['images']==archive['snapshots']['candidate']['images'];assert old_snapshot['materials']==archive['snapshots']['candidate']['materials']
old_body={};old_skin={}
for label in ['full','four']:
 obj=bpy.data.objects['Bounded neck27 triangulated body '+label+', unaccepted'];old_body[label]=non_group_state(obj);old_skin[label]=memberships(obj,set(bones),True)
bpy.ops.wm.open_mainfile(filepath=str(asset/'neck-interface28/auxiliary-restored.blend'))
after=snapshot();assert len(after['objects'])==44
for name,d in old_snapshot['objects'].items():assert after['objects'][name]==d,name
for name,d in old_snapshot['definitions'].items():assert after['definitions'][name]==d,name
assert after['images']==old_snapshot['images'] and after['materials']==old_snapshot['materials'];rig=bpy.data.objects['Independent anatomical foundation rig'];assert list(rig.data.bones.keys())==bones
rows=[]
for label in ['full','four']:
 name='Bounded neck28 auxiliary-preserved body '+label+', unaccepted';obj=bpy.data.objects[name];assert definitions(obj)==source_defs;aux=memberships(obj,set(bones),False);skin=memberships(obj,set(bones),True);assert aux==source_aux;assert skin==old_skin[label];assert not any(v>=9037 for v,gn,w in aux);assert non_group_state(obj)==old_body[label]
 mesh=obj.data;mesh.calc_loop_triangles();positions=flat(mesh.vertices,'co',3,np.float32);triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],dtype=np.int32);weights=np.zeros((9219,51),dtype=np.float32)
 for v,gn,w in skin:weights[v,bones.index(gn)]=w
 assert positions.shape==(9219,3) and np.array_equal(positions,f['bodyRestXYZ']);assert np.array_equal(triangles,f['bodyTriangles']);assert np.array_equal(weights,f['body'+label.title()+'Weights']);slots=(weights>0).sum(1);assert label!='four' or slots.max()<=4
 definition_index={x['name']:i for i,x in enumerate(source_defs)};arrays[label+'AuxiliaryMembershipRows']=np.array([[v,definition_index[gn],w] for v,gn,w in aux],dtype=np.float64);arrays[label+'SemanticWeights']=weights
 rows.append({'field':label,'object':name,'definitions204OrderNameAndLockExact':True,'auxiliaryDefinitions':153,'auxiliaryOriginalAssignmentsExact':len(aux),'auxiliaryZeroMembershipCount':sum(w==0 for v,gn,w in aux),'outsidePositiveAuxiliaryAssignmentsExact':len(outside_aux),'outsideOriginalVertices':len(outside),'all9037OriginalMembershipsExact':True,'new182VertexAuxiliaryMemberships':0,'all9219SemanticBoneMembershipsAndWeightsExact':True,'nonGroupGeometryTopologyRawAttributesUVMaterialNormalsObjectBindingExact':True,'rawNonGroupStateSHA256':json_digest(old_body[label]),'storedPositionsSHA256':digest(positions),'semanticWeightsSHA256':digest(weights),'maximumBonePositiveSlots':int(slots.max()),'hiddenByDefault':obj.hide_get() and obj.hide_render})
print('RESTORED_GROUPS_AND_STORED_FIELDS_EXACT',flush=True)
# Only the three admitted existing witnesses. No new stream/controller/capture.
poses=np.load(ev/'neck-interface99/pose-witnesses.npz');domains=poses['domains'];source_indices=poses['sourceIndices'];all_matrices=poses['rigLocalSkinMatrices'];assert poses['boneNames'].tolist()==bones
rest=np.array([rig.data.bones[name].matrix_local for name in bones],dtype=np.float64);order=sorted(bones,key=lambda name:len(rig.data.bones[name].parent_recursive));lookup={name:i for i,name in enumerate(bones)};checks=[]
objects=[rig]+[bpy.data.objects[prefix+label+', unaccepted'] for label in ['full','four'] for prefix in ['Bounded neck27 triangulated body ','Bounded neck28 auxiliary-preserved body ']]
for obj in objects:obj.hide_set(False)
for domain,index in [('native',0),('native',72),('actual47',668)]:
 ids=np.flatnonzero((domains==domain)&(source_indices==index));assert len(ids)==1;skin_matrix=all_matrices[int(ids[0])];desired=skin_matrix.astype(np.float64)@rest
 for name in order:
  bone=rig.data.bones[name];parent=bone.parent;kwargs={} if parent is None else {'parent_matrix':Matrix(desired[lookup[parent.name]].tolist()),'parent_matrix_local':parent.matrix_local}
  rig.pose.bones[name].matrix_basis=bone.convert_local_to_pose(Matrix(desired[lookup[name]].tolist()),bone.matrix_local,invert=True,**kwargs)
 bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get()
 for label in ['full','four']:
  paired=[]
  for kind,prefix in [('control','Bounded neck27 triangulated body '),('restored','Bounded neck28 auxiliary-preserved body ')]:
   evaluated=bpy.data.objects[prefix+label+', unaccepted'].evaluated_get(depsgraph);mesh=evaluated.to_mesh()
   try:xyz=flat(mesh.vertices,'co',3,np.float32)
   finally:evaluated.to_mesh_clear()
   assert xyz.shape==(9219,3);paired.append(xyz);arrays[domain+str(index)+'_'+label+'_'+kind+'ObjectLocalXYZ']=xyz
  assert paired[0].tobytes()==paired[1].tobytes()
  checks.append({'domain':domain,'sourceIndex':index,'field':label,'vertices':9219,'matrixArchiveRow':int(ids[0]),'rigLocalMatrixFloat32SHA256':digest(skin_matrix),'evaluatedObjectLocalFloat32BytesExact':True,'maximumPositionDifferenceM':float(np.abs(paired[0].astype(float)-paired[1]).max()),'positionsSHA256':digest(paired[0])})
 print('FROZEN_PARITY',domain,index,'full+four9219exact',flush=True)
# Process exits without saving in-memory pose/visibility changes.
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
np.savez_compressed(out/'membership-and-parity.npz',**arrays)
report={'status':'UNACCEPTED_AUXILIARY_PRESERVATION_AND_THREE_WITNESS_PARITY_VERIFIED','candidateCheckpoint':'54f0ec748a560486cba3e634893bc46639a9a29d','preparationSHA256':sha(qa/'neck64/preparation.json'),'recipeSHA256':sha(__file__),'pinnedReaderSHA256':sha(helper),'blenderVersion':bpy.app.version_string,'all14InputPinsUnchanged':True,'controls':{'originalAndFailed42ObjectSnapshotsExact':True,'originalAndFailedVertexGroupDefinitionsAndLocksExact':True,'original51StoredRestBindSavedPoseExact':True,'original17PackedImagesExact':True,'original18MaterialGraphsExact':True,'oldObjectStateSHA256':{name:json_digest(d) for name,d in old_snapshot['objects'].items()}},'original204GroupDefinitions':source_defs,'bodyChecks':rows,'evaluatedParity':checks,'membershipAndParityNPZ_SHA256':sha(out/'membership-and-parity.npz'),'rootArtVerdict':'REJECT neck27 moving appearance; shelf/folded throat/rear overhang unchanged. Auxiliary correction is preservation-only.','limits':['Only auxiliary correction and same-field parity measured. Original9037auxiliary memberships restored;182derived vertices have no fabricated source auxiliary membership. Bone semantics by name, raw auxiliary slot counts do not define the four-influence skin contract.','Exactly three archived reconstructed poses/six full-four pair comparisons. Not all1232pose parity, exact game trace, dynamic contact/shape/identity or art qualification. Frozen99contact/area-compression/actual47identity failures remain red.','No new capture/controller/native save/export/source edit, anatomical proposal, package/model/GPU job, worker, upload or promotion. File hashes remain unchanged despite in-memory existing-pose evaluation.','Configurable snapshot scope inherits pinned independent reader limits: unenumerated RNA collections, animation F-curves/NLA and external linked content not certified.','Parent owns ask275/index reconciliation and art/admission. Agent1 owns bounded anatomical proposal. Original490garment/head contacts not waived, source26 repair separate; all M0-M5/engine/device/player gates open.']}
(out/'assessment.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'controls':{k:v for k,v in report['controls'].items() if k!='oldObjectStateSHA256'},'bodyChecks':rows,'evaluatedParity':checks},indent=2))
