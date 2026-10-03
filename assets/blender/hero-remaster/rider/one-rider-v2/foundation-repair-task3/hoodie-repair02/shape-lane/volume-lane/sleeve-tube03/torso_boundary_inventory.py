"""Bounded topology-based torso patch expansion around proven bad old seam."""
from pathlib import Path
import numpy as np,json,sys
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import *
c=SourceCharts();old=np.load(HERE.parent/'armhole-construction/source-armhole-cut.npz');cut=np.load(HERE/'sleeve-cut-inventory.npz');ct=c.ct;both=old['sleeveFacesL']|old['sleeveFacesR'];body=ct[~both];e=np.unique(np.sort(np.r_[body[:,[0,1]],body[:,[1,2]],body[:,[2,0]]],axis=1),axis=0);length=np.linalg.norm(c.unique[e[:,0]]-c.unique[e[:,1]],axis=1);g=coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr();out={};rows=[]
for side in ['L','R']:
 loop=old['cutLoop'+side+'0'];dist=dijkstra(g,directed=False,indices=loop,min_only=True);bodyCut=(~both)&(dist[ct].min(1)<.025)&(c.unique[ct][:,:,1].mean(1)<1.49);deleted=old['sleeveFaces'+side]|bodyCut;retainedTube=cut['retainedTubeFaceMask'+side];clipped=np.zeros(len(ct),bool);clipped[cut['clippedTubeFaceIDs'+side]]=True;deleted[retainedTube|clipped]=False
 # Ring at exact plane is tracked separately; source edges around the expanded
 # upper deletion form the actual torso boundary, with lower tube interfaces.
 records=np.sort(np.r_[ct[:,[0,1]],ct[:,[1,2]],ct[:,[2,0]]],axis=1);faces=np.tile(np.arange(len(ct)),3);ee,iv,count=np.unique(records,axis=0,return_inverse=True,return_counts=True);order=np.argsort(iv);starts=np.r_[0,np.cumsum(count)];boundary=[]
 for k in np.flatnonzero(count==2):
  a,b=faces[order[starts[k]:starts[k+1]]]
  if deleted[a]!=deleted[b]:boundary.append(ee[k])
 boundary=np.array(boundary,int);adj={}
 for a,b in boundary:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
 degrees={int(k):len(v)for k,v in adj.items()if len(v)!=2};loops=[];seen=set()
 if not degrees:
  for first in adj:
   if first in seen:continue
   v=first;prev=None;loop=[]
   while v not in seen:loop.append(v);seen.add(v);nxt=[x for x in adj[v]if x!=prev][0];prev,v=v,nxt
   assert v==first;loops.append(np.array(loop,int))
 out['deletedSourceFaces'+side]=deleted;out['expandedBodyRemovedFaces'+side]=bodyCut;out['rawBoundarySourceEdges'+side]=boundary;out['sourceBodyDistance'+side]=dist
 for i,loop in enumerate(loops):out[f'rawBoundaryLoop{side}{i}']=loop
 rows.append({'side':side,'bodyExpansionGeodesicM':.025,'upperBodyFaceCentreLimitY':1.49,'originalBodyFacesRemoved':int(bodyCut.sum()),'originalFacesDeleted':int(deleted.sum()),'boundaryEdges':len(boundary),'badBoundaryDegrees':degrees,'rawBoundaryLoops':len(loops),'loopRanges':[{'nodes':len(loop),'min':c.unique[loop].min(0).tolist(),'max':c.unique[loop].max(0).tolist()}for loop in loops],'note':'Raw lower tube source-interface loop must be replaced by its exact plane-clipped ring. Torso loop remains original source vertices/UV ancestry. No geometry has been regenerated.'})
np.savez_compressed(HERE/'expanded-torso-cut-inventory.npz',**out);(HERE/'expanded-torso-cut-inventory.json').write_text(json.dumps({'status':'CUT_INVENTORY_ONLY; boundary and rest construction not yet accepted','rows':rows},indent=2));print(json.dumps(rows,indent=2))
