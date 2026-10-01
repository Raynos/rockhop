"""Actual native anatomical graft continuation of source-sheet clipping."""
from scipy.interpolate import RBFInterpolator
from geometry_checks import surface_clearance,topology as eye_topology,self_test
assert self_test()['pass']

NATIVE=ROOT/'rig-adapter01/anatomical-eye-donor01/standalone01'
bridge=[];graft_reports=[];rays=[]
def surface_hit(points,faces,y,z):
    xyz=points[faces];yz=xyz[:,:,1:];p=np.array([y,z])
    eligible=np.flatnonzero((yz.min(1)<=p+1e-10).all(1)&(yz.max(1)>=p-1e-10).all(1))
    a=yz[eligible,1]-yz[eligible,0];b=yz[eligible,2]-yz[eligible,0];d=p-yz[eligible,0]
    det=a[:,0]*b[:,1]-a[:,1]*b[:,0];keep=abs(det)>1e-15
    eligible=eligible[keep];a=a[keep];b=b[keep];d=d[keep];det=det[keep]
    u=(d[:,0]*b[:,1]-d[:,1]*b[:,0])/det;q=(a[:,0]*d[:,1]-a[:,1]*d[:,0])/det
    bary=np.c_[1-u-q,u,q];inside=(bary>=-1e-8).all(1)
    return None if not inside.any() else float(np.max(np.sum(bary[inside]*xyz[eligible[inside],:,0],axis=1)))

def ordered(loop,cy,cz,points):
    loop=np.array(loop);p=points[loop,1:]-[cy,cz]
    if np.sum(p[:,1]*np.roll(p[:,0],-1)-p[:,0]*np.roll(p[:,1],-1))<0:loop=loop[::-1]
    loop=np.roll(loop,-int(np.argmax(points[loop,2])))
    lengths=np.linalg.norm(np.roll(points[loop],-1,axis=0)-points[loop],axis=1)
    return loop,np.r_[0,np.cumsum(lengths[:-1])]/lengths.sum()*2*np.pi

def zipper(a,aa,b,bb):
    i=j=0;result=[]
    while i<len(a) or j<len(b):
        na=aa[(i+1)%len(a)]+(2*np.pi if i+1>=len(a) else 0) if i<len(a) else np.inf
        nb=bb[(j+1)%len(b)]+(2*np.pi if j+1>=len(b) else 0) if j<len(b) else np.inf
        if na<=nb:result.append([int(a[i%len(a)]),int(b[j%len(b)]),int(a[(i+1)%len(a)])]);i+=1
        else:result.append([int(a[i%len(a)]),int(b[j%len(b)]),int(b[(j+1)%len(b)])]);j+=1
    return np.array(result,dtype=int)

def orient_strip(strip,reference,reference_vertices):
    points=np.array(expanded['POSITION'],dtype='<f4')
    _,canonical=np.unique(points,axis=0,return_inverse=True)
    directed=set((int(a),int(b)) for f in canonical[reference] for a,b in zip(f,np.roll(f,-1)))
    physical_vertices=set(canonical[list(reference_vertices)])
    shared=[(int(a),int(b)) for f in canonical[strip] for a,b in zip(f,np.roll(f,-1)) if a in physical_vertices and b in physical_vertices]
    same=sum(edge in directed for edge in shared);opposite=sum(edge[::-1] in directed for edge in shared)
    assert same+opposite==len(shared) and (same==0 or opposite==0),'Consistent existing seam winding'
    return strip[:,::-1] if same else strip

def add_points(points,normals=None):
    indices=[]
    for i,point in enumerate(points):
        indices.append(len(expanded['POSITION']))
        for key in expanded:
            expanded[key].append({'POSITION':point,'NORMAL':normals[i] if normals is not None else [1.,0,0],
                'TEXCOORD_0':[.5,.5],'JOINTS_0':[4,0,0,0],'WEIGHTS_0':[1.,0,0,0]}[key])
    return np.array(indices)

def native_loops(quads):
    count=Counter(tuple(sorted((int(a),int(b)))) for f in quads for a,b in zip(f,np.roll(f,-1)))
    edges=[edge for edge,n in count.items() if n==1];adj=defaultdict(list)
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    assert all(len(n)==2 for n in adj.values());unseen=set(adj);result=[]
    while unseen:
        first=min(unseen);loop=[first];prev=None;cur=first
        while True:
            nxt=next(n for n in adj[cur] if n!=prev)
            if nxt==first:break
            assert nxt not in loop;loop.append(nxt);prev,cur=cur,nxt
        unseen-=set(loop);result.append(loop)
    return result

def eye_geometry(prefix,cy,cz,apex,shift=0):
    result=[]
    for suffix in ['cornea','sclera_iris']:
        mesh=next(m for m in ddoc['meshes'] if m['name']==prefix+'_'+suffix);p0=mesh['primitives'][0]
        points=array(ddoc,dbin,p0['attributes']['POSITION']).astype(float)
        offset=np.array([apex-.0152355616+shift,cy,cz-(-.033 if prefix=='R' else .033)])
        result.append((points+offset,array(ddoc,dbin,p0['indices']).reshape(-1,3)))
    return result

eye_shifts={}
for eye,cy,cz,apex in SEEDS:
    rings=[l for l in loops if np.max(abs(positions[l,1]-cy))<INNER_HEIGHT+.0001 and np.max(abs(positions[l,2]-cz))<INNER_WIDTH+.0001]
    assert len(rings)==2;rings.sort(key=lambda l:positions[l,0].mean(),reverse=True)
    front,fa=ordered(rings[0],cy,cz,positions);back,ba=ordered(rings[1],cy,cz,positions)
    native_side='R' if eye=='positiveZ' else 'L';prefix='L' if eye=='positiveZ' else 'R'
    nd=np.load(NATIVE/f'fitted-native-{native_side}-lids.npz')
    raw_native=nd['positions'].copy();np0=raw_native.copy();nq=nd['quads'];boundary=native_loops(nq)
    assert len(boundary)==2
    boundary.sort(key=lambda l:np.ptp(np0[l,1])*np.ptp(np0[l,2]),reverse=True)
    outer=boundary[0];inner=boundary[1]
    neighbors=defaultdict(set)
    for f in nq:
        for a,b in zip(f,np.roll(f,-1)):neighbors[int(a)].add(int(b));neighbors[int(b)].add(int(a))
    distances={i:0 for i in outer};fringe=set(outer)
    for depth in range(1,3):
        nxt={b for a in fringe for b in neighbors[a]}-set(distances)
        distances.update({i:depth for i in nxt});fringe=nxt
    shifts=[]
    for i in outer:
        angle=np.arctan2((np0[i,1]-cy)/HEIGHT,(np0[i,2]-cz)/WIDTH)
        yy=cy+.90*HEIGHT*np.sin(angle);zz=cz+.90*WIDTH*np.cos(angle)
        xx=surface_hit(v,tri,yy,zz);assert xx is not None
        shifts.append(np.array([xx,yy,zz])-np0[i])
    shifts=np.array(shifts)
    for i,depth in distances.items():
        if depth>=2:continue
        nearest=int(np.argmin(np.linalg.norm(raw_native[outer]-raw_native[i],axis=1)))
        np0[i]+=shifts[nearest]*(1. if depth==0 else .5)
    assert np.array_equal(np0[inner],raw_native[inner]),'Actual native anatomical aperture preserved'
    indices=add_points(np0,nd['normals']);nt=np.concatenate([nq[:,[0,1,2]],nq[:,[0,2,3]]])
    nt=indices[nt];current=np.array(expanded['POSITION'],dtype='<f4')
    outloop,oa=ordered(indices[outer],cy,cz,current);inloop,ia=ordered(indices[inner],cy,cz,current)
    join=orient_strip(zipper(front,fa,outloop,oa),output,set(front))
    wall=orient_strip(zipper(inloop,ia,back,ba),nt,set(inloop))
    local=np.concatenate([nt,join,wall]);bridge.extend(local.tolist())
    # Actual surfaces are open-backed; test their triangles rather than
    # demanding every inward wall be in front of a single corneal ray.
    candidates=[];selected=None
    tissue=current[local].astype(float)
    for depth_mm in np.arange(0.,8.0001,.25):
        shift=-float(depth_mm)/1000
        cornea,iris=eye_geometry(prefix,cy,cz,apex,shift)
        checks={}
        for category,faces in [('native_lid',nt),('front_join',join),('inward_wall',wall)]:
            for donor_category,(ep,ef) in [('cornea',cornea),('opaque_sclera_iris',iris)]:
                checks[category+'/'+donor_category]=surface_clearance(current[faces].astype(float),ep[ef],reach=.00025)
        safe=all(row['distanceLowerBoundM']>=.00010 for row in checks.values())
        visibility=[]
        for yy,zz in [(cy,cz),(cy-.002,cz),(cy+.002,cz),(cy,cz-.005),(cy,cz+.005)]:
            ix=surface_hit(*iris,yy,zz)
            gx=surface_hit(current,local,yy,zz);sx=surface_hit(positions,output,yy,zz)
            visible=ix is not None and (gx is None or ix>gx+.0001) and (sx is None or ix>sx+.0001)
            visibility.append({'y':yy,'z':zz,'irisFrontX':ix,'nativeGraftFrontX':gx,'retainedSkinFrontX':sx,'visible':visible})
        candidate={'depthShiftM':shift,'actualSurfaceChecks':checks,'apertureRays':visibility,'safe':safe,'allApertureRaysVisible':all(q['visible'] for q in visibility)}
        candidates.append(candidate)
        if safe and candidate['allApertureRaysVisible']:
            selected=candidate;break
    if selected is None:
        np.savez_compressed(OUT/'native-graft-failure.npz',positions=current,sourceTriangles=output,nativeTriangles=nt,
            frontJoinTriangles=join,inwardWallTriangles=wall,nativeSourcePositions=raw_native,nativeRegisteredPositions=np0,
            actualCorneaPositions=eye_geometry(prefix,cy,cz,apex)[0][0],actualCorneaTriangles=cornea[1],
            actualIrisPositions=eye_geometry(prefix,cy,cz,apex)[1][0],actualIrisTriangles=iris[1])
        failure={'status':'REJECTED before export; no measured surface-safe and visible fit within8mm','eye':eye,
            'sourceSHA256':hashlib.sha256(raw).hexdigest(),'candidateExported':False,'GPUWorkPerformed':False,
            'fitBoundM':.008,'clearanceRequiredM':.00010,'fitTrials':candidates,
            'donorTopology':{'cornea':eye_topology(*cornea),'opaque_sclera_iris':eye_topology(*iris)},
            'surgicalROI':{'outerHalfWidthM':WIDTH,'outerHalfHeightM':HEIGHT,'innerHalfWidthM':INNER_WIDTH,'innerHalfHeightM':INNER_HEIGHT,'innerFaceClassifier':'frozen physical-edge connectivity/depth-landmark sheet selection','outerMinimumXM':.72,'innerMinimumXM':.69},
            'nativeAperturePositionsExact':np.array_equal(np0[inner],raw_native[inner]),
            'limits':['Actual donor components remain open-backed; no closed sphere containment claimed.','Opaque iris and sclera are tested together as their actual shared mesh; no untested surface is dropped.','No source conservation or full export validation was reached.']}
        (EVIDENCE/'native-graft-failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        print(json.dumps({'status':failure['status'],'eye':eye,'trials':len(candidates)},indent=2));raise SystemExit(1)
    shift=selected['depthShiftM'];eye_shifts[prefix]=shift
    rays.extend([dict(eye=eye,**r) for r in selected['apertureRays']])
    graft_reports.append({'eye':eye,'selectedActualSurfaceCheck':selected,'fitTrials':candidates,
        'donorTopology':{'cornea':eye_topology(*cornea),'opaque_sclera_iris':eye_topology(*iris)}})
    graft_reports.append({'eye':eye,'nativeSide':native_side,'originalNativeQuads':len(nq),'nativeApertureVertices':len(inner),
        'nativeAperturePositionsExact':True,'outerRegistrationBandMaxGraphDepth':1,
        'maxOuterBoundaryRegistrationM':float(np.linalg.norm(shifts,axis=1).max()),
        'actualEyeDepthShiftM':shift,'exactTriangleSurfaceChecks':True,'clearanceRequiredM':.00010,
        'nativeTriangles':len(nt),'sourceJoinTriangles':len(join),'inwardWallTriangles':len(wall)})

positions=np.array(expanded['POSITION'],dtype='<f4');bridge=np.array(bridge,dtype=np.int64)
joined=np.concatenate([output,bridge]);final,_,finaldirected,_=topology(positions,joined)
assert final==before,(before,final)
oriented=Counter(map(tuple,finaldirected.tolist()));assert max(oriented.values())==1,'Joined surface winding consistent'
areas=np.linalg.norm(np.cross(positions[joined[:,1]]-positions[joined[:,0]],positions[joined[:,2]]-positions[joined[:,0]]),axis=1)/2
assert areas.min()>1e-14 and np.isfinite(positions).all()

# Freeze CPU geometry only; independent conservation and skin/normal gates
# precede any GLB export. This is the single construction, not a new model.
np.savez_compressed(OUT/'geometry-preexport.npz',positions=positions,sourceTriangles=output,graftTriangles=bridge,
    sourceTriangleProvenance=np.array(conforming_origins,dtype=np.int32),surgicallyChangedSourceFaces=np.array(changed,dtype=np.int32),
    **{'attribute_'+key:np.array(value,dtype=attrs[key].dtype) for key,value in expanded.items()})
report={'status':'UNACCEPTED CPU native graft geometry; not exported','sourceSHA256':hashlib.sha256(raw).hexdigest(),
    'body11Unchanged':source.read_bytes()==raw,'candidateExported':False,'GPUWorkPerformed':False,
    'surgicalROI':{'outerHalfWidthM':WIDTH,'outerHalfHeightM':HEIGHT,'innerHalfWidthM':INNER_WIDTH,'innerHalfHeightM':INNER_HEIGHT,
        'innerFaceClassifier':'frozen physical-edge connectivity/depth-landmark sheet selection','outerMinimumXM':.72,'innerMinimumXM':.69},
    'sourceTopology':before,'joinedTopology':final,'minimumJoinedTriangleAreaM2':float(areas.min()),
    'nativeGrafts':graft_reports,'apertureRays':rays,'elapsedSeconds':time.monotonic()-start,
    'limits':['Conservation, UV baking, physical normal continuity and parent appearance gates are pending before export.','No closed donor volume is assumed; actual open cornea and combined opaque sclera/iris surfaces were checked.']}
(EVIDENCE/'geometry-preexport.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['nativeGrafts','apertureRays']},indent=2))
