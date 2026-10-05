"""Convert pinned original local coordinates into native world rest surfaces."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
p = argparse.ArgumentParser(description=__doc__); p.add_argument('source_fields'); p.add_argument('contract'); p.add_argument('out'); a = p.parse_args()
out = Path(a.out); assert not out.exists(); sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
n = np.load(a.source_fields); contract = json.loads(Path(a.contract).read_text()); assert sha(a.source_fields) == contract['fieldsSHA256']
parts = {}
for key, prefix, name in [('body','canonical','Canonical anatomical body, baked adult hm08'),('head','head','Protected textured head above hidden neck interface'),('boxer','boxers','Opaque boxer fitting garment')]:
    world = np.asarray(next(x for x in contract['sourceMeshes'] if x['name'] == name)['world'])
    xyz = np.column_stack([n[prefix+'XYZ'],np.ones(len(n[prefix+'XYZ']))])@world.T
    parts[key] = {'xyzWorld':xyz[:,:3].tolist(),'faces':n[prefix+'Triangles'].tolist()}
out.write_text(json.dumps({'parts':parts,'sourceSHA256':contract['sourceSHA256'],'fieldsSHA256':sha(a.source_fields),'contractSHA256':sha(a.contract),'extractorSHA256':sha(__file__)}))
