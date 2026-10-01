"""Read serialized source/candidate fields for independent rest geometry audit."""
import numpy as np, json
from pathlib import Path
root=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01')
a=np.load(root/'fit01.npz');b=np.load(root/'cage04/fit04.npz');Q=a['quads']
tri=np.concatenate([Q[:,[0,1,2]],Q[:,[0,2,3]]])
def cross(P):
    p=P[tri];return np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
x,y=cross(a['positions']),cross(b['positions'])
d=(x*y).sum(1)/np.maximum(np.linalg.norm(x,axis=1)*np.linalg.norm(y,axis=1),1e-20)
report={'negativeNormalDots':int((d<0).sum()),'minimumNormalDot':float(d.min()),
        'minimumTriangleAreaM2':float(np.linalg.norm(y,axis=1).min()/2),
        'nativeQuadsUVWeightsExact':all(np.array_equal(a[k],b[k]) for k in ['quads','uvLoops','weights'])}
out=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cage04/rest-independent-audit.json')
assert json.loads(out.read_text())==report, 'Independent serialized-field result must match frozen receipt'
print(json.dumps(report))
