"""Read-only graph consequences of proposed face mask; no mesh cut or edit."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for key in ['preflight','boundary-context','out','evidence']:
        parser.add_argument('--'+key,required=True)
    args=parser.parse_args();p=json.loads(Path(args.preflight).read_text());assert sha(p['output']['path'])==p['output']['sha256'];m=np.load(p['output']['path']);source=np.load(p['source']['path']);assert sha(p['source']['path'])==p['source']['sha256'];assert np.array_equal(m['sourceXYZ'],source['vertices']) and np.array_equal(m['sourceFaces'],source['faces'])
    faces,vertices,remove=m['sourceFaces'],m['sourceXYZ'],m['faceRemoveCandidate'];edges={};neighbors=[[]for _ in faces]
    for row,face in enumerate(faces):
        for a,b in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:edges.setdefault(tuple(sorted([int(a),int(b)])),[]).append(row)
    assert all(len(rows)==2 for rows in edges.values())
    for edge,rows in edges.items():a,b=rows;neighbors[a].append(b);neighbors[b].append(a)
    remaining=set(np.flatnonzero(~remove).tolist());components=[]
    while remaining:
        stack=[min(remaining)];rows=[]
        while stack:
            row=stack.pop()
            if row not in remaining:continue
            remaining.remove(row);rows.append(row);stack.extend(n for n in neighbors[row]if n in remaining)
        components.append(sorted(rows))
    components.sort(key=lambda rows:-len(rows));labels=np.full(len(faces),-1,np.int32)
    for index,rows in enumerate(components):labels[rows]=index
    boundary=json.loads(Path(args.boundary_context).read_text());loop_reports=[]
    for loop in boundary['loops']:
        verts=loop['sourceVertexIds'];pairs=list(zip(verts,verts[1:]+verts[:1]));retained=[];masked=[]
        for a,b in pairs:
            rows=edges[tuple(sorted([a,b]))];assert int(remove[rows].sum())==1
            retained.append(next(row for row in rows if not remove[row]));masked.append(next(row for row in rows if remove[row]))
        loop_reports.append({'sourceVertexIds':verts,'edges':len(pairs),'meanSourceXYZ':loop['mean'],'retainedIncidentFaceRows':retained,'candidateIncidentFaceRows':masked,'retainedComponentIds':sorted(np.unique(labels[retained]).tolist())})
    tri=5167;assert not remove[tri];small=next(loop for loop in loop_reports if loop['edges']==3);assert set(small['sourceVertexIds'])==set(faces[tri].tolist());assert set(small['retainedIncidentFaceRows'])=={tri}
    normal=np.cross(vertices[faces[tri,1]]-vertices[faces[tri,0]],vertices[faces[tri,2]]-vertices[faces[tri,0]]);normal/=np.linalg.norm(normal)
    reports=[]
    for index,rows in enumerate(components):
        cf=faces[rows];ce=np.unique(np.sort(np.concatenate([cf[:,[0,1]],cf[:,[1,2]],cf[:,[2,0]]]),axis=1),axis=0);cv=np.unique(cf)
        reports.append({'componentId':index,'faceCount':len(rows),'vertexCount':len(cv),'edgeCount':len(ce),'eulerCharacteristic':int(len(cv)-len(ce)+len(rows)),'sourceFaceRows':rows if len(rows)<20 else None,'boundaryLoopEdgeCounts':[loop['edges']for loop in loop_reports if index in loop['retainedComponentIds']]})
    out=Path(args.out);assert not out.exists();out.mkdir(parents=True);raw=out/'graph-contract.npz';np.savez_compressed(raw,retainedFaceComponent=labels,sourceFaceRows=np.arange(len(faces)),sourceFaces=faces,sourceXYZ=vertices,proposedRemoveMask=remove)
    report={'accepted':False,'status':'READ_ONLY_HYPOTHETICAL_RETAINED_GRAPH_CLASSIFICATION','recipeSHA256':sha(__file__),'preflight':{'path':args.preflight,'sha256':sha(args.preflight)},'source':p['source'],'mask':p['output'],'components':reports,'boundaryLoops':loop_reports,'triangle5167':{'sourceVertexIds':faces[tri].tolist(),'meanSourceXYZ':vertices[faces[tri]].mean(0).tolist(),'geometricNormal':normal.tolist(),'originalNeighbors':neighbors[tri],'allOriginalNeighborsCandidateMasked':bool(remove[neighbors[tri]].all()),'cavityVisibleFromAnyFiveAnchors':bool(m['faceCavityVisible'][tri]),'externalVisibleFromAnyFiveViews':bool(m['faceExternalViewVisible'][tri]),'protectedDistal':bool(m['protectedDistalFaces'][tri]),'hypotheticalRetainedComponentId':int(labels[tri])},'raw':{'path':str(raw),'sha256':sha(raw)},'surfaceEdited':False,'limits':['Graph prediction of proposed mask only; no mesh cut/fit/skin/render.','An isolated retained triangle explains the secondary boundary but does not semantically authorize its removal or209 ambiguous exterior faces.','Graph topology alone does not identify source cavity/exterior, whole palm/finger enclosure, intended cuff rim or production acceptance.']}
    Path(args.evidence).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'components':reports,'triangleNeighbors':neighbors[tri]}))


if __name__=='__main__':main()
