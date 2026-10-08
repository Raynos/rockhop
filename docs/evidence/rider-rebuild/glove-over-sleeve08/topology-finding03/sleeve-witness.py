"""Replay the already-observed author03 source/topology witnesses; read only."""
import ast
import hashlib
import json
import runpy
from pathlib import Path
import numpy as np

ROOT = Path('/Users/raynos/projects/games/rockhop')
HERE = ROOT/'assets/blender/rider-rebuild/glove-over-sleeve08'
control = json.loads((HERE/'input.json').read_text())
V = runpy.run_path(str(HERE/'volume.py'))
source_path = ROOT/control['originalHoodie']['path']
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == control['originalHoodie']['sha256']
source = V['read_hoodie'](source_path)
frames = json.loads((ROOT/control['hoodieSourceFrames']['path']).read_text())
crop_path = ROOT/'harness/out/rider-rebuild/glove-over-sleeve08/authored03/actual-hoodie-wrists.npz'
assert hashlib.sha256(crop_path.read_bytes()).hexdigest() == 'b30a1299e1291895a91ff267d20a14d752a2a6c3236c45e2a112cb26913dd1bd'
crop = np.load(crop_path)
ids, triangles = crop['nativeVertexIds'], crop['faces']
face_ids = crop['nativeLoopTriangleIds']
tree = ast.parse((HERE/'author.py').read_text())
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'strict_cross')
scope = {'np': np}
exec(compile(ast.Module(body=[node], type_ignores=[]), 'strict_cross', 'exec'), scope)
result = {'scope': 'Existing author03 witnessed faces and original source terminal topology only; no geometry edits', 'hands': {}}
world_source = source[ids]*np.asarray(frames['sourceDisplayAffine']['scale'])+np.asarray(frames['sourceDisplayAffine']['translation'])
# UV seams duplicate positions; welding here is diagnostic only, never authoring.
_, index, inverse = np.unique(np.round(world_source, 8), axis=0, return_index=True, return_inverse=True)
welded_points = world_source[index]
welded_faces = inverse[triangles]
valid_faces = welded_faces[np.all(np.diff(np.sort(welded_faces, axis=1), axis=1) > 0, axis=1)]
edges, incidence = np.unique(np.sort(np.concatenate([valid_faces[:, [0, 1]], valid_faces[:, [1, 2]], valid_faces[:, [2, 0]]]), axis=1), axis=0, return_counts=True)
for side, pair in [('L', [918439, 919448]), ('R', [16950, 16954])]:
    face = np.array([triangles[np.flatnonzero(face_ids == i)[0]] for i in pair])
    hand = {'nativeTriangleIds': pair, 'nativeVertexIds': ids[face].tolist(), 'pair': {}}
    for name, points in [('originalSource', source[ids]), ('engine05Baseline', crop['baselineWorldXYZ']), ('author03Actual', crop['worldXYZ'])]:
        t = points[face]
        hand['pair'][name] = {'strictCross': scope['strict_cross'](*t), 'areaMM2': (.5e6*np.linalg.norm(np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]), axis=1)).tolist()}
    bone = next(b for b in frames['authoringBones'] if b['name'] == 'AUTHOR_Forearm.'+side)
    head = np.asarray(bone['sourceHead'])
    axis = np.asarray(bone['sourceTail'])-head
    axis /= np.linalg.norm(axis)
    axial = np.sum((welded_points-head)*axis, axis=1)
    own = welded_points[:, 0] > 0 if side == 'L' else welded_points[:, 0] < 0
    tip = float(axial[own].max())
    terminal_edges = np.all(own[edges], axis=1) & np.all(axial[edges] > tip-.02, axis=1)
    hand['sourceTerminal20MM'] = {'tipAxialM': tip, 'edges': int(terminal_edges.sum()), 'boundaryEdges': int(np.sum(terminal_edges & (incidence == 1))), 'nonmanifoldEdges': int(np.sum(terminal_edges & (incidence > 2)))}
    hand['sourceSections'] = []
    side_faces = welded_faces[np.all(own[welded_faces], axis=1)]
    for gap in [.001, .005, .01, .02]:
        distance = axial-(tip-gap)
        crossing = side_faces[np.any(distance[side_faces] > 0, axis=1) & np.any(distance[side_faces] < 0, axis=1)]
        adjacency = {}
        for tri in crossing:
            cut = [tuple(sorted((tri[j], tri[(j+1) % 3]))) for j in range(3) if distance[tri[j]]*distance[tri[(j+1) % 3]] < 0]
            if len(cut) == 2:
                adjacency.setdefault(cut[0], set()).add(cut[1])
                adjacency.setdefault(cut[1], set()).add(cut[0])
        remaining, components = set(adjacency), []
        while remaining:
            pending, component = [remaining.pop()], []
            while pending:
                current = pending.pop()
                component.append(current)
                for neighbor in adjacency[current] & remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
            components.append({'edges': len(component), 'allDegree2': all(len(adjacency[e]) == 2 for e in component)})
        hand['sourceSections'].append({'tipMinusMM': gap*1000, 'components': components})
    result['hands'][side] = hand
print(json.dumps(result, indent=2))
