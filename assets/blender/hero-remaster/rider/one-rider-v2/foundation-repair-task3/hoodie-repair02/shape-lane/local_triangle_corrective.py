"""Literal local triangle separation corrective for owned geometric pose targets.
Six-edge transverse witnesses; minimum local plane displacement candidate, 0.2mm
clearance,5mm total vertex cap. Not simulation, CCD or fullbodycontact proof.
"""
from pathlib import Path
import sys,numpy as np,json
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent;EPS=1e-9
exec('def crossing'+(ROOT/'audit/self_intersections.py').read_text().split('def crossing')[1].split('def audit')[0])
class LocalTriangleCorrective:
 def __init__(self):
  sd=np.load(OUT/'shape-retop-uvsafe.npz');ct=np.concatenate([INV[sd[f'tr{i}']+OFF[i]]for i in [0,2]]);roi=((U[ct][:,:,1]>1.08)&(U[ct][:,:,1]<1.49)&(abs(U[ct][:,:,2])<.405)).all(1);self.tri=ct[roi];self.ids=np.flatnonzero(roi);self.forbidden=np.unique(np.concatenate([INV[OFF[i]:OFF[i+1]]for i in [1,3,4]]))
 def pairs(self,q):
  t=self.tri;T=q[t];cent=T.mean(1);rad=np.linalg.norm(T-cent[:,None],axis=2).max(1);tree=cKDTree(cent);pairs=np.array([(a,b)for a,row in enumerate(tree.query_ball_point(cent,rad+rad.max()))for b in row if a<b],int).reshape(-1,2);lo=T.min(1);hi=T.max(1);pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)];pairs=pairs[np.array([not set(t[a]).intersection(t[b])for a,b in pairs])];return pairs[crossing(T[pairs[:,0]],T[pairs[:,1]])]
 def target(self,p,clearance=.0002,cap=.005,iterations=12):
  q=np.zeros_like(U);np.add.at(q,INV,np.concatenate(p));q/=np.bincount(INV)[:,None];base=q.copy();history=[]
  for iteration in range(iterations):
   pairs=self.pairs(q);history.append(int(len(pairs)))
   if not len(pairs):break
   for fa,fb in pairs:
    options=[]
    for a,b in [(fa,fb),(fb,fa)]:
     va=self.tri[a];vb=self.tri[b]
     if np.intersect1d(va,self.forbidden).size:continue
     A=q[va];B=q[vb];n=np.cross(B[1]-B[0],B[2]-B[0]);n/=max(np.linalg.norm(n),1e-15);d=np.einsum('ij,j->i',A-B[0],n)
     for sg in [1,-1]:
      shift=np.maximum(clearance-sg*d,0)[:,None]*(sg*n);goal=A+shift;change=goal-base[va];length=np.linalg.norm(change,axis=1)
      if length.max()>cap:continue
      options.append((float(np.sum(shift**2)),va,goal))
    if options:
     _,va,goal=min(options,key=lambda r:r[0]);q[va]=goal
  final=self.pairs(q);delta=q-base;out=[p[i]+delta[INV[OFF[i]:OFF[i+1]]]for i in range(5)];return out,{'initialPairs':history[0],'finalPairs':len(final),'iterations':len(history),'pairHistory':history,'maxAdditionalCorrectionM':float(np.linalg.norm(delta,axis=1).max()),'finalWitnesses':self.ids[final].tolist()[:20],'headExact':all(np.array_equal(out[i],p[i])for i in [3,4]),'handsExact':np.array_equal(out[1],p[1]),'limits':'Finite strictcrossingtargets only. Not CCD, thicknesscertificate or clothforce. Newcrosses/trianglequality require independentgate.'}
if __name__=='__main__':
 edit=LocalTriangleCorrective();rows=[]
 for path in sorted(OUT.glob('differential-raise-*.npz'))+sorted(OUT.glob('differential-sit-*.npz')):
  d=np.load(path);p=[d[f'p{i}']for i in range(5)];q,m=edit.target(p);name=path.name.replace('differential-','differential-local-');np.savez(OUT/name,**{f'p{i}':v for i,v in enumerate(q)},matrices=d['matrices']);m['pose']=name;rows.append(m);print(m,flush=True)
 (OUT/'differential-local-provenance.json').write_text(json.dumps({'method':'Differentialcage thenliteralnonadjacenttriangle localplane separatingcorrective .2mmoffset5mmcap. All exactaliasescommon.','rows':rows},indent=2))
