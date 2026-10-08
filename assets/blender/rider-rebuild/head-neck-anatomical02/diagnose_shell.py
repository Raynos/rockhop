"""Pinned raw-source topology diagnostic, no Blender or geometry mutation.

Parent runs with CPU2 lease: python diagnose_shell.py FRESH_OUT.
Tests whether the nested cut rims come from UV-corresponding solidified layers.
"""
import collections
import hashlib
import json
import struct
import sys
from pathlib import Path
import numpy as np
DONOR=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb')
DIGEST='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
ROOT=Path(__file__).resolve().parents[4]

def main():
    out=Path(sys.argv[1]).resolve();assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/head-neck-anatomical02')
    raw=DONOR.read_bytes();assert hashlib.sha256(raw).hexdigest()==DIGEST
    size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    def accessor(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];w=np.dtype(dt).itemsize
        return np.ndarray((a['count'],n),dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*w),w)).copy()
    node=next(x for x in doc['nodes'] if x.get('name')=='textured');primitives=doc['meshes'][node['mesh']]['primitives']
    points=[];faces=[];uv=[];face_ids=[];parts=[];offset=0
    for part,p in enumerate(primitives):
        v=accessor(p['attributes']['POSITION']);f=accessor(p['indices']).reshape(-1,3);t=accessor(p['attributes']['TEXCOORD_0'])
        points.extend(v.tolist());faces.extend((f+offset).tolist());uv.extend(t[f].tolist());face_ids.extend((np.arange(len(f))+part*1000000).tolist());parts.extend([part]*len(f));offset+=len(v)
    rawpoints=np.array(points,dtype=np.float32);points,identity=np.unique(rawpoints,axis=0,return_inverse=True);faces=identity[np.array(faces)];uv=np.array(uv,dtype=np.float32)
    points=np.c_[-points[:,2],-(points[:,0]-.65),points[:,1]]*(1.78/1.8225715160369873)
    signature=collections.defaultdict(list)
    for i,tex in enumerate(uv):
        signature[tuple(sorted(tuple(float(x) for x in st) for st in tex))].append(i)
    multiplicity=collections.Counter(map(len,signature.values()));paired={i for indexes in signature.values() if len(indexes)==2 for i in indexes}
    # Graph only between exact UV-corresponding triangle faces. Source solidify
    # sidewall triangles have degenerate UVs, and are deliberately excluded.
    edges=collections.defaultdict(list)
    for i in paired:
        f=faces[i]
        for a,b in zip(f,np.roll(f,-1)):edges[tuple(sorted((int(a),int(b))))].append(i)
    graph=collections.defaultdict(set)
    for indexes in edges.values():
        for a in indexes:
            for b in indexes:
                if a!=b:graph[a].add(b)
    remaining=set(paired);components=[];membership=np.full(len(faces),-1,dtype=np.int32)
    while remaining:
        seed=remaining.pop();pending=[seed];comp=[seed]
        while pending:
            for b in graph[pending.pop()]:
                if b in remaining:remaining.remove(b);pending.append(b);comp.append(b)
        index=len(components);membership[comp]=index;tri=points[faces[comp]]
        # Centre-relative oriented volume makes the open patch statistic readable;
        # its sign alone does not authorize deleting small concave surface patches.
        centre=np.array([0.,-.015,1.66]);rel=tri-centre
        volume=float(np.sum(np.einsum('ij,ij->i',rel[:,0],np.cross(rel[:,1],rel[:,2])))/6)
        components.append({'index':index,'triangles':len(comp),'parts':dict(collections.Counter(int(parts[i]) for i in comp)),
            'bounds':[tri.min(axis=(0,1)).tolist(),tri.max(axis=(0,1)).tolist()],
            'centreRelativeOrientedVolume':volume,'minimumSourceFaceId':int(min(face_ids[i] for i in comp)),
            'maximumSourceFaceId':int(max(face_ids[i] for i in comp))})
    pairs=[]
    for indexes in signature.values():
        if len(indexes)!=2:continue
        a,b=indexes;ca=points[faces[a]].mean(0);cb=points[faces[b]].mean(0)
        pairs.append((a,b,float(np.linalg.norm(ca-cb)),int(membership[a]),int(membership[b])))
    pair_components=collections.Counter((min(a[3],a[4]),max(a[3],a[4])) for a in pairs)
    # Nonpaired triangles may be proper source material repairs, not all sidewalls.
    nonpaired=[]
    for part in range(len(primitives)):
        indexes=[i for i in range(len(faces)) if i not in paired and parts[i]==part]
        degenerate=0
        for i in indexes:
            a=uv[i,1]-uv[i,0];b=uv[i,2]-uv[i,0]
            degenerate+=abs(float(a[0]*b[1]-a[1]*b[0]))<1e-12
        nonpaired.append({'part':part,'triangles':len(indexes),'degenerateUVTriangles':degenerate})
    out.mkdir(parents=True)
    np.savez_compressed(out/'source-shell-map.npz',sourceFaceIds=np.array(face_ids),triangleComponent=membership,
        exactUVPairedFaceIndices=np.array(sorted(paired)),sourcePositions=points,sourceFaces=faces,
        pairRows=np.array(pairs),triangleCornerUV=uv)
    result={'accepted':False,'source':{'path':str(DONOR),'sha256':DIGEST},'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'sourceTriangles':len(faces),'exactUVSignatureMultiplicity':dict(multiplicity),
        'exactUVPairedTriangles':len(paired),'pairedSurfaceComponents':components,
        'componentPairCounts':{str(k):v for k,v in pair_components.items()},
        'pairedCentroidSeparationMetres':{'min':min(a[2] for a in pairs),'median':float(np.median([a[2] for a in pairs])),'max':max(a[2] for a in pairs)} if pairs else None,
        'nonpairedByPart':nonpaired,'limits':['Diagnostic only; no geometry modified.','Exact UV pairing plus connected layer and exposed crown evidence are needed before interior cleanup; a normal sign alone cannot delete the ear exterior.']}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
