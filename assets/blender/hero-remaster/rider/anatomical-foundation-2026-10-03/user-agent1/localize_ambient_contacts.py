"""Locate frozen donor contacts against actual free edges and anatomical axes."""
import argparse, collections, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','audit','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,audit,out=[Path(getattr(a,k)).resolve() for k in ['source','field','audit','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,audit]};assert pins[str(source)]=='c50417a78f90b1e7376ff6166275b92379bd23e7146832ebf34ebb5bfa50f3cc'
f=np.load(field);r=json.loads(audit.read_text());bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Actual selected donor, ambient measured-lumen flow, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig'];g.data.calc_loop_triangles();body.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=np.array([t.vertices[:] for t in g.data.loop_triangles]);bp=np.array([v.co[:] for v in body.data.vertices]);bt=np.array([t.vertices[:] for t in body.data.loop_triangles]);assert np.array_equal(p,f['finalNativeXYZ']) and np.array_equal(tri,f['triangles'])
edgeFaces=collections.defaultdict(list);adj=collections.defaultdict(set)
for i,poly in enumerate(g.data.polygons):
    ids=list(poly.vertices)
    for j in range(len(ids)):edgeFaces[tuple(sorted((ids[j],ids[(j+1)%len(ids)])))].append(i)
free={e for e,faces in edgeFaces.items() if len(faces)==1};remaining=set(free);loops=[]
while remaining:
    first=remaining.pop();edges={first};vertices=set(first);stack=list(first)
    while stack:
        v=stack.pop()
        for e in list(remaining):
            if v in e:remaining.remove(e);edges.add(e);other=e[0] if e[1]==v else e[1];vertices.add(other);stack.append(other)
    ids=sorted(vertices);q=p[ids];degrees=collections.Counter(v for e in edges for v in e);loops.append({'vertexIDs':ids,'edges':sorted(edges),'allDegree2':all(n==2 for n in degrees.values()),'centroidM':q.mean(0).tolist(),'boundsM':[q.min(0).tolist(),q.max(0).tolist()]})
loops.sort(key=lambda x:tuple(x['centroidM']));freeEdges=np.array([e for loop in loops for e in loop['edges']]);edgeLoop=np.array([i for i,loop in enumerate(loops) for e in loop['edges']]);ea=p[freeEdges[:,0]];eb=p[freeEdges[:,1]];ed=eb-ea;ed2=(ed*ed).sum(1)
# Mesh graph distance is geometric diagnostic, not a material seam label.
for u,v in edgeFaces:adj[u].add(v);adj[v].add(u)
steps=np.full(len(p),-1,dtype=int);queue=collections.deque(sorted({v for e in free for v in e}))
for v in queue:steps[v]=0
while queue:
    v=queue.popleft()
    for w in adj[v]:
        if steps[w]<0:steps[w]=steps[v]+1;queue.append(w)
def in_triangle(q,t):
    u=t[1]-t[0];v=t[2]-t[0];w=q-t[0];den=(u@u)*(v@v)-(u@v)**2
    if abs(den)<1e-20:return False
    x=((v@v)*(w@u)-(u@v)*(w@v))/den;y=((u@u)*(w@v)-(u@v)*(w@u))/den
    return x>=-1e-7 and y>=-1e-7 and x+y<=1+1e-7
def intersection_points(a,b):
    result=[]
    for x,t in [(a,b),(b,a)]:
        n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20);d=(x-t[0])@n
        for k in range(3):
            l=(k+1)%3
            if abs(d[k])<1e-9 and in_triangle(x[k],t):result.append(x[k])
            if d[k]*d[l]<0:
                q=x[k]+d[k]/(d[k]-d[l])*(x[l]-x[k])
                if in_triangle(q,t):result.append(q)
    unique=[]
    for q in result:
        if not any(np.linalg.norm(q-z)<1e-8 for z in unique):unique.append(q)
    return np.array(unique).reshape(-1,3)
def nearest_free(q):
    u=np.clip(np.einsum('ij,ij->i',q-ea,ed)/np.maximum(ed2,1e-20),0,1);closest=ea+u[:,None]*ed;distance=np.linalg.norm(closest-q,axis=1);i=int(distance.argmin());return {'distanceM':float(distance[i]),'loop':int(edgeLoop[i]),'edgeVertexIDs':freeEdges[i].tolist(),'closestFreeEdgeXYZ':closest[i].tolist()}
def station(points,name):
    b=rig.data.bones[name];head=np.array(b.head_local);axis=np.array(b.tail_local)-head;length=np.linalg.norm(axis);axis/=length;along=(points-head)@axis
    return {'bone':name,'stationRange':[(along/length).min().item(),(along/length).max().item()],'signedBoneTailPlaneDistanceM':[(along-length).min().item(),(along-length).max().item()],'axis':axis.tolist(),'headM':head.tolist(),'tailM':list(b.tail_local)}
btree=BVHTree.FromPolygons([Vector(v) for v in bp],bt.tolist(),all_triangles=True);witnesses=[]
for record in r['allBodyWitnesses']:
    i,j=record['garmentTriangle'],record['bodyTriangle'];ids=tri[i];q=p[ids];crossing=intersection_points(q,bp[bt[j]]);assert len(crossing)>0,(i,j);part=record['dominantRawBodyBone'];axisBone='forearm.'+part[-1] if part.startswith(('forearm','hand')) else part;stats=station(crossing,axisBone);b=rig.data.bones[axisBone];axis=np.array(b.tail_local)-np.array(b.head_local);axis/=np.linalg.norm(axis);center=q.mean(0);projection=np.array(b.head_local)+axis*((center-np.array(b.head_local))@axis);radial=center-projection;normal=np.cross(q[1]-q[0],q[2]-q[0]);radialDot=float(normal@radial/max(np.linalg.norm(normal)*np.linalg.norm(radial),1e-20));near=[]
    for v in q:
        location,n,index,d=btree.find_nearest(Vector(v));near.append({'distanceM':d,'normalSignedDistanceM':float((v-np.array(location))@np.array(n)),'bodyTriangle':index})
    witnesses.append({'garmentTriangle':i,'bodyTriangle':j,'dominantRawBone':part,'garmentVertexIDs':ids.tolist(),'sourceParentPolygon':int(g.data.attributes['simplified_donor_polygon'].data[g.data.loop_triangles[i].polygon_index].value),'crossingPointsXYZ':crossing.tolist(),'nearestActualFreeEdgeAtCrossing':[nearest_free(z) for z in crossing],'minimumVertexGraphStepsToFreeEdge':int(steps[ids].min()),'nativeNormalRadialCosine':radialDot,'crossingAxis':stats,'garmentVertexLocalNearestBodyDistances':near})
summary={}
for part in sorted({x['dominantRawBone'] for x in witnesses}):
    rows=[x for x in witnesses if x['dominantRawBone']==part];dist=[y['distanceM'] for x in rows for y in x['nearestActualFreeEdgeAtCrossing']];summary[part]={'pairs':len(rows),'uniqueGarmentTriangles':len({x['garmentTriangle'] for x in rows}),'crossingFreeEdgeDistanceMPercentiles':np.percentile(dist,[0,50,95,100]).tolist(),'nearestFreeLoopCounts':dict(collections.Counter(str(y['loop']) for x in rows for y in x['nearestActualFreeEdgeAtCrossing'])),'minVertexGraphStepsRange':[min(x['minimumVertexGraphStepsToFreeEdge'] for x in rows),max(x['minimumVertexGraphStepsToFreeEdge'] for x in rows)],'stationRange':[min(x['crossingAxis']['stationRange'][0] for x in rows),max(x['crossingAxis']['stationRange'][1] for x in rows)],'signedBoneTailPlaneDistanceM':[min(x['crossingAxis']['signedBoneTailPlaneDistanceM'][0] for x in rows),max(x['crossingAxis']['signedBoneTailPlaneDistanceM'][1] for x in rows)],'radialNormalCosineRange':[min(x['nativeNormalRadialCosine'] for x in rows),max(x['nativeNormalRadialCosine'] for x in rows)]}
for loop in loops:
    q=p[loop['vertexIDs']];loop['forearmStations']={side:station(q,'forearm.'+side) for side in ['L','R']}
result={'status':'UNACCEPTED readonly source22 contact/end localization','pins':pins,'recipeSHA256':sha(__file__),'vertices':len(p),'triangles':len(tri),'boundaryEdges':len(free),'boundaryLoops':loops,'bodyContactPairs':len(witnesses),'contactClasses':summary,'allContactWitnesses':witnesses,'method':'Triangle edge/plane intersections with barycentric inclusion; crossing-point distances to every actual free-edge segment; vertex graph BFS; fixed bone-axis stations. Local nearest-body normal signs and radial surface orientation are geometric diagnostics only.','limits':['Coplanar overlapping triangles need separate polygon clipping; every observed pair here yields edge/plane witnesses, no general coplanar proof.','Nearest free edge does not identify a physical air port. Raw weight class and radial sign cannot authorize wall deletion. Normal-nearest sign is not a global containment/winding proof.','No geometry/source save/scale/time/density retry/capture/rig/motion/body-head-51bind change or player promotion. Wearing/art/M0-M5/mobile remain open.']}
assert pins=={x:sha(x) for x in pins};out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print('AMBIENT_CONTACTS_LOCALIZED',json.dumps(summary),flush=True)
