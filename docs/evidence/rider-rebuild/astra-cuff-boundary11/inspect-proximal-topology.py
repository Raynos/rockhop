"""Read-only CPU2 cuff boundary audit. Writes a /tmp receipt, never meshes."""
import hashlib,json
from pathlib import Path
import numpy as np
root=Path('/Users/raynos/projects/games/rockhop')
path=root/'harness/out/rider-rebuild/glove-cuff-construction07/inspection01/guide-L.npz'
a=np.load(path);v=a['originalSourceXYZ'];faces=a['faces']

def cut_report(y,below):
    verts=list(v);cache={};out=[];owners=[]
    for fi,tri in enumerate(faces):
        polygon=[]
        for x,z in zip(tri,np.roll(tri,-1)):
            xin=(v[x,1]<y)==below;zin=(v[z,1]<y)==below
            if xin:polygon.append(int(x))
            if xin!=zin:
                key=tuple(sorted((int(x),int(z))))
                if key not in cache:
                    cache[key]=len(verts);t=(y-v[x,1])/(v[z,1]-v[x,1]);verts.append(v[x]+t*(v[z]-v[x]))
                polygon.append(cache[key])
        for j in range(1,len(polygon)-1):out.append([polygon[0],polygon[j],polygon[j+1]]);owners.append(fi)
    f=np.array(out);edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);edges,count=np.unique(edges,axis=0,return_counts=True)
    assert count.max()==2
    adjacency={int(x):[] for x in np.unique(f)}
    for x,z in edges:adjacency[x].append(z);adjacency[z].append(x)
    unseen=set(adjacency);components=[]
    while unseen:
        todo=[unseen.pop()];component=set(todo)
        while todo:
            for z in adjacency[todo.pop()]:
                if z in unseen:unseen.remove(z);component.add(z);todo.append(z)
        ids=np.array(sorted(component));em=np.isin(edges[:,0],ids);fm=np.isin(f[:,0],ids)
        boundary=edges[(count==1)&em];badj={int(x):[] for x in np.unique(boundary)}
        for x,z in boundary:badj[x].append(z);badj[z].append(x)
        assert all(len(x)==2 for x in badj.values())
        remaining=set(badj);loops=[]
        while remaining:
            start=min(remaining);loop=[];previous=None;node=start
            while node not in loop:
                loop.append(node);other=sorted(x for x in badj[node] if x!=previous)[0];previous,node=node,other
            assert node==start;remaining.difference_update(loop);loops.append(len(loop))
        chi=len(component)-int(em.sum())+int(fm.sum())
        components.append(dict(vertices=len(component),edges=int(em.sum()),triangles=int(fm.sum()),euler=chi,boundaryLoops=sorted(loops,reverse=True)))
    return dict(sourceY=y,side='proximal' if below else 'distal',components=components,originalFaceOwners=len(set(owners)))
reports=[cut_report(y,below) for y in [-.58,-.65] for below in [True,False]]
loop=a['section3_loop2_sourceEdges'];ids=np.unique(loop)
result={'acceptedArt':False,'source':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cuts':reports,'oldLipAnchors':a['oldLipAnchors'].tolist(),'oldLipSourceXYZ':v[a['oldLipAnchors']].tolist(),'smallSourceYMinus07Loop':{'sourceEdges':loop.tolist(),'sourceVertices':ids.tolist(),'sourceXYZBounds':[v[ids].min(0).tolist(),v[ids].max(0).tolist()]},'limits':['Read-only topology diagnosis; no saved cut or mesh.','Two boundary loops do not imply annulus: proximal Euler -2, genus one if orientable.','The 19-edge extra section is a localized inspection target, not a certified full handle selection.','No feature semantics, sleeve clearance, transfer, rig, or moving art acceptance.']}
Path('/tmp/astra-cuff-boundary11.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['cuts']))
