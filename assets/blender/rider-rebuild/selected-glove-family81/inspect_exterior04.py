"""Independent saved-array ancestry, full-field and sewn-topology inspection.

This is not a surface/deformation/bake/appearance acceptance gate.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
ROOT=Path(__file__).resolve().parents[4]


def pin(path):
    path=Path(path).resolve()
    return {'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def checked(row):
    path=(ROOT/row['path']).resolve()
    assert path.is_relative_to(ROOT) and pin(path)==row
    return path


def main(file):
    file=Path(file).resolve(); r=json.loads(file.read_text())
    assert r['acceptedArt'] is False and r['policy']['maximumAttempts']==1 and r['policy']['optimizerCalls']==0
    for key in ('recipe','geometryRecipe','cpuAdmission','extraction','sourceReceipt','nativeSource','surfaceLandmarks'): checked(r[key])
    e=json.loads(checked(r['extraction']).read_text()); source=e['objects']['ActualSelectedGlove.R']
    assert r['sourceArrays']==source['arrays'] and r['sourceAncestry']==source['ancestry']
    assert r['groupNames']==source['groupNames'] and len(r['groupNames'])==75
    with np.load(checked(r['sourceArrays']),allow_pickle=False) as raw: a={key:raw[key] for key in raw.files}
    with np.load(checked(r['sourceAncestry']),allow_pickle=False) as raw: ancestry={key:raw[key] for key in raw.files}
    with np.load(checked(r['candidate']),allow_pickle=False) as raw: c={key:raw[key] for key in raw.files}
    p=c['positions']; f=c['triangles']; parent_faces=c['sourceFaceIds']; bary=c['barycentric']
    assert p.dtype==np.float32 and f.dtype==np.int32 and bary.dtype==np.float64
    assert np.isfinite(p).all() and np.isfinite(bary).all() and (bary>=0).all()
    assert ((f>=0)&(f<len(p))).all() and ((parent_faces>=0)&(parent_faces<len(a['triangles']))).all()
    assert np.max(np.abs(bary.sum(1)-1))<=4*np.finfo(np.float64).eps
    parents=a['triangles'][parent_faces]; source_points=a['positions'][parents].astype(np.float64)
    reconstructed=np.einsum('ij,ijk->ik',bary,source_points).astype(np.float32)
    assert np.array_equal(p,reconstructed), 'Target positions do not match their exact stored source ancestry'
    so,si,sw=a['fieldOffsets'],a['fieldIndices'],a['fieldWeights']
    co,ci,cw=c['fieldOffsets'],c['fieldIndices'],c['fieldWeights']
    assert co[0]==0 and co[-1]==len(ci)==len(cw) and len(co)==len(p)+1 and (np.diff(co)>0).all()
    assert np.isfinite(cw).all() and ((cw>=0)&(cw<=1)).all()
    dense=np.zeros((len(a['positions']),75),np.float64)
    dense[np.repeat(np.arange(len(dense)),np.diff(so)),si]=sw
    expected=np.sum(dense[parents]*bary[:,:,None],axis=1).astype(np.float32)
    actual=np.zeros((len(p),75),np.float32)
    actual[np.repeat(np.arange(len(p)),np.diff(co)),ci]=cw
    assert np.array_equal(actual,expected), 'Full named field transport differs'
    for vertex in range(len(p)):
        expected_order=[]; seen=set()
        for parent,coefficient in zip(parents[vertex],bary[vertex]):
            if coefficient==0: continue
            for group in si[so[parent]:so[parent+1]]:
                if int(group) not in seen: seen.add(int(group)); expected_order.append(int(group))
        assert ci[co[vertex]:co[vertex+1]].tolist()==expected_order, 'A raw membership was pruned, duplicated or reordered'
    for i in range(len(source['uvLayerNames'])):
        uv=np.einsum('ij,ijk->ik',bary,a['uvLayer'+str(i)][a['triangleLoopIds'][parent_faces]]).astype(np.float32)
        assert np.array_equal(c['sourceSampleUV'+str(i)],uv)
    # Topology is checked from saved indices, independently of the constructor graph.
    incidence=defaultdict(list); adjacency=defaultdict(set)
    for face,t in enumerate(f):
        for x,y in zip(t,np.roll(t,-1)):
            x,y=int(x),int(y); incidence[tuple(sorted((x,y)))].append((face,x,y)); adjacency[x].add(y); adjacency[y].add(x)
    boundary=[rows[0][1:] for rows in incidence.values() if len(rows)==1]
    manifold=all(len(rows)<=2 and (len(rows)==1 or rows[0][1:]==rows[1][1:][::-1]) for rows in incidence.values())
    components=0; remaining=set(range(len(p)))
    while remaining:
        components+=1; stack=[remaining.pop()]
        while stack:
            for neighbour in adjacency[stack.pop()]:
                if neighbour in remaining: remaining.remove(neighbour); stack.append(neighbour)
    expected_boundary=c['expectedOpenBoundaryVertices'].tolist()
    assert len(expected_boundary)==len(set(expected_boundary))==64
    expected_edges={tuple(sorted((a,b))) for a,b in zip(expected_boundary,expected_boundary[1:]+expected_boundary[:1])}
    boundary_exact={tuple(sorted(edge)) for edge in boundary}==expected_edges and len(boundary)==64
    triangle_keys=Counter(tuple(sorted(t)) for t in f.tolist()); duplicate_faces=sum(n-1 for n in triangle_keys.values() if n>1)
    links=defaultdict(lambda:defaultdict(list)); bad_links=[]; boundary_vertices=set(expected_boundary)
    for t in f.tolist():
        for v,x,y in ((t[0],t[1],t[2]),(t[1],t[2],t[0]),(t[2],t[0],t[1])):
            links[v][x].append(y); links[v][y].append(x)
    for v,link in links.items():
        degrees=sorted(map(len,link.values())); wanted=([1,1]+[2]*(len(link)-2)) if v in boundary_vertices else [2]*len(link)
        reached=set(); pending=[next(iter(link))]
        while pending:
            x=pending.pop()
            if x not in reached: reached.add(x); pending.extend(link[x])
        if degrees!=wanted or len(reached)!=len(link): bad_links.append(v)
    pp=p[f].astype(np.float64); cross=np.cross(pp[:,1]-pp[:,0],pp[:,2]-pp[:,0]); double_area=np.linalg.norm(cross,axis=1)
    positive=double_area>0; normals=np.divide(cross,double_area[:,None],out=np.zeros_like(cross),where=positive[:,None])
    # Angle-weighted geometric vertex normals; no copied shading normal can hide reversals.
    vertex_normals=np.zeros_like(p,dtype=np.float64)
    for corner in range(3):
        x=pp[:,(corner+1)%3]-pp[:,corner]; y=pp[:,(corner+2)%3]-pp[:,corner]
        angles=np.arctan2(np.linalg.norm(np.cross(x,y),axis=1),np.sum(x*y,axis=1))
        np.add.at(vertex_normals,f[:,corner],normals*angles[:,None])
    zero_vertex=np.flatnonzero(np.linalg.norm(vertex_normals,axis=1)==0)
    centroid_faces=c['centroidSourceFaceIds']; cb=c['centroidBarycentric']
    assert ((centroid_faces>=0)&(centroid_faces<len(a['triangles']))).all() and np.isfinite(cb).all() and (cb>=0).all()
    assert np.max(np.abs(cb.sum(1)-1))<=4*np.finfo(np.float64).eps
    sp=a['positions'][a['triangles'][centroid_faces]].astype(np.float64)
    source_cross=np.cross(sp[:,1]-sp[:,0],sp[:,2]-sp[:,0]); source_length=np.linalg.norm(source_cross,axis=1)
    assert (source_length>0).all()
    source_normal=source_cross/source_length[:,None]
    dots=np.sum(normals*source_normal,axis=1); distances=np.linalg.norm(pp.mean(1)-np.sum(sp*cb[:,:,None],axis=1),axis=1)
    inner=(ancestry['authoredVertexRoles'][a['triangles'][centroid_faces]]==3).all(1)
    roles=ancestry['authoredFaceRoles'][centroid_faces]; wall=c['centroidWalls']
    assert np.all(((wall=='outer')&(roles!=2))|((wall=='inner')&inner)|((wall=='rim')&(roles==2)&~inner))
    bad_normals=np.flatnonzero(dots<r['policy']['minimumNormalDot']); bad_distance=np.flatnonzero(distances>r['policy']['maximumSurfaceErrorM'])
    references=np.unique(f); euler=len(p)-len(incidence)+len(f)
    topology=manifold and not bad_links and components==1 and boundary_exact and duplicate_faces==0 and positive.all() and len(references)==len(p) and euler==1
    passed=bool(topology and len(zero_vertex)==0 and len(bad_normals)==0 and len(bad_distance)==0)
    result={'status':'EXTERIOR04_SAVED_ARRAY_INSPECTION_PASSED_UNACCEPTED' if passed else 'EXTERIOR04_SAVED_ARRAY_INSPECTION_FAILED_UNACCEPTED',
        'acceptedArt':False,'inspector':pin(__file__),'construction':pin(file),'candidate':r['candidate'],
        'exactSourceAncestryPositions':True,'all75RawNamedFieldsTransported':True,'sourceRawCSRUnmodified':True,
        'sourceUVCorrespondenceExact':True,'vertices':len(p),'triangles':len(f),'memberships':len(cw),
        'maximumMemberships':int(np.diff(co).max()),'rawWeightSumRange':[float(actual.astype(np.float64).sum(1).min()),float(actual.astype(np.float64).sum(1).max())],
        'components':components,'manifoldConsistentDirectedEdges':manifold,'exact64EdgeWristOpening':boundary_exact,
        'nonmanifoldVertexLinkIds':bad_links,
        'eulerCharacteristic':euler,'duplicateOrOppositeFaces':duplicate_faces,'zeroAreaFaces':int((~positive).sum()),
        'unreferencedVertices':len(p)-len(references),'undefinedGeometricVertexNormalIds':zero_vertex.tolist(),
        'sameWallCentroidNormalMinimumDot':float(dots.min()),'sameWallCentroidNormalFailures':bad_normals.tolist(),
        'sameWallCentroidMaximumDistanceM':float(distances.max()),'sameWallCentroidDistanceFailures':bad_distance.tolist(),
        'limits':'Finite candidate samples only. No full bidirectional surface/contact/grip/lean proof, native reopen, target atlas, source bake, whole-rider moving art or device acceptance.'}
    out=file.with_name('inspection.json')
    with out.open('x') as stream: json.dump(result,stream,indent=2); stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)},indent=2))
    return 0 if passed else 2


if __name__=='__main__':
    assert len(sys.argv)==2
    raise SystemExit(main(sys.argv[1]))
