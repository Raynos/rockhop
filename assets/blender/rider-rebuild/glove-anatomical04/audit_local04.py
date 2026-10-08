"""Bounded actual saved guide/wearer residual and local ownership audit."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def closest(points, vertices, faces):
    """Exact closest guide triangle, with barycentric face/edge candidates."""
    tri = vertices[faces].astype(np.float64)
    a, b, c = (tri[:, i] for i in range(3))
    ab, ac = b-a, c-a
    normal = np.cross(ab, ac)
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    d00, d01, d11 = (np.einsum('ij,ij->i', x, y) for x, y in ((ab, ab), (ab, ac), (ac, ac)))
    denominator = d00*d11-d01*d01
    rows = []
    for p in points:
        ap = p-a
        d20, d21 = np.einsum('ij,ij->i', ap, ab), np.einsum('ij,ij->i', ap, ac)
        v, w = (d11*d20-d01*d21)/denominator, (d00*d21-d01*d20)/denominator
        q = a+v[:, None]*ab+w[:, None]*ac
        valid = (v >= 0) & (w >= 0) & (v+w <= 1)
        distance = np.einsum('ij,ij->i', q-p, q-p)
        distance[~valid] = np.inf
        for start, end in ((a,b),(b,c),(c,a)):
            edge=end-start
            t=np.clip(np.einsum('ij,ij->i',p-start,edge)/np.einsum('ij,ij->i',edge,edge),0,1)
            candidate=start+t[:,None]*edge
            d=np.einsum('ij,ij->i',candidate-p,candidate-p)
            replace=d<distance; q[replace]=candidate[replace]; distance[replace]=d[replace]
        face=int(np.argmin(distance))
        rows.append({'face':face,'point':q[face].tolist(),
                     'distance':float(np.sqrt(distance[face])),
                     'signedNormalDistance':float(np.dot(p-q[face],normal[face]))})
    return rows


def main():
    control=json.loads((HERE/'controls-orientation02.json').read_text())
    frozen=json.loads((HERE/'guide-controls02.json').read_text())
    original=np.load(ROOT/frozen['selectedGuide']['path'])['vertices']
    report={'acceptedArt':False,'operation':'READ_ONLY_ACTUAL_LOCAL_RESIDUAL_OWNERSHIP_AUDIT',
            'recipeSHA256':sha(__file__),'hands':{},'sourceHandleTargetsChanged':0}
    for side in ('R','L'):
        path=ROOT/f'harness/out/rider-rebuild/glove-anatomical04/solved03/guide-{side}.npz'
        actual=np.load(path); matrix=actual['objectMatrix']; v=actual['vertices']
        world=np.einsum('ij,kj->ik',v,matrix[:3,:3])+matrix[:3,3]
        hand=np.load(ROOT/control['pins']['hand'+side]['path'])
        nearest=closest(hand['vertices'],world,actual['faces'])
        names=hand['jointNames'].tolist(); weights=hand['nativeCoefficients']
        digit_masses=np.stack([weights[:,[i for i,n in enumerate(names) if n.endswith('.'+side) and
                           n.startswith('DEF-'+stem+'.')]].sum(1)
                    for stem in ('f_pinky','f_ring','f_middle','f_index','thumb')],axis=1)
        palm=weights[:,[i for i,n in enumerate(names) if n.endswith('.'+side) and
                      (n.startswith('DEF-hand.') or n.startswith('DEF-palm.'))]].sum(1)
        labels=np.argmax(digit_masses,axis=1); labels[np.max(digit_masses,axis=1)<palm]=-1
        outside=[]
        for i,row in enumerate(nearest):
            if row['signedNormalDistance'] > 0:
                outside.append({'wearerVertex':i,'domain':int(labels[i]),'palmMass':float(palm[i]),
                                'digitMass':digit_masses[i].tolist(),**row})
        handles=[]
        for h in frozen['hands'][side]['handles']:
            achieved=world[h['guideVertex']]
            delta=np.asarray(h['targetWorld'])-achieved
            handles.append({'label':h['label'],'guideVertex':h['guideVertex'],
                            'originalSelectedSourceVertex':h['selectedSourceVertex'],
                            'originalGuideSourcePosition':original[h['guideVertex']].tolist(),
                            'achievedWorld':achieved.tolist(),'targetWorld':h['targetWorld'],
                            'deltaWorld':delta.tolist(),'residualMeters':float(np.linalg.norm(delta))})
        report['hands'][side]={'guideArraySHA256':sha(path),'outsideGuideVertices':outside,
                             'outsideCount':len(outside),'handles':handles}
        print(side,'outside',len(outside),'max',max((r['signedNormalDistance'] for r in outside),default=0),
              'domains',{str(i):sum(r['domain']==i for r in outside) for i in range(-1,5)})
        print('largest handles',[(h['label'],round(h['residualMeters'],5)) for h in
                                sorted(handles,key=lambda h:h['residualMeters'],reverse=True)[:15]])
    out=ROOT/'docs/evidence/rider-rebuild/glove-anatomical04/local-residual-audit04.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('audit',sha(out))


if __name__=='__main__': main()
