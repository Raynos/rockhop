"""Local original47 sleeve donors and matching-topology custom bake cages.

These are geometric ray origins, not inferred source-wall labels. Original
source face IDs and UV/PBR stay exact. A missing local ray refuses preparation;
no nearest-surface transfer or global geodesic classification is used.
"""


def receiver_parts(a,mesh,np):
    roles=a['faceRoles'];walls=a['faceWallKey']
    assert len(roles)==len(mesh.polygons)==len(walls)
    assert np.array_equal(a['polygonStarts'],np.asarray([p.loop_start for p in mesh.polygons]))
    assert np.array_equal(a['polygonCounts'],np.asarray([p.loop_total for p in mesh.polygons]))
    assert np.array_equal(a['cornerVertexIds'],np.asarray([l.vertex_index for l in mesh.loops]))
    keep=roles=='selected_retained'
    assert np.array_equal(keep,walls=='retained') and keep.any()
    allowed={'connected_cap','connected_arm_zipper','authored_outer','authored_inner','authored_cuff_rim'}
    assert all(str(role).rsplit('_',1)[0] in allowed for role in roles[~keep])
    assert set(walls[~keep])=={s+':'+w for s in ('L','R') for w in ('outer','inner','rim')}
    for side in ('L','R'):
        assert all(str(role).endswith('_'+side) for role in roles[np.char.startswith(walls,side+':')])
    return keep,walls


def source_patch(points,faces,side,cut_width,np):
    """Whole original triangles outside/crossing the literal77 armhole cut.

    Include one vertex-incident face ring on its retained side. Dense47 splits
    UV seams into separate IDs, so adjacency bridges exact saved positions.
    This overlap belongs only to the scratch donor; no retained panel is baked.
    """
    sign=1 if side=='L' else -1
    outside=sign*points[:,0]>=cut_width(points[:,2])
    core=np.any(outside[faces],axis=1)
    assert core.any(),('Missing actual source sleeve',side)
    _,inverse=np.unique(points,axis=0,return_inverse=True)
    incident=np.zeros(int(inverse.max())+1,bool);incident[inverse[faces[core]].ravel()]=True
    selected=core|np.any(incident[inverse[faces]],axis=1)
    ids=np.flatnonzero(selected).astype(np.int32)
    assert not np.any(sign*points[faces[ids],0]<0),('Local sleeve donor crosses body midline',side)
    return ids,{'actualSourceTriangles':len(ids),'outsideOrCrossingCutTriangles':int(core.sum()),
        'retainedSideOverlapTriangles':int(np.sum(selected&~core)),
        'selection':'Whole original47 triangles outside/crossing actual77 cut_width plus one exact-position vertex-incident face ring'}


def centerline(points,rest,side,np):
    """Project onto the actual two native75 arm segments, never onto a source surface."""
    bones={r[0]:r for r in rest}
    s,e,w=[np.asarray(bones[n+'.'+side][2],np.float64) for n in ('DEF-upper_arm','DEF-forearm','DEF-hand')]
    segments=[]
    for a,b in ((s,e),(e,w)):
        axis=b-a;t=np.clip((points-a)@axis/(axis@axis),0,1)
        centers=a+t[:,None]*axis;segments.append((np.sum((points-centers)**2,axis=1),centers))
    use_lower=segments[1][0]<segments[0][0]
    centers=np.where(use_lower[:,None],segments[1][1],segments[0][1])
    return centers,(w-e)/np.linalg.norm(w-e),w


def first_hit(tree,origin,direction,maximum,Vector,np):
    assert np.isfinite(origin).all() and np.isfinite(direction).all() and maximum>0
    hit=tree.ray_cast(Vector(origin),Vector(direction),float(maximum))
    assert hit[0] is not None,'Actual local source ray misses: fit the selected highpoly derivative/cage before baking'
    point,normal=np.asarray(hit[0],float),np.asarray(hit[1],float)
    assert np.dot(normal,direction)<0,'First local source hit is back-facing: wrong side or source fold; no fallback'
    return point,int(hit[2]),float(hit[3])


def cage(points,faces,source_points,source_faces,tree,rest,key,Vector,np):
    """Use shared receiver vertices and finite exterior/cavity/distal origins.

    The custom-cage ray points from this origin through the actual receiver.
    The exterior begins beyond all donor vertices in its ray direction. The
    cavity begins between its native arm axis and the first facing inner hit.
    Cuff origins lie beyond the complete local donor on the native forearm axis.
    """
    side,wall=key.split(':');centers,axis,wrist=centerline(points,rest,side,np)
    radial=points-centers;radius=np.linalg.norm(radial,axis=1)
    assert np.all(radius>0)
    radial/=radius[:,None]
    # An arithmetic separation from the actual donor bounds, not a wall label
    # or a tunable nearest-hit tolerance.
    span=float(np.linalg.norm(np.ptp(source_points,axis=0)))
    padding=32*np.finfo(np.float32).eps*max(1.,span)
    from itertools import product
    bounds=np.asarray(list(product(*zip(source_points.min(0),source_points.max(0)))))
    origins=np.empty_like(points,dtype=np.float64)
    for i,(p,c,d) in enumerate(zip(points,centers,radial)):
        if wall=='outer':
            extent=max(float(np.max((bounds-c)@d)),float(radius[i]))+padding
            origins[i]=c+d*extent
        elif wall=='inner':
            _,_,distance=first_hit(tree,c,d,span+float(np.linalg.norm(p-c)),Vector,np)
            origins[i]=c+d*min(distance,radius[i])*.5
        else:
            assert wall=='rim'
            extent=max(float(np.max((bounds-p)@axis)),0.)+padding
            origins[i]=p+axis*extent
    # Float32 is the actual saved cage position precision. Verify these bytes,
    # not a different float64 cage that Blender will never see.
    origins=origins.astype(np.float32)
    tri=origins[faces];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
    assert np.all(area>0),('Collapsed matching-topology cage',key)
    # Cuff rays stop at the actual receiver rim's proximal extent plus one
    # actual source triangle edge, so the forearm cannot substitute for a cuff.
    source_tri=source_points[source_faces]
    edge=max(float(np.linalg.norm(source_tri[:,i]-source_tri[:,j],axis=1).max())
             for i,j in ((0,1),(1,2),(2,0)))
    cuff_floor=float(np.min((points-wrist)@axis))-edge
    samples_p=np.concatenate([points,points[faces].mean(1)])
    samples_c=np.concatenate([origins,origins[faces].mean(1)])
    samples_center=np.concatenate([centers,centers[faces].mean(1)])
    ids=[];distances=[]
    for p,c,center in zip(samples_p,samples_c,samples_center):
        direction=p-c;length=np.linalg.norm(direction);assert length>0;direction/=length
        if wall=='outer':
            limit=float((center-c)@direction)
        elif wall=='inner':
            limit=float(np.linalg.norm(p-center))+span
        else:limit=float((c-wrist)@axis)-cuff_floor
        q,fi,distance=first_hit(tree,c,direction,limit,Vector,np)
        if wall!='rim':
            assert float((q-center)@(p-center))>0,('Ray crossed to opposite sleeve wall',key)
        ids.append(fi);distances.append(distance)
    envelope=np.concatenate([bounds,origins])
    ray_limit=float(np.linalg.norm(np.ptp(envelope,axis=0)))+padding
    return origins,{'maximumBakeRayDistanceLocalM':ray_limit,'vertexAndFaceCenterRays':len(ids),'firstHitLocalFaceIds':ids,
        'maximumObservedHitDistanceM':max(distances),'minimumCageTriangleAreaM2':float(area.min()/2),'cuffProximalStop':cuff_floor,
        'sourceCoverage':'Actual first-hit vertices and face centers only; complete texel coverage is required by the native bake',
        'rayOrigin':{'outer':'outside complete local source toward native arm axis',
                     'inner':'inside cavity toward receiver', 'rim':'beyond source cuff toward forearm'}[wall]}
