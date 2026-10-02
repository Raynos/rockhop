"""Parent verifies exact source boundary indices and donor winding independently."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop')
E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-boundaries181'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((E/'report.json').read_text());verified=[]
for rec in report['inputHashes']+report['privateOutputs']:
    p=Path(rec['path']);assert sha(p)==rec['SHA256'];verified.append(str(p))
assert sha(E/'audit.py')==report['recipeSHA256']
p=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb');raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);binary=raw[28+n:]
def array(i):
    a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];k={'SCALAR':1,'VEC3':3}[a['type']];s=np.dtype(dt).itemsize
    return np.ndarray((a['count'],k),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',s*k),s)).copy()
qs=j['meshes'][0]['primitives'];positions=[array(q['attributes']['POSITION'])for q in qs];triangles=[array(q['indices']).reshape(-1,3)for q in qs]
U,inv=np.unique(np.concatenate(positions),axis=0,return_inverse=True);maps=np.split(inv,np.cumsum([len(x)for x in positions])[:-1]);M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-boundaries181');a=np.load(M/'source-boundary-profiles.npz');assert np.array_equal(U,a['allPhysicalFloat32Positions'])
for i,m in enumerate(maps):assert np.array_equal(m,a[f'sourcePrimitive{i}RowsToPhysical'])
edgeMaps=[]
for i,f in enumerate(triangles):
    incidences=Counter();orientations={}
    for row in maps[i][f]:
        for x,z in zip(row,np.roll(row,-1)):
            edge=tuple(sorted((int(x),int(z))));incidences[edge]+=1;orientations.setdefault(edge,[]).append(int(x)<int(z))
    edgeMaps.append((incidences,orientations))
checks=[]
for prefix,partA,partB,expected in [('hood_body',0,2,[307]),('cuff_body_glove',0,1,[65,62])]:
    for i,count in enumerate(expected):
        ids=a[f'{prefix}Cycle{i}PhysicalIDs'];P=a[f'{prefix}Cycle{i}Float32Positions'];assert len(ids)==count and len(set(ids.tolist()))==count and np.array_equal(P,U[ids])
        edges=[tuple(sorted((int(x),int(z))))for x,z in zip(ids,np.roll(ids,-1))];assert len(set(edges))==count
        for edge in edges:
            assert edgeMaps[partA][0][edge]==edgeMaps[partB][0][edge]==1
            assert edgeMaps[partA][1][edge][0]!=edgeMaps[partB][1][edge][0]
        checks.append({'interface':prefix,'cycle':i,'nodes':count,'positionsOriginalFloat32Exact':True,'oneFacePerPrimitiveOppositeWinding':True})
(E/'parent-review.json').write_text(json.dumps({'status':'SOURCE_BOUNDARY_CONTRACT_VERIFIED_NOT_CHARACTER_PASS','pinnedFilesVerified':verified,'recipeSHA256Verified':report['recipeSHA256'],'allPhysicalSourcePositionsAndPrimitiveRowMapsExact':True,'independentBoundaryChecks':checks,'hoodUpperOpening':'237node separate source boundary remains protected; not automatically the head-neck seam.','profileLimits':'Bounds from Zclipped windows are reference exclusions, not exact anatomical width. High p0 rings omit hood-owned posterior geometry. No candidate geometry generated.','limits':'No collision/appearance/motion acceptance, new rig or physicalC19pose repair. Final newmesh seam IDs, float32 topology and wardrobe join still require evidence.'},indent=2)+'\n')
print(json.dumps({'pinnedFiles':len(verified),'exactClosedDonorCycles':checks}))
