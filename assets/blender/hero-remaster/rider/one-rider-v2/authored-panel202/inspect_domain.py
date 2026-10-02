from pathlib import Path
import ast,json,struct,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
sha=lambda b:hashlib.sha256(b).hexdigest()
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/authored-panel202'
p=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py';n=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.ClassDef)and n.name=='GLB');exec(compile(ast.Module(body=[n],type_ignores=[]),str(p),'exec'))
g=GLB(B/'source-preserving-garment185/operator/rider.glb','ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5');a,F=g.primitive(0,0);U,q=np.unique(a['POSITION'],axis=0,return_inverse=True);T=q[F]
d=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/local-retopology-design200/source-domain-boundaries.json').read_text());scope=d['proposedSourceFaceIDs'];fig,axs=plt.subplots(1,3,figsize=(18,7))
for ax,xy,title in zip(axs,[[2,1],[0,1],[0,2]],['Front lateralZ / heightY','Side forwardX / heightY','Top forwardX / lateralZ']):
 faces=T[np.all((U[T][:,:,1]>1.10)&(U[T][:,:,1]<1.55)&(U[T][:,:,2]>.08),axis=1)]
 ax.add_collection(LineCollection(U[faces][:, [0,1,2,0]][:,:,xy],colors='#dddddd',linewidths=.15))
 ax.add_collection(LineCollection(U[T[scope]][:,[0,1,2,0]][:,:,xy],colors='#bce4d3',linewidths=.4))
 for c,col in zip(d['orderedBoundaryRings'],['#aa3377','#2277cc']):
  p=np.array(c['positionsM']);ax.plot(np.r_[p[:,xy[0]],p[0,xy[0]]],np.r_[p[:,xy[1]],p[0,xy[1]]],color=col,lw=1.5)
  for i in range(0,len(p),5):ax.text(*p[i,xy],str(i),fontsize=7,color=col)
 s=np.array(d['original45NodeSeamReference']['positionsM']);ax.plot(s[:,xy[0]],s[:,xy[1]],'r-',lw=2)
 ax.autoscale();ax.set_aspect('equal');ax.set_title(title);ax.grid()
fig.tight_layout();fig.savefig(E/'source-domain-projections.png',dpi=140)
print('readonly domain inspected')
