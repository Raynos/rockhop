"""Conditional parent-only correction; requires reviewed native57 proof SHA.

Original guarded Blender invocation: --python author.py --
  NATIVE57_DIAGNOSTIC_JSON REVIEWED_DIAGNOSTIC_SHA256 NEW_ALLOCATION46_OUTPUT
Reuses exact candidate01 and frozen author56. Never reruns simplification.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fan

AUTHOR56 = fan.ROOT/'assets/blender/rider-rebuild/selected-boot-correspondence56/author.py'
AUTHOR56_SHA = 'e73906dcdea2938a0add64594317752366bdfe29468a9ba7133b690e23590ee9'


def adapted_source():
    fan.pin(AUTHOR56, AUTHOR56_SHA)
    previous = fan.load(AUTHOR56, 'orientation57_author56')
    source, adapter46 = previous.adapted_source()
    patches = [
        ('KERNEL56.install(engine, out)', 'ORIENTATION57.install(engine, out, PROOF57)'),
        ("'recipeSHA256': sha(AUTHOR56),",
         "'recipeSHA256': sha(AUTHOR57), 'orientationAdapter57': {'proof': PROOF57, 'author56SHA256': AUTHOR56_SHA, 'orientationRecipeSHA256': sha(ORIENTATION57.__file__), 'metric': 'Native donor vertex normal at exact original ancestor versus native target vertex normal; threshold 0.25 unchanged'},"),
        ('all downstream gates unchanged',
         'vertex-to-vertex orientation at exact ancestry; threshold and separate geometric face, surface and skin gates unchanged'),
        ('with unchanged source bearings and frozen25 downstream gates.',
         'with unchanged source bearings; native vertex orientation uses exact donor vertex ancestry, while separate geometric face, surface and skin gates remain.'),
    ]
    for old, new in patches:
        assert source.count(old) == 1, ('Orientation57 author patch drift', old)
        source = source.replace(old, new)
    return source, previous, adapter46


def main():
    import orientation
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 3
    proof_pin = orientation.verify_proof(args[0], args[1])
    source, previous, adapter46 = adapted_source()
    namespace = {'__file__': str(previous.AUTHOR46), '__name__': 'orientation57_native',
        'FROZEN': adapter46.FROZEN, 'FROZEN_SHA': adapter46.FROZEN_SHA,
        'AUTHOR56': AUTHOR56, 'AUTHOR56_SHA': AUTHOR56_SHA, 'AUTHOR57': Path(__file__).resolve(),
        'AUTHOR46': previous.AUTHOR46, 'AUTHOR46_SHA': previous.AUTHOR46_SHA,
        'KERNEL56': orientation.kernel, 'ORIENTATION57': orientation, 'PROOF57': proof_pin,
        'CANDIDATE56': previous.CANDIDATE, 'CANDIDATE56_SHA': previous.CANDIDATE_SHA}
    old_argv = sys.argv[:]
    sys.argv = old_argv[:old_argv.index('--')+1]+[str(previous.CANDIDATE), args[2]]
    try:
        exec(compile(source, str(AUTHOR56)+'[orientation57]', 'exec'), namespace)
        namespace['main']()
    finally:
        sys.argv = old_argv


if __name__ == '__main__': main()
