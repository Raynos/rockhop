"""Lane A: one explicit seam-landmark folded quad panel, native Blender only.

No radius/ring cut, remesh, ellipse, skeleton, source edits or GPU workload.
"""
import bpy, bmesh, numpy as np, json, hashlib, time, math, heapq
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
RUN=R/'autonomous-lanes/A-manual-panel/trial01'
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-manual-panel/trial01')
RUN.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'report.json').exists(): raise RuntimeError('Frozen trial exists')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bodypath=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend'
headpath=R/'head-cleanup/mpfb-v8-palette/african/head.blend'
maskpath=R/'collar-trial1/collar-selection.npz'
inputs={str(p):sha(p) for p in [bodypath,headpath,maskpath]}
start=time.perf_counter()
report={'status':'UNACCEPTED first explicit seam-landmark panel', 'inputs':inputs,
 'recipeSHA256':sha(Path(__file__)), 'deadlineUTC':'2026-10-01T02:17:00Z',
 'settings':{'landmarkIDs':[11791,5144,5237,14112,3282,14048,14019,13615],
 'pathCost':'source edge length * (1 + 4 * squared distance to explicit landmark segment / segment length squared)',
 'headScale':.42,'headOffset':[0,0,1.59338],'neckTrimZ':1.49,
 'foldAuthorship':'Eight explicit cloth crease controls, piecewise straight interpolation by source seam arc length',
 'sharedSourceCoordinates':'No source vertex displacement outside the replaced panel'},
 'limits':['Unrigged static character; parent appearance judgment required.',
 'Neck deformation, texture/normal continuity in motion, contacts and gameplay remain unmeasured.']}

def circuits(bm):
 pending={e for e in bm.edges if e.is_boundary}; rings=[]
 while pending:
  seed=pending.pop(); edges={seed}; stack=[seed]
  while stack:
   for v in stack.pop().verts:
    for e in v.link_edges:
     if e in pending: pending.remove(e); edges.add(e); stack.append(e)
  adj={}
  for e in edges:
   for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
  if any(len(n)!=2 for n in adj.values()):raise RuntimeError('Actual boundary has a branch')
  first=min(adj,key=lambda v:tuple(v.co)); ring=[first];prev=None;cur=first
  while True:
   nxt=next(v for v in adj[cur] if v!=prev)
   if nxt==first:break
   ring.append(nxt);prev,cur=cur,nxt
   if len(ring)>len(adj):raise RuntimeError('Boundary fails closure')
  rings.append(ring)
 return rings

def facehash(faces,layers):
 rows=[]
 for f in faces:
  corners=[tuple(float(x) for x in list(l.vert.co)+[q for uv in layers for q in l[uv].uv]) for l in f.loops]
  rows.append((f.material_index,tuple(sorted(corners))))
 return hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()

def topo(bm):
 winding=0
 for e in bm.edges:
  if e.is_manifold:
   directions=[next(l.vert for l in f.loops if l.edge==e)==e.verts[0] for f in e.link_faces]
   winding+=directions[0]==directions[1]
 return {'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'inconsistentWindingEdges':winding}

try:
 bpy.ops.wm.open_mainfile(filepath=str(bodypath))
 body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
 assert not body.modifiers,'Source must be static'
 bm=bmesh.new();bm.from_mesh(body.data)
 bodyuvs=list(bm.loops.layers.uv.values()); sourceActiveUV=body.data.uv_layers.active_index
 data=np.load(maskpath);vertices=data['verticesBlender'];triangles=data['faces'];keep=data['retainedFaceMask'];tree=KDTree(len(triangles))
 for i,ids in enumerate(triangles):tree.insert(vertices[ids].mean(0),i)
 tree.balance();deleted=[];matched=[]
 for face in bm.faces:
  if len(face.verts)!=3:continue
  points=np.array([v.co for v in face.verts]);co,i,d=tree.find(points.mean(0))
  if d<2e-6 and not keep[i] and max(min(np.linalg.norm(q-p) for p in vertices[triangles[i]]) for q in points)<2e-6:deleted.append(face);matched.append(i)
 assert len(set(matched))==int((~keep).sum())
 bmesh.ops.delete(bm,geom=deleted,context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.verts.index_update();bm.verts.ensure_lookup_table();bm.faces.index_update();bm.edges.index_update()
 originalFaces=list(bm.faces);sourceFaceIDs={f:f.index for f in bm.faces}
 rim=circuits(bm);assert len(rim)==1
 oldrim=set(rim[0]);anchorIDs=report['settings']['landmarkIDs'];anchors=[bm.verts[i] for i in anchorIDs]
 expected=json.loads((OUT.parent/'setup.json').read_text())['landmarks']
 assert all((a.co-Vector(e['actualWorldM'])).length<2e-6 for a,e in zip(anchors,expected))
 edgeLookup={frozenset(e.verts):e for e in bm.edges}
 paths=[];used=set();anchorSet=set(anchors)
 for a,b in zip(anchors,anchors[1:]+anchors[:1]):
  forbidden=oldrim|(used-{a,b})|(anchorSet-{a,b})
  delta=b.co-a.co;lengthSquared=delta.length_squared
  def cost(e):
   midpoint=(e.verts[0].co+e.verts[1].co)*.5
   t=max(0,min(1,(midpoint-a.co).dot(delta)/lengthSquared));d=(midpoint-(a.co+delta*t)).length_squared
   return e.calc_length()*(1+4*d/lengthSquared)
  queue=[(0,a.index)];dist={a:0};previous={};visited=set()
  while queue:
   value,idx=heapq.heappop(queue);cur=bm.verts[idx]
   if cur in visited:continue
   visited.add(cur)
   if cur==b:break
   for edge in cur.link_edges:
    other=edge.other_vert(cur)
    if other in forbidden or not edge.is_manifold or any(f.material_index!=0 for f in edge.link_faces):continue
    proposal=value+cost(edge)
    if proposal<dist.get(other,math.inf):dist[other]=proposal;previous[other]=cur;heapq.heappush(queue,(proposal,other.index))
  if b not in previous:raise RuntimeError('Explicit landmark segment has no protected source-edge route')
  path=[b]
  while path[-1]!=a:path.append(previous[path[-1]])
  path.reverse();paths.append(path);used.update(path)
 seam=[v for path in paths for v in path[:-1]]
 seamEdges={edgeLookup[frozenset((a,b))] for a,b in zip(seam,seam[1:]+seam[:1])}
 degrees={v:sum(v in e.verts for e in seamEdges) for v in seam}
 assert len(seam)==len(set(seam)) and len(seamEdges)==len(seam) and set(degrees.values())=={2}
 assert not oldrim.intersection(seam)
 report['explicitSeam']={'landmarks':expected,'orderedSourceVertexIDs':[v.index for v in seam], 'segmentSourceVertexIDs':[[v.index for v in p] for p in paths],'closedSimpleCircuit':True,'allDegreeTwo':True,'oldRimIntersectionCount':0}
 (OUT/'seam-guard.json').write_text(json.dumps(report['explicitSeam'],indent=2)+'\n')
 # Replace only the cloth region bounded by this actual authored source-edge seam.
 inside=set(f for v in oldrim for f in v.link_faces);todo=list(inside)
 while todo:
  face=todo.pop()
  for edge in face.edges:
   if edge in seamEdges:continue
   for other in edge.link_faces:
    if other not in inside:inside.add(other);todo.append(other)
 assert inside and len(inside)<len(originalFaces)//5,'Seam must contain a small local panel'
 assert all(f.material_index==0 for f in inside),'Never remove glove/anatomy materials'
 protected=[f for f in originalFaces if f not in inside];before=facehash(protected,bodyuvs)
 report['panelRemoval']={'sourceFaceIDs':[sourceFaceIDs[f] for f in inside],'faces':len(inside),'protectedSourceFaces':len(protected),'protectedAllUVMaterialCoordinatesSHA256':before}
 bmesh.ops.delete(bm,geom=list(inside),context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 boundary=circuits(bm);assert len(boundary)==1 and set(boundary[0])==set(seam),'Replacement boundary must equal recorded explicit seam'
 # Load NEW native head with its own native atlas and eye objects.
 with bpy.data.libraries.load(str(headpath),link=False) as (src,dst):dst.objects=list(src.objects)
 native=[o for o in dst.objects if o and o.type=='MESH'];head=next(o for o in native if 'head' in o.name.lower());eyes=[o for o in native if o!=head]
 for obj in native:
  bpy.context.scene.collection.objects.link(obj);obj.data=obj.data.copy();transform=obj.matrix_world.copy()
  for v in obj.data.vertices:v.co=(transform@v.co)*.42+Vector((0,0,1.59338))
  obj.parent=None;obj.matrix_world=Matrix.Identity(4)
 hb=bmesh.new();hb.from_mesh(head.data);huv=hb.loops.layers.uv.active
 fixed=[f for f in hb.faces if min(v.co.z for v in f.verts)>1.53];headBefore=facehash(fixed,[huv])
 bmesh.ops.bisect_plane(hb,geom=list(hb.verts)+list(hb.edges)+list(hb.faces),dist=1e-7,plane_co=(0,0,1.49),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
 loose=[v for v in hb.verts if not v.link_faces]
 if loose:bmesh.ops.delete(hb,geom=loose,context='VERTS')
 necks=circuits(hb);assert len(necks)==1;neck=necks[0]
 assert max(abs(v.co.z-1.49) for v in neck)<2e-6 and facehash(fixed,[huv])==headBefore
 nativeUV=bm.loops.layers.uv.new('NativeHeadUV')
 skin=head.data.materials[0].copy();skin.name='African native atlas, preserved face UV'
 for node in skin.node_tree.nodes:
  if node.type=='UVMAP':node.uv_map='NativeHeadUV'
 # Direct image textures receive an explicit matching native UV map.
 uvnode=skin.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='NativeHeadUV'
 for node in list(skin.node_tree.nodes):
  if node.type=='TEX_IMAGE':skin.node_tree.links.new(uvnode.outputs['UV'],node.inputs['Vector'])
 body.data.materials.append(skin);skinIndex=len(body.data.materials)-1
 cloth=bpy.data.materials.new('Authored mustard collar cloth panel');cloth.use_nodes=True
 shader=cloth.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.31,.17,.060,1);shader.inputs['Roughness'].default_value=.84
 body.data.materials.append(cloth);clothIndex=len(body.data.materials)-1
 lining=bpy.data.materials.new('Authored folded inner collar lining');lining.use_nodes=True
 shader=lining.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.13,.067,.023,1);shader.inputs['Roughness'].default_value=.9
 body.data.materials.append(lining);liningIndex=len(body.data.materials)-1
 mapping={v:bm.verts.new(v.co) for v in hb.verts}
 for f in hb.faces:
  new=bm.faces.new([mapping[v] for v in f.verts]);new.material_index=skinIndex;new.smooth=True
  for old,loop in zip(f.loops,new.loops):loop[nativeUV].uv=old[huv].uv
 skinRing=[mapping[v] for v in neck]
 # Eight garment crease points intentionally authored independently of old sawtooth rim.
 foldControls=[Vector(p) for p in [(0,-.070,1.485),(-.064,-.060,1.492),(-.076,-.005,1.527),(-.060,.061,1.545),(0,.080,1.548),(.060,.061,1.545),(.076,-.005,1.527),(.064,-.060,1.492)]]
 foldCoordinates=[]
 for i,path in enumerate(paths):
  segment=[(b.co-a.co).length for a,b in zip(path,path[1:])];total=sum(segment);travel=0
  for j,v in enumerate(path[:-1]):
   foldCoordinates.append(foldControls[i].lerp(foldControls[(i+1)%8],travel/total));travel+=segment[j]
 folds=[bm.verts.new(p) for p in foldCoordinates]
 report['fold']={'explicitWorldControlsM':[list(p) for p in foldControls],'quadStripVertices':len(folds),'noOldRimCoordinatesUsed':True,'noEllipse':True}
 panel=[]
 def addface(vs,material):
  f=bm.faces.new(vs);f.material_index=material;f.smooth=True
  for l in f.loops:
   for uv in bodyuvs:l[uv].uv=(l.vert.co.x+.5,l.vert.co.y+.5)
  panel.append(f);return f
 for i in range(len(seam)):
  j=(i+1)%len(seam);addface([seam[i],seam[j],folds[j],folds[i]],clothIndex)
 area=lambda ring:sum(a.co.x*b.co.y-b.co.x*a.co.y for a,b in zip(ring,ring[1:]+ring[:1]))
 if area(folds)*area(skinRing)<0:skinRing.reverse()
 seed=min(range(len(skinRing)),key=lambda i:(skinRing[i].co-folds[0].co).length_squared);skinRing=skinRing[seed:]+skinRing[:seed]
 def lengths(r):
  values=np.array([(r[(i+1)%len(r)].co-r[i].co).length for i in range(len(r))]);return np.concatenate([[0],np.cumsum(values)])/values.sum()
 fr=lengths(folds);sr=lengths(skinRing);i=j=0
 while i<len(folds) or j<len(skinRing):
  an=fr[i+1] if i<len(folds) else math.inf;bn=sr[j+1] if j<len(skinRing) else math.inf
  if an<bn:addface([folds[i%len(folds)],folds[(i+1)%len(folds)],skinRing[j%len(skinRing)]],liningIndex);i+=1
  else:addface([folds[i%len(folds)],skinRing[(j+1)%len(skinRing)],skinRing[j%len(skinRing)]],liningIndex);j+=1
 # Recalculate only newly authored faces/new head; retained body winding is untouched.
 bmesh.ops.recalc_face_normals(bm,faces=panel+[f for f in bm.faces if f.material_index==skinIndex])
 assert facehash(protected,bodyuvs)==before,'Protected source changed'
 report['head']={'faceCoordinatesAndUVPreservedAboveZ':1.53,'protectedFaceHash':headBefore,'protectedFaces':len(fixed),'neckBoundaryVertices':len(neck),'eyes':[o.name for o in eyes]}
 report['join']={'sourceSeamVertices':len(seam),'foldVertices':len(folds),'nativeNeckVertices':len(neck),'newPanelFaces':len(panel),'topology':topo(bm),'sharedVertexJoin':True}
 assert report['join']['topology']['boundaryEdges']==0 and report['join']['topology']['nonmanifoldEdges']==0,'Joined surface must be manifold'
 assert report['join']['topology']['inconsistentWindingEdges']==0,'Shared seam winding disagrees'
 assignments=[f.material_index for f in bm.faces];bm.to_mesh(body.data);bm.free();hb.free()
 for p,m in zip(body.data.polygons,assignments):p.material_index=m
 body.data.uv_layers.active_index=sourceActiveUV;body.data.update();body.name='UNACCEPTED lane A explicit seam-panel rider'
 bpy.data.objects.remove(head,do_unlink=True)
 report['materials']={'names':[m.name for m in body.data.materials],'polygonCounts':{m.name:sum(p.material_index==i for p in body.data.polygons) for i,m in enumerate(body.data.materials)},'sourceSlotsNeverCleared':True,'activeBodyUV':body.data.uv_layers.active.name,'nativeFaceUV':'NativeHeadUV'}
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 for eye in eyes:eye.select_set(True)
 bpy.context.view_layer.objects.active=body
 bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'rider.blend'))
 bpy.ops.export_scene.gltf(filepath=str(RUN/'rider.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
 report['outputs']={str(p):sha(p) for p in [RUN/'rider.blend',RUN/'rider.glb']}
 report['inputsAfter']={p:sha(Path(p)) for p in inputs};assert inputs==report['inputsAfter']
 report['status']='UNACCEPTED first panel frozen; export/reimport appearance checks pending'
except Exception as error:
 report['status']='FAILED first explicit seam-landmark panel, no accepted rider';report['failure']=repr(error)
 report['wallSeconds']=time.perf_counter()-start
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 raise
report['wallSeconds']=time.perf_counter()-start
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('LANE_A_TRIAL_FROZEN',json.dumps(report['join']),flush=True)
