"""Literal plane intersections as read-only diagnostic, not whole-body cuts."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/head-join211');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/head-join211');a=np.load(B/'arrays.npz');rows=[];records={};im=Image.new('RGB',(1600,1200),'#eee');d=ImageDraw.Draw(im)
for k,(label,h) in enumerate([(l,h) for l,hs in [('s0m0p0',[.65,.7,.73,.76,.79,.82,.85,.88]),('s1m1p0',[1.46,1.49,1.52,1.55])] for h in hs]):
 v=a[label+'_v'];f=a[label+'_f'];v,iv=np.unique(v,axis=0,return_inverse=True);f=iv[f];q=v[f];cross=(q[:,:,1].min(1)<h)&(q[:,:,1].max(1)>h);ids=np.flatnonzero(cross);T=f[ids];edges=np.stack([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]],1);P=v[edges];m=(P[:,:,0,1]<h)!=(P[:,:,1,1]<h);ee=edges[m];tt=np.repeat(ids,3).reshape(-1,3)[m];U,inv=np.unique(np.sort(ee,axis=1),axis=0,return_inverse=True);t=(h-v[U[:,0],1])/(v[U[:,1],1]-v[U[:,0],1]);p=v[U[:,0]]+t[:,None]*(v[U[:,1]]-v[U[:,0]]);seg=inv.reshape(-1,2);adj={}
 for i,j in seg:
  adj.setdefault(int(i),[]).append(int(j));adj.setdefault(int(j),[]).append(int(i))
 todo=set(adj);loops=[]
 while todo:
  seed=todo.pop();group={seed};st=[seed]
  while st:
   for j in adj[st.pop()]:
    if j in todo:todo.remove(j);group.add(j);st.append(j)
  ids2=sorted(group);xyz=p[ids2];loops.append({'nodes':len(group),'degreeSet':sorted(set(len(adj[i]) for i in group)),'bounds':[xyz.min(0).tolist(),xyz.max(0).tolist()],'mean':xyz.mean(0).tolist(),'sectionNodes':ids2})
 key=f'{label}-{h}';records[key]={'sourceCrossedFaces':ids.tolist(),'sourceCrossedEdges':U.tolist(),'sectionPositions':p.tolist(),'sectionSegments':seg.tolist(),'loops':loops};rows.append({'key':key,'loops':[{k:v for k,v in l.items() if k!='sectionNodes'} for l in loops]});x0=(k%4)*400;y0=(k//4)*400;d.text((x0+10,y0+10),key,fill='black');xy=p[:,[0,2]];lo=xy.min(0);hi=xy.max(0);scale=min(350/max(hi[0]-lo[0],.1),330/max(hi[1]-lo[1],.1));px=(xy-lo)*scale;px[:,1]=350-px[:,1]
 for i,j in seg:d.line([(x0+20+px[i,0],y0+20+px[i,1]),(x0+20+px[j,0],y0+20+px[j,1])],fill='#222',width=1)
 for n,loop in enumerate(loops):c=(px[loop['sectionNodes']]).mean(0);d.text((x0+20+c[0],y0+20+c[1]),str(n),fill='red')
(B/'sections.json').write_text(json.dumps(records,indent=2)+'\n');(E/'section-summary.json').write_text(json.dumps(rows,indent=2)+'\n');im.save(E/'section-projection.png');print(json.dumps(rows,indent=2))
