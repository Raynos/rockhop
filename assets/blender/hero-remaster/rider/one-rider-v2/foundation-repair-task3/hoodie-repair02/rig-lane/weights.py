from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.sparse.linalg import spsolve
HERE=Path(__file__).resolve().parent
SOFT='--soft-seeds'in sys.argv
C1='--c1'in sys.argv
SOFTANCHOR='--soft-anchor'in sys.argv
sys.path.insert(0,str(HERE.parent/'scripts'))
from base import *
cloth=np.unique(CT);mask=np.zeros(len(U),bool);mask[cloth]=True
y=U[:,1];z=abs(U[:,2]);e=edges
low=mask&(y<1.185);le=e[low[e].all(1)]
lg=coo_matrix((np.ones(2*len(le)),(np.r_[le[:,0],le[:,1]],np.r_[le[:,1],le[:,0]])),shape=(len(U),len(U))).tocsr()
_,lab=connected_components(lg,directed=False)
seed={}
for side,sg in [('L',1),('R',-1)]:
 c=lab[np.argmin(np.linalg.norm(U-[.61,1.1,sg*.285],axis=1))]
 seed[side]=low&(lab==c)&(y>.87)
length=np.linalg.norm(U[e[:,0]]-U[e[:,1]],axis=1)
adj=coo_matrix((np.r_[1/np.maximum(length,.001),1/np.maximum(length,.001)],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr()
degree=np.asarray(adj.sum(1)).ravel();lap=-adj
lap=lap+coo_matrix((degree,(np.arange(len(U)),np.arange(len(U)))),shape=lap.shape).tocsr()
# Exact source lower sleeve components and torso core are semantic anchors, not global height bands.
torsoLabel=lab[np.argmin(np.linalg.norm(U-[.64,1.1,0],axis=1))]
torsoSeed=low&(lab==torsoLabel)&(y>.94)
if SOFT:
 metric=coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr()
 for name,region in [('torso',torsoSeed),*seed.items()]:
  crossingEdges=e[region[e[:,0]]!=region[e[:,1]]]
  frontier=np.unique(crossingEdges[region[crossingEdges]])
  dist=dijkstra(metric,indices=frontier,min_only=True,directed=False)
  eroded=region&(dist>.070)
  if name=='torso':torsoSeed=eroded
  else:seed[name]=eroded
anchor0=mask&((z<.125)|torsoSeed|((y>1.46)&(z<.19)))
owner={}
for side,sg in [('L',1),('R',-1)]:
 fixed1=seed[side]|(mask&(sg*U[:,2]>.255)&(y<1.43)&(y>.94))
 fixed0=anchor0|(mask&(sg*U[:,2]<0))|(~mask)|(y<.87)
 fixed0&=~fixed1
 penalty=None
 if SOFTANCHOR:
  marker1=seed[side]|(mask&(sg*U[:,2]>.255)&(y<1.43)&(y>.94))
  marker0=torsoSeed
  metric=coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr()
  confidence=np.zeros(len(U))
  for region in [marker0,marker1]:
   boundary=e[region[e[:,0]]!=region[e[:,1]]]
   frontier=np.unique(boundary[region[boundary]])
   dist=dijkstra(metric,indices=frontier,min_only=True,directed=False)
   confidence[region]=smooth(dist[region]/.080)
  cuffids=np.intersect1d(INV[OFF[0]:OFF[1]],INV[OFF[1]:OFF[2]])
  cuffids=cuffids[U[cuffids,2]*sg>0]
  cuffdist=dijkstra(metric,indices=cuffids,min_only=True,directed=False)
  fixed1=mask&(cuffdist<.015)
  fixed0=(mask&(z<.080))|(mask&(sg*U[:,2]<0))|(~mask)|(y<.87)|(y>1.49)
  penalty=.18*degree*confidence
 fixed=fixed0|fixed1;free=np.flatnonzero(~fixed);fi=np.flatnonzero(fixed)
 v=np.zeros(len(U));v[fixed1]=1
 # Screen weakly against lateral sleeve-axis proximity; hard semantic anchors dominate.
 a=IND['upperArm.'+side];b=a+1;axis=P[b]-P[a]
 t=np.clip(np.einsum('ij,j->i',U-P[a],axis)/np.dot(axis,axis),0,1)
 centre=P[a]+t[:,None]*axis
 proximity=np.linalg.norm(U-centre,axis=1)
 prior=smooth((.16-proximity)/.09)*(U[:,2]*sg>0)
 screening=(.002 if SOFTANCHOR else .03)*np.maximum(degree[free],1)
 if SOFTANCHOR:screening+=penalty[free]
 mat=lap[free][:,free]+coo_matrix((screening,(np.arange(len(free)),np.arange(len(free)))),shape=(len(free),len(free))).tocsr()
 rhs=-lap[free][:,fi]@v[fi]+screening*prior[free]
 if SOFTANCHOR:rhs=-lap[free][:,fi]@v[fi]+.002*np.maximum(degree[free],1)*prior[free]+penalty[free]*marker1[free]
 v[free]=spsolve(mat,rhs);owner[side]=smooth(v)if C1 else np.clip(v,0,1)
uw=np.zeros((len(U),N));cnt=np.bincount(INV)
np.add.at(uw,INV,np.concatenate(W));uw/=cnt[:,None]
tor=uw.copy();tor[:,[5,6,7,8,9,10,11,12]]=0
tot=tor.sum(1);tor/=np.maximum(tot[:,None],1e-15);tor[tot<1e-9]=0;tor[tot<1e-9,2]=1
new=uw.copy();use=mask&(y>.87)&(y<1.49)
alpha=owner['L']+owner['R'];nw=tor*(1-alpha[:,None])
for side,sg in [('L',1),('R',-1)]:
 a,b,c=[IND[s+'.'+side]for s in ['upperArm','forearm','hand']]
 axis=P[b]-P[a];t=np.einsum('ij,j->i',U-P[a],axis)/np.dot(axis,axis)
 fore=smooth((t-.76)/.39)
 # A cuff sewn to a rigid glove follows that hand for ~2cm, then transitions through the forearm.
 handalias=np.intersect1d(INV[OFF[0]:OFF[1]],INV[OFF[1]:OFF[2]])
 cuff=handalias[U[handalias,2]*sg>0]
 graph=coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr()
 dc=dijkstra(graph,indices=cuff,min_only=True,directed=False)
 wrist=1-smooth((dc-.018)/.072);wrist[~np.isfinite(dc)]=0
 arm=np.zeros_like(uw);arm[:,a]=1-fore;arm[:,b]=fore*(1-wrist);arm[:,c]=fore*wrist
 # Shared cuff aliases are mandatory exact rigid hand anchors.
 arm[cuff]=0;arm[cuff,c]=1
 nw+=arm*owner[side][:,None]
new[use]=nw[use]
# Copy frozen hand/head weights across every alias, never average changed cloth into rigid parts.
for i in [1,3,4]:new[INV[OFF[i]:OFF[i+1]]]=W[i]
si=np.argsort(new,axis=1)[:,-4:];val=np.take_along_axis(new,si,axis=1);val/=val.sum(1,keepdims=True)
new[:]=0;np.put_along_axis(new,si,val,axis=1)
out=[new[INV[OFF[i]:OFF[i+1]]]for i in range(5)]
stem='weights-soft-anchor'if SOFTANCHOR else'weights-c1'if C1 else'weights-softened'if SOFT else'anatomical-weights'
np.savez(HERE/f'{stem}.npz',**{f'W{i}':w for i,w in enumerate(out)},ownershipL=owner['L'],ownershipR=owner['R'],uniquePositions=U,sourceCentres=P)
record={'sourceSHA256':hashlib.sha256(G.raw).hexdigest(),'method':'Harmonic semantic ownership with source-topology sleeve components, fixed torso core/side anchors, screened distance to upper-arm axis; all exact aliases copied from one welded field; rigid glove/head ownership restored. Arm-to-forearm based longitudinal joint-axis projection; wrist cuff distance on true garment graph.','changedVertices':sum(int((np.abs(a-b).max(1)>1e-10).sum())for a,b in zip(W,out)),'rigidPrimitivesUnchanged':all(np.array_equal(a,b)for a,b in zip([W[i]for i in [1,3,4]],[out[i]for i in [1,3,4]])),'aliasGap':float(max(np.abs(out[i]-new[INV[OFF[i]:OFF[i+1]]]).max()for i in range(5))),'jointCentresUnchanged':True,'shapeAssumption':'Weights computed on frozen source connectivity/positions; can apply to envelope variant with identical vertex and triangle ordering. No topology-remap support implicit.','limits':'Harmonic ownership cannot repair low armhole envelope or rest shoulder triangle crossings. Requires shape/pose gates and full export parity before acceptance.'}
record['geodesicSeedErosionM']=.070 if SOFT else 0
record['C1OwnershipEndpoints']=C1
record['SoftSemanticAnchors']=SOFTANCHOR
(HERE/f'{stem}-provenance.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
