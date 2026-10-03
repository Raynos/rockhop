"""Report native decoder geometry witnesses without repairing or accepting it."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def audit(vertices, faces):
    report = {'accepted': False, 'vertices': vertices.shape[0] if vertices.ndim else 0,
              'faces': faces.shape[0] if faces.ndim else 0,
              'vertexDtype': str(vertices.dtype), 'faceDtype': str(faces.dtype),
              'validGeometryArrays': False,
              'limits': ['No self-intersection, anatomy, garment opening, fit or motion test.',
                         'Boundary counts do not classify intentional clothing openings.']}
    if vertices.ndim != 2 or vertices.shape[1] != 3 or faces.ndim != 2 or faces.shape[1] != 3:
        report['error'] = 'Expected vertex/triangle arrays with three columns'
        return report
    report['nonfiniteVertexElements'] = int((~np.isfinite(vertices)).sum())
    if not len(vertices) or not len(faces) or not np.issubdtype(faces.dtype, np.integer):
        report['error'] = 'Empty geometry or non-integer native indices'
        return report
    report['invalidIndexElements'] = int(((faces < 0) | (faces >= len(vertices))).sum())
    if report['nonfiniteVertexElements'] or report['invalidIndexElements']:
        report['error'] = 'Nonfinite vertices or out-of-range indices; raw retained'
        return report
    report['validGeometryArrays'] = True
    v = vertices.astype(np.float64)
    report['boundsNative'] = [v.min(axis=0).tolist(), v.max(axis=0).tolist()]
    repeated = (faces[:, 0] == faces[:, 1]) | (faces[:, 1] == faces[:, 2]) | (faces[:, 2] == faces[:, 0])
    report['repeatedIndexTriangles'] = int(repeated.sum())
    cross = np.cross(v[faces[:, 1]] - v[faces[:, 0]], v[faces[:, 2]] - v[faces[:, 0]])
    area = np.linalg.norm(cross, axis=1) / 2
    report['zeroAreaTriangles'] = int((area == 0).sum())
    report['minimumAreaNativeSquaredUnits'] = float(area.min())
    report['duplicateTrianglesIgnoringWinding'] = int(len(faces) - len(np.unique(np.sort(faces, axis=1), axis=0)))
    directed = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    edges, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0,
                                       return_inverse=True, return_counts=True)
    orientation = np.where(directed[:, 0] < directed[:, 1], 1, -1)
    balance = np.bincount(inverse, weights=orientation, minlength=len(edges))
    report.update(uniqueEdges=len(edges), boundaryEdges=int((counts == 1).sum()),
                  overusedEdges=int((counts > 2).sum()),
                  equalDirectionTwoFaceEdges=int(((counts == 2) & (np.abs(balance) == 2)).sum()))
    used = np.unique(faces)
    report['unusedVertices'] = int(len(vertices) - len(used))
    parent = np.arange(len(vertices))

    def root(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = int(parent[node])
        return node

    for left, right in edges:
        left, right = root(int(left)), root(int(right))
        if left != right:
            parent[right] = left
    labels = np.array([root(int(i)) for i in faces[:, 0]])
    _, component_faces = np.unique(labels, return_counts=True)
    report['vertexConnectedFaceComponents'] = len(component_faces)
    report['componentTriangleCountsDescending'] = sorted(map(int, component_faces), reverse=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    source = Path(args.archive)
    with np.load(source, allow_pickle=False) as raw:
        report = audit(raw['vertices'], raw['faces'])
    report.update(source=str(source), sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  auditSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    Path(args.out).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return 0 if report['validGeometryArrays'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
