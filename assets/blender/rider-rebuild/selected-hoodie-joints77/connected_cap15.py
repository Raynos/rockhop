"""Exact frozen14 construction; clamp only a roundoff-negative torso remainder.

Actual body samples/own-arm values, geometry and the single solve stay intact.
"""
import hashlib
from pathlib import Path

ORIGINAL = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/connected_cap.py',
            'sha256': '3418b3172fbef6bac584d526bb72bd332878050ef473bf05320169096e2c743e'}
_root = Path(__file__).resolve().parents[4]
_path = _root/ORIGINAL['path']
assert hashlib.sha256(_path.read_bytes()).hexdigest() == ORIGINAL['sha256']
_source = _path.read_text()
_old = 'result[spine_ids] = (1-result.sum())*spine/spine.sum()'
_new = 'result[spine_ids] = max(0., 1-result.sum())*spine/spine.sum()'
assert _source.count(_old) == 1
exec(compile(_source.replace(_old, _new), str(_path), 'exec'), globals())
