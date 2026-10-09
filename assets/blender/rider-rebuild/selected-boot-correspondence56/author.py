"""Parent-only adapter of frozen author46; reuse its exact candidate01.

blender -b -t 2 --python-exit-code 1 --python author.py --
  harness/out/rider-rebuild/selected-production-allocation46/candidate01/constructor.json
  harness/out/rider-rebuild/selected-production-allocation46/native02
The normal original guard owns execution. Importing this module is CPU-only.
"""
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AUTHOR56 = Path(__file__).resolve()
AUTHOR46 = ROOT/'assets/blender/rider-rebuild/selected-production-allocation46/author.py'
AUTHOR46_SHA = 'e802d51a7a1384bd76dab84050c63d8c58498fd851af8949c435a8c5f56f7906'
CANDIDATE = ROOT/'harness/out/rider-rebuild/selected-production-allocation46/candidate01/constructor.json'
CANDIDATE_SHA = '624affb3b59053d6bdee32fb3283c6b2ce23ff3d849c3fe0dd9669ec9319f3c8'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def adapted_source():
    assert hashlib.sha256(AUTHOR46.read_bytes()).hexdigest() == AUTHOR46_SHA, 'Frozen author46 changed'
    adapter = load(AUTHOR46, 'correspondence56_author46')
    source = adapter.adapted_source()
    patches = [
        ("receipt_path = Path(args[0]).resolve(); out = Path(args[1]).resolve()",
         "receipt_path = Path(args[0]).resolve(); out = Path(args[1]).resolve()\n    assert receipt_path == CANDIDATE56 and sha(receipt_path) == CANDIDATE56_SHA, 'Exact candidate46 required'"),
        ("engine = load(engine_path, 'constructor37_frozen25')",
         "engine = load(engine_path, 'constructor37_frozen25')\n    KERNEL56.install(engine, out)"),
        ("'recipeSHA256': sha(__file__), 'objects': {}",
         "'recipeSHA256': sha(AUTHOR56), 'correspondenceAdapter': {'author46': {'path': str(AUTHOR46.relative_to(ROOT)), 'sha256': AUTHOR46_SHA}, 'kernel56': {'path': str(Path(KERNEL56.__file__).relative_to(ROOT)), 'sha256': sha(KERNEL56.__file__)}, 'policy': 'Same BVH source bearing; scale-independent cross-product barycentrics; all downstream gates unchanged'}, 'objects': {}"),
        ('precede unchanged frozen25 correspondence.',
         'precede scale-independent kernel56 correspondence with unchanged source bearings and frozen25 downstream gates.'),
    ]
    for old, new in patches:
        assert source.count(old) == 1, ('Adapter56 patch drift', old)
        source = source.replace(old, new)
    return source, adapter


def main():
    source, adapter = adapted_source()
    kernel = load(AUTHOR56.with_name('kernel.py'), 'correspondence56_kernel')
    # Retain author46's HERE, recipe checks and output containment. Only the
    # top-level recipe provenance points to this explicit adapter.
    namespace = {'__file__': str(AUTHOR46), '__name__': 'correspondence56_native',
                 'FROZEN': adapter.FROZEN, 'FROZEN_SHA': adapter.FROZEN_SHA,
                 'AUTHOR56': AUTHOR56, 'AUTHOR46': AUTHOR46, 'AUTHOR46_SHA': AUTHOR46_SHA,
                 'KERNEL56': kernel, 'CANDIDATE56': CANDIDATE, 'CANDIDATE56_SHA': CANDIDATE_SHA}
    exec(compile(source, str(AUTHOR46)+'[correspondence56]', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__': main()
