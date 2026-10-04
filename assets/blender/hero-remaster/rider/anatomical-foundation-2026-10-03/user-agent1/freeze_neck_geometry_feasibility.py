"""Freeze the one geometry result and read-only rest checks. No skin/render."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[6];owned=Path(__file__).resolve().parent
ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';out=ev/'neck-interface102'
source=owned/'neck-interface28/auxiliary-restored.blend';native=owned/'neck-interface29/geometry-only-feasibility.blend'
native.parent.mkdir(parents=True,exist_ok=True);assert not native.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
solve=json.loads((out/'geometry-solve.json').read_text());field=out/'geometry-fields.npz';assert sha(field)==solve['fieldsSHA256']
f=dict(np.load(field));w=np.load(out/'solve-witnesses.npz');mapping=w['physicalRawToNode'];NB=len(f['bodyRestXYZ']);NH=len(f['headRestXYZ'])
scope=json.loads((root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/body59/proposal.json').read_text())['preciseInitialAuthoringMargin']
helper_path=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/neck62/read-native.py';text=helper_path.read_text();helpers=dict(bpy=bpy,np=np,hashlib=hashlib)
exec(compile(text[text.index('def digest('):text.index('for label,path in paths.items():')],str(helper_path),'exec'),helpers)
def snapshot():
 return {'objects':{o.name:helpers['state'](o) for o in bpy.data.objects},'materials':helpers['materials'](),'images':{im.name:{'packed':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None,'colour':im.colorspace_settings.name,'size':list(im.size),'filepath':im.filepath} for im in bpy.data.images}}
def groups(o):return [(g.name,g.lock_weight) for g in o.vertex_groups]
def data_without_positions(o):
 d=helpers['state'](o);d['mesh'].pop('positions');d['mesh'].pop('cornerNormals');d['mesh']['attributes'].pop('position');return d
bpy.ops.wm.open_mainfile(filepath=str(source));before=snapshot();objects={};states={};definitions={};checks=[]
for part in ['body','head']:
 for label in ['full','four']:
  old=bpy.data.objects[('Bounded neck28 auxiliary-preserved body ' if part=='body' else 'Bounded neck27 triangulated head ')+label+', unaccepted'];states[(part,label)]=data_without_positions(old);definitions[(part,label)]=groups(old)
  oldp=np.array([v.co[:] for v in old.data.vertices],dtype=np.float32);new=old.copy();new.data=old.data.copy();new.name='Bounded neck29 geometry-only '+part+' '+label+', unaccepted';new.data.name='Unaccepted neck29 geometry-only '+part+' '+label;bpy.context.collection.objects.link(new)
  new.data.vertices.foreach_set('co',f[part+'RestXYZ'].ravel());new.data.update();new.hide_set(True);new.hide_render=True
  assert data_without_positions(new)==states[(part,label)] and groups(new)==definitions[(part,label)]
  original=9037 if part=='body' else 43707;allowed=scope['bodyExistingRenderedNativeVertices' if part=='body' else 'headInitialBoundaryLedNativeVertexIDs'];outside=np.setdiff1d(np.arange(original),allowed)
  assert np.array_equal(f[part+'RestXYZ'][outside],oldp[outside]);objects[(part,label)]=new.name
  checks.append({'part':part,'field':label,'outsideOriginalVertices':len(outside),'outsideStoredPositionsExact':True,'allRawAssignmentsAndGroupDefinitionsExact':True,'allNonPositionGenericAttributesAndUVPBRExact':True,'topologyAndSourceFaceCyclesExact':True,'normalPolicy':'No custom-normal attribute edits. Mesh normals derive from changed geometry; actual decoded corner differences are reported separately, not concealed.'})
current=snapshot()
for name,state in before['objects'].items():assert current['objects'][name]==state,name
assert current['materials']==before['materials'] and current['images']==before['images']
bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True);bpy.ops.wm.open_mainfile(filepath=str(native));after=snapshot()
for name,state in before['objects'].items():assert after['objects'][name]==state,name
assert after['materials']==before['materials'] and after['images']==before['images']
parts={};normal_deltas=[];current_fields=dict(f)
for part in ['body','head']:
 o=bpy.data.objects[objects[(part,'four')]];o.data.calc_loop_triangles();t=np.array([x.vertices[:] for x in o.data.loop_triangles],dtype=np.int32);p=np.array([v.co[:] for v in o.data.vertices],dtype=np.float32);assert np.array_equal(p,f[part+'RestXYZ'])
 for label in ['full','four']:
  obj=bpy.data.objects[objects[(part,label)]];assert data_without_positions(obj)==states[(part,label)] and groups(obj)==definitions[(part,label)]
 current_fields[part+'FixedReferenceTriangles']=f[part+'Triangles'];current_fields[part+'Triangles']=t
 source_poly=f[part+'CandidatePolygonToCheckpointPolygon'][np.array([x.polygon_index for x in o.data.loop_triangles])];current_fields[part+'TriangleSourcePolygonIDs']=source_poly
 original=9037 if part=='body' else 43707;allowed=np.r_[scope['bodyExistingRenderedNativeVertices' if part=='body' else 'headInitialBoundaryLedNativeVertexIDs'],np.arange(original,len(p))]
 local=np.flatnonzero(np.isin(t,allowed).any(axis=1));current_fields[part+'LocalTriangleIDs']=local
 q=p[t].astype(float);cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);area=np.linalg.norm(cross,axis=1)*.5
 world=np.column_stack([p,np.ones(len(p))])@np.array(o.matrix_world).T
 parts[part]={'p':world[:,:3],'t':t,'local':set(local.tolist()),'physical':mapping[:NB] if part=='body' else mapping[NB:],'sourcePolygons':source_poly,'area':area}
 old=bpy.data.objects[('Bounded neck28 auxiliary-preserved body ' if part=='body' else 'Bounded neck27 triangulated head ')+'four, unaccepted'];old_norm=np.array([x.vector[:] for x in old.data.corner_normals]);new_norm=np.array([x.vector[:] for x in o.data.corner_normals]);loops=np.array([x.vertex_index for x in o.data.loops]);protected=~np.isin(loops,allowed);delta=np.linalg.norm(new_norm-old_norm,axis=1)
 normal_deltas.append({'part':part,'allRawCustomNormalFieldsExact':True,'decodedCornerChangedTotal':int((delta>0).sum()),'decodedProtectedCornerChanged':int(((delta>0)&protected).sum()),'maximumDecodedProtectedCornerDelta':float(delta[protected].max()) if protected.any() else 0.})

def topology(triangles):
 e=np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]);u,inv,count=np.unique(np.sort(e,axis=1),axis=0,return_inverse=True,return_counts=True)
 signs=np.where(e[:,0]<e[:,1],1,-1);balance=np.zeros(len(u),dtype=int);np.add.at(balance,inv,signs)
 return {'triangles':len(triangles),'unmatchedEdges':int((count==1).sum()),'nonmanifoldEdges':int((count>2).sum()),'twoIncidenceNonOpposed':int(((count==2)&(balance!=0)).sum()),'nonmanifoldWitnesses':u[count>2].tolist()}
all_tri=np.vstack([parts[k]['physical'][parts[k]['t']] for k in ['body','head']]);top=topology(all_tri)
# Explicit physical perimeter and separate inward closure (no new join registry).
seam=np.unique(mapping[:NB][f['bodySeamPhysicalIDs']>=0]);seam_edges={tuple(sorted((int(mapping[:NB][np.flatnonzero(f['bodySeamPhysicalIDs']==i)[0]]),int(mapping[:NB][np.flatnonzero(f['bodySeamPhysicalIDs']==((i+1)%238))[0]])))) for i in range(238)}
e=np.concatenate([all_tri[:,[0,1]],all_tri[:,[1,2]],all_tri[:,[2,0]]]);u,inv,count=np.unique(np.sort(e,axis=1),axis=0,return_inverse=True,return_counts=True);lookup={tuple(edge):i for i,edge in enumerate(u)}
seam_count=[int(count[lookup[edge]]) for edge in seam_edges];assert len(seam_edges)==238
inner_ids=set(mapping[NB:][f['headInnerClosurePhysicalIDs']>=0]);inner_edges=[i for i,(a,b) in enumerate(u) if a in inner_ids and b in inner_ids]
# All rest raw intersection pairs: local-versus-whole, exclude shared physical vertices only.
for key,d in parts.items():d['bvh']=BVHTree.FromPolygons(d['p'].tolist(),d['t'].tolist(),all_triangles=True,epsilon=0.)
def pair_rows(a,b,self_pair=False):
 A,B=parts[a],parts[b];pairs=[]
 for i,j in A['bvh'].overlap(B['bvh']):
  if self_pair:
   if i>=j or (i not in A['local'] and j not in A['local']):continue
  elif i not in A['local'] and j not in B['local']:continue
  if np.intersect1d(A['physical'][A['t'][i]],B['physical'][B['t'][j]]).size:continue
  pairs.append([int(i),int(j)])
 return {'pairs':len(pairs),'trianglePairs':pairs,'sourcePolygonPairs':[[int(A['sourcePolygons'][i]),int(B['sourcePolygons'][j])] for i,j in pairs]}
contacts={'bodySelf':pair_rows('body','body',True),'headSelf':pair_rows('head','head',True),'bodyHead':pair_rows('body','head')}
# Garment target retained separately; source490 is not a waiver.
garment=bpy.data.objects['Actual donor explicit native-four skin, unaccepted'];garment.data.calc_loop_triangles();gp=np.array([v.co[:] for v in garment.data.vertices]);gt=np.array([t.vertices[:] for t in garment.data.loop_triangles]);gp=(np.column_stack([gp,np.ones(len(gp))])@np.array(garment.matrix_world).T)[:,:3];gbvh=BVHTree.FromPolygons(gp.tolist(),gt.tolist(),all_triangles=True,epsilon=0.)
garment_counts={k:len(gbvh.overlap(d['bvh'])) for k,d in parts.items()}
oldhead=bpy.data.objects['Protected textured head above hidden neck interface'];oldhead.data.calc_loop_triangles();op=np.array([v.co[:] for v in oldhead.data.vertices]);op=(np.column_stack([op,np.ones(len(op))])@np.array(oldhead.matrix_world).T)[:,:3];ot=np.array([t.vertices[:] for t in oldhead.data.loop_triangles]);original_head_count=len(gbvh.overlap(BVHTree.FromPolygons(op.tolist(),ot.tolist(),all_triangles=True,epsilon=0.)))
np.savez_compressed(native.parent/'geometry-only-fields.npz',**current_fields)
areas=[{'part':k,'localTrianglesIncludingOneCorner':len(d['local']),'minimumLocalAreaM2':float(d['area'][list(d['local'])].min()),'localAtOrBelow1e_14':int((d['area'][list(d['local'])]<=1e-14).sum())} for k,d in parts.items()]
passes=not top['nonmanifoldEdges'] and not top['twoIncidenceNonOpposed'] and all(x==2 for x in seam_count) and all(count[i]==2 for i in inner_edges) and not any(r['localAtOrBelow1e_14'] for r in areas) and not any(d['pairs'] for d in contacts.values())
report={'status':'UNACCEPTED_REST_STRUCTURE_PASS_ROOT_VISUAL_PENDING' if passes else 'FAILED_GEOMETRY_ONLY_REST_CONTACT_OR_TOPOLOGY_CHECKPOINT','native':str(native.relative_to(root)),'nativeSHA256':sha(native),'fields':str((native.parent/'geometry-only-fields.npz').relative_to(root)),'fieldsSHA256':sha(native.parent/'geometry-only-fields.npz'),'recipeSHA256':sha(__file__),'geometrySolveSHA256':sha(out/'geometry-solve.json'),'sourceNativeSHA256':sha(source),'oldObjectsExactAfterSaveReopen':len(before['objects']),'original51RestBindSavedPoseExact':True,'packedImagesExact':len(before['images']),'materialGraphsExact':len(before['materials']),'newObjects':[objects[key] for key in objects],'protectionChecks':checks,'normalDerivedDifferences':normal_deltas,'currentRestTopology':top,'outer238Incidence2':all(x==2 for x in seam_count),'innerClosureEdges':len(inner_edges),'innerEdgesIncidence2':all(count[i]==2 for i in inner_edges),'localAreas':areas,'restContacts':contacts,'garmentRestPairs':garment_counts,'originalProtectedHeadGarmentRestPairs':original_head_count,'limits':['Geometry only; all sourcefull/four weights/auxiliary definitions/memberships exact. No skin solve or pose/controller/capture/export/install/GPU/model/worker/promotion.','Raw BVH pairs are not signed depth/visible-hole scores; root sole played judge. Reference-normal sign changes are not automatically winding reversal.','Actual derived corner normals can change with geometry although raw custom attributes remain exact; differences are explicit, never camouflage or a normal acceptance.','No motion qualification; original99collision/compression/actual47identity and source26garment490contacts remain red; all M0-M5 open.']}
(out/'rest-candidate.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','nativeSHA256','oldObjectsExactAfterSaveReopen','currentRestTopology','localAreas','garmentRestPairs','normalDerivedDifferences']},indent=2));print('REST_CONTACT_COUNTS',{k:v['pairs'] for k,v in contacts.items()},flush=True)
