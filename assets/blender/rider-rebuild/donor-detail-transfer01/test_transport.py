"""Geometry correspondence tests only; no synthetic character or appearance assets."""
import unittest
import numpy as np
from transport_core import transport_point, clip_source_triangles, validate_support, validate_transported_triangles

class GeometryTransport(unittest.TestCase):
    def setUp(self):
        self.triangle = np.asarray([[0., 0, 0], [1, 0, 0], [0, 1, 0]])
        self.bary = np.asarray([.2, .3, .5])
        self.point = self.bary @ self.triangle + [0, 0, .04]

    def test_identity_keeps_dense_residual_exact(self):
        point, residual, frame = transport_point(self.triangle, self.triangle, self.point, self.bary)
        np.testing.assert_array_equal(point, self.point)
        np.testing.assert_array_equal(frame, np.eye(3))
        np.testing.assert_allclose(residual, [0, 0, .04])

    def test_rotation_scale_and_translation_transport_detail(self):
        rotation = np.asarray([[0., -1, 0], [1, 0, 0], [0, 0, 1]])
        fitted = self.triangle @ rotation.T * 2 + [2, 3, 4]
        point, _, frame = transport_point(self.triangle, fitted, self.point, self.bary)
        np.testing.assert_allclose(point, self.point @ rotation.T * 2 + [2, 3, 4])
        np.testing.assert_allclose(frame, rotation * 2)

    def test_in_plane_shear_preserves_barycentric_surface(self):
        fitted = np.asarray([[1., 2, 3], [3, 2, 3], [2, 3, 3]])
        point, _, _ = transport_point(self.triangle, fitted, self.bary @ self.triangle, self.bary)
        np.testing.assert_allclose(point, self.bary @ fitted)

    def test_cap_cut_keeps_original_triangle_barycentric_lineage(self):
        xyz, rows, bary, removed = clip_source_triangles(self.triangle, [[0, 1, 2]],
            [{'point': [.4, 0, 0], 'normal': [1., 0, 0]}])
        self.assertEqual(len(xyz), 2)
        np.testing.assert_array_equal(rows, [0, 0])
        np.testing.assert_allclose(xyz, bary @ self.triangle)
        self.assertLessEqual(xyz[:, :, 0].max(), .4)
        self.assertEqual(len(removed), 0)

    def test_removed_cap_is_masked_not_given_zero_deformation(self):
        points = np.vstack([self.triangle, self.triangle + [0, 0, 2]])
        xyz, rows, _, removed = clip_source_triangles(points, [[0, 1, 2], [3, 4, 5]],
            [{'point': [0, 0, 1], 'normal': [0., 0, 1]}])
        np.testing.assert_array_equal(rows, [0])
        np.testing.assert_array_equal(removed, [1])
        self.assertEqual(len(xyz), 1)

    def test_missing_or_outside_support_fails(self):
        with self.assertRaises(AssertionError):
            validate_support([self.point], [self.triangle], [-1], [self.bary], .1)
        with self.assertRaises(AssertionError):
            validate_support([self.point], [self.triangle], [0], [self.bary], .01)
        with self.assertRaises(AssertionError):
            transport_point(self.triangle, self.triangle, self.point, [-.1, .6, .5])

    def test_degenerate_reference_fails(self):
        with self.assertRaises(AssertionError):
            transport_point(np.zeros((3, 3)), self.triangle, self.point, self.bary)

    def test_actual_folded_transport_is_rejected(self):
        with self.assertRaises(AssertionError):
            validate_transported_triangles([self.triangle], [self.triangle[::-1]], [np.repeat(np.eye(3)[None], 3, axis=0)])

if __name__ == '__main__': unittest.main()
