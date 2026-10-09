"""Actual canonical forearm-positive triangle support defines cuff ownership."""
import json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def load_canonical(root,names):
    config=json.loads((root/'assets/blender/rider-rebuild/selected-ankle-field42/input.json').read_text())
    pins={k:config['sources'][k] for k in ['reference','canonicalFields','originalBody']}
    for row in pins.values():assert hashlib.sha256((root/row['path']).read_bytes()).hexdigest()==row['sha256']
    ref=np.load(root/pins['reference']['path']);key='RiderBody__FullAnatomyReference'
    native=ref[key+'_basis'];faces=ref[key+'_triangles'];source_ids=ref[key+'__SOURCE_VERTEX_ID']
    original=np.load(root/pins['originalBody']['path']);original_names=original['jointNames'].tolist()
    named=json.loads((root/pins['canonicalFields']['path']).read_text())
    fields=np.array([[row.get(name,0.) for name in names] for row in named])
    forearms={side:[i for i,n in enumerate(names) if n in ['DEF-forearm.'+side,'DEF-forearm.'+side+'.001']] for side in ['L','R']}
    support={side:np.any(fields[:,ids][faces]>0,axis=(1,2)) for side,ids in forearms.items()}
    rows=np.unique(faces[np.logical_or(support['L'],support['R'])])
    assert np.array_equal(native[rows],original['vertices'][source_ids[rows]])
    for i,name in enumerate(names):
        if name in original_names:assert np.array_equal(fields[rows,i],original['nativeCoefficients'][source_ids[rows],original_names.index(name)])
    p=native[:,[0,2,1]].copy();p[:,2]*=-1
    tree=BVHTree.FromPolygons(p.tolist(),faces.tolist(),all_triangles=True)
    def classify(points,side):
        ownership=np.zeros(len(points),bool);nearest=np.zeros(len(points),np.int32);distance=np.zeros(len(points));signed=np.zeros(len(points))
        for i,point in enumerate(points):
            q,n,face,d=tree.find_nearest(Vector(point));nearest[i]=face;distance[i]=d;signed[i]=float((point-np.asarray(q))@n)
            ownership[i]=support[side][face]
        return ownership,nearest,distance,signed
    return classify,{'sources':pins,'verifiedOriginalForearmSupportVertices':len(rows),
        'canonicalSupportTriangles':{side:int(rows.sum()) for side,rows in support.items()},
        'method':'Nearest actual canonical wearer triangle, whose original native field has positive ipsilateral forearm support on at least one corner. Exact wearer Basis and full fields verified on the whole triangle support. No tuned coordinate or angular threshold.'}
