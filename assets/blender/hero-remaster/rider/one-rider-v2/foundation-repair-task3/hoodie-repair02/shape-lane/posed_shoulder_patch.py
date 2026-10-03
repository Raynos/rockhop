"""Pose compression corrective: fixed-boundary sewn shoulder disk harmonic surface.
Operates on geometric coordinates, includes BOTH material primitives and aliases.
Does not change rest and does not detach sleeve. No contacts/CCD assumption.
"""
from pathlib import Path
import sys,json,numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import factorized
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent
class Patch:
 def __init__(self,radius=.06):
  s=np.load(OUT/'shape-retop-uvsafe.npz');ct=np.concatenate([INV[s[f'tr{i}']+OFF[i]]for i in [0,2]]);self.patches=[];self.meta=[]
  for sg in [1,-1]:
   sel=((U[:,0]-.517)**2+((U[:,1]-1.367)*1.3)**2+((U[:,2]-sg*.183)*1.3)**2)<radius**2
   fs=ct[sel[ct].all(1)];ee=np.sort(np.concatenate([fs[:,[0,1]],fs[:,[1,2]],fs[:,[0,2]]]),axis=1);ee,count=np.unique(ee,axis=0,return_counts=True);boundary=np.unique(ee[count==1]);vs=np.unique(fs);inside=np.setdiff1d(vs,boundary);graph=coo_matrix((np.ones(2*len(ee)),(np.r_[ee[:,0],ee[:,1]],np.r_[ee[:,1],ee[:,0]])),shape=(len(U),len(U))).tocsr();L=diags(np.asarray(graph.sum(1)).ravel())-graph;self.patches.append((inside,boundary,factorized(L[inside][:,inside].tocsc()),L[inside][:,boundary]));self.meta.append({'side':sg,'radiusM':radius,'insideCount':len(inside),'boundaryCount':len(boundary),'euler':int(len(vs)-len(ee)+len(fs)),'boundaryEdgesDegree2':bool(np.all(np.bincount(ee[count==1].ravel())[boundary]==2))})
 def target(self,pos,D):
  if np.max(abs(D-np.eye(4)))<1e-10:return pos,{'additionalCorrectionM':0.,'identityRestExact':True}
  original=np.concatenate(pos);q=np.zeros_like(U);np.add.at(q,INV,original);q/=np.bincount(INV)[:,None];before=q.copy()
  for inside,boundary,solve,Lb in self.patches:
   rhs=-Lb@q[boundary];q[inside]=np.column_stack([solve(rhs[:,c])for c in range(3)])
  delta=q-before;out=[pos[i]+delta[INV[OFF[i]:OFF[i+1]]]for i in range(5)];return out,{'additionalCorrectionM':float(np.linalg.norm(delta,axis=1).max()),'identityRestExact':False,'patches':self.meta,'headExact':all(np.array_equal(out[i],pos[i])for i in [3,4]),'handsExact':np.array_equal(out[1],pos[1])}
if __name__=='__main__':
 patch=Patch();rows=[]
 for path in sorted(OUT.glob('differential-raise-*.npz'))+sorted(OUT.glob('differential-sit-*.npz')):
  d=np.load(path);p=[d[f'p{i}']for i in range(5)];q,m=patch.target(p,d['matrices']);newname=path.name.replace('differential-','differential-shoulder-');np.savez(OUT/newname,**{f'p{i}':v for i,v in enumerate(q)},matrices=d['matrices']);m['pose']=newname;rows.append(m);print(m,flush=True)
 (OUT/'differential-shoulder-provenance.json').write_text(json.dumps({'method':'Differentialcage followedbyfixed-boundary60mm sewnposteriorshoulderposecompressionpatch, source identityunchanged','rows':rows,'limits':'Finiteposecorrective. Fullcanonical/continuous/runtime/thicknessgatepending.'},indent=2))
