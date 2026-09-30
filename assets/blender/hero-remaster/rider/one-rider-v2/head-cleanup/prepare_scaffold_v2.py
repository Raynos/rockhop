"""Attempt2 scaffold: preserve source shape, clean redundant/internal triangles.

CPU-only. No resampling/remeshing/decimation, no source overwrite or UV claim.
"""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
import trimesh
import pymeshlab
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
if (out/'scaffold.npz').exists(): raise RuntimeError('Frozen scaffold exists')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before = sha(a.input); start = time.monotonic()
m = trimesh.load(a.input, process=False).to_geometry()
stages = []
def record(name, mesh):
    counts = np.bincount(mesh.edges_unique_inverse)
    stages.append(dict(stage=name, vertices=len(mesh.vertices), faces=len(mesh.faces),
                       boundaryEdges=int(np.sum(counts==1)),
                       nonmanifoldEdges=int(np.sum(counts>2))))
record('raw GLB includes UV/normal splits', m)
m.merge_vertices(merge_tex=True, merge_norm=True); record('position seam weld',m)
v,f = m.vertices,m.faces
area = np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
m.update_faces(area>1e-12); m.update_faces(m.unique_faces())
m.remove_unreferenced_vertices(); record('remove degenerate and duplicate faces',m)
ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(m.vertices,m.faces))
ms.apply_filter('meshing_repair_non_manifold_edges', method='Remove Faces')
q = ms.current_mesh(); m = trimesh.Trimesh(q.vertex_matrix(),q.face_matrix(),process=False)
record('remove minimum-area offending nonmanifold faces',m)
ms.apply_filter('meshing_close_holes', maxholesize=128, refinehole=False,
                selfintersection=True)
q = ms.current_mesh(); m = trimesh.Trimesh(q.vertex_matrix(),q.face_matrix(),process=False)
record('close only holes with at most 128 edges',m)
components = m.split(only_watertight=False)
if not components: raise RuntimeError('No scaffold component')
m = max(components,key=lambda x:len(x.faces)); record('largest connected skin component',m)
# Native source GLB flipped X/Z during export; explicit adapter to dense NPZ.
native = m.vertices * [-1,1,-1]
np.savez(out/'scaffold.npz',vertices=native.astype(np.float32),faces=m.faces.astype(np.int32))
report=dict(status='UNACCEPTED repaired source scaffold, not dense original',
            source=a.input, sourceSHA256=before, sourceSHA256After=sha(a.input),
            scriptSHA256=sha(__file__), stages=stages,
            sourceComponents=len(components), wallSeconds=time.monotonic()-start,
            limits=['Original GLB UVs/textures retained untouched, not copied to this scaffold.',
                    'Small-hole fill can simplify crease anatomy; gray review required.',
                    'No dense fit or scalp stitching yet.'])
assert before==report['sourceSHA256After']
(out/'scaffold-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
