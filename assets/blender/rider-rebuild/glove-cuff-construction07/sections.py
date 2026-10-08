"""Read existing selected topology; section planes are diagnostics, not cuts."""
import numpy as np


def section_loops(source, current, faces, ordinate):
    """Ordered intersected-edge loops with exact source/current interpolation.

    Use immutable source Y to identify material, avoiding a guessed fitted-world
    cut across folded layers. The current section can be nonplanar.
    """
    nodes, adjacency = {}, {}
    for face in faces:
        crossings = []
        for a, b in zip(face, np.roll(face, -1)):
            if (source[a, 1] < ordinate) == (source[b, 1] < ordinate):
                continue
            key = tuple(sorted((int(a), int(b))))
            a, b = key
            fraction = (ordinate-source[a, 1])/(source[b, 1]-source[a, 1])
            nodes[key] = (float(fraction), source[a]+fraction*(source[b]-source[a]),
                          current[a]+fraction*(current[b]-current[a]))
            crossings.append(key)
        assert len(crossings) in (0, 2), 'Section passes through a source vertex'
        if len(crossings) == 2:
            a, b = crossings
            adjacency.setdefault(a, []).append(b)
            adjacency.setdefault(b, []).append(a)
    assert all(len(n) == 2 for n in adjacency.values()), 'Section is not closed'
    remaining, loops = set(nodes), []
    while remaining:
        start = min(remaining)
        ordered, previous, node = [], None, start
        while node not in ordered:
            ordered.append(node)
            other = sorted(n for n in adjacency[node] if n != previous)[0]
            previous, node = node, other
        assert node == start, 'Section contains a branched component'
        remaining.difference_update(ordered)
        original = np.asarray([nodes[n][1] for n in ordered])
        fitted = np.asarray([nodes[n][2] for n in ordered])
        planar = original[:, [0, 2]]
        area = .5*np.sum(planar[:, 0]*np.roll(planar[:, 1], -1)
                         -planar[:, 1]*np.roll(planar[:, 0], -1))
        loops.append({'sourceEdges': np.asarray(ordered, dtype=np.int32),
                      'edgeFractions': np.asarray([nodes[n][0] for n in ordered]),
                      'originalXYZ': original, 'currentWorldXYZ': fitted,
                      'sourcePlaneSignedArea': float(area)})
    return sorted(loops, key=lambda row: -abs(row['sourcePlaneSignedArea']))


def topology(vertices, faces):
    edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]],
                                    faces[:, [2, 0]]]), axis=1)
    unique, incidence = np.unique(edges, axis=0, return_counts=True)
    area = np.linalg.norm(np.cross(vertices[faces[:, 1]]-vertices[faces[:, 0]],
                                   vertices[faces[:, 2]]-vertices[faces[:, 0]]), axis=1)/2
    counts, multiplicities = np.unique(incidence, return_counts=True)
    return {'vertices': len(vertices), 'triangles': len(faces),
            'edges': len(unique), 'eulerCharacteristic': len(vertices)-len(unique)+len(faces),
            'edgeIncidence': dict(zip(map(str, counts), map(int, multiplicities))),
            'minimumTriangleArea': float(area.min()),
            'zeroAreaTriangles': int(np.sum(area == 0)),
            'limits': 'Euler characteristic alone does not classify a physical cuff wall.'}
