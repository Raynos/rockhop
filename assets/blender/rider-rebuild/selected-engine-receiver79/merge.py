"""Thin reviewed51/47/38 merger reuse for actual compact77 + unchanged52."""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = runpy.run_path(str(HERE/'component.py'))
BASE51 = {'path':'assets/blender/rider-rebuild/selected-distal-wardrobe51/merge51.py',
          'sha256':'e69052249c0e4317cc8a5f69dddeed4c7e605bba890e7136565f6b1b5a49aea0'}


def wrapper():
    source = c['checked'](BASE51).read_text()
    changes = {
        'selected-distal-wardrobe51/merge':'selected-engine-receiver79/merge',
        "HERE/'dense51.py'":"HERE/'dense.py'",
        'UNACCEPTED-selected-dressed-distal51.blend':'UNACCEPTED-selected-dressed-receiver79.blend',
        'UNACCEPTED_DISTAL51_TO_NATIVE52_SEPARATE_COMPARISON_PASS_REPLAY_ART_PENDING':
            'UNACCEPTED_RECEIVER79_TO_NATIVE52_SEPARATE_COMPARISON_PASS_REPLAY_ART_PENDING',
        'SINGLE_DISTAL51_MERGE_NATIVE_WITNESS_ONLY':'SINGLE_RECEIVER79_MERGE_NATIVE_WITNESS_ONLY',
        'UNACCEPTED_MERGED51_ORIGINAL08_MATRIX_REPLAY_PASS_ART_PENDING':
            'UNACCEPTED_MERGED79_ORIGINAL08_MATRIX_REPLAY_PASS_ART_PENDING'}
    for old,new in changes.items():
        assert source.count(old) >= 1,old
        source = source.replace(old,new)
    # The reviewed51 factory retains exact47 code and its own scoped globals.
    # Its final donor verification resolves this owned component.py instead.
    namespace = {'__name__':'receiver79_reviewed51','__file__':__file__}
    exec(compile(source,str(c['checked'](BASE51)),'exec'),namespace)
    original_factory = namespace['methods']
    def factory():
        m = original_factory()
        original_transplant = m['transplant_source']
        def transplant_source():
            src = original_transplant()
            old = 'selected_materials = list(obj.data.materials)'
            assert src.count(old) == 1
            return src.replace(old,"selected_materials = list(donor.data.materials) if name == 'RiderHoodie' else list(obj.data.materials)")
        m['transplant_source'] = transplant_source
        return m
    namespace['methods'] = factory
    return namespace


def methods(): return wrapper()['methods']()


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    m = wrapper()
    if args[0] == 'freeze': m['freeze'](*args[1:])
    elif args[0] == 'compare': m['methods']()['compare'](*args[1:])
    else:
        import bpy
        inner = m['methods']()
        if args[0] in ('merge','replay'): inner[args[0]](*args[1:],bpy)
        else:
            assert args[0] in ('target','source','merged')
            inner['witness'](args[0],args[1],bpy)
