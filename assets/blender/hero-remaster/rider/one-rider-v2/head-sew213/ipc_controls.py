"""Measure native IPC coverage; no positive coplanar assertion from a boolean."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
import ipctk,numpy as np,json
from pathlib import Path
ipctk.set_num_threads(2)
cases={'nonadjacent_crossing':([[0,0,0],[1,0,0],[0,1,0],[.2,.2,-1],[.2,.2,1],[.8,.2,0]],[[0,1,2],[3,4,5]]),'nonadjacent_separated':([[0,0,0],[1,0,0],[0,1,0],[2.2,.2,-1],[2.2,.2,1],[2.8,.2,0]],[[0,1,2],[3,4,5]]),'shared_vertex_crossing':([[0,0,0],[1,0,0],[0,1,0],[.2,.2,-1],[.2,.2,1]],[[0,1,2],[0,3,4]]),'shared_edge_positive_coplanar_fold':([[0,0,0],[1,0,0],[0,1,0],[.2,.2,0]],[[0,1,2],[1,0,3]]),'nonadjacent_positive_coplanar_overlap':([[0,0,0],[1,0,0],[0,1,0],[.1,.1,0],[.6,.1,0],[.1,.6,0]],[[0,1,2],[3,4,5]])}
rows=[]
for name,(P,T) in cases.items():
 P=np.array(P,float);T=np.array(T,np.int32);E=np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1),axis=0);result=bool(ipctk.has_intersections(ipctk.CollisionMesh(P,E,T),P));rows.append({'case':name,'intersects':result})
report={'rows':rows,'nativeThreads':ipctk.get_num_threads(),'limits':'Measured controls define coverage. False is not a general coplanar-clear claim. Separate exact planar area-overlap and adjacent-fold checks required.'};Path('docs/evidence/hero-remaster/one-rider-v2/head-sew213/ipc-controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
