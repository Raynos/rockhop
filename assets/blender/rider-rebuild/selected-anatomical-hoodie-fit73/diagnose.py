"""Bounded actual-array diagnosis; no native modification or fit acceptance."""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ORIGINAL = ROOT/'harness/out/rider-rebuild/selected-proximal-fit-review54/original01/actual-hoodie-geometry.npz'
BODY = ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09/reference05/original-full-reference.npz'
CURRENT = ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit72/transport01/complete/positions.npy'
CONTROLS = ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit65/component01/fixed-material-targets.npz'
G = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit65/geometry.py'))


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def proper_crossings(points, faces, selected):
    """Transverse edge/interior intersections, excluding geometric shared corners."""
    triangles = points[faces].astype(float)
    low, high = triangles.min(1), triangles.max(1)
    rows = []
    for face_id in selected:
        triangle = triangles[face_id]
        candidates = np.flatnonzero(np.all(high >= triangle.min(0), axis=1)
                                    & np.all(low <= triangle.max(0), axis=1))
        candidates = candidates[candidates != face_id]
        other = triangles[candidates]
        shared = np.any(np.all(triangle[:, None, None, :] == other[None, :, :, :], axis=3), axis=(0, 2))
        candidates = candidates[~shared]; other = other[~shared]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            origin = triangle[a]; direction = triangle[b]-origin
            e1, e2 = other[:, 1]-other[:, 0], other[:, 2]-other[:, 0]
            cross = np.cross(direction, e2); det = np.einsum('ij,ij->i', e1, cross)
            valid = det != 0; inv = 1/np.where(valid, det, 1)
            offset = origin-other[:, 0]; u = np.einsum('ij,ij->i', offset, cross)*inv
            q = np.cross(offset, e1); v = q@direction*inv
            distance = np.einsum('ij,ij->i', e2, q)*inv
            hit = valid & (u > 0) & (v > 0) & (u+v < 1) & (distance > 0) & (distance < 1)
            for index in np.flatnonzero(hit):
                rows.append({'face': int(face_id), 'otherFace': int(candidates[index]),
                             'edge': [a, b], 'edgeFraction': float(distance[index]),
                             'otherBarycentric': [float(1-u[index]-v[index]), float(u[index]), float(v[index])]})
    return rows


def main(output):
    output = Path(output).resolve(); assert output.is_relative_to(ROOT) and not output.exists()
    original = np.load(ORIGINAL); p, f = original['points'], original['faces']
    current = np.load(CURRENT, mmap_mode='r'); controls = np.load(CONTROLS)['controlSource']
    body = np.load(BODY); key = 'RiderBody__FullAnatomyReference'
    mesh = G['Mesh'](body[key+'_basis'], body[key+'_triangles'])
    ids = np.unique(np.r_[np.linspace(0, len(p)-1, 192, dtype=int), 255716])
    report = {'acceptedArt': False, 'status': 'BOUNDED_ACTUAL_SOURCE_DIAGNOSIS_ONLY',
              'inputs': {k: pin(v) for k, v in [('original47', ORIGINAL), ('current72', CURRENT), ('body', BODY), ('controls65', CONTROLS)]},
              'recipe': pin(Path(__file__).resolve()), 'sampleVertexIds': ids.tolist(), 'sampledContact': {}}
    for name, points in [('original47', p), ('current72', current)]:
        gap, body_faces = mesh.nearest(points[ids])
        report['sampledContact'][name] = {'deficientCount': int((gap < .00258).sum()),
            'insideCount': int((gap < 0).sum()), 'minimumM': float(gap.min()),
            'minimumNativeVertexId': int(ids[np.argmin(gap)])}
    unique, inverse = np.unique(p, axis=0, return_inverse=True)
    edges = np.unique(np.sort(np.concatenate([inverse[f[:, [0, 1]]], inverse[f[:, [1, 2]]], inverse[f[:, [2, 0]]]]), axis=1), axis=0)
    edges = edges[edges[:, 0] != edges[:, 1]]
    report['materialGraph'] = {'uniqueExactPositions': len(unique), 'nativeVertices': len(p),
        'nativeUVSplitDuplicates': len(p)-len(unique), 'edges': len(edges),
        'edgeLengthPercentilesM': np.percentile(np.linalg.norm(unique[edges[:, 0]]-unique[edges[:, 1]], axis=1), [0, 1, 50, 99, 100]).tolist(),
        'weldPolicy': 'Exact identical source positions only; native topology/UV/skin never welded'}
    report['worst72Witness'] = {'nativeVertexId': 255716, 'sourcePoint': p[255716].tolist(),
        'currentPoint': current[255716].tolist(),
        'nearestSourceControlDistanceM': float(np.linalg.norm(controls-p[255716], axis=1).min())}
    selected = np.unique(np.r_[np.linspace(0, len(f)-1, 192, dtype=int),
                              np.flatnonzero(np.any(f == 255716, axis=1)), 734276, 729981])
    report['properCrossings'] = {'testedSourceFaces': selected.tolist(),
        'method': 'All source triangles AABB candidates, strict transverse segment/interior tests, shared geometric corners excluded',
        'witnesses': proper_crossings(p, f, selected)}
    source_mesh = G['Mesh'](p, f); pairs = []
    for face_id in selected[::8]:
        triangle = p[f[face_id]].astype(float); center = triangle.mean(0)
        normal = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0]); length = np.linalg.norm(normal)
        if not length: continue
        normal /= length; precision = float(np.spacing(np.float32(max(abs(p).max(), 1.))))
        hits = source_mesh.ray_hits(center-normal*precision, -normal)
        hits = [h for h in hits if h[2] != face_id]
        pairs.append({'sourceFace': int(face_id), 'firstHit': None if not hits else
            {'distanceM': hits[0][0]+precision, 'outwardDotRay': hits[0][1],
             'sourceFace': hits[0][2], 'barycentric': hits[0][3]}})
    report['boundedInwardWallRays'] = pairs
    report['limits'] = ['193 vertices and bounded triangles/rays diagnose source; complete contact/self checks still required.',
                        'No fit, native construction, art, animation or game acceptance.']
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'report': pin(output), 'crossingWitnesses': len(report['properCrossings']['witnesses']),
                      'wallRayCount': len(pairs), 'contact': report['sampledContact']}))


if __name__ == '__main__': main(sys.argv[1])
