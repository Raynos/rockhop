"""One isolated nonplanar collar extraction, preserving source UVs and positions.

Semantic graph cut is a candidate boundary, not acceptance or a sewn neck.
The source head is removed only in the derivative. No global remeshing occurs.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, maximum_flow, breadth_first_order

SOURCE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
EXPECTED = 'f657aa963f2e582a9f70291b3dbd160dafd6e944419d48b21b0425521d4cd63a'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def largest_region(mask, adjacency):
    indices = np.flatnonzero(mask)
    graph = coo_matrix((np.ones(len(adjacency)), (adjacency[:, 0], adjacency[:, 1])),
                       shape=(len(mask), len(mask))).tocsr()
    count, labels = connected_components(graph[indices][:, indices], directed=False)
    sizes = np.bincount(labels)
    result = np.zeros(len(mask), dtype=bool)
    result[indices[labels == np.argmax(sizes)]] = True
    return result, {'components': int(count), 'sizes': sorted(sizes.tolist(), reverse=True)}


def boundary_loops(mesh):
    edges = mesh.edges_unique[np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique)) == 1]
    neighbors = {}
    for a, b in edges:
        neighbors.setdefault(int(a), []).append(int(b))
        neighbors.setdefault(int(b), []).append(int(a))
    if any(len(v) != 2 for v in neighbors.values()):
        raise RuntimeError('Boundary has branches; do not export an ambiguous collar')
    remaining = set(neighbors)
    loops = []
    while remaining:
        start = min(remaining)
        loop, previous, current = [], None, start
        while current not in loop:
            loop.append(current)
            nxt = next(n for n in neighbors[current] if n != previous)
            previous, current = current, nxt
        if current != start:
            raise RuntimeError('Boundary walk does not close')
        remaining.difference_update(loop)
        loops.append(loop)
    return sorted(loops, key=len, reverse=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'selection.json').exists():
        raise RuntimeError('Frozen experiment exists; choose a fresh directory')
    before = sha(SOURCE)
    assert before == EXPECTED
    mesh = trimesh.load(SOURCE, process=False).to_geometry()
    mesh.vertices = mesh.vertices[:, [0, 2, 1]] * [1, -1, 1]
    lo, hi = mesh.bounds
    scale = 1.8 / (hi[2] - lo[2])
    mesh.vertices = (mesh.vertices - [(lo[0]+hi[0])/2, (lo[1]+hi[1])/2, lo[2]]) * scale
    vertices, faces = mesh.vertices.copy(), mesh.faces.copy()
    positions, inverse = np.unique(np.round(vertices, 7), axis=0, return_inverse=True)
    welded = trimesh.Trimesh(positions, inverse[faces], process=False)
    adjacency = welded.face_adjacency
    center = vertices[faces].mean(axis=1)
    pixels = np.asarray(mesh.visual.material.baseColorTexture.convert('RGB'))
    uv = mesh.visual.uv[faces].mean(axis=1)
    x = np.clip((uv[:, 0]*pixels.shape[1]).astype(int), 0, pixels.shape[1]-1)
    y = np.clip(((1-uv[:, 1])*pixels.shape[0]).astype(int), 0, pixels.shape[0]-1)
    rgb = pixels[y, x].astype(float)
    rg, bg = rgb[:, 0]/np.maximum(rgb[:, 1], 1), rgb[:, 2]/np.maximum(rgb[:, 1], 1)
    cloth_color = (rg > 1.28) & (bg < .65) & (center[:, 2] < 1.595)
    hood_spatial = (center[:, 2] < 1.53) | (abs(center[:, 0]) > .105) | (center[:, 1] > .035)
    body_seed = (center[:, 2] < 1.495) | (cloth_color & hood_spatial)
    skin_seed = ((center[:, 2] > 1.505) & (center[:, 1] < .045) &
                 (abs(center[:, 0]) < .08) & (bg > .70))
    head_seed = (center[:, 2] > 1.615) | skin_seed
    assert not np.any(body_seed & head_seed), 'Conflicting protected seeds'
    difference = np.linalg.norm(rgb[adjacency[:, 0]] - rgb[adjacency[:, 1]], axis=1)
    weights = np.maximum(2, 100-difference).astype(np.int64)
    band = (center[:, 2] >= 1.49) & (center[:, 2] <= 1.60)
    weights *= np.where(band[adjacency].all(axis=1), 1, 30)
    n, source, sink = len(faces), len(faces), len(faces)+1
    head_ids, body_ids = np.flatnonzero(head_seed), np.flatnonzero(body_seed)
    rows = np.concatenate([adjacency[:, 0], adjacency[:, 1], np.full(len(head_ids), source), body_ids])
    cols = np.concatenate([adjacency[:, 1], adjacency[:, 0], head_ids, np.full(len(body_ids), sink)])
    data = np.concatenate([weights, weights, np.full(len(head_ids)+len(body_ids), 10**7)])
    graph = coo_matrix((data, (rows, cols)), shape=(n+2, n+2), dtype=np.int64).tocsr()
    flow = maximum_flow(graph, source, sink)
    residual = graph - flow.flow
    residual.data = (residual.data > 0).astype(np.int64)
    residual.eliminate_zeros()
    reachable = breadth_first_order(residual, source, directed=True, return_predecessors=False)
    head = np.zeros(n, dtype=bool)
    head[reachable[reachable < n]] = True
    # Remove no isolated garment/skin speck as a separate new hole: retain only
    # the main connected head deletion, then retain the main whole-body surface.
    head, head_components = largest_region(head, adjacency)
    retained, body_components = largest_region(~head, adjacency)
    candidate = trimesh.Trimesh(positions, inverse[faces[retained]], process=False)
    candidate.remove_unreferenced_vertices()
    loops = boundary_loops(candidate)
    # A second circuit is deliberately NOT silently filled or reported sewn.
    loop_rows = [{'count': len(loop), 'positions': candidate.vertices[loop].tolist(),
                  'bounds': [candidate.vertices[loop].min(axis=0).tolist(),
                             candidate.vertices[loop].max(axis=0).tolist()]} for loop in loops]
    np.savez(out/'collar-selection.npz', retainedFaceMask=retained,
             verticesBlender=vertices, faces=faces, uv=mesh.visual.uv,
             boundaryVertices=candidate.vertices[np.concatenate(loops)])
    # The exporter preserves selected original triangles and UV seam duplicates.
    # Convert canonical Blender coordinates back to glTF Y-up for correct import.
    exported = mesh.copy()
    exported.update_faces(retained)
    exported.remove_unreferenced_vertices()
    exported.vertices = exported.vertices[:, [0, 2, 1]] * [1, 1, -1]
    exported.export(out/'body-open-collar.glb')
    source_after = sha(SOURCE)
    assert before == source_after
    counts = np.bincount(candidate.edges_unique_inverse, minlength=len(candidate.edges_unique))
    report = {'status': 'UNACCEPTED isolated open-collar candidate; no head attachment or rig',
              'source': str(SOURCE), 'sourceSHA256': before, 'sourceSHA256After': source_after,
              'recipeSHA256': sha(__file__), 'outputSHA256': sha(out/'body-open-collar.glb'),
              'inputFaces': n, 'retainedFaces': int(retained.sum()),
              'originalCoordinateAndUVPolicy': 'Exact retained source vertices/UVs; axis and uniform display normalization only',
              'displayHeightOldHairInclusive': 1.8, 'normalizationScale': float(scale),
              'graphCutFlow': int(flow.flow_value), 'headComponents': head_components,
              'retainedComponents': body_components, 'boundaryLoops': loop_rows,
              'boundaryEdges': int(np.sum(counts == 1)), 'nonmanifoldEdges': int(np.sum(counts > 2)),
              'protectedBodySeedFacesRemoved': int(np.sum(body_seed & ~retained)),
              'colorClassifiedClothFacesRemoved': int(np.sum(cloth_color & ~retained)),
              'limits': ['Semantic colour seeds can misclassify skin/hood; actual PBR/gray review required',
                         'Any additional boundary requires explicit correction, not an overlap',
                         'No neck sewing, normals match, deformation or appearance pass']}
    (out/'selection.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'boundaryLoops'}, indent=2))


if __name__ == '__main__':
    main()
