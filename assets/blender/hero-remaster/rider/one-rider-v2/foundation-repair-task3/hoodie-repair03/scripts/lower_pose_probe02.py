"""Finite all-cloth literal probe on a frozen garment-construction ablation."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
sys.path.insert(0,str(ROOT/'scripts'));from glb import GLB
Q=ROOT/'hoodie-repair02/qa-lane';G=GLB(ROOT/'deliverables/C19.glb');PR=[p for m in G.j['meshes']for p in m['primitives']]
GP=[G.array(p['attributes']['POSITION']).astype(float)for p in PR];GT=[G.array(p['indices']).astype(int).reshape(-1,3)for p in PR]
B=np.load(ROOT/'experiments/C19-bind.npz');_,alias=np.unique(np.concatenate(GP),axis=0,return_inverse=True);off=np.r_[0,np.cumsum([len(p)for p in GP])]
base={f'p{i}':GP[i]for i in range(5)};base.update({f'tr{i}':GT[i]for i in range(5)});base.update({f'W{i}':B[f'W{i}']for i in range(5)});base.update({f'physicalWeld{i}':alias[off[i]:off[i+1]]for i in range(5)})
s=(Q/'scripts/geometry_gate.py').read_text();ns={'np':np,'EPS':1e-9};exec(s[s.index('def crossing'):s.index('def region_geom')],ns);crossing=ns['crossing']
control_path=ROOT/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz';control=np.load(control_path)
paths=[ROOT/'hoodie-repair03/lower-foundation/construction02'/f'{v}.npz'for v in ['L0-separation','L1-material-ownership']]
variants=[('C19',base,None)]+[(p.stem,np.load(p),p)for p in paths]
out=ROOT/'hoodie-repair03/lower-foundation/pose-probe02';out.mkdir(parents=True,exist_ok=True)

def pair_gate(P,T,AL,newmask,lower):
 qq=P[T];lo,hi=qq.min(1),qq.max(1);cent=qq.mean(1);rad=np.linalg.norm(qq-cent[:,None],axis=2).max(1);tree=cKDTree(cent);al=AL[T];counts={'nonadjacent':0,'oneCorner':0,'involvingNewLining':0,'involvingOriginalLower':0};hits=[]
 for st in range(0,len(T),64):
  nearby=tree.query_ball_point(cent[st:st+64],rad[st:st+64]+rad.max());pairs=np.array([(st+i,j)for i,js in enumerate(nearby)for j in js if st+i<j],int).reshape(-1,2)
  if not len(pairs):continue
  pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)];shared=np.array([len(set(al[a]).intersection(al[b]))for a,b in pairs]);keep=shared<2;pairs=pairs[keep];shared=shared[keep]
  if not len(pairs):continue
  hit=crossing(qq[pairs[:,0]],qq[pairs[:,1]])
  for pair,n in zip(pairs[hit],shared[hit]):
   counts['nonadjacent'if n==0 else'oneCorner']+=1;counts['involvingNewLining']+=int(newmask[pair].any());counts['involvingOriginalLower']+=int(lower[pair].any());hits.append([int(pair[0]),int(pair[1]),int(n)])
 return counts,np.array(hits,int).reshape(-1,3)

rows=[]
for frame in [304,250,350]:
 D=control['D'][frame]
 for label,data,path in variants:
  Ps=[data[f'p{i}']for i in range(5)];Ts=[data[f'tr{i}']for i in range(5)];Ws=[data[f'W{i}']for i in range(5)];As=[data[f'physicalWeld{i}']for i in range(5)]
  posed=[np.einsum('vj,jab,vb->va',Ws[i],D[:,:3,:],np.c_[Ps[i],np.ones(len(Ps[i]))],optimize=False)for i in range(5)]
  P=np.concatenate([posed[0],posed[2]]);R=np.concatenate([Ps[0],Ps[2]]);T=np.concatenate([Ts[0],Ts[2]+len(Ps[0])]);AL=np.r_[As[0],As[2]];newmask=np.zeros(len(T),bool);newmask[len(GT[0]):len(Ts[0])]=True
  lower=np.zeros(len(T),bool);lower[:len(GT[0])]=(GP[0][GT[0]][:,:,1].min(1)<1.12)&(GP[0][GT[0]][:,:,1].max(1)>.75)
  rp,pp=R[T],P[T];r_area=np.linalg.norm(np.cross(rp[:,1]-rp[:,0],rp[:,2]-rp[:,0]),axis=1);p_area=np.linalg.norm(np.cross(pp[:,1]-pp[:,0],pp[:,2]-pp[:,0]),axis=1);ratio=p_area/np.maximum(r_area,1e-20)
  re=np.linalg.norm(rp-np.roll(rp,-1,axis=1),axis=2);pe=np.linalg.norm(pp-np.roll(pp,-1,axis=1),axis=2);meaning=re>.002;er=(pe/re)[meaning];lower_er=(pe/re)[meaning&lower[:,None]]
  used=np.unique(T);ids=AL[used];positions=P[used];_,inverse=np.unique(ids,return_inverse=True);low=np.full((inverse.max()+1,3),np.inf);high=np.full_like(low,-np.inf);np.minimum.at(low,inverse,positions);np.maximum.at(high,inverse,positions);gap=float(np.linalg.norm(high-low,axis=1).max())
  counts,hits=pair_gate(P,T,AL,newmask,lower)
  pose_path=out/f'{label}-{frame}.npz';np.savez(pose_path,**{f'p{i}':posed[i]for i in range(5)},matrices=D,allClothCrossingPairs=hits)
  row={'variant':label,'frame':frame,'matrixSHA256':hashlib.sha256(D.tobytes()).hexdigest(),'candidateSHA256':hashlib.sha256(path.read_bytes()).hexdigest()if path else hashlib.sha256(G.raw).hexdigest(),'allClothCrossings':counts,'collapsedAllClothQuarterArea':int((ratio<.25).sum()),'collapsedOriginalLowerQuarterArea':int(((ratio<.25)&lower).sum()),'collapsedNewLiningQuarterArea':int(((ratio<.25)&newmask).sum()),'maxMeaningfulEdgeStretch':float(er.max()),'maxOriginalLowerMeaningfulEdgeStretch':float(lower_er.max()),'originalLowerP99Stretch':float(np.percentile(lower_er,99)),'referencedSameGarmentWeldGapM':gap,'posePath':str(pose_path)};rows.append(row);print(json.dumps(row),flush=True)
report={'status':'FINITE_UNACCEPTED lower material separation comparison','controls':str(control_path),'controlSHA256':hashlib.sha256(control_path.read_bytes()).hexdigest(),'method':'Identical literal19-joint D across C19/L0/L1; no fitted morphs; cloth0+2 full-face strict transverse pairs with authoritative physicalWeld. Original lower =source face with any corner below1.12m and any corner above.75m, disclosed diagnostic subset only; all-cloth counts also retained. Meaningful edge rest>2mm.','limits':['Coplanar/tangent contact/thickness unclassified','Finite3recorded controls, not continuous/gameplay acceptance','No grip/sole/saddle pressure/contact certificate','L1 raw graph distance followed by weld reconciliation is a material ownership ablation, not anatomical truth'],'rows':rows}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
