"""Exact reconstructive14 admission with the single corrected15 authority."""
import hashlib
from pathlib import Path

ORIGINAL = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/connected_cap_binding.py',
            'sha256': '12168f54407c6473678d832f6545f736f7e80fc528e026d8b4e5dfaea6ec4145'}
_path = Path(__file__).resolve().parents[4]/ORIGINAL['path']
assert hashlib.sha256(_path.read_bytes()).hexdigest() == ORIGINAL['sha256']
_source = _path.read_text()
for _old, _new in {
    'selected-hoodie-joints77/connected_cap.py': 'selected-hoodie-joints77/connected_cap15.py',
    '3418b3172fbef6bac584d526bb72bd332878050ef473bf05320169096e2c743e':
        '7b8c859863e9c7e8b1224973f4e7365cae2c022c7e8ceae6730ec806d1da65fc',
}.items():
    assert _source.count(_old) == 1
    _source = _source.replace(_old, _new)
exec(compile(_source, str(_path), 'exec'), globals())
