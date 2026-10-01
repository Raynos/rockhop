"""Fresh sewn hoodbag: true flat-rest cloth simulation, not a cape loft.
Two exterior panels share rear-center stitched vertices. Four final pattern charts:
outer left/right actually simulated; lining left/right offset from measured drape.
No bake or final identity. Source bodies outside declared fullhood mask are exact.
"""
import bpy,numpy as np,json,hashlib,time,math,datetime,resource
from pathlib import Path
from mathutils import Vector,Euler
from mathutils.bvhtree import BVHTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume/cloth-bag/trial01');cfg=json.loads((R/'settings.json').read_text());c=cfg['cloth'];deadline=datetime.datetime.fromisoformat(cfg['deadlineUTC']).timestamp();t=time.monotonic();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();bp=Path(cfg['bodySource']);hp=Path(cfg['sizingSkinSource']);sources={str(p):sha(p) for p in [bp,hp]};rep={'status':'UNACCEPTED truecloth hoodbag trial01','oldLineageFailuresRetired':15,'priorNEWWholehoodAppearanceFailures':1,'threads':2,'device':'CPU','simulationSnapshots':[],'sources':sources}

def loops(f):
 ed=np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]));u,k=np.unique(np.sort(ed,axis=1),axis=0,return_counts=True);g={}
 for a,b in u[k==1]:g.setdefault(int(a),[]).append(int(b));g.setdefault(int(b),[]).append(int(a))
 if any(len(x)!=2 for x in g.values()):raise RuntimeError('Guarded body seam branch')
 out=[];seen=set()
 for a in g:
  if a in seen:continue
  p=[];last=-1;cur=a
  while cur not in seen:p.append(cur);seen.add(cur);ns=g[cur];nx=ns[0] if ns[0]!=last else ns[1];last,cur=cur,nx
  if cur!=a:raise RuntimeError('Open guarded body circuit')
  q=np.array(p)
  if not np.any(np.all(ed==q[:2],axis=1)):q=q[::-1]
  out.append(q)
 return out

def uvunwrap(u):
 u=np.array(u,float)
 if u.max()-u.min()>.5:u[u<.5]+=1
 return u

def neck(angle):return np.array([c['pinnedNeckRadiusX']*math.sin(angle),c['pinnedNeckCenterY']-c['pinnedNeckRadiusY']*math.cos(angle),c['pinnedNeckZ']-c['pinnedNeckZVariation']*math.cos(angle)])

def restore_weights(obj,names,weights,split):
 for name in names:obj.vertex_groups.new(name=name)
 for vi,ws in enumerate(weights):
  for gi,w in ws:obj.vertex_groups[gi].add([vi],w,'REPLACE')
 for si,(a,b,x) in split.items():
  wa=dict(weights[a]);wb=dict(weights[b])
  for gi in set(wa)|set(wb):obj.vertex_groups[gi].add([int(si)],wa.get(gi,0)*(1-x)+wb.get(gi,0)*x,'REPLACE')

try:
 bpy.ops.wm.open_mainfile(filepath=str(bp));scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=c['frames'];scene.render.fps=24;scene.gravity=(0,0,-9.81)
 body=max((o for o in scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));old=body.data;mats=list(old.materials);uvnames=[u.name for u in old.uv_layers];weights=[[(g.group,g.weight) for g in v.groups] for v in old.vertices];groups=[g.name for g in body.vertex_groups];split=json.loads((R/'interpolated-source-weights.json').read_text());d=np.load(R/'fresh-wholehood-exclusion.npz');source=np.load(R/'body-source.npz');verts=list(d['vertices']);faces=list(d['faces']);oldUV=list(d['allTriangleUV'].transpose(1,0,2,3));material=list(d['materialIndex']);origin=list(d['faceOrigin']);charts=[np.zeros((3,2)) for _ in faces];rim=loops(d['faces'])[0];hem=d['vertices'][rim];frontidx=int(np.argmin(np.abs(hem[:,0])+.5*(hem[:,1]-hem[:,1].min())));rim=np.roll(rim,-frontidx);hem=d['vertices'][rim];N=len(rim);sg=np.sign(np.sum(hem[:,0]*np.roll(hem[:,1],-1)-hem[:,1]*np.roll(hem[:,0],-1)));arc=np.r_[0,np.cumsum(np.linalg.norm(np.roll(hem,-1,axis=0)-hem,axis=1))];arc/=arc[-1];angles=sg*2*np.pi*arc[:-1]
 def add(ids,uv,mi):faces.append(ids);oldUV.append(np.zeros((2,3,2)));charts.append(np.array(uv));material.append(mi);origin.append(-2)
 # New low shirt/yoke is a body attachment fixture, not the failed raised cape.
 prev=rim.tolist()
 for row in range(1,4):
  a=row/3;target=np.array([neck(x) for x in angles]);target[:,2]-=.008;pts=hem*(1-a)+target*a;ids=[]
  for p in pts:ids.append(len(verts));verts.append(p)
  for j in range(N):jn=(j+1)%N;u0=arc[j];u1=arc[j+1];uv=[(u1*.94+.03,.04+(row-1)/3*.36),(u0*.94+.03,.04+(row-1)/3*.36),(u0*.94+.03,.04+row/3*.36),(u1*.94+.03,.04+row/3*.36)];q=[prev[jn],prev[j],ids[j],ids[jn]];add(q[:3],uv[:3],2);add([q[0],q[2],q[3]],[uv[0],uv[2],uv[3]],2)
  prev=ids
 # Shared collar fixture uses the exact future pinned textile edge coordinates.
 tip=math.radians(c['neckTipDegrees']);panAngles=[tip+(math.pi-tip)*u/c['U'] for u in range(c['U']+1)];baseangles=[0]+panAngles+[-a for a in panAngles[:-1]];baseangles.sort(key=lambda a:float(np.mod(a*sg,2*np.pi)));topids=[];topmap={}
 for a in baseangles:vi=len(verts);verts.append(neck(a));topids.append(vi);topmap[round(float(np.mod(a,2*np.pi)),7)]=vi
 al=np.r_[0,np.cumsum(np.linalg.norm(np.roll(np.array(verts)[prev],-1,axis=0)-np.array(verts)[prev],axis=1))];bl=np.r_[0,np.cumsum(np.linalg.norm(np.roll(np.array(verts)[topids],-1,axis=0)-np.array(verts)[topids],axis=1))];al/=al[-1];bl/=bl[-1];i=j=0
 while i<len(prev) or j<len(topids):
  a0=prev[i%len(prev)];b0=topids[j%len(topids)]
  if j==len(topids) or (i<len(prev) and al[i+1]<bl[j+1]):ids=[prev[(i+1)%len(prev)],a0,b0];uv=[(al[i+1]*.94+.03,.41),(al[i]*.94+.03,.41),(bl[j]*.94+.03,.46)];i+=1
  else:ids=[a0,b0,topids[(j+1)%len(topids)]];uv=[(al[i]*.94+.03,.41),(bl[j]*.94+.03,.46),(bl[j+1]*.94+.03,.46)];j+=1
  add(ids,uv,3)
 fixture_v=np.array(verts);fixture_f=np.array(faces);fixture_uv=np.array(oldUV).transpose(1,0,2,3);fixture_m=np.array(material);fixture_o=np.array(origin);fixture_chart=np.array(charts)
 mesh=bpy.data.meshes.new('NEW lowyoke neck attachment fixture');mesh.from_pydata(verts,[],faces);mesh.update()
 for m in mats:mesh.materials.append(m)
 for name in ['NEW low shirt yoke','NEW neck binding with UV width','NEW draped outer LEFT','NEW draped outer RIGHT','NEW drape-derived lining LEFT','NEW drape-derived lining RIGHT','NEW sewn face-opening roll']:
  m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.42,.42,.42,1);p.inputs['Roughness'].default_value=.75;mesh.materials.append(m)
 for p,mi in zip(mesh.polygons,material):p.material_index=mi;p.use_smooth=True
 for k,name in enumerate(uvnames+['DrapedHoodPatternUV']):
  layer=mesh.uv_layers.new(name=name);data=fixture_uv[k] if k<2 else fixture_chart
  for p,uv in zip(mesh.polygons,data):
   for li,x in zip(p.loop_indices,uv):layer.data[li].uv=x
 body.data=mesh;body.matrix_world.identity();restore_weights(body,groups,weights,split);body.modifiers.new('Actual torso/yoke cloth collider','COLLISION');body.collision.thickness_outer=.003;body.collision.thickness_inner=.001
 with bpy.data.libraries.load(str(hp),link=False) as (sr,ds):ds.objects=list(sr.objects)
 heads=[]
 for o in ds.objects:
  if o and o.type=='MESH':
   scene.collection.objects.link(o);o.scale=tuple(x*cfg['skinAdapter']['scale'] for x in o.scale);o.location=o.location*cfg['skinAdapter']['scale']+Vector(cfg['skinAdapter']['translation']);o.name='NEUTRAL SIZING ONLY '+o.name;heads.append(o)
 head=max(heads,key=lambda o:len(o.data.vertices));head.modifiers.new('Actual neutral head cloth collider','COLLISION');head.collision.thickness_outer=.003;head.collision.thickness_inner=.001;bpy.context.view_layer.update()
 cv=[];rest=[];cf=[];cuv=[];cm=[];lookup={};pinmap={};grid={}
 for side,sign in enumerate([1,-1]):
  for vi in range(c['V']+1):
   v=vi/c['V']
   for ui in range(c['U']+1):
    u=ui/c['U'];a=sign*panAngles[ui];key=('rear',vi) if ui==c['U'] else (side,ui,vi)
    if key not in lookup:
     pos=neck(a);pos[0]+=sign*.120*(1-u)*math.sin(math.pi*v);pos[1]+=.190*v;pos[2]+=.020*math.sin(math.pi*v)*(1-u)-.018*v;idx=len(cv);lookup[key]=idx;cv.append(pos);rest.append([sign*.29*(1-u),v*(.19+.045*u),0]);
     if vi==0:pinmap[idx]=topmap[round(float(np.mod(a,2*np.pi)),7)]
    grid[side,ui,vi]=lookup[key]
  for vi in range(c['V']):
   for ui in range(c['U']):
    ids=[grid[side,ui,vi],grid[side,ui+1,vi],grid[side,ui+1,vi+1],grid[side,ui,vi+1]];uv=np.array([[ui/c['U'],vi/c['V']],[(ui+1)/c['U'],vi/c['V']],[(ui+1)/c['U'],(vi+1)/c['V']],[ui/c['U'],(vi+1)/c['V']]])* [.43,.43]+[.03+side*.5,.52]
    if sign<0:ids=ids[::-1];uv=uv[::-1]
    cf.append(ids);cuv.append(uv);cm.append(4+side)
 # Actual cloth starts outside collisions where a bounded local normal push is needed.
 trees=[]
 for obj in [body,head]:trees.append(BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons],all_triangles=False))
 init=np.array(cv);pushed=[]
 for i,x in enumerate(cv):
  if i in pinmap:continue
  for tree in trees:
   p,n,fi,dd=tree.find_nearest(Vector(x))
   if dd<.020 and (Vector(x)-p).dot(n)<0:x=np.array(p+n*.006);cv[i]=x
  if np.linalg.norm(np.array(x)-init[i])>1e-8:pushed.append(i)
 start=np.array(cv);clothmesh=bpy.data.meshes.new('TWO true mirrored hoodbag textile panels sewn rear-center');clothmesh.from_pydata(cv,[],cf);clothmesh.update();cloth=bpy.data.objects.new('Actual CPU cloth sewn hoodbag',clothmesh);scene.collection.objects.link(cloth)
 for m in mesh.materials:clothmesh.materials.append(m)
 for p,mi in zip(clothmesh.polygons,cm):p.material_index=mi;p.use_smooth=True
 cu=clothmesh.uv_layers.new(name='DrapedHoodPatternUV')
 for p,uv in zip(clothmesh.polygons,cuv):
  for li,x in zip(p.loop_indices,uv):cu.data[li].uv=x
 basis=cloth.shape_key_add(name='Initial drape fixture');flat=cloth.shape_key_add(name='Actual flat sewing rest pattern')
 for p,x in zip(flat.data,rest):p.co=x
 flat.value=0;pin=cloth.vertex_groups.new(name='Actual fixed neck textile attachment');pin.add(list(pinmap),1,'REPLACE');mod=cloth.modifiers.new('Actual gravity hoodbag cloth simulation','CLOTH');cs=mod.settings;cs.quality=c['quality'];cs.mass=c['mass'];cs.tension_stiffness=c['tension'];cs.compression_stiffness=c['compression'];cs.shear_stiffness=c['shear'];cs.bending_stiffness=c['bending'];cs.vertex_group_mass=pin.name;cs.pin_stiffness=1;cs.rest_shape_key=flat;cs.use_sewing_springs=False;coll=mod.collision_settings;coll.use_collision=True;coll.distance_min=c['collisionDistance'];coll.collision_quality=4;coll.friction=5;coll.use_self_collision=True;coll.self_distance_min=c['selfDistance'];coll.self_friction=5;mod.point_cache.frame_start=1;mod.point_cache.frame_end=c['frames']
 np.savez(R/'actual-cloth-initial-and-flat-rest.npz',initial=start,flatRest=np.array(rest),faces=np.array(cf),pinnedIndices=np.array(list(pinmap)),initialCollisionCorrectedIndices=np.array(pushed));rep.update(actualClothVertices=len(cv),actualClothQuadFaces=len(cf),pinnedVertices=len(pinmap),rearCenterSharedVertices=c['V']+1,flatRestKeyUsed=cs.rest_shape_key.name,rearSewing='Shared rear-center topology before gravity; no sewing-spring solver falsely claimed',settings=c,initialCollisionCorrections=len(pushed),initialCollisionMaxCorrection=float(np.linalg.norm(start-init,axis=1).max()))
 snapshots=[];final=None
 for frame in range(1,c['frames']+1):
  if time.time()>deadline-120:rep['simulationStoppedAtDeadline']=True;break
  scene.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get();ev=cloth.evaluated_get(dg);em=ev.to_mesh();coords=np.array([v.co[:] for v in em.vertices]);norm=np.array([v.normal[:] for v in em.vertices]);ev.to_mesh_clear();final=coords.copy()
  if frame in [1,12,24,36,48]:
   delta=np.linalg.norm(coords-start,axis=1);row={'frame':frame,'timeSeconds':frame/24,'displacementMean':float(delta.mean()),'displacementMax':float(delta.max()),'verticesMovedOver1mm':int(np.sum(delta>.001)),'pinMaximumDisplacement':float(delta[list(pinmap)].max())};rep['simulationSnapshots'].append(row);np.savez(R/('actual-drape-frame'+str(frame)+'.npz'),vertices=coords,normals=norm);print('ACTUAL_CLOTH_FRAME',json.dumps(row),flush=True)
  rep['evaluatedFrames']=frame
 if final is None or np.max(np.linalg.norm(final-start,axis=1))<.001:raise RuntimeError('Actual cloth did not deform; cannot claim drape')
 # Freeze actual exterior cloth; derived lining is disclosed, not separately simulated.
 fv=fixture_v.tolist();ff=fixture_f.tolist();fu=fixture_uv.transpose(1,0,2,3).tolist();fm=fixture_m.tolist();fo=fixture_o.tolist();fc=fixture_chart.tolist();outmap={}
 for i,x in enumerate(final):
  if i in pinmap:outmap[i]=pinmap[i]
  else:outmap[i]=len(fv);fv.append(x)
 for ids,uv,mi in zip(cf,cuv,cm):
  for tri in [(0,1,2),(0,2,3)]:ff.append([outmap[ids[k]] for k in tri]);fu.append(np.zeros((2,3,2)));fc.append(uv[list(tri)]);fm.append(mi);fo.append(-3)
 # Two drape-derived lining panels, offset inwards; hidden lower lining hem drops12mm.
 inmap={}
 for i,x in enumerate(final):
  xx=x-norm[i]*c['liningOffset']
  if i in pinmap:xx[2]-=.012
  inmap[i]=len(fv);fv.append(xx)
 for ids,uv,mi in zip(cf,cuv,cm):
  uv=uv.copy();uv[:,1]-=.49
  for tri in [(2,1,0),(3,2,0)]:ff.append([inmap[ids[k]] for k in tri]);fu.append(np.zeros((2,3,2)));fc.append(uv[list(tri)]);fm.append(mi+2);fo.append(-4)
 # Roll the free face rim outer-to-lining, with explicit nonzero atlas width.
 ce=np.concatenate((np.array(cf)[:,[0,1]],np.array(cf)[:,[1,2]],np.array(cf)[:,[2,3]],np.array(cf)[:,[3,0]]));ue,counts=np.unique(np.sort(ce,axis=1),axis=0,return_counts=True)
 for a,b in ue[counts==1]:
  if a in pinmap and b in pinmap:continue
  if not np.any(np.all(ce==[a,b],axis=1)):a,b=b,a
  ids=[outmap[b],outmap[a],inmap[a],inmap[b]];u0=0.03+(.94*a/max(len(cv)-1,1));u1=0.03+(.94*b/max(len(cv)-1,1));uv=[[u1,.975],[u0,.975],[u0,.99],[u1,.99]]
  for tri in [(0,1,2),(0,2,3)]:ff.append([ids[k] for k in tri]);fu.append(np.zeros((2,3,2)));fc.append(np.array(uv)[list(tri)]);fm.append(8);fo.append(-5)
 fv=np.array(fv);ff=np.array(ff);fu=np.array(fu).transpose(1,0,2,3);fc=np.array(fc);fm=np.array(fm);fo=np.array(fo);valid=fo>=0;assert np.array_equal(ff[valid],source['faces'][fo[valid]]);assert np.array_equal(fu[:,valid],source['allTriangleUV'][:,fo[valid]]);assert np.array_equal(fm[valid],source['materialIndex'][fo[valid]])
 mesh2=bpy.data.meshes.new('Measured CPU draped hoodbag plus protected body');mesh2.from_pydata(fv.tolist(),[],ff.tolist());mesh2.update()
 for m in mesh.materials:mesh2.materials.append(m)
 for p,mi in zip(mesh2.polygons,fm):p.material_index=int(mi);p.use_smooth=True
 for k,name in enumerate(uvnames+['DrapedHoodPatternUV']):
  u=mesh2.uv_layers.new(name=name);uv=fu[k] if k<2 else fc
  for p,x in zip(mesh2.polygons,uv):
   for li,q in zip(p.loop_indices,x):u.data[li].uv=q
 body.data=mesh2;restore_weights(body,groups,weights,split);body.name='UNACCEPTED actual cloth hoodbag neutral body';body.modifiers.clear();cloth.hide_render=True;cloth.hide_set(True)
 delta=np.linalg.norm(final-start,axis=1);rep.update(finalFrame=rep['evaluatedFrames'],actualMovedVertices=int(np.sum(delta>.001)),maxActualSimulationDeformation=float(delta.max()),protectedOriginalTriangles=int(valid.sum()),nativeSizingSkinUnchanged=True,liningSimulation='Not separately simulated; two lining panels offset from actual measured exterior drape',newGarmentRigWeights='Unassigned, parent19boneadapter pending',noBakes=True)
 np.savez(R/'actual-draped-character-geometry.npz',vertices=fv,faces=ff,sourceUVs=fu,newPatternUV=fc,materialIndex=fm,faceOrigin=fo)
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for o in heads:o.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.wm.save_as_mainfile(filepath=str(R/'actual-cloth-neutral-master.blend'));bpy.ops.export_scene.gltf(filepath=str(R/'geometry-preview.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_apply=False,export_materials='EXPORT')
 rep['status']='UNACCEPTED actual CPU cloth drape measured; requires parent appearance review';rep['GLBSHA']=sha(R/'geometry-preview.glb')
except Exception as e:
 import traceback;rep['status']='FAILED actual cloth mechanism';rep['error']=str(e);rep['traceback']=traceback.format_exc()
finally:
 rep['elapsedSeconds']=time.monotonic()-t;rep['peakRSSBytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;rep['recipeSHA']=sha(__file__);rep['sourcesAfter']={str(p):sha(p) for p in [bp,hp]};assert rep['sourcesAfter']==sources;(R/'simulation-report.json').write_text(json.dumps(rep,indent=2)+'\n');print('SIMULATION_REPORT',json.dumps(rep),flush=True)
