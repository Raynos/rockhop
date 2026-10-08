"""Freeze explicit selected support IDs/fields and source geometry diagrams.

Read-only source extraction; no Blender, pose solve, mesh or controller write.
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def pin(row):
    path = ROOT / row['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['path']
    return path


def disk(triangles):
    edges = Counter(tuple(sorted((int(a), int(b)))) for face in triangles
                    for a, b in zip(face, np.roll(face, -1)))
    assert max(edges.values()) == 2
    graph = defaultdict(set)
    for a, b in edges:
        graph[a].add(b); graph[b].add(a)
    seen, pending = set(), [next(iter(graph))]
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node); pending.extend(graph[node] - seen)
    assert len(seen) == len(graph)
    assert len(graph) - len(edges) + len(triangles) == 1
    boundary = [edge for edge, count in edges.items() if count == 1]
    degree = Counter(v for edge in boundary for v in edge)
    assert set(degree.values()) == {2}
    return boundary


def main():
    out = Path(sys.argv[1]).resolve()
    assert out.is_relative_to(ROOT / 'docs/evidence/rider-rebuild/selected-posterior-support03')
    assert not out.exists()
    config = json.loads((HERE / 'patches.json').read_text())
    lineage = json.loads(pin(config['lineage']).read_text())
    body, fields = np.load(pin(config['body'])), np.load(pin(config['fields']))
    names = fields['jointNames'].tolist()
    positions = dict(lineage['nativeRestPositions'])
    rows = lineage['nativeTriangles']
    result = {'accepted': False, 'classification': config['classification'],
              'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'definitionSHA256': hashlib.sha256((HERE / 'patches.json').read_bytes()).hexdigest(),
              'sources': {k: config[k] for k in ('lineage', 'body', 'fields')},
              'selection': config['selection'], 'offlineSupportProxies': config['offlineSupportProxies'],
              'patches': {}}
    for side, sign in (('left', 1), ('right', -1)):
        definition = config[side]
        row = {}
        for kind in ('context', 'core'):
            ids = set(definition[kind + 'PolygonIds'])
            selected = [r for r in rows if r['originalPolygonID'] in ids]
            assert len(selected) == len(ids)*2
            triangles = np.array([r['nativeVertexIDs'] for r in selected])
            vertices = sorted(set(triangles.ravel().tolist()))
            points = np.array([positions[i] for i in vertices])
            assert np.all(points[:, 0]*sign > 0)
            surface = np.array([[positions[i] for i in face] for face in triangles])
            normals = np.cross(surface[:, 1]-surface[:, 0], surface[:, 2]-surface[:, 0])
            areas = np.linalg.norm(normals, axis=1)/2
            normals /= (2*areas[:, None])
            assert np.all(areas > 0) and np.all(normals[:, 1] > 0) and np.all(normals[:, 2] < 0)
            boundary = disk(triangles)
            row[kind] = {'originalPolygonIds': sorted(ids), 'triangles': selected,
                         'nativeVertices': [{'id': i, 'sourceXYZ': positions[i],
                            'namedFour': [[name, float(fields['fourCoefficients'][i, j])]
                                          for j, name in enumerate(names) if fields['fourCoefficients'][i, j] > 0]}
                                           for i in vertices],
                         'boundaryNativeEdges': boundary, 'connectedDisk': True,
                         'sourceAreaM2': float(areas.sum()),
                         'sourceAreaCentroidXYZ': np.average(surface.mean(1), axis=0, weights=areas).tolist(),
                         'sourceBoundsXYZ': [points.min(0).tolist(), points.max(0).tolist()],
                         'sourceNormalBoundsXYZ': [normals.min(0).tolist(), normals.max(0).tolist()]}
        row['bodyReferenceTriangles'] = [{'faceId': int(i), 'nativeVertexIds': body['faces'][i].tolist(),
                                        'sourceXYZ': body['vertices'][body['faces'][i]].tolist(),
                                        'originalSourcePolygonId': int(body['sourcePolygonRows'][i])}
                                       for i in definition['bodyReferenceFaceIds']]
        result['patches'][side] = row
    out.write_text(json.dumps(result, indent=2) + '\n')

    fig, axes = plt.subplots(1, 3, figsize=(11, 4.5), constrained_layout=True)
    projections = [(0, 2, 'Back: source X / Z'), (1, 2, 'Profile: source Y / Z'), (0, 1, 'Below: source X / Y')]
    all_triangles = np.array([[positions[i] for i in row['nativeVertexIDs']] for row in rows])
    for ax, (a, b, title) in zip(axes, projections):
        ax.add_collection(PolyCollection(all_triangles[:, :, [a, b]], facecolors='#dde8ed', edgecolors='#acbcc4', linewidths=.25))
        for side, color in [('left', '#e8a44d'), ('right', '#42a7ae')]:
            patch = result['patches'][side]
            for kind, opacity in [('context', .45), ('core', 1.)]:
                tri = np.array([[positions[i] for i in row['nativeVertexIDs']] for row in patch[kind]['triangles']])
                ax.add_collection(PolyCollection(tri[:, :, [a, b]], facecolors=color, edgecolors='#333333', linewidths=.5, alpha=opacity))
            centroid = patch['core']['sourceAreaCentroidXYZ']
            ax.plot(centroid[a], centroid[b], 'ko', ms=3)
        ax.autoscale(); ax.set_aspect('equal'); ax.set_title(title); ax.grid(alpha=.15)
    axes[0].set_xlim(-.13, .13); axes[0].set_ylim(.81, .96)
    axes[1].set_xlim(.045, .155); axes[1].set_ylim(.81, .96)
    axes[2].set_xlim(-.13, .13); axes[2].set_ylim(.05, .155)
    fig.suptitle('Authored lower-gluteal candidates: solid = medial core; translucent = context\nSource diagram only; no seated-pose or art acceptance')
    image = out.with_suffix('.png'); assert not image.exists()
    fig.savefig(image, dpi=140)
    print(json.dumps({'output': str(out.relative_to(ROOT)), 'image': str(image.relative_to(ROOT)),
        'patches': {side: {kind: {'polygons': len(row[kind]['originalPolygonIds']),
             'triangles': len(row[kind]['triangles']), 'vertices': len(row[kind]['nativeVertices']),
             'areaM2': row[kind]['sourceAreaM2'], 'centroid': row[kind]['sourceAreaCentroidXYZ']}
             for kind in ('context', 'core')} for side, row in result['patches'].items()}}, indent=2))


if __name__ == '__main__':
    main()
