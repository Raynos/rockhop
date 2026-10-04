"""Derived display orientation adapter; never edits source vertices or arrays."""
import hashlib
import numpy as np
import trimesh
from audit_native import audit

def orient_derived_preview(vertices, faces, bounded=False):
    if bounded:
        return _orient_bounded_patches(vertices,faces)
    v=np.array(vertices,copy=True); f=np.array(faces,copy=True)
    mesh=trimesh.Trimesh(vertices=v.copy(),faces=f.copy(),process=False)
    trimesh.repair.fix_normals(mesh,multibody=True)
    output=np.asarray(mesh.faces,dtype=f.dtype).copy()
    if not np.array_equal(mesh.vertices,v) or not np.array_equal(np.sort(output,axis=1),np.sort(f,axis=1)):
        raise ValueError('Orientation adapter changed geometric triangles')
    check=audit(v,output)
    return output, {'accepted':False,'adapter':'orientation of DERIVED display only',
        'verticesUnchanged':True,'samePerRowTriangleVertexSets':True,
        'flippedRows':int(np.count_nonzero(np.any(output!=f,axis=1))),
        'faceSetSHA256':hashlib.sha256(np.sort(f,axis=1).tobytes()).hexdigest(),
        'derivedAudit':check,'manifoldSharedEdgeOrientationConsistent':check['equalDirectionTwoFaceEdges']==0,
        'limits':['Nonmanifold/boundary geometry is not repaired','No smoothing, remesh, added/deleted triangles or native mutation',
                  'Open components have no guaranteed global inside/outside interpretation']}


def _orient_bounded_patches(vertices,faces):
    """Same adjacency/closed-volume basis with explicit contradiction gate.

    Parity graph runs in compiled SciPy rather than millions of NetworkX
    Python nodes. Nonmanifold edges create no orientation constraint.
    Open patches retain the first native face as sign anchor; closed patches
    use signed volume. Contradictory patches remain byte-identical.
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    v=np.asarray(vertices);f=np.asarray(faces)
    assert np.isfinite(v).all() and f.min()>=0 and f.max()<len(v)
    total=len(f);keys=np.empty(total*3,np.uint64);directions=np.empty(total*3,bool)
    owners=np.tile(np.arange(total,dtype=np.int32),3)
    for edge,(a,b) in enumerate(((0,1),(1,2),(2,0))):
        aa,bb=f[:,a],f[:,b];span=slice(edge*total,(edge+1)*total)
        keys[span]=np.minimum(aa,bb).astype(np.uint64)*len(v)+np.maximum(aa,bb).astype(np.uint64)
        directions[span]=aa<bb
    order=np.argsort(keys);keys=keys[order];directions=directions[order];owners=owners[order];del order
    starts=np.r_[0,np.flatnonzero(keys[1:]!=keys[:-1])+1]
    counts=np.diff(np.r_[starts,len(keys)]);two=starts[counts==2]
    aa,bb=owners[two],owners[two+1];parity=(directions[two]==directions[two+1]).astype(np.int32)
    boundary_face=np.zeros(total,bool);boundary_face[owners[starts[counts==1]]]=True
    nonmanifold_face=np.zeros(total,bool)
    nonmanifold_face[owners[np.repeat(counts>2,counts)]]=True
    rows=np.r_[aa*2,aa*2+1];cols=np.r_[bb*2+parity,bb*2+1-parity]
    graph=coo_matrix((np.ones(len(rows),np.uint8),(rows,cols)),shape=(total*2,total*2)).tocsr()
    _,labels=connected_components(graph,directed=False)
    del graph,rows,cols,keys,directions
    l0,l1=labels[::2],labels[1::2];contradiction=l0==l1
    patch_ids,patch=np.unique(np.minimum(l0,l1),return_inverse=True);number=len(patch_ids)
    anchors=np.full(number,total,np.int32);np.minimum.at(anchors,patch,np.arange(total,dtype=np.int32))
    flip=(l0>l1)&~contradiction;flip^=flip[anchors][patch]
    sizes=np.bincount(patch,minlength=number)
    boundary=np.bincount(patch,weights=boundary_face,minlength=number)>0
    nonmanifold=np.bincount(patch,weights=nonmanifold_face,minlength=number)>0
    contradictory=np.bincount(patch,weights=contradiction,minlength=number)>0
    closed=~(boundary|nonmanifold|contradictory)
    volumes=np.zeros(number,np.float64)
    for start in range(0,total,262144):
        end=min(start+262144,total);tri=v[f[start:end]].astype(np.float64)
        volume=np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2]))/6
        volume*=1-2*flip[start:end].astype(np.int8)
        volumes+=np.bincount(patch[start:end],weights=volume,minlength=number)
    tolerance=max(float(np.ptp(v,axis=0).max())**3,1e-30)*1e-12
    sign_ambiguous=closed&(abs(volumes)<=tolerance)
    outward_flip=closed&(volumes < -tolerance)
    flip^=outward_flip[patch];flip[contradiction]=False
    output=f.copy();output[flip]=output[flip,::-1]
    assert np.array_equal(np.sort(output,axis=1),np.sort(f,axis=1))
    original_same=parity.astype(bool);derived_same=original_same^flip[aa]^flip[bb]
    assert not derived_same[~contradiction[aa]].any()
    nonmanifold_incident_counts=np.bincount(patch,weights=nonmanifold_face,minlength=number).astype(np.int64)
    boundary_incident_counts=np.bincount(patch,weights=boundary_face,minlength=number).astype(np.int64)
    records={'facePatch':patch.astype(np.int32),'patchFaces':sizes,'patchAnchorFace':anchors,
             'patchBoundaryIncidentFaces':boundary_incident_counts,'patchNonmanifoldIncidentFaces':nonmanifold_incident_counts,
             'patchContradictory':contradictory,'patchClosed':closed,'patchSignAmbiguous':sign_ambiguous,
             'patchSignedVolumeBeforeOutwardChoice':volumes,'faceFlipped':flip}
    report={'accepted':False,'adapter':'OWNED derived orientation; bounded parity implementation of adjacency/closed-volume basis',
            'verticesUnchanged':True,'samePerRowTriangleVertexSets':True,'flippedRows':int(flip.sum()),
            'faceSetSHA256':hashlib.sha256(np.sort(f,axis=1).tobytes()).hexdigest(),
            'rawEqualDirectionTwoFaceEdges':int(original_same.sum()),'derivedEqualDirectionTwoFaceEdges':int(derived_same.sum()),
            'boundaryEdgesUnchanged':int((counts==1).sum()),'nonmanifoldEdgesUnchanged':int((counts>2).sum()),
            'manifoldAdjacencyPatches':number,'closedOrientablePatches':int(closed.sum()),
            'openOrNonmanifoldPatches':int((boundary|nonmanifold).sum()),
            'nonmanifoldIncidentFacesPreserved':int(nonmanifold_face.sum()),
            'contradictoryPatchesUnchanged':int(contradictory.sum()),'contradictoryFacesUnchanged':int(contradiction.sum()),
            'signAmbiguousClosedPatches':int(sign_ambiguous.sum()),'outwardVolumeChoices':int(outward_flip.sum()),
            'openSignBasis':'Smallest native face index in each manifold-adjacency patch retains original ordering; no global inside/outside claim',
            'closedSignBasis':'Positive signed volume only on orientable patches with no boundary/nonmanifold incident edge, absvolume above scale^3*1e-12; self-intersection not certified',
            'nonmanifoldPolicy':'No constraints cross >2-face edges; all faces/edges preserved; incident patches use native sign anchor and are explicitly non-global',
            'contradictionPolicy':'Every face in a contradictory manifold-adjacency patch retains original ordering',
            'limits':['No topology repair, cleanup, reduction, component deletion, recolor or vertex movement.',
                      'Open/nonmanifold/sign-ambiguous patches have no proven outward orientation.',
                      'Not whole-mesh intersection, fit, rig, CUDA or game-ready acceptance.']}
    return output,report,records
