"""Surgical source armhole partition; frozen source, exact sewn topology.
Separate lower-cuff-connected sleeve from torso in dual face graph, using source
opposing normal sheet evidence. This is a construction cut, not skin weights.
"""
from pathlib import Path
import sys,json,hashlib,shutil
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import *
from scipy.sparse.csgraph import maximum_flow,breadth_first_order

def ordered_loops(edges):
 adj={}
 for a,b in edges:
  adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
 if any(len(v)!=2 for v in adj.values()):return [],{'degrees':{str(k):len(v)for k,v in adj.items()if len(v)!=2}}
 loops=[];seen=set()
 for first in adj:
  if first in seen:continue
  curr=first;prev=None;loop=[]
  while curr not in seen:
   loop.append(curr);seen.add(curr);nxt=[n for n in adj[curr]if n!=prev][0];prev,curr=curr,nxt
  assert curr==first;loops.append(loop)
 return loops,{'degree2':True}

c=SourceCharts();src=c.input;backup=HERE/'frozen-v7-bind.npz'
if not backup.exists():shutil.copyfile(src,backup)
assert hashlib.sha256(src.read_bytes()).hexdigest()==hashlib.sha256(backup.read_bytes()).hexdigest()
ct=c.ct;nfaces=len(ct);q=c.unique[ct];cen=q.mean(1);norm=unit(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]));records=np.sort(np.concatenate([ct[:,[0,1]],ct[:,[1,2]],ct[:,[0,2]]]),axis=1);faces=np.tile(np.arange(nfaces),3);edges,inv,count=np.unique(records,axis=0,return_inverse=True,return_counts=True);order=np.argsort(inv);starts=np.r_[0,np.cumsum(count)];dual=[]
for k in np.flatnonzero(count==2):dual.append([faces[order[starts[k]]],faces[order[starts[k]+1]],k])
dual=np.array(dual,int);rows=[];out={'sourceAlias':INV,'primitiveOffsets':OFF,'uniqueRestPositions':c.unique,'clothFacesUnique':ct,'dualFaceEdges':dual,'sourceEdges':edges}
for sg,side in [(1,'L'),(-1,'R')]:
 hint=c.labels[sg]['faceSeed'];conf=abs(c.labels[sg]['faceScore']);normalData=np.clip((conf-.65)/.8,0,1)*200
 curve=RoundedCurve(P[[6,7,8]if sg==1 else[10,11,12]],c.ref[sg]['startNormal']);ss=curve.closest(cen);foot,*_=curve.at(ss);radial=cen-foot;outerUpper=(cen[:,1]>1.17)&(cen[:,1]<1.47)&(radial[:,2]*sg>.012)&(np.linalg.norm(radial,axis=1)<.14)&(c.labels[sg]['faceArmNormalFit']>.35);sleeveAnchor=c.labels[sg]['lowerSleeve'][ct].all(1)|outerUpper;torsoAnchor=(abs(cen[:,2])<.09)|(cen[:,1]>1.49)|((cen[:,1]<1.10)&~sleeveAnchor)|(cen[:,2]*sg<0)
 cost0=np.where(hint==1,normalData,0);cost1=np.where(hint==0,normalData,0);cost0[sleeveAnchor]=10000000;cost1[torsoAnchor]=10000000
 ndot=np.einsum('ij,ij->i',norm[dual[:,0]],norm[dual[:,1]]);ll=np.linalg.norm(c.unique[edges[dual[:,2],0]]-c.unique[edges[dual[:,2],1]],axis=1);smoothCost=np.maximum(1,np.rint(1000*ll/.01*(.035+.965*(1+ndot)*.5))).astype(np.int64)
 source=nfaces;sink=nfaces+1;a=np.r_[dual[:,0],dual[:,1],np.full(nfaces,source),np.arange(nfaces)];b=np.r_[dual[:,1],dual[:,0],np.arange(nfaces),np.full(nfaces,sink)];cap=np.r_[smoothCost,smoothCost,np.rint(cost1).astype(int),np.rint(cost0).astype(int)];capacity=coo_matrix((cap,(a,b)),shape=(nfaces+2,nfaces+2)).tocsr();result=maximum_flow(capacity,source,sink);residual=capacity-result.flow;residual.data=(residual.data>0).astype(np.int8);residual.eliminate_zeros();reach=breadth_first_order(residual,source,directed=True,return_predecessors=False);label=np.zeros(nfaces,bool);label[reach[reach<nfaces]]=True # source side is torso? Cost1 source edge cuts when sink(1), so reachable is0.
 sleeve=~label
 # Retain only face-connected sleeve component containing exact cuff triangles.
 dd=dual[sleeve[dual[:,:2]].all(1)];g=coo_matrix((np.ones(2*len(dd)),(np.r_[dd[:,0],dd[:,1]],np.r_[dd[:,1],dd[:,0]])),shape=(nfaces,nfaces)).tocsr();_,lab=connected_components(g);anchorFaces=np.flatnonzero(sleeveAnchor&sleeve);keepComp=np.unique(lab[anchorFaces]);sleeve&=np.isin(lab,keepComp)
 cut=dual[sleeve[dual[:,0]]!=sleeve[dual[:,1]]];ce=edges[cut[:,2]];loops,gate=ordered_loops(ce)
 out[f'sleeveFaces{side}']=sleeve;out[f'cutEdges{side}']=ce
 for j,loop in enumerate(loops):out[f'cutLoop{side}{j}']=np.array(loop,int)
 row={'side':side,'sleeveFaces':int(sleeve.sum()),'cutEdges':len(ce),'loops':len(loops),'loopLengths':[len(x)for x in loops],'loopRestRanges':[{'min':c.unique[x].min(0).tolist(),'max':c.unique[x].max(0).tolist()}for x in loops],'loopTopology':gate,'flow':int(result.flow_value),'limits':'Source-normal chart hints plus dual graph cut are an authored local partition, not measured sleeve sewing labels. No source geometry changed yet.'};rows.append(row);print(json.dumps(row),flush=True)
np.savez(HERE/'source-armhole-cut.npz',**out)
(HERE/'source-armhole-cut.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'sourceBackupSHA256':hashlib.sha256(backup.read_bytes()).hexdigest(),'rows':rows,'sourceAttributesUnmodified':True},indent=2))
