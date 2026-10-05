"""Read-only proposed mask combinatorics and dense corner-UV ancestry."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for key in ['preflight','dense','evidence']:
        parser.add_argument('--'+key,required=True)
    args=parser.parse_args();p=json.loads(Path(args.preflight).read_text());assert sha(p['output']['path'])==p['output']['sha256'];m=np.load(p['output']['path']);dense=np.load(args.dense)
    lookup={int(row):index for index,row in enumerate(dense['originalTriangleRows'])}
    rows=np.array([lookup[int(row)]for row in m['sourceTriangleRows']]);bary=m['sourceBarycentric'];triangles=dense['vertices'][dense['faces'][rows]]
    reconstructed=(triangles*bary[:,:,None]).sum(1);uv=(dense['originalCornerUV'][rows]*bary[:,:,None]).sum(1)
    xyz_error=float(np.linalg.norm(reconstructed-m['sourceXYZ'],axis=1).max());uv_error=float(abs(uv-m['sourceUV']).max())
    assert xyz_error<1e-12 and uv_error<1e-12
    boundary=m['boundaryEdges'];degrees=np.bincount(boundary.ravel(),minlength=len(m['sourceXYZ']));active=np.flatnonzero(degrees);neighbors={int(i):[]for i in active}
    for a,b in boundary:neighbors[int(a)].append(int(b));neighbors[int(b)].append(int(a))
    remaining=set(neighbors);components=[]
    while remaining:
        stack=[min(remaining)];region=[]
        while stack:
            i=stack.pop()
            if i not in remaining:continue
            remaining.remove(i);region.append(i);stack.extend(j for j in neighbors[i]if j in remaining)
        components.append(region)
    remove=m['faceRemoveCandidate'];faces=m['sourceFaces'];kept_faces=faces[~remove]
    kept_rows=np.flatnonzero(~remove);kept_vertices=np.unique(kept_faces)
    npz_path=Path(p['output']['path']).with_name('boundary-and-lineage-contract.npz')
    np.savez_compressed(npz_path,retainedFaceRows=kept_rows,retainedVertexRows=kept_vertices,removedFaceRows=np.flatnonzero(remove),boundaryEdges=boundary,denseTriangleRows=rows,barycentric=bary,sourceCornerProjectedUV=uv)
    report={'accepted':False,'status':'PROPOSED_MASK_BOUNDARY_AND_UV_LINEAGE_READBACK_ONLY','preflightSHA256':sha(args.preflight),'dense':{'path':args.dense,'sha256':sha(args.dense)},'sourceReconstructionMaxError':xyz_error,'sourceCornerUVProjectionMaxError':uv_error,'boundaryVertices':len(active),'boundaryComponents':len(components),'boundaryDegreeNotTwoVertices':int((degrees[active]!=2).sum()),'boundaryComponentVertexCounts':[len(x)for x in components],'retainedFaceRows':len(kept_rows),'candidateRemoveFaces':int(remove.sum()),'candidateDistalFaceOverlaps':int((remove&m['protectedDistalFaces']).sum()),'candidateExteriorVisibilityConflicts':int(m['faceAmbiguousConflict'].sum()),'lineageContract':{'path':str(npz_path),'sha256':sha(npz_path)},'surfaceEdited':False,'limits':['This is combinatorial prediction only; no mesh has been cut. Visibility conflicts and incomplete interior coverage can reject the mask independently of regular boundaries.','Per-vertex original triangle/barycentric corner-UV projection is exact but may alias original UV seams; final production corner-UV baking/authoring remains required.','All retained source rows/coordinates can remain exact under face-only removal, but that does not prove semantic exterior preservation or whole palm/finger enclosure.']}
    Path(args.evidence).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['boundaryComponents','boundaryDegreeNotTwoVertices','candidateRemoveFaces','candidateExteriorVisibilityConflicts','candidateDistalFaceOverlaps']}))


if __name__=='__main__':main()
