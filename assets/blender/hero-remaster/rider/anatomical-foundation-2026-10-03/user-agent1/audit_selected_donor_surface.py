"""Read saved donor construction after a report-only serialization failure."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','archive','executed-recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,archive,recipe,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','archive','executed-recipe','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,archive,recipe]}
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Actual selected donor surface with wearer cuts, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08']
g.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=[tuple(t.vertices) for t in g.data.loop_triangles]
d=np.load(archive);assert np.array_equal(p,d['finalNativeXYZ']);assert np.array_equal(np.array(tri),d['triangles'])
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);btri=[tuple(t.vertices) for t in body.data.loop_triangles]
gt=BVHTree.FromPolygons([Vector(v) for v in p],tri,all_triangles=True);bt=BVHTree.FromPolygons([Vector(v) for v in bp],btri,all_triangles=True)
bodyPairs=gt.overlap(bt);selfPairs=[(i,j) for i,j in gt.overlap(gt) if i<j and not set(tri[i])&set(tri[j])]
assert np.array_equal(np.array(bodyPairs,dtype=np.int32).reshape(-1,2),d['bodyTrianglePairs'].reshape(-1,2));assert np.array_equal(np.array(selfPairs,dtype=np.int32).reshape(-1,2),d['selfTrianglePairs'].reshape(-1,2))
edgeFaces={}
for face in g.data.polygons:
    ids=list(face.vertices)
    for i,j in zip(ids,ids[1:]+ids[:1]):edgeFaces.setdefault(tuple(sorted((i,j))),[]).append(face.index)
boundary={e for e,f in edgeFaces.items() if len(f)==1};loops=[]
while boundary:
    first=boundary.pop();found={first};stack=[first]
    while stack:
        e=stack.pop();adj={x for x in boundary if set(x)&set(e)};boundary-=adj;found|=adj;stack.extend(adj)
    ids=sorted({i for e in found for i in e});q=p[ids]
    loops.append({'edges':len(found),'vertices':len(ids),'allDegree2':all(sum(i in e for e in found)==2 for i in ids),'nativeVertexIDs':ids,'nativeXYZBoundsM':[q.min(0).tolist(),q.max(0).tolist()],'nativeCentroidM':q.mean(0).tolist()})
def witnesses(pairs,other,otherTri):
    return [{'garmentTriangle':i,'otherTriangle':j,'garmentVertexIDs':list(tri[i]),'otherVertexIDs':list(otherTri[j]),'garmentNativeXYZ':p[list(tri[i])].tolist(),'otherNativeXYZ':other[list(otherTri[j])].tolist()} for i,j in pairs[:64]]
report={'status':'UNACCEPTED saved actual-donor construction audit; report serialization only repaired','pins':pins,'recipeSHA256':sha(__file__),
        'executedConstruction':'Frozen serialization-rejected-builder.py saved native and exact array archive before JSON failed on NumPy float32; this audit reads those unchanged outputs, never remakes/saves them.',
        'parentSource13SHA256':'6ef79e38e3dc86b635977ba17a2f2f6100721715b002c4e831b8bcce90ed4e93','donorSHA256':'800d7a9717757b90b296a78c605cddb698c68d399a96e403aa381103e77d2eba',
        'simplification':{'method':'Original high donor clone welded1e-7, detached54vertex104face speck removed, Collapse ratio0.018 with UV/material/seam delimiters','originalHighVertices':716971,'cleanedVertices':460752,'cleanedTriangles':921568,'simplifiedVertices':len(d['simplifiedDonorDisplayXYZ']),'registeredFrame':'Frozen piecewise construction mapping; original shape/PBR drives geometry, no stock-pattern relief'},
        'wearerCuts':{'hem':'Central donor minimum Z +8mm, horizontal plane','cuffs':'Each true forearm wrist minus5mm along its original axis, perpendicular plane','neck':'Explicit convex20-plane ellipse XY center(0.015,0),radii(0.078,0.085)m,Z1.485..1.67m; surface partition then interior pieces deleted, no Boolean modifier/body snaps'},
        'finalTopology':{'vertices':len(p),'polygons':len(g.data.polygons),'triangles':len(tri),'boundaryLoops':loops,'otherNonManifoldEdges':sum(len(f)>2 for f in edgeFaces.values())},
        'restGarmentBodyTrianglePairs':len(bodyPairs),'restNonAdjacentSelfTrianglePairs':len(selfPairs),'nativeAndArchivedPositionsTrianglesContactsExact':True,'bodyWitnesses':witnesses(bodyPairs,bp,btri),'selfWitnesses':witnesses(selfPairs,p,tri),
        'material':{'name':g.data.materials[0].name,'originalUVMaps':[u.name for u in g.data.uv_layers],'images':[[n.image.name,list(n.image.size),n.image.colorspace_settings.name] for n in g.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image]},
        'limits':['Rest intersections/topology defects are explicit prerequisites, not accepted wearing/art or global clearance.','No new capture after source61 verdict; donor16 appearance/fit/rig remain pending root.','AllM0-M5/mobile open; no inference, worker, broad motion or normal-player/Library promotion.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print('SAVED_DONOR_AUDITED',len(p),len(tri),'body',len(bodyPairs),'self',len(selfPairs),'loops',len(loops),'otherNonManifold',report['finalTopology']['otherNonManifoldEdges'],flush=True)
