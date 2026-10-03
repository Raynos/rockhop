"""Fresh chart ownership on frozen V7 geometry, no pose optimization or cage.
Semantic geodesic confidence softens opposing-normal seed regions; hard anchors
are only exact rigid seam groups and preserved leg ownership. Whole sewn cloth
graph is solved, never a height-cut region. Source chart labels are authored hints.
"""
from pathlib import Path
import sys,json,hashlib,numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve,factorized
from scipy.sparse.csgraph import dijkstra
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'mechanical-suite'))
CHARTDIR=HERE
from data import *
HERE=CHARTDIR
OUT=HERE
f=np.load(HERE.parent/'mechanical-suite/input/v7-bind.npz');pp=[f[f'p{i}']for i in range(5)];old=[f[f'W{i}']for i in range(5)];tri=[f[f'tr{i}']for i in range(5)]
labels=np.load(HERE/'inputs/source-chart-labels.npz');assert np.array_equal(labels['sourceAlias'],INV);assert np.array_equal(labels['sourceUniquePositions'],U)
ct=labels['clothFacesUnique'];cloth=np.zeros(len(U),bool);cloth[np.unique(ct)]=True
unique=np.zeros_like(U);np.add.at(unique,INV,np.concatenate(pp));count=np.bincount(INV);unique/=count[:,None]
basew=np.zeros((len(U),N));np.add.at(basew,INV,np.concatenate(old));basew/=count[:,None]
e=np.unique(np.sort(np.concatenate([ct[:,[0,1]],ct[:,[1,2]],ct[:,[0,2]]]),axis=1),axis=0);length=np.linalg.norm(unique[e[:,0]]-unique[e[:,1]],axis=1)
q=unique[ct];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);normal=np.zeros_like(U)
for k in range(3):np.add.at(normal,ct[:,k],fn)
normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-15)
agreement=np.einsum('ij,ij->i',normal[e[:,0]],normal[e[:,1]],optimize=False)
# Surface topology alone establishes connectivity; source-normal agreement only
# modulates its conductance. There are no nearest-position cross-sheet links.
conductance=(.08+.92*np.maximum(agreement,0)**2)/np.maximum(length,.002)
g=coo_matrix((np.r_[conductance,conductance],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr();degree=np.asarray(g.sum(1)).ravel();L=diags(degree)-g
metric=coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=L.shape).tocsr()
cuff=labels['cuffAliases'];assert len(cuff)==127
insert=np.intersect1d(np.unique(INV[OFF[0]:OFF[1]]),np.unique(INV[OFF[2]:OFF[3]]));assert len(insert)==307
rigid=np.unique(np.concatenate([INV[OFF[i]:OFF[i+1]]for i in [1,3,4]]));leg=(basew[:,13:].sum(1)>.5)&cloth
B=coo_matrix((np.r_[np.ones(len(e)),-np.ones(len(e))],(np.r_[np.arange(len(e)),np.arange(len(e))],np.r_[e[:,0],e[:,1]])),shape=(len(e),len(U))).tocsr()
owner={};stats=[]
for side,sg in [('L',1),('R',-1)]:
 seed=labels[f'vertexSeed{side}'].copy();semantic=cloth&(seed>=0)
 # Include UNKNOWN and opposite-class neighbors in the confidence frontier.
 frontierEdges=e[((seed[e[:,0]]!=seed[e[:,1]])|labels[f'conflictingVertexLabels{side}'][e].any(1))&semantic[e].any(1)]
 frontier=np.unique(frontierEdges);dist=dijkstra(metric,indices=frontier,min_only=True,directed=False)
 confidence=np.zeros(len(U));confidence[semantic]=smooth(dist[semantic]/.060)
 conflict=labels[f'conflictingVertexLabels{side}'];confidence[conflict]=0
 cuffSide=cuff[U[cuff,2]*sg>0];hard0=(~cloth)|leg|np.isin(np.arange(len(U)),rigid);hard1=np.zeros(len(U),bool);hard1[cuffSide]=True;hard0[hard1]=False
 fixed=hard0|hard1;free=np.flatnonzero(~fixed);fixedids=np.flatnonzero(fixed);v=np.zeros(len(U));v[hard1]=1
 penalty=.12*degree*confidence
 # Tiny zero screen anchors unconstrained islands without using legacy ownership.
 screen=1e-6*np.maximum(degree,1)
 A=L[free][:,free]+diags(penalty[free]+screen[free]);rhs=-L[free][:,fixedids]@v[fixedids]+penalty[free]*(seed[free]==1)
 v[free]=spsolve(A,rhs)
 # Bounded geodesic gradient QP. This is pose-independent: its constraints
 # refer only to sewn rest edges, never a fit to the304 or endpoint geometry.
 # Normal disagreement may hint at charts, but cannot excuse a sudden motion
 # ownership jump over a2mm shared garment edge.
 rho=12.;bound=8*np.maximum(length,1e-5)
 solve=factorized(((1+rho)*L[free][:,free]+diags(penalty[free]+screen[free])).tocsc())
 fixedRHS=-(1+rho)*L[free][:,fixedids]@v[fixedids]+penalty[free]*(seed[free]==1)
 z=np.clip(B@v,-bound,bound);dual=np.zeros(len(e));violation=1.
 for iteration in range(1000):
  v[free]=solve(fixedRHS+rho*(B[:,free].T@(conductance*(z-dual))))
  bv=B@v;previous=z.copy();z=np.clip(bv+dual,-bound,bound);dual+=bv-z
  violation=float(np.maximum(abs(bv)-bound,0).max())
  if violation<1e-6 and float(abs(z-previous).max())<1e-6:break
 v=np.clip(v,0,1);owner[side]=v
 actualViolation=float(np.maximum(abs(B@v)-bound,0).max())
 opposite=(seed[e[:,0]]>=0)&(seed[e[:,1]]>=0)&(seed[e[:,0]]!=seed[e[:,1]])
 stats.append({'boundedGradientPerM':8.,'gradientQPBudget':1000,'gradientQPIterations':iteration+1,'maxOwnershipBoundViolation':actualViolation,'gradientQPConverged':actualViolation<1e-6,'side':side,'opposingHintEdges':int(opposite.sum()),'hardOpposingHintEdges':0,'confidenceAtOpposingEdgesMax':float(confidence[np.unique(e[opposite])].max(initial=0)),'confidenceFrontierVertices':len(frontier),'softSeedVertices':int((confidence>0).sum()),'fixedCuffCount':len(cuffSide),'maxOwnershipEdgeDifference':float(abs(v[e[:,0]]-v[e[:,1]]).max()),'p99OwnershipEdgeDifference':float(np.quantile(abs(v[e[:,0]]-v[e[:,1]]),.99))})
alpha=owner['L']+owner['R'];over=alpha>1
for side in owner:owner[side][over]/=alpha[over]
alpha=owner['L']+owner['R']
armIds=[6,7,8,10,11,12];tor=basew.copy();tor[:,armIds]=0;tor[:,[5,9]]=0;tot=tor.sum(1);tor/=np.maximum(tot[:,None],1e-15);tor[tot<1e-12]=0;tor[tot<1e-12,2]=1
freshArm={}
for side,sg in [('L',1),('R',-1)]:
 a,b,c=[IND[n+'.'+side]for n in ['upperArm','forearm','hand']];u=P[b]-P[a];v=P[c]-P[b];l1=np.linalg.norm(u);l2=np.linalg.norm(v);tu=np.clip(np.einsum('ij,j->i',unique-P[a],u,optimize=False)/np.dot(u,u),0,1);tv=np.clip(np.einsum('ij,j->i',unique-P[b],v,optimize=False)/np.dot(v,v),0,1)
 du=np.linalg.norm(unique-(P[a]+tu[:,None]*u),axis=1);dv=np.linalg.norm(unique-(P[b]+tv[:,None]*v),axis=1);s=np.where(du<=dv,tu*l1,l1+tv*l2)
 # Blend about the actual elbow arc coordinate; neither coordinate nor region
 # is based on global height. Cuff blend uses true sewn intrinsic distance.
 fore=smooth((s-(l1-.065))/.130);cs=cuff[U[cuff,2]*sg>0];dc=dijkstra(metric,indices=cs,min_only=True,directed=False);hand=1-smooth(dc/.075);hand[~np.isfinite(dc)]=0
 aw=np.zeros_like(basew);aw[:,a]=(1-fore)*(1-hand);aw[:,b]=fore*(1-hand);aw[:,c]=hand;freshArm[side]=aw
for variant in ['chart-ownership','chart-anatomical']:
 nw=tor*(1-alpha[:,None])
 for side in ['L','R']:
  a=IND['upperArm.'+side];aw=freshArm[side]
  if variant=='chart-ownership':
   local=basew[:,a:a+3];total=local.sum(1);aw=np.zeros_like(basew);aw[:,a:a+3]=local/np.maximum(total[:,None],1e-15);empty=total<1e-12;aw[empty]=freshArm[side][empty]
  nw+=aw*owner[side][:,None]
 # Keep every outside-cloth, leg and rigid-head/glove original row exact.
 nw[~cloth|leg]=basew[~cloth|leg]
 for i in [1,3,4]:nw[INV[OFF[i]:OFF[i+1]]]=old[i]
 slots=np.argsort(nw,axis=1)[:,-4:];values=np.take_along_axis(nw,slots,axis=1);values/=np.maximum(values.sum(1,keepdims=True),1e-15);outw=np.zeros_like(nw);np.put_along_axis(outw,slots,values,axis=1)
 out=[outw[INV[OFF[i]:OFF[i+1]]]for i in range(5)];np.savez_compressed(HERE/(variant+'.npz'),**{f'W{i}':w for i,w in enumerate(out)},ownershipL=owner['L'],ownershipR=owner['R'],uniquePositions=U,sourceAlias=INV,sourceCentres=P)
 meta={'variant':variant,'geometrySHA256':hashlib.sha256((HERE.parent/'mechanical-suite/input/v7-bind.npz').read_bytes()).hexdigest(),'chartLabelsSHA256':hashlib.sha256((HERE/'inputs/source-chart-labels.npz').read_bytes()).hexdigest(),'weightsSHA256':hashlib.sha256((HERE/(variant+'.npz')).read_bytes()).hexdigest(),'method':'Whole source-sewn graph with normal-modulated conductance, semantic boundary geodesic soft confidence + bounded intrinsic8/m gradient QP; cuff/leg/rigid anchors only. No pose training, height eligibility mask, nearest-position sheet weld, cage, helper or DQ.','withinRegionDistribution':'Original normalized torso and arm bone proportions'if variant=='chart-ownership'else'Original normalized torso proportions; fresh actual-arm-axis/elbow/cuff assignment','stats':stats,'rigidPrimitiveWeightsExact':all(np.array_equal(out[i],old[i])for i in [1,3,4]),'cuffAliasGroups':len(cuff),'bodyInsertAliasGroups':len(insert),'allAliasWeightRowsExact':True,'maxNonzeroInfluences':int((outw>1e-12).sum(1).max()),'maxWeightSumError':float(abs(outw.sum(1)-1).max()),'changedClothUniqueVertices':int((np.abs(outw-basew).max(1)>1e-9)[cloth].sum()),'maxWeightEdgeDeltaL2':float(np.linalg.norm(outw[e[:,0]]-outw[e[:,1]],axis=1).max()),'limits':['Normal chart seeds are authored anatomical hints, not scanned cloth segmentation.','Softness/geodesic length and normal conductance are authored assumptions; ambiguities remain.','Torso within-region distribution and all leg/head/glove rows remain controlled source components; this is a fresh sleeve-ownership/arm assignment comparison, not an entirely replaced full-body bind.','Only actual triangle/moving visual/holdout gates can qualify the field.']}
 (HERE/(variant+'-provenance.json')).write_text(json.dumps(meta,indent=2));print(json.dumps(meta),flush=True)
