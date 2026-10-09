"""Parent-only native intake: explicit actual constructor62 path and reviewed SHA.

Original guarded Blender --python author.py --
  ACTUAL_CONSTRUCTOR62_JSON REVIEWED_CONSTRUCTOR_SHA256 NEW_NATIVE63_OUTPUT
Imports are CPU-only. The receipt and final candidate are pinned to actual62.
"""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import admission

ROOT = admission.ROOT
AUTHOR63 = Path(__file__).resolve()
AUTHOR57 = ROOT/'assets/blender/rider-rebuild/selected-boot-fold57/author.py'
AUTHOR57_SHA = '1f99906b30d58e1c9849396e23cd6e219e1e177d190be336a48902950677d1aa'
ORIENTATION57 = AUTHOR57.with_name('orientation.py')
ORIENTATION57_SHA = '88ccf86250e709b4f4b7b76827d103764c9e36bb96934618917ed0bb2fa95abe'
FAN57_SHA = '141a51716ffe65defaca86210789ecde72cc526e5faa516f10609b6c89dfeb82'
PROOF57 = ROOT/'harness/out/rider-rebuild/selected-boot-fold57/native01/diagnostic.json'
PROOF57_SHA = 'b12aa95d60ba0889b3c0a84184a0c8fc61f67f986b18a5416fffacaaca3bb52a'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def adapted_source():
    admission.pin(AUTHOR57, AUTHOR57_SHA); admission.pin(ORIENTATION57, ORIENTATION57_SHA)
    admission.pin(AUTHOR57.with_name('fan.py'), FAN57_SHA)
    author57 = load(AUTHOR57, 'native63_author57')
    source, previous, adapter46 = author57.adapted_source()
    patches = [
        ("assert receipt['candidateAttempts'] == 1 and receipt['acceptedArt'] is False",
         "assert receipt['candidateAttempts'] == 2 and receipt['acceptedArt'] is False\n    assert receipt['fixedPoint']['complete'] is True"),
        ("assert receipt_path == CANDIDATE56 and sha(receipt_path) == CANDIDATE56_SHA, 'Exact candidate46 required'",
         "assert receipt_path == ADMITTED63_RECEIPT and sha(receipt_path) == ADMITTED63_SHA, 'Reviewed actual constructor62 receipt changed'"),
        ("base = ROOT/'harness/out/rider-rebuild/selected-production-allocation46'",
         "base = ROOT/'harness/out/rider-rebuild/selected-boot-closure62'\n    output_base63 = ROOT/'harness/out/rider-rebuild/selected-boot-native63'"),
        ('receipt_path.is_relative_to(base) and out.is_relative_to(base) and not out.exists()',
         'receipt_path.is_relative_to(base) and out.is_relative_to(output_base63) and not out.exists()'),
        ("assert receipt['recipeSHA256'] == sha(HERE/'construct.mjs')",
         "assert receipt['recipeSHA256'] == sha(CONSTRUCTOR62) == CONSTRUCTOR62_SHA"),
        ("'recipeSHA256': sha(AUTHOR57),",
         "'recipeSHA256': sha(AUTHOR63), 'nativeAdmission63': ADMISSION63, 'author57Ancestry': {'path': str(AUTHOR57.relative_to(ROOT)), 'sha256': AUTHOR57_SHA},"),
        ("assert np.array_equal(engine.points(target).astype(np.float32), p)",
         "assert np.array_equal(engine.points(target).astype(np.float32), p)\n    assert np.array_equal(engine.triangles(target), f), 'Native target altered exact admitted topology'"),
        ("out.mkdir(parents=True)",
         "out.mkdir(parents=True)\n    (out/'admission63.json').write_text(json.dumps(ADMISSION63, indent=2)+'\\n')"),
        ("'Constructor46.original-position-topology'", "'Constructor62.protected-fan-original-position-topology'"),
        ("'UNACCEPTED_CONSTRUCTOR46_BEFORE_QUALIFICATION'", "'UNACCEPTED_CONSTRUCTOR62_BEFORE_QUALIFICATION'"),
        ("'UNACCEPTED-constructor46-before-transfer.blend'", "'UNACCEPTED-constructor62-before-transfer.blend'"),
        ("'REJECTED_NATIVE_CONSTRUCTOR46_UNACCEPTED'", "'REJECTED_NATIVE_CONSTRUCTOR62_UNACCEPTED'"),
    ]
    for old, new in patches:
        assert source.count(old) == 1, ('Native63 adapter drift', old)
        source = source.replace(old, new)
    return source, author57, previous, adapter46


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 3
    accepted = admission.admit(args[0], args[1], args[2])
    source, author57, previous, adapter46 = adapted_source()
    orientation = load(ORIENTATION57, 'native63_orientation57')
    proof = orientation.verify_proof(PROOF57, PROOF57_SHA)
    namespace = {'__file__': str(AUTHOR63), '__name__': 'native63_frozen_qualification',
        'FROZEN': adapter46.FROZEN, 'FROZEN_SHA': adapter46.FROZEN_SHA,
        'AUTHOR56_SHA': author57.AUTHOR56_SHA, 'AUTHOR63': AUTHOR63,
        'AUTHOR57': AUTHOR57, 'AUTHOR57_SHA': AUTHOR57_SHA,
        'AUTHOR46': previous.AUTHOR46, 'AUTHOR46_SHA': previous.AUTHOR46_SHA,
        'KERNEL56': orientation.kernel, 'ORIENTATION57': orientation, 'PROOF57': proof,
        'ADMISSION63': accepted, 'ADMITTED63_RECEIPT': Path(args[0]).resolve(), 'ADMITTED63_SHA': args[1],
        'CONSTRUCTOR62': admission.CONSTRUCTOR62, 'CONSTRUCTOR62_SHA': admission.CONSTRUCTOR62_SHA}
    old_argv = sys.argv[:]
    sys.argv = old_argv[:old_argv.index('--')+1]+[args[0], args[2]]
    try:
        exec(compile(source, str(AUTHOR57)+'[native63]', 'exec'), namespace)
        namespace['main']()
    finally:
        sys.argv = old_argv


if __name__ == '__main__': main()
