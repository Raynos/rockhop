"""Same-rest/same-D static weight ablation with literal sewn triangle gates."""
from pathlib import Path
import sys,json,hashlib,ast,numpy as np
from scipy.spatial import cKDTree
CHART=Path(__file__).resolve().parent;sys.path.insert(0,str(CHART.parent/'mechanical-suite'))
from data import *
from source34 import load_frozen_source34
f=np.load(CHART.parent/'mechanical-suite/input/v7-bind.npz');pp=[f[f'p{i}']for i in range(5)];tri0=[f[f'tr{i}']for i in range(5)];old=[f[f'W{i}']for i in range(5)]
base=np.concatenate([pp[0],pp[2]]);src=np.concatenate([POS[0],POS[2]]);tri=np.concatenate([tri0[0],tri0[2]+len(pp[0])]);_,alias=np.unique(src,axis=0,return_inverse=True)
# Reuse only the public narrow-phase definition, no old audit execution/writes.
code=(CHART.parents[2]/'audit/self_intersections.py').read_text();tree=ast.parse(code);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='crossing');exec(compile(ast.Module(body=[node],type_ignores=[]),'<reviewed strict triangle predicate>','exec'));EPS=1e-9
mask=((src[tri][:,:,1]>1.08)&(src[tri][:,:,1]<1.49)&(abs(src[tri][:,:,2])<.405)).all(1);ids=np.flatnonzero(mask);tr=tri[mask];ta=alias[tr];ed=np.unique(np.sort(np.concatenate([tr[:,[0,1]],tr[:,[1,2]],tr[:,[0,2]]]),axis=1),axis=0);l0=np.linalg.norm(base[ed[:,0]]-base[ed[:,1]],axis=1);a0=np.linalg.norm(np.cross(base[tr[:,1]]-base[tr[:,0]],base[tr[:,2]]-base[tr[:,0]]),axis=1)
allalias=INV;counts=np.bincount(INV)
def gate(pts,doTriangles):
 q=np.concatenate([pts[0],pts[2]]);T=q[tr];ratio=np.linalg.norm(q[ed[:,0]]-q[ed[:,1]],axis=1)/np.maximum(l0,1e-15);area=np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1)/np.maximum(a0,1e-15)
 avg=np.zeros((len(counts),3));np.add.at(avg,allalias,np.concatenate(pts));avg/=counts[:,None];out={'maxEdgeMinRest2mm':float(ratio[l0>=.002].max()),'p99EdgeMinRest2mm':float(np.quantile(ratio[l0>=.002],.99)),'collapsedFaces25Pct':int((area<.25).sum()),'minAreaRatio':float(area.min()),'sourceExactAliasMaxGapM':float(np.linalg.norm(np.concatenate(pts)-avg[allalias],axis=1).max())}
 if doTriangles:
  centre=T.mean(1);radius=np.linalg.norm(T-centre[:,None],axis=2).max(1);pairs=np.array([(a,b)for a,near in enumerate(cKDTree(centre).query_ball_point(centre,radius+radius.max()))for b in near if a<b],int).reshape(-1,2);lo=T.min(1);hi=T.max(1);pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)];shared=(ta[pairs[:,0],:,None]==ta[pairs[:,1],None,:]).any(2).sum(1);keep=shared<2;pairs=pairs[keep];shared=shared[keep];hit=crossing(T[pairs[:,0]],T[pairs[:,1]])
  out.update(strictNonadjacentCrossings=int((hit&(shared==0)).sum()),strictOneCornerCrossings=int((hit&(shared==1)).sum()),witnessCombinedFacePairs=ids[pairs[hit]].tolist()[:20])
 return out
poses=[('neutral',0,np.repeat(np.eye(4)[None],N,axis=0),False)]
for t in [.25,.375,.5,.625,.75,.875,1]:poses.append(('forward',t,legacy('forward',t),t in [.375,.625,.875]))
for angle in [30,45,60,75,90,105,120]:poses.append(('neutral_elbow',angle,neutral_elbow(angle),angle in [45,75,105]))
allgame=np.load(CHART/'source34-480-matrices.npz')['D']
for i in [114,186,304,426,250,350]:poses.append(('actual_source34',i,allgame[i],i in[250,350]))
variants={'control':old}
for name in ['chart-ownership','chart-anatomical']:
 x=np.load(CHART/(name+'.npz'));variants[name]=[x[f'W{i}']for i in range(5)]
rows=[];(CHART/'poses').mkdir(exist_ok=True)
for kind,value,D,holdout in poses:
 for variant,w in variants.items():
  pts=deform(pp,w,D);label=f'{variant}-{kind}-{value:g}';p=CHART/'poses'/(label+'.npz');np.savez_compressed(p,matrices=D,**{f'p{i}':x for i,x in enumerate(pts)})
  # Full triangle gates include endpoints and withheld actual/elbow/reach probes.
  metrics=gate(pts,True);row={'variant':variant,'probe':kind,'fraction':value,'holdout':holdout,'path':str(p),'worldMatricesSHA256':hashlib.sha256(D.tobytes()).hexdigest(),'headGlovePositionsControlExact':all(np.array_equal(pts[i],deform([pp[i]],[old[i]],D)[0])for i in [])};row.pop('headGlovePositionsControlExact');row['headGloveWeightsControlExact']=all(np.array_equal(w[i],old[i])for i in [1,3,4]);row.update(metrics);rows.append(row);print(json.dumps({k:v for k,v in row.items()if k not in ['path','witnessCombinedFacePairs']}),flush=True)
(CHART/'finite-gates.json').write_text(json.dumps({'geometryRestPath':str(CHART.parent/'mechanical-suite/input/v7-bind.npz'),'geometryRestSHA256':hashlib.sha256((CHART.parent/'mechanical-suite/input/v7-bind.npz').read_bytes()).hexdigest(),'method':'Frozen V7 triangle0+2 upper ROI; same exact worldD pervariant; sphere/AABB broadphase; strict six-edge transverse intersections. Complete shared source seam edges excluded; one-corner crossings reported separately. All morphs zero.','limits':['Finite21poses, not CCD.','No new shape/material, contact support, garment thickness or GPU/PBR acceptance.','Coplanar/tangent contacts not classified by strict transverse predicate.'],'rows':rows},indent=2))
