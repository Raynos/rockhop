"""Read-only finite homology localization; virtual cuff cell never edits source."""
import argparse
from collections import deque
import hashlib
import heapq
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(adjacency, root, count):
    distance = np.full(count, np.inf)
    parent = np.full(count, -1, np.int32)
    parent_edge = np.full(count, -1, np.int32)
    distance[root] = 0.
    queue = [(0., root)]
    while queue:
        value, vertex = heapq.heappop(queue)
        if value != distance[vertex]:
            continue
        for neighbor, edge, weight in adjacency[vertex]:
            candidate = value + weight
            if candidate < distance[neighbor]:
                distance[neighbor] = candidate
                parent[neighbor], parent_edge[neighbor] = vertex, edge
                heapq.heappush(queue, (candidate, neighbor))
    return distance, parent, parent_edge


def ancestor_table(parent, root, referenced):
    children = [[] for _ in parent]
    for vertex in referenced:
        if vertex != root:
            children[parent[vertex]].append(int(vertex))
    depth = np.zeros(len(parent), np.int32)
    order, queue = [], deque([root])
    while queue:
        vertex = queue.popleft()
        order.append(vertex)
        for child in children[vertex]:
            depth[child] = depth[vertex] + 1
            queue.append(child)
    first = parent.copy()
    first[root] = root
    first[first < 0] = root
    up = [first]
    for _ in range(int(depth.max()).bit_length()):
        up.append(up[-1][up[-1]])
    return depth, up, order


def lca(a, b, depth, up):
    if depth[a] < depth[b]:
        a, b = b, a
    difference = int(depth[a] - depth[b])
    for k in range(len(up)):
        if difference & (1 << k):
            a = int(up[k][a])
    if a == b:
        return a
    for k in reversed(range(len(up))):
        if up[k][a] != up[k][b]:
            a, b = int(up[k][a]), int(up[k][b])
    return int(up[0][a])


def cycle(a, b, edge, common, parent, parent_edge):
    vertices_a, edges_a, vertices_b, edges_b = [a], [], [b], []
    while vertices_a[-1] != common:
        current = vertices_a[-1]
        edges_a.append(int(parent_edge[current]))
        vertices_a.append(int(parent[current]))
    while vertices_b[-1] != common:
        current = vertices_b[-1]
        edges_b.append(int(parent_edge[current]))
        vertices_b.append(int(parent[current]))
    vertices = vertices_a + list(reversed(vertices_b[:-1]))
    edges = edges_a + list(reversed(edges_b)) + [edge]
    assert len(vertices) == len(edges) and len(set(vertices)) == len(vertices)
    return vertices, edges


def main():
    parser = argparse.ArgumentParser()
    for name in ['opening', 'opening-sha256', 'anatomy', 'anatomy-sha256', 'out', 'evidence']:
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    pins = [(args.opening, args.opening_sha256), (args.anatomy, args.anatomy_sha256)]
    assert all(sha(path) == expected for path, expected in pins)
    opening = json.loads(Path(args.opening).read_text())
    anatomy = json.loads(Path(args.anatomy).read_text())
    source_path, source_hash = opening['candidate']['path'], opening['candidate']['sha256']
    assert source_hash == '8379004e394bbae110f495c13bfc12a205977061d13cefdcc8ee24c6e5343782'
    assert sha(source_path) == source_hash
    branch_pin = anatomy['output']
    assert sha(branch_pin['path']) == branch_pin['sha256']
    source, branches = np.load(source_path), np.load(branch_pin['path'])
    xyz, faces = source['vertices'], source['faces']
    labels = branches['branchLabels']
    assert np.array_equal(xyz, branches['vertices'])
    assert np.array_equal(faces, branches['faces'][source['sourcePrototypeFaceRows']])
    assert len(faces) == 14543 and len(xyz) == 8000 and np.isfinite(xyz).all()
    incidence, orientation, links = {}, {}, [{} for _ in xyz]
    for row, face in enumerate(faces):
        assert len(set(face.tolist())) == 3
        for vertex, a, b in [(face[0], face[1], face[2]), (face[1], face[2], face[0]), (face[2], face[0], face[1])]:
            links[vertex].setdefault(int(a), []).append(int(b))
            links[vertex].setdefault(int(b), []).append(int(a))
        for a, b in zip(face, np.roll(face, -1)):
            pair = tuple(sorted((int(a), int(b))))
            incidence.setdefault(pair, []).append(row)
            orientation[pair] = orientation.get(pair, 0) + (1 if a < b else -1)
    edge_vertices = sorted(incidence)
    edge_rows = [incidence[edge] for edge in edge_vertices]
    referenced = np.unique(faces)
    boundary = [index for index, rows in enumerate(edge_rows) if len(rows) == 1]
    assert len(boundary) == 71 and len(referenced) == 7306 and len(edge_rows) == 21850
    assert all(len(rows) in [1, 2] for rows in edge_rows)
    assert all(orientation[edge] == 0 if len(rows) == 2 else abs(orientation[edge]) == 1 for edge, rows in incidence.items())
    boundary_set = set(np.unique(np.array([edge_vertices[i] for i in boundary])).tolist())
    for vertex in referenced:
        link = links[vertex]
        reached, queue = set(), [min(link)]
        while queue:
            current = queue.pop()
            if current in reached:
                continue
            reached.add(current)
            queue.extend(link[current])
        degrees = [len(neighbors) for neighbors in link.values()]
        assert len(reached) == len(link) and all(degree in [1, 2] for degree in degrees)
        assert degrees.count(1) == (2 if int(vertex) in boundary_set else 0)
    # A virtual single polygon cell closes the cuff only in the cellular chain
    # complex. Its boundary is all 71 actual source edges; no positions/faces save.
    cap = len(faces)
    dual_incidence = [rows if len(rows) == 2 else rows + [cap] for rows in edge_rows]
    adjacency = [[] for _ in xyz]
    for edge, (a, b) in enumerate(edge_vertices):
        weight = float(np.linalg.norm(xyz[a] - xyz[b]))
        assert weight > 0 and np.isfinite(weight)
        adjacency[a].append((b, edge, weight))
        adjacency[b].append((a, edge, weight))
    boundary_vertices = np.unique(np.array([edge_vertices[i] for i in boundary]))
    root = int(boundary_vertices.min())
    distance, parent, parent_edge = tree(adjacency, root, len(xyz))
    assert np.isfinite(distance[referenced]).all()
    primal = set(parent_edge[referenced].tolist()) - {-1}
    dual = [[] for _ in range(cap + 1)]
    for edge, (a, b) in enumerate(dual_incidence):
        if edge not in primal:
            dual[a].append((b, edge))
            dual[b].append((a, edge))
    dual_parent = np.full(cap + 1, -1, np.int32)
    dual_parent_edge = np.full(cap + 1, -1, np.int32)
    dual_parent[cap] = cap
    queue = deque([cap])
    while queue:
        face = queue.popleft()
        for neighbor, edge in dual[face]:
            if dual_parent[neighbor] < 0:
                dual_parent[neighbor], dual_parent_edge[neighbor] = face, edge
                queue.append(neighbor)
    assert (dual_parent >= 0).all()
    cotree = set(dual_parent_edge.tolist()) - {-1}
    leftover = sorted(set(range(len(edge_rows))) - primal - cotree)
    assert len(primal) == 7305 and len(cotree) == 14543 and len(leftover) == 2
    # Each leftover edge plus its dual-tree path is a closed dual cycle. Its
    # incidence on actual source edges is a GF(2) cocycle that certifies surface
    # cycles as non-boundaries, independent of geometric appearance.
    edge_code = np.zeros(len(edge_rows), np.uint8)
    dual_certificates = []
    for bit, edge in enumerate(leftover):
        a, b = dual_incidence[edge]
        paths = []
        for start in [a, b]:
            vertices_path, edges_path = [start], []
            while vertices_path[-1] != cap:
                current = vertices_path[-1]
                edges_path.append(int(dual_parent_edge[current]))
                vertices_path.append(int(dual_parent[current]))
            paths.append((vertices_path, edges_path))
        vertices_a, edges_a = paths[0]
        vertices_b, edges_b = paths[1]
        common = next(face for face in vertices_a if face in set(vertices_b))
        support = edges_a[:vertices_a.index(common)] + edges_b[:vertices_b.index(common)] + [edge]
        assert len(support) == len(set(support))
        edge_code[support] ^= 1 << bit
        dual_certificates.append(support)
    face_parity = np.zeros(cap + 1, np.uint8)
    for edge, (a, b) in enumerate(dual_incidence):
        face_parity[a] ^= edge_code[edge]
        face_parity[b] ^= edge_code[edge]
    assert not face_parity.any()
    depth, up, _ = ancestor_table(parent, root, referenced)
    reference_cycles = []
    for edge in leftover:
        a, b = edge_vertices[edge]
        reference_cycles.append(cycle(a, b, edge, lca(a, b, depth, up), parent, parent_edge)[1])
    pairing = [[int(np.bitwise_xor.reduce(edge_code[edges]) >> bit & 1) for bit in range(2)] for edges in reference_cycles]
    assert pairing == [[1, 0], [0, 1]]
    seed_targets = {'cuff': xyz[boundary_vertices].mean(0), 'unclassifiedPalmCuff': xyz[referenced[labels[referenced] == 0]].mean(0)}
    for name, row in anatomy['digits'].items():
        seed_targets[name + 'ProximalHypothesis'] = np.array(row['sectionCenters'][0])
        seed_targets[name + 'DistalHypothesis'] = np.array(row['sectionCenters'][-1])
    for axis in range(3):
        for label, operation in [('Min', np.argmin), ('Max', np.argmax)]:
            vertex = referenced[operation(xyz[referenced, axis])]
            seed_targets[f'sourceAxis{axis}{label}'] = xyz[vertex]
    seeds = {name: int(referenced[np.argmin(((xyz[referenced] - target) ** 2).sum(1))]) for name, target in seed_targets.items()}
    best, seed_results = {}, []
    for seed in sorted(set(seeds.values())):
        dist, par, pe = tree(adjacency, seed, len(xyz))
        dep, table, order = ancestor_table(par, seed, referenced)
        code = np.zeros(len(xyz), np.uint8)
        for vertex in order[1:]:
            code[vertex] = code[par[vertex]] ^ edge_code[pe[vertex]]
        local = {}
        for edge, (a, b) in enumerate(edge_vertices):
            klass = int(code[a] ^ code[b] ^ edge_code[edge])
            if not klass:
                continue
            common = lca(a, b, dep, table)
            length = float(dist[a] + dist[b] - 2 * dist[common] + np.linalg.norm(xyz[a] - xyz[b]))
            key = (length, edge)
            if klass not in local or key < local[klass][0]:
                local[klass] = (key, a, b, common)
        assert set(local) == {1, 2, 3}
        seed_results.append({'sourceVertex': seed, 'bestLengthByClass': {str(k): v[0][0] for k, v in local.items()}})
        for klass, (key, a, b, common) in local.items():
            if klass in best and (key[0], seed, key[1]) >= best[klass]['selectionKey']:
                continue
            cv, ce = cycle(a, b, key[1], common, par, pe)
            assert int(np.bitwise_xor.reduce(edge_code[ce])) == klass
            assert all(tuple(sorted((cv[i], cv[(i + 1) % len(cv)]))) == edge_vertices[ce[i]] for i in range(len(cv)))
            points = xyz[cv]
            actual_length = float(np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1).sum())
            assert abs(actual_length - key[0]) < 1e-10
            incident = sorted({row for edge in ce for row in edge_rows[edge]})
            best[klass] = {'selectionKey': (key[0], seed, key[1]), 'homologyClass': klass, 'sourceVertexIds': cv, 'sourceEdges': [list(edge_vertices[e]) for e in ce], 'sourceXYZ': points.tolist(), 'lengthSourceUnits': actual_length, 'boundsSourceXYZ': [points.min(0).tolist(), points.max(0).tolist()], 'meanSourceXYZ': points.mean(0).tolist(), 'distalVertexLabelCounts': {str(k): int((labels[cv] == k).sum()) for k in range(6)}, 'incidentRetainedFaceRows': incident, 'incidentPrototypeFaceRows': source['sourcePrototypeFaceRows'][incident].tolist(), 'vertexDenseTriangleRows': source['originalTriangleRows'][cv].tolist(), 'vertexDenseBarycentric': source['barycentric'][cv].tolist(), 'distanceToCuffVerticesMinSourceUnits': float(np.sqrt(((points[:, None] - xyz[boundary_vertices]) ** 2).sum(2)).min()), 'nearestHypothesisDistancesSourceUnits': {name: float(np.linalg.norm(points - target, axis=1).min()) for name, target in seed_targets.items()}}
    assert all(sha(path) == expected for path, expected in pins) and sha(source_path) == source_hash
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    raw = out / 'homology-certificate.npz'
    np.savez_compressed(raw, sourceEdgeVertexIds=np.array(edge_vertices), dualIncidentFaceRows=np.array(dual_incidence), edgeCocycleCodes=edge_code, primalTreeEdges=np.array(sorted(primal)), dualTreeEdges=np.array(sorted(cotree)), leftoverEdges=np.array(leftover), referenceCycle0=np.array(reference_cycles[0]), referenceCycle1=np.array(reference_cycles[1]), virtualCuffBoundaryEdges=np.array(boundary))
    report = {'acceptedWearable': False, 'status': 'FINITE_SOURCE_SURFACE_HOMOLOGY_LOCALIZATION_ONLY', 'recipeSHA256': sha(__file__), 'opening': {'path': args.opening, 'sha256': args.opening_sha256}, 'source': {'path': source_path, 'sha256': source_hash}, 'anatomy': {'path': args.anatomy, 'sha256': args.anatomy_sha256}, 'rawCertificate': {'path': str(raw), 'sha256': sha(raw)}, 'virtualCell': {'sourceEdited': False, 'triangulatedOrSavedAsMesh': False, 'boundaryActualSourceEdges': 71, 'purpose': 'Algebraic cuff closure only; capped cell complex has Euler0 and genus1.'}, 'referencePairingGF2': pairing, 'faceBoundaryCocycleParityNonzero': int(np.count_nonzero(face_parity)), 'homologyRank': 2, 'seeds': seeds, 'seedResults': seed_results, 'localizedCycles': [best[k] for k in [1, 2, 3]], 'limits': ['Shortest selected fundamental source-edge cycle per homology class among the declared finite Dijkstra-root family; no globally shortest/geodesic claim.', 'Classes1and2 are independent; class3 is their sum over GF2. Dual cocycles and zero face parity certify non-boundaries on source topology.', 'Surface homology generators locate nontrivial source-edge neighborhoods; they do not prove a geometric through-passage, free cavity volume, mouth traversal, finger enclosure or wearable usability.', 'Distal labels1..5 are prior connectivity hypotheses; label0 combines unresolved palm, web and cuff. Nearby section centers are hypotheses, not joints or authored anatomy.', 'Lengths and XYZ use original uncalibrated donor units, never metres. No native/model/fit/skin/render/source edit or further cut.']}
    Path(args.evidence).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'roots': len(seed_results), 'cycleLengthsSourceUnits': {str(k): best[k]['lengthSourceUnits'] for k in best}}))


if __name__ == '__main__':
    main()
