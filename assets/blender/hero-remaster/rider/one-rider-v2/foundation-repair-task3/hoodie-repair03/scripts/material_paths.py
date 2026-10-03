from pathlib import Path
import sys,numpy as np,json
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT3=ROOT/'hoodie-repair03';b=np.load(OUT/'v7-bind.npz');p=np.concatenate([b[f'p{i}']for i in range(5)]);rest=np.zeros_like(U);np.add.at(rest,INV,p);rest/=np.bincount(INV)[:,None];ww=np.zeros((len(U),19));np.add.at(ww,INV,np.concatenate([b[f'W{i}']for i in range(5)]));ww/=np.bincount(INV)[:,None]
ct=np.concatenate([INV[b[f'tr{i}']+OFF[i]]for i in [0,2]]);ee=np.unique(np.sort(np.concatenate([ct[:,[0,1]],ct[:,[1,2]],ct[:,[0,2]]]),axis=1),axis=0);length=np.linalg.norm(rest[ee[:,0]]-rest[ee[:,1]],axis=1);graph=coo_matrix((np.r_[length,length],(np.r_[ee[:,0],ee[:,1]],np.r_[ee[:,1],ee[:,0]])),shape=(len(U),len(U))).tocsr();cloth=np.zeros(len(U),bool);cloth[np.unique(ct)]=True
core=cloth&(ww[:,1]+ww[:,2]>.999)&(abs(U[:,2])<.115)&(U[:,1]>1.05)&(U[:,1]<1.49);coreids=np.flatnonzero(core);# fixed torso and truly rigid hand-owned cloth anchors only; no inferred side-torso labels
# deterministically cover anatomical height/fore-aft coordinates and both sides.
selectors=[np.array([x,y,z])for x in [.57,.67,.74]for y in [1.10,1.20,1.30,1.42]for z in [-.095,.095]];anchors=np.unique([coreids[np.argmin(np.linalg.norm(rest[coreids]-q,axis=1))]for q in selectors]);dist=dijkstra(graph,indices=anchors,directed=False);rows=[]
for side,sg,j in [('L',1,8),('R',-1,12)]:
 sharedcuff=np.intersect1d(INV[OFF[0]:OFF[1]],INV[OFF[1]:OFF[2]]);cuff=sharedcuff[(U[sharedcuff,2]*sg>.24)&(U[sharedcuff,1]>.88)&(U[sharedcuff,1]<1.0)];geod=dist[:,cuff]
 for kind in ['horizontal','overhead','forward','elbow']:
  f=OUT/'qa-lane/poses'/f'v5-{kind}-1.npz';d=np.load(f);D=d['matrices'];poses=deform([b[f'p{i}']for i in range(5)],[b[f'W{i}']for i in range(5)],D,False);world=np.zeros_like(U);np.add.at(world,INV,np.concatenate(poses));world/=np.bincount(INV)[:,None];delta=np.linalg.norm(world[anchors,None]-world[cuff][None],axis=2);ratio=np.divide(delta,geod,out=np.zeros_like(delta),where=np.isfinite(geod)&(geod>1e-9));a,c=np.unravel_index(np.argmax(ratio),ratio.shape);ids=[int(anchors[a]),int(cuff[c])];start,end=ids
  _,pred=dijkstra(graph,indices=start,directed=False,return_predecessors=True);path=[end]
  while path[-1]!=start and len(path)<len(U):
   nxt=int(pred[path[-1]])
   if nxt<0:break
   path.append(nxt)
  rows.append({'side':side,'pose':kind,'endpoint_distance_m':float(delta[a,c]),'shortest_material_edge_path_m':float(geod[a,c]),'required_path_average_stretch_lower_bound':float(ratio[a,c]),'rest_unique_vertex_anchors':ids,'source_rest_anchor_positions_m':rest[ids].tolist(),'posed_anchor_positions_m':world[ids].tolist(),'path_unique_vertex_ids':path[::-1],'fixed_anchor_basis':'exact >.999 spine/chest influence with |sourcez|<.115 and exact original127 sewn cloth/glove alias positions; rigid glove input','limits':'Endpoint separation divided by actual rest-edge shortestpath lowerbounds maximum edge stretch under these conditionally held central torso and required sewn cuff anchors. Less than2.5 does not prove an embedding, volume or collision-free feasibility.'});print(side,kind,ratio[a,c],flush=True)
(OUT3/'evidence/material-path-lower-bounds.json').write_text(json.dumps({'joints':19,'static_bind':'v7-bind.npz','core_anchors':len(anchors),'rows':rows,'method':'Material triangle-edge Dijkstra; paired held torso/cuff points. Triangle diagonal choices affect bound; reported current finaltopology only. No closed-shell volume assumption or physicalclothcertificate.'},indent=2))
