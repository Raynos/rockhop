"""ONE frozen BMesh local collar fairing and native neck feasibility trial.

CPU only. Source mask is fixed; no graph cut, ellipse, global remesh, rig or bake.
"""
import bpy,bmesh,numpy as np,hashlib,json,time,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
RUN=R/'neck-native/trial02';OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/neck-native/trial02')
RUN.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
if (RUN/'body-head.blend').exists():raise RuntimeError('Frozen trial already exists')
start=time.perf_counter();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bodypath=R/'glove-cleanup/neutral-assembly/body-neutral-hands.blend';headpath=R/'head-cleanup/mpfb-v6-native-male/head.blend';maskpath=R/'collar-trial1/collar-selection.npz'
inputs={str(p):sha(p) for p in [bodypath,headpath,maskpath]}
report={'status':'UNACCEPTED native collar integration trial02','inputs':inputs,'recipeSHA256':sha(Path(__file__)),'settings':{'headUniformScale':.42,'headWorldZOffset':1.59338,'headWorldYOffset':0,'newNeckCutWorldZ':1.49,'sourceMatchToleranceM':2e-6,'localFairBandRadiusM':.035,'maximumDisplacementM':.012,'faceAdjacencyRings':4,'fairingIterations':0,'fairingLambda':0,'fairing':'Fixed FOUR actual face-adjacency rings; every vertex within35mm; original outer boundary fixed','bridge':'Actual two boundary circuits, arclength zipper and one shared-index inner-facing ring; no ellipse'},'limits':['Appearance, texture seam, normal continuity, neck rotation/bending and full rig remain unaccepted/unmeasured.','Neutral static geometry feasibility only; no historical head donor, global remesh, rig, physics or contacts.']}

def loops(b):
 pending={e for e in b.edges if e.is_boundary};result=[]
 while pending:
  seed=pending.pop();edges={seed};todo=[seed]
  while todo:
   for v in todo.pop().verts:
    for e in v.link_edges:
     if e in pending:pending.remove(e);edges.add(e);todo.append(e)
  adj={}
  for e in edges:
   for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
  if any(len(n)!=2 for n in adj.values()):raise RuntimeError('Boundary branches; do not fake a circuit')
  first=min(adj,key=lambda v:tuple(v.co));ring=[first];previous=None;current=first
  while True:
   nxt=next(x for x in adj[current] if x!=previous)
   if nxt==first:break
   ring.append(nxt);previous,current=current,nxt
   if len(ring)>len(adj):raise RuntimeError('Boundary does not close')
  result.append(ring)
 return sorted(result,key=len,reverse=True)

def facehash(faces,uv):
 rows=sorted((f.material_index,sorted(tuple(round(float(x),7) for x in list(l.vert.co)+list(l[uv].uv)) for l in f.loops)) for f in faces)
 return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()

def topology(b):
 b.verts.index_update();b.faces.index_update();winding=[]
 for e in b.edges:
  if e.is_manifold:
   directions=[]
   for f in e.link_faces:
    l=next(l for l in f.loops if l.edge==e);directions.append(l.vert==e.verts[0])
   if directions[0]==directions[1]:winding.append(e.index)
 components=[]
 pending=set(b.verts)
 while pending:
  seed=pending.pop();stack=[seed];count=1
  while stack:
   current=stack.pop()
   for e in current.link_edges:
    other=e.other_vert(current)
    if other in pending:pending.remove(other);stack.append(other);count+=1
  components.append(count)
 return {'vertices':len(b.verts),'faces':len(b.faces),'boundaryEdges':sum(e.is_boundary for e in b.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in b.edges),'inconsistentWindingEdges':len(winding),'componentVertexCounts':sorted(components,reverse=True)}

try:
 bpy.ops.wm.open_mainfile(filepath=str(bodypath));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');bm=bmesh.new();bm.from_mesh(body.data);uv=bm.loops.layers.uv.active
 assert not body.modifiers,'Neutral source must be unrigged static geometry'
 data=np.load(maskpath);v=data['verticesBlender'];f=data['faces'];keep=data['retainedFaceMask'];tree=KDTree(len(f))
 for i,ids in enumerate(f):tree.insert(v[ids].mean(0),i)
 tree.balance();delete=[];removed=[]
 for face in bm.faces:
  if len(face.verts)!=3:continue
  points=np.array([x.co for x in face.verts]);co,i,d=tree.find(points.mean(0))
  if d>2e-6:continue
  if max(min(np.linalg.norm(q-p) for p in v[f[i]]) for q in points)>2e-6:continue
  if not keep[i]:delete.append(face);removed.append(i)
 assert len(set(removed))==int((~keep).sum()),'Exact source deletion did not match every retained-mask source face'
 bmesh.ops.delete(bm,geom=delete,context='FACES');loose=[x for x in bm.verts if not x.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 boundary=loops(bm);assert len(boundary)==1,'Fixed source mask must yield one actual hood circuit'
 rim=boundary[0];rim_tree=KDTree(len(rim))
 for i,x in enumerate(rim):rim_tree.insert(x.co,i)
 rim_tree.balance();band=[];original={x:x.co.copy() for x in bm.verts};weights={}
 for x in bm.verts:
  d=rim_tree.find(x.co)[2]
  if d<.035:band.append(x);weights[x]=(1-d/.035)**2
 protected=[face for face in bm.faces if not any(x in weights for x in face.verts)];protected_before=facehash(protected,uv)
  # Exactly FOUR source face-adjacency rings, no adaptive broadening or fill.
 strip=set();frontier={face for x in rim for face in x.link_faces}
 ring_counts=[]
 for ring_number in range(4):
  admitted={face for face in frontier if face not in strip and all(x in weights for x in face.verts)}
  ring_counts.append(len(admitted));strip.update(admitted)
  frontier={other for face in admitted for e in face.edges for other in e.link_faces if other not in strip}
 strip_rows=[sorted([list(x.co) for x in face.verts]) for face in strip]
 strip_sha=hashlib.sha256(json.dumps(sorted(strip_rows),separators=(',',':')).encode()).hexdigest()
 assert strip,'Fixed bounded strip empty; stop'
 bmesh.ops.delete(bm,geom=list(strip),context='FACES')
 loose=[x for x in bm.verts if not x.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 boundary=loops(bm);assert len(boundary)==1,'Fixed FOUR-ring strip yields multiple holes; stop, no widening/fill'
 rim=boundary[0]
 assert facehash(protected,uv)==protected_before,'Outside local band source corners/material/UV changed'
 report['body']={'removedHistoricalHeadTriangles':len(removed),'sourceDeletedTriangleOrdinalSHA256':hashlib.sha256(np.asarray(sorted(removed),dtype=np.int32).tobytes()).hexdigest(),'retainedMaskDeleteCount':int((~keep).sum()),'actualBoundaryVertices':len(rim),'localFairBandVertices':len(band),'maximumDisplacementM':0,'removedLocalSourceFaces':len(strip),'fourRingFaceCounts':ring_counts,'removedStripCornerSHA256':strip_sha,'outsideBandRetainedFaces':len(protected),'outsideBandCornerMaterialUVSHA256':protected_before,'outsideBandExactPreservation':True,'topologyBeforeJoin':topology(bm),'fairingOriginalBoundaryBounds':[list(Vector([min(original[x][i] for x in rim) for i in range(3)])),list(Vector([max(original[x][i] for x in rim) for i in range(3)]))],'fairingNewBoundaryBounds':[list(Vector([min(x.co[i] for x in rim) for i in range(3)])),list(Vector([max(x.co[i] for x in rim) for i in range(3)]))]}
 # Append immutable NEW native head/eyes into this trial; copying avoids source saves.
 with bpy.data.libraries.load(str(headpath),link=False) as (src,dst):dst.objects=list(src.objects)
 native=[o for o in dst.objects if o and o.type=='MESH'];head=next(o for o in native if 'head' in o.name.lower());eyes=[o for o in native if o!=head]
 for o in native:
  bpy.context.scene.collection.objects.link(o)
  matrix=o.matrix_world.copy()
  for x in o.data.vertices:x.co=(matrix@x.co)*.42+Vector((0,0,1.59338))
  o.parent=None;o.matrix_world=Matrix.Identity(4)
 hb=bmesh.new();hb.from_mesh(head.data);huv=hb.loops.layers.uv.active
 fixed_head=[face for face in hb.faces if min(x.co.z for x in face.verts)>1.53];head_before=facehash(fixed_head,huv)
 bmesh.ops.bisect_plane(hb,geom=list(hb.verts)+list(hb.edges)+list(hb.faces),dist=1e-7,plane_co=(0,0,1.49),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
 loose=[x for x in hb.verts if not x.link_faces]
 if loose:bmesh.ops.delete(hb,geom=loose,context='VERTS')
 neck_loops=loops(hb);assert len(neck_loops)==1,'New native neck trim yields multiple holes; stop instead of faking join'
 neck=neck_loops[0];assert max(abs(x.co.z-1.49) for x in neck)<2e-6,'Unexpected native hole outside neck cut'
 assert facehash(fixed_head,huv)==head_before,'New face UV/geometry changed outside neck trim'
 # Preserve original body slots. New head and lining have separate explicit slots.
 mats=list(body.data.materials);skin_index=len(mats);mats.append(head.data.materials[0])
 lining=bpy.data.materials.new('UNACCEPTED native collar inside-facing');lining.use_nodes=True
 bs=lining.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.14,.09,.035,1);bs.inputs['Roughness'].default_value=.8
 lining_index=len(mats);mats.append(lining)
 mapped={x:bm.verts.new(x.co) for x in hb.verts}
 for face in hb.faces:
  target=bm.faces.new([mapped[x] for x in face.verts]);target.material_index=skin_index;target.smooth=face.smooth
  for old,new in zip(face.loops,target.loops):new[uv].uv=old[huv].uv
 skin_ring=[mapped[x] for x in neck]
 def area(r):return sum(a.co.x*b.co.y-b.co.x*a.co.y for a,b in zip(r,r[1:]+r[:1]))
 if area(rim)*area(skin_ring)<0:skin_ring.reverse()
 # Align the existing circuits at a nearest real vertex, then use actual arclength.
 seed=min(range(len(skin_ring)),key=lambda i:(skin_ring[i].co-rim[0].co).length_squared);skin_ring=skin_ring[seed:]+skin_ring[:seed]
 def lengths(r):
  a=np.array([(r[(i+1)%len(r)].co-r[i].co).length for i in range(len(r))]);return np.concatenate([[0],np.cumsum(a)])/a.sum()
 sr=lengths(skin_ring);rr=lengths(rim)
 def at(t):
  j=min(int(np.searchsorted(sr,t,side='right'))-1,len(skin_ring)-1);u=(t-sr[j])/(sr[j+1]-sr[j]);return skin_ring[j].co.lerp(skin_ring[(j+1)%len(skin_ring)].co,float(u))
 mid=[bm.verts.new(x.co.lerp(at(float(rr[i])),.35)) for i,x in enumerate(rim)]
 bridge=[]
 def newface(vertices):
  face=bm.faces.new(vertices);face.material_index=lining_index;face.smooth=True
  for l in face.loops:l[uv].uv=(.5+l.vert.co.x,.5+l.vert.co.y)
  bridge.append(face)
 for i in range(len(rim)):j=(i+1)%len(rim);newface([rim[i],rim[j],mid[j],mid[i]])
 i=j=0
 while i<len(mid) or j<len(skin_ring):
  an=rr[i+1] if i<len(mid) else math.inf;bn=sr[j+1] if j<len(skin_ring) else math.inf
  if an<bn:newface([mid[i%len(mid)],mid[(i+1)%len(mid)],skin_ring[j%len(skin_ring)]]);i+=1
  else:newface([mid[i%len(mid)],skin_ring[(j+1)%len(skin_ring)],skin_ring[j%len(skin_ring)]]);j+=1
 # Orient only the new inner-facing faces against an actual retained hood edge.
 for e in bm.edges:
  if set(e.verts)=={rim[0],rim[1]}:
   original_face=next(face for face in e.link_faces if face not in bridge);added_face=next(face for face in e.link_faces if face in bridge)
   direction=lambda face:next(l.vert for l in face.loops if l.edge==e)
   if direction(original_face)==direction(added_face):
    for face in bridge:face.normal_flip()
   break
 assert facehash(protected,uv)==protected_before,'Outside body band changed during sewing'
 report['head']={'neckBoundaryVertices':len(neck),'neckTrimWorldZ':1.49,'unchangedFaceAboveWorldZ':1.53,'unchangedHeadFaceCount':len(fixed_head),'unchangedHeadFaceCornerUVSHA256':head_before,'faceUVAndGeometryPreserved':True,'crownWorldZ':max(x.co.z for x in hb.verts),'eyesRetainedObjects':[o.name for o in eyes]}
 report['join']={'sharedActualBodyBoundaryVertices':len(rim),'sharedNewHeadBoundaryVertices':len(neck),'sharedInsideFacingRingVertices':len(mid),'newInsideFacingFaces':len(bridge),'noEllipticalCap':True,'headAndBodySingleMesh':True,'topologyAfterJoin':topology(bm),'skinMaterialIndex':skin_index,'liningMaterialIndex':lining_index}
 # Keep original slots and append NEW slots BEFORE conversion; explicitly restore every face index AFTER.
 while len(body.data.materials)<len(mats):body.data.materials.append(mats[len(body.data.materials)])
 bm.faces.index_update();material_array=np.array([face.material_index for face in bm.faces],dtype=np.int32)
 bm.to_mesh(body.data);bm.free();hb.free();body.data.update()
 assert len(material_array)==len(body.data.polygons)
 body.data.polygons.foreach_set('material_index',material_array)
 report['actualSavedMaterialFaceCounts']={str(i):int((material_array==i).sum()) for i in range(len(mats))}
 assert all(count>0 for count in report['actualSavedMaterialFaceCounts'].values()),'Actual intended material region missing'
 np.savez(RUN/'intended-material-indices.npz',materialIndex=material_array)
 body.name='UNACCEPTED NEW native head and neutral hand body shared collar';bpy.data.objects.remove(head,do_unlink=True)
 for face in body.data.polygons:face.use_smooth=True
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for o in eyes:o.select_set(True)
 bpy.context.view_layer.objects.active=body
 bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'body-head.blend'))
 bpy.ops.export_scene.gltf(filepath=str(RUN/'body-head.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
 report['outputs']={str(p):sha(p) for p in [RUN/'body-head.blend',RUN/'body-head.glb']}
 report['inputsAfter']={p:sha(Path(p)) for p in inputs};assert inputs==report['inputsAfter']
 report['status']='UNACCEPTED frozen second/final native BMesh trial; independent export/visual checks pending'
except Exception as e:
 report['status']='FAILED native collar trial02; no accepted join';report['failure']=repr(e)
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');raise
report['wallSeconds']=time.perf_counter()-start;(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('TRIAL_FROZEN',json.dumps({'status':report['status'],'join':report.get('join')}),flush=True)
