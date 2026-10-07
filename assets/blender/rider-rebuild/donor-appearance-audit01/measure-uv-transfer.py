"""Read-only dense UV chart/compact triangle audit; no bpy, scene or model writes."""
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02'
LINEAGE = ROOT / 'harness/out/rider-rebuild/construction02/selected-wardrobe01/actual-donor-wardrobe/jeans-source-corner-lineage.json'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()

def uv_charts(faces, uv):
    """Join source faces only across shared geometric edges with matching endpoint UV."""
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    corner_uv = np.concatenate([uv[:, [0, 1]], uv[:, [1, 2]], uv[:, [2, 0]]])
    owners = np.tile(np.arange(len(faces)), 3)
    reverse = edges[:, 0] > edges[:, 1]
    edges[reverse] = edges[reverse, ::-1]
    corner_uv[reverse] = corner_uv[reverse, ::-1]
    keys = edges[:, 0] * (int(faces.max()) + 1) + edges[:, 1]
    order = np.argsort(keys, kind='stable')
    keys, owners, corner_uv = keys[order], owners[order], corner_uv[order]
    starts = np.r_[0, np.flatnonzero(np.diff(keys)) + 1]
    lengths = np.diff(np.r_[starts, len(keys)])
    pairs = starts[lengths == 2]
    uv_error = np.max(np.abs(corner_uv[pairs].astype(np.float64) - corner_uv[pairs + 1]), axis=(1, 2))
    continuous = uv_error <= 1e-6
    a, b = owners[pairs[continuous]], owners[pairs[continuous] + 1]
    graph = coo_matrix((np.ones(len(a), dtype=np.uint8), (a, b)), shape=(len(faces), len(faces))).tocsr()
    count, labels = connected_components(graph, directed=False)
    return labels, {'connectedUVCharts': int(count), 'chartEndpointToleranceUV': 1e-6,
                    'sharedGeometricEdges': int(len(pairs)), 'UVSeamEdges': int(np.sum(~continuous)),
                    'boundaryGeometricEdges': int(np.sum(lengths == 1)), 'nonmanifoldGeometricEdges': int(np.sum(lengths > 2))}

def closest_candidates(points, triangles):
    """Closest barycentrics for every point/candidate triangle in float64."""
    a, b, c = (triangles[:, :, i] for i in range(3))
    ab, ac, ap = b - a, c - a, points[:, None] - a
    normal = np.cross(ab, ac)
    denom = np.sum(normal * normal, axis=2)
    safe = np.maximum(denom, 1e-30)
    v = np.sum(np.cross(ap, ac) * normal, axis=2) / safe
    w = np.sum(np.cross(ab, ap) * normal, axis=2) / safe
    bary = np.stack([1 - v - w, v, w], axis=2)
    projected = np.sum(triangles * bary[:, :, :, None], axis=2)
    distances = np.sum((projected - points[:, None]) ** 2, axis=2)
    valid = (np.min(bary, axis=2) >= 0) & (denom > 1e-30)
    distances[~valid] = np.inf
    for ia, ib in ((0, 1), (1, 2), (2, 0)):
        pa, pb = triangles[:, :, ia], triangles[:, :, ib]
        edge = pb - pa
        t = np.clip(np.sum((points[:, None] - pa) * edge, axis=2) / np.maximum(np.sum(edge * edge, axis=2), 1e-30), 0, 1)
        q = pa + edge * t[:, :, None]
        d = np.sum((q - points[:, None]) ** 2, axis=2)
        better = d < distances
        replacement = np.zeros_like(bary)
        replacement[:, :, ia], replacement[:, :, ib] = 1 - t, t
        bary[better] = replacement[better]
        distances[better] = d[better]
    best = distances.argmin(axis=1)
    return best, bary[np.arange(len(points)), best], np.sqrt(distances[np.arange(len(points)), best])

def nearest_sample(tree, dense_v, dense_f, points, k=32):
    _, candidates = tree.query(points, k=k, workers=1)
    best, bary, distance = closest_candidates(points, dense_v[dense_f[candidates]].astype(np.float64))
    return candidates[np.arange(len(points)), best], bary, distance

def summaries(values):
    return {label: float(value) for label, value in zip(['minimum', 'median', 'p95', 'p99', 'maximum'],
        np.quantile(values, [0, .5, .95, .99, 1]))}

def executed_jeans_uv(corner_uv):
    """Read exported per-loop IDs so the measured lineage is tied to actual GPU UV."""
    source = ROOT / 'harness/out/rider-rebuild/construction02/selected-wardrobe01/rider.glb'
    raw = source.read_bytes(); size = struct.unpack_from('<I', raw, 12)[0]
    document, binary = json.loads(raw[20:20+size]), raw[28+size:]
    def accessor(index):
        row = document['accessors'][index]; view = document['bufferViews'][row['bufferView']]
        fmt = '<' + {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[row['componentType']] * {'SCALAR': 1, 'VEC2': 2}[row['type']]
        base = view.get('byteOffset', 0) + row.get('byteOffset', 0)
        stride = view.get('byteStride', struct.calcsize(fmt))
        return [struct.unpack_from(fmt, binary, base+i*stride) for i in range(row['count'])]
    node = next(n for n in document['nodes'] if n.get('name') == 'RiderJeans')
    rows = {}
    for primitive in document['meshes'][node['mesh']]['primitives']:
        attrs = primitive['attributes']
        for identity, uv in zip(accessor(attrs['_CORNER_ID']), accessor(attrs['TEXCOORD_0'])):
            key = int(identity[0]); assert key not in rows or rows[key] == uv
            rows[key] = uv
    assert set(rows) == set(range(corner_uv.size // 2))
    actual = np.asarray([rows[i] for i in range(len(rows))], dtype=np.float32)
    expected = corner_uv.reshape(-1, 2).astype(np.float32)
    expected[:, 1] = 1 - expected[:, 1]
    error = float(np.max(np.abs(expected - actual)))
    assert error <= 1e-7
    return {'path': str(source), 'sha256': sha(source), 'sourceCornerIDsCount': len(rows),
            'allRecordedCornerIDsPresent': True, 'originalLineageVsExecutedGLTFUVMaximumError': error,
            'exactFloat32ArraysEqual': bool(np.array_equal(expected, actual)), 'gltfVConvention': '1-nativeV'}

def main(output):
    assert not output.exists(), 'Preserve previous measured evidence'
    results, witnesses = {}, {}
    for item in ('jeans', 'boots'):
        folder = PREP / item
        dense = dict(np.load(folder / 'cleaned-donor.npz'))
        compact = dict(np.load(folder / 'retopology-prototype.npz'))
        dv, df, duv = dense['vertices'], dense['faces'], dense['originalCornerUV']
        cv, cf = compact['vertices'], compact['faces']
        chart, chart_stats = uv_charts(df, duv)
        tree = cKDTree(dv[df].mean(axis=1))
        if item == 'jeans':
            ancestry = json.loads(LINEAGE.read_text())
            assert ancestry['sourceSHA256'] == sha(folder / 'cleaned-donor.npz')
            assert len(ancestry['corners']) == len(cf)
            source_faces = np.asarray([[c['sourceChartFace'] for c in row] for row in ancestry['corners']])
            bary = np.asarray([[c['barycentric'] for c in row] for row in ancestry['corners']])
            mapped_uv = np.sum(duv[source_faces] * bary[:, :, :, None], axis=2)
            map_scope = 'EXACT executed jeans source-corner lineage; no UV regeneration'
        else:
            # Original compact vertex ancestry is independently stored. This is
            # NOT the executed Blender per-corner BVH mapping, which was not saved.
            lookup = {int(row): i for i, row in enumerate(dense['originalTriangleRows'])}
            face_rows = np.asarray([lookup[int(row)] for row in compact['originalTriangleRows']])
            source_faces = face_rows[cf]
            bary = compact['barycentric'][cf]
            mapped_uv = np.sum(duv[source_faces] * bary[:, :, :, None], axis=2)
            map_scope = 'Prototype vertex source ancestry only; executed boot per-corner BVH mapping is UNMEASURED'
        corner_charts = chart[source_faces]
        mixed = np.any(corner_charts != corner_charts[:, :1], axis=1)
        def area(uv):
            a, b = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
            return np.abs(a[:, 0]*b[:, 1] - a[:, 1]*b[:, 0]) * .5
        source_uv_area, compact_uv_area = area(duv), area(mapped_uv)
        # Centre mapping discrepancy detects incompatible source patches even when
        # all corners themselves lie inside their own tiny source triangles.
        points = cv[cf].mean(axis=1)
        hit_rows, hit_bary, hit_distances = [], [], []
        for begin in range(0, len(points), 512):
            row, weights, distance = nearest_sample(tree, dv, df, points[begin:begin + 512])
            hit_rows.append(row); hit_bary.append(weights); hit_distances.append(distance)
        centre_face, centre_bary, centre_distance = np.concatenate(hit_rows), np.concatenate(hit_bary), np.concatenate(hit_distances)
        centre_uv = np.sum(duv[centre_face] * centre_bary[:, :, None], axis=1)
        predicted_uv = mapped_uv.mean(axis=1)
        errors_px = np.linalg.norm(centre_uv - predicted_uv, axis=1) * 4096
        # Raster colours isolate mapping from lighting and body interpenetration.
        texture = np.asarray(Image.open(folder / 'baseColorTexture.png').convert('RGB'))
        def colour(uv):
            xy = np.rint(np.clip(uv, 0, 1) * np.asarray([texture.shape[1] - 1, texture.shape[0] - 1])).astype(int)
            return texture[texture.shape[0] - 1 - xy[:, 1], xy[:, 0]].astype(float)
        colour_error = np.linalg.norm(colour(centre_uv) - colour(predicted_uv), axis=1)
        severe = errors_px > 32
        stats = {'accepted': False, 'scope': map_scope, 'denseVertices': len(dv), 'denseFaces': len(df),
                 'compactVertices': len(cv), 'compactFaces': len(cf), 'denseUVChartTopology': chart_stats,
                 'compactFacesWhoseCornersBorrowDifferentUVCharts': int(mixed.sum()),
                 'mixedChartFaceFraction': float(mixed.mean()),
                 'compactUVTriangleArea': summaries(compact_uv_area), 'denseUVTriangleArea': summaries(source_uv_area),
                 'compactFaceCentreToSourceDistanceInSourceUnits': summaries(centre_distance),
                 'centreUVLinearInterpolationErrorPixelsAt4096': summaries(errors_px),
                 'centreErrorsOver32Pixels': int(severe.sum()),
                 'centreRGBErrorByteEuclidean': summaries(colour_error),
                 'RGBErrorsOver30Of255Euclidean': int((colour_error > 30).sum()),
                 'centreNearestMethod': 'Closest point among 32 nearest dense triangle centroids, chunk512; sampled diagnostic, not certified global BVH.',
                 'sources': {name: {'path': str(folder / name), 'sha256': sha(folder / name)} for name in
                             ('cleaned-donor.npz', 'retopology-prototype.npz', 'baseColorTexture.png')},
                 'limits': ['Chart mixing is a strict seam incompatibility for existing original atlas interpolation.',
                            'Centre sampling also includes compact geometry chord error and possible nearest-sheet ambiguity.',
                            'No native/export/player/material source was modified; this is not moving art acceptance.']}
        if item == 'jeans':
            stats['executedLineage'] = {'path': str(LINEAGE), 'sha256': sha(LINEAGE)}
            stats['executedGLTFUV'] = executed_jeans_uv(mapped_uv)
        results[item] = stats
        witnesses[item + '_corner_source_faces'] = source_faces
        witnesses[item + '_corner_source_charts'] = corner_charts
        witnesses[item + '_corner_uv'] = mapped_uv
        witnesses[item + '_centre_source_faces'] = centre_face
        witnesses[item + '_centre_source_barycentric'] = centre_bary
        witnesses[item + '_centre_uv_linear_error_pixels'] = errors_px
        witnesses[item + '_centre_rgb_error'] = colour_error
        print(item, json.dumps({k: v for k, v in stats.items() if k in
              ('compactFacesWhoseCornersBorrowDifferentUVCharts', 'mixedChartFaceFraction', 'centreUVLinearInterpolationErrorPixelsAt4096', 'centreRGBErrorByteEuclidean')}))
    output.mkdir(parents=True)
    np.savez_compressed(output / 'witnesses.npz', **witnesses)
    report = {'accepted': False, 'kind': 'Read-only original dense UV chart and compact interpolation audit',
              'recipeSHA256': sha(__file__), 'items': results, 'witnessesSHA256': sha(output / 'witnesses.npz')}
    (output / 'measurements.json').write_text(json.dumps(report, indent=2) + '\n')

if __name__ == '__main__': main(Path(sys.argv[1]).resolve())
