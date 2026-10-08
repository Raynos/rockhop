"""Freeze six anatomically located compact Inflate brush edits on saved guides.

Sparse observed skin crossings set brush depth. No per-vertex wearer projection,
new global envelope, solver gain or unobserved source fit is introduced.
"""
import hashlib
import heapq
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
DATA=ROOT/'harness/out/rider-rebuild/glove-anatomical04/solved03'
PATCHES={
    'central-palmar-between-finger-bases':[379,382,409,487,488,489,642,643,652,653],
    'thumb-root-thenar':[317,321,322,685,686,692],
    'dorsal-small-spot':[579],
    'dorsal-cuff-small-spot':[446,519],
    'pinky-cap':[224,225,226,271,272,273,274,276,277,278,279,280,480],
    'ring-cap':[49,215,216,217,219,479],
}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def distances(vertices,faces,seeds):
    adjacency=[{} for _ in vertices]
    for face in faces:
        for a,b in zip(face,np.roll(face,-1)):
            length=float(np.linalg.norm(vertices[a]-vertices[b]))
            adjacency[a][int(b)]=length;adjacency[b][int(a)]=length
    d=np.full(len(vertices),np.inf);queue=[]
    for i in seeds:d[i]=0;heapq.heappush(queue,(0,int(i)))
    while queue:
        value,i=heapq.heappop(queue)
        if value!=d[i]:continue
        for j,length in adjacency[i].items():
            candidate=value+length
            if candidate<d[j]:d[j]=candidate;heapq.heappush(queue,(candidate,j))
    return d


def main():
    audit_path=ROOT/'docs/evidence/rider-rebuild/glove-anatomical04/local-residual-audit04.json'
    audit=json.loads(audit_path.read_text())
    right=np.load(DATA/'guide-R.npz')
    outside={r['wearerVertex']:r for r in audit['hands']['R']['outsideGuideVertices']}
    report={'acceptedArt':False,'operation':'FROZEN_SIX_LOCAL_ANATOMICAL_INFLATE_EDITS',
            'recipeSHA256':sha(__file__),'auditSHA256':sha(audit_path),
            'method':'Compact geodesic Inflate brush on actual saved selected guide; unchanged topology.',
            'falloffMeters':.012,'easeMeters':.003,'hands':{},
            'limits':['Local brush source is not wearing-fit or art acceptance.',
                      'No final appearance geometry is replaced; untouched dense selected UV/PBR follows existing binding.']}
    out=HERE/'local-controls04.json';assert not out.exists()
    for side in ('R','L'):
        path=DATA/f'guide-{side}.npz';actual=np.load(path)
        original=actual['vertices'].astype(np.float64);faces=actual['faces'];matrix=actual['objectMatrix']
        world=np.einsum('ij,kj->ik',original,matrix[:3,:3])+matrix[:3,3]
        cross=np.cross(world[faces[:,1]]-world[faces[:,0]],world[faces[:,2]]-world[faces[:,0]])
        face_normals=cross/np.linalg.norm(cross,axis=1)[:,None]
        normals=np.zeros_like(world)
        for corner in range(3):np.add.at(normals,faces[:,corner],cross)
        normals/=np.linalg.norm(normals,axis=1)[:,None]
        offsets=np.zeros_like(world);patches=[]
        for name,wearer_ids in PATCHES.items():
            # Exact shared selected guide indices carry mirrored anatomy; the
            # measured wearer ids only author the right patch footprint.
            face_ids=[outside[i]['face'] for i in wearer_ids]
            seeds=np.unique(right['faces'][face_ids].ravel())
            geodesic=distances(world,faces,seeds)
            t=np.clip(geodesic/report['falloffMeters'],0,1)
            weight=1-t*t*(3-2*t)
            rows=[r for r in audit['hands'][side]['outsideGuideVertices']
                  if geodesic[faces[r['face']]].min()<1e-10]
            assert rows,('No actual counterpart in explicit anatomical patch',side,name)
            needed=[]
            for row in rows:
                face=row['face'];brush_normal=normals[faces[face]].mean(0)
                incidence=float(np.dot(brush_normal,face_normals[face]))
                assert incidence>0
                needed.append((row['signedNormalDistance']+report['easeMeters'])/incidence)
            depth=max(needed)
            offsets+=normals*(depth*weight)[:,None]
            patches.append({'name':name,'observedRightWearerVertices':wearer_ids,
                            'originalSelectedGuideCoreVertices':seeds.tolist(),
                            'mode':'INFLATE','depthMeters':depth,
                            'actualOutsideCoreCount':len(rows),
                            'maximumMeasuredCoreCrossingMeters':max(r['signedNormalDistance'] for r in rows),
                            'supportedVertices':int(np.count_nonzero(weight)),
                            'falloffMeters':report['falloffMeters']})
        inverse=np.linalg.inv(matrix[:3,:3])
        local_offsets=np.einsum('ij,kj->ik',offsets,inverse)
        corrected=original+local_offsets
        areas=np.linalg.norm(np.cross(corrected[faces[:,1]]-corrected[faces[:,0]],
                                      corrected[faces[:,2]]-corrected[faces[:,0]]),axis=1)
        assert np.all(areas>np.finfo(np.float32).eps)
        offset_path=HERE/f'local-offsets04-{side}.npz';assert not offset_path.exists()
        np.savez_compressed(offset_path,original=original,offsets=local_offsets,corrected=corrected,faces=faces)
        report['hands'][side]={'actualGuide':{'path':str(path.relative_to(ROOT)),'sha256':sha(path)},
            'offsets':{'path':str(offset_path.relative_to(ROOT)),'sha256':sha(offset_path)},
            'patches':patches,'changedVertices':int(np.count_nonzero(np.linalg.norm(offsets,axis=1))),
            'unchangedVertices':int(np.count_nonzero(np.linalg.norm(offsets,axis=1)==0)),
            'maximumOffsetMeters':float(np.linalg.norm(offsets,axis=1).max()),
            'minimumCorrectedTriangleCrossSourceUnits':float(areas.min())}
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'controlsSHA256':sha(out),'hands':{s:{k:v for k,v in row.items() if k not in ('patches',)}
                                                       for s,row in report['hands'].items()}},indent=2))


if __name__=='__main__':main()
