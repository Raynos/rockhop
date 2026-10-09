"""Exact actual-bike endpoint14 sheets with corrected15 authority."""
import hashlib
from pathlib import Path

ORIGINAL = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/connected_cap_views.py',
            'sha256': 'b34bfe8b3ba72247629238eb769f3c823879a578aac573f056212e279a2a0277'}
_path = Path(__file__).resolve().parents[4]/ORIGINAL['path']
assert hashlib.sha256(_path.read_bytes()).hexdigest() == ORIGINAL['sha256']
_source = _path.read_text()
for _old, _new in {
    "'connected_cap.py'": "'connected_cap15.py'",
    'selected-hoodie-joints77/connected_cap_binding.py': 'selected-hoodie-joints77/connected_cap_binding15.py',
    '12168f54407c6473678d832f6545f736f7e80fc528e026d8b4e5dfaea6ec4145':
        'fbbc65482ce51632ae657c0693cc6515fce8807af197bf463a936e9128f25b40',
}.items():
    assert _source.count(_old) == 1
    _source = _source.replace(_old, _new)
exec(compile(_source, str(_path), 'exec'), globals())
