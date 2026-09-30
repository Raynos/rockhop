"""Canonical full-source control for matched collar extraction review."""
from pathlib import Path
import hashlib
import json
import trimesh

source = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
out = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/collar-control')
out.mkdir(parents=True, exist_ok=True)
if (out/'control.json').exists():
    raise RuntimeError('Frozen control exists')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
before = sha(source)
assert before == 'f657aa963f2e582a9f70291b3dbd160dafd6e944419d48b21b0425521d4cd63a'
mesh = trimesh.load(source, process=False).to_geometry()
mesh.vertices = mesh.vertices[:, [0, 2, 1]] * [1, -1, 1]
lo, hi = mesh.bounds
scale = 1.8 / (hi[2]-lo[2])
mesh.vertices = (mesh.vertices-[(lo[0]+hi[0])/2, (lo[1]+hi[1])/2, lo[2]])*scale
mesh.vertices = mesh.vertices[:, [0, 2, 1]] * [1, 1, -1]
mesh.export(out/'body-control.glb')
assert before == sha(source)
(out/'control.json').write_text(json.dumps({'source':str(source),'sourceSHA256':before,
    'recipeSHA256':sha(__file__),'outputSHA256':sha(out/'body-control.glb'),
    'policy':'All original triangles/UVs/native PBR preserved; axes/uniform1.8m display normalization only',
    'faces':len(mesh.faces),'scale':float(scale)},indent=2)+'\n')
