"""CPU-only measurements of untouched MakeHuman CC0 eye surfaces."""
import json
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

root = Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes')
verts, normals, uvs, faces = [], [], [], []
for line in (root/'high-poly/high-poly.obj').read_text().splitlines():
    tokens = line.split()
    if not tokens:
        continue
    if tokens[0] == 'v': verts.append(list(map(float, tokens[1:4])))
    elif tokens[0] == 'vn': normals.append(list(map(float, tokens[1:4])))
    elif tokens[0] == 'vt': uvs.append(list(map(float, tokens[1:3])))
    elif tokens[0] == 'f': faces.append([tuple(int(x)-1 for x in s.split('/')) for s in tokens[1:]])
v, n, uv = map(np.array, (verts, normals, uvs))
adj = [set() for _ in v]
for f in faces:
    for a,b in zip(f, f[1:]+f[:1]):
        adj[a[0]].add(b[0]); adj[b[0]].add(a[0])
unseen = set(range(len(v))); comps=[]
while unseen:
    stack=[min(unseen)]; c=set(stack); unseen.difference_update(c)
    while stack:
        q=stack.pop()
        for x in adj[q]&unseen:
            unseen.remove(x);c.add(x);stack.append(x)
    comps.append(c)
img=np.array(Image.open(root/'materials/brown_eye.png').convert('RGBA'))
result=[]
for i,c in enumerate(comps):
    ff=[f for f in faces if f[0][0] in c]
    vv=v[sorted(c)]; uu=uv[sorted({p[1] for f in ff for p in f})]
    pix=img[np.clip(((1-uu[:,1])*(img.shape[0]-1)).astype(int),0,img.shape[0]-1),np.clip((uu[:,0]*(img.shape[1]-1)).astype(int),0,img.shape[1]-1)]
    edges=Counter(tuple(sorted((a[0],b[0]))) for f in ff for a,b in zip(f,f[1:]+f[:1]))
    vol=0
    for f in ff:
        for j in range(1,len(f)-1):
            a,b,d=v[[f[0][0],f[j][0],f[j+1][0]]]
            vol+=np.dot(a,np.cross(b,d))/6
    result.append(dict(component=i,vertices=len(c),faces=len(ff),vertexRange=[min(c),max(c)],bbox=[vv.min(0).tolist(),vv.max(0).tolist()],mean=vv.mean(0).tolist(),uvBBox=[uu.min(0).tolist(),uu.max(0).tolist()],alphaSampleUnique=np.unique(pix[:,3]).tolist(),RGBSampleRange=[pix[:,:3].min(0).tolist(),pix[:,:3].max(0).tolist()],boundaryEdges=sum(x==1 for x in edges.values()),nonmanifoldEdges=sum(x>2 for x in edges.values()),signedVolume=vol))
print(json.dumps(dict(components=result,imageShape=list(img.shape),alphaPixels=dict(zip(map(str,np.unique(img[:,:,3])),map(int,np.unique(img[:,:,3],return_counts=True)[1])))),indent=2))
