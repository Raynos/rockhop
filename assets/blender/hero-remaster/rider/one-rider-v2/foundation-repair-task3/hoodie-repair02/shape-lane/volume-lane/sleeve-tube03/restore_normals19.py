from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import ROOT,INV,OFF,unit
src=HERE/'source-sleeve-tube-rest18-dart.npz';f=dict(np.load(src));shape=np.load(ROOT/'hoodie-repair02/v7-shape-input.npz');v7=np.load(ROOT/'hoodie-repair02/v7-bind.npz');counts=[len(v7[f'p{i}'])for i in range(5)]
refs={};clipped=[]
for pi in [0,2]:
 n=f[f'n{pi}'].copy();parents=f[f'sourceVertexParents{pi}'];bary=f[f'sourceVertexBarycentric{pi}'];ids=np.flatnonzero((np.arange(len(n))>=counts[pi])&(parents[:,0]>=0)&(parents[:,1]>=0))
 if len(ids):n[ids]=unit((shape[f'n{pi}'][parents[ids]]*bary[ids,:,None]).sum(1))
 f[f'n{pi}']=n;clipped.append({'primitive':pi,'rows':len(ids),'maxChangeDegrees':float(np.rad2deg(np.arccos(np.clip(np.einsum('ij,ij->i',n[ids],np.load(src)[f'n{pi}'][ids]),-1,1))).max(initial=0))})
 active=np.unique(f[f'tr{pi}']);source=active[(active<counts[pi])|np.isin(active,ids)]
 for i in source:refs.setdefault(int(f[f'physicalWeld{pi}'][i]),[]).append(n[i])
ref={k:unit(np.asarray(v).mean(0)[None])[0]for k,v in refs.items()};hard=[]
for k,v in refs.items():
 ns=np.asarray(v);angle=float(np.rad2deg(np.arccos(np.clip(np.einsum('ij,kj->ik',ns,ns),-1,1))).max(initial=0))
 if angle>10:hard.append({'physicalWeld':k,'maxSourceNormalSpreadDegrees':angle,'sourceRows':len(ns)})
# Graph of the actual patch in authoritative physical weld coordinates.
ids=np.unique(np.concatenate([f[f'physicalWeld{i}'][f[f'tr{i}']].ravel()for i in [0,2]]));lookup={int(k):j for j,k in enumerate(ids)};edges=[];points={}
for pi in [0,2]:
 p=f[f'p{pi}'];w=f[f'physicalWeld{pi}'];t=f[f'tr{pi}'];e=np.unique(np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[0,2]]]),axis=1),axis=0)
 for a,b in e:
  wa,wb=int(w[a]),int(w[b])
  if wa!=wb:edges.append((lookup[wa],lookup[wb],max(float(np.linalg.norm(p[a]-p[b])),1e-9)))
 for i in np.unique(t):points[int(w[i])]=p[i]
e=np.asarray(edges);g=coo_matrix((np.r_[e[:,2],e[:,2]],(np.r_[e[:,0],e[:,1]].astype(int),np.r_[e[:,1],e[:,0]].astype(int))),shape=(len(ids),len(ids))).tocsr();seeds=np.array([lookup[k]for k in ref if k in lookup]);dist,pred,nearest=dijkstra(g,indices=seeds,min_only=True,return_predecessors=True);margin=.020;changed=[]
for pi in [0,2]:
 old=f[f'n{pi}'].copy();nn=old.copy();w=f[f'physicalWeld{pi}'];active=np.unique(f[f'tr{pi}']);patch=active[active>=counts[pi]]
 for i in patch:
  k=int(w[i]);j=lookup[k]
  if k in refs:
   cand=np.asarray(refs[k]);nn[i]=cand[np.argmax(np.einsum('ij,j->i',cand,old[i]))]
  elif dist[j]<margin and nearest[j]>=0:
   target=ref[int(ids[nearest[j]])];alpha=(1-dist[j]/margin);alpha=alpha*alpha*(3-2*alpha);nn[i]=unit(((1-alpha)*old[i]+alpha*target)[None])[0]
 f[f'n{pi}']=nn;change=np.rad2deg(np.arccos(np.clip(np.einsum('ij,ij->i',old,nn),-1,1)));changed.append({'primitive':pi,'changedRowsAbove1degree':int((change>1).sum()),'maxChangeDegrees':float(change.max()),'originalPrefixExact':bool(np.array_equal(nn[:counts[pi]],shape[f'n{pi}']))})
out=HERE/'source-sleeve-tube-rest19-normal.npz';np.savez_compressed(out,**f)
report={'status':'NORMAL_ONLY_CLONE; standing visual review pending, no motion/runtime acceptance','parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'method':'Retained clipped source normals use exact normalized source-edge barycentric normals. New UV/patch seam rows adopt closest actual referenced source normal; inherited >10degree hard seams retained explicitly, not averaged away. Only appended patch normals blend toward nearest source seam within20mm actual sewn geodesic distance. Original all5 normal prefixes preserved. Geometry/UV/W/tr untouched.','clippedRows':clipped,'changes':changed,'inheritedHardSourceNormalGroups':hard,'geometryUVWeightsTrianglesExact':all(np.array_equal(f[k],np.load(src)[k])for k in f if not(k.startswith('n')and k[1:].isdigit())),'fiveInfluenceContractUnchanged':True}
(HERE/'source-sleeve-tube-rest19-normal-provenance.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items()if k!='inheritedHardSourceNormalGroups'},indent=2));print('inherited hard source groups',len(hard))
