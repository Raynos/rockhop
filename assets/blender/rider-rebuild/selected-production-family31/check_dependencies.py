"""Small dependency-direction and deletion-safety fixtures; no Blender load."""
import json
import unittest

from dependencies import closure, dependencies, removable_unused


class DependencyTests(unittest.TestCase):
    def setUp(self):
        # Keys are USED IDs; values are their USERS, as in bpy.data.user_map().
        self.graph = dependencies({'boot': {'scene'}, 'hoodie': {'scene'}, 'rig': {'boot', 'hoodie'},
            'bootMesh': {'boot'}, 'hoodieMesh': {'hoodie'}, 'material': {'bootMesh', 'hoodieMesh'},
            'image': {'material'}, 'pole': {'rig'}, 'parent': {'rig'}, 'action': {'rig'},
            'targetCollection': {'pole'}, 'targetObject': {'targetCollection'}})
        self.keep = closure(['boot', 'rig'], self.graph)

    def test_scene_membership_does_not_keep_unrelated_mesh(self):
        self.assertTrue({'scene', 'hoodie', 'hoodieMesh'}.isdisjoint(self.keep))

    def test_shared_material_map_and_object_dependencies_are_retained(self):
        self.assertEqual(self.keep, {'boot', 'rig', 'bootMesh', 'material', 'image', 'pole',
                                    'parent', 'action', 'targetCollection', 'targetObject'})

    def test_cyclic_driver_dependencies_terminate(self):
        self.assertEqual(closure(['a'], dependencies({'a': {'b'}, 'b': {'a'}})), {'a', 'b'})

    def test_actual_scene_dependency_is_not_silently_discarded(self):
        self.graph['rig'].add('scene')
        self.assertIn('hoodieMesh', closure(['boot', 'rig'], self.graph))

    def test_only_unused_nonclosure_data_can_be_removed(self):
        self.assertTrue(removable_unused('hoodieMesh', self.keep, 0))
        self.assertFalse(removable_unused('image', self.keep, 0))
        self.assertFalse(removable_unused('unrelatedButLive', self.keep, 2))
        self.assertFalse(removable_unused('fakeUser', self.keep, 1))


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(DependencyTests))
    print(json.dumps({'testsRun': result.testsRun, 'failures': len(result.failures),
                      'errors': len(result.errors), 'passed': result.wasSuccessful(), 'nativeExecuted': False}))
    raise SystemExit(not result.wasSuccessful())
