"""Read-only finite saddle surfaces in frozen actual gameplay. CPU only, no asset edits."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
os.environ.setdefault('OMP_NUM_THREADS', '2')
import hashlib, json, struct
from pathlib import Path
import numpy as np
REPO=Path('/Users/raynos/projects/games/rockhop')
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/saddle-surface165'
PRIVATE=ROOT/'saddle-surface165'
BODY34=ROOT/'rig-adapter01/body-bind34'
V5=ROOT/'garment-rebuild01/physical-v5-control157'
EVID=REPO/'docs/evidence/hero-remaster/one-rider-v2'
inputs={}
def sha(b): return hashlib.sha256(b).hexdigest()
def read(path):
 b=Path(path).read_bytes(); inputs[str(path)]={'sha256':sha(b),'bytes':len(b)}; return b

def js(path):return json.loads(read(path))
def canonical(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':')).encode())
def arr(folder,record,width=None):
 b=read(folder/record['file']);assert sha(b)==record['sha256'];a=np.frombuffer(b,dtype='<f8');assert a.size==record.get('values',record.get('bytes',len(b))//8);return a.reshape(-1,width)if width else a

def glb(path):
 b=read(path);assert b[:4]==b'glTF';n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);at=20+n;size,kind=struct.unpack_from('<II',b,at);assert kind==0x004e4942;binary=b[at+8:at+8+size]
 def accessor(i):
  a=j['accessors'][i];dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  if 'bufferView'in a:
   v=j['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width*dtype.itemsize)
   result=np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=offset,strides=(stride,dtype.itemsize)).copy()
  else:result=np.zeros((a['count'],width),dtype=dtype)
  if 'sparse'in a:
   sp=a['sparse'];idx=sp['indices'];val=sp['values'];iv=j['bufferViews'][idx['bufferView']];vv=j['bufferViews'][val['bufferView']];idt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4'}[idx['componentType']]);ids=np.frombuffer(binary,dtype=idt,count=sp['count'],offset=iv.get('byteOffset',0)+idx.get('byteOffset',0));vals=np.frombuffer(binary,dtype=dtype,count=sp['count']*width,offset=vv.get('byteOffset',0)+val.get('byteOffset',0)).reshape(-1,width);result[ids]=vals
  return result
 return j,accessor

def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def clip(poly,t):
 if cross(t[1]-t[0],t[2]-t[0])<0:t=t[[0,2,1]]
 for i in range(3):
  a,b=t[i],t[(i+1)%3];edge=b-a;res=[]
  if not len(poly):break
  for p,q in zip(poly,np.roll(poly,-1,axis=0)):
   dp,dq=cross(edge,p-a),cross(edge,q-a);pin,qin=dp>=-1e-10,dq>=-1e-10
   if pin:res.append(p)
   if pin!=qin and abs(dp-dq)>1e-14:res.append(p+(q-p)*dp/(dp-dq))
  poly=np.asarray(res,float).reshape(-1,2)
 return poly

def heights(q,xz):
 m=np.array([q[1,[0,2]]-q[0,[0,2]],q[2,[0,2]]-q[0,[0,2]]]).T
 if abs(np.linalg.det(m))<1e-12:return None
 uv=np.linalg.solve(m,(xz-q[0,[0,2]]).T).T;return q[0,1]+uv[:,0]*(q[1,1]-q[0,1])+uv[:,1]*(q[2,1]-q[0,1])

def roi(p,t):
 q=p[t];return np.flatnonzero(((q[:,:,1]>.69)&(q[:,:,1]<1.08)&(abs(q[:,:,2])<.245)).all(1))

def evaluate(pos,t,ids,seat,seatids):
 h=pos[t[ids]];proj=h[:,:,[0,2]];lo=proj.min(1);hi=proj.max(1);best=np.inf;wit=None;crosswit=None;pairs=0;negative=0;crossing=0;near=0;skipped=0
 for si,st in enumerate(seat):
  sq=st[:,[0,2]];candidates=np.flatnonzero((lo<=sq.max(0)).all(1)&(hi>=sq.min(0)).all(1))
  for fi in candidates:
   poly=clip(proj[fi].copy(),sq)
   if len(poly)<3:continue
   area=.5*abs(sum(cross(poly[k],poly[(k+1)%len(poly)])for k in range(len(poly))))
   if area<=1e-16:continue
   hy,sy=heights(h[fi],poly),heights(st,poly)
   if hy is None or sy is None:skipped+=1;continue
   g=hy-sy;pairs+=1;negative+=int(g.min()<-1e-9);crossing+=int(g.min()<-1e-9 and g.max()>1e-9);near+=int(g.min()<=.003 and g.max()>=-.003);k=int(np.argmin(g))
   if crosswit is None and g.min()<-1e-9 and g.max()>1e-9:
    segment=[]
    for pi in range(len(poly)):
     pj=(pi+1)%len(poly)
     if g[pi]*g[pj]<0:segment.append((poly[pi]+(poly[pj]-poly[pi])*g[pi]/(g[pi]-g[pj])).tolist())
    crosswit={'rider_triangle_id':int(ids[fi]),'rider_vertex_ids':t[ids[fi]].tolist(),'rider_triangle_bike_frame_m':h[fi].tolist(),'seat_source_bodywork_face':int(seatids[si]),'seat_vertex_ids':BT[seatids[si]].tolist(),'seat_triangle_bike_frame_m':st.tolist(),'overlap_polygon_xz_m':poly.tolist(),'gap_at_polygon_vertices_m':g.tolist(),'zero_gap_segment_xz_m':segment}
   if g[k]<best:
    best=float(g[k]);wit={'rider_GLTF_mesh':0,'rider_GLTF_primitive':0,'rider_triangle_id':int(ids[fi]),'rider_vertex_ids':t[ids[fi]].tolist(),'rider_triangle_bike_frame_m':h[fi].tolist(),'seat_source_bodywork_face':int(seatids[si]),'seat_vertex_ids':BT[seatids[si]].tolist(),'seat_triangle_bike_frame_m':st.tolist(),'minimum_xz_m':poly[k].tolist(),'rider_height_m':float(hy[k]),'seat_height_m':float(sy[k]),'overlap_polygon_xz_m':poly.tolist(),'overlap_area_m2':float(area)}
 return {'finite_projection_pairs':pairs,'negative_gap_pairs':negative,'surface_crossing_pairs':crossing,'near_3mm_pairs':near,'skipped_projection_degenerate_pairs':skipped,'minimum_bike_frame_Y_gap_mm':None if not np.isfinite(best)else best*1000,'witness':wit,'first_surface_crossing_witness':crosswit}

m34=js(EVID/'rig-adapter01/body-bind34/candidate-cpu/pose-manifest.json')
mv5=js(V5/'candidate-cpu/pose-manifest.json')
f34=BODY34/'candidate-cpu';fv5=V5/'candidate-cpu'
p34=js(EVID/'rig-adapter01/body-bind34/played/candidate/side/textured/report.json')
pv5=js(EVID/'garment-rebuild01/physical-v5-control157/played/candidate/side/textured/report.json')
full=js(EVID/'garment-rebuild01/full-motion155/report.json')
assert inputs[full['source']]['sha256']==full['playedReportSHA256']
variants={}
for name,manifest,folder,played in [('physical34',m34,f34,p34),('physicalV5',mv5,fv5,pv5)]:
 gj,get=glb(manifest['source']);assert inputs[manifest['source']]['sha256']==manifest['sourceSHA256']==played['sourceSHA256'];prim=gj['meshes'][0]['primitives'][0];rest=arr(folder,manifest['primitives'][0]['attributes']['position'],3);t=arr(folder,manifest['primitives'][0]['index'],3).astype(np.int64);ids=roi(rest,t)
 assert np.array_equal(get(prim['attributes']['POSITION']),rest);assert np.array_equal(get(prim['indices']).reshape(-1,3),t)
 hipvertices=np.unique(t[ids]);morphmax=[]
 for target in prim.get('targets',[]):morphmax.append(float(abs(get(target['POSITION'])[hipvertices]).max()))
 assert max(morphmax,default=0)==0,'Hip morph positions are not zero'
 hoodp=arr(folder,manifest['primitives'][1]['attributes']['position'],3);hoodt=arr(folder,manifest['primitives'][1]['index'],3).astype(int)
 assert len(roi(hoodp,hoodt))==0
 variants[name]=(manifest,folder,played,rest,t,ids,gj,get)
 variants[name+'_meta']={'sourceSHA256':manifest['sourceSHA256'],'rest_hip_triangle_ids':ids.tolist(),'hip_vertex_count':len(hipvertices),'hip_morph_max_abs_m':morphmax,'hood_hip_ROI_faces':0,'bones':manifest['primitives'][0]['bones']}

BPraw=arr(f34,m34['bodyworkSource']['positions'],3);BT=arr(f34,m34['bodyworkSource']['triangles'],3).astype(np.int64)
bikej,bikeget=glb(REPO/'public/models/bike-rookie.glb');assert inputs[str(REPO/'public/models/bike-rookie.glb')]['sha256']==m34['bodyworkSource']['sourceSHA256'];origin=next(i for i,x in enumerate(bikej['nodes'])if x.get('name')=='attach_frame_origin');bodyNode=next(i for i,x in enumerate(bikej['nodes'])if x.get('name')=='bodywork');bodyN=bikej['nodes'][bodyNode];bp=bikej['meshes'][bodyN['mesh']]['primitives'][0]
assert not any(k in bodyN for k in ['matrix','rotation','translation','scale']);assert np.array_equal(np.frombuffer(read(PRIVATE/'bike-decoded-position.f64'),dtype='<f8').reshape(-1,3),BPraw);assert np.array_equal(np.frombuffer(read(PRIVATE/'bike-decoded-triangles.f64'),dtype='<f8').reshape(-1,3),BT)
# The scene only has one flat node tree for this mesh/marker; reject unknown graph transforms.
parent={c:i for i,n in enumerate(bikej['nodes'])for c in n.get('children',[])}
for child in [origin,bodyNode]:
 chain=[];v=child
 while v in parent:v=parent[v];chain.append(v);assert not any(k in bikej['nodes'][v]for k in ['matrix','rotation','translation','scale'])
shift=-np.array(bikej['nodes'][origin]['translation'],float);BP=BPraw+shift
read(REPO/'node_modules/meshoptimizer/meshopt_decoder.cjs')
read(REPO/'node_modules/meshoptimizer/package.json')
bikeSource=read(REPO/'src/render/hero/gltfBike.ts')
assert b'this.scene.position.copy(this.shift).negate()'in bikeSource and b'this.frame.add(this.scene)'in bikeSource
bq=BP[BT];n=np.cross(bq[:,1]-bq[:,0],bq[:,2]-bq[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-15)
seatids=np.flatnonzero(((bq[:,:,0]>=-.541)&(bq[:,:,0]<=-.049)&(bq[:,:,1]>=.5405)&(bq[:,:,1]<=.631)&(abs(bq[:,:,2])<=.069)).all(1)&(n[:,1]>.3));assert len(seatids)==48;seat=bq[seatids]
authored=js(REPO/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/hoodie-repair02/qa-lane/uv-lower01/saddle-triangle-surface-gap.json')
bikeauth=js(REPO/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/evidence/bike.json');abody=next(x for x in bikeauth if x['name']=='bodywork');assert np.array_equal(np.array(abody['triangles']).reshape(-1,3),BT)
bike_task3_delta=float(abs(np.array(abody['positions'])-BP).max())
M=arr(Path(full['matricesPrivateDirectory']),full['outputs'][0]).reshape(480,19,4,4).transpose(0,1,3,2)
rows=[];checks=[];snapshots={}
for name in ['physical34','physicalV5']:
 manifest,folder,played,rest,t,ids,gj,get=variants[name]
 for row in manifest['rows']:
  i=row['i'];sample=played['samples'][i];body=arr(folder,row['dump'][0]['positions'],3);actualbike=arr(folder,row['bodyworkBikeFrame'],3);error=float(abs(actualbike-BP).max());assert error<1e-12
  joint=arr(folder,row['dump'][0]['jointTransforms']).reshape(19,4,4).transpose(0,2,1)
  checks.append({'variant':name,'i':i,'rigid_bike_reconstruction_max_m':error,'joint_matrix_delta_vs_full34':float(abs(joint-M[i]).max())})
  out=evaluate(body,t,ids,actualbike[BT[seatids]],seatids);out.update({'variant':name,'i':i,'tick':sample['tick'],'role':'frozen_actual_witness','phase':sample['phase'],'actual_rider_metadata':{'rider':sample['state']['rider'],'riderBody':sample['state']['riderBody'],'debug':sample['debug'],'contacts':sample['state']['contacts']},'lean':sample['state']['rider']['lean'],'state_hash_recorded':sample['hash'],'state_sha256':canonical(sample['state']),'camera_sha256':canonical(sample['camera']),'bones_sha256':canonical(sample['bones']),'bikeframe_bones_sha256':canonical(sample['bonesInBikeFrame']),'position_dump':row['dump'][0]['positions'],'joint_dump':row['dump'][0]['jointTransforms'],'grounded':[sample['state']['wheels'][s]['grounded']for s in ['rear','front']]});rows.append(out);snapshots[f'{name}_{i}_hip_triangles']=body[t[ids]]

# Only retained34 extra frames; don't silently infer V5 runtime transforms for more poses.
manifest,folder,played,rest,t,ids,gj,get=variants['physical34'];a=manifest['primitives'][0]['attributes'];skin=arr(folder,a['skinIndex'],4).astype(int);weight=arr(folder,a['skinWeight'],4);h=np.c_[rest,np.ones(len(rest))]
# Diagnose why final-affine weighted LBS cannot substitute for the retained dumps.
row=manifest['rows'][0];i=row['i'];predicted=np.einsum('vk,vkij,vj->vi',weight,M[i][skin],h)[:,:3];dump=arr(folder,row['dump'][0]['positions'],3)
naive_error=float(abs(predicted[np.unique(t[ids])]-dump[np.unique(t[ids])]).max())
checks.append({'variant':'physical34','i':i,'naive_weighted_final_affine_hip_position_max_m':naive_error,'result':'NOT_EXACT_DO_NOT_SUBSTITUTE','reason':'Three sums weighted Cartesian bone points then applies outer affine once; weighted final joint matrices repeat outer translation times serialized float32 sum(weights).'})
samples=played['samples'];ground=lambda s:any(s['state']['wheels'][k]['grounded']for k in ['rear','front'])
landing=min((samples[i-1]['state']['bike']['vel']['y'],i)for i in range(1,len(samples))if not ground(samples[i-1])and ground(samples[i]))[1]
minlean=min(range(len(samples)),key=lambda i:samples[i]['state']['rider']['lean']);maxlean=max(range(len(samples)),key=lambda i:samples[i]['state']['rider']['lean'])
missing={'status':'UNMEASURED_SURFACE','actual_recorded_frames':{'maximum_forward_lean':maxlean,'strongest_recorded_landing_before':landing-1,'strongest_recorded_landing_grounded':landing,'strongest_recorded_landing_recovery':landing+1},'missing_exact_fields':['bike.frame.matrixWorld inverse per selected frame','mesh.matrixWorld and bindMatrixInverse per selected frame, or their exact combined outer affine prefix','alternatively complete skinned position dumps for those frames'],'reason':'Full155 retains final joint transforms but not the exact outer affine prefix. No fitted/estimated transform or tolerance relaxation used.'}
np.savez_compressed(PRIVATE/'finite-surfaces.npz',seat_triangle_ids=seatids,seat_triangles=seat,**snapshots)
read(PRIVATE/'finite-surfaces.npz')
report={'status':'FINITE_CONTACT_AUDIT_ONLY_UNACCEPTED','method':'Exact finite convex XZ triangle overlap; linear bike-frame Y height gap minimum at overlap vertices. No socket/nearest-vertex metric.','recipe_hashes':{'audit.py':sha(Path(__file__).read_bytes()),'decode-bike.mjs':sha(Path(__file__).with_name('decode-bike.mjs').read_bytes())},'source_namespace':'rider glTF mesh0 primitive0 triangle row IDs; bike glTF bodywork mesh0 primitive0 triangle row IDs; zero-based vertices/frames.','settings':{'CPU_threads':2,'hip_all_corner_rest_Y_m':[.69,1.08],'hip_all_corner_abs_rest_Z_m':.245,'seat_all_corner_X_m':[-.541,-.049],'seat_all_corner_Y_m':[.5405,.631],'seat_all_corner_abs_Z_m':.069,'seat_unit_normal_Y_gt':.3,'clip_inside_epsilon':1e-10,'projection_determinant_min':1e-12,'overlap_area_min_m2':1e-16,'signed_negative_epsilon_m':1e-9},'seat_triangle_ids':seatids.tolist(),'bike_mapping':{'source_node_id':bodyNode,'mesh_id':bodyN['mesh'],'primitive':0,'origin_node_id':origin,'origin_node':bikej['nodes'][origin],'body_node':bodyN,'bike_frame_translation_m':shift.tolist(),'bodywork_is_rigid_chassis_child':True,'task3_authored_bike_frame_max_delta_m':bike_task3_delta,'world_bike_transform':'Not needed for relative contact in shared bike.frame; absolute world transforms were not newly exported.'},'variants':{k:variants[k+'_meta']for k in ['physical34','physicalV5']},'authored_comparison':{'reported_C19_gap_mm':authored['rows'][0]['minimum_vertical_triangle_surface_gap_mm'],'endpoint_path':authored['source_endpoint_path'],'time_s':authored['time_s'],'scope':'Different finite authored sitting pose, not actual gameplay contact clearance.'},'additional_gameplay_surfaces':missing,'frame_selection':{'landing_grounded_i':landing,'landing_prior_velocity_y_m_s':samples[landing-1]['state']['bike']['vel']['y'],'minimum_lean_i':minlean,'maximum_lean_i':maxlean},'verification':checks,'rows':rows,'limitations':['Positive gaps do not imply failed riding contact: standing/airborne stances may intentionally separate rider and saddle. This audit measures geometry without imposing continuous seat support.',
'Finite projected saddle-region clearance only, not Euclidean closest distance, anatomical acceptance, cloth thickness, force, friction, or continuous collision detection.','Bike-frame Y is chassis-relative vertical, not gravity/world vertical on an angled bike.','Hood has zero faces in this hip ROI; anatomical body beneath garment is absent. ROI may include folded clothing and upper thighs; anatomical subregion is unclassified, so no butt-only claim.','Both34 and V5 are measured only at the same four literal actual dumps; maximum-forward-lean and landing/recovery surface rows remain UNMEASURED. Full155 joint matrices are hash-pinned as setup evidence only.','Only 48 selected upward saddle triangles and rest-defined hip-region body faces; side/underside surfaces and other bike parts are outside scope.','Recorded frames are 12fps at ticks10 apart; onset of ground contact lies between snapshots. No new rendered/device/stranger evidence.'],'input_files':inputs}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
for row in rows:print(row['variant'],row['i'],row['role'],round(row['minimum_bike_frame_Y_gap_mm'],6)if row['minimum_bike_frame_Y_gap_mm']is not None else None,'pairs',row['finite_projection_pairs'],'negative',row['negative_gap_pairs'],'crossing',row['surface_crossing_pairs'])
