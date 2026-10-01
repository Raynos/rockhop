import importlib.util,unittest
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('sheet',Path(__file__).with_name('sheet_thickness.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def patch(points):return {'vertices':np.array(points,np.float64),'triangles':np.array([[0,1,2]],np.int64)}
class ThicknessTests(unittest.TestCase):
 def test_parallel_partial_overlap(self):
  front=patch([[0,0,0],[1,0,0],[0,1,0]]);back=patch([[.1,.1,.04],[.8,.1,.04],[.1,.8,.04]]);p=module.verify_sheet_thickness(front,back);self.assertTrue(p['positiveThicknessAndCapNonintersection']);self.assertAlmostEqual(p['minimumLocalThickness'],.04)
 def test_narrow_corner_crossing_cannot_hide_between_samples(self):
  front=patch([[0,0,0],[1,0,0],[0,1,0]]);back=patch([[0,0,.1],[1,0,.1],[0,1,-.0001]]);p=module.verify_sheet_thickness(front,back);self.assertFalse(p['positiveThicknessAndCapNonintersection']);self.assertAlmostEqual(p['minimumLocalThickness'],-.0001)
 def test_no_footprint_is_unproved(self):
  front=patch([[0,0,0],[1,0,0],[0,1,0]]);back=patch([[2,2,.1],[3,2,.1],[2,3,.1]]);p=module.verify_sheet_thickness(front,back);self.assertFalse(p['positiveThicknessAndCapNonintersection']);self.assertIsNone(p['minimumLocalThickness'])
 def test_edge_only_touch_is_not_volume_proof(self):
  front=patch([[0,0,0],[1,0,0],[0,1,0]]);back=patch([[1,0,.1],[2,0,.1],[1,1,.1]]);p=module.verify_sheet_thickness(front,back);self.assertFalse(p['positiveThicknessAndCapNonintersection']);self.assertEqual(p['analyticProjectedOverlapPolygons'],0)
if __name__=='__main__':unittest.main()
