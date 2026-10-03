"""All480 source34 matrix replay strain/area gates, fixed geometry/controlD."""
from pathlib import Path
import sys,json,hashlib,numpy as np
CHART=Path(__file__).resolve().parent;sys.path.insert(0,str(CHART.parent/'mechanical-suite'))
from data import *
f=np.load(CHART.parent/'mechanical-suite/input/v7-bind.npz');pp=[f[f'p{i}']for i in range(5)];tri=np.concatenate([f['tr0'],f['tr2']+len(pp[0])]);src=np.concatenate([POS[0],POS[2]]);base=np.concatenate([pp[0],pp[2]]);mask=((src[tri][:,:,1]>1.08)&(src[tri][:,:,1]<1.49)&(abs(src[tri][:,:,2])<.405)).all(1);tri=tri[mask];verts,inverse=np.unique(tri,return_inverse=True);localtri=inverse.reshape(-1,3);ed=np.unique(np.sort(np.concatenate([localtri[:,[0,1]],localtri[:,[1,2]],localtri[:,[0,2]]]),axis=1),axis=0);p=base[verts];l0=np.linalg.norm(p[ed[:,0]]-p[ed[:,1]],axis=1);a0=np.linalg.norm(np.cross(p[localtri[:,1]]-p[localtri[:,0]],p[localtri[:,2]]-p[localtri[:,0]]),axis=1)
D=np.load(CHART/'source34-480-matrices.npz')['D'];variants={'control':np.concatenate([f['W0'],f['W2']])[verts]}
for name in ['chart-ownership','chart-anatomical']:
 w=np.load(CHART/(name+'.npz'));variants[name]=np.concatenate([w['W0'],w['W2']])[verts]
rows=[]
for name,w in variants.items():
 for frame,m in enumerate(D):
  q=np.einsum('vj,jab,vb->va',w,m[:,:3,:],np.c_[p,np.ones(len(p))],optimize=False);rat=np.linalg.norm(q[ed[:,0]]-q[ed[:,1]],axis=1)/np.maximum(l0,1e-15);ar=np.linalg.norm(np.cross(q[localtri[:,1]]-q[localtri[:,0]],q[localtri[:,2]]-q[localtri[:,0]]),axis=1)/np.maximum(a0,1e-15);rows.append({'variant':name,'frame':frame,'maxEdgeMinRest2mm':float(rat[l0>=.002].max()),'p99EdgeMinRest2mm':float(np.quantile(rat[l0>=.002],.99)),'collapsedFaces25Pct':int((ar<.25).sum()),'minAreaRatio':float(ar.min())})
summary=[]
for name in variants:
 r=[x for x in rows if x['variant']==name];worst=max(r,key=lambda x:x['maxEdgeMinRest2mm']);summary.append({'variant':name,'maxEdge480':worst['maxEdgeMinRest2mm'],'worstFrame':worst['frame'],'maxCompressed480':max(x['collapsedFaces25Pct']for x in r),'meanMaxEdge':float(np.mean([x['maxEdgeMinRest2mm']for x in r]))})
(CHART/'sequence480-strain.json').write_text(json.dumps({'sourceMatricesSHA256':hashlib.sha256((CHART/'source34-480-matrices.npz').read_bytes()).hexdigest(),'method':'All480 exact actual source34 worldD; unchanged frozen V7rest; upper primitive0+2 ROI; same rest edge/area denominators; morphs0.','limits':['Strain/area metrics only on480recorded12fps samples, no all-frame collision or continuous certificate.','Separate finite21pose triangle/corner gates remain decisive; low stretch is not acceptance.'],'summary':summary,'rows':rows},indent=2));print(json.dumps(summary))
