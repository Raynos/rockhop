"""Split disconnected vertex fans without displacement, then expose simple loops."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pymeshlab
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
if (out/'scaffold.npz').exists():raise RuntimeError('Frozen output exists')
p=np.load(a.input);ms=pymeshlab.MeshSet()
ms.add_mesh(pymeshlab.Mesh(p['vertices'],p['faces']))
ms.apply_filter('meshing_repair_non_manifold_vertices',vertdispratio=0)
q=ms.current_mesh();v=q.vertex_matrix();f=q.face_matrix()
np.savez(out/'scaffold.npz',vertices=v.astype(np.float32),faces=f.astype(np.int32))
e,c=np.unique(np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1),axis=0,return_counts=True)
b=e[c==1];degrees=np.bincount(b.ravel(),minlength=len(v))
report=dict(status='UNACCEPTED zero-displacement topology split',vertices=len(v),faces=len(f),
            boundaryEdges=int(np.sum(c==1)),nonmanifoldEdges=int(np.sum(c>2)),
            boundaryDegreeExactlyTwo=bool(np.all(degrees[degrees>0]==2)),
            sourceSHA256=hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),
            scriptSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            limits=['Coordinates remain source scaffold; topology split is not anatomical approval.'])
(out/'split-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
