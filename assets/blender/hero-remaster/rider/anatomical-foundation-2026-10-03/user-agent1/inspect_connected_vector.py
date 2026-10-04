"""Record true triangle contacts in the selected-source connected vector fit."""
import argparse,collections,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['candidate','field','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);candidate,field,out=[Path(getattr(a,k)).resolve() for k in ['candidate','field','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [candidate,field]}
assert pins[str(candidate)]=='96c0d90b437662e11dfb9a2386d2c61126538c1beec02db251e28674caf2f0bd'
bpy.ops.wm.open_mainfile(filepath=str(candidate));g=bpy.data.objects['Selected Hunyuan connected vector wearable, unrigged'];g.data.calc_loop_triangles()
d=np.load(field);seed=d['seedXYZ'];p=np.array([list(v.co) for v in g.data.vertices]);f=[tuple(t.vertices) for t in g.data.loop_triangles]
assert np.linalg.norm(p-d['finalXYZ'],axis=1).max()<1e-7
parents=[v.value for v in g.data.attributes['source_parent_polygon'].data]
panel=lambda i:'shirt' if parents[g.data.loop_triangles[i].polygon_index]<1204 else 'collar' if parents[g.data.loop_triangles[i].polygon_index]<1224 else 'hood'
t=BVHTree.FromPolygons([Vector(x) for x in p],f,all_triangles=True);records=[];ids=set();centroids=[]
for i,j in t.overlap(t):
    if i>=j or set(f[i])&set(f[j]):continue
    surfaces=[]
    for tri in [i,j]:
        vertices=list(f[tri]);ids.update(vertices);centroids.append(p[vertices].mean(0))
        surfaces.append({'triangle':tri,'panel':panel(tri),'sourceParentPolygon':parents[g.data.loop_triangles[tri].polygon_index],
                         'vertices':vertices,'seedXYZ':seed[vertices].tolist(),'finalXYZ':p[vertices].tolist(),
                         'connectedDisplacementM':d['connectedDisplacement'][vertices].tolist()})
    records.append({'surfaces':surfaces})
centroids=np.array(centroids);report={'status':'UNACCEPTED connected-vector fit contact localization, no intervention',
        'pins':pins,'recipeSHA256':sha(__file__),'selfPairs':len(records),
        'pairsByPanels':dict(collections.Counter('/'.join(sorted(s['panel'] for s in w['surfaces'])) for w in records)),
        'contactVertices':sorted(ids),'centroidBoundsNativeM':[centroids.min(0).tolist(),centroids.max(0).tolist()],
        'witnesses':records,'limits':['Actual frozen triangle/domain witnesses only, not a collision correction or moving fit/art/mobile approval.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['selfPairs','pairsByPanels','centroidBoundsNativeM']}),len(ids),flush=True)
