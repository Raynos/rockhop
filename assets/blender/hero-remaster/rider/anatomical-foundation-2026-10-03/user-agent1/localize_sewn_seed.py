"""Locate exact seed contacts by verified original-panel ancestry, no fitting edit."""
import argparse,hashlib,json,sys,math,collections
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for n in ['source','field','seed-builder','out']:ap.add_argument('--'+n,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,seed_builder,out=[Path(getattr(a,n.replace('-','_'))).resolve() for n in ['source','field','seed-builder','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,seed_builder]}
assert pins[str(source)]=='4c35e5aaa3fed563b8440b16f90d1f2257611838b6584b9983ad234b014a8c93'
bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];pattern=bpy.data.objects['Separate fitted sweatshirt control, hood not constructed'];rig=bpy.data.objects['Independent anatomical foundation rig']
candidate=bpy.data.objects['Selected Hunyuan connected sewn wearable, unrigged']
code=seed_builder.read_text();code=code[code.index('vertices=[list'):code.index('lineage=[];unmapped=[];maximum_fit_adjustment=0')]
code=code.replace('-.03+.10*math.cos(theta)','-.01+.12*math.cos(theta)').replace('q[0]-=.025*math.sin(math.pi*t)','q[0]-=.025*max(0.,-math.cos(theta))*math.sin(math.pi*t)')
needle='garment=bpy.data.objects.new';assert code.count(needle)==1
code=code.replace(needle,"parent_ids=mesh.attributes.new('source_parent_polygon',type='INT',domain='FACE')\nfor parent_id,entry in enumerate(parent_ids.data):entry.value=parent_id\n"+needle)
ns={'bpy':bpy,'bmesh':bmesh,'np':np,'math':math,'body':body,'pattern':pattern};exec(compile(code,str(seed_builder),'exec'),ns)
seed=ns['garment'];seedXYZ=np.load(field)['seedXYZ'];assert np.array_equal(np.array([list(v.co) for v in seed.data.vertices]),seedXYZ)
assert [list(f.vertices) for f in seed.data.polygons]==[list(f.vertices) for f in candidate.data.polygons]
parents=[v.value for v in seed.data.attributes['source_parent_polygon'].data]
counts=collections.Counter(parents);assert len(counts)==1444 and set(counts.values())=={4},counts
sort_edges={tuple(sorted((i,j))) for i,j in zip(ns['neck'],ns['neck'][1:]+ns['neck'][:1])}
actual_edges={tuple(e) for e in ns['neck_edges']};assert sort_edges==actual_edges
body.data.calc_loop_triangles();bf=[tuple(t.vertices) for t in body.data.loop_triangles];bp=[v.co.copy() for v in body.data.vertices]
bt=BVHTree.FromPolygons(bp,bf,all_triangles=True)
def mesh(o):
 o.data.calc_loop_triangles();p=[v.co.copy() for v in o.data.vertices];f=[tuple(t.vertices) for t in o.data.loop_triangles]
 return BVHTree.FromPolygons(p,f,all_triangles=True),p,f
st,sp,sf=mesh(seed);pt,pp,pf=mesh(pattern)
source_pattern_body=pt.overlap(bt);source_pattern_self=[(i,j) for i,j in pt.overlap(pt) if i<j and not set(pf[i])&set(pf[j])]
panel=lambda tri:'original-shirt' if parents[seed.data.loop_triangles[tri].polygon_index]<1204 else 'new-hood'
body_records=[]
for garmenttri,bodytri in st.overlap(bt):
 weights={}
 for vertex in bf[bodytri]:
  for g in body.data.vertices[vertex].groups:
   name=body.vertex_groups[g.group].name
   if name in rig.data.bones:weights[name]=weights.get(name,0)+float(g.weight)/3
 body_records.append({'seedTriangle':garmenttri,'seedPolygon':seed.data.loop_triangles[garmenttri].polygon_index,
  'sourceParentPolygon':parents[seed.data.loop_triangles[garmenttri].polygon_index],'panel':panel(garmenttri),
  'seedVertices':list(sf[garmenttri]),'bodyTriangle':bodytri,'bodyVertices':list(bf[bodytri]),
  'bodyDominantJoint':max(weights,key=weights.get),'seedCentroidNativeM':list(sum((sp[i] for i in sf[garmenttri]),Vector())/3)})
self_records=[]
for i,j in st.overlap(st):
 if i>=j or set(sf[i])&set(sf[j]):continue
 self_records.append({'triangles':[i,j],'panels':[panel(i),panel(j)],
  'sourceParentPolygons':[parents[seed.data.loop_triangles[k].polygon_index] for k in [i,j]],
  'centroidsNativeM':[list(sum((sp[v] for v in sf[k]),Vector())/3) for k in [i,j]]})
body_count=dict(collections.Counter(r['panel'] for r in body_records));self_count=dict(collections.Counter('/'.join(sorted(r['panels'])) for r in self_records))
report={'status':'UNACCEPTED exact sewn-seed contact localization; no geometry intervention',
 'pins':pins,'recipeSHA256':sha(__file__),'seedCoordinatesExactFrozenField':True,'panelParentAncestry':'1444 original source panels each creates exactly4 child polygons; all candidate polygon cycles exact',
 'neckAngularOrderMatchesActualBoundaryEdges':True,'sourcePattern':{'vertices':len(pp),'triangles':len(pf),
  'bodyTrianglePairs':len(source_pattern_body),'nonAdjacentSelfTrianglePairs':len(source_pattern_self),
  'objectWorldRows':[list(r) for r in pattern.matrix_world]},'bodyWorldRows':[list(r) for r in body.matrix_world],
 'seedBodyPairsByPanel':body_count,'seedSelfPairsByPanels':self_count,
 'seedBodyPairsByDominantJoint':dict(collections.Counter(r['bodyDominantJoint'] for r in body_records)),
 'seedBodyRecords':body_records,'seedSelfRecords':self_records,
 'limits':['Actual body triangle/vertex and original-panel ancestry, not a new body or an assumed rest quad diagonal.',
 'Static BVH intersections are witnesses; no signed-clearance/skin/livecollision/actualgame/mobile/art acceptance.',
 'Source files unchanged; source seed qualification precedes more donor deformation or rig handoff. Root alone judges.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'pattern':report['sourcePattern'],'body':body_count,'self':self_count,'joints':report['seedBodyPairsByDominantJoint']}),flush=True)
