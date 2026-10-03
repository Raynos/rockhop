from base import *
import hashlib
q=U.copy();y=U[:,1];z=abs(U[:,2]);x=U[:,0];cloth=np.unique(CT);mask=np.zeros(len(U),bool);mask[cloth]=True
# Compact anatomical underarm cage lifts the low gusset while leaving outer sleeves and head in place.
gusset=smooth((y-1.10)/.10)*smooth((1.46-y)/.13)*np.exp(-((z-.195)/.044)**4)*mask
q[:,1]+=.115*gusset
chest=smooth((y-1.08)/.12)*smooth((1.49-y)/.15)*smooth((.215-z)/.08)*smooth((x-.65)/.12)*mask
q[:,0]-=.032*chest
# Fair the existing shoulder insert locally, using welded neighbours including its sewn material boundary.
rr=np.r_[edges[:,0],edges[:,1]];cc=np.r_[edges[:,1],edges[:,0]];adj=coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(U),len(U))).tocsr();deg=np.asarray(adj.sum(1)).ravel();reg=np.exp(-((y-1.365)/.035)**4)*np.exp(-((z-.177)/.04)**4)*np.exp(-((x-.53)/.055)**4)*mask
for _ in range(8):q+=.28*reg[:,None]*(adj@q/np.maximum(deg[:,None],1)-q)
new=[q[INV[OFF[i]:OFF[i+1]]].copy()for i in range(5)];newW=[w.copy()for w in W]
# Geodesic sleeve/torso ownership uses disconnected lower sleeve components as seeds.
low=(U[:,1]<1.185)&mask;select=low[edges].all(1);le=edges[select];lgraph=coo_matrix((np.ones(2*len(le)),(np.r_[le[:,0],le[:,1]],np.r_[le[:,1],le[:,0]])),shape=(len(U),len(U))).tocsr();nc,labels=connected_components(lgraph,directed=False);seeds={}
for side,sg in [('L',1),('R',-1)]:
 c=labels[np.argmin(np.linalg.norm(U-np.array([.61,1.1,sg*.285]),axis=1))];seeds[side]=np.flatnonzero((labels==c)&low&(U[:,1]>.92));print(side,len(seeds[side]))
e=edges;length=np.linalg.norm(q[e[:,0]]-q[e[:,1]],axis=1);graph=coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr();torso=np.flatnonzero(mask&(z<.125)&(y>1.03)&(y<1.39));dt=dijkstra(graph,indices=torso,min_only=True,directed=False);da={side:dijkstra(graph,indices=s,min_only=True,directed=False)for side,s in seeds.items()}
owned={}
for side,sg in [('L',1),('R',-1)]:
 a,b,c=[IND[s+'.'+side]for s in ['upperArm','forearm','hand']];d=da[side];frac=np.divide(dt,dt+d,out=np.zeros(len(U)),where=np.isfinite(dt+d)&(dt+d>0));owner=smooth((frac-.30)/.40)*(U[:,2]*sg>0)*mask
 owner=np.where(np.isin(np.arange(len(U)),seeds[side]),1,owner)
 owned[side]=owner
 for i in [0,2]:
  ui=INV[OFF[i]:OFF[i+1]];alpha=owner[ui];use=mask[ui]&(POS[i][:,1]>.94)&(POS[i][:,1]<1.49)&(POS[i][:,2]*sg>0);pa=POS[i];ab=P[b]-P[a];bc=P[c]-P[b];t=np.einsum('ij,j->i',pa-P[a],ab)/np.dot(ab,ab);el=smooth((t-.79)/.20);wc=smooth((P[b,1]+.07-pa[:,1])/.14);arm=np.zeros_like(newW[i]);arm[:,a]=1-el;arm[:,b]=el*(1-wc);arm[:,c]=el*wc
  torsoW=newW[i].copy();torsoW[:,[5,6,7,8,9,10,11,12]]=0;tot=torsoW.sum(1);torsoW/=np.maximum(tot[:,None],1e-15);torsoW[tot<1e-9]=0;torsoW[tot<1e-9,2]=1
  nw=torsoW*(1-alpha[:,None])+arm*alpha[:,None];newW[i][use]=nw[use]
# Material aliases carry exactly one common weight vector.
aw=np.concatenate(newW);uw=np.zeros((len(U),N));np.add.at(uw,INV,aw);cnt=np.bincount(INV);uw/=cnt[:,None]
for i in [0,2]:newW[i]=uw[INV[OFF[i]:OFF[i+1]]]
for i in range(5):
 si=np.argsort(newW[i],axis=1)[:,-4:];val=np.take_along_axis(newW[i],si,axis=1);val/=val.sum(1,keepdims=True);o=np.zeros_like(newW[i]);np.put_along_axis(o,si,val,axis=1);newW[i]=o
np.savez(OUT/'round1-bind.npz',**{f'p{i}':p for i,p in enumerate(new)},**{f'W{i}':w for i,w in enumerate(newW)})
for layer,pos,w in [('control',POS,W),('shape',new,W),('weights',new,newW)]:
 for kind,t in [('rest',0),('raise',.5),('raise',1),('sit',0),('sit',.5),('sit',1)]:
  D=raise_pose(t)if kind=='raise'else sit_pose(t)if kind=='sit'else np.repeat(np.eye(4)[None],N,axis=0);p=deform(pos,w,D,kind=='sit');np.savez(OUT/'poses'/f'r1-{layer}-{kind}-{t}.npz',**{f'p{i}':x for i,x in enumerate(p)},matrices=D)
(OUT/'round1-provenance.json').write_text(json.dumps({'method':'Local anatomical envelope cage, welded shoulder insert fairing, lower-sleeve graph components as geodesic ownership seeds. No garment01 solver.','maxRestDisplacementM':float(np.linalg.norm(q-U,axis=1).max()),'changedUniqueVertices':int((np.linalg.norm(q-U,axis=1)>1e-9).sum()),'headExact':all(np.array_equal(POS[i],new[i])for i in [3,4]),'seeds':{s:len(v)for s,v in seeds.items()}},indent=2));print('ROUND1 PREPARED')
