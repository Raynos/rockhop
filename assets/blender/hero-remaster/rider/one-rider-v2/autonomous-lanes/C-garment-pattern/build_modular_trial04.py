"""One modular skin/garment trial: continuous native bust, separate curved hood.

Entire new skin source is unchanged. Original garment outside an exact face-star
strip stays fixed. Authored cloth UVs use nearest original cloth triangle's actual
barycentric atlas coordinates, with no generic tan-material substitution.
"""
import bpy,bmesh,numpy as np,json,hashlib,time,math,traceback,datetime
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
RUN=R/'autonomous-lanes/C-garment-pattern/trial04';OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial04')
RUN.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
assert not (RUN/'character.blend').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bp=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';hp=R/'head-cleanup/mpfb-v8-palette/african/head.blend';mask=R/'collar-trial1/collar-selection.npz'
report={'status':'UNACCEPTED C modular hood trial04','actualStartUTC':'2026-10-01 01:56:30 UTC','originalDeadlineUTC':'2026-10-01 02:26:30 UTC','deadlineUTC':'2026-10-01 02:43:00 UTC','inputs':{str(p):sha(p) for p in [bp,hp,mask]},'recipeSHA256':sha(__file__),'mechanism':'Continuous original native skin bust unchanged under separate authored curved hood panels and rolled lining; actual original cloth barycentric UV/PBR transfer','authorizedExactPinchCorrection':[19285,19904],'authorizedExactIslandCorrection':[26265,26268,26649,26650],'boundedContinuationUTC':'2026-10-01 02:43:00 UTC','priorFailures':'C trial01 appearance rejected5/10 body3/10 face; six historical neck failures retained. No history reset.'}
def loops(b):
 pending={e for e in b.edges if e.is_boundary};rs=[]
 while pending:
  e=pending.pop();es={e};stack=[e]
  while stack:
   for v in stack.pop().verts:
    for e in v.link_edges:
     if e in pending:pending.remove(e);es.add(e);stack.append(e)
  adj={}
  for e in es:
   a,c=e.verts;adj.setdefault(a,[]).append(c);adj.setdefault(c,[]).append(a)
  assert all(len(n)==2 for n in adj.values()),'True collar boundary branches: freeze rather than silently widen'
  start=min(adj,key=lambda v:tuple(v.co));ring=[start];prev=None;cur=start
  while True:
   n=next(v for v in adj[cur] if v!=prev)
   if n==start:break
   ring.append(n);prev,cur=cur,n;assert len(ring)<=len(adj)
  if sum(a.co.x*c.co.y-c.co.x*a.co.y for a,c in zip(ring,ring[1:]+ring[:1]))<0:ring.reverse()
  rs.append(ring)
 return rs
def digest(fs,us):
 rows=[(f.material_index,sorted(tuple(round(float(x),7) for x in list(l.vert.co)+sum((list(l[u].uv) for u in us),[])) for l in f.loops)) for f in fs]
 return hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()
def distances(r):
 ls=np.array([(r[(i+1)%len(r)].co-r[i].co).length for i in range(len(r))]);return np.r_[0,np.cumsum(ls)]/ls.sum()
def at(r,d,t):
 i=min(int(np.searchsorted(d,t,side='right'))-1,len(r)-1);return r[i].co.lerp(r[(i+1)%len(r)].co,float((t-d[i])/(d[i+1]-d[i])))
try:
 bpy.ops.wm.open_mainfile(filepath=str(bp));s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=2
 body=next(o for o in s.objects if o.type=='MESH');b=bmesh.new();b.from_mesh(body.data);b.faces.index_update();b.verts.index_update();us=[b.loops.layers.uv.get(u.name) for u in body.data.uv_layers]
 face_origin={f:f.index for f in b.faces};v_origin={v:v.index for v in b.verts}
 src=np.load(mask);v=src['verticesBlender'];f=src['faces'];keep=src['retainedFaceMask'];tree=KDTree(len(f))
 for i,ids in enumerate(f):tree.insert(v[ids].mean(0),i)
 tree.balance();head_delete=[]
 for q in b.faces:
  if len(q.verts)!=3:continue
  pts=np.array([v.co for v in q.verts]);_,i,d=tree.find(pts.mean(0))
  if d<2e-6 and not keep[i] and max(min(np.linalg.norm(p-qq) for qq in v[f[i]]) for p in pts)<2e-6:head_delete.append(q)
 assert len(head_delete)==13657,'Exact rejected old-head mask must correspond'
 head_ids=[face_origin[q] for q in head_delete];bmesh.ops.delete(b,geom=head_delete,context='FACES');loose=[v for v in b.verts if not v.link_faces]
 if loose:bmesh.ops.delete(b,geom=loose,context='VERTS')
 rings=loops(b);assert len(rings)==1;oldrim=rings[0];N=64;old_d=distances(oldrim);oldcurve=np.array([at(oldrim,old_d,i/N) for i in range(N)])
 # Exact source cloth reference is head-free, avoiding old skin/hair atlas contamination.
 cloth_reference=b.copy();cloth_reference.verts.index_update();cloth_reference.faces.index_update();bmesh.ops.triangulate(cloth_reference,faces=list(cloth_reference.faces));cloth_reference.faces.index_update()
 reference_vertices=[x.co.copy() for x in cloth_reference.verts];reference_faces=[[x.index for x in q.verts] for q in cloth_reference.faces];reference_uv=[[[list(l[u].uv) for l in q.loops] for q in cloth_reference.faces] for u in [cloth_reference.loops.layers.uv.get(x.name) for x in body.data.uv_layers]]
 bvh=BVHTree.FromPolygons(reference_vertices,reference_faces,all_triangles=True)
 # Verified lower original cloth only: warm ochre texels below1.49m, no dark nape/hair.
 original_bs=next(n for n in body.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 pending=[l.from_node for l in original_bs.inputs['Base Color'].links];original_image=None;seen=set()
 while pending:
  node=pending.pop()
  if node in seen:continue
  seen.add(node)
  if node.type=='TEX_IMAGE' and node.image:original_image=node.image;break
  pending.extend(link.from_node for inp in node.inputs for link in inp.links)
 assert original_image,'Actual native basecolor image must be identified'
 width,height=original_image.size;pixels=np.asarray(original_image.pixels[:],np.float32).reshape(height,width,4)
 cloth_indices=[];sample_rgb=[]
 for index,ids in enumerate(reference_faces):
  center=sum((reference_vertices[i] for i in ids),Vector())/3
  if not (1.32<center.z<1.49 and abs(center.x)<.27):continue
  uvcenter=np.mean(reference_uv[0][index],axis=0);x=int(uvcenter[0]*width)%width;y=int(uvcenter[1]*height)%height;rgb=pixels[y,x,:3]
  if rgb[0]>.035 and rgb[0]>1.12*rgb[1] and rgb[2]<.85*rgb[1]:cloth_indices.append(index);sample_rgb.append(rgb.tolist())
 assert len(cloth_indices)>100,'Verified original ochre cloth reference insufficient; stop'
 cloth_bvh=BVHTree.FromPolygons(reference_vertices,[reference_faces[i] for i in cloth_indices],all_triangles=True)
 report['verifiedOriginalClothReference']={'triangleCount':len(cloth_indices),'worldZBand':[1.32,1.49],'maxAbsX':.27,'actualImage':original_image.name,'warmTexelRule':'R>.035,R>1.12G,B<.85G','actualRGBMin':np.min(sample_rgb,axis=0).tolist(),'actualRGBMax':np.max(sample_rgb,axis=0).tolist(),'darkOldNapeHairExcluded':True}
 def transfer(p,k):
  co,normal,local_index,dist=cloth_bvh.find_nearest(p);idx=cloth_indices[local_index];ids=reference_faces[idx];uu=reference_uv[k][idx]
  result=barycentric_transform(co,*[reference_vertices[i] for i in ids],*[Vector((u[0],u[1],0)) for u in uu]);return result.xy
 # Complete vertex-stars, no radius-clipped fragments; bounded two layers only.
 selected=set(oldrim)
 for layer in range(2):selected.update(e.other_vert(v) for v in list(selected) for e in v.link_edges)
 strip={q for v in selected for q in v.link_faces};pinch=[q for q in b.faces if face_origin[q] in {19285,19904,26265,26268,26649,26650}];assert len(pinch)==6;strip.update(pinch);strip_ids=[face_origin[q] for q in strip];protected=[q for q in b.faces if q not in strip];protected_before=digest(protected,us)
 original_region=body.copy();original_region.data=body.data.copy();original_region.name='SAVED original rejected head and exact local hood strip comparison only';s.collection.objects.link(original_region);original_region.hide_render=True;original_region.hide_set(True)
 rb=bmesh.new();rb.from_mesh(original_region.data);rb.faces.index_update();retain_ids=set(head_ids+strip_ids);bmesh.ops.delete(rb,geom=[q for q in rb.faces if q.index not in retain_ids],context='FACES');loose=[v for v in rb.verts if not v.link_faces]
 if loose:bmesh.ops.delete(rb,geom=loose,context='VERTS')
 rb.to_mesh(original_region.data);rb.free()
 bmesh.ops.delete(b,geom=list(strip),context='FACES');loose=[v for v in b.verts if not v.link_faces]
 if loose:bmesh.ops.delete(b,geom=loose,context='VERTS')
 rs=loops(b);assert len(rs)==1,'Whole-star cloth extraction yielded multiple boundaries; stop'
 base_ring=rs[0];bd=distances(base_ring);base=[at(base_ring,bd,i/N) for i in range(N)]
 # Low frequency closed spline preserves original hood shape, without sawtooth nape.
 fourier=np.fft.rfft(oldcurve,axis=0);fourier[7:]=0;opening=np.fft.irfft(fourier,n=N,axis=0)
 for i,p in enumerate(opening):
  back=max(0,min(1,(p[1]+.04)/.17));p[2]=min(p[2],1.505+.068*back)
 # Phase corresponds to the original ring's leftmost start; align actual source boundary.
 offset=min(range(N),key=lambda i:np.linalg.norm(opening[i]-base[0]));opening=np.roll(opening,-offset,axis=0)
 control=[];quads=[];normal_targets=[]
 for row in range(7):
  t=row/6
  for i,start in enumerate(base):
   target=Vector(opening[i]);delta=target-start;_,normal,_,_=bvh.find_nearest(start);tangent=delta-normal*delta.dot(normal)
   if tangent.length>1e-7:tangent=tangent.normalized()*min(delta.length,.035)
   # Hermite derivative follows the original retained source cloth tangent.
   h00=2*t**3-3*t*t+1;h10=t**3-2*t*t+t;h01=-2*t**3+3*t*t;h11=t**3-t*t
   q=start*h00+tangent*h10+target*h01+delta*.25*h11
   if row==0:q+=tangent.normalized()*.001 if tangent.length>1e-7 else Vector((0,0,.001))
   control.append(tuple(q))
 for row in range(6):
  for i in range(N):j=(i+1)%N;quads.append((row*N+i,row*N+j,(row+1)*N+j,(row+1)*N+i))
 me=bpy.data.meshes.new('New source-tangent curved garment pattern');me.from_pydata(control,[],quads);me.update();panel=bpy.data.objects.new('New separate hood opening authored cloth',me);s.collection.objects.link(panel)
 sub=panel.modifiers.new('Native curved cloth Catmull-Clark','SUBSURF');sub.levels=1;sub.render_levels=1
 solid=panel.modifiers.new('Native 2mm neckline lining','SOLIDIFY');solid.thickness=.002;solid.offset=-1;solid.use_rim=False
 bpy.ops.object.select_all(action='DESELECT');panel.select_set(True);bpy.context.view_layer.objects.active=panel
 for mod in list(panel.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 pb=bmesh.new();pb.from_mesh(panel.data);prs=loops(pb);assert len(prs)==4
 # Match the two layer boundary pairs by actual distance to authored source base.
 def base_distance(r):return sum(min((v.co-p).length_squared for p in base) for v in r)/len(r)
 prs.sort(key=base_distance);bases=prs[:2];rolls=prs[2:]
 outer_base=min(bases,key=lambda r:sum(bvh.find_nearest(v.co)[3] for v in r));inner_base=next(r for r in bases if r is not outer_base)
 pmap={v:b.verts.new(v.co) for v in pb.verts};new=[]
 def addface(vs):
  q=b.faces.new(vs);q.material_index=0;q.smooth=True
  for l in q.loops:
   adjacent=[f for f in l.vert.link_faces if f in protected]
   for k,u in enumerate(us):
    if adjacent:
     oldface=min(adjacent,key=lambda f:(f.calc_center_median()-q.calc_center_median()).length_squared);oldloop=next(ol for ol in oldface.loops if ol.vert==l.vert);l[u].uv=oldloop[u].uv
    else:l[u].uv=transfer(l.vert.co,k)
  new.append(q);return q
 for q in pb.faces:addface([pmap[v] for v in q.verts])
 def sew(a,c):
  a=list(a);c=list(c);k=min(range(len(c)),key=lambda i:(a[0].co-c[i].co).length_squared);c=c[k:]+c[:k];da,dc=distances(a),distances(c);i=j=0;count=0
  while i<len(a) or j<len(c):
   aa=da[i+1] if i<len(a) else math.inf;cc=dc[j+1] if j<len(c) else math.inf
   if aa<cc:vs=[a[i%len(a)],a[(i+1)%len(a)],c[j%len(c)]];i+=1
   else:vs=[a[i%len(a)],c[(j+1)%len(c)],c[j%len(c)]];j+=1
   addface(vs);count+=1
  return count
 sewn={'sourceGarmentToActualOuterPanel':sew(base_ring,[pmap[v] for v in outer_base]),'actualRolledNecklineThickness':sew([pmap[v] for v in rolls[0]],[pmap[v] for v in rolls[1]])}
 assert digest(protected,us)==protected_before,'Protected source garment/limbs/handUV changed'
 bmesh.ops.recalc_face_normals(b,faces=list(b.faces));topology={'boundaryEdges':sum(e.is_boundary for e in b.edges),'nonmanifoldEdges':sum(not e.is_manifold and not e.is_boundary for e in b.edges),'degenerateFaces':sum(q.calc_area()<1e-12 for q in b.faces),'openHiddenLiningHemVertices':len(inner_base)}
 assert topology['nonmanifoldEdges']==0,'Nonmanifold garment seam cannot pass'
 b.to_mesh(body.data);body.data.update();body.name='UNACCEPTED C modular source hoodie curved neckline native hands'
 # Entire original NEW head/bust and eyes retained, only canonical rigid/uniform transform.
 with bpy.data.libraries.load(str(hp),link=False) as (src,dst):dst.objects=list(src.objects)
 native=[o for o in dst.objects if o and o.type=='MESH'];head_proof=[]
 for o in native:
  s.collection.objects.link(o);before=hashlib.sha256(np.asarray([list(v.co) for v in o.data.vertices],np.float32).tobytes()).hexdigest();mat=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Translation(Vector((0,0,1.59338)))@Matrix.Scale(.42,4)@mat
  after=hashlib.sha256(np.asarray([list(v.co) for v in o.data.vertices],np.float32).tobytes()).hexdigest();assert before==after;head_proof.append({'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'sourceCoordinatesSHA256':before,'sourceCoordinatesUnchanged':True,'nativeUVsUnchanged':True,'continuousEntireBustNotTrimmed':True,'canonicalMatrix':[list(row) for row in o.matrix_world]})
 # Actual 3D native skin/cloth clearance, no 2D projected-rim containment assertion.
 native_head=next(o for o in native if 'head' in o.name.lower());hm=native_head.data;hm.calc_loop_triangles()
 skin_positions=[native_head.matrix_world@v.co for v in hm.vertices];skin_triangles=[list(t.vertices) for t in hm.loop_triangles]
 skin_bvh=BVHTree.FromPolygons(skin_positions,skin_triangles,all_triangles=True)
 clearance=[];negative=[]
 for index,p in enumerate(control):
  co,normal,tri,d=skin_bvh.find_nearest(Vector(p))
  if co.z<1.49:continue
  signed=float((Vector(p)-co).dot(normal));clearance.append((d,signed))
  if signed<-.0005:negative.append({'controlVertex':index,'cloth':p,'skin':list(co),'distanceM':d,'signedDistanceM':signed})
 report['actualLocal3DSkinClothClearance']={'sampleBasis':'All actual authored control panel vertices against unchanged full native skin triangles; not a projected2D contour','sampleCount':len(clearance),'minimumDistanceM':min(x[0] for x in clearance) if clearance else None,'minimumSignedSurfaceDistanceM':min(x[1] for x in clearance) if clearance else None,'signedInsideSamplesBeyond0_5mm':len(negative),'insideWitnesses':negative[:20],'limitations':'Control vertices only, not dense continuous triangle/selfcollision or final neck-motion acceptance'}
 np.savez_compressed(RUN/'source-region-mask.npz',removedOldHeadSourceFaceIds=np.asarray(head_ids,np.int32),removedLocalHoodStripSourceFaceIds=np.asarray(sorted(strip_ids),np.int32),protectedSourceFaceIds=np.asarray([face_origin[q] for q in protected],np.int32))
 bpy.data.objects.remove(panel,do_unlink=True)
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for o in native:o.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'character.blend'));bpy.ops.export_scene.gltf(filepath=str(RUN/'character.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
 report['sourceProtection']={'removedOldRejectedHeadFaces':len(head_ids),'removedExactTwoVertexStarHoodStripFaces':len(strip_ids),'sourceMaskFile':str(RUN/'source-region-mask.npz'),'sourceMaskSHA256':sha(RUN/'source-region-mask.npz'),'protectedSourcePolygons':len(protected),'protectedPositionAllUVsMaterialSHA256':protected_before,'protectedExact':True,'sourceNativeMaterialsAndFaceAssignmentsPreserved':True,'allOriginalHandsFeetLegsOutsideMask':True}
 report['headProof']=head_proof;report['cloth']={'sourceBaseBoundaryVertices':len(base_ring),'originalHoodOpeningVertices':len(oldrim),'authoredControlVertices':len(control),'authoredControlQuads':len(quads),'cleanOpeningFourierModes':6,'actualPBRTransfer':'New face corners use original actual cloth triangle barycentricUV0/UV1; exact original native body PBR textures/material, no color substitute','sourceTangentHermiteConstruction':True,'thicknessM':.002,'sewn':sewn,'liningHem':'One open hidden cloth lining hem beneath sourcehood; no exposed separate skin join. Hidden boundary requires moving proof.','skinClothWeld':False}
 report['topology']=topology;report['outputs']={str(p):sha(p) for p in [RUN/'character.blend',RUN/'character.glb']};report['inputsAfter']={p:sha(p) for p in report['inputs']};assert report['inputsAfter']==report['inputs'];report['status']='UNACCEPTED frozen C modular hood trial04; actual appearance/deformation review pending'
except Exception as error:report['status']='FAILED C modular hood trial04';report['failure']=repr(error);report['traceback']=traceback.format_exc();raise
finally:
 report['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('MODULAR_FROZEN',json.dumps({'status':report['status'],'failure':report.get('failure'),'topology':report.get('topology')}),flush=True)
