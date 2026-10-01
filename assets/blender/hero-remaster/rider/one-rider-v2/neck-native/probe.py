"""Read-only native neck source/mask correspondence probe, CPU only."""
import bpy,bmesh,numpy as np,json,hashlib
from mathutils.kdtree import KDTree
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/neck-native')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bodypath=R/'glove-cleanup/neutral-assembly/body-neutral-hands.blend';headpath=R/'head-cleanup/mpfb-v6-native-male/head.blend';maskpath=R/'collar-trial1/collar-selection.npz'
data=np.load(maskpath);v=data['verticesBlender'];f=data['faces'];keep=data['retainedFaceMask']
def sig(points):return tuple(sorted(tuple(round(float(x),5) for x in p) for p in points))
source={sig(v[ids]):(i,keep[i],v[ids]) for i,ids in enumerate(f)}
tree=KDTree(len(f))
for i,ids in enumerate(f):tree.insert(v[ids].mean(0),i)
tree.balance()
bpy.ops.wm.open_mainfile(filepath=str(bodypath));body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.index_update();bm.faces.index_update()
matched=removed=0;delete=[];mismatch=[]
for face in bm.faces:
 if len(face.verts)!=3:continue
 points=np.array([x.co for x in face.verts]);hit=source.get(sig(points))
 if hit is None:
  co,i,distance=tree.find(points.mean(0))
  if distance<2e-6:hit=(i,keep[i],v[f[i]])
 if hit:
  distance=max(min(np.linalg.norm(q-p) for p in hit[2]) for q in points)
  if distance>2e-6:mismatch.append(distance);continue
  matched+=1
  if not hit[1]:delete.append(face);removed+=1
bmesh.ops.delete(bm,geom=delete,context='FACES');loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bound=[e for e in bm.edges if e.is_boundary];pending=set(bound);loops=[]
while pending:
 e=pending.pop();edges={e};stack=[e]
 while stack:
  for vertex in stack.pop().verts:
   for other in vertex.link_edges:
    if other in pending:pending.remove(other);edges.add(other);stack.append(other)
 verts={v for e in edges for v in e.verts};points=np.array([x.co for x in verts]);loops.append({'edges':len(edges),'vertices':len(verts),'bounds':[points.min(0).tolist(),points.max(0).tolist()],'mean':points.mean(0).tolist(),'vertexDegrees':sorted(set(sum(v in e.verts for e in edges) for v in verts))})
report={'status':'read-only source correspondence; no join','inputs':{str(p):sha(p) for p in [bodypath,headpath,maskpath]},'sourceFaces':len(f),'sourceDeleteFaces':int((~keep).sum()),'bodyFaces':len(body.data.polygons),'matchedSourceTriangles':matched,'matchedRemovedTriangles':removed,'signatureCollisions':len(f)-len(source),'matchingToleranceM':2e-6,'mismatchDistances':mismatch,'bodyBoundaryAfterExactMask':loops,'bodyAfterMaskVertices':len(bm.verts),'bodyAfterMaskFaces':len(bm.faces),'bodyNonmanifoldEdgesAfterMask':sum(not e.is_manifold for e in bm.edges)}
bm.free()
bpy.ops.wm.open_mainfile(filepath=str(headpath));report['headObjects']=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 p=np.array([o.matrix_world@x.co for x in o.data.vertices]);report['headObjects'].append({'name':o.name,'vertices':len(p),'faces':len(o.data.polygons),'boundsNativeBlender':[p.min(0).tolist(),p.max(0).tolist()],'boundsScaledWorld':[(p*.42+[0,0,1.59338]).min(0).tolist(),(p*.42+[0,0,1.59338]).max(0).tolist()],'UV':[u.name for u in o.data.uv_layers]})
(O/'probe02.json').write_text(json.dumps(report,indent=2)+'\n');print('PROBE_SUMMARY',json.dumps({k:report[k] for k in ['matchedSourceTriangles','matchedRemovedTriangles','bodyBoundaryAfterExactMask','bodyNonmanifoldEdgesAfterMask','headObjects']}),flush=True)
