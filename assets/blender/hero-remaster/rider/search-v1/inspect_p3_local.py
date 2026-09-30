"""Read-only locality audit for chosen P3; no model or texture writes."""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh

REPO = Path(__file__).resolve().parents[5]
SOURCE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/pixal/03/working.glb')
OUT = REPO / 'docs/evidence/hero-remaster/rider-search-v1/manual-p3'
OUT.mkdir(parents=True, exist_ok=True)
sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert sha == 'fa149ce5584cc2039d92cda7403c852bbe93004c28f1790894492e7ec7d6e005'
original = trimesh.load(SOURCE, force='mesh', process=False)
mesh = original.copy()
mesh.merge_vertices(merge_tex=True, merge_norm=True, digits_vertex=8)
counts = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))

def components(edges):
    neighbors = {}
    for a, b in edges:
        neighbors.setdefault(int(a), set()).add(int(b))
        neighbors.setdefault(int(b), set()).add(int(a))
    visited = set()
    groups = []
    for start in sorted(neighbors):
        if start in visited:
            continue
        stack, group = [start], []
        while stack:
            v = stack.pop()
            if v in visited:
                continue
            visited.add(v)
            group.append(v)
            stack.extend(neighbors[v] - visited)
        group = sorted(group)
        vertices = mesh.vertices[group]
        degrees = [len(neighbors[v]) for v in group]
        selected = edges[np.isin(edges[:, 0], group)]
        lengths = np.linalg.norm(mesh.vertices[selected[:, 0]] - mesh.vertices[selected[:, 1]], axis=1)
        groups.append({'vertices': len(group), 'edges': len(selected), 'firstWeldedVertex': group[0],
                       'min': vertices.min(axis=0).tolist(), 'max': vertices.max(axis=0).tolist(),
                       'center': vertices.mean(axis=0).tolist(), 'degreeRange': [min(degrees), max(degrees)],
                       'closedSimpleLoop': all(d == 2 for d in degrees),
                       'perimeterMetresAt1p8Height': float(lengths.sum() * 1.8 / mesh.extents[1]),
                       'touchesFrozenHeadNeck': bool((vertices[:, 1] >= .25).any())})
    return groups

sorted_faces = np.sort(mesh.faces, axis=1)
_, inverse, repeats = np.unique(sorted_faces, axis=0, return_inverse=True, return_counts=True)
duplicate_mask = repeats[inverse] > 1
repeat_index = np.any(np.diff(sorted_faces, axis=1) == 0, axis=1)
head_faces = (mesh.vertices[mesh.faces][:, :, 1] >= .25).any(axis=1)
region_vertices = original.vertices[:, 1] >= .25
region_faces = region_vertices[original.faces].any(axis=1)
uv = np.asarray(original.visual.uv)
frozen = {'sourceYAxisThreshold': .25, 'sourceAxes': 'glTF X/Z horizontal, Y up',
          'meaning': 'Conservative head/neck envelope including touching triangles; body repair cannot move/delete these vertices/faces or edit texture',
          'vertices': int(region_vertices.sum()), 'faces': int(region_faces.sum()),
          'vertexRecordSHA256': hashlib.sha256(np.c_[np.flatnonzero(region_vertices), original.vertices[region_vertices], uv[region_vertices]].tobytes()).hexdigest(),
          'faceRecordSHA256': hashlib.sha256(np.c_[np.flatnonzero(region_faces), original.faces[region_faces]].tobytes()).hexdigest()}
report = {'status': 'inspection only; no correction attempt', 'source': str(SOURCE), 'sourceSHA256': sha,
          'sourceFaces': len(original.faces), 'sourceVertices': len(original.vertices),
          'positionWeldedVertices': len(mesh.vertices), 'weldDigits': 8, 'frozenHeadNeck': frozen,
          'boundaryEdges': int((counts == 1).sum()), 'edgesWithMoreThanTwoFaces': int((counts > 2).sum()),
          'boundaryComponents': components(mesh.edges_unique[counts == 1]),
          'overlapComponents': components(mesh.edges_unique[counts > 2]),
          'duplicateGeometryFaceMembers': int(duplicate_mask.sum()),
          'duplicateGeometryMembersTouchingFrozenHeadNeck': int((duplicate_mask & head_faces).sum()),
          'positionWeldRepeatIndexFaces': int(repeat_index.sum()),
          'positionWeldRepeatIndexFacesTouchingFrozenHeadNeck': int((repeat_index & head_faces).sum()),
          'sourceRepeatIndexFaces': int(np.any(np.diff(np.sort(original.faces, axis=1), axis=1) == 0, axis=1).sum()),
          'limits': ['Analysis weld ignores UV/normal seams; original model remains byte-identical',
                     'Connected boundaries do not alone prove a visually significant defect',
                     'No geometry correction, new bust, skinning or physics changes']}
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == sha
(OUT / 'locality-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items() if key not in ['boundaryComponents', 'overlapComponents']}, indent=2))
print('boundary groups:', len(report['boundaryComponents']))
print('nonmanifold groups:', len(report['overlapComponents']))
print('largest boundary groups:', sorted(report['boundaryComponents'], key=lambda c:c['edges'], reverse=True)[:8])
