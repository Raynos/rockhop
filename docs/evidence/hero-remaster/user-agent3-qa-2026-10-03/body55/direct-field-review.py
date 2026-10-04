"""Replay frozen surface fields into disposable presentation meshes, CPU only."""
import argparse,gzip,hashlib,json,math,sys,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True);ap.add_argument('--prepare-only',action='store_true');ap.add_argument('--pilot',action='store_true');ap.add_argument('--domain',choices=['native','actual47'],default='native');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);root=Path.cwd();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True);qa=Path(__file__).resolve().parent.parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();freeze=json.loads((qa/'body52/source.json').read_text());native=qa/'body52/native-fields.npz';export=qa/'body52/export-fields.npz';n=np.load(native);e=np.load(export);base=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/diagnostic02';driver_path=base/'driver.json';driver=json.loads(driver_path.read_text());actual_path=qa/'garment47/first.weights.ndjson.gz';master=root/next(k for k in freeze['pins'] if k.endswith('selected-hoodie19/profile-fit.blend'))
for p,record in freeze['pins'].items():assert sha(root/p)==record['sha256'],p
pins={str(p.relative_to(root)):sha(p) for p in [master,native,export,driver_path,qa/'body53/assessment.json',qa/'body53/local-witnesses.json',actual_path,*[base/(label+'-native-'+domain+'.f64') for label in ['body','boxers'] for domain in ['full','four']]]}
for label in ['body','boxers']:
 for domain in ['full','four']:
  name=label+'-native-'+domain+'.f64';assert sha(base/name)==driver['pins'][name]['sha256'] and (base/name).stat().st_size==driver['pins'][name]['bytes']
normal=lambda name:name.replace('.','').replace('_','');names=n['boneNames'].tolist();order=[list(map(normal,names)).index(normal(s)) for s in e['jointNames']];C=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1.]]);R=C.T;body_ids=n['renderedBodySourceIDs'].astype(int);body_stream={d:np.memmap(base/f'body-native-{d}.f64',dtype='<f8',mode='r',shape=(529,13380,3)) for d in ['full','four']};boxer_stream={d:np.memmap(base/f'boxers-native-{d}.f64',dtype='<f8',mode='r',shape=(529,467,3)) for d in ['full','four']}
with gzip.open(actual_path,'rt') as f:actual=[json.loads(line) for line in f]
assert len(actual)==703
rest={};weights={}
for label in ['canonicalFour','originalFull','boxers','protectedHead','cheek']:
 xyz=n[label+'XYZ'];rest[label]=(np.column_stack([xyz,np.ones(len(xyz))])@(C@n[label+'World']).T);w=n[label+'Weights'][:,order].copy();w/=w.sum(1)[:,None];weights[label]=w
assessment=json.loads((qa/'body53/assessment.json').read_text());body_rows={(x['domain'],x['frame']):x for x in assessment['records']};local=json.loads((qa/'body53/local-witnesses.json').read_text())['witnesses']
def skin(label,K):return np.einsum('vj,jab,vb->va',weights[label],K,rest[label],optimize=True)[:,:3]
def field(domain,index,weight):
 if domain=='native':
  W=np.array([np.array(driver['frames'][index]['jointWorldColumnMajor'][names[j]]).reshape(4,4).T for j in order]);K=W@e['inverseBinds'];body=body_stream[weight][index];boxers=boxer_stream[weight][index]
 else:
  K=np.array(actual[index-1]['matrices']).reshape(51,4,4).transpose(0,2,1);W=K@np.linalg.inv(e['inverseBinds']);body=skin('originalFull' if weight=='full' else 'canonicalFour',K);boxers=skin('boxers',K)
 return {'body':body[body_ids],'head':skin('protectedHead',K),'cheek':skin('cheek',K),'boxers':boxers},W,body
# Exact matching witnesses and source index/timing remain separate from film time.
def sequence(domain):
 if domain=='native':
  rows=[{'sourceIndex':i,'sourceTimeS':driver['frames'][i]['timeS'],'kind':'moving','durationS':1/12} for i in range(0,529,4)]
  rows.extend({'sourceIndex':i,'sourceTimeS':driver['frames'][i]['timeS'],'kind':'paused exact witness','durationS':3} for i in [72,242])
 else:
  rows=[{'sourceIndex':min(i,703),'sourceTimeS':min(i,703)/120,'kind':'moving','durationS':1/30} for i in range(4,708,4)]
  rows.extend({'sourceIndex':i,'sourceTimeS':i/120,'kind':'paused exact witness','durationS':3} for i in [512,514,668,669])
 return rows
# Every native body field is used byte-for-byte from its existing stream. Prove
# boxer control and actual53 selected witnesses independently before rendering.
boxer_parity=0.
for i in range(529):
 W=np.array([np.array(driver['frames'][i]['jointWorldColumnMajor'][names[j]]).reshape(4,4).T for j in order]);K=W@e['inverseBinds'];boxer_parity=max(boxer_parity,float(np.linalg.norm(skin('boxers',K)-boxer_stream['four'][i],axis=1).max()))
assert boxer_parity<2e-6
witness_parity=0.
for witness in local:
 domain='native' if witness['domain']=='syntheticFour' else 'actual47';_,_,body=field(domain,witness['frameOrInputTick'],'four')
 for key in ['A','B']:
  gap=float(np.abs(body[witness['nativeIDs'+key]]-witness['XYZ_'+key]).max());witness_parity=max(witness_parity,gap);assert gap==0,(domain,witness['region'],gap)
# Read original frozen source only. No source object, pose, modifiers, materials,
# UV or custom normals are edited; the new Scene links presentation copies only.
bpy.ops.wm.open_mainfile(filepath=str(master),use_scripts=False)
labels={'body':'Canonical body with hidden head interface','head':'Protected textured head above hidden neck interface','cheek':'Protected coherent cheek patch','boxers':'Opaque boxer fitting garment'}
originals={key:bpy.data.objects[name] for key,name in labels.items()};rig=bpy.data.objects['Independent anatomical foundation rig'];protected_sources={**originals,'canonicalFour':bpy.data.objects['Canonical anatomical body, baked adult hm08'],'originalFull':bpy.data.objects['Full native diagnostic body']}
def source_state():
 record={}
 for key,obj in protected_sources.items():
  mesh=obj.data;xyz=np.array([v.co[:] for v in mesh.vertices],dtype='<f4');live_weights=np.zeros((len(mesh.vertices),51));
  for vertex in mesh.vertices:
   for membership in vertex.groups:
    name=obj.vertex_groups[membership.group].name
    if name in names:live_weights[vertex.index,names.index(name)]=membership.weight
  assert np.array_equal(live_weights,n[{'body':'renderedBody','head':'protectedHead','cheek':'cheek','boxers':'boxers','canonicalFour':'canonicalFour','originalFull':'originalFull'}[key]+'Weights'])
  uv={u.name:sha_array(np.array([v.uv[:] for v in u.data],dtype='<f4')) for u in mesh.uv_layers};record[key]={'XYZ':sha_array(xyz),'polygons':sha_array(np.array([v for p in mesh.polygons for v in p.vertices],dtype='<i4')),'weights':sha_array(live_weights),'UV':uv,'smooth':sha_array(np.array([p.use_smooth for p in mesh.polygons],dtype='u1')),'materials':[m.name if m else None for m in mesh.materials],'modifiers':[(m.name,m.type,m.show_render,m.show_viewport) for m in obj.modifiers],'matrixWorld':np.array(obj.matrix_world).tolist(),'customNormals':mesh.has_custom_normals,'hideRender':obj.hide_render}
 record['rig']={'rest':[np.array(b.matrix_local).tolist() for b in rig.data.bones],'pose':[np.array(b.matrix_basis).tolist() for b in rig.pose.bones],'weightsUntouched':'Original objects are never used as render surfaces; no group writes.'};return record
def sha_array(array):return hashlib.sha256(array.tobytes()).hexdigest()
before=source_state();assert len(rig.data.bones)==51
# Fixed camera bounds use every rendered sample / both fields / protected head.
# This is a framing check on existing poses, not a new controller or pose sweep.
bounds=[];saved_witnesses=json.loads(gzip.decompress((qa/'body53/witnesses.json.gz').read_bytes()));witness_map={}
for witness in saved_witnesses:
 if 'nativeIDsA' in witness:witness_map.setdefault((witness['domain'],witness['frame']),[]).append(witness)
all_body_witness_residual=0.;matched_body_witnesses=0
for domain in ['native','actual47']:
 for index in sorted({x['sourceIndex'] for x in sequence(domain)}):
  for weight in ['full','four']:
   fields,W,body=field(domain,index,weight);relative=np.vstack([fields['body'],fields['head'],fields['boxers']])-W[0,:3,3];native_xyz=relative@R[:3,:3].T
   for yaw in [0,90,180]:
    angle=math.radians(yaw);rotation=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1.]]);points=native_xyz@rotation.T;bounds.append([points[:,1].min(),points[:,1].max(),points[:,2].min(),points[:,2].max()])
   key=('syntheticFull' if weight=='full' else 'syntheticFour',index) if domain=='native' else ('actual47Full' if weight=='full' else 'actual47Four',index)
   for witness in witness_map.get(key,[]):
    for part in ['A','B']:
     error=float(np.abs(body[witness['nativeIDs'+part]]-witness['XYZ_'+part]).max());all_body_witness_residual=max(all_body_witness_residual,error);assert error==0
    matched_body_witnesses+=1
bounds=np.array(bounds);max_horizontal=float(np.abs(bounds[:,:2]).max());zmin=float(bounds[:,2].min());zmax=float(bounds[:,3].max());cell_width=2*max_horizontal+.24;row_pitch=zmax-zmin+.24;lower_pelvis=-zmin+.16;upper_pelvis=lower_pelvis+row_pitch;display_height=2*(zmax-zmin)+.56;ortho_width=max(3*cell_width+.10,display_height*1.5);camera_center_z=display_height/2
framing={'allRenderedSamplesAndBothFields':True,'maxAbsHorizontalFromPelvisM':max_horizontal,'relativeZRangeM':[zmin,zmax],'columnPitchM':cell_width,'rowPitchM':row_pitch,'lowerPelvisZM':lower_pelvis,'upperPelvisZM':upper_pelvis,'allBody53SavedWitnessesAtRenderedSamples':matched_body_witnesses,'maximumFloat64XYZWitnessResidualM':all_body_witness_residual}
boxer_bsdf=[node for mat in originals['boxers'].data.materials if mat and mat.use_nodes for node in mat.node_tree.nodes if node.type=='BSDF_PRINCIPLED'];assert boxer_bsdf and all(node.inputs['Alpha'].default_value==1 and not node.inputs['Alpha'].is_linked for node in boxer_bsdf)

scene=bpy.data.scenes.new('Agent3 frozen-field CPU presentation only');bpy.context.window.scene=scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4;scene.cycles.use_denoising=True;scene.cycles.max_bounces=3;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=1920;scene.render.resolution_y=1280;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Frozen field neutral studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.075,.075,.075,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
target=Vector((.65,0,camera_center_z))
for name,position,power in [('Key',(4,-4,6),1100),('Fill',(-3,4,5),1000),('Top',(.65,0,7),800)]:
 light=bpy.data.lights.new('Field review '+name,'AREA');light.energy=power;light.size=5;obj=bpy.data.objects.new(light.name,light);scene.collection.objects.link(obj);obj.location=position;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Frozen field orthographic camera');cd.type='ORTHO';cd.ortho_scale=ortho_width;camera=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(camera);camera.location=(10,0,camera_center_z);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
copies=[];triangle_checks={};material_checks={}
for row,weight in enumerate(['full','four']):
 for column,yaw in enumerate([0,90,180]):
  rotation=np.array([[math.cos(math.radians(yaw)),-math.sin(math.radians(yaw)),0],[math.sin(math.radians(yaw)),math.cos(math.radians(yaw)),0],[0,0,1.]])
  transforms=[]
  for key,orig in originals.items():
   mesh=orig.data;mesh.calc_loop_triangles();tris=np.array([t.vertices[:] for t in mesh.loop_triangles],dtype='<i4');loops=np.array([t.loops[:] for t in mesh.loop_triangles],dtype=int).ravel();source_label={'body':'renderedBody','head':'protectedHead','cheek':'cheek','boxers':'boxers'}[key];assert np.array_equal(tris,n[source_label+'Triangles']);display=bpy.data.meshes.new(f'{weight} {yaw} direct {key}');display.from_pydata([v.co[:] for v in mesh.vertices],[],tris.tolist());display.update()
   for material in mesh.materials:display.materials.append(material)
   for p,t in zip(display.polygons,mesh.loop_triangles):p.material_index=mesh.polygons[t.polygon_index].material_index;p.use_smooth=mesh.polygons[t.polygon_index].use_smooth
   for source_uv in mesh.uv_layers:
    layer=display.uv_layers.new(name=source_uv.name);data=np.array([u.uv[:] for u in source_uv.data],dtype=np.float32)[loops];layer.data.foreach_set('uv',data.ravel());layer.active_render=source_uv.active_render;assert sha_array(np.array([u.uv[:] for u in layer.data],dtype='<f4'))==sha_array(data.astype('<f4'))
   obj=bpy.data.objects.new(f'{weight} {yaw} frozen {key}',display);scene.collection.objects.link(obj);transforms.append((key,obj));triangle_checks[key]=sha_array(tris);material_checks[key]={'sameOriginalMaterialObjects':all(a is b for a,b in zip(display.materials,mesh.materials)),'sourceUVLayers':[u.name for u in mesh.uv_layers],'sourceUseSmoothFlagsPreserved':True,'noNewCustomNormals':True}
  copies.append({'weight':weight,'row':row,'column':column,'yaw':yaw,'rotation':rotation,'objects':transforms,'offset':np.array([.65,(column-1)*cell_width,upper_pelvis if row==0 else lower_pelvis])})
bpy.context.view_layer.update()
settings={'resolution':[1920,1280],'engine':'CYCLES','device':'CPU','samples':4,'threads':2,'viewTransform':'AgX','cameraWorldRows':np.array(camera.matrix_world).tolist(),'orthoWidthM':ortho_width,'framingProof':framing,'views':['front +X','side +Y','rear -X'],'rowWeightDomains':['native/actual full','native/actual normalized-four'],'displayTransform':'Translate source pelvis world to fixed panel origin, convert glTF XYZ by C^T, then yaw0/90/180 around native Z. No scaling or undo of rider orientation. Full top, Four bottom.','panelPelvisOriginsNativeM':[x['offset'].tolist() for x in copies],'normalPolicy':'Presentation triangle meshes keep source UV/material/smooth flags, recompute geometric normals as vertices move; no source normal/geometry write or shader equivalence claim.','modesty':'Existing opaque467vertex/870triangle underwear control in both rows; no removal/transparency or genital detail. Proximal hip surface can remain covered.'}
prepared={'status':'ADMITTED_BOUNDED_EXPOSED_BODY_DIRECT_FIELD_PREPARATION','creationDate':'2026-10-04','sourceThread':'01a1054f-988a-710f-b72e-417ac96ba032','pins':pins,'recipeSHA256':sha(__file__),'all51OriginalRestAndPosePreserved':source_state()==before,'nativeBoxerFourVsExistingStreamMaximumResidualM':boxer_parity,'exactBody53SelectedWitnessXYZResidualM':witness_parity,'triangleHashes':triangle_checks,'presentationUVMaterialProof':material_checks,'settings':settings,'sequences':{d:sequence(d) for d in ['native','actual47']},'reuseAudit':[{'candidate':'diagnostic02/review/native-full-vs-four.mp4','decision':'Matching pose stream; dressed, conceals body shoulders/hips.'},{'candidate':'selected-hoodie24/body-fit89/body-fit-coverage-context.mp4','decision':'Protected wearer and opaque underwear, but rest orbit only; no body53 moving poses.'},{'candidate':'fitting01 A/T/neutral inputs','decision':'Still fitting references only, not played motion.'},{'candidate':'one-rider-v2 body-bind media / donor generations','decision':'Different frozen body/bind/pose provenance; not a matching body53 exposed-body control.'}],'limits':['Native and actual47 pose identities separated; no actual50 synchronization or new controller simulation.','Full fitting body13,380vertices quantification mapped to rendered9,037body subset; protected head/cheek unchanged source. Historical gray full-native head is not rendered.','Geometric-normal CPU display, not production engine/GPU/lighting/LOD/device fidelity. Parent alone judges art; all M0-M5 stay open.','No original source/body/head/51rig/weights/material/UV edit or source save/export/replacement/promotion/inference/installation/worker/publication.']}
assert source_state()==before and pins=={p:sha(root/p) for p in pins};(out/'preparation.json').write_text(json.dumps(prepared,indent=2)+'\n');print('DIRECT_FIELD_PREPARED',boxer_parity,witness_parity,flush=True)
if args.prepare_only:raise SystemExit(0)
frames=[];seq=sequence(args.domain);seq=seq[:1] if args.pilot else seq;started=time.monotonic();frames_dir=out/'frames';frames_dir.mkdir(exist_ok=True)
for number,item in enumerate(seq):
 index=item['sourceIndex'];fields={};worlds={};full_body={}
 for weight in ['full','four']:fields[weight],worlds[weight],full_body[weight]=field(args.domain,index,weight)
 frame={'number':number,**item,'sourceDomain':args.domain,'views':[],'sourceBodyWorldFloat64SHA256':{d:sha_array(full_body[d]) for d in ['full','four']},'body53':{d:body_rows[('syntheticFull' if d=='full' else 'syntheticFour',index) if args.domain=='native' else ('actual47Full' if d=='full' else 'actual47Four',index)] for d in ['full','four']}}
 for copy in copies:
  W=worlds[copy['weight']];pelvis=W[0,:3,3];transform=copy['rotation']@R[:3,:3];offset=copy['offset'];display_points={};float32_error=0.
  for key,obj in copy['objects']:
   points=(fields[copy['weight']][key]-pelvis)@transform.T+offset;obj.data.vertices.foreach_set('co',points.astype(np.float32).ravel());obj.data.update();display_points[key]=points;float32_error=max(float32_error,float(np.linalg.norm(points.astype(np.float32).astype(float)-points,axis=1).max()))
  view={'row':copy['row'],'column':copy['column'],'weight':copy['weight'],'yaw':copy['yaw'],'sourcePelvisWorldM':pelvis.tolist(),'displayFromSourceRotationRows':transform.tolist(),'displayTranslationM':(offset-transform@pelvis).tolist(),'focusCrops':{},'displayFloat32MaximumResidualM':float32_error}
  for region,bones in [('shoulders',['upperArm.L','upperArm.R']),('hips',['thigh.L','thigh.R'])]:
   joints=[list(map(normal,e['jointNames'])).index(normal(b)) for b in bones];anchor=W[joints,:3,3].mean(0);point=transform@(anchor-pelvis)+offset;project=world_to_camera_view(scene,camera,Vector(point));cx=float(project.x*1920);cy=float((1-project.y)*1280);width,height=(350,260) if region=='shoulders' else (300,260);left=int(round(cx-width/2));top=int(round(cy-height/2));assert 0<=left<1920-width and 0<=top<1280-height,(args.domain,index,region,left,top);view['focusCrops'][region]={'pixelXYWH':[left,top,width,height],'sourceAnchorWorldM':anchor.tolist(),'cameraProjectedPixelXY':[cx,cy]}
  points=np.vstack([display_points['body'],display_points['head'],display_points['boxers']]);cm=np.array(camera.matrix_world);camera_xyz=(points-cm[:3,3])@cm[:3,:3];xy=camera_xyz[:,:2]/[ortho_width,ortho_width*1280/1920]+.5;view['allVertexProjectedBounds']={'minXY':xy.min(0).tolist(),'maxXY':xy.max(0).tolist(),'vertices':len(points)};assert np.all(xy>0) and np.all(xy<1) and np.all(camera_xyz[:,2]<0)
  frame['views'].append(view)
 bpy.context.view_layer.update();scene.render.filepath=str(frames_dir/f'{number:04d}.png');bpy.ops.render.render(write_still=True);frame['PNG_SHA256']=sha(scene.render.filepath);frames.append(frame);(out/'render-progress.json').write_text(json.dumps({'status':'UNACCEPTED_RENDER_IN_PROGRESS','domain':args.domain,'completedFrames':len(frames),'targetFrames':len(seq),'elapsedS':time.monotonic()-started},indent=2)+'\n')
 if number%8==0:print('DIRECT_FIELD_FRAME',args.domain,number,'source',index,'seconds',round(time.monotonic()-started,1),flush=True)
 assert time.monotonic()-started<2700,'Own bounded CPU capture cap'
assert source_state()==before and pins=={p:sha(root/p) for p in pins};report={'status':'UNACCEPTED_DIRECT_EXISTING_BODY_FIELD_REVIEW_RENDERED','recipeSHA256':sha(__file__),'preparationSHA256':sha(out/'preparation.json'),'domain':args.domain,'pilot':args.pilot,'frames':frames,'originalSourceAnd51RigPreserved':True,'elapsedS':time.monotonic()-started,'limits':prepared['limits']};(out/'render.json').write_text(json.dumps(report,separators=(',',':'))+'\n');print('DIRECT_FIELD_RENDER_READY',args.domain,len(frames),report['elapsedS'],flush=True)
