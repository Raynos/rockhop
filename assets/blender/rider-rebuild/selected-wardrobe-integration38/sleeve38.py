"""Execute exact sleeve28 geometry; change only finished-scratch/save lifetime.

Parent guarded CPU2 only. No threshold, contact, UV, map, skin or topology
method is changed. The unmodified qualifier28 consumes construction.json only
after qualify-sleeve38.py succeeds in a separate process.
"""
import gc
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
checkpoint = runpy.run_path(str(HERE/'sleeve_checkpoint.py'))
ORIGINAL = {'path': 'assets/blender/rider-rebuild/selected-sleeve-rebuild28/author.py',
            'sha256': 'e6a13cd8bc1d0ec18776da9fb4c8ec83598f7365807478ec9de6a87b394fa6e1'}


def transformed_source():
    source = checkpoint['checked'](ORIGINAL).read_text()
    start = source.index('    assert before == {o.name: geometry(o) for o in protected}\n')
    end = source.index("\n\n\nif __name__ == '__main__': main()", start)
    tail = '''    assert rest_before == rest(rig), 'Cheap native75 rest changed before save'
    expected = {'geometry': before, 'rest': rest_before}
    report = {'acceptedArt': False, 'recipeSHA256': checkpoint['pin'](WRAPPER)['sha256'],
              'originalConstructor': ORIGINAL,
              'actualFullReferenceExactToSavedBasisAndTriangles': True,
              'continuousClothFit': fit_report, 'sleeves': sleeve_reports, 'ancestry': ancestry,
              'inheritedDegenerateCleanup': cleanup,
              'field': checkpoint['pin'](out/'complete-sleeve-field.npz'),
              'limits': ['Original28 geometric construction unchanged; this is a save-lifetime correction only.',
                         'Dense six full-triangle relations and independent generic/bike moving enclosure remain required.',
                         'Source outward PBR, retained UVs and source-prefix fields retained; original turned lip replacement remains an unaccepted detail change.',
                         'Protected geometry and rest are pending until separate reopened qualification.']}
    # All returned native fields and source ancestry have finished before any
    # scratch is released. No Blender ID or actual mesh datablock is removed.
    reference.close()
    del hp, hf, surgery, source, world, faces, moved, changed, field, reference
    del bp, bf, profiles, actual_gloves, glove_trees, profile, gp, gf, dump, data, xyz
    gc.collect()
    checkpoint['save_pending'](out, config_path, config, expected, report, bpy)
'''
    return source[:start]+tail+source[end:]


if __name__ == '__main__':
    namespace = {'__name__': 'sleeve28_checkpoint38', '__file__': str(checkpoint['checked'](ORIGINAL)),
                 'checkpoint': checkpoint, 'ORIGINAL': ORIGINAL, 'WRAPPER': __file__, 'gc': gc}
    exec(compile(transformed_source(), namespace['__file__'], 'exec'), namespace)
    namespace['main']()
