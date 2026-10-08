"""Analytic material topology controls, not substitute jeans assets."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('source_slits', HERE/'audit-source-slits.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


def contour(points):
    xy = np.asarray(points, dtype=float)
    return {'polygon': np.column_stack((xy[:, 0], np.zeros(len(xy)), xy[:, 1]))}


class MaterialTopologyControls(unittest.TestCase):
    def test_nested_material_boundaries_retain_two_hits(self):
        square = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1.]])
        rows = audit.material_rays([contour(square), contour(square*.5)], np.zeros(2), 32)
        self.assertTrue(all(row['hitCount'] == 2 for row in rows))
        self.assertAlmostEqual(rows[0]['distances'][0], .5)
        self.assertAlmostEqual(rows[0]['distances'][1], 1.)

    def test_actual_c_section_keeps_directional_gap(self):
        c = contour([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, .2],
                     [-.5, .2], [-.5, .5], [.5, .5], [.5, -.5], [-.5, -.5],
                     [-.5, -.2], [-1, -.2]])
        rows = audit.material_rays([c], np.zeros(2), 32)
        self.assertEqual(rows[16]['hitCount'], 0)
        self.assertEqual(rows[0]['hitCount'], 2)
        self.assertAlmostEqual(rows[0]['distances'][0], .5)
        self.assertGreater(sum(row['hitCount'] == 0 for row in rows), 0)

    def test_center_in_solid_material_has_one_exit(self):
        square = contour([[-1, -1], [1, -1], [1, 1], [-1, 1]])
        rows = audit.material_rays([square], np.zeros(2), 32)
        self.assertTrue(all(row['hitCount'] == 1 for row in rows))

    def test_angular_arrangement_finds_sub_grid_opening(self):
        epsilon = .00001
        points = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, epsilon],
                           [-.5, epsilon], [-.5, .5], [.5, .5], [.5, -.5],
                           [-.5, -.5], [-.5, -epsilon], [-1, -epsilon]])
        angle = .001
        rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        c = contour(points @ rotation.T)
        rays = audit.material_rays([c], np.zeros(2), 720)
        self.assertTrue(all(row['hitCount'] > 0 for row in rays))
        coverage = audit.angular_material_coverage([c], np.zeros(2))
        self.assertGreater(coverage['totalGapRadians'], 0.)
        self.assertAlmostEqual(coverage['totalGapRadians'], 2*np.arctan(epsilon), places=12)

    def test_nested_material_cones_cover_complete_circle(self):
        square = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1.]])
        coverage = audit.angular_material_coverage([contour(square), contour(square*.5)], np.zeros(2))
        self.assertEqual(coverage['totalGapRadians'], 0.)


if __name__ == '__main__':
    unittest.main()
