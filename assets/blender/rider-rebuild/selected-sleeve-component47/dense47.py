"""One unchanged dense28 relation; explicit47 scope/provenance adapter only.

Parent CPU2 process per relation. Never infers motion or accepted art.
"""
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'component.py'))
ORIGINAL = {'path': 'assets/blender/rider-rebuild/selected-sleeve-rebuild28/qualify.py',
            'sha256': 'd4e261170c8d754ca97eec329d2958ad88e059a5f87903fc862207d87087710c'}


def transformed_source():
    source = h['checked'](ORIGINAL).read_text()
    changes = {
        "ROOT/'harness/out/rider-rebuild/selected-sleeve-rebuild28'":
            "ROOT/'harness/out/rider-rebuild/selected-sleeve-component47'",
        "'recipeSHA256': sha(__file__),":
            "'recipeSHA256': sha(WRAPPER), 'originalQualifier': ORIGINAL,"}
    for old, new in changes.items():
        assert source.count(old) == 1
        source = source.replace(old, new)
    return source


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    report = json.loads(Path(args[0]).read_text())
    assert report['status'] == h['QUALIFIED'] and report['protectedValidationPassed'] is True
    assert report['nativeStorage']['reopenVerified'] is True and report['acceptedArt'] is False
    h['source_identity'](h['read'](report['input']), report)
    namespace = {'__name__': 'sleeve47_unchanged_dense28', '__file__': str(h['checked'](ORIGINAL)),
                 'WRAPPER': __file__, 'ORIGINAL': ORIGINAL}
    exec(compile(transformed_source(), namespace['__file__'], 'exec'), namespace)
    namespace['main']()
