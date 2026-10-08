"""Actual dense inner-only clipping and paired fitted original corner lineage.

No compact inherited UV, no repeated source exterior inside the new cavity.
Exact dense visibility must produce one true rim cycle or ownership fails.
"""
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def original_corner_bary(clipped, original_faces):
    result = np.zeros((len(clipped['faces']), 3, 3), dtype=np.float64)
    for face_id, (face, owner) in enumerate(zip(clipped['faces'], clipped['sourceFaceIDs'])):
        original = original_faces[owner]
        for corner, vertex in enumerate(face):
            original_vertex = clipped['sourceVertexIDs'][vertex]
            if original_vertex >= 0:
                index = np.flatnonzero(original == original_vertex)
                assert len(index) == 1
                result[face_id, corner, index[0]] = 1.
            else:
                edge = clipped['sourceEdgeVertexIDs'][vertex]
                t = clipped['sourceEdgeInterpolationT'][vertex]
                i, j = (np.flatnonzero(original == point) for point in edge)
                assert len(i) == len(j) == 1
                result[face_id, corner, i[0]] = 1 - t
                result[face_id, corner, j[0]] = t
    assert result.min() >= 0 and abs(result.sum(2) - 1).max() < 1e-12
    return result


def closest_bary(point, triangle):
    """Recompute exact chosen-triangle feature minimum in double precision."""
    candidates = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        edge = triangle[j] - triangle[i]
        t = np.clip((point - triangle[i]) @ edge / (edge @ edge), 0., 1.)
        bary = np.zeros(3); bary[i], bary[j] = 1 - t, t
        candidates.append(bary)
    a, b = triangle[1] - triangle[0], triangle[2] - triangle[0]
    normal = np.cross(a, b); denominator = normal @ normal
    assert denominator > 1e-30
    projected = point - normal * ((point - triangle[0]) @ normal / denominator)
    v = np.cross(projected - triangle[0], b) @ normal / denominator
    w = np.cross(a, projected - triangle[0]) @ normal / denominator
    if v >= 0 and w >= 0 and v + w <= 1:
        candidates.append(np.array([1 - v - w, v, w]))
    distances = [np.linalg.norm(point - bary @ triangle) for bary in candidates]
    best = int(np.argmin(distances))
    return candidates[best], float(distances[best])


def frame(triangles):
    a, b = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    normal = np.cross(a, b); area = np.linalg.norm(normal, axis=1)
    assert (area > 1e-20).all()
    return np.stack([a, b, normal / np.sqrt(area)[:, None]], axis=2)


def classify_dense(dense, helper, output):
    vertices = dense['vertices'].astype(np.float64); faces = dense['faces']
    triangles = vertices[faces]; centers = triangles.mean(1)
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    assert (lengths > 0).all(), 'Dense source has degenerate geometric faces'
    normals /= lengths[:, None]
    tree = BVHTree.FromPolygons([Vector(row) for row in vertices], faces.tolist(), all_triangles=True)
    seeds = np.asarray([[.45, .15, -.07], [.45, 0., -.07], [.45, -.20, -.07]])
    visible = np.zeros(len(faces), dtype=bool)
    for seed in seeds:
        assert tree.ray_cast(Vector(seed), Vector((0, 1, 0)))[0] is None
        delta = centers - seed; distance = np.linalg.norm(delta, axis=1)
        direction = delta / distance[:, None]
        facing = np.einsum('ij,ij->i', normals, -direction) > .0001
        for row in np.flatnonzero(facing & ~visible):
            hit, normal, hit_id, hit_distance = tree.ray_cast(Vector(seed), Vector(direction[row]))
            if hit is not None and hit_id == row and abs(hit_distance - distance[row]) < 2e-6:
                visible[row] = True
    np.savez_compressed(output / 'original-dense-semantic-mask.npz', originalDenseInnerVisibleMask=visible,
                        originalDenseFaceRows=np.arange(len(faces)), actualCavitySeeds=seeds)
    clipped = helper.cut_only_inner(vertices, faces, visible, .18001)
    loop = helper.one_boundary(clipped['faces'])
    assert abs(clipped['vertices'][loop, 1] - .18001).max() < 1e-10, 'Dense inner visibility leaves unsupported cavity gaps'
    bary = original_corner_bary(clipped, faces)
    reconstructed = np.einsum('fci,fij->fcj', bary, vertices[faces[clipped['sourceFaceIDs']]])
    assert np.max(abs(reconstructed - clipped['vertices'][clipped['faces']])) < 1e-12
    clipped['originalCornerBarycentrics'] = bary
    clipped['originalDenseInnerVisibleMask'] = visible
    clipped['sourceCavityRimLoop'] = loop
    np.savez_compressed(output / 'original-dense-inner-cut.npz', **clipped)
    return clipped


def pair_dense(dense, clipped, compact_fit, output, side):
    reference = compact_fit['referenceVertices']
    current = compact_fit['vertices'].astype(np.float32).astype(np.float64)
    faces, affine = compact_fit['faces'], compact_fit['sourceToNativeAffine']
    points = clipped['vertices'] @ affine[:3, :3].T + affine[:3, 3]
    tree = BVHTree.FromPolygons([Vector(row) for row in reference], faces.tolist(), all_triangles=True)
    owners, barys, distances = [], [], []
    for point in points:
        hit, normal, row, distance = tree.find_nearest(Vector(point))
        assert hit is not None
        bary, actual_distance = closest_bary(point, reference[faces[row]])
        owners.append(row); barys.append(bary); distances.append(actual_distance)
    owners, barys, distances = np.asarray(owners), np.asarray(barys), np.asarray(distances)
    assert distances.max() <= .008, 'Original dense point lacks bounded actual source support'
    jacobians = frame(current[faces]) @ np.linalg.inv(frame(reference[faces]))
    residual = points - np.einsum('ni,nij->nj', barys, reference[faces[owners]])
    fitted = np.einsum('ni,nij->nj', barys, current[faces[owners]])
    fitted += np.einsum('nij,nj->ni', jacobians[owners], residual)
    dense_faces = clipped['faces'].copy(); corner_bary = clipped['originalCornerBarycentrics'].copy()
    if np.linalg.det(affine[:3, :3]) < 0:
        dense_faces = dense_faces[:, ::-1]; corner_bary = corner_bary[:, ::-1]
    original_rows = clipped['sourceFaceIDs']
    corner_uv = np.einsum('fci,fij->fcj', corner_bary, dense['originalCornerUV'][original_rows])
    corner_normals = np.einsum('fci,fij->fcj', corner_bary, dense['donorCornerNormals'][original_rows])
    corner_normals = corner_normals @ np.linalg.inv(affine[:3, :3])
    corner_frames = jacobians[owners[dense_faces]]
    fitted_normals = np.linalg.solve(corner_frames.transpose(0, 1, 3, 2), corner_normals[..., None])[..., 0]
    fitted_normals /= np.linalg.norm(fitted_normals, axis=2)[:, :, None]
    before, after = points[dense_faces], fitted[dense_faces]
    old_normal = np.cross(before[:, 1] - before[:, 0], before[:, 2] - before[:, 0])
    new_normal = np.cross(after[:, 1] - after[:, 0], after[:, 2] - after[:, 0])
    expected = np.linalg.solve(corner_frames[:, 0].transpose(0, 2, 1), old_normal[..., None])[..., 0]
    orientation = np.einsum('fi,fi->f', expected, new_normal)
    np.savez_compressed(output / ('dense-fitted-lineage-' + side + '.npz'),
                        uniqueReferencePoints=points, uniqueFittedPoints=fitted, fittedDenseFaces=dense_faces,
                        postcutCompactFaceRows=owners, postcutCompactBarycentrics=barys,
                        originalLocalResidual=residual, referenceToFittedJacobians=jacobians[owners],
                        denseOriginalFaceRows=original_rows, denseOriginalTriangleRows=dense['originalTriangleRows'][original_rows],
                        denseOriginalCornerBarycentrics=corner_bary, denseCornerUV=corner_uv,
                        fittedDenseCornerNormals=fitted_normals, referenceSupportDistances=distances,
                        excludedOriginalDenseFaceRows=np.setdiff1d(np.arange(len(dense['faces'])), original_rows),
                        transportedDenseOrientationDot=orientation)
    assert np.isfinite(fitted).all() and np.isfinite(fitted_normals).all() and (orientation > 0).all(), 'Fitted original dense detail folds/collapses'
    return {'originalDenseTriangles': len(dense['faces']), 'retainedPostcutDenseTriangles': len(dense_faces),
            'actualDenseInnerRimVertices': len(clipped['sourceCavityRimLoop']),
            'maximumReferenceSupportDistanceM': float(distances.max()),
            'maximumTransportedResidualM': float(np.linalg.norm(jacobians[owners] @ residual[..., None], axis=1).max()),
            'minimumTransportedOrientationDot': float(orientation.min())}
