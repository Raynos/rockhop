"""Audit reconstructed donor surface without claiming physical garment fit."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for name in ['source','candidate','evidence']:ap.add_argument('--'+name,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,candidate,evidence=[Path(getattr(a,n)).resolve() for n in ['source','candidate','evidence']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def native():
 rows={}
 for o in bpy.data.objects:
  if o.type=='MESH':
   rows[o.name]={'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(f.vertices) for f in o.data.polygons],
    'groups':[[[o.vertex_groups[g.group].name,g.weight] for g in v.groups] for v in o.data.vertices],
    'uv':[[list(l.uv) for l in layer.data] for layer in o.data.uv_layers],
    'shapeKeys':None if o.data.shape_keys is None else [[k.name,k.value,[list(v.co) for v in k.data]] for k in o.data.shape_keys.key_blocks],
    'matrix':[list(r) for r in o.matrix_world]}
 rig=bpy.data.objects['Independent anatomical foundation rig']
 return rows,{b.name:{'parent':b.parent.name if b.parent else None,'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones}
bpy.ops.wm.open_mainfile(filepath=str(source));original,bind=native()
bpy.ops.wm.open_mainfile(filepath=str(candidate));current,currentbind=native()
assert bind==currentbind
assert all(current[n]==v for n,v in original.items())
surface=bpy.data.objects['Selected hoodie reconstructed surface, openings and fit pending']
high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only']
def tree(o):
 o.data.calc_loop_triangles();return BVHTree.FromPolygons([v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
st,ht=tree(surface),tree(high)
highsamples=[float(st.find_nearest(v.co)[3]) for v in list(high.data.vertices)[::max(1,len(high.data.vertices)//4096)]]
surfacepoints=[float(ht.find_nearest(v.co)[3]) for v in surface.data.vertices]
centroids=[float(ht.find_nearest(sum((surface.data.vertices[i].co for i in t.vertices),Vector())/3)[3]) for t in surface.data.loop_triangles]
stats=lambda values:{'count':len(values),'rms':float(np.sqrt(np.mean(np.square(values)))),'p95':float(np.percentile(values,95)),
 'p99':float(np.percentile(values,99)),'max':float(max(values))}
bm=bmesh.new();bm.from_mesh(surface.data);bm.verts.index_update();bm.edges.index_update()
boundary={e for e in bm.edges if e.is_boundary};loops=[]
while boundary:
 edge=boundary.pop();found={edge};stack=[edge]
 while stack:
  e=stack.pop()
  for v in e.verts:
   for neighbor in v.link_edges:
    if neighbor in boundary:boundary.remove(neighbor);found.add(neighbor);stack.append(neighbor)
 vertices={v for e in found for v in e.verts};p=np.array([list(v.co) for v in vertices])
 loops.append({'edgeCount':len(found),'vertexCount':len(vertices),'vertices':[v.index for v in vertices],
  'centerDisplayDonorUnits':p.mean(0).tolist(),'boundsDisplayDonorUnits':[p.min(0).tolist(),p.max(0).tolist()],
  'isCycle':all(sum(e in found for e in v.link_edges)==2 for v in vertices)})
non_boundary_bad=sum(not e.is_boundary and not e.is_manifold for e in bm.edges)
bm.free()
uv=np.array([list(l.uv) for l in surface.data.uv_layers.active.data]);assert np.isfinite(uv).all()
report={'status':'UNACCEPTED surface/PBR reconstruction; not physical garment fit',
 'sourceSHA256':sha(source),'candidateSHA256':sha(candidate),'recipeSHA256':sha(__file__),
 'originalNativeMeshesExact':len(original),'originalJointBindExact':len(bind),'nonBoundaryNonManifoldEdges':non_boundary_bad,
 'boundaryComponents':loops,'nearestDistanceDonorUnits':{'sourceVertexSampleToSurface':stats(highsamples),
 'surfaceVerticesToSource':stats(surfacepoints),'surfaceTriangleCentroidsToSource':stats(centroids)},
 'UVFinite':True,'UVBounds':[uv.min(0).tolist(),uv.max(0).tolist()],
 'limits':['Unsigned sample distances are not silhouette/moving visual acceptance or physical clearance.',
 'Source distance sample includes untouched detached speck; boundary components are not certified neck/cuff/hem openings.',
 'No units/pose/body registration, through-cavity, rig, game/contact/collision or mobile acceptance.']}
(evidence/'surface-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
