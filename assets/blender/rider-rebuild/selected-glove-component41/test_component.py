"""Small source-only fixtures; no Blender, browser, images or substitute art."""
import copy
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


c = load('component41_fixture', HERE/'component.py')
a = load('assembly41_fixture', HERE/'assemble.py')


class Library:
    def __init__(self, bpy, extra=()): self.bpy, self.extra = bpy, extra
    def __enter__(self):
        self.selected = NS(objects=[])
        return NS(objects=list(c.REQUESTED)+['RiderHoodie', 'RiderJeans']), self.selected
    def __exit__(self, *unused):
        self.requested = list(self.selected.objects)
        self.selected.objects = [NS(name=name) for name in self.requested]
        self.bpy.data.objects.extend(self.selected.objects+[NS(name=name) for name in self.extra])


def blender_fixture(extra=()):
    linked = []
    bpy = NS(data=NS(objects=[]), context=NS(scene=NS(collection=NS(objects=NS(link=linked.append))),
                                          view_layer=NS(update=lambda: None)))
    library = Library(bpy, extra)
    bpy.data.libraries = NS(load=lambda path, link: library)
    return bpy, library, linked


def qualified():
    return {'status': c.QUALIFIED, 'acceptedArt': False, 'sourceRecipe': c.pin(HERE/'component.py'),
            'methodAncestry': c.FROZEN04, 'sourceInput': c.INPUT10,
            'objects': {name: {'allSourcePrefixNamedFieldsExact': True,
                              'allNewSourceParentNamedFieldsExactAfterFloat32Storage': True} for name in c.GLOVES},
            'protectedValidationPassed': True, 'exact75RestUnchanged': True,
            'constructedGloveGeometryAndNamedFieldsExactAfterReopen': True,
            'protectedValidationStage': 'SEPARATE_REOPENED_COMPONENT_NATIVE',
            'nativeStorage': {'compressed': False, 'reopenVerified': True}}


class ComponentTests(unittest.TestCase):
    def test_only_selected_gloves_rig_and_full_anatomy_requested(self):
        bpy, library, linked = blender_fixture()
        c.append_component(bpy, HERE/'fixture.blend')
        self.assertEqual(library.requested, list(c.REQUESTED))
        self.assertEqual({obj.name for obj in linked}, set(c.REQUESTED))

    def test_unexpected_object_dependency_is_not_silently_loaded(self):
        bpy, unused, linked = blender_fixture(('RiderHoodie',))
        with self.assertRaisesRegex(AssertionError, 'Unexpected selected component object dependency'):
            c.append_component(bpy, HERE/'fixture.blend')
        self.assertFalse(linked)

    def test_nonempty_process_cannot_append_suffixes(self):
        bpy, unused, unused_linked = blender_fixture()
        bpy.data.objects.append(NS(name='RiderSkeleton'))
        with self.assertRaisesRegex(AssertionError, 'new empty background process'):
            c.append_component(bpy, HERE/'fixture.blend')

    def test_exact_component_provenance_passes(self):
        a.component_gate(qualified())

    def test_incomplete_or_relabelled_receipts_fail_closed(self):
        changes = [('status', c.PENDING), ('sourceRecipe', c.FROZEN04),
                   ('methodAncestry', {'path': 'generic.py', 'sha256': '0'*64}),
                   ('protectedValidationPassed', False),
                   ('protectedValidationStage', 'SEPARATE_REOPENED_NATIVE'),
                   ('constructedGloveGeometryAndNamedFieldsExactAfterReopen', False),
                   ('nativeStorage', {'compressed': False, 'reopenVerified': False})]
        for key, value in changes:
            with self.subTest(key=key):
                receipt = qualified(); receipt[key] = value
                with self.assertRaises(AssertionError): a.component_gate(receipt)
        receipt = qualified(); del receipt['objects'][c.GLOVES[1]]
        with self.assertRaises(AssertionError): a.component_gate(receipt)

    def test_frozen_transplant_compiles_without_altering_its_source(self):
        before = c.checked(a.TRANSPLANT).read_bytes()
        source = a.transplant_source()
        compile(source, str(HERE/'transplant-fixture.py'), 'exec')
        self.assertEqual(c.checked(a.TRANSPLANT).read_bytes(), before)
        namespace = a.transplant_namespace()
        self.assertTrue(callable(namespace['integrate']))

    def test_actual_frozen_method_chain_imports_without_scene_or_array_load(self):
        # Import stubs only: calling any Blender/numeric API would fail. This
        # resolves the real hash-checked04→02→original→10→09 chain and proof.
        numeric = types.ModuleType('numpy')
        mathutils = types.ModuleType('mathutils'); mathutils.Vector = object
        geometry = types.ModuleType('mathutils.geometry')
        geometry.delaunay_2d_cdt = geometry.tessellate_polygon = object
        bvh = types.ModuleType('mathutils.bvhtree'); bvh.BVHTree = object
        modules = {'numpy': numeric, 'bpy': types.ModuleType('bpy'), 'mathutils': mathutils,
                   'mathutils.geometry': geometry, 'mathutils.bvhtree': bvh}
        with patch.dict(sys.modules, modules):
            engine, config, base, prior = c.methods()
        self.assertEqual(Path(engine.G['reconstruct'].__code__.co_filename).name, 'reconstruct.py')
        self.assertEqual(prior['master']['sha256'], '95a4f14e06fb52cc055df6d1446a035d8cd3d35180d565ad52f3a70b3b05664b')
        self.assertEqual(config['cuffReconstructionHelper']['path'],
                         'assets/blender/rider-rebuild/selected-cuff-topology10/reconstruct.py')

    def test_original_witness_cannot_omit_hoodie_or_full_reference(self):
        receipt = qualified(); receipt.update(priorInput={'path': 'prior.json', 'sha256': '0'*64},
                                             sourceMaster={'path': 'native.blend', 'sha256': '1'*64})
        prior = {'master': receipt['sourceMaster'], 'geometryHelper': {'path': 'geometry.py', 'sha256': '2'*64},
                 'restHelper': {'path': 'rest.py', 'sha256': '3'*64}}
        visible = ['RiderBody', 'RiderHoodie', 'RiderJeans', *c.GLOVES, 'ActualSelectedBoot.L', 'ActualSelectedBoot.R']
        names = sorted((set(visible)-set(c.GLOVES))|{c.REFERENCE})
        original = {'sourceMaster': receipt['sourceMaster'], 'sourceRecipe': a.pin(HERE/'assemble.py'),
                    'sourceInput': receipt['priorInput'], 'geometryHelper': prior['geometryHelper'],
                    'restHelper': prior['restHelper'], 'visibleMeshes': visible, 'protectedNames': names,
                    'expectedProtectedGeometry': dict.fromkeys(names, 'fixture'),
                    'expectedRest': [None]*75, 'restForTransplant': [None]*75}
        with patch.dict(a.component, {'read': lambda pin: prior}):
            a.witness_gate(original, receipt)
            for name in ('RiderHoodie', c.REFERENCE):
                bad = copy.deepcopy(original); bad['protectedNames'].remove(name)
                del bad['expectedProtectedGeometry'][name]
                with self.assertRaises(AssertionError): a.witness_gate(bad, receipt)


if __name__ == '__main__': unittest.main()
