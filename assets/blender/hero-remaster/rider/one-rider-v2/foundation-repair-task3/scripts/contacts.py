from pathlib import Path
import numpy as np,json,sys
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from types import SimpleNamespace
sys.path.insert(0,'scripts');from glb import GLB
root=Path.cwd();g=GLB(root/'baseline/rider.glb');pr=[p for m in g.j['meshes']for p in m['primitives']];ps=[g.array(p['attributes']['POSITION']).astype(float)for p in pr];roi=json.load(open('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/framed04/source-roi.json'))
bike={x['name']:x for x in json.load(open('evidence/bike.json'))};B={k:SimpleNamespace(vertices=np.array(v['positions']),faces=np.array(v['triangles']).reshape(-1,3))for k,v in bike.items()};support=B['bodywork'];source=Path('/Users/raynos/Documents/Codex/2026-10-01/task-2/evidence/motion');sm=json.loads((source/'pose-manifest.json').read_text());bp=np.fromfile(source/sm['bodyworkSource']['positions']['file'],'<f8').reshape(-1,3);bt=np.fromfile(source/sm['bodyworkSource']['triangles']['file'],'<f8').astype(int).reshape(-1,3);sq=bp[bt];cr=np.cross(sq[:,1]-sq[:,0],sq[:,2]-sq[:,0]);norm=cr/np.maximum(np.linalg.norm(cr,axis=1,keepdims=True),1e-15);mask=np.all((sq[:,:,0]>=.1095)&(sq[:,:,0]<=.6005)&(sq[:,:,1]>=.5405)&(sq[:,:,1]<=.631)&(abs(sq[:,:,2])<=.069),axis=1)&(norm[:,1]>.3);seat=support.vertices[bt[mask]];print('seat triangles',len(seat));report={'method':'Actual triangle surface unsigned palm/sole distance, and vertex-projected seat-top clearance. Not whole-body collision certificate; independent exact triangle self-intersection audit is separate.','seatTriangleCount':len(seat),'variants':{}}
for n in ['A','B','C19','C']:
 rows=[]
 for k in range(25):
  d=np.load(f'experiments/{n}-rigid_length_stand_to_sit-{k:03d}.npz');P=[d[f'p{i}']for i in range(5)];r={'key':k,'contacts':[]}
  for region,pi in [('hands',1),('feet',0)]:
   for rr in roi[region]:
    ix=rr['sourceVertices'];v=P[pi][ix];mesh=B[rr['bikeMeshName']]
    tree=BVHTree.FromPolygons(mesh.vertices.tolist(),mesh.faces.tolist(),all_triangles=True);dist=np.array([tree.find_nearest(Vector(pt))[3]for pt in v]);r['contacts'].append({'region':region,'side':rr['side'],'points':len(v),'minSurfaceDistanceM':float(dist.min()),'p50SurfaceDistanceM':float(np.median(dist)),'maxSurfaceDistanceM':float(dist.max())})
  active=(ps[0][:,1]>.69)&(ps[0][:,1]<1.08)&(abs(ps[0][:,2])<.245);v=P[0][active];heights=np.full(len(v),-np.inf)
  for st in seat:
   ma=np.array([[st[1,0]-st[0,0],st[2,0]-st[0,0]],[st[1,2]-st[0,2],st[2,2]-st[0,2]]]);det=np.linalg.det(ma)
   if abs(det)<1e-12:continue
   uv=np.einsum('ij,kj->ik',v[:,[0,2]]-st[0,[0,2]],np.linalg.inv(ma),optimize=False);inside=(uv.min(1)>=0)&(uv.sum(1)<=1);yy=st[0,1]+uv[:,0]*(st[1,1]-st[0,1])+uv[:,1]*(st[2,1]-st[0,1]);heights[inside]=np.maximum(heights[inside],yy[inside])
  sel=np.isfinite(heights);gap=v[sel,1]-heights[sel];r['seat']={'projectedVertices':int(sel.sum()),'negativeClearanceVertices':int(np.sum(gap<0)),'minClearanceM':float(gap.min())if len(gap)else None};rows.append(r)
 report['variants'][n]=rows
Path('evidence/contacts.json').write_text(json.dumps(report,indent=2));print({n:[rows[0]['seat'],rows[-1]['seat']]for n,rows in report['variants'].items()})
