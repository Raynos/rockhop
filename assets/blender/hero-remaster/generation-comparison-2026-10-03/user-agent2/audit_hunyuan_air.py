"""Immutable original-GLB air-path and planar section audit; never writes meshes.

Rows are original glTF triangle IDs. Native units are uncalibrated, Y up.
Exact coordinate weld is incidence analysis only, not a geometry derivative.
No inference, Blender, GPU, model downloads, solid filling or fitting.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import time
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

SOURCE_SHA = '800d7a9717757b90b296a78c605cddb698c68d399a96e403aa381103e77d2eba'
SOURCE_BYTES = 42329320


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def load_glb(path):
    data = Path(path).read_bytes()
    assert len(data) == SOURCE_BYTES and digest(data) == SOURCE_SHA
    magic, version, total = struct.unpack_from('<III', data)
    assert (magic, version, total) == (0x46546c67, 2, len(data))
    length, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(data[20:20 + length]); offset = 20 + length
    length, kind = struct.unpack_from('<II', data, offset)
    assert kind == 0x004e4942
    binary = data[offset + 8:offset + 8 + length]
    assert len(doc['meshes']) == 1 and len(doc['meshes'][0]['primitives']) == 1
    for node in doc.get('nodes', []):
        assert all(k not in node for k in ('translation', 'rotation', 'scale'))
        assert np.array_equal(node.get('matrix', np.eye(4).flatten().tolist()), np.eye(4).flatten())
    p = doc['meshes'][0]['primitives'][0]
    assert p.get('mode', 4) == 4 and 'targets' not in p
    def accessor(index):
        a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
        assert not a.get('normalized') and 'sparse' not in a and view.get('buffer', 0) == 0
        dtype = np.dtype({5126:'<f4', 5125:'<u4', 5123:'<u2'}[a['componentType']])
        cols = {'SCALAR':1, 'VEC2':2, 'VEC3':3}[a['type']]
        return np.ndarray((a['count'], cols), dtype=dtype, buffer=binary,
                          offset=view.get('byteOffset', 0) + a.get('byteOffset', 0),
                          strides=(view.get('byteStride', dtype.itemsize * cols), dtype.itemsize)).copy()
    v = accessor(p['attributes']['POSITION']).astype(np.float64)
    f = accessor(p['indices']).reshape(-1, 3).astype(np.int64)
    uv = accessor(p['attributes']['TEXCOORD_0']).astype(np.float64)
    material = doc['materials'][p['material']]; pbr = material['pbrMetallicRoughness']
    maps = {}; images = {}
    for name in ('baseColorTexture', 'metallicRoughnessTexture'):
        t = pbr[name]; assert t.get('texCoord', 0) == 0 and not t.get('extensions')
        texture = doc['textures'][t['index']]; im = doc['images'][texture['source']]
        view = doc['bufferViews'][im['bufferView']]
        raw = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
        decoded = Image.open(io.BytesIO(raw)).convert('RGB')
        images[name] = np.asarray(decoded)
        maps[name] = {'sha256':digest(raw), 'bytes':len(raw), 'mimeType':im['mimeType'],
                      'size':list(decoded.size), 'texture':texture,
                      'sampler':doc.get('samplers', [])[texture['sampler']] if 'sampler' in texture else 'glTF defaults'}
    assert np.isfinite(v).all() and np.isfinite(uv).all()
    return v, f, uv, images, {'source':str(Path(path)), 'sourceSHA256':digest(data),
        'sourceBytes':len(data), 'nodes':doc.get('nodes'), 'material':material, 'maps':maps}


def segment_hits(v, f, start, end, eps=1e-10):
    """Moller-Trumbore on all conservative AABB candidates; both face sides.

    No missing spatial-index dependency. Deduplicate locations, retaining rows.
    Coplanar paths are ambiguous, never silently proved clear.
    """
    a = np.asarray(start, dtype=float); b = np.asarray(end, dtype=float); d = b - a
    assert np.linalg.norm(d) > 0
    tri = v[f]; lo = np.minimum(a, b) - eps; hi = np.maximum(a, b) + eps
    candidate = np.flatnonzero((tri.max(axis=1) >= lo).all(axis=1) & (tri.min(axis=1) <= hi).all(axis=1))
    t = tri[candidate]; e1 = t[:,1] - t[:,0]; e2 = t[:,2] - t[:,0]
    h = np.cross(np.broadcast_to(d, e2.shape), e2); determinant = (e1*h).sum(axis=1)
    parallel = np.abs(determinant) <= eps * np.linalg.norm(e1,axis=1) * np.linalg.norm(e2,axis=1) * np.linalg.norm(d)
    norm = np.cross(e1,e2); nlen = np.linalg.norm(norm,axis=1)
    planar = parallel & (nlen > 0) & (np.abs(((a-t[:,0])*norm).sum(axis=1)) <= eps*nlen)
    good = ~parallel & (nlen > 0)
    t = t[good]; e1=e1[good]; e2=e2[good]; h=h[good]; det=determinant[good]; rows=candidate[good]
    s = a-t[:,0]; u=(s*h).sum(axis=1)/det; q=np.cross(s,e1)
    w=(q*d).sum(axis=1)/det; fraction=(q*e2).sum(axis=1)/det
    hit=(u >= -eps)&(w >= -eps)&(u+w <= 1+eps)&(fraction >= -eps)&(fraction <= 1+eps)
    indices=np.flatnonzero(hit); indices=indices[np.argsort(fraction[indices])]
    clusters=[]
    for j in indices:
        value=float(fraction[j]); point=(a+value*d).tolist()
        item={'triangle':int(rows[j]), 'fraction':value, 'point':point,
              'barycentric':[float(1-u[j]-w[j]),float(u[j]),float(w[j])]}
        if clusters and abs(value-clusters[-1]['fraction'])*np.linalg.norm(d)<1e-7:
            clusters[-1]['coincidentTriangles'].append(item)
        else:
            item['coincidentTriangles']=[]; clusters.append(item)
    return {'start':a.tolist(),'end':b.tolist(),'length':float(np.linalg.norm(d)),
        'candidateTriangles':len(candidate),'coplanarCandidateTriangles':int(planar.sum()),
        'ambiguousCoplanar':bool(planar.any()),'intersections':clusters,
        'clearSegmentWitness':not clusters and not planar.any()}



def segment_clearance(v, f, start, end):
    """Exhaustive minimum distance via conservative AABB lower-bound pruning.

    With no intersection, closest points are an endpoint to a triangle face
    or segment to an edge. Degenerate triangles retain their segment edges.
    Upper bound comes from distance to an actual original vertex. All triangles
    with box lower bound below that distance are tested, not a sampled subset.
    """
    a=np.asarray(start);b=np.asarray(end);d=b-a;dd=np.dot(d,d)
    t=np.clip(((v-a)*d).sum(axis=1)/dd,0,1)
    upper=float(np.linalg.norm(v-(a+t[:,None]*d),axis=1).min())
    tri=v[f];low=tri.min(axis=1);high=tri.max(axis=1)
    gap=np.maximum(np.maximum(np.minimum(a,b)-high,low-np.maximum(a,b)),0)
    ids=np.flatnonzero((gap*gap).sum(axis=1)<=upper*upper+1e-14);tri=tri[ids]
    best=np.full(len(ids),np.inf)
    def point_edge(point, p, q):
        e=q-p;ee=(e*e).sum(axis=1)
        r=np.clip(((point-p)*e).sum(axis=1)/np.where(ee>0,ee,1),0,1)
        return ((point-(p+r[:,None]*e))**2).sum(axis=1)
    for i,k in ((0,1),(1,2),(2,0)):
        q0=tri[:,i];q1=tri[:,k];e=q1-q0;ee=(e*e).sum(axis=1)
        ed=(e*d).sum(axis=1);w=a-q0;dw=(w*d).sum(axis=1);ew=(w*e).sum(axis=1)
        det=dd*ee-ed*ed;safe=np.where(det>1e-24,det,1)
        s=(ed*ew-ee*dw)/safe;r=(dd*ew-ed*dw)/safe
        valid=(det>1e-24)&(s>=0)&(s<=1)&(r>=0)&(r<=1)
        free=((a+s[:,None]*d)-(q0+r[:,None]*e))**2
        distance=np.where(valid,free.sum(axis=1),np.inf)
        for point in (a,b):distance=np.minimum(distance,point_edge(point,q0,q1))
        for point in (q0,q1):
            s=np.clip(((point-a)*d).sum(axis=1)/dd,0,1)
            distance=np.minimum(distance,((point-(a+s[:,None]*d))**2).sum(axis=1))
        best=np.minimum(best,distance)
    e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];n=np.cross(e1,e2);nn=(n*n).sum(axis=1)
    dot11=(e1*e1).sum(axis=1);dot22=(e2*e2).sum(axis=1);dot12=(e1*e2).sum(axis=1)
    determinant=dot11*dot22-dot12*dot12;safe=np.where(determinant>1e-24,determinant,1)
    for point in (a,b):
        delta=point-tri[:,0];d1=(delta*e1).sum(axis=1);d2=(delta*e2).sum(axis=1)
        u=(dot22*d1-dot12*d2)/safe;w=(dot11*d2-dot12*d1)/safe
        valid=(determinant>1e-24)&(u>=0)&(w>=0)&(u+w<=1)
        distance=((delta*n).sum(axis=1)**2)/np.where(nn>0,nn,1)
        best=np.minimum(best,np.where(valid,distance,np.inf))
    k=int(np.argmin(best));result=float(np.sqrt(max(0,best[k])))
    assert result<=upper+1e-7
    return {'minimumDistanceNativeUnits':result,'closestOriginalTriangleRow':int(ids[k]),
        'vertexUpperBound':upper,'trianglesExhaustivelyTested':len(ids),
        'allOriginalTrianglesBounded':len(f),'numericalToleranceClaim':1e-7,
        'estimatedOpenTubeRadiusAfterTolerance':max(0,result-1e-7),
        'notFormalIntervalCertificate':True,
        'method':'Exact segment-edge and endpoint-triangle distance for nonintersecting path, all original rows conservatively bounded; not sparse ray sampling.'}

def section(v, f, axis, value, tolerance=1e-7):
    tri=v[f]; delta=tri[:,:,axis]-value
    # Face exactly containing a plane vertex is reported as ambiguous and excluded.
    on=(np.abs(delta)<=1e-12).any(axis=1)
    crossings=[]; rows=[]
    for i,j in ((0,1),(1,2),(2,0)):
        yes=((delta[:,i]<0)!=(delta[:,j]<0)) & ~on
        ids=np.flatnonzero(yes)
        alpha=-delta[ids,i]/(delta[ids,j]-delta[ids,i])
        crossings.append(tri[ids,i]+alpha[:,None]*(tri[ids,j]-tri[ids,i])); rows.append(ids)
    points=np.concatenate(crossings); ids=np.concatenate(rows); order=np.argsort(ids,kind='stable')
    points=points[order]; ids=ids[order]
    unique, counts=np.unique(ids,return_counts=True)
    assert (counts==2).all()
    segments=points.reshape(-1,2,3); face_ids=unique
    keys=np.rint(segments.reshape(-1,3)/tolerance).astype(np.int64)
    _, first, inverse=np.unique(keys,axis=0,return_index=True,return_inverse=True)
    nodes=segments.reshape(-1,3)[first]; edges=inverse.reshape(-1,2)
    graph=coo_matrix((np.ones(len(edges)*2),(edges.flatten(),edges[:,::-1].flatten())),shape=(len(nodes),len(nodes))).tocsr()
    count, labels=connected_components(graph,directed=False)
    degree=np.bincount(edges.flatten(),minlength=len(nodes)); loops=[]
    projected=[k for k in range(3) if k!=axis]
    for component in range(count):
        n=np.flatnonzero(labels==component); e=np.flatnonzero(labels[edges[:,0]]==component)
        if not (degree[n]==2).all():
            loops.append({'closed':False,'segments':len(e),'bounds':[nodes[n].min(axis=0).tolist(),nodes[n].max(axis=0).tolist()], 'badDegreeNodes':int((degree[n]!=2).sum())});continue
        adj={int(k):[] for k in n}
        for k in e:
            a,b=edges[k];adj[int(a)].append((int(b),int(k)));adj[int(b)].append((int(a),int(k)))
        current=int(n[0]); previous=-1; ordered=[]; ordered_faces=[]
        while True:
            ordered.append(current)
            nxt, edge=next((b,k) for b,k in adj[current] if b!=previous)
            ordered_faces.append(int(face_ids[edge]));previous,current=current,nxt
            if current==ordered[0]:break
            assert len(ordered)<=len(n)
        p=nodes[ordered];p2=p[:,projected];q=np.roll(p2,-1,axis=0)
        area=abs(float(np.sum(p2[:,0]*q[:,1]-q[:,0]*p2[:,1])))/2
        loops.append({'closed':True,'segments':len(e),'area':area,
            'bounds':[p.min(axis=0).tolist(),p.max(axis=0).tolist()],
            'points':p.tolist(),'triangleRows':ordered_faces})
    return {'axis':axis,'value':value,'quantizationNativeUnits':tolerance,
        'excludedPlaneVertexFaces':int(on.sum()),'segments':len(segments),'loops':loops}


def point_inside(point, loop, axis):
    axes=[k for k in range(3) if k!=axis]; p=np.asarray(loop['points'])[:,axes]
    x,y=np.asarray(point)[axes];q=np.roll(p,-1,axis=0)
    crosses=(p[:,1]>y)!=(q[:,1]>y)
    denominator=np.where(crosses,q[:,1]-p[:,1],1.)
    return bool(np.count_nonzero(crosses & (x < (q[:,0]-p[:,0])*(y-p[:,1])/denominator+p[:,0]))%2)


def inventory(v,f,meta):
    unique,inverse=np.unique(v,axis=0,return_inverse=True); faces=inverse[f]
    edges=np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]))
    sorted_edges=np.sort(edges,axis=1)
    _,eid,counts=np.unique(sorted_edges,axis=0,return_inverse=True,return_counts=True)
    balance=np.bincount(eid,weights=np.where(edges[:,0]<edges[:,1],1.,-1.))
    graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(unique),len(unique))).tocsr()
    n,labels=connected_components(graph,directed=False)
    face_labels=labels[faces[:,0]]; area2=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
    comps=[]
    for k in range(n):
        ids=np.flatnonzero(face_labels==k);verts=unique[labels==k]
        if len(ids):comps.append({'component':k,'faces':len(ids),'bounds':[verts.min(axis=0).tolist(),verts.max(axis=0).tolist()], 'originalTriangleRowsMinMax':[int(ids.min()),int(ids.max())]})
    return {**meta,'verticesRawUV':len(v),'verticesExactCoordinateWeld':len(unique),'trianglesOriginal':len(f),
        'bounds':[v.min(axis=0).tolist(),v.max(axis=0).tolist()],
        'zeroAreaTriangles':int((area2==0).sum()),'zeroAreaRows':np.flatnonzero(area2==0).tolist(),
        'weldedBoundaryEdges':int((counts==1).sum()),'weldedOverusedEdges':int((counts>2).sum()),
        'weldedTwoFaceOrientationConflicts':int(((counts==2)&(balance!=0)).sum()),
        'components':sorted(comps,key=lambda c:-c['faces']),
        'limits':['Closed incidence does not imply absent cuffs or empty lumen. A hollow capped shell can also be a closed manifold.',
                  'Units are original model coordinates, not meters; no body fit or source mutation.']}


def controls():
    # watertight annular pipe versus same outer tube closed at its two ends.
    n=32;theta=np.arange(n)*2*np.pi/n
    rings=[np.column_stack((r*np.cos(theta),np.full(n,y),r*np.sin(theta))) for y,r in ((-1,1),(1,1),(-1,.7),(1,.7))]
    v=np.concatenate(rings);f=[]
    def join(a,b):
        for j in range(n):
            k=(j+1)%n;f.extend([[a+j,a+k,b+j],[a+k,b+k,b+j]])
    join(0,n);join(3*n,2*n);join(2*n,0);join(n,3*n)
    f=np.asarray(f); open_path=segment_hits(v,f,[0,-2,0],[0,2,0])
    assert open_path['clearSegmentWitness']
    clearance=segment_clearance(v,f,[0,-2,0],[0,2,0])
    expected=.7*np.cos(np.pi/n)
    angle=.371;rotation=np.array([[1,0,0],[0,np.cos(angle),-np.sin(angle)],[0,np.sin(angle),np.cos(angle)]])
    offset=np.array([.193,.271,-.118]);rotated_v=v@rotation.T+offset
    rotated_a=np.array([0,-2,0])@rotation.T+offset;rotated_b=np.array([0,2,0])@rotation.T+offset
    assert segment_hits(rotated_v,f,rotated_a,rotated_b)['clearSegmentWitness']
    rotated_clearance=segment_clearance(rotated_v,f,rotated_a,rotated_b)
    assert abs(rotated_clearance['minimumDistanceNativeUnits']-expected)<1e-10
    assert abs(clearance['minimumDistanceNativeUnits']-expected)<1e-10
    s=section(v,f,1,.123456); closed=[x for x in s['loops'] if x['closed']]
    assert len(closed)==2 and all(point_inside([0,.123456,0],x,1) for x in closed)
    # Cap disk crosses the same central air path, although annulus already has zero boundary.
    capped_v=np.vstack((v, [0,-1,0],[0,1,0]));cap=[]
    for j in range(n):cap.extend([[4*n,j,(j+1)%n],[4*n+1,n+(j+1)%n,n+j]])
    cap_path=segment_hits(capped_v,np.vstack((f,cap)),[0,-2,0],[0,2,0])
    assert len(cap_path['intersections'])==2 and not cap_path['clearSegmentWitness']
    hit=segment_hits(v,f,[-2,.123456,0],[2,.123456,0]);assert len(hit['intersections'])==4
    # Separate truly closed solid cylinder, same zero-boundary count as hollow annular tube.
    cylinder_f=[]
    for j in range(n):
        k=(j+1)%n;cylinder_f.extend([[j,k,n+j],[k,n+k,n+j],[4*n,k,j],[4*n+1,n+j,n+k]])
    cf=np.asarray(cylinder_f);ce=np.sort(np.concatenate([cf[:,[0,1]],cf[:,[1,2]],cf[:,[2,0]]]),axis=1)
    assert (np.unique(ce,axis=0,return_counts=True)[1]==2).all()
    solid_path=segment_hits(capped_v,cf,[0,-2,0],[0,2,0]);assert len(solid_path['intersections'])==2
    e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
    assert (np.unique(e,axis=0,return_counts=True)[1]==2).all()
    return {'passed':True,'annularTubeZeroBoundaryEdges':True,'solidCylinderZeroBoundaryEdges':True,
        'hollowTubeAxialClear':True,'solidCylinderAxialHits':2,
        'annularSectionClosedNestedLoops':2,'transverseWallCrossings':4,
        'addedCapAxialHits':2,'hollowClearance':clearance, 'hollowExpectedClearance':float(expected),'rotatedTranslatedTubeClearance':rotated_clearance,'methodLimits':'Sampled noncoplanar segment proof only; loop nesting by itself does not classify material occupancy.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    p.add_argument('--mode',choices=['inventory','measure'],required=True);p.add_argument('--spec')
    args=p.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    assert not (out/'report.json').exists()
    control=controls();save(out/'controls.json',control)
    v,f,uv,images,meta=load_glb(args.source)
    if args.mode=='inventory':report=inventory(v,f,meta)
    else:
        spec=json.loads(Path(args.spec).read_text());sections=[];paths=[]
        for s in spec['sections']:
            result=section(v,f,s['axis'],s['value'],s.get('tolerance',1e-7));result['name']=s['name'];sections.append(result)
        for s in spec['paths']:
            result=segment_hits(v,f,s['start'],s['end']);result['name']=s['name']
            if result['clearSegmentWitness']:result['clearance']=segment_clearance(v,f,s['start'],s['end'])
            for hit in result['intersections']:
                ids=f[hit['triangle']];normal=np.cross(v[ids[1]]-v[ids[0]],v[ids[2]]-v[ids[0]])
                normal=normal/np.linalg.norm(normal);direction=np.asarray(s['end'])-s['start'];direction=direction/np.linalg.norm(direction)
                hit['geometricNormal']=normal.tolist();hit['normalDotPathDirection']=float(normal@direction)
                uvpoint=np.asarray(hit['barycentric'])@uv[ids];hit['uv']=uvpoint.tolist()
                hit['texturesNearestDiagnostic']={}
                for name,im in images.items():
                    # glTF image UV origin top-left; repeat default, nearest diagnostic only.
                    h,w=im.shape[:2];x=int(np.floor((uvpoint[0]%1)*w));y=int(np.floor((uvpoint[1]%1)*h))
                    hit['texturesNearestDiagnostic'][name]=im[y,x].tolist()
            paths.append(result)
        (out/'sections.json').write_text(json.dumps(sections,separators=(',',':'),allow_nan=False)+'\n');save(out/'paths.json',paths)
        report={**meta,'specSHA256':digest(Path(args.spec).read_bytes()),'sections':len(sections),'paths':len(paths),
            'clearSegments':[x['name'] for x in paths if x['clearSegmentWitness']],
            'blockedSegments':[x['name'] for x in paths if x['intersections']],
            'ambiguousSegments':[x['name'] for x in paths if x['ambiguousCoplanar']],
            'accepted':False,'limits':'Sampled geometric witnesses, not global air topology, physical thickness, fit, deformation or art acceptance. Texture values are raw RGB nearest diagnostic, not shaded linear colors.'}
    report.update(recipeSHA256=digest(Path(__file__).read_bytes()),elapsedSeconds=round(time.monotonic()-start,3),accepted=False)
    save(out/'report.json',report);print(json.dumps({'elapsedSeconds':report['elapsedSeconds'],'out':str(out),'accepted':False}))


if __name__=='__main__':main()
