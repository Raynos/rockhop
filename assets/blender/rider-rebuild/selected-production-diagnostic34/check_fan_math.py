import json
import math
import unittest
from fan_math import dot, fan, triangle


class FanTests(unittest.TestCase):
    def test_planar_vertex_matches_both_geometric_averages(self):
        rows = [triangle([[0, 0, 0], [1, 0, 0], [0, 1, 0]], 0),
                triangle([[0, 0, 0], [0, 1, 0], [-1, 0, 0]], 0)]
        self.assertEqual(fan(rows), {'angleWeighted': [0., 0., 1.], 'areaWeighted': [0., 0., 1.]})
        self.assertAlmostEqual(rows[0]['cornerAngleRadians'], math.pi/2)
        self.assertAlmostEqual(rows[0]['areaM2'], .5)

    def test_face_and_vertex_average_can_point_to_opposite_hemispheres(self):
        rows = [{'normal': [0, 0, 1], 'areaM2': .1, 'cornerAngleRadians': .1},
                {'normal': [0, .6, -.8], 'areaM2': 1., 'cornerAngleRadians': 1.}]
        self.assertLess(dot(rows[0]['normal'], fan(rows)['angleWeighted']), 0)
        # This arithmetic possibility alone is not a real topology diagnosis.

    def test_winding_flip_is_visible_in_independent_geometry(self):
        forward = triangle([[0, 0, 0], [1, 0, 0], [0, 1, 0]], 0)
        backward = triangle([[0, 0, 0], [0, 1, 0], [1, 0, 0]], 0)
        self.assertEqual(dot(forward['normal'], backward['normal']), -1)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(FanTests))
    print(json.dumps({'testsRun': result.testsRun, 'passed': result.wasSuccessful(), 'nativeExecuted': False}))
    raise SystemExit(not result.wasSuccessful())
