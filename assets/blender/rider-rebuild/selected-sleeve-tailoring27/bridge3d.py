"""Preserve two actual directed rings while sewing a nonplanar annular strip.

No caps, boundary movement, point deletion, or planar projection. This helper
requires actual subsequent dense self/body/garment checks; it claims topology
only, never a physical or visual pass.
"""
from collections import defaultdict
import numpy as np


def ring(surgery, edges):
    world=np.asarray(surgery.world);ids=sorted({v for _,_,a,b in edges for v in (a,b)})
    _,groups=np.unique(np.round(world[ids],9),axis=0,return_inverse=True)
    group=dict(zip(ids,map(int,groups)));representative={};following={};uv={};material={}
    for vertex,g in group.items():representative.setdefault(g,vertex)
    for face,corner,a,b in edges:
        x,y=group[a],group[b]
        assert x!=y and x not in following, 'Boundary must be one consistently directed ring'
        following[x]=y;uv[x]=np.array(surgery.uv[face][corner]);material[x]=surgery.material[face]
    assert set(following)==set(following.values())
    first=min(following);chain=[first];at=following[first]
    while at!=first:
        assert at not in chain;chain.append(at);at=following[at]
    assert len(chain)==len(following), 'Multiple circuits require separate explicit ownership'
    return [representative[g] for g in chain],{representative[g]:uv[g] for g in chain},{representative[g]:material[g] for g in chain}


def zipper(a,b,world):
    """a is reverse existing winding; b retains existing winding."""
    # A closest actual 3D pair fixes phase; arc length controls triangulation,
    # not a radial chart or assumed concentric ring.
    distance=np.sum((world[a][:,None]-world[b][None,:])**2,axis=2)
    i,j=np.unravel_index(np.argmin(distance),distance.shape)
    a=a[i:]+a[:i];b=b[j:]+b[:j]
    def stations(ids):
        length=np.linalg.norm(world[np.roll(ids,-1)]-world[ids],axis=1)
        assert np.all(length>0)
        return np.r_[0,np.cumsum(length)]/length.sum()
    sa,sb=stations(a),stations(b);i=j=0;faces=[]
    while i<len(a) or j<len(b):
        if j==len(b) or (i<len(a) and sa[i+1]<=sb[j+1]):
            faces.append([a[i%len(a)],a[(i+1)%len(a)],b[j%len(b)]]);i+=1
        else:
            faces.append([a[i%len(a)],b[(j+1)%len(b)],b[j%len(b)]]);j+=1
    return faces


def bridge(surgery, first_edges, second_edges):
    a,au,am=ring(surgery,first_edges);b,bu,bm=ring(surgery,second_edges)
    world=np.asarray(surgery.world);faces=zipper(a[::-1],b,world);f=np.asarray(faces)
    area=np.linalg.norm(np.cross(world[f[:,1]]-world[f[:,0]],world[f[:,2]]-world[f[:,0]]),axis=1)
    assert np.all(area>1e-14), ('Degenerate authored annulus',float(area.min()))
    incidence=defaultdict(list)
    for face in faces:
        for x,y in zip(face,face[1:]+face[:1]):incidence[tuple(sorted((x,y)))].append((x,y))
    expected={tuple(sorted((x,y))):(y,x) for loop in (a,b) for x,y in zip(loop,loop[1:]+loop[:1])}
    actual={key:rows[0] for key,rows in incidence.items() if len(rows)==1}
    assert actual==expected, 'Every sewn boundary edge must oppose its source half edge'
    assert all(len(rows)==1 or (len(rows)==2 and rows[0]==rows[1][::-1]) for rows in incidence.values())
    assert len(set(f.ravel()))-len(incidence)+len(faces)==0
    uv={**au,**bu};materials={**am,**bm}
    for face in faces:surgery.add_face(face,[uv[v] for v in face],materials[face[0]])
    return dict(boundaryVertices=[len(a),len(b)],newFaces=len(faces),sewn=True,
                bothBoundaryLoopsPreserved=True,actualVerticesMoved=False,
                eulerCharacteristic=0,minimumDoubleTriangleAreaM2=float(area.min()),
                physicalAndMovingGatesPassed=False)
