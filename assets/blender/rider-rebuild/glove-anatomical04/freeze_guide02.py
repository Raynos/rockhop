"""Freeze one selected-source guide and303 uniquely owned handles per side."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def pin(path):
    path = Path(path)
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    source_controls = HERE / 'controls-orientation02.json'
    controls = json.loads(source_controls.read_text())
    path = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/gloves/retopology-prototype.npz'
    data = np.load(path)
    points, faces = data['vertices'].astype(np.float32), data['faces']
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    edges.sort(1)
    edges, counts = np.unique(edges, axis=0, return_counts=True)
    assert np.all(counts == 2)
    parent = list(range(len(points)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b in edges.tolist():
        a, b = root(a), root(b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    assert len(set(root(i) for i in range(len(points)))) == 1
    cross = np.linalg.norm(np.cross(points[faces[:, 1]] - points[faces[:, 0]],
                                    points[faces[:, 2]] - points[faces[:, 0]]), axis=1)
    assert np.all(cross > np.finfo(np.float32).eps)
    edge_sum = sum(np.sum((points[faces[:, (i + 1) % 3]] - points[faces[:, i]]) ** 2, axis=1) for i in range(3))
    quality = 2 * np.sqrt(3) * cross / edge_sum
    result = {'acceptedArt': False, 'stage': 'FROZEN_SELECTED_GUIDE_REMEDY_NOT_EXECUTED',
              'sourceControls': pin(source_controls), 'selectedGuide': pin(path),
              'previousAuthorHelpers': pin(HERE / 'author.py'), 'hands': {},
              'guideValidation': {'vertices': len(points), 'triangles': len(faces),
                                  'connectedComponents': 1, 'allEdgesUsedTwice': True,
                                  'trianglesSuppressedByBlenderFloatEpsilon': 0,
                                  'zeroActiveIncidentVertices': 0,
                                  'minimumTriangleQuality': float(quality.min()),
                                  'minimumTriangleCrossMagnitudeSourceUnits': float(cross.min()),
                                  'originalSelectedSurfaceProjectionMaximum': float(data['projectionDistances'].max())},
              'coordinateContract': 'Guide/dense bind and solve in original source units; one equal object placement for both.'}
    for side in ('R', 'L'):
        handles = controls['hands'][side]['handles']
        source = np.asarray([h['sourceRest'] for h in handles])
        distance = np.linalg.norm(source[:, None, :] - points[None, :, :], axis=2)
        # One deterministic nearest-unclaimed guide vertex per actual handle.
        # Source coordinates are reference positions, never fitted point fields.
        ownership, used = {}, set()
        for flat in np.argsort(distance, axis=None):
            handle_id, vertex_id = divmod(int(flat), len(points))
            if handle_id not in ownership and vertex_id not in used:
                ownership[handle_id] = vertex_id
                used.add(vertex_id)
                if len(ownership) == len(handles):
                    break
        assert len(ownership) == len(handles) == len(used) == 303
        placement = controls['hands'][side]['initialPlacement']
        linear, translation = np.asarray(placement['linear']), np.asarray(placement['translation'])
        inverse = np.linalg.inv(linear)
        rows = []
        for i, handle in enumerate(handles):
            vertex_id = ownership[i]
            target = inverse @ (np.asarray(handle['targetWorld']) - translation)
            rows.append({'label': handle['label'], 'selectedSourceVertex': handle['sourceVertex'],
                         'guideVertex': vertex_id, 'guideOriginalSourcePosition': points[vertex_id].tolist(),
                         'sourceHandleToGuideDistance': float(distance[i, vertex_id]),
                         'targetOriginalSourceFrame': target.tolist(), 'targetWorld': handle['targetWorld']})
        result['hands'][side] = {'handles': rows, 'distinctGuideVertexOwnership': True,
                                 'maximumSourceHandleToGuideDistance': max(r['sourceHandleToGuideDistance'] for r in rows)}
    out = HERE / 'guide-controls02.json'
    assert not out.exists()
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'controls': pin(out), 'guideValidation': result['guideValidation'],
                      'maximumAnchorDistance': {s: result['hands'][s]['maximumSourceHandleToGuideDistance'] for s in ('R', 'L')}}))


if __name__ == '__main__':
    main()
