"""Read-only cavity visibility mask; no source or candidate surface edit."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for key in ['source','source-sha256','branches','out','evidence']:
        parser.add_argument('--'+key,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);assert sha(args.source)==args.source_sha256
    out=Path(args.out);assert not out.exists();out.mkdir(parents=True);ev=Path(args.evidence);ev.mkdir(parents=True,exist_ok=True)
    source=np.load(args.source);vertices,faces=source['vertices'],source['faces'];branches=np.load(args.branches)['branchLabels'];triangles=vertices[faces];centers=triangles.mean(1)
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1),1e-30)[:,None]
    tree=BVHTree.FromPolygons([Vector(v)for v in vertices],faces.tolist(),all_triangles=True,epsilon=0)
    def visible(origin):
        rows=np.zeros(len(faces),bool)
        for i,center in enumerate(centers):
            delta=center-origin;distance=float(np.linalg.norm(delta));direction=delta/distance
            loc,n,index,hit_distance=tree.ray_cast(Vector(origin),Vector(direction),distance+1e-6)
            if index==i and abs(hit_distance-distance)<1e-5:rows[i]=True
        return rows
    # Anchors are inside both section loops at sourceY=-.655137.
    center=np.array([-.19893085956573486,-.655137,-.06397416442632675])
    anchors=[center+np.array([dx,0,dz])for dx,dz in [(0,0),(-.06,0),(.06,0),(0,-.06),(0,.06)]]
    cavity=np.stack([visible(origin)for origin in anchors])
    cavity_union=cavity.any(0)
    # Exterior visibility is an observation, not a complete exterior classifier.
    views=[np.array(p,float)for p in [(-3,.0,0),(3,.0,0),(0,.0,-3),(0,.0,3),(0,3,0)]]
    exterior=np.stack([visible(origin)for origin in views]);exterior_union=exterior.any(0)
    directed=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);edge,inv,count=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True,return_counts=True)
    incident=[[]for _ in edge]
    for i,e in enumerate(inv):incident[int(e)].append(i%len(faces))
    pairs=np.array([owners for owners in incident if len(owners)==2]);neighbors=[[]for _ in faces]
    for a,b in pairs:neighbors[a].append(int(b));neighbors[b].append(int(a))
    remaining=set(np.flatnonzero(cavity_union).tolist());components=[]
    while remaining:
        stack=[min(remaining)];region=[]
        while stack:
            current=stack.pop()
            if current not in remaining:continue
            remaining.remove(current);region.append(current)
            stack.extend(i for i in neighbors[current]if i in remaining)
        components.append(region)
    component_count=len(components);seed=6364;assert cavity_union[seed]
    mask=np.zeros(len(faces),bool)
    mask[next(region for region in components if seed in region)]=True
    # This is a proposed entire visible-connected interior, not an executed cut.
    conflict=mask&exterior_union
    protected_distal=(branches[faces]>0).any(1)
    roof_seed=np.flatnonzero(mask&(normals[:,1]<-.9))
    boundary=edge[(mask[pairs[:,0]]!=mask[pairs[:,1]])] if len(pairs)==len(edge) else np.empty((0,2),int)
    np.savez_compressed(out/'mask.npz',faceRemoveCandidate=mask,faceCavityVisible=cavity_union,faceExternalViewVisible=exterior_union,faceAmbiguousConflict=conflict,protectedDistalFaces=protected_distal,boundaryEdges=boundary,sourceFaces=faces,sourceXYZ=vertices,sourceTriangleRows=source['originalTriangleRows'],sourceBarycentric=source['barycentric'],sourceUV=source['uv'])
    report={'accepted':False,'status':'READ_ONLY_CUFF_REMOVAL_MASK_PREFLIGHT_NOT_EXECUTED','recipeSHA256':sha(__file__),'source':{'path':args.source,'sha256':sha(args.source)},'output':{'path':str(out/'mask.npz'),'sha256':sha(out/'mask.npz')},'anchors':np.array(anchors).tolist(),'externalViews':np.array(views).tolist(),'cavityVisibleFacesPerAnchor':cavity.sum(1).tolist(),'cavityVisibleUnionFaces':int(cavity_union.sum()),'visibleComponentCount':component_count,'roofSeedTriangle':seed,'connectedCandidateFaces':int(mask.sum()),'candidateExternalVisibilityConflicts':int(conflict.sum()),'candidateDistalProtectedOverlaps':int((mask&protected_distal).sum()),'boundaryEdges':len(boundary),'negativeAxialRoofFaces':len(roof_seed),'candidatesByNormal':{'negativeYBelowMinus09':len(roof_seed)},'removedFaces':0,'sourceEdited':False,'limits':['Mask is only the connected cavity-visible patch from five anchors; occluded interior lining may remain and external-view conflicts must be resolved.','External lateral/up visibility is an observation, not proof of true exterior classification; cuff-mouth views may see interior.','No cut, fit, velocity, skin, body/bind/map edit or wearable/cavity acceptance. Root must inspect preflight; uncertainty is a stop condition.']}
    (ev/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['connectedCandidateFaces','candidateExternalVisibilityConflicts','candidateDistalProtectedOverlaps','boundaryEdges']}))


if __name__=='__main__':main()
