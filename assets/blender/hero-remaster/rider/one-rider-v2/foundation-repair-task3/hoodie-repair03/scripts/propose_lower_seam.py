"""Diagnostic curved seam proposal on unchanged cloth; no cutting or repair.

Use intrinsic face adjacency, actual folded geometry, and source atlas clues.
Anatomical upper/lower seeds only bound the search. Every proposed cycle must
be reviewed in rest front/side/back views before it becomes a garment seam.
"""
from pathlib import Path
import sys, io, json, hashlib
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import maximum_flow, breadth_first_order, connected_components

ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
sys.path.insert(0, str(ROOT / 'scripts'))
from glb import GLB
g = GLB(ROOT / 'deliverables/C19.glb')
pr = [p for m in g.j['meshes'] for p in m['primitives']]
P = [g.array(p['attributes']['POSITION']).astype(float) for p in pr]
T = [g.array(p['indices']).reshape(-1, 3).astype(int) for p in pr]
points = np.concatenate([P[0], P[2]])
faces = np.concatenate([T[0], T[2] + len(P[0])])
unique, aliases = np.unique(points, axis=0, return_inverse=True)
ft = aliases[faces]
edges = np.sort(np.concatenate([ft[:, [0, 1]], ft[:, [1, 2]], ft[:, [0, 2]]]), axis=1)
edgefaces = np.tile(np.arange(len(faces)), 3)
order = np.lexsort((edges[:, 1], edges[:, 0]))
edges, edgefaces = edges[order], edgefaces[order]
uedge, starts, counts = np.unique(edges, axis=0, return_index=True, return_counts=True)
inside = np.flatnonzero(counts == 2)
adjacent = np.array([edgefaces[starts[i]:starts[i]+2] for i in inside])
facepoints = points[faces]
normal = np.cross(facepoints[:, 1]-facepoints[:, 0], facepoints[:, 2]-facepoints[:, 0])
normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-15)
gold, blue = [], []
for i in [0, 2]:
    m = g.j['materials'][pr[i]['material']]
    im = g.j['images'][g.j['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
    bv = g.j['bufferViews'][im['bufferView']]
    image = np.asarray(Image.open(io.BytesIO(bytes(g.bin[bv.get('byteOffset', 0):bv.get('byteOffset', 0)+bv['byteLength']]))).convert('RGB')).astype(float)
    uv = g.array(pr[i]['attributes']['TEXCOORD_0'])[T[i]].mean(1)
    xy = np.clip(uv, 0, 1) * [image.shape[1]-1, image.shape[0]-1]
    c = image[np.rint(xy[:, 1]).astype(int), np.rint(xy[:, 0]).astype(int)]
    gold.append((c[:, 0]>c[:, 1]+15)&(c[:, 1]>c[:, 2]+12)&(c[:, 0]>75))
    blue.append((c[:, 2]>c[:, 0]*1.12)&(c[:, 2]>c[:, 1]*1.02)&(c[:, 0]<140))
gold, blue = np.concatenate(gold), np.concatenate(blue)
color_boundary = (gold[adjacent[:, 0]] & blue[adjacent[:, 1]]) | (blue[adjacent[:, 0]] & gold[adjacent[:, 1]])
angle = np.arccos(np.clip(np.einsum('ij,ij->i', normal[adjacent[:, 0]], normal[adjacent[:, 1]]), -1, 1))
length = np.linalg.norm(unique[uedge[inside, 0]]-unique[uedge[inside, 1]], axis=1)
source_seeds = np.flatnonzero(facepoints[:, :, 1].min(1)>1.11)
sink_seeds = np.flatnonzero(facepoints[:, :, 1].max(1)<.84)
OUT = ROOT / 'hoodie-repair03/lower-foundation/seam-proposals'
OUT.mkdir(parents=True, exist_ok=True)
reports = []
for label, color_strength in [('geometry', 0), ('texture-clues', .7)]:
    capacity = np.maximum(1, np.rint(length*(.08+np.exp(-3*angle))*(1-color_strength*color_boundary)*1e5)).astype(np.int64)
    n = len(faces)
    large = int(capacity.sum()*2+1)
    assert large < 2**31-1, 'SciPy flow capacity overflow'
    rows = np.r_[adjacent[:, 0], adjacent[:, 1], np.full(len(source_seeds), n), sink_seeds]
    cols = np.r_[adjacent[:, 1], adjacent[:, 0], source_seeds, np.full(len(sink_seeds), n+1)]
    caps = np.r_[capacity, capacity, np.full(len(source_seeds)+len(sink_seeds), large)]
    graph = coo_matrix((caps, (rows, cols)), shape=(n+2, n+2)).tocsr()
    flow = maximum_flow(graph, n, n+1)
    residual = graph-flow.flow
    residual.data[residual.data<=0] = 0
    residual.eliminate_zeros()
    reached = breadth_first_order(residual, n, directed=True, return_predecessors=False)
    shirt = np.zeros(n+2, bool)
    shirt[reached] = True
    cut = inside[shirt[adjacent[:, 0]] != shirt[adjacent[:, 1]]]
    ce = uedge[cut]
    assert len(ce) > 0 and flow.flow_value > 0, 'No valid separating flow cut'
    vertices, degrees = np.unique(ce, return_counts=True)
    cg = coo_matrix((np.ones(len(ce)*2), (np.r_[ce[:, 0], ce[:, 1]], np.r_[ce[:, 1], ce[:, 0]])), shape=(len(unique), len(unique))).tocsr()
    _, components = connected_components(cg, directed=False)
    component_sizes = np.bincount(components[vertices])
    cycle = []
    simple = len(component_sizes[component_sizes>0])==1 and np.all(degrees==2)
    if simple:
        neighbors = {int(v): cg.indices[cg.indptr[v]:cg.indptr[v+1]].tolist() for v in vertices}
        start = int(vertices[0]); prev, current = -1, start
        for _ in range(len(vertices)):
            cycle.append(current)
            next_vertex = next(v for v in neighbors[current] if v!=prev)
            prev, current = current, next_vertex
        assert current==start and len(set(cycle))==len(vertices)
    provenance = {'sourceSHA256': hashlib.sha256(g.raw).hexdigest(), 'status': 'UNACCEPTED curved seam proposal; no source geometry or skin edits', 'method': 'Minimum intrinsic dual-face cut using actual edge length, dihedral folds and optional original atlas locating clues. Upper/lower seed sets bound the search, no planar cut.', 'label': label, 'edgeCount': len(ce), 'oneSimpleDegreeTwoClosedCycle': bool(simple), 'componentVertexSizes': component_sizes[component_sizes>0].tolist(), 'yRangeM': unique[vertices, 1][[np.argmin(unique[vertices, 1]), np.argmax(unique[vertices, 1])]].tolist(), 'clothTopologyUnchanged': True, 'requiredReview': 'Actual gray/textured rest front/side/back overlay and source ridge landmarks; partition consistency; explicit separate physical weld IDs and hidden caps before any pose claim.'}
    np.savez(OUT/f'{label}.npz', sourcePoints=unique, cycle=np.array(cycle, int), cutEdges=ce, sourceCombinedFaces=faces, sourceWeldTriangles=ft, shirtFaces=shirt[:n], aliases=aliases)
    (OUT/f'{label}.json').write_text(json.dumps(provenance, indent=2)+'\n')
    reports.append(provenance)
print(json.dumps(reports, indent=2))
