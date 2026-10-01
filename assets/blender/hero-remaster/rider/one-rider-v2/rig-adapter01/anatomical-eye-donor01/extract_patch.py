"""Extract actual native CC0 quad lids around the closed posterior socket cup.

No analytic eyelid rings. Source quad connectivity and 3D relief are retained.
Output is a standalone fitted anatomical donor proposal, not a joined rider.
"""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/anatomical-eye-donor01')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/anatomical-eye-donor01')
DEST=ROOT/'standalone01'
assert not DEST.exists(),'Frozen standalone donor is never overwritten'
DEST.mkdir()
source=ROOT/'native-source.npz';raw=source.read_bytes();data=np.load(source)
v=data['positions'];uv=data['uv'];quads=data['quads'];puv=data['quadUVIndices'];sourceids=data['sourceFaceIDs']
edges=defaultdict(list)
for fi,face in enumerate(quads):
    for a,b in zip(face,np.roll(face,-1)):edges[tuple(sorted((int(a),int(b))))].append(fi)
adj=defaultdict(set)
for faces in edges.values():
    assert len(faces)==2,'Native full body is closed manifold'
    adj[faces[0]].add(faces[1]);adj[faces[1]].add(faces[0])

def loops(selected):
    counter=Counter(tuple(sorted((int(a),int(b)))) for fi in selected for a,b in zip(quads[fi],np.roll(quads[fi],-1)))
    boundary=np.array([edge for edge,n in counter.items() if n==1],dtype=int).reshape(-1,2)
    matrix=coo_matrix((np.ones(len(boundary)),(boundary[:,0],boundary[:,1])),shape=(len(v),len(v))).tocsr()
    _,label=connected_components(matrix,directed=False)
    result=[]
    for n in np.unique(label[np.unique(boundary)]):
        local=boundary[label[boundary[:,0]]==n];ids=np.unique(local);degrees=Counter(local.ravel())
        result.append({'vertices':len(ids),'vertexIDs':ids.tolist(),'degreeHistogram':dict(Counter(degrees.values())),
            'boundsRaw':[v[ids].min(0).tolist(),v[ids].max(0).tolist()]})
    return result

centers=v[quads].mean(1);maxz=v[quads][:,:,2].max(1)
native_normals=np.zeros_like(v)
for face in quads:
    normal=np.cross(v[face[1]]-v[face[0]],v[face[2]]-v[face[0]])+np.cross(v[face[2]]-v[face[0]],v[face[3]]-v[face[0]])
    native_normals[face]+=normal
native_normals/=np.maximum(np.linalg.norm(native_normals,axis=1,keepdims=True),1e-15)
report=[]
for side,sign,cy,cz,apex in [('L',1,1.6970,-.0332,.747949309),('R',-1,1.6965,.032,.746970099)]:
    center=np.array([sign*.30775,7.28415,1.24535])
    # Native posterior cup removal is source-depth/topology based, not a new
    # synthetic aperture contour. Keep the connected cup around the eye axis.
    candidates=set(np.flatnonzero((abs(centers[:,0]-center[0])<.23)&(abs(centers[:,1]-center[1])<.16)&(maxz<1.23)&(centers[:,2]>.65)))
    components=[]
    while candidates:
        component={candidates.pop()};front=set(component)
        while front:
            nxt={b for a in front for b in adj[a]}&candidates
            candidates-=nxt;component|=nxt;front=nxt
        components.append(component)
    cup=max(components,key=len)
    cup_loops=loops(cup)
    assert len(cup_loops)==1 and cup_loops[0]['degreeHistogram']=={2:cup_loops[0]['vertices']},'Single native closed cup cap'
    selected=set(cup);front=set(cup);layers=[]
    for layer in range(1,13):
        front={b for a in front for b in adj[a]}-selected;selected|=front
        patch=selected-cup;boundary=loops(patch)
        layers.append({'nativeFaceLayersOutsideCup':layer,'nativeQuads':len(patch),
            'boundaryLoops':boundary,'sourceFaceIDs':sorted(sourceids[list(patch)].tolist())})
    # Row6 reaches the real narrow anatomical aperture. Earlier rows are the
    # deep native socket cup and must not be mistaken for external eyelids.
    # Keep six source quad strips outward from that real aperture (rows7–12).
    keep_source=sorted(set(layers[11]['sourceFaceIDs'])-set(layers[5]['sourceFaceIDs']))
    patch=np.array([int(np.flatnonzero(sourceids==i)[0]) for i in keep_source])
    patch_loops=loops(patch)
    assert len(patch_loops)==2 and all(b['degreeHistogram']=={2:b['vertices']} for b in patch_loops)
    used=np.unique(quads[patch]);lookup={int(i):n for n,i in enumerate(used)}
    # Same common scale as retained actual 26mm CC0 eyeball donor. Each eye is
    # translated independently; no whole-character/head scaling or source edit.
    scale=.0841151730831446
    rotation=np.array([[0,0,1],[0,1,0],[-1,0,0]],dtype=float)
    assert np.linalg.det(rotation)==1
    targetcenter=np.array([apex-.0152355616,cy,cz])
    fitted=(v[used]-center)@rotation.T*scale+targetcenter
    localquads=np.array([[lookup[int(i)] for i in face] for face in quads[patch]],dtype=int)
    fitted_normals=native_normals[used]@rotation.T
    assert np.isfinite(fitted).all() and np.isfinite(fitted_normals).all() and np.isfinite(uv[puv[patch]]).all()
    assert np.all(abs(np.linalg.norm(fitted_normals,axis=1)-1)<1e-12)
    triangles=np.concatenate([localquads[:,[0,1,2]],localquads[:,[0,2,3]]])
    fn=np.cross(fitted[triangles[:,1]]-fitted[triangles[:,0]],fitted[triangles[:,2]]-fitted[triangles[:,0]])
    areas=np.linalg.norm(fn,axis=1)/2
    assert areas.min()>1e-14,'Nondegenerate actual native lid triangles'
    original=v[used];on=np.cross(original[triangles[:,1]]-original[triangles[:,0]],original[triangles[:,2]]-original[triangles[:,0]])
    assert np.all(np.einsum('ij,ij->i',fn,on@rotation.T)>0),'Proper rotation preserves native winding'
    lengths=np.linalg.norm(fitted[localquads]-np.roll(fitted[localquads],1,axis=1),axis=2)
    oldlengths=np.linalg.norm(original[localquads]-np.roll(original[localquads],1,axis=1),axis=2)
    edge_error=float(abs(lengths/oldlengths-scale).max())
    assert edge_error<1e-12,'Intrinsic native relief retained by uniform transform'
    np.savez_compressed(DEST/f'fitted-native-{side}-lids.npz',positions=fitted,rawPositions=v[used],normals=fitted_normals,
        quads=localquads,uv=uv,quadUVIndices=puv[patch],nativeVertexIDs=used,nativeSourceFaceIDs=sourceids[patch])
    obj=['# UNACCEPTED standalone native anatomical donor, no rider join','# Source CC0 MakeHuman hm08; source quad connectivity retained']
    for point in fitted:obj.append('v '+' '.join(format(float(x),'.10g') for x in point))
    texused=np.unique(puv[patch]);texlookup={int(i):n for n,i in enumerate(texused)}
    for point in uv[texused]:obj.append('vt '+' '.join(format(float(x),'.10g') for x in point))
    for normal in fitted_normals:obj.append('vn '+' '.join(format(float(x),'.10g') for x in normal))
    for face,tex in zip(localquads,puv[patch]):obj.append('f '+' '.join(f'{int(i)+1}/{texlookup[int(t)]+1}/{int(i)+1}' for i,t in zip(face,tex)))
    objpath=DEST/f'fitted-native-{side}-lids.obj'
    objpath.write_text('\n'.join(obj)+'\n')
    report.append({'side':side,'sourceEyeJointRaw':center.tolist(),'posteriorCupQuadsRemovedFromDonor':len(cup),
        'posteriorCupSourceFaceIDs':sorted(sourceids[list(cup)].tolist()),'nativeCupBoundary':cup_loops[0],
        'nativeTopologyLayers':layers,'selectedLayers':[7,8,9,10,11,12],'selectedNativeQuads':len(patch),
        'selectedPatchBoundaryLoops':patch_loops,'nativeSourceFaceIDs':sourceids[patch].tolist(),
        'posteriorCupAndWallQuadsExcluded':len(cup)+layers[5]['nativeQuads'],
        'selectedNativeVertices':len(used),'uniformScale':scale,'targetGlobeCenterM':targetcenter.tolist(),
        'fittedBoundsM':[fitted.min(0).tolist(),fitted.max(0).tolist()],
        'fittedFrontDepthReliefMM':float(np.ptp(fitted[:,0])*1000),
        'normals':'Whole native body area-weighted quad normals, proper rotation; source UVs and quad connectivity unchanged',
        'finitePositionsNormalsUVs':True,'unitNormals':True,'sourceWindingPreserved':True,
        'triangles':len(triangles),'minTriangleAreaM2':float(areas.min()),'maxUniformEdgeRatioError':edge_error,
        'UVBoundsNative':[uv[puv[patch]].reshape(-1,2).min(0).tolist(),uv[puv[patch]].reshape(-1,2).max(0).tolist()],
        'nativeOBJ':str(objpath),'nativeOBJ_SHA256':hashlib.sha256(objpath.read_bytes()).hexdigest(),
        'fitLimits':'Provisional center/scale compatible with retained eye donor dimensions; no socket/globe collision, skin join, source identity or visual acceptance.'})
assert source.read_bytes()==raw
result={'status':'UNACCEPTED fresh native anatomical lid donor pair; unjoined CPU proposal',
    'sourceNativeNPZSHA256':hashlib.sha256(raw).hexdigest(),'retainedNativeQuadConnectivity':True,
    'newAnalyticLidRings':0,'sourceRiderChanged':False,'eyes':report,
    'limits':['Default raw hm08 Basis anatomy, no copied historical generated head.',
        'Uniform per-eye fit preserves source native 3D relief; translating eyes independently changes pair spacing only.',
        'Native UVs retained but donor skin not textured/baked into rider; no appearance claim.',
        'No skin join, normals seam, donor eye clearance, rig binding, game clips, Blender render or model generation attempted.']}
(OUT/'extraction.json').write_text(json.dumps(result,indent=2)+'\n')
(DEST/'construction.json').write_text(json.dumps(result,indent=2)+'\n')
for eye in report:
    print({k:value for k,value in eye.items() if k not in ['posteriorCupSourceFaceIDs','nativeTopologyLayers','nativeCupBoundary']})
    print('cup',eye['nativeCupBoundary'])
    print('layers',[(l['nativeFaceLayersOutsideCup'],l['nativeQuads'],[(b['vertices'],b['degreeHistogram']) for b in l['boundaryLoops']]) for l in eye['nativeTopologyLayers']])
