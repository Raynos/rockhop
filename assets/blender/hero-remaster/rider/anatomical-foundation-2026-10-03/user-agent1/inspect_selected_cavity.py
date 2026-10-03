"""Recover and audit a failed cavity's exact registered pre-Boolean surface."""
import bpy,bmesh,numpy as np,json,hashlib,sys,argparse
from pathlib import Path
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for name in ['surface','candidate','registration','out']:ap.add_argument('--'+name,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);surface,candidate,registration,out=[Path(getattr(a,n)).resolve() for n in ['surface','candidate','registration','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(surface))
obj=bpy.data.objects['Selected hoodie reconstructed surface, openings and fit pending'];coords=np.load(registration)['nativeRestXYZ']
bm=bmesh.new();bm.from_mesh(obj.data)
bound={e for e in bm.edges if e.is_boundary}
while bound:
 edge=bound.pop();found={edge};stack=[edge]
 while stack:
  e=stack.pop()
  for v in e.verts:
   for n in v.link_edges:
    if n in bound:bound.remove(n);found.add(n);stack.append(n)
 assert len(found)==3;bmesh.ops.holes_fill(bm,edges=list(found),sides=3)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
for v,p in zip(obj.data.vertices,coords):v.co=p
def audit(o):
 bm=bmesh.new();bm.from_mesh(o.data);stats={'vertices':len(bm.verts),'faces':len(bm.faces),
  'signedVolumeNativeUnits':bm.calc_volume(signed=True),'boundaryEdges':sum(e.is_boundary for e in bm.edges),
  'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'nonContiguousEdges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges)};bm.free()
 o.data.calc_loop_triangles();faces=[tuple(t.vertices) for t in o.data.loop_triangles];p=[v.co.copy() for v in o.data.vertices]
 tree=BVHTree.FromPolygons(p,faces,all_triangles=True)
 pairs=[(i,j) for i,j in tree.overlap(tree) if i<j and not set(faces[i])&set(faces[j])]
 stats.update({'triangles':len(faces),'nonAdjacentSelfTrianglePairs':len(pairs),
  'dataBounds':[np.min(np.array(p),0).tolist(),np.max(np.array(p),0).tolist()],
  'objectWorldMatrixRows':[list(r) for r in o.matrix_world]})
 return stats
registered=audit(obj)
bpy.ops.wm.open_mainfile(filepath=str(candidate))
cutter=audit(bpy.data.objects['Canonical wearer cavity cutter, derivative only'])
result=audit(bpy.data.objects['Selected Hunyuan wearable construction, unrigged and unaccepted'])
report={'status':'REJECTED registered/cavity construction diagnosis; no new geometry intervention',
 'pins':{str(p):sha(p) for p in [surface,candidate,registration]},'recipeSHA256':sha(__file__),
 'registeredPreBoolean':registered,'actualBodyCutter':cutter,'failedResult':result,
 'limits':['Reconstructed exact pre-Boolean source positions/caps; no source overwrite or acceptance.',
 'Boolean registration used direct display-axis rotation for arms without the torso frame rotation; this is a documented frame defect for the next construction, not an accepted fitting transform.',
 'Nonadjacent BVH overlaps are sampled triangle witnesses, not signed thickness or live collision response.']}
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
