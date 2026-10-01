"""Read-only audit of the single stopped body18 trial and actual prior wall."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,struct
import numpy as np
from geometry_checks import surface_clearance,topology,self_test

ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind18/construction01')
frozen=ROOT/'body-bind18/construction01/construction-guard-failure.npz'
saved=np.load(frozen)
points=saved['positions'];faces=saved['output']
unique,canonical=np.unique(points,axis=0,return_inverse=True)
physical=canonical[faces]
edges=Counter(tuple(sorted((int(a),int(b)))) for f in physical for a,b in zip(f,np.roll(f,-1)))
adj=defaultdict(list)
for (a,b),count in edges.items():
    if count==1:
        adj[a].append(b);adj[b].append(a)
branch=[i for i,n in adj.items() if len(n)!=2]
source=saved['v'];original=saved['tri'];xyz=source[original]
face_normals=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
face_normals/=np.maximum(np.linalg.norm(face_normals,axis=1,keepdims=True),1e-30)
records=[]
for vertex in branch:
    point=unique[vertex].astype(float)
    nearby=np.flatnonzero((xyz.min(1)<=point+3e-7).all(1)&(xyz.max(1)>=point-3e-7).all(1))
    containing=[]
    for i in nearby:
        triangle=xyz[i]
        e=np.array([triangle[1]-triangle[0],triangle[2]-triangle[0]])
        q=np.linalg.lstsq(e.T,point-triangle[0],rcond=None)[0]
        residual=np.linalg.norm(e.T@q-(point-triangle[0]))
        bary=np.r_[1-q.sum(),q]
        if residual<3e-7 and (bary>=-1e-5).all():
            containing.append({'sourceTriangle':int(i),'normalX':float(face_normals[i,0]),
                'inwardClassifier':bool(face_normals[i,0]<0),'planeResidualM':float(residual),
                'barycentric':bary.tolist(),'minimumTriangleX':float(triangle[:,0].min())})
    records.append({'physicalVertex':int(vertex),'positionM':point.tolist(),'boundaryDegree':len(adj[vertex]),
        'boundaryNeighborPositionsM':unique[adj[vertex]].tolist(),'sourceFacesContainingPoint':containing})
assert branch,'Expected frozen non-simple source boundary'

previous=np.load(ROOT/'body-bind17/construction01/clearance-registration-failure.npz')
donor_topology={key:topology(previous[key+'Positions'],previous[key+'Triangles']) for key in ['actualCornea','actualIris']}
preflight=[]
for shift in [0,-.002,-.004,-.006,-.008]:
    categories={}
    for category,key in [('native_lid','nativeTriangles'),('front_join','frontJoinTriangles'),('inward_wall','inwardWallTriangles')]:
        for name in ['actualCornea','actualIris']:
            donor=previous[name+'Positions'].copy();donor[:,0]+=shift
            categories[category+'/'+name]=surface_clearance(previous['positions'][previous[key]].astype(float),donor[previous[name+'Triangles']],reach=.00025)
    preflight.append({'shiftM':shift,'categories':categories})

source_file=ROOT/'body-bind11/guarded-correction01/rider.glb'
sha=hashlib.sha256(source_file.read_bytes()).hexdigest()
assert sha=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
assert not list((ROOT/'body-bind18').rglob('*.glb'))
native_hashes={}
for side,expected in [('L','0f34dc4467f12f7e0cfddd42dd3823d6c5dfbe91320303286ec3985f441f3e30'),
    ('R','a2d2a9f09d0fc133503725c6332e4dee128fe9973ae199586fe2f2d792144ce6')]:
    path=ROOT/f'anatomical-eye-donor01/standalone01/fitted-native-{side}-lids.npz'
    measured=hashlib.sha256(path.read_bytes()).hexdigest()
    assert measured==expected
    native_hashes[side]=measured
eye_sha=hashlib.sha256((ROOT.parent/'eye-donor01/guarded01/eyes.glb').read_bytes()).hexdigest()
assert eye_sha=='c11e5273b7e8d82a94a46d46c853e0ad42e7caeb2328716bc4a5c4090170d0fb'
report={'status':'FROZEN failed source-sheet cut before anatomical assembly; current11 unchanged',
    'CPUOnly':True,'GPUWorkPerformed':False,'candidateExported':False,'sourceSHA256':sha,
    'failureClassification':'Procedural normal-sign clip classification; not a generator or anatomy failure',
    'nativeDonorHashesUnchanged':native_hashes,'actualEyeDonorSHA256':eye_sha,
    'frozenGeometrySHA256':hashlib.sha256(frozen.read_bytes()).hexdigest(),'geometryAlgorithmSelfTests':self_test(),
    'trialROI':{'outerHalfWidthM':.018,'outerHalfHeightM':.009,'innerHalfWidthM':.022,'innerHalfHeightM':.017,
        'outerMinimumXM':.72,'innerMinimumXM':.69,'innerSourceSheetClassifier':'geometric triangle normal X<0'},
    'sourceTopology':topology(source,original),'stoppedTopology':topology(points,faces),
    'boundaryDegreeHistogram':dict(Counter(len(v) for v in adj.values())),
    'nonSimpleBoundaryVertices':records,'actualEyeDonorTopology':donor_topology,
    'priorNegativeZEyePreflight':preflight,
    'limits':[
        'Body18 stopped before assembling native tissue, constructing its inward wall, fit searching, source conservation, normals/skinUV or export. These gates are pending and not passes.',
        'The retained prior body17 inward wall has actual surface intersections at all five measured shifts, including8mm. This does not prove every real-valued shift fails.',
        'Cornea and opaque sclera/iris are separate open-backed actual surfaces; both were checked. No closed eyeball volume is invented.',
        'The opaque donor shares one mesh for iris and sclera; testing every triangle of that mesh includes both, without an inferred texture-only exclusion.',
        'Enlarging surgery by face-normal sign creates a branched source boundary. This classifier is not a sufficient connected-sheet segmentation.',
        'No attempt to repair the branch or relax8mm was made. No appearance, anatomy, rig motion or game-ready acceptance is claimed.',
    ]}
(EVIDENCE/'trial-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['nonSimpleBoundaryVertices','priorNegativeZEyePreflight']},indent=2))
print(json.dumps(records,indent=2))
