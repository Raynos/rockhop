"""Run the pinned boot recipe, preserving array witnesses on rejection."""
import hashlib
import json
import runpy
import sys
import traceback
from pathlib import Path
import numpy as np

recipe = Path(__file__).resolve().with_name('fit-selected-boots03.py')
arguments = sys.argv[sys.argv.index('--') + 1:]
assert len(arguments) == 1
output = Path(arguments[0]).resolve()
assert output.is_relative_to(recipe.parents[4] / 'harness/out/rider-rebuild') and not output.exists()
sys.argv = [str(recipe), '--', str(output)]
assert hashlib.sha256(recipe.read_bytes()).hexdigest() == '5aaf5dc2641e801001745edcece73d93e168e19f0d32575de4db4bbb13ff9846'
try:
    runpy.run_path(str(recipe), run_name='__main__')
except BaseException as error:
    tb, scope = error.__traceback__, None
    while tb:
        if Path(tb.tb_frame.f_code.co_filename) == recipe:
            scope = {**tb.tb_frame.f_globals, **tb.tb_frame.f_locals}
        tb = tb.tb_next
    if scope is not None:
        output.mkdir(parents=True, exist_ok=True)
        witness = {key: value for key, value in scope.items()
                   if isinstance(value, np.ndarray) and value.dtype.kind in 'fibu' and value.size < 3000000}
        if 'bm' in scope:
            try:
                bm = scope['bm']; bm.verts.index_update()
                witness['liveCutVertices'] = np.asarray([tuple(v.co) for v in bm.verts])
                witness['liveCutFacesFlat'] = np.asarray([v.index for f in bm.faces for v in f.verts])
                witness['liveCutFaceSizes'] = np.asarray([len(f.verts) for f in bm.faces])
            except (ReferenceError, AttributeError):
                pass
        np.savez_compressed(output / 'rejected-array-witness.npz', **witness)
        record = {'accepted': False, 'error': type(error).__name__ + ': ' + str(error),
                  'side': scope.get('side'), 'arrayNames': list(witness), 'traceback': traceback.format_exc(),
                  'recipeSHA256': hashlib.sha256(recipe.read_bytes()).hexdigest(),
                  'wrapperSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        (output / 'rejection-wrapper.json').write_text(json.dumps(record, indent=2) + '\n')
    raise
