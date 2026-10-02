"""Read-only cross-section provenance for a NEW T-pose rig authoring proposal."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/tpose-rig-adapter212'
z=np.load(B/'finite-cleanup210/ancestry.npz');P=z['positions'].astype(np.float64);F=z['faces']
c=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/head-join211/join-contract.json').read_text())
M=np.array(c['explicitBodyTransform']['matrixNativeToCanonical']);Q=P@M[:3,:3].T+M[:3,3]
def section(axis,h):
    mask=(Q[F,axis].min(1)<h)&(Q[F,axis].max(1)>h); ids=np.flatnonzero(mask); edges={};segments=[]
    for fi in ids:
        hits=[]
        for a,b in zip(F[fi],np.roll(F[fi],-1)):
            if (Q[a,axis]-h)*(Q[b,axis]-h)<0:
                edge=tuple(sorted((int(a),int(b))))
                if edge not in edges:
                    a,b=edge;t=(h-Q[a,axis])/(Q[b,axis]-Q[a,axis]);edges[edge]=(Q[a]+t*(Q[b]-Q[a]),float(t))
                hits.append(edge)
        assert len(hits)==2
        segments.append((hits[0],hits[1],int(fi)))
    adjacency={k:[] for k in edges}
    for a,b,fi in segments:adjacency[a].append(b);adjacency[b].append(a)
    assert all(len(v)==2 for v in adjacency.values())
    seen=set();loops=[];plane=[i for i in range(3) if i!=axis]
    for initial in adjacency:
        if initial in seen:continue
        ordered=[];previous=None;current=initial
        while current not in seen:
            seen.add(current);ordered.append(current);nexts=adjacency[current];nxt=nexts[0] if nexts[0]!=previous else nexts[1];previous,current=current,nxt
        assert current==initial
        pts=np.array([edges[e][0] for e in ordered]);xy=pts[:,plane];following=np.roll(xy,-1,axis=0);cross=xy[:,0]*following[:,1]-following[:,0]*xy[:,1];signed=cross.sum()/2
        assert abs(signed)>1e-16
        centroid=np.empty(3);centroid[axis]=h;centroid[plane]=((xy+following)*cross[:,None]).sum(0)/(6*signed)
        edgeids=[list(e) for e in ordered]
        loops.append({'samples':len(pts),'areaM2':float(abs(signed)),'areaCentroidCanonical':centroid.tolist(),'boundsCanonical':[pts.min(0).tolist(),pts.max(0).tolist()],'sourceEdges':edgeids,'edgeInterpolationT':[edges[e][1] for e in ordered]})
    return {'axis':axis,'planeCanonicalM':h,'crossedSourceFaces':ids.tolist(),'loops':loops}
sections=[section(1,h) for h in (.06,.115,.45,.49,.84,.9,1.04,1.22,1.30,1.39,1.45)]
sections += [section(2,sign*h) for sign in (-1,1) for h in (.18,.22,.34,.38,.42,.50,.54,.56,.58,.60,.62,.64)]
(E/'sections.json').write_text(json.dumps(sections,indent=2)+'\n')
summary=[{k:v for k,v in s.items() if k!='crossedSourceFaces'} for s in sections]
for s in summary:
    s['loops']=[{k:v for k,v in l.items() if k not in ('sourceEdges','edgeInterpolationT')} for l in s['loops']]
(E/'section-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
im=Image.new('RGB',(1600,1100),'#eeeeee');draw=ImageDraw.Draw(im)
for panel,(a,b,name) in enumerate(((2,1,'Canonical front Z/Y'),(0,1,'Canonical profile X/Y'))):
    offset=panel*800;xy=Q[:,[a,b]];low=np.array([-0.8,-.05]) if panel==0 else np.array([.35,-.05]);high=np.array([.8,1.85]) if panel==0 else np.array([.95,1.85]);scale=min(740/(high[0]-low[0]),1000/(high[1]-low[1]));screen=(xy-low)*scale
    for x,y in screen[::3]:
        if 0<=x<740 and 0<=y<1000:draw.point((offset+30+int(x),1060-int(y)),fill='#777777')
    draw.text((offset+30,20),name,fill='black')
im.save(E/'geometry-projection.png')
print(json.dumps([{'axis':s['axis'],'height':s['planeCanonicalM'],'loops':[{'c':l['areaCentroidCanonical'],'area':l['areaM2']} for l in s['loops']]} for s in summary],indent=2))
