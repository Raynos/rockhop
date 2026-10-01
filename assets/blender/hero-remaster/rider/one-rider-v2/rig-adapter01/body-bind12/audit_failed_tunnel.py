"""Freeze the rejected CPU construction as measured evidence, not an asset."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, struct
import numpy as np

REPO=Path('/Users/raynos/projects/games/rockhop')
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT=ROOT/'rig-adapter01/body-bind12/construction01'
EVIDENCE=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind12/construction01'
source=ROOT/'rig-adapter01/body-bind11/guarded-correction01/rider.glb'
raw=source.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
index=doc['meshes'][1]['primitives'][0]['attributes']['POSITION']
accessor=doc['accessors'][index];view=doc['bufferViews'][accessor['bufferView']]
original=np.ndarray((accessor['count'],3),dtype='<f4',buffer=binary,offset=view.get('byteOffset',0)+accessor.get('byteOffset',0),strides=(view.get('byteStride',12),4))
trial=np.load(OUT/'bridge-failure.npz')
positions=trial['positions'];canonical,weld=np.unique(positions,axis=0,return_inverse=True)
def edges(triangles):
    return Counter(tuple(sorted(e)) for face in weld[triangles]
        for e in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])])
cut=edges(trial['cutTriangles']);bridge=edges(trial['bridgeTriangles'])
boundaries=[e for e,count in cut.items() if count==1]
adj=defaultdict(list)
for a,b in boundaries:adj[a].append(b);adj[b].append(a)
assert all(len(values)==2 for values in adj.values())
unseen=set(adj);loops=[]
while unseen:
    seed=min(unseen);previous=None;cur=seed;loop=[seed]
    while True:
        nxt=next(a for a in adj[cur] if a!=previous)
        if nxt==seed:break
        assert nxt not in loop
        loop.append(nxt);previous,cur=cur,nxt
    unseen-=set(loop);points=canonical[loop]
    loops.append(dict(vertices=len(loop),boundsM=[points.min(0).tolist(),points.max(0).tolist()]))
missed=[e for e,count in cut.items() if count==1 and e not in bridge and canonical[list(e),1].mean()>1.69]
points=positions[trial['bridgeTriangles']].astype(float)
area=np.linalg.norm(np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]),axis=1)/2
combined=cut+bridge
degrees=Counter(a for edge,count in combined.items() if count==1 for a in edge)
recipe=REPO/'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind12'
report=dict(status='REJECTED; no candidate GLB exported',attempts=3,
    technique='64-sided analytic ellipse subtraction plus conforming source edges and angular tunnel zipper',
    sourceSHA256=hashlib.sha256(raw).hexdigest(),sourceUntouched=True,
    originalHeadPositionPrefixExact=bool(np.array_equal(positions[:len(original)],original)),
    sourceHeadTriangles=99485,cutHeadTriangles=len(trial['cutTriangles']),
    cutTopology=dict(boundaryEdges=len(boundaries),boundaryLoops=len(loops),nonmanifoldEdges=sum(count>2 for count in cut.values()),boundaryDegreeTwo=True,loops=loops),
    zipperTriangles=len(area),zeroAreaTubeTriangles=int(np.sum(area==0)),
    tubeTrianglesBelow1eMinus14M2=int(np.sum(area<=1e-14)),
    missedEyeRimEdges=len(missed),joinedBoundaryEdges=sum(count==1 for count in combined.values()),
    joinedNonmanifoldEdges=sum(count>2 for count in combined.values()),
    joinedBoundaryDegreeHistogram=dict(Counter(degrees.values())),
    failure='Angular sorting of the folded inner-sheet boundary does not preserve actual ordered rim adjacency;41 source rim edges remain unpaired and tube contains degenerate faces.',
    nextApproach='Switch to the measured36x18mm orbital surgery patch: preserve ordered outer source boundary, replace locally folded inner orbital sheet with deliberately ordered4 almond eyelid rings plus inner tunnel, then fit exact CC0 donor and ray-test pupil visibility.',
    frozenGeometry=str(OUT/'bridge-failure.npz'),
    recipeHashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in recipe.glob('build_apertures*.py')},
    limits=['A clean analytic cut alone is not a completed lid or a rigged character asset.','No rendering, GPU/Metal workload, appearance score or actual gameplay judgement occurred.','Current approved body11 remains the comparison and working direction.'])
assert report['sourceSHA256']=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
assert report['originalHeadPositionPrefixExact'] and not (OUT/'rider.glb').exists()
(EVIDENCE/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','attempts','missedEyeRimEdges','zeroAreaTubeTriangles','sourceUntouched']}))
