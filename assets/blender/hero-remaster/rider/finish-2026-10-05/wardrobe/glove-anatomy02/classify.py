"""Connectivity-derived five donor branches; no glove fitting or bone edits."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def components(vertices, faces, threshold):
    mask = vertices[:, 1] > threshold
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    edges = edges[mask[edges].all(1)]
    adjacency = coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(len(vertices), len(vertices)))
    _, labels = connected_components(adjacency, directed=False)
    groups = [np.flatnonzero(mask & (labels == label)) for label in np.unique(labels[mask])]
    return sorted([group for group in groups if len(group) > 20], key=lambda group: vertices[group, 0].mean())


def section(vertices, faces, group, axis, station):
    active = np.zeros(len(vertices), bool)
    active[group] = True
    relevant = faces[active[faces].any(1)]
    edges = np.unique(np.sort(np.concatenate([relevant[:, [0, 1]], relevant[:, [1, 2]], relevant[:, [2, 0]]]), axis=1), axis=0)
    start, end = vertices[edges[:, 0]], vertices[edges[:, 1]]
    a, b = (start * axis).sum(1) - station, (end * axis).sum(1) - station
    crossed = (a * b < 0) & (abs(a - b) > 1e-12)
    hits = start[crossed] + (end[crossed] - start[crossed]) * (a[crossed] / (a[crossed] - b[crossed]))[:, None]
    assert len(hits) > 3
    # Midpoint of the section's coordinate bounds, not an anatomical joint claim.
    return (hits.min(0) + hits.max(0)) / 2, hits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--previous', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--evidence', required=True)
    args = parser.parse_args()
    source = np.load(args.source)
    vertices, faces = source['vertices'], source['faces']
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    previous = json.loads(Path(args.previous).read_text())['gloves']['digits']
    four = components(vertices, faces, .2)
    assert len(four) == 4
    thumb_candidates = components(vertices, faces, -.1)
    assert len(thumb_candidates) == 2
    thumb = max(thumb_candidates, key=lambda group: vertices[group, 0].mean())
    assert vertices[thumb, 0].min() > .3
    labels = np.zeros(len(vertices), np.uint8)
    records = {}
    for index, (name, group) in enumerate(zip(['pinky', 'ring', 'middle', 'index', 'thumb'], four + [thumb]), 1):
        labels[group] = index
        branch = vertices[group]
        if name != 'thumb':
            axis = np.array([0., 1., 0.])
            start, end = .21, float(branch[:, 1].max() - .012)
        else:
            # Thumb is a distinct connectivity component below the long-digit roots.
            axis = np.array([1., .55, 0.])
            axis /= np.linalg.norm(axis)
            projection = (branch * axis).sum(1)
            start, end = float(np.quantile(projection, .08)), float(projection.max() - .012)
        stations = np.linspace(start, end, 4)
        knots = np.array([section(vertices, faces, group, axis, station)[0] for station in stations])
        old_tip = np.array(previous[name]['tip'])
        distance = float(np.linalg.norm(branch - old_tip, axis=1).min())
        nearest_name = min(zip(['pinky', 'ring', 'middle', 'index', 'thumb'], four + [thumb]), key=lambda row: np.linalg.norm(vertices[row[1]] - old_tip, axis=1).min())[0]
        records[name] = {'regionId': index, 'vertices': len(group), 'bounds': [branch.min(0).tolist(), branch.max(0).tolist()],
                         'axis': axis.tolist(), 'sectionStations': stations.tolist(), 'sectionCenters': knots.tolist(),
                         'previousTip': old_tip.tolist(), 'previousTipNearestOwnBranchDistanceSourceUnits': distance,
                         'previousTipNearestConnectivityBranch': nearest_name,
                         'limits': 'Section centers are geometric fitting hypotheses, not anatomical source joints. Proximal palm/web attachment remains unclassified.'}
    np.savez_compressed(out / 'branches.npz', vertices=vertices, faces=faces, branchLabels=labels,
                        uv=source['uv'], originalTriangleRows=source['originalTriangleRows'], barycentric=source['barycentric'])
    assert np.isfinite(vertices).all() and all(np.isfinite(np.array(row['sectionCenters'])).all() for row in records.values())
    report = {'accepted': False, 'status': 'SOURCE_BRANCH_CORRESPONDENCE_CHECKPOINT_UNACCEPTED',
              'recipeSHA256': sha(__file__), 'source': {'path': args.source, 'sha256': sha(args.source)},
              'previousSemantics': {'path': args.previous, 'sha256': sha(args.previous)},
              'output': {'path': str(out / 'branches.npz'), 'sha256': sha(out / 'branches.npz')},
              'sourceXYZFacesUVLineageExact': all(np.array_equal(source[key], np.load(out / 'branches.npz')[key]) for key in ['vertices', 'faces', 'uv', 'originalTriangleRows', 'barycentric']),
              'connectedLongDigitsAtY020': 4, 'separatedThumbAtYMinus010': True, 'digits': records,
              'limits': ['Distal connectivity only; palm, cuff, proximal roots and source handedness still require author interpretation.',
                         'No fitting, skinning, model inference, original source edit, bind change, body change or player promotion.']}
    (evidence / 'classification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'branches': {name: {'vertices': row['vertices'], 'oldTipNearest': row['previousTipNearestConnectivityBranch'], 'ownDistance': row['previousTipNearestOwnBranchDistanceSourceUnits']} for name, row in records.items()}}))


if __name__ == '__main__':
    main()
