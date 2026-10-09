"""Selected dense topology domains and exact corner-ancestry cage positions.

Cuts and seeds are actual dense47 vertex/face IDs from independently traced
selected seams. No global nearest, normal-only wall classification or inferred
future domain is available here. Mixed/unseparated wall anchors refuse.
"""
from collections import defaultdict,deque


def closest(point,triangle,np):
    """Recompute the actual closest point, including literal triangle edges.

    Boundary coefficients come from an edge segment solve, not from clamping
    an almost-negative projected barycentric row from Blender's float BVH.
    """
    triangle=np.asarray(triangle,np.float64);point=np.asarray(point,np.float64)
    a,b=triangle[1]-triangle[0],triangle[2]-triangle[0]
    q=point-triangle[0];aa,ab,bb=a@a,a@b,b@b;det=aa*bb-ab*ab
    assert det>0,'Degenerate dense ancestor triangle'
    v=(bb*(q@a)-ab*(q@b))/det;w=(aa*(q@b)-ab*(q@a))/det
    candidate=np.asarray([1-v-w,v,w]);best=None;distance=float('inf')
    if np.all(candidate>=0):
        best=candidate;distance=float(np.sum((candidate@triangle-point)**2))
    for i,j in ((0,1),(1,2),(2,0)):
        edge=triangle[j]-triangle[i];norm=edge@edge;assert norm>0
        t=min(1.,max(0.,float((point-triangle[i])@edge/norm)))
        coefficients=np.zeros(3);coefficients[i]=1-t;coefficients[j]=t
        actual=float(np.sum((coefficients@triangle-point)**2))
        if actual<distance:best,distance=coefficients,actual
    assert best is not None and np.all(best>=0)
    return best


def domains(points,faces,cuts,anchors,np):
    # Original dense source splits UV/normal vertices into49,287 islands.
    # Equal saved positions bridge those islands without changing one vertex.
    _,inverse=np.unique(points,axis=0,return_inverse=True)
    original_faces=faces;faces=inverse[faces]
    edges=defaultdict(list)
    for fi,face in enumerate(faces):
        for a,b in zip(face,(face[1],face[2],face[0])):
            edges[tuple(sorted((int(a),int(b))))].append(fi)
    assert all(len(edge)==2 and all(isinstance(i,int) and 0<=i<len(points) for i in edge) for edge in cuts)
    cuts={tuple(sorted(int(inverse[i]) for i in edge)) for edge in cuts}
    assert cuts <= set(edges),'Traced source cut is not an actual dense47 edge'
    adjacency=[[] for _ in faces]
    for edge,rows in edges.items():
        if edge in cuts:continue
        assert len(rows)<=2,('Nonmanifold source edge needs explicit traced cut',edge,len(rows))
        if len(rows)==2:
            a,b=rows;adjacency[a].append(b);adjacency[b].append(a)
    component=[-1]*len(faces);members=[]
    for start in range(len(faces)):
        if component[start]>=0:continue
        identity=len(members);queue=deque([start]);rows=[];component[start]=identity
        while queue:
            face=queue.popleft();rows.append(face)
            for other in adjacency[face]:
                if component[other]<0:component[other]=identity;queue.append(other)
        members.append(rows)
    ownership={};labelled={}
    for key,seeds in anchors.items():
        assert seeds,('Absent literal source seam anchors',key)
        assert all(isinstance(i,int) and 0<=i<len(faces) for i in seeds),('Invalid actual dense face anchor',key)
        ids={component[int(i)] for i in seeds}
        for identity in ids:
            assert identity not in ownership or ownership[identity]==key, (
                'Actual cuts do not separate selected source wall anchors',key,ownership.get(identity),identity)
            ownership[identity]=key
        labelled[key]=sorted(i for identity in sorted(ids) for i in members[identity])
    return labelled,{'actualDenseTriangles':len(faces),'actualCutEdges':len(cuts),
        'connectedComponents':len(members),'labelledFaceCounts':{k:len(v) for k,v in labelled.items()},
        'unassignedFaces':sum(len(rows) for i,rows in enumerate(members) if i not in ownership),
        'classification':'Connected original dense triangle topology, bridging only byte-exact position triples, after explicit traced source-edge cuts; no proximity/orientation wall labels'}


def positions(target_points,source_points,source_faces,face_ids,bary,domain_faces,np,extension=.001):
    ids=np.asarray(face_ids,np.int64);bary=np.asarray(bary,np.float64)
    assert ids.shape==(len(target_points),) and bary.shape==(len(ids),3)
    assert np.isfinite(bary).all() and np.all(bary>=0)
    residual=float(np.max(abs(bary.sum(1)-1)))
    assert residual<=4*np.finfo(np.float32).eps,'Stored source barycentric coefficients are not affine within float32 arithmetic'
    assert np.all((ids>=0)&(ids<len(source_faces)))
    allowed=set(map(int,domain_faces))
    assert set(map(int,ids))<=allowed,'Exact appearance ancestry leaves its selected source wall domain'
    tri=source_points[source_faces[ids]].astype(np.float64)
    q=np.sum(tri*bary[:,:,None],axis=1)
    delta=q-target_points;length=np.linalg.norm(delta,axis=1)
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(normal,axis=1)
    assert np.all(area>0),'Degenerate actual dense ancestor face'
    normal/=area[:,None]
    direction=normal.copy();different=length>0
    direction[different]=delta[different]/length[different,None]
    cage=q+direction*extension
    assert np.isfinite(cage).all()
    # Every nonzero ray passes through its exact source-triangle barycentric
    # point before reaching this actual receiver corner, even at39mm offset.
    return cage,q,{'corners':len(ids),'maximumActualSourceToReceiverM':float(length.max()),
        'extensionBeyondAncestralPointM':extension,'sourceFaces':len(allowed),
        'maximumStoredBarycentricSumResidual':residual,'sourceCoefficientsRenormalized':False,
        'method':'Exact dense face/barycentric source point extended along actual source-to-receiver segment; zero-length case uses that same face normal'}
