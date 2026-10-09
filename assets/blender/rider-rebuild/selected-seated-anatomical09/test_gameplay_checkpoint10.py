"""Reject incorrect native preservation evidence before costly replay."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('checkpoint10', Path(__file__).with_name('gameplay_checkpoint10.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Preservation(unittest.TestCase):
    def setUp(self):
        self.before = {'accepted': False, 'kind': 'source', 'native': 'old', 'pending': 'pending',
                       'protected': {'RiderJeans': 'geometry-maps'}, 'fields': {'RiderJeans': 'weights'},
                       'keys': {'RiderBody': 'coordinates'}, 'rest': ['original75'],
                       'visibleMeshes': ['selected'], 'recipe': 'actual10',
                       'actions': {'RiderIdle': {'curves': [1, 2]}}}
        self.after = copy.deepcopy(self.before)
        self.after.update(kind='saved', native='new')
        self.after['actions']['RiderGameplayLeanPro'] = {'curves': [3, 4]}

    def compare(self):
        module.compare_snapshots(self.before, self.after, 'pending', 'old', 'new')

    def test_added_action_preserves_original(self):
        self.compare()

    def test_changed_geometry_fields_rest_keys_or_materials_rejected(self):
        for key in ('protected', 'fields', 'rest', 'keys', 'visibleMeshes'):
            with self.subTest(key=key):
                old = self.after[key]
                self.after[key] = 'changed'
                with self.assertRaises(AssertionError):
                    self.compare()
                self.after[key] = old

    def test_changed_original_action_rejected(self):
        self.after['actions']['RiderIdle']['curves'][0] = 99
        with self.assertRaises(AssertionError):
            self.compare()

    def test_source_or_saved_substitution_rejected(self):
        for key in ('native', 'pending', 'kind', 'recipe'):
            with self.subTest(key=key):
                old = self.after[key]
                self.after[key] = 'substitute'
                with self.assertRaises(AssertionError):
                    self.compare()
                self.after[key] = old


if __name__ == '__main__':
    unittest.main()
