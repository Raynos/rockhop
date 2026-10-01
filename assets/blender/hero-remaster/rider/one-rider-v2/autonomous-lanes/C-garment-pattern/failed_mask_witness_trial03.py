"""Exact failed source-mask replay for evidence only; no correction or new panel.

Settings identical to frozen trial03. Saves compact IDs and actual failure state.
"""
import bpy,bmesh,numpy as np,json,hashlib,datetime
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=R/'autonomous-lanes/C-garment-pattern/trial03';O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial03')
assert not (RUN/'failed-mask-witness.blend').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();bp=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';hp=R/'head-cleanup/mpfb-v8-palette/african/head.blend';mask=R/'collar-trial1/collar-selection.npz';inputs={str(p):sha(p) for p in [bp,hp,mask]}
bpy.ops.wm.open_mainfile(filepath=str(bp));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');b=bmesh.new();b.from_mesh(body.data);b.faces.index_update();face_origin={q:q.index for q in b.faces}
d=np.load(mask);v=d['verticesBlender'];f=d['faces'];keep=d['retainedFaceMask'];t=KDTree(len(f))
for i,ids in enumerate(f):t.insert(v[ids].mean(0),i)
t.balance();deleted=[]
for q in b.faces:
 if len(q.verts)!=3:continue
 pts=np.array([x.co for x in q.verts]);_,i,dist=t.find(pts.mean(0))
 if dist<2e-6 and not keep[i] and max(min(np.linalg.norm(p-qq) for qq in v[f[i]]) for p in pts)<2e-6:deleted.append(q)
assert len(deleted)==13657
headids=[face_origin[q] for q in deleted];bmesh.ops.delete(b,geom=deleted,context='FACES');loose=[v for v in b.verts if not v.link_faces]
if loose:bmesh.ops.delete(b,geom=loose,context='VERTS')
oldrim=set(v for e in b.edges if e.is_boundary for v in e.verts);selected=set(oldrim)
for layer in range(2):selected.update(e.other_vert(v) for v in list(selected) for e in v.link_edges)
strip={q for v in selected for q in v.link_faces};pinch=[q for q in b.faces if face_origin[q] in {19285,19904}];assert len(pinch)==2;strip.update(pinch);stripids=[face_origin[q] for q in strip];protected=[face_origin[q] for q in b.faces if q not in strip]
bmesh.ops.delete(b,geom=list(strip),context='FACES');loose=[v for v in b.verts if not v.link_faces]
if loose:bmesh.ops.delete(b,geom=loose,context='VERTS')
boundary=[e for e in b.edges if e.is_boundary];vertices=set(v for e in boundary for v in e.verts);branches=[{'position':list(v.co),'boundaryDegree':sum(e.is_boundary for e in v.link_edges),'linkedFaceCount':len(v.link_faces)} for v in vertices if sum(e.is_boundary for e in v.link_edges)!=2]
assert not branches,'Exact authorized correction must remove the old pinch'
adj={}
for e in boundary:
 a,c=e.verts;adj.setdefault(a,[]).append(c);adj.setdefault(c,[]).append(a)
remaining=set(adj);circuits=[]
while remaining:
 start=min(remaining,key=lambda v:tuple(v.co));ring=[start];prev=None;cur=start
 while True:
  nxt=next(v for v in adj[cur] if v!=prev)
  if nxt==start:break
  ring.append(nxt);prev,cur=cur,nxt
 remaining.difference_update(ring);pts=np.asarray([list(v.co) for v in ring]);circuits.append({'vertices':len(ring),'bounds':[pts.min(0).tolist(),pts.max(0).tolist()]})
assert len(circuits)>1,'Exact replay must expose the second circuit failure'
remaining=set(b.faces);components=[]
while remaining:
 seed=remaining.pop();stack=[seed];part=[seed]
 while stack:
  q=stack.pop()
  for e in q.edges:
   for other in e.link_faces:
    if other in remaining:remaining.remove(other);part.append(other);stack.append(other)
 pts=np.asarray([list(v.co) for q in part for v in q.verts]);components.append({'faces':len(part),'sourceFaceIdsSHA256':hashlib.sha256(np.asarray(sorted(face_origin[q] for q in part),np.int32).tobytes()).hexdigest(),'bounds':[pts.min(0).tolist(),pts.max(0).tolist()]})
np.savez_compressed(RUN/'failed-source-mask.npz',removedOldHeadFaceIds=np.asarray(headids,np.int32),removedTwoStarHoodFaceIds=np.asarray(sorted(stripids),np.int32),protectedSourceFaceIds=np.asarray(sorted(protected),np.int32),actualBoundarySegments=np.asarray([[list(v.co) for v in e.verts] for e in boundary],np.float32))
b.to_mesh(body.data);b.free();body.data.update();body.name='FAILED C modular two-star source-mask witness ONLY no new cloth'
with bpy.data.libraries.load(str(hp),link=False) as (src,dst):dst.objects=list(src.objects)
native=[o for o in dst.objects if o and o.type=='MESH']
for o in native:
 bpy.context.scene.collection.objects.link(o);matrix=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Translation(Vector((0,0,1.59338)))@Matrix.Scale(.42,4)@matrix
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in native:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'failed-mask-witness.blend'));bpy.ops.export_scene.gltf(filepath=str(RUN/'failed-mask-witness.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
report={'status':'FAILED SOURCE MASK WITNESS ONLY; exact same two-star settings, no new cloth construction or correction','actualReplayPurpose':'Read-only source replay to freeze failure geometry and compact IDs; not a second construction attempt','removedOldHeadFaces':len(headids),'removedTwoStarClothFaces':len(stripids),'protectedSourceFaces':len(protected),'actualBoundaryEdges':len(boundary),'actualBoundaryBranchVertices':branches,'actualBoundaryCircuits':circuits,'faceConnectedComponents':components,'authorizedExactExtraFaces':[19285,19904],'sourceMaskSHA256':sha(RUN/'failed-source-mask.npz'),'sourceMaskPath':str(RUN/'failed-source-mask.npz'),'originalFailureReportSHA256':sha(O/'report.json'),'sources':inputs,'sourcesAfter':{p:sha(p) for p in inputs},'outputs':{str(p):sha(p) for p in [RUN/'failed-mask-witness.blend',RUN/'failed-mask-witness.glb']},'finishedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
assert inputs==report['sourcesAfter'];(O/'failed-mask-witness.json').write_text(json.dumps(report,indent=2)+'\n');print('EXACT_FAILED_MASK',len(circuits),len(boundary),len(stripids),flush=True)
