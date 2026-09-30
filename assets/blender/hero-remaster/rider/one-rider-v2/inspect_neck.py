"""Read-only cross sections and PBR samples; never cuts the donor."""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh

SOURCE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
OUT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/neck-inspection')
OUT.mkdir(parents=True, exist_ok=True)
before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
scene = trimesh.load(SOURCE, process=False)
mesh = scene.to_geometry()
# glTF Y-up -> Blender Z-up; same display normalization as matched review.
mesh.vertices = mesh.vertices[:, [0, 2, 1]] * [1, -1, 1]
lo, hi = mesh.bounds
scale = 1.8 / (hi[2] - lo[2])
mesh.vertices = (mesh.vertices - [(lo[0]+hi[0])/2, (lo[1]+hi[1])/2, lo[2]]) * scale
rows = []
sections = {}
for height in [1.40, 1.44, 1.48, 1.52, 1.56, 1.60, 1.64]:
    section = mesh.section(plane_origin=[0, 0, height], plane_normal=[0, 0, 1])
    paths = section.discrete if section else []
    sections[str(height)] = [p.tolist() for p in paths]
    rows.append({'heightMetres': height, 'contours': [
        {'vertices': len(p), 'closed': bool(np.linalg.norm(p[0]-p[-1]) < 1e-6),
         'bounds': [p.min(axis=0).tolist(), p.max(axis=0).tolist()],
         'centroid': p.mean(axis=0).tolist()} for p in paths]})
pixels = np.asarray(mesh.visual.material.baseColorTexture.convert('RGB'))
uv = mesh.visual.uv
iy = np.clip(((1-uv[:, 1])*pixels.shape[0]).astype(int), 0, pixels.shape[0]-1)
ix = np.clip((uv[:, 0]*pixels.shape[1]).astype(int), 0, pixels.shape[1]-1)
rgb = pixels[iy, ix]
head = mesh.vertices[:, 2] >= 1.40
np.savez(OUT / 'head-samples.npz', vertices=mesh.vertices[head], rgb=rgb[head])
after = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert before == after
(OUT / 'sections.json').write_text(json.dumps(sections, indent=2)+'\n')
(OUT / 'inspection.json').write_text(json.dumps({
    'status': 'read-only diagnosis; no boundary chosen or correction attempted',
    'source': str(SOURCE), 'sourceSHA256': before, 'sourceSHA256After': after,
    'normalization': {'height': 1.8, 'scale': scale, 'inputBoundsBlender': [lo.tolist(), hi.tolist()]},
    'sections': rows, 'limits': ['Cross-section circuits are diagnostic, not a selected sewn skin contour',
                                'UV colour alone cannot separate similarly coloured hoodie and skin',
                                'No source mutation, assembly, rig or quality acceptance']}, indent=2)+'\n')
print(json.dumps(rows, indent=2))
