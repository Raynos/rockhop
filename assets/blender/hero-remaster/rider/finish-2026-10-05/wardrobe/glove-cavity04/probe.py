"""Read-only source cuff/section topology and axial ray witnesses, no fitting."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sections(vertices, faces, station):
    points=[];links=[];lookup={}
    for triangle in faces:
        ids=[]
        for a,b in [(triangle[0],triangle[1]),(triangle[1],triangle[2]),(triangle[2],triangle[0])]:
            da,db=vertices[a,1]-station,vertices[b,1]-station
            if da*db<0:
                key=tuple(sorted([int(a),int(b)]))
                if key not in lookup:
                    lookup[key]=len(points)
                    points.append(vertices[a]+da/(da-db)*(vertices[b]-vertices[a]))
                ids.append(lookup[key])
        if len(ids)==2:links.append(ids)
        else:assert len(ids)==0
    adjacency={i:[]for i in range(len(points))}
    for a,b in links:adjacency[a].append(b);adjacency[b].append(a)
    assert all(len(v)==2 for v in adjacency.values())
    remaining=set(adjacency);loops=[]
    while remaining:
        first=min(remaining);ordered=[first];previous=-1;current=first
        while True:
            nxt=next(i for i in adjacency[current]if i!=previous)
            if nxt==first:break
            ordered.append(nxt);previous,current=current,nxt
        remaining.difference_update(ordered)
        xyz=np.array([points[i]for i in ordered]);xz=xyz[:,[0,2]]
        area=abs(float((xz[:,0]*np.roll(xz[:,1],-1)-xz[:,1]*np.roll(xz[:,0],-1)).sum()/2))
        loops.append({'points':len(xyz),'projectedAbsAreaSourceUnits2':area,'boundsXZ':[xz.min(0).tolist(),xz.max(0).tolist()],
                      'meanXZ':xz.mean(0).tolist(),'orderedXYZ':xyz.tolist()})
    return sorted(loops,key=lambda r:-r['projectedAbsAreaSourceUnits2'])


def axial_hits(vertices,faces,x,z):
    origin=np.array([x,-1.2,z]);direction=np.array([0.,1.,0.]);triangles=vertices[faces]
    edge1=triangles[:,1]-triangles[:,0];edge2=triangles[:,2]-triangles[:,0]
    h=np.cross(np.broadcast_to(direction,edge2.shape),edge2);det=(edge1*h).sum(1)
    active=abs(det)>1e-12;inv=np.zeros(len(det));inv[active]=1/det[active]
    delta=origin-triangles[:,0];u=(delta*h).sum(1)*inv;q=np.cross(delta,edge1)
    v=(q*direction).sum(1)*inv;t=(edge2*q).sum(1)*inv
    eligible=active&(u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)&(t>0)
    ids=np.flatnonzero(eligible);normals=np.cross(edge1,edge2);normals/=np.maximum(np.linalg.norm(normals,axis=1),1e-30)[:,None]
    rows=[]
    for i in ids[np.argsort(t[ids])]:
        if rows and abs(float(t[i])+origin[1]-rows[-1]['sourceY'])<1e-8:continue
        rows.append({'sourceY':float(t[i])+float(origin[1]),'triangleRow':int(i),'normalDotAxis':float(normals[i,1]),'barycentric':[float(1-u[i]-v[i]),float(u[i]),float(v[i])]})
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True);parser.add_argument('--semantics',required=True);parser.add_argument('--out',required=True);parser.add_argument('--evidence',required=True)
    args=parser.parse_args();out=Path(args.out);assert not out.exists();out.mkdir(parents=True);ev=Path(args.evidence);ev.mkdir(parents=True,exist_ok=True)
    source=np.load(args.source);vertices,faces=source['vertices'],source['faces']
    directed=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);edges,counts=np.unique(np.sort(directed,axis=1),axis=0,return_counts=True)
    oriented=np.sign(directed[:,1]-directed[:,0]);_,inverse=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True);balance=np.bincount(inverse,weights=oriented)
    adj=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(vertices),len(vertices)));component_count,_=connected_components(adj,directed=False)
    topology={'vertices':len(vertices),'usedVertices':len(np.unique(faces)),'triangles':len(faces),'uniqueEdges':len(edges),'eulerCharacteristic':int(len(np.unique(faces))-len(edges)+len(faces)),'components':component_count,'boundaryEdges':int((counts==1).sum()),'nonmanifoldEdges':int((counts>2).sum()),'inconsistentOrientedEdges':int((balance!=0).sum())}
    section_rows=[]
    for station in [-.985137,-.955137,-.905137,-.855137,-.805137,-.755137,-.705137,-.655137,-.605137,-.505137,-.405137,-.305137,-.205137,-.105137,.045137,.145137,.245137]:
        loops=sections(vertices,faces,station)
        section_rows.append({'sourceY':station,'loops':loops})
    center=np.array(json.loads(Path(args.semantics).read_text())['gloves']['coarsePalmRegistration']['R']['sourceWristCentre'])
    rays=[]
    for dx in [-.12,-.06,0,.06,.12]:
        for dz in [-.12,-.06,0,.06,.12]:
            x,z=float(center[0]+dx),float(center[2]+dz);rays.append({'sourceX':x,'sourceZ':z,'hits':axial_hits(vertices,faces,x,z)})
    raw=out/'sections-and-rays.json';raw.write_text(json.dumps({'sections':section_rows,'rays':rays},indent=2)+'\n')
    report={'accepted':False,'status':'READ_ONLY_DONOR_CUFF_TOPOLOGY_AND_RAY_WITNESSES','recipeSHA256':sha(__file__),'source':{'path':args.source,'sha256':sha(args.source)},'topology':topology,'sections':[{'sourceY':r['sourceY'],'loopCount':len(r['loops']),'loops':[{k:v for k,v in row.items()if k!='orderedXYZ'}for row in r['loops']]}for r in section_rows],'axialRays':rays,'raw':{'path':str(raw),'sha256':sha(raw)},'limits':['Plane section loops and positive-axis rays only; no global cavity/solid occupancy or canonical-forearm admission proof.','A closed manifold can have a cavity opening despite zero boundary edges. Genus/orientation and loop/ray transitions are diagnostic evidence, not art acceptance.','Source untouched; no cutting, fitting, velocity, skin, body, bind, map, model or render execution.']}
    (ev/'probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'topology':topology,'sections':[(r['sourceY'],len(r['loops']))for r in section_rows],'centerRay':rays[12]}))


if __name__=='__main__':main()
