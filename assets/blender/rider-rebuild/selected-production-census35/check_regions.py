import json
import unittest
from regions import connected_regions


class RegionTests(unittest.TestCase):
    def test_edge_neighbors_form_one_region(self):
        self.assertEqual(connected_regions([[0, 1, 2], [2, 1, 3], [3, 1, 4]], [0, 1, 2]), [[0, 1, 2]])

    def test_point_contact_and_passing_face_do_not_bridge(self):
        faces = [[0, 1, 2], [2, 1, 3], [3, 1, 4], [0, 5, 6]]
        self.assertEqual(connected_regions(faces, [0, 2, 3]), [[0], [2], [3]])

    def test_nonmanifold_shared_edge_remains_explicit(self):
        self.assertEqual(connected_regions([[0, 1, 2], [1, 0, 3], [0, 1, 4]], [0, 1, 2]), [[0, 1, 2]])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(RegionTests))
    print(json.dumps({'testsRun': result.testsRun, 'passed': result.wasSuccessful(), 'nativeExecuted': False}))
    raise SystemExit(not result.wasSuccessful())
