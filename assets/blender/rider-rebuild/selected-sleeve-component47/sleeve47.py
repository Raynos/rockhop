"""Explicit47 component adapter around exact28 + save-lifetime38.

Only intake, present-object scope, provenance, output path and lifetime-helper
binding change. No fit, geometry, material, source-field or tolerance change.
"""
import gc
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
helper47 = runpy.run_path(str(HERE/'component.py'))
wrapper38 = runpy.run_path(str(helper47['checked'](helper47['SLEEVE38'])))
ORIGINAL = wrapper38['ORIGINAL']


def transformed_source():
    source = wrapper38['transformed_source']()
    substitutions = {
        "ROOT/'harness/out/rider-rebuild/selected-sleeve-rebuild28'":
            "ROOT/'harness/out/rider-rebuild/selected-sleeve-component47'",
        "assert checkpoint['originalHoodieUnchangedBeforeSave'] and checkpoint['exact75RestUnchanged']":
            "helper47['intake_gate'](checkpoint)",
        "for row in checkpoint['gloveObjects'].values(): pin(row)":
            "for row in helper47['read'](checkpoint['componentReceipt'])['objects'].values(): pin(row['ancestry'])",
        "== B.VISIBLE": "== helper47['MESHES']",
        "B.VISIBLE-{'RiderHoodie'} | {'RiderBody__FullAnatomyReference'}": "helper47['PROTECTED']",
        "checkpoint['pin']": "helper47['pin']",
        "checkpoint['save_pending']": "helper47['save_pending']",
        "Original28 geometric construction unchanged; this is a save-lifetime correction only.":
            "Original28 geometric construction and lifetime38 reused; explicit47 component-only intake and preservation scope."}
    for old, new in substitutions.items():
        assert source.count(old) == (2 if old == "checkpoint['pin']" else 1), ('Unexpected frozen38 source', old)
        source = source.replace(old, new)
    return source


if __name__ == '__main__':
    namespace = {'__name__': 'sleeve47_exact28_component', '__file__': str(helper47['checked'](ORIGINAL)),
                 'helper47': helper47, 'ORIGINAL': ORIGINAL, 'WRAPPER': __file__, 'gc': gc}
    exec(compile(transformed_source(), namespace['__file__'], 'exec'), namespace)
    namespace['main']()
