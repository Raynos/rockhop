from pathlib import Path
import json,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';HERE=ROOT/'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
def read(p):
 with np.load(p) as z:return {k:z[k] for k in z.files}
a=read(HERE/'source-sleeve-tube-rest07-uvchart.npz');b=read(HERE/'source-sleeve-tube-rest10-rmf.npz')
def boundary(d):
 p=np.r_[d['p0'],d['p2']]; ids=np.r_[d['physicalWeld0'],d['physicalWeld2']];tri=np.r_[d['tr0'],d['tr2']+len(d['p0'])];q=ids[tri];e,n=np.unique(np.sort(np.r_[q[:,[0,1]],q[:,[1,2]],q[:,[2,0]]],axis=1),axis=0,return_counts=True);coords={int(k):v for k,v in zip(ids,p)}
 return e[n==1],{tuple(np.array(sorted([coords[int(x)].tolist(),coords[int(y)].tolist()])).ravel()) for x,y in e[n==1]}
ae,ap=boundary(a);be,bp=boundary(b);path=Q/'uv-lower01/sleeve-tube10-independent-rest.json';r=json.loads(path.read_text());r['checks']['boundary_physical_edge_set_exact07']=bool(np.array_equal(ae,be));r['checks']['boundary_position_set_exact07']=ap==bp;r['boundary_source_proof']='Boundary physical edge and exact coordinate sets equal independently source-verified07/06, not just equal edge counts.';r['status']='BOUNDED_REST_AND_SOURCE_CONTRACT_PASS' if all(r['checks'].values()) else 'FAIL';path.write_text(json.dumps(r,indent=2)); print(r['status'],len(bp))
