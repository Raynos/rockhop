"""Read-only exact actual dense palm crossing and source ownership receipt."""
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    helper=HERE/'audit_local04.py'
    assert sha(helper)=='3712983b0c5b1783035a77eddb6af331767046bf08fb7643c9bc86e150a453e5'
    control=json.loads((HERE/'controls-orientation02.json').read_text())
    frozen=json.loads((HERE/'guide-controls02.json').read_text())
    guide=np.load(ROOT/frozen['selectedGuide']['path'])['vertices']
    actual_path=ROOT/'harness/out/rider-rebuild/glove-anatomical04/solved03/actual-right.npz'
    actual=np.load(actual_path);hand=np.load(ROOT/control['pins']['handR']['path'])
    ids=[642,643,652,379]
    rows=runpy.run_path(str(helper))['closest'](hand['vertices'][ids],actual['vertices'],actual['faces'])
    ownership=[];digits=['pinky','ring','middle','index','thumb']
    for handle in frozen['hands']['R']['handles']:
        digit=handle['label'].split('/')[0]
        if digit not in digits:continue
        point=guide[handle['guideVertex']];distance=[]
        for name in digits:
            path=np.asarray(control['sourceRest']['digits'][name]);best=np.inf
            for a,b in zip(path[:-1],path[1:]):
                t=np.clip(np.dot(point-a,b-a)/np.dot(b-a,b-a),0,1)
                best=min(best,np.linalg.norm(point-a-t*(b-a)))
            distance.append(float(best))
        owner=digits[int(np.argmin(distance))]
        if owner!=digit:
            ownership.append({'label':handle['label'],'guideVertex':handle['guideVertex'],
                'nearestSourceDigit':owner,'nearestSourceCenterlineDistance':min(distance),
                'declaredSourceCenterlineDistance':distance[digits.index(digit)]})
    report={'acceptedArt':False,'recipeSHA256':sha(__file__),'helperSHA256':sha(helper),
            'actualDenseArraySHA256':sha(actual_path),'exactActualDenseCrossings':
                [{'wearerVertex':i,**row} for i,row in zip(ids,rows)],
            'ambiguousOriginalProximalSourceHandles':ownership,
            'limits':['Nearest centerline ambiguity at shared proximal webs is not categorical misbinding.',
                      'Exact skin intersection measures reject gross fit; no art acceptance.']}
    out=ROOT/'docs/evidence/rider-rebuild/glove-anatomical04/local-dense-proof04.json'
    out.write_text(json.dumps(report,indent=2)+'\n');print('proofSHA256',sha(out))


if __name__=='__main__':main()
