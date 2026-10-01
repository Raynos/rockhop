"""Replay EXACT failed trial02 prefix for forensic export only; no fix/selection change."""
import bpy,bmesh,json,hashlib,numpy as np,time,math
from pathlib import Path
from collections import Counter
from mathutils import Vector
recipe=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/neck-native/build_trial02.py')
text=recipe.read_text();marker=" boundary=loops(bm);assert len(boundary)==1,'Fixed FOUR-ring strip yields multiple holes; stop, no widening/fill'"
assert text.count(marker)==1
prefix=text[:text.index(marker)]+'\nexcept Exception:\n raise\n'
# The unchanged prefix owns the same constants/data selection. It writes no report or
# mesh before this marker. The original failure report is never overwritten.
exec(compile(prefix,str(recipe), 'exec'),globals())
if (OUT/'forensic.json').exists():raise RuntimeError('Frozen forensic witness exists')
failed_report=OUT/'report.json';frozen_report_sha=sha(failed_report)
# Record exact source triangle identities of the removed strip from frozen corners.
strip_ids=[];unknown=[]
for row in strip_rows:
 points=np.array(row);co,i,d=tree.find(points.mean(0))
 if len(points)==3 and d<2e-6 and max(min(np.linalg.norm(q-p) for p in v[f[i]]) for q in points)<2e-6:strip_ids.append(i)
 else:unknown.append(row)
assert not unknown,'Forensic source identities did not match exact failed selection'
boundary_edges={e for e in bm.edges if e.is_boundary};degree=Counter(x for e in boundary_edges for x in e.verts);histogram=Counter(degree.values());remaining=set(boundary_edges);circuits=[]
while remaining:
 seed=remaining.pop();component={seed};pending=[seed]
 while pending:
  for x in pending.pop().verts:
   for e in x.link_edges:
    if e in remaining:remaining.remove(e);component.add(e);pending.append(e)
 points=np.array([x.co for e in component for x in e.verts]);vertices=set(x for e in component for x in e.verts)
 circuits.append({'edges':len(component),'vertices':len(vertices),'degreeHistogram':dict(Counter(sum(x in e.verts for e in component) for x in vertices)),'bounds':[points.min(0).tolist(),points.max(0).tolist()]})
report={'status':'FAILED trial02 exact-prefix forensic witness; native collar technique STOPPED after two trials','originalFailureReportSHA256':frozen_report_sha,'exactFailedRecipeSHA256':sha(recipe),'forensicRecipeSHA256':sha(Path(__file__)),'prefixMarker':marker.strip(),'fourRingFaceCounts':ring_counts,'removedLocalSourceFaces':len(strip_rows),'sourceTriangleOrdinals':sorted(strip_ids),'removedStripCornerSHA256':strip_sha,'boundaryEdges':len(boundary_edges),'boundaryDegreeHistogram':dict(histogram),'branchVertices':sum(n!=2 for n in degree.values()),'boundaryComponents':circuits,'rawFailedPrefixTopology':topology(bm),'sourceInputsSHA256':inputs,'settings':report['settings'],'noNewSelectionOrFix':True,'newNativeHeadAdded':False,'limits':['This geometry is the failed strip prefix before any head join.','No hood widening, fill, smoothing, remesh, ellipse, texture trial, rig or contacts.','Any next garment panel needs explicit human choice and a new budget.']}
# Preserve the actual remaining source face material indices; no new material asset.
material_indices=np.array([face.material_index for face in bm.faces],np.int32);bm.to_mesh(body.data);body.data.polygons.foreach_set('material_index',material_indices);bm.free();body.data.update();body.name='FAILED native collar trial02 raw four-ring prefix; NOT sewn'
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'failed-strip.blend'));bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(RUN/'failed-strip.glb'),export_format='GLB',use_selection=True,export_animations=False)
report['failedGeometryFilesSHA256']={str(p):sha(p) for p in [RUN/'failed-strip.blend',RUN/'failed-strip.glb']};report['sourceInputsSHA256After']={p:sha(Path(p)) for p in inputs};assert inputs==report['sourceInputsSHA256After'];assert sha(failed_report)==frozen_report_sha
(OUT/'forensic.json').write_text(json.dumps(report,indent=2)+'\n');print('FORENSIC_FROZEN',json.dumps({k:report[k] for k in ['fourRingFaceCounts','removedLocalSourceFaces','boundaryEdges','boundaryDegreeHistogram','branchVertices','boundaryComponents']}),flush=True)
