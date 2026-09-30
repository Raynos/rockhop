"""Keep meshopt geometry in GLB and restore shared maps after CLI embedding.

Image bytes are matched by SHA-256; exporter order is not trusted.
The CLI places images before compressed mesh data; fail if that changes.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = path.read_bytes()
length = struct.unpack_from('<I', data, 12)[0]
doc = json.loads(data[20:20+length])
blob = data[28+length:]
views = doc['bufferViews']
names = {hashlib.sha256(p.read_bytes()).hexdigest(): p.name for p in path.parent.iterdir()
         if p.suffix in ('.png', '.jpg', '.webp')}
removed = set()
for im in doc.get('images', []):
    vi = im.pop('bufferView')
    view = views[vi]
    offset = view.get('byteOffset', 0)
    image = blob[offset:offset+view['byteLength']]
    digest = hashlib.sha256(image).hexdigest()
    if digest not in names:
        raise RuntimeError('Exporter changed image bytes: '+digest)
    im['uri'] = names[digest]
    removed.add(vi)
cut = max(views[i].get('byteOffset', 0) + views[i]['byteLength'] for i in removed)
cut = (cut+3)//4*4
mapping = {}
retained = []
for i, view in enumerate(views):
    if i in removed:
        continue
    mapping[i] = len(retained)
    if view['buffer'] == 0:
        assert view.get('byteOffset', 0) >= cut
        view['byteOffset'] = view.get('byteOffset', 0)-cut
    compressed = view.get('extensions', {}).get('EXT_meshopt_compression')
    if compressed and compressed['buffer'] == 0:
        assert compressed.get('byteOffset', 0) >= cut
        compressed['byteOffset'] = compressed.get('byteOffset', 0)-cut
    retained.append(view)
doc['bufferViews'] = retained
for accessor in doc['accessors']:
    if 'bufferView' in accessor:
        accessor['bufferView'] = mapping[accessor['bufferView']]
blob = blob[cut:]
doc['buffers'][0]['byteLength'] = len(blob)
js = json.dumps(doc, separators=(',', ':')).encode()
js += b' ' * (-len(js)%4)
blob += b'\0' * (-len(blob)%4)
path.write_bytes(struct.pack('<III', 0x46546C67, 2, 28+len(js)+len(blob))+
                 struct.pack('<II', len(js), 0x4E4F534A)+js+
                 struct.pack('<II', len(blob), 0x004E4942)+blob)
print(path.name, 'shared maps restored;', len(data), '->', path.stat().st_size, 'bytes')
