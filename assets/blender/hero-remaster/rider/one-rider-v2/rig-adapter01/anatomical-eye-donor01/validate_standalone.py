"""Read-only independent checks of frozen native donor topology and provenance."""
from pathlib import Path
from collections import Counter
import hashlib,json
import numpy as np
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
DONOR=ROOT/'rig-adapter01/anatomical-eye-donor01'
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/anatomical-eye-donor01')
native=np.load(DONOR/'native-source.npz');sources={int(i):q for i,q in zip(native['sourceFaceIDs'],native['quads'])}
uv_sources={int(i):q for i,q in zip(native['sourceFaceIDs'],native['quadUVIndices'])}
record=json.loads((DONOR/'standalone01/construction.json').read_text());rows=[]
for side in ['L','R']:
    path=DONOR/'standalone01'/f'fitted-native-{side}-lids.npz';data=np.load(path)
    positions=data['positions'];ids=data['nativeVertexIDs'];quads=data['quads'];normals=data['normals'];uv=data['uv'];faceids=data['nativeSourceFaceIDs']
    assert np.array_equal(data['rawPositions'],native['positions'][ids]),'Original native positions exact'
    assert np.array_equal(ids[quads],np.array([sources[int(i)] for i in faceids])),'Actual native quad connectivity exact'
    assert np.array_equal(data['quadUVIndices'],np.array([uv_sources[int(i)] for i in faceids])) and np.array_equal(uv,native['uv']),'Actual native UVs exact'
    assert np.isfinite(positions).all() and np.isfinite(normals).all() and np.isfinite(uv).all()
    assert abs(np.linalg.norm(normals,axis=1)-1).max()<1e-12
    directed=Counter((int(a),int(b)) for q in quads for a,b in zip(q,np.roll(q,-1)))
    canonical=Counter(tuple(sorted((a,b))) for a,b in directed)
    assert max(canonical.values())==2 and max(directed.values())==1,'Consistent manifold edges'
    assert len(positions)-len(canonical)+len(quads)==0,'Native annulus Euler characteristic'
    boundary=[edge for edge,n in canonical.items() if n==1];degree=Counter(i for edge in boundary for i in edge)
    assert len(boundary)==64 and set(degree.values())=={2},'Two retained 32-edge loops'
    edges=quads[:,[1,2,3,0]]-quads
    triangles=np.concatenate([quads[:,[0,1,2]],quads[:,[0,2,3]]])
    cross=np.cross(positions[triangles[:,1]]-positions[triangles[:,0]],positions[triangles[:,2]]-positions[triangles[:,0]])
    area=np.linalg.norm(cross,axis=1)/2;assert area.min()>1e-14
    obj=DONOR/'standalone01'/f'fitted-native-{side}-lids.obj'
    eye=next(e for e in record['eyes'] if e['side']==side)
    assert hashlib.sha256(obj.read_bytes()).hexdigest()==eye['nativeOBJ_SHA256']
    rows.append({'side':side,'vertices':len(positions),'quads':len(quads),'triangles':len(triangles),
        'canonicalEdges':len(canonical),'boundaryEdges':len(boundary),'EulerCharacteristic':0,
        'originalNativePositionQuadUVProvenanceExact':True,'finiteUnitNormals':True,
        'minTriangleAreaM2':float(area.min()),'OBJ_SHA256':eye['nativeOBJ_SHA256'],'NPZ_SHA256':hashlib.sha256(path.read_bytes()).hexdigest()})
master=ROOT/'rig-adapter01/body-bind11/guarded-correction01/rider.glb'
mastersha=hashlib.sha256(master.read_bytes()).hexdigest()
assert mastersha=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
report={'status':'PASS frozen standalone anatomical donor checks; unjoined art proposal',
    'currentRiderSHA256Unchanged':mastersha,'eyes':rows,
    'limits':['No source head surgery, skin material bake, aperture/globe clearance, rig binding or rendered appearance acceptance.',
        'Two open native annulus loops are intentional standalone donor boundaries; completed character requires continuous graft and inward skin treatment.']}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
