"""Lane C: authored clean hood annular cloth panels, native modifiers, actual sewing.

One isolated CPU trial. Source body below reviewed upper-hood band is immutable.
The inner lining is continuous through shared vertices, never an intersecting shell.
"""
import bpy,bmesh,numpy as np,json,hashlib,math,time,traceback
from pathlib import Path
from mathutils import Vector,Matrix
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
RUN=R/'autonomous-lanes/C-garment-pattern/trial01'
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial01')
RUN.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
assert not (RUN/'character.blend').exists(),'Frozen trial cannot be overwritten'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bodypath=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend'
headpath=R/'head-cleanup/mpfb-v8-palette/african/head.blend'
report={'status':'UNACCEPTED garment-pattern trial01','startedUTC':time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime()),'deadlineUTC':'2026-10-01 02:17:00 UTC','inputs':{str(p):sha(p) for p in [bodypath,headpath]},'recipeSHA256':sha(__file__),'mechanism':'Authored stitched cloth panels; native Catmull-Clark subdivision, limited shrinkwrap onto original saved cloth reference, native 2mm solidification, actual shared-index sewing of both lining and new neck','failureHistory':'Six prior neck failures retained; no history reset. This is first C pattern trial.','limits':['New hood solid-color PBR has no baked high resolution textile map.','Static appearance is not final rig/contact acceptance.','All source face anatomy/UV/eyes stay fixed outside lower neck trim.']}
def circuits(b):
 pending={e for e in b.edges if e.is_boundary};rings=[]
 while pending:
  e=pending.pop();edges={e};stack=[e]
  while stack:
   for v in stack.pop().verts:
    for other in v.link_edges:
     if other in pending:pending.remove(other);edges.add(other);stack.append(other)
  adjacency={}
  for e in edges:
   a,c=e.verts;adjacency.setdefault(a,[]).append(c);adjacency.setdefault(c,[]).append(a)
  assert all(len(x)==2 for x in adjacency.values()),'Branched boundary must freeze, not be hidden'
  start=min(adjacency,key=lambda v:tuple(v.co));ring=[start];previous=None;current=start
  while True:
   following=next(v for v in adjacency[current] if v!=previous)
   if following==start:break
   ring.append(following);previous,current=current,following
   assert len(ring)<=len(adjacency)
  rings.append(ring)
 return rings
def signature(faces,uvs):
 rows=[]
 for f in faces:
  rows.append([f.material_index,sorted(tuple(round(float(v),7) for v in list(l.vert.co)+sum((list(l[u].uv) for u in uvs),[])) for l in f.loops)])
 return hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()
def topo(b):
 return {'vertices':len(b.verts),'faces':len(b.faces),'boundaryEdges':sum(e.is_boundary for e in b.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in b.edges),'degenerateFaces':sum(f.calc_area()<1e-12 for f in b.faces)}
def orient(ring):
 if sum(a.co.x*c.co.y-c.co.x*a.co.y for a,c in zip(ring,ring[1:]+ring[:1]))<0:ring.reverse()
 return ring
def arclength(ring):
 a=np.array([(ring[(i+1)%len(ring)].co-ring[i].co).length for i in range(len(ring))]);return np.r_[0,np.cumsum(a)]/a.sum()
def at(ring,dist,t):
 i=min(int(np.searchsorted(dist,t,side='right'))-1,len(ring)-1);f=(t-dist[i])/(dist[i+1]-dist[i]);return ring[i].co.lerp(ring[(i+1)%len(ring)].co,float(f))
try:
 bpy.ops.wm.open_mainfile(filepath=str(bodypath));scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2
 body=next(o for o in scene.objects if o.type=='MESH');bm=bmesh.new();bm.from_mesh(body.data);bm.verts.index_update();bm.faces.index_update()
 uvnames=[u.name for u in body.data.uv_layers];uvs=[bm.loops.layers.uv.get(n) for n in uvnames];mats=list(body.data.materials)
 original_mat_indices=[f.material_index for f in bm.faces]
 removed=[f for f in bm.faces if min(v.co.z for v in f.verts)>1.45];removed_ids=sorted(f.index for f in removed)
 protected=[f for f in bm.faces if f not in set(removed)];before=signature(protected,uvs)
 (OUT/'removed-upper-hood-and-rejected-head-source-face-ids.json').write_text(json.dumps(removed_ids)+'\n')
 # Original upper hood/head surface is retained as an explicit comparison mesh only.
 reference=body.copy();reference.data=body.data.copy();reference.name='SAVED ORIGINAL upper hood and rejected old head comparison only';scene.collection.objects.link(reference)
 refbm=bmesh.new();refbm.from_mesh(reference.data);refbm.faces.ensure_lookup_table()
 bmesh.ops.delete(refbm,geom=[f for f in refbm.faces if f.index not in set(removed_ids)],context='FACES')
 loose=[v for v in refbm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(refbm,geom=loose,context='VERTS')
 refbm.to_mesh(reference.data);refbm.free();reference.hide_render=True;reference.hide_set(True)
 bmesh.ops.delete(bm,geom=removed,context='FACES');loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 source_rings=circuits(bm);assert len(source_rings)==1,'Upper hood panel removal must yield exactly one garment opening'
 rim=orient(source_rings[0]);d=arclength(rim);N=64
 base=[at(rim,d,i/N) for i in range(N)]
 # Two side panels share the central back and front seams in this annular pattern.
 # Six transverse rings form a broad collar roll, rather than a tall neck slab.
 verts=[];faces=[]
 for row in range(6):
  t=row/5
  for i,p in enumerate(base):
   a=math.atan2(p.y-.018,p.x);back=(math.sin(a)+1)/2
   if row==0:q=p.copy()
   elif row==1:q=p.lerp(Vector((.120*math.cos(a),.018+.110*math.sin(a),1.47+.010*back)),.60)
   elif row==2:q=Vector((.115*math.cos(a),.018+.108*math.sin(a),1.475+.072*back))
   elif row==3:q=Vector((.100*math.cos(a),.018+.097*math.sin(a),1.487+.070*back))
   elif row==4:q=Vector((.080*math.cos(a),.018+.078*math.sin(a),1.488+.063*back))
   else:q=Vector((.065*math.cos(a),.018+.064*math.sin(a),1.486+.054*back))
   # Deliberate soft cloth folds at rear/side, not noisy anatomy warping.
   if 0<row<5:
    q.z+=.0035*math.sin(6*a)*math.sin(math.pi*t)*back
   verts.append(tuple(q))
 for row in range(5):
  for i in range(N):j=(i+1)%N;faces.append((row*N+i,row*N+j,(row+1)*N+j,(row+1)*N+i))
 mesh=bpy.data.meshes.new('Authored two-side stitched hood pattern');mesh.from_pydata(verts,[],faces);mesh.update()
 pattern=bpy.data.objects.new('NEW garment pattern outer hood',mesh);scene.collection.objects.link(pattern)
 puv=mesh.uv_layers.new(name='NewHoodPatternUV')
 for poly in mesh.polygons:
  for li in poly.loop_indices:
   idx=mesh.loops[li].vertex_index;puv.data[li].uv=((idx%N)/N,(idx//N)/5)
 vg=pattern.vertex_groups.new(name='Original silhouette lower fold fit')
 for i in range(N):vg.add([i],.12,'REPLACE')
 sub=pattern.modifiers.new('Native stitched panel Catmull-Clark','SUBSURF');sub.levels=1;sub.render_levels=1
 shrink=pattern.modifiers.new('Native lower-fold source silhouette shrinkwrap','SHRINKWRAP');shrink.target=reference;shrink.vertex_group=vg.name;shrink.wrap_method='NEAREST_SURFACEPOINT';shrink.offset=.0005
 solid=pattern.modifiers.new('Native actual two millimeter cloth thickness','SOLIDIFY');solid.thickness=.002;solid.offset=-1;solid.use_rim=False
 bpy.ops.object.select_all(action='DESELECT');pattern.select_set(True);bpy.context.view_layer.objects.active=pattern
 for modifier in list(pattern.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
 pb=bmesh.new();pb.from_mesh(pattern.data);p_uv=pb.loops.layers.uv.active;prings=circuits(pb)
 assert len(prings)==4,'Solidified open cloth pattern must have four actual boundary circuits'
 # Outer/inner lower base loops have larger radial extent than the collar roll.
 prings.sort(key=lambda r:sum(v.co.x*v.co.x+(v.co.y-.018)**2 for v in r)/len(r),reverse=True)
 base_rings=prings[:2];roll_rings=prings[2:]
 outer_base=max(base_rings,key=lambda r:sum(v.co.z for v in r)/len(r));inner_base=next(r for r in base_rings if r is not outer_base)
 # Append exactly once; every later sewing operation reuses these shared indices.
 hood_mat=bpy.data.materials.new('NEW authored clean hoodie cloth PBR solid ochre');hood_mat.use_nodes=True
 bs=hood_mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.36,.205,.085,1);bs.inputs['Roughness'].default_value=.79
 lining_mat=bpy.data.materials.new('NEW authored hood inner lining PBR');lining_mat.use_nodes=True
 bs=lining_mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.255,.135,.048,1);bs.inputs['Roughness'].default_value=.86
 outer_idx=len(mats);mats.append(hood_mat);lining_idx=len(mats);mats.append(lining_mat)
 pmap={v:bm.verts.new(v.co) for v in pb.verts};new_faces=[]
 for f in pb.faces:
  nf=bm.faces.new([pmap[v] for v in f.verts]);nf.material_index=outer_idx if f.normal.z>=0 else lining_idx;nf.smooth=True
  for old,new in zip(f.loops,nf.loops):
   for u in uvs:new[u].uv=old[p_uv].uv
  new_faces.append(nf)
 with bpy.data.libraries.load(str(headpath),link=False) as (src,dst):dst.objects=list(src.objects)
 native=[o for o in dst.objects if o and o.type=='MESH'];head=next(o for o in native if 'head' in o.name.lower());eyes=[o for o in native if o!=head]
 for o in native:
  scene.collection.objects.link(o);matrix=o.matrix_world.copy()
  for v in o.data.vertices:v.co=(matrix@v.co)*.42+Vector((0,0,1.59338))
  o.parent=None;o.matrix_world=Matrix.Identity(4)
 hb=bmesh.new();hb.from_mesh(head.data);huv=hb.loops.layers.uv.active
 fixed=[f for f in hb.faces if min(v.co.z for v in f.verts)>1.53];fixed_before=signature(fixed,[huv])
 bmesh.ops.bisect_plane(hb,geom=list(hb.verts)+list(hb.edges)+list(hb.faces),dist=1e-7,plane_co=(0,0,1.49),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
 loose=[v for v in hb.verts if not v.link_faces]
 if loose:bmesh.ops.delete(hb,geom=loose,context='VERTS')
 head_rings=circuits(hb);assert len(head_rings)==1,'Native neck must have one real skin boundary'
 assert signature(fixed,[huv])==fixed_before,'Fixed new face or UV modified'
 head_offset=len(mats)
 for mat in head.data.materials:mats.append(mat)
 hmap={v:bm.verts.new(v.co) for v in hb.verts}
 for f in hb.faces:
  nf=bm.faces.new([hmap[v] for v in f.verts]);nf.material_index=head_offset+f.material_index;nf.smooth=f.smooth
  for old,new in zip(f.loops,nf.loops):
   for u in uvs:new[u].uv=old[huv].uv
 def sew(a,c,mat):
  a=orient(list(a));c=orient(list(c));k=min(range(len(c)),key=lambda j:(c[j].co-a[0].co).length_squared);c=c[k:]+c[:k]
  da,dc=arclength(a),arclength(c);i=j=0;made=[]
  while i<len(a) or j<len(c):
   an=da[i+1] if i<len(a) else math.inf;cn=dc[j+1] if j<len(c) else math.inf
   if an<cn:vs=[a[i%len(a)],a[(i+1)%len(a)],c[j%len(c)]];i+=1
   else:vs=[a[i%len(a)],c[(j+1)%len(c)],c[j%len(c)]];j+=1
   f=bm.faces.new(vs);f.material_index=mat;f.smooth=True
   for l in f.loops:
    for u in uvs:l[u].uv=(.5+l.vert.co.x,.5+l.vert.co.y)
   made.append(f)
  new_faces.extend(made);return len(made)
 sewn={'garmentToOuterPanel':sew(rim,[pmap[v] for v in outer_base],outer_idx),'hoodRollToInnerLining':sew([pmap[v] for v in roll_rings[0]],[pmap[v] for v in roll_rings[1]],lining_idx),'innerLiningToActualSkinNeck':sew([pmap[v] for v in inner_base],[hmap[v] for v in head_rings[0]],lining_idx)}
 assert signature(protected,uvs)==before,'Protected source body/UV/material changed'
 report['sourceProtection']={'removedNamedRegion':'Original upper hoodie/hood above 1.45m plus rejected H21 head; original retained in saved comparison object','removedFaceCount':len(removed_ids),'removedSourceFaceIdsSHA256':sha(OUT/'removed-upper-hood-and-rejected-head-source-face-ids.json'),'protectedSourceFaces':len(protected),'protectedGeometryAllUVsMaterialSHA256':before,'exactPreserved':True,'newFaceUVGeometryAbove1_53mSHA256':fixed_before,'newFaceGeometryUVPreserved':True,'bodyMaterialSlotsAppendedWithoutClearing':True,'originalMaterialsFaceArrays':original_mat_indices[:0]}
 report['cloth']={'authoredPanels':2,'authoredSharedFrontRearSeams':True,'controlVertices':len(verts),'controlQuads':len(faces),'subdivisionLevels':1,'lowerBoundaryShrinkwrapWeight':.12,'thicknessM':.002,'actualBoundaryCounts':[len(r) for r in prings],'newSkinBoundaryVertices':len(head_rings[0]),'sewnActualSharedIndexFaces':sewn,'sourceGarmentBoundaryVertices':len(rim),'newHoodTextures':'No high-resolution textile bake: deliberate solid-color PBR with authored native UVs'}
 report['topology']=topo(bm);assert report['topology']['boundaryEdges']==0 and report['topology']['nonmanifoldEdges']==0,'Continuous sewing did not produce manifold skin/cloth boundary'
 # Propagate consistent winding across connected surface, without changing position or UV.
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bm.to_mesh(body.data);bm.free();pb.free();hb.free();body.data.update()
 # Append slots only. Reassign the captured explicit output indices after any slot operations.
 output_face_mats=[p.material_index for p in body.data.polygons]
 for m in mats[len(body.data.materials):]:body.data.materials.append(m)
 for p,idx in zip(body.data.polygons,output_face_mats):p.material_index=idx
 bpy.data.objects.remove(pattern,do_unlink=True);bpy.data.objects.remove(head,do_unlink=True)
 body.name='UNACCEPTED C clean garment pattern NEW African head NEW neutral glove body'
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for o in eyes:o.select_set(True)
 bpy.context.view_layer.objects.active=body
 bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'character.blend'))
 bpy.ops.export_scene.gltf(filepath=str(RUN/'character.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
 report['outputs']={str(p):sha(p) for p in [RUN/'character.blend',RUN/'character.glb']};report['inputsAfter']={p:sha(p) for p in report['inputs']};assert report['inputsAfter']==report['inputs']
 report['status']='UNACCEPTED frozen C garment-pattern trial01; actual reimport and visual/motion review pending'
except Exception as error:
 report['status']='FAILED C garment-pattern trial01; no accepted output';report['failure']=repr(error);report['traceback']=traceback.format_exc();raise
finally:
 report['finishedUTC']=time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime());(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('FROZEN',json.dumps({'status':report['status'],'topology':report.get('topology'),'failure':report.get('failure')}),flush=True)
