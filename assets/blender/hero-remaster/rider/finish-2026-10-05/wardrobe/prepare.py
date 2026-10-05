"""Immutable source extraction, explicit cleanup, bake correspondence prototypes.

Run with the installed Hunyuan Python under the canonical non-evicting guard.
No inference, source edits, assembled rider, skeleton or production promotion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image
import pymeshlab
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from trimesh.triangles import closest_point, points_to_barycentric

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path), 'bytes': Path(path).stat().st_size, 'sha256': sha(path)}


def read_glb(path, out):
    payload = path.read_bytes()
    magic, version, total = struct.unpack_from('<III', payload)
    assert magic == 0x46546c67 and version == 2 and total == len(payload)
    n, kind = struct.unpack_from('<II', payload, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(payload[20:20+n])
    at = 20+n
    length, kind = struct.unpack_from('<II', payload, at)
    assert kind == 0x004e4942
    binary = payload[at+8:at+8+length]
    assert len(doc['meshes']) == 1 and len(doc['meshes'][0]['primitives']) == 1
    for node in doc['nodes']:
        assert not any(k in node for k in ('translation', 'rotation', 'scale'))
        assert np.array_equal(np.array(node.get('matrix', np.eye(4).ravel())), np.eye(4).ravel())

    def accessor(index):
        a = doc['accessors'][index]
        b = doc['bufferViews'][a['bufferView']]
        dtype = {5126:'<f4', 5125:'<u4', 5123:'<u2'}[a['componentType']]
        cols = {'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        item = np.dtype(dtype).itemsize
        return np.ndarray((a['count'],cols), dtype=dtype, buffer=binary,
                          offset=b.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(b.get('byteStride',item*cols),item)).copy()

    p = doc['meshes'][0]['primitives'][0]
    assert p.get('mode',4) == 4
    arrays = {k:accessor(a) for k,a in p['attributes'].items()}
    arrays['faces'] = accessor(p['indices']).reshape(-1,3)
    pbr = doc['materials'][p['material']]['pbrMetallicRoughness']
    textures = {}
    for name in ('baseColorTexture','metallicRoughnessTexture'):
        image = doc['images'][doc['textures'][pbr[name]['index']]['source']]
        view = doc['bufferViews'][image['bufferView']]
        suffix = {'image/png':'.png','image/jpeg':'.jpg'}[image['mimeType']]
        target = out / (name+suffix)
        begin = view.get('byteOffset',0)
        target.write_bytes(binary[begin:begin+view['byteLength']])
        textures[name] = {**pin(target), 'size':list(Image.open(target).size), 'byteExactEmbeddedExtraction':True}
    return arrays, textures, pbr


def cleanup(arrays):
    v, f = arrays['POSITION'], arrays['faces'].astype(np.int64)
    welded, first, inverse = np.unique(v, axis=0, return_index=True, return_inverse=True)
    wf = inverse[f]
    area2 = np.linalg.norm(np.cross(welded[wf[:,1]]-welded[wf[:,0]],
                                    welded[wf[:,2]]-welded[wf[:,0]]),axis=1)
    keep = area2 > 0
    valid_rows = np.flatnonzero(keep)
    graph = coo_matrix((np.ones(3*len(valid_rows),np.uint8),
                       (wf[keep].ravel(),np.roll(wf[keep],1,axis=1).ravel())),
                      shape=(len(welded),len(welded))).tocsr()
    count, labels = connected_components(graph,directed=False)
    sizes = np.bincount(labels[wf[keep,0]],minlength=count)
    largest = sizes.argmax()
    main_rows = valid_rows[labels[wf[keep,0]] == largest]
    ordered = np.sort(wf[main_rows],axis=1)
    _, unique_rows = np.unique(ordered,axis=0,return_index=True)
    selected = main_rows[np.sort(unique_rows)]
    used, cleanfaces = np.unique(wf[selected].ravel(),return_inverse=True)
    report = {'sourceVertices':len(v),'sourceFaces':len(f),'exactWeldedVertices':len(welded),
              'exactZeroAreaRowsRemoved':int((~keep).sum()),
              'detachedNondegenerateRowsRemoved':len(valid_rows)-len(main_rows),
              'duplicateUnorientedRowsRemoved':len(main_rows)-len(selected),
              'componentFacesDescending':[int(i) for i in sorted(sizes[sizes>0],reverse=True)],
              'remainingVertices':len(used),'remainingFaces':len(selected),
              'sourcePositionDisplacement':0,'sourceRetainedTriangleRowsExact':True,
              'weldSemantics':'Exact float32 POSITION equality; UVs remain original per-corner, no texture weld',
              'limits':['Largest component only is an explicit donor derivative, not wearable topology acceptance.',
                        'No self-intersection repair, winding repair, garment openings, body fit or rig changes.']}
    return welded[used], cleanfaces.reshape(-1,3), selected, report


def correspondence(points, vertices, faces, rows):
    triangles = vertices[faces].astype(np.float64)
    tree = cKDTree(triangles.mean(axis=1))
    chosen, barys, gaps = [],[],[]
    for start in range(0,len(points),512):
        batch = points[start:start+512].astype(np.float64)
        _, ids = tree.query(batch,k=min(32,len(triangles)))
        candidates = triangles[ids].reshape(-1,3,3)
        repeated = np.repeat(batch,ids.shape[1],axis=0)
        nearest = closest_point(candidates,repeated).reshape(len(batch),-1,3)
        squared = ((nearest-batch[:,None,:])**2).sum(axis=2)
        best = squared.argmin(axis=1)
        take = ids[np.arange(len(batch)),best]
        surface = nearest[np.arange(len(batch)),best]
        chosen.append(rows[take])
        barys.append(points_to_barycentric(triangles[take],surface))
        gaps.append(np.sqrt(squared[np.arange(len(batch)),best]))
    return np.concatenate(chosen),np.concatenate(barys),np.concatenate(gaps)


def write_obj(path, vertices, faces, corner_uv, maps):
    mtl = path.with_suffix('.mtl')
    mtl.write_text('newmtl original_source\nKd 1 1 1\nmap_Kd baseColorTexture.png\n')
    with path.open('w') as fp:
        fp.write('# Unaccepted donor prototype; original glTF UV y flipped for OBJ\nmtllib '+mtl.name+'\nusemtl original_source\n')
        for x,y,z in vertices: fp.write(f'v {x:.9g} {y:.9g} {z:.9g}\n')
        for u,v in corner_uv.reshape(-1,2): fp.write(f'vt {u:.9g} {1-v:.9g}\n')
        for i,(a,b,c) in enumerate(faces): fp.write(f'f {a+1}/{3*i+1} {b+1}/{3*i+2} {c+1}/{3*i+3}\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-verification',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--evidence',required=True)
    args=parser.parse_args()
    out,evidence=Path(args.out),Path(args.evidence)
    assert not out.exists(), 'Fresh output required'
    out.mkdir(parents=True)
    evidence.mkdir(parents=True,exist_ok=True)
    items=[]
    for source in json.loads(Path(args.source_verification).read_text())['sources']:
        name=source['name']; dest=out/name;dest.mkdir()
        original=Path(source['path'])
        assert sha(original)==source['sha256']
        arrays,textures,pbr=read_glb(original,dest)
        v,f,rows,clean=cleanup(arrays)
        normal_policy='Original NORMAL attribute preserved'
        if 'NORMAL' not in arrays:
            all_v,inv=np.unique(arrays['POSITION'],axis=0,return_inverse=True)
            all_f=inv[arrays['faces']]
            face_n=np.cross(all_v[all_f[:,1]]-all_v[all_f[:,0]],all_v[all_f[:,2]]-all_v[all_f[:,0]])
            accum=np.zeros_like(all_v)
            for corner in range(3): np.add.at(accum,all_f[:,corner],face_n)
            accum/=np.maximum(np.linalg.norm(accum,axis=1),1e-15)[:,None]
            arrays['NORMAL']=accum[inv]
            normal_policy='Source declares no NORMAL; explicit derived area-weighted exact-position welded normals, not original normal data'
        native=dest/'cleaned-donor.npz'
        np.savez_compressed(native,vertices=v,faces=f,originalTriangleRows=rows,
                            originalCornerUV=arrays['TEXCOORD_0'][arrays['faces'][rows]],
                            donorCornerNormals=arrays['NORMAL'][arrays['faces'][rows]])
        ms=pymeshlab.MeshSet()
        ms.add_mesh(pymeshlab.Mesh(v.astype(np.float64),f.astype(np.int32)))
        target={'hoodie':20000,'jeans':16000,'gloves':16000,'boots':10000}[name]
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=target,preserveboundary=True,
              preservenormal=True,preservetopology=True,optimalplacement=False,autoclean=True)
        proxy=ms.current_mesh();pv,pf=proxy.vertex_matrix(),proxy.face_matrix()
        original_rows,barys,dist=correspondence(pv,v,f,rows)
        source_faces=arrays['faces'][original_rows]
        mapped_uv=(arrays['TEXCOORD_0'][source_faces]*barys[:,:,None]).sum(axis=1)
        mapped_normals=(arrays['NORMAL'][source_faces]*barys[:,:,None]).sum(axis=1)
        lengths=np.linalg.norm(mapped_normals,axis=1);mapped_normals/=np.maximum(lengths,1e-15)[:,None]
        proxyfile=dest/'retopology-prototype.npz'
        np.savez_compressed(proxyfile,vertices=pv,faces=pf,uv=mapped_uv,normals=mapped_normals,
                            originalTriangleRows=original_rows,barycentric=barys,
                            projectionDistances=dist)
        obj=dest/'retopology-prototype.obj'
        write_obj(obj,pv,pf,mapped_uv[pf],textures)
        # Original-to-canonical Blender basis only: source+Zfront -> Blender+Xfront,
        # source+Yup -> Blender+Zup; source+X -> Blender+Y. Determinant +1.
        basis=[[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]]
        result={'item':name,'accepted':False,'status':'SOURCE_CLEANUP_AND_BAKE_INPUT_READY_UNACCEPTED',
                'source':pin(original),'sourceBounds':np.array([v.min(0),v.max(0)]).tolist(),
                'sourceDimensions':np.ptp(v,axis=0).tolist(),
                'axes':'Source+Yup; source+Zfront from fixed original orbit; boot toe points -X, not source+Z.',
                'units':'Uncalibrated generation units; body fitting scale requires canonical landmarks',
                'sourceFrontToBlenderBasisOnly':basis,'cleanup':clean,
                'cleanedDonor':pin(native),'maps':textures,'originalPBR':pbr,'normalPolicy':normal_policy,
                'prototype':{'npz':pin(proxyfile),'obj':pin(obj),'vertices':len(pv),'faces':len(pf),
                 'targetFaces':target,'method':'Position-preserving quadric edge collapse; protected topology/normals/boundary',
                 'sourceFaceRows':True,'sourceBarycentric':True,'sourceProjectionMax':float(dist.max()),
                 'sourceProjectionP95':float(np.quantile(dist,.95)),
                 'limits':['Prototype lacks authored joint loops, inner clearance, skin, contact and visual acceptance.',
                           'Per-vertex UV projection can cross original UV seams; original-corner donor is authoritative for final bake.',
                           'Nearest32 source centroid candidate search is not a global closest-surface certificate.']},
                'sourceStillImmutable':sha(original)==source['sha256']}
        (evidence/(name+'-source.json')).write_text(json.dumps(result,indent=2)+'\n')
        items.append(result)
        print(json.dumps({'item':name,'cleanFaces':len(f),'prototypeFaces':len(pf),'maxProjection':float(dist.max())}),flush=True)
    package={'accepted':False,'recipe':pin(Path(__file__)),'sourceVerification':pin(Path(args.source_verification)),
             'items':items,'limits':'Source-space cleanup/bake inputs only; one native author fits production wardrobe/rig.'}
    (evidence/'prep01.json').write_text(json.dumps(package,indent=2)+'\n')


if __name__=='__main__': main()
