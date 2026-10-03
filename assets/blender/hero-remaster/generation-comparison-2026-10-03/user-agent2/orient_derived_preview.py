"""Derived display orientation adapter; never edits source vertices or arrays."""
import hashlib
import numpy as np
import trimesh
from audit_native import audit

def orient_derived_preview(vertices, faces):
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
