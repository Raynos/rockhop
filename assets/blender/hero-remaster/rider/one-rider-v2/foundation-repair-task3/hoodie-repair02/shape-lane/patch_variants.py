from pathlib import Path
import sys,json,numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent
for radius in [.02,.025,.035,.04,.045,.05]:
 q=U.copy();patches=[]
 for sg in [1,-1]:
  select=((U[:,0]-.517)**2+((U[:,1]-1.367)*1.3)**2+((U[:,2]-sg*.183)*1.3)**2)<radius**2
  fs=CT[select[CT].all(1)];ee=np.sort(np.concatenate([fs[:,[0,1]],fs[:,[1,2]],fs[:,[0,2]]]),axis=1);ee,c=np.unique(ee,axis=0,return_counts=True);bv=np.unique(ee[c==1]);vs=np.unique(fs);iv=np.setdiff1d(vs,bv);adj=coo_matrix((np.ones(2*len(ee)),(np.r_[ee[:,0],ee[:,1]],np.r_[ee[:,1],ee[:,0]])),shape=(len(U),len(U))).tocsr();L=diags(np.asarray(adj.sum(1)).ravel())-adj
  q[iv]=spsolve(L[iv][:,iv],-L[iv][:,bv]@q[bv]);patches.append({'sideSign':sg,'radiusM':radius,'boundary':bv.tolist(),'interior':iv.tolist(),'facesGlobalCombined':np.flatnonzero(select[CT].all(1)).tolist(),'boundaryEdges':ee[c==1].tolist(),'eulerCharacteristic':len(vs)-len(ee)+len(fs),'boundaryExact':True})
 out={f'p{i}':q[INV[OFF[i]:OFF[i+1]]].copy()for i in range(5)};np.savez(OUT/f'shoulder-r{radius}.npz',**out,uniquePositions=q,sourceAlias=INV,sourceUnique=U,primitiveOffsets=OFF);(OUT/f'shoulder-r{radius}-patches.json').write_text(json.dumps(patches))
