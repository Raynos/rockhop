"""Pure geometry for actual dense source-to-fitted detail transport.

Inputs are measured post-cut reference/fitted triangles. This module never
creates character geometry, guesses missing correspondence or changes masters.
"""
import numpy as np

def triangle_frame(triangle):
    triangle = np.asarray(triangle, dtype=np.float64)
    assert triangle.shape == (3, 3) and np.isfinite(triangle).all()
    a, b = triangle[1] - triangle[0], triangle[2] - triangle[0]
    normal = np.cross(a, b)
    area2 = float(np.linalg.norm(normal))
    assert area2 > 1e-20, 'Degenerate correspondence triangle'
    frame = np.column_stack([a, b, normal / np.sqrt(area2)])
    assert np.linalg.det(frame) > 0
    return frame

def transport_point(reference_triangle, fitted_triangle, point, barycentric):
    reference, fitted = np.asarray(reference_triangle), np.asarray(fitted_triangle)
    point, bary = np.asarray(point, dtype=np.float64), np.asarray(barycentric, dtype=np.float64)
    assert point.shape == (3,) and bary.shape == (3,) and np.isfinite(point).all() and np.isfinite(bary).all()
    assert bary.min() >= -1e-10 and abs(bary.sum() - 1) < 1e-10, 'Missing in-triangle correspondence'
    jacobian = triangle_frame(fitted) @ np.linalg.inv(triangle_frame(reference))
    residual = point - bary @ reference
    output = bary @ fitted + jacobian @ residual
    assert np.isfinite(output).all() and np.linalg.det(jacobian) > 0
    return output, residual, jacobian

def clip_source_triangles(vertices, faces, planes):
    """Preserve original-face barycentric lineage through explicit cap cuts.

    Returns expanded triangle corners and original triangle/corner barycentrics.
    Expansion is intentional: every source atlas corner keeps its exact owner.
    All planes operate in the DECLARED reference native frame and keep <= 0.
    """
    vertices, faces = np.asarray(vertices, dtype=np.float64), np.asarray(faces, dtype=np.int64)
    assert vertices.ndim == 2 and vertices.shape[1] == 3 and np.isfinite(vertices).all()
    assert faces.ndim == 2 and faces.shape[1] == 3 and ((faces >= 0) & (faces < len(vertices))).all()
    xyz, origin, bary = vertices[faces], np.arange(len(faces)), np.repeat(np.eye(3)[None], len(faces), axis=0)
    removed = []
    for plane in planes:
        point, normal = np.asarray(plane['point']), np.asarray(plane['normal'])
        assert point.shape == normal.shape == (3,) and np.isfinite(point).all() and np.isfinite(normal).all()
        assert abs(np.linalg.norm(normal) - 1) < 1e-8, 'Explicit unit cut normal required'
        signed = (xyz - point) @ normal
        inside = signed <= 0
        keep, drop = inside.all(axis=1), (~inside).all(axis=1)
        removed.extend(origin[drop].tolist())
        kept_xyz, kept_origin, kept_bary = [xyz[keep]], [origin[keep]], [bary[keep]]
        for row in np.flatnonzero(~keep & ~drop):
            polygon = []
            for i in range(3):
                j = (i + 1) % 3
                if inside[row, i]: polygon.append((xyz[row, i], bary[row, i]))
                if inside[row, i] != inside[row, j]:
                    t = signed[row, i] / (signed[row, i] - signed[row, j])
                    polygon.append((xyz[row, i]*(1-t) + xyz[row, j]*t, bary[row, i]*(1-t) + bary[row, j]*t))
            unique_polygon = []
            for value in polygon:
                if not unique_polygon or not np.array_equal(value[0], unique_polygon[-1][0]): unique_polygon.append(value)
            polygon = unique_polygon
            if len(polygon) > 1 and np.array_equal(polygon[0][0], polygon[-1][0]): polygon.pop()
            for i in range(1, len(polygon)-1):
                ids = (0, i, i+1)
                triangle = np.asarray([polygon[j][0] for j in ids])
                if np.linalg.norm(np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0])) <= 1e-30: continue
                kept_xyz.append(np.asarray([[polygon[j][0] for j in ids]]))
                kept_bary.append(np.asarray([[polygon[j][1] for j in ids]]))
                kept_origin.append(np.asarray([origin[row]]))
        xyz, origin, bary = np.concatenate(kept_xyz), np.concatenate(kept_origin), np.concatenate(kept_bary)
    assert len(xyz) > 0 and np.isfinite(xyz).all()
    assert np.max(abs(bary.sum(axis=2) - 1)) < 1e-10 and bary.min() >= -1e-10
    return xyz, origin, bary, np.asarray(sorted(set(removed)), dtype=np.int64)

def validate_support(source_points, reference_triangles, face_ids, barycentric, maximum_distance):
    points, triangles = np.asarray(source_points), np.asarray(reference_triangles)
    rows, bary = np.asarray(face_ids), np.asarray(barycentric)
    assert len(points) == len(rows) == len(bary) and np.isfinite(points).all()
    assert ((rows >= 0) & (rows < len(triangles))).all(), 'Unowned dense appearance points'
    assert np.isfinite(bary).all() and bary.min() >= -1e-10 and np.max(abs(bary.sum(axis=1) - 1)) < 1e-10
    distances = np.linalg.norm(points - np.einsum('ni,nij->nj', bary, triangles[rows]), axis=1)
    assert maximum_distance > 0 and distances.max() <= maximum_distance, 'Missing bounded dense-to-reference support'
    return distances

def validate_transported_triangles(reference_corners, fitted_corners, jacobians):
    a, b = np.asarray(reference_corners), np.asarray(fitted_corners)
    source_normal = np.cross(a[:, 1]-a[:, 0], a[:, 2]-a[:, 0])
    target_normal = np.cross(b[:, 1]-b[:, 0], b[:, 2]-b[:, 0])
    frames = np.asarray(jacobians).mean(axis=1)
    expected = np.linalg.solve(frames.transpose(0, 2, 1), source_normal[..., None])[..., 0]
    dot = np.einsum('ij,ij->i', expected, target_normal)
    assert np.isfinite(dot).all() and (dot > 0).all(), 'Transported dense triangle folded or collapsed'
    return float(dot.min())
