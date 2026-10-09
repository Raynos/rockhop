"""Expose all pinned native63 samples to the CPU JS preflight; no scene read."""
import hashlib
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
PRODUCTION=ROOT/'harness/out/rider-rebuild/selected-boot-native63/native01/production.json'
PRODUCTION_SHA='ba31a23f3489296c97ca02d3e34808cc10e8f869cc1f035d347b148efdba7644'
SAMPLES_SHA='a392ee80c46ba2f0caa927b430ef5bb74fe4349eed53c78845dbcd88b7f39eda'
def pin(p, expected=None):
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    if expected is not None: assert digest==expected
    return {'path':str(p.relative_to(ROOT)), 'sha256':digest}
production_pin=pin(PRODUCTION,PRODUCTION_SHA); report=json.loads(PRODUCTION.read_text())
sample=report['sourceSurfaceSamples']['target-face-centroids']['arrays'];assert sample['sha256']==SAMPLES_SHA
file=ROOT/sample['path'];pin(file,SAMPLES_SHA)
out=ROOT/'docs/evidence/rider-rebuild/selected-boot-surface67';out.mkdir(parents=True,exist_ok=True)
with np.load(file) as package:
    raw=bytearray();layout={}
    for key in ['sourceFaceId','distanceM','normalDot']:
        values=package[key];assert len(values)==26528
        data=values.tobytes();layout[key]={'dtype':values.dtype.str,'count':len(values),'byteOffset':len(raw),'byteLength':len(data)};raw.extend(data)
binary=out/'native-reference.bin';binary.write_bytes(raw)
(out/'native-reference.json').write_text(json.dumps({'status':'EXACT_NATIVE63_SAMPLES_FOR_CPU_COMPARISON','recipe':pin(Path(__file__)),
    'production':production_pin,'sourceNPZ':sample,'samples':26528,'arrays':dict(pin(binary),layout=layout)},indent=2)+'\n')
print(json.dumps(pin(out/'native-reference.json')))
