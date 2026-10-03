"""Small fixed-position diagonal retriangulation inside sewn shoulder disks.
Flips only actual same-material same-UV-index edges; all outside faces, exact
material boundary, per-vertex coordinates and UVs fixed. No cloth simulation.
"""
from pathlib import Path
import sys,numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent;src=np.load(OUT/'shape-rest-final.npz');pos=[src[f'p{i}'].copy()for i in range(5)];tri=[t.copy()for t in TRI];patches=json.load(open(OUT/'shoulder-r0.035-patches.json'));allowed=np.unique(np.concatenate([p['facesGlobalCombined']for p in patches]));logs=[]
def quality(q):
 area=np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]));edge2=sum(float(np.dot(q[a]-q[b],q[a]-q[b]))for a,b in [(0,1),(1,2),(2,0)]);return float(2*np.sqrt(3)*area/max(edge2,1e-20))
for prim,offset in [(0,0),(2,len(TRI[0]))]:
 faces=np.intersect1d(allowed,np.arange(offset,offset+len(TRI[prim])))-offset;t=tri[prim];p=pos[prim]
 for iteration in range(24):
  emap={}
  for f in faces:
   for a,b in [(0,1),(1,2),(2,0)]:emap.setdefault(tuple(sorted([int(t[f,a]),int(t[f,b])])),[]).append((int(f),int(t[f,a]),int(t[f,b]),int(t[f,3-a-b])))
  changes=0;used=set()
  for edge,rows in emap.items():
   if len(rows)!=2:continue
   (f,a,b,c),(g,x,y,d)=rows
   if f in used or g in used or x!=b or y!=a or c==d:continue
   if tuple(sorted([c,d]))in emap:continue
   old=p[t[[f,g]]];newtris=np.array([[c,d,b],[d,c,a]]);new=p[newtris];n0=np.cross(old[:,1]-old[:,0],old[:,2]-old[:,0]);n1=np.cross(new[:,1]-new[:,0],new[:,2]-new[:,0]);normal=n0.sum(0)
   if np.any(n1@normal<=1e-16):continue
   qo=[quality(q)for q in old];qn=[quality(q)for q in new]
   if min(qn)<min(qo)+1e-5:continue
   if min(qn)*sum(qn)<min(qo)*sum(qo)*1.025:continue
   a0=np.linalg.norm(n0,axis=1).sum();a1=np.linalg.norm(n1,axis=1).sum()
   if not .8<a1/max(a0,1e-15)<1.20:continue
   t[[f,g]]=newtris;changes+=1;used|={f,g};logs.append({'primitive':prim,'faces':[f,g],'removedEdge':[a,b],'newEdge':[c,d],'oldMinQuality':min(qo),'newMinQuality':min(qn)})
  if changes==0:break
 print('primitive',prim,'flipcount',sum(r['primitive']==prim for r in logs),flush=True)
# No coordinate edit. Recompute normals across exactly sewn clothing material vertices.
nt=np.concatenate([INV[tri[i]+OFF[i]]for i in [0,2]]);uq=np.zeros_like(U);np.add.at(uq,INV,np.concatenate(pos));uq/=np.bincount(INV)[:,None];q=uq[nt];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);un=np.zeros_like(U)
for j in range(3):np.add.at(un,nt[:,j],fn)
un/=np.maximum(np.linalg.norm(un,axis=1,keepdims=True),1e-15);normal=[NOR[i].copy()for i in range(5)]
for i in [0,2]:normal[i]=un[INV[OFF[i]:OFF[i+1]]]
np.savez(OUT/'shape-retop-final.npz',**{f'p{i}':p for i,p in enumerate(pos)},**{f'n{i}':n for i,n in enumerate(normal)},**{f'tr{i}':t for i,t in enumerate(tri)},sourceAlias=INV,primitiveOffsets=OFF)
rows=[]
for i,off in [(0,0),(2,len(TRI[0]))]:
 f=np.intersect1d(allowed,np.arange(off,off+len(TRI[i])))-off;old=np.array([quality(pos[i][t])for t in TRI[i][f]]);new=np.array([quality(pos[i][t])for t in tri[i][f]]);rows.append({'primitive':i,'patchFaces':len(f),'sourceDiagonalMinQuality':float(old.min(initial=1)),'newDiagonalMinQuality':float(new.min(initial=1)),'sourceDiagonalMeanQuality':float(old.mean()),'newDiagonalMeanQuality':float(new.mean()),'oldBelowPoint1':int((old<.1).sum()),'newBelowPoint1':int((new<.1).sum()),'changedFaceCount':int(np.any(tri[i]!=TRI[i],axis=1).sum())})
rep={'sourceSHA256':hashlib.sha256(G.raw).hexdigest(),'shapeBaseSHA256':hashlib.sha256((OUT/'shape-rest-final.npz').read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256((OUT/'shape-retop-final.npz').read_bytes()).hexdigest(),'method':'Local sewn shoulder disk diagonal flips to improve triangle quality. Same vertices/UVs/material slot; no crossing material seam or UV duplicate-index seam. Coordinate arrays exact to shape-rest-final. No runtimecloth.','flipCount':len(logs),'quality':rows,'logs':logs,'limits':'Retriangulation removes source-face correspondence for changedface area ratios. Must qualify actual deformed triangle areas using new restfaces and exact exported topology; no inference from reduced bad oldface counts. Full finite crossing gate follows.'};(OUT/'shape-retop-provenance.json').write_text(json.dumps(rep,indent=2));print(json.dumps({k:v for k,v in rep.items()if k!='logs'},indent=2))
