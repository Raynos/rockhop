"""Authored source garment chart seeds independent of old LS arm influences.
Reliable lower sleeve connected components are selected by exact sewn cuff
aliases. Upper opposing sheets are labelled only by confident source face-normal
agreement with estimated torso/arm radial normals; ambiguous bridge unlabelled.
"""
from rounded_curve import *
from scipy.sparse import coo_matrix,diags
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import factorized
class SourceCharts(RoundedSleeve):
 def __init__(self):
  super().__init__();ct=np.concatenate([INV[self.tri[i]+OFF[i]]for i in [0,2]]);self.ct=ct
  edges=np.unique(np.sort(np.concatenate([ct[:,[0,1]],ct[:,[1,2]],ct[:,[0,2]]]),axis=1),axis=0);self.edges=edges
  cuff=np.intersect1d(np.unique(ct),np.unique(INV[OFF[1]:OFF[2]]));self.cuff=cuff
  lower=U[:,1]<1.185;e=edges[lower[edges].all(1)];g=coo_matrix((np.ones(2*len(e)),(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr();_,component=connected_components(g)
  q=self.unique[ct];centre=q.mean(1);normal=unit(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]));cx=(P[6,0]+P[10,0])*.5;torsoNormal=unit(np.c_[centre[:,0]-cx,np.zeros(len(centre)),centre[:,2]])
  ll=np.linalg.norm(self.unique[edges[:,0]]-self.unique[edges[:,1]],axis=1);ew=(.008/np.maximum(ll,.002))**2;g=coo_matrix((np.r_[ew,ew],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(U),len(U))).tocsr();self.L=diags(np.asarray(g.sum(1)).ravel())-g
  self.labels={};self.fields={};self.meta=[]
  for sg,a in [(1,6),(-1,10)]:
   components=np.unique(component[cuff[U[cuff,2]*sg>0]]);lowerSleeve=self.cloth&lower&np.isin(component,components)
   curve=RoundedCurve(P[[a,a+1,a+2]],self.ref[sg]['startNormal']);s=curve.closest(centre);cc,*_=curve.at(s);armNormal=unit(centre-cc);armFit=np.einsum('ij,ij->i',normal,armNormal);torsoFit=np.einsum('ij,ij->i',normal,torsoNormal);score=armFit-torsoFit
   faceDomain=(centre[:,2]*sg>.12)&(centre[:,1]>1.16)&(centre[:,1]<1.445)
   faceLabels=np.full(len(ct),-1,int);faceLabels[faceDomain&(score>.65)&(armFit>.55)]=1;faceLabels[faceDomain&(score<-.65)&(torsoFit>.55)]=0
   votes=np.zeros((len(U),2),int)
   for k in [0,1]:
    for j in range(3):np.add.at(votes[:,k],ct[faceLabels==k,j],1)
   # Conflicting incident face classes identify a physical sheet transition;
   # they remain free rather than impose a vertex-level hard cut.
   seed=np.full(len(U),-1,int);seed[(votes[:,0]>0)&(votes[:,1]==0)]=0;seed[(votes[:,1]>0)&(votes[:,0]==0)]=1
   seed[self.cloth&(((U[:,1]<1.10)&~lowerSleeve)|(abs(U[:,2])<.09)|(U[:,1]>1.49)|(U[:,2]*sg<0))]=0
   seed[lowerSleeve]=1
   fixed=np.flatnonzero(self.cloth&(seed>=0));free=np.flatnonzero(self.cloth&(seed<0));field=np.zeros(len(U));field[fixed]=seed[fixed]
   solve=factorized(self.L[free][:,free].tocsc());field[free]=solve(-self.L[free][:,fixed]@field[fixed]);field=np.clip(field,0,1)
   self.labels[sg]={'vertexSeed':seed,'faceSeed':faceLabels,'faceScore':score,'faceArmNormalFit':armFit,'faceTorsoNormalFit':torsoFit,'lowerSleeve':lowerSleeve,'conflictingVertexLabels':(votes>0).all(1)};self.fields[sg]=field
   self.meta.append({'side':sg,'lowerSleeveAliases':int(lowerSleeve.sum()),'confidentTorsoFaces':int((faceLabels==0).sum()),'confidentSleeveFaces':int((faceLabels==1).sum()),'conflictingSeedVertices':int(((votes>0).all(1)).sum()),'ambiguousFreeVertices':len(free),'torsoSeedVertices':int((seed==0).sum()),'sleeveSeedVertices':int((seed==1).sum())})
 def save(self):
  out={'sourceUniquePositions':U,'v7UniquePositions':self.unique,'sourceAlias':INV,'primitiveOffsets':OFF,'clothFacesUnique':self.ct,'cuffAliases':self.cuff}
  for sg,side in [(1,'L'),(-1,'R')]:
   for k,v in self.labels[sg].items():out[f'{k}{side}']=v
   out[f'harmonicField{side}']=self.fields[sg]
  np.savez(OUT/'source-chart-labels.npz',**out)
  (OUT/'source-chart-labels.json').write_text(json.dumps({'sourceV7BindSHA256':hashlib.sha256(self.input.read_bytes()).hexdigest(),'method':'True disconnected lower sleeve components seeded by sewn cuff aliases; high-confidence opposing source face-normal radial agreement; conflicting/ambiguous upper bridge free harmonic continuation','rows':self.meta,'limits':'Authored estimated anatomical chart labels, not measured body segmentation. Harmonic interpolation is a proposed chart, not seam/anatomy ground truth. Source face order concatenates actual V7 primitive0 then2; unique IDs use exact source aliases. No old LS weight score used to generate labels.'},indent=2))
if __name__=='__main__':
 c=SourceCharts();c.save();print(json.dumps(c.meta,indent=2))
