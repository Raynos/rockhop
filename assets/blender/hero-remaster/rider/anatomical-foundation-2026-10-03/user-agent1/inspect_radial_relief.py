"""Localize actual sewn relief self contacts without changing the candidate."""
import argparse,collections,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['candidate','field','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);candidate,field,out=[Path(getattr(a,k)).resolve() for k in ['candidate','field','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [candidate,field]}
assert pins[str(candidate)]=='3859ffbe0716d1a6d87705c8f84fc4838527128b509ebc9244042199dcf91d34'
bpy.ops.wm.open_mainfile(filepath=str(candidate));g=bpy.data.objects['Selected Hunyuan radial exterior wearable, unrigged'];g.data.calc_loop_triangles()
data=np.load(field);region=data['region'];seed=data['seedXYZ'];final=data['finalXYZ'];directions=data['direction'];relief=data['connectedRelief'];ease=data['boundaryEase']
p=np.array([list(v.co) for v in g.data.vertices]);f=[tuple(t.vertices) for t in g.data.loop_triangles]
error=float(np.max(np.linalg.norm(p-final,axis=1)));assert error<1e-7,error
parents=[v.value for v in g.data.attributes['source_parent_polygon'].data]
label=lambda tri:'shirt' if parents[g.data.loop_triangles[tri].polygon_index]<1204 else 'collar' if parents[g.data.loop_triangles[tri].polygon_index]<1224 else 'hood'
tree=BVHTree.FromPolygons([Vector(x) for x in p],f,all_triangles=True);st=BVHTree.FromPolygons([Vector(x) for x in seed],f,all_triangles=True)
seedpairs=[(i,j) for i,j in st.overlap(st) if i<j and not set(f[i])&set(f[j])];assert len(seedpairs)==0
records=[]
for i,j in tree.overlap(tree):
    if i>=j or set(f[i])&set(f[j]):continue
    surfaces=[]
    for tri in [i,j]:
        ids=list(f[tri]);surfaces.append({'triangle':tri,'panel':label(tri),'sourceParentPolygon':parents[g.data.loop_triangles[tri].polygon_index],
            'vertices':ids,'region':region[ids].tolist(),'seedXYZ':seed[ids].tolist(),'finalXYZ':p[ids].tolist(),
            'directions':directions[ids].tolist(),'connectedReliefM':relief[ids].tolist(),'boundaryEase':ease[ids].tolist(),
            'centroidNativeM':p[ids].mean(0).tolist()})
    records.append({'surfaces':surfaces})
classes=dict(collections.Counter('/'.join(sorted(s['panel'] for s in r['surfaces'])) for r in records))
centroids=np.array([s['centroidNativeM'] for r in records for s in r['surfaces']])
report={'status':'UNACCEPTED selected radial-relief self-contact localization; no intervention',
        'pins':pins,'recipeSHA256':sha(__file__),'nativeStorageErrorM':error,'seedSelfPairs':len(seedpairs),'candidateSelfPairs':len(records),
        'pairsByPanels':classes,'contactCentroidBoundsM':[centroids.min(0).tolist(),centroids.max(0).tolist()],
        'witnesses':records,'limits':['Actual triangle witnesses and exact frozen seed/relief/direction domains only; no rig/game/art/mobile or global-clearance pass.',
                                   'Scalar connectivity does not guarantee embedded-surface injectivity; original source and failed candidate are unchanged.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['nativeStorageErrorM','seedSelfPairs','candidateSelfPairs','pairsByPanels','contactCentroidBoundsM']}),flush=True)
