"""Copied-ID ownership and deletion-order fixtures, without Blender or baking."""
import json
import unittest
from types import SimpleNamespace

from lifetime import OwnedMeshes, BpyProxy


class ID:
    def __init__(self, name, data=None, users=1):
        self.name = name; self.data = data; self.users = users

    def as_pointer(self): return id(self)


class LifetimeTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.meshes = SimpleNamespace(remove=lambda mesh, **kw: self.events.append(('mesh', mesh.name, kw)))
        def remove(obj, **kw):
            self.events.append(('object', obj.name, kw)); obj.data.users -= 1
        self.objects = SimpleNamespace(remove=remove)
        self.tracker = OwnedMeshes(lambda: self.objects, lambda: self.meshes)
        self.source = ID('selectedBoot', ID('sourceMesh'))
        self.donor = ID('donor', ID('freshCopy'))

    def test_removes_owned_mesh_after_object_only_at_zero_users(self):
        self.tracker.register(self.donor, self.source, 'donor')
        self.tracker.remove(self.donor, do_unlink=True)
        self.assertEqual(self.events, [('object', 'donor', {'do_unlink': True}),
                                       ('mesh', 'freshCopy', {'do_unlink': False})])
        self.assertFalse(self.tracker.pending)
        self.assertEqual(self.source.data.users, 1)

    def test_never_removes_unregistered_mesh(self):
        self.tracker.remove(self.donor, do_unlink=True)
        self.assertEqual(len(self.events), 1)

    def test_refuses_alias_to_original_mesh(self):
        self.donor.data = self.source.data
        with self.assertRaises(AssertionError): self.tracker.register(self.donor, self.source, 'donor')

    def test_refuses_live_or_fake_user_after_object_removal(self):
        self.donor.data.users = 2
        self.tracker.register(self.donor, self.source, 'donor')
        with self.assertRaises(AssertionError): self.tracker.remove(self.donor, do_unlink=True)
        self.assertEqual(len(self.events), 1)
        self.assertEqual(len(self.tracker.pending), 1)

    def test_refuses_changed_mesh_before_object_removal(self):
        self.tracker.register(self.donor, self.source, 'donor'); self.donor.data = ID('replacement')
        with self.assertRaises(AssertionError): self.tracker.remove(self.donor)
        self.assertFalse(self.events)

    def test_module_proxy_never_changes_original_operator_or_data(self):
        operators = object(); real = SimpleNamespace(ops=operators, data=SimpleNamespace(objects=self.objects))
        proxy = BpyProxy(real, self.tracker.remove)
        self.assertIs(proxy.ops, operators)
        self.assertIs(real.data.objects, self.objects)
        self.assertIsNot(proxy.data.objects.remove, real.data.objects.remove)

    def test_file_open_replacement_uses_new_main_collections(self):
        original = self.objects
        real = SimpleNamespace(data=SimpleNamespace(objects=original))
        proxy = BpyProxy(real, self.tracker.remove)
        self.objects = SimpleNamespace(remove=original.remove, marker='new Main')
        real.data = SimpleNamespace(objects=self.objects)
        self.assertEqual(proxy.data.objects.marker, 'new Main')
        self.tracker.register(self.donor, self.source, 'donor')
        proxy.data.objects.remove(self.donor, do_unlink=True)
        self.assertEqual(len(self.tracker.released), 1)

    def test_frozen_source_and_target_item_lookups_before_after_main_replacement(self):
        class Objects(dict): pass
        level = 'full'; names = ['ActualSelectedBoot.L', 'ActualSelectedBoot.R']
        def main(label):
            objects = Objects({key: ID(label + ':' + key) for name in names
                               for key in [name, 'Production.' + level + '.' + name]})
            objects.remove = self.objects.remove
            return SimpleNamespace(objects=objects)
        old = main('old'); new = main('new'); operators = object()
        real = SimpleNamespace(data=old, ops=operators)
        proxy = BpyProxy(real, self.tracker.remove)
        for current in [old, new]:
            real.data = current
            for name in names:
                source = proxy.data.objects[name]
                target = proxy.data.objects['Production.' + level + '.' + name]
                self.assertIs(source, current.objects[name])
                self.assertIs(target, current.objects['Production.' + level + '.' + name])
            self.assertIs(proxy.ops, operators)
        self.assertIsNot(old.objects[names[0]], proxy.data.objects[names[0]])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(LifetimeTests))
    print(json.dumps({'testsRun': result.testsRun, 'failures': len(result.failures),
                      'errors': len(result.errors), 'passed': result.wasSuccessful(), 'nativeExecuted': False}))
    raise SystemExit(not result.wasSuccessful())
