"""Read-only diagnosis of native source versus Blender import triangle counts."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parent
rows=[]
for engine in ['hunyuan','trellis']:
 for i in range(1,6):
  s=f'{i:02d}';p=ROOT/engine/(s+'.raw-shape.npz' if engine=='hunyuan' else s+'.npz')
  m=ROOT/'rendered'/engine/s/'native-gray/manifest.json'
  if not m.exists():continue
  d=np.load(p);v=d['vertices'];f=d['faces']
  repeated=(f[:,0]==f[:,1])|(f[:,1]==f[:,2])|(f[:,0]==f[:,2])
  area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)*.5
  imported=json.loads(m.read_text())['triangles']
  rows.append({'engine':engine,'design':s,'nativeFaces':len(f),'blenderImportedFaces':imported,
               'removedAtImport':len(f)-imported,'repeatedVertexIndexFaces':int(repeated.sum()),
               'zeroAreaFaces':int((area==0).sum()),'below1e-15AreaFaces':int((area<1e-15).sum()),
               'repeatedIndexCountMatchesDelta':int(repeated.sum())==len(f)-imported})
out={'status':'read-only source/import discrepancy; parent decides disclosure','subjects':rows,
     'limits':['Source NPZ/GLB untouched','This does not prove absence of other source defects or visual acceptance']}
(ROOT/'rendered/native-import-deltas.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
