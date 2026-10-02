"""Measure actual Blender self-BVH coverage independently of narrow-phase math."""
from mathutils.bvhtree import BVHTree
from pathlib import Path
import json
cases={
'nonadjacent_crossing':([[0,0,0],[1,0,0],[0,1,0],[.2,.2,-1],[.2,.2,1],[.8,.2,0]],[[0,1,2],[3,4,5]]),
'nonadjacent_separated':([[0,0,0],[1,0,0],[0,1,0],[2.2,.2,-1],[2.2,.2,1],[2.8,.2,0]],[[0,1,2],[3,4,5]]),
'shared_vertex_crossing':([[0,0,0],[1,0,0],[0,1,0],[.2,.2,-1],[.2,.2,1]],[[0,1,2],[0,3,4]]),
'shared_edge_positive_coplanar_fold':([[0,0,0],[1,0,0],[0,1,0],[.2,.2,0]],[[0,1,2],[1,0,3]]),
'nonadjacent_positive_coplanar_overlap':([[0,0,0],[1,0,0],[0,1,0],[.1,.1,0],[.6,.1,0],[.1,.6,0]],[[0,1,2],[3,4,5]])}
rows=[]
for name,(v,f) in cases.items():
 b=BVHTree.FromPolygons(v,f,all_triangles=True,epsilon=0);rows.append({'case':name,'pairs':b.overlap(b)})
assert rows[0]['pairs'] and not rows[1]['pairs']
report={'rows':rows,'limits':'Actual self-BVH coverage measured; no assumption that internal exclusions equal no application exclusions.'};Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rest-surface214/controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
