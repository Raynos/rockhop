"""Read-only final output audit: exact protected source and actual 3D clearance."""
import bpy,bmesh,numpy as np,json,hashlib,datetime
from pathlib import Path
from collections import Counter,defaultdict
from mathutils.bvhtree import BVHTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=R/'autonomous-lanes/C-garment-pattern/trial04';O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial04')
source=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';master=RUN/'character.blend';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p) for p in [source,master,RUN/'character.glb']};protected=set(np.load(RUN/'source-region-mask.npz')['protectedSourceFaceIds'].tolist())
def records(o,ids=None):
 m=o.data;out=[]
 for q in m.polygons:
  if ids is not None and q.index not in ids:continue
  corners=[tuple(float(x) for x in list(m.vertices[m.loops[li].vertex_index].co)+sum((list(u.data[li].uv) for u in m.uv_layers),[])) for li in q.loop_indices];out.append((q.material_index,tuple(sorted(corners))))
 return Counter(out)
def weights(o):
 out=defaultdict(list)
 for v in o.data.vertices:out[tuple(float(x) for x in v.co)].append(tuple(sorted((o.vertex_groups[g.group].name,float(g.weight)) for g in v.groups)))
 return {k:sorted(v) for k,v in out.items()}
bpy.ops.wm.open_mainfile(filepath=str(source));s=next(o for o in bpy.context.scene.objects if o.type=='MESH');before=records(s,protected);sw=weights(s);source_coords=set(sw)
bpy.ops.wm.open_mainfile(filepath=str(master));body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('UNACCEPTED C modular'));after=records(body);bw=weights(body);bad_weights=[k for k,v in bw.items() if k in sw and sw[k]!=v]
head=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'native evaluated' in o.name);hm=head.data;hm.calc_loop_triangles();skin_positions=[head.matrix_world@v.co for v in hm.vertices];skin=BVHTree.FromPolygons(skin_positions,[list(t.vertices) for t in hm.loop_triangles],all_triangles=True)
actual_new=[v for v in body.data.vertices if tuple(float(x) for x in v.co) not in source_coords];samples=[];inside=[]
for v in actual_new:
 p=body.matrix_world@v.co;co,normal,tri,d=skin.find_nearest(p)
 if co.z<1.49:continue
 signed=float((p-co).dot(normal));samples.append((d,signed))
 if signed<-.0005:inside.append({'actualVertex':v.index,'cloth':list(p),'nearestSkin':list(co),'signedDistanceM':signed,'distanceM':d})
boundary=[];b=bmesh.new();b.from_mesh(body.data)
for e in b.edges:
 if e.is_boundary:boundary.append([list(v.co) for v in e.verts])
report={'status':'UNACCEPTED final construction audit; visible lining/UV/penetration defects, no rig pass','inputs':inputs,'protectedSourcePolygons':sum(before.values()),'missingPositionAllUVLayersMaterialPolygons':sum((before-after).values()),'protectedExactStoredFloats':True,'retainedOriginalNativeWeightMismatchCount':len(bad_weights),'newFinalMeshClothVertices':len(actual_new),'actualLocal3DClearance':{'basis':'ACTUAL final subdivision+solidification output vertices against complete unchanged native skin triangles, nearest skin pointz>=1.49m; no projected2D containment assertion','sampleCount':len(samples),'minimumDistanceM':min(x[0] for x in samples),'minimumSignedSurfaceDistanceM':min(x[1] for x in samples),'signedInsideSamplesBeyond0_5mm':len(inside),'worstInsideSamples':sorted(inside,key=lambda x:x['signedDistanceM'])[:20],'limitations':'Vertex sampling, not a continuous triangle/selfcollision or neck motion acceptance'},'openInternalLiningBoundaryEdges':len(boundary),'sourceUVPrecision':'Exact stored sourcefloat values; no rounding','materialAssignments':{'slots':[m.name for m in body.data.materials],'faceCounts':dict(Counter(p.material_index for p in body.data.polygons))},'inputsAfter':{p:sha(p) for p in inputs},'finishedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
assert inputs==report['inputsAfter'];(O/'final-source-and-clearance-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('ACTUAL_FINAL_AUDIT',json.dumps({k:report[k] for k in ['protectedSourcePolygons','missingPositionAllUVLayersMaterialPolygons','retainedOriginalNativeWeightMismatchCount','newFinalMeshClothVertices','actualLocal3DClearance']}),flush=True)
