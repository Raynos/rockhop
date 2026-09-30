"""Sew actual simple boundary loops; never close arbitrary visual overlaps."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
if (out/'scaffold.npz').exists():raise RuntimeError('Frozen output exists')
p=np.load(a.input);v=p['vertices'].astype(np.float64);f=p['faces']
def edge_data(faces):
    directed=np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]))
    e,first,inv,c=np.unique(np.sort(directed,axis=1),axis=0,
                          return_index=True,return_inverse=True,return_counts=True)
    return e,first,inv,c,directed
e,first,inv,c,directed=edge_data(f)
area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
remove=set()
for eid in np.flatnonzero(c>2):
    fs=np.flatnonzero(inv==eid)%len(f)
    keep=fs[np.argsort(area[fs])[-2:]]
    remove.update(int(x) for x in fs if x not in keep)
f=f[[i not in remove for i in range(len(f))]]
e,first,inv,c,directed=edge_data(f)
boundary=e[c==1]; orient=directed[first[c==1]]
neighbors={}
for x,y in boundary:
    neighbors.setdefault(int(x),[]).append(int(y))
    neighbors.setdefault(int(y),[]).append(int(x))
seen=set();loops=[];skipped=[]
for start in neighbors:
    if start in seen:continue
    component=set();todo=[start]
    while todo:
        x=todo.pop()
        if x in component:continue
        component.add(x);todo.extend(neighbors[x])
    seen.update(component)
    if len(component)>128 or any(len(neighbors[x])!=2 for x in component):
        skipped.append(dict(vertices=len(component),degreeTwo=all(len(neighbors[x])==2 for x in component)))
        continue
    order=[start];previous=None;current=start
    while True:
        nxt=next(x for x in neighbors[current] if x!=previous)
        if nxt==start:break
        order.append(nxt);previous,current=current,nxt
    loops.append(order)
new_vertices=[];new_faces=[]
lookup={tuple(sorted(x)):tuple(x) for x in orient}
for loop in loops:
    index=len(v)+len(new_vertices);new_vertices.append(v[loop].mean(axis=0))
    for i,x in enumerate(loop):
        y=loop[(i+1)%len(loop)];aa,bb=lookup[tuple(sorted((x,y)))]
        new_faces.append((bb,aa,index))
if new_vertices:v=np.vstack((v,new_vertices));f=np.vstack((f,new_faces))
e,first,inv,c,directed=edge_data(f)
np.savez(out/'scaffold.npz',vertices=v.astype(np.float32),faces=f.astype(np.int32))
report=dict(status='UNACCEPTED scaffold topology preflight',vertices=len(v),faces=len(f),
            nonmanifoldFacesRemoved=len(remove),simpleLoopsSewn=len(loops),
            skippedBoundaryComponents=skipped,boundaryEdges=int(np.sum(c==1)),
            nonmanifoldEdges=int(np.sum(c>2)),sourceSHA256=hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),
            scriptSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            limits=['Small fan fills can alter local creases; anatomy requires gray review.',
                    'Source scaffold is not dense original; source files untouched.'])
(out/'finalize-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
