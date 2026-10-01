"""Compare actual physical state across matched surface/camera captures."""
from pathlib import Path
import json

base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-hips11/framed02')
previous=json.loads(Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/framed02/report.json').read_text())
assert len(previous['samples']) >= 264
rows=[]
for angle in ['side','rear-three-quarter']:
    pair=[json.loads((base/angle/surface/'report.json').read_text()) for surface in ['textured','gray']]
    for r in pair:
        assert r['sourceSHA256']=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
        assert r['frames']==264 and r['fps']==12 and not r['errors']
        assert any(x['sha256']==r['sourceSHA256'] and x['status']==200 for x in r['loaded'])
        for a,b in zip(r['samples'],previous['samples']):
            for key in ['state','hash','debug']:
                assert a[key]==b[key], (angle,r['surface'],a['i'],key)
    for a,b in zip(pair[0]['samples'],pair[1]['samples']):
        for key in ['bones','camera','anchor','orbit']:
            assert a[key]==b[key],(angle,a['i'],key)
    rows.append({'angle':angle,'physicalStateHashDebugExactVsPrior':264,'PBRGrayBonesCameraExact':264,'loadedCurrentRiderVerified':True})
(base/'matched-validation.json').write_text(json.dumps({'rows':rows,'limit':'World presentation differs across camera angles; world bones compared only within matched textured/gray angle pairs.'},indent=2)+'\n')
print(json.dumps(rows))
