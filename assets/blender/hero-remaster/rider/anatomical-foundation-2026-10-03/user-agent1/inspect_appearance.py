"""Read-only exact approved donor material/image/vertex-colour registration."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--donor', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args(); donor, out = Path(a.donor).resolve(), Path(a.out).resolve()
sha = lambda b: hashlib.sha256(b).hexdigest()
raw = donor.read_bytes(); assert sha(raw) == 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
length = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + length]); binary = raw[28 + length:]
out.mkdir(parents=True, exist_ok=True)
if (out / 'material-registration.json').exists():
    raise RuntimeError('Frozen registration exists')
images = []
for index, image in enumerate(doc['images']):
    view = doc['bufferViews'][image['bufferView']]; data = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
    file = out / f'donor-image-{index}.png'; file.write_bytes(data)
    images.append({'index': index, 'name': image.get('name'), 'path': str(file), 'bytes': len(data), 'sha256': sha(data)})
rows = []
for mid, mesh in enumerate(doc['meshes']):
    for pid, p in enumerate(mesh['primitives']):
        rows.append({'mesh': mid, 'primitive': pid, 'material': p['material'],
            'vertices': doc['accessors'][p['attributes']['POSITION']]['count'],
            'attributes': {n: {'componentType': doc['accessors'][i]['componentType'], 'type': doc['accessors'][i]['type'],
                'minimum': doc['accessors'][i].get('min'), 'maximum': doc['accessors'][i].get('max')} for n, i in p['attributes'].items()}})
report = {'status': 'READ-ONLY appearance donation registration, no geometry/admission or art acceptance',
    'donorSHA256': sha(raw), 'recipeSHA256': sha(Path(__file__).read_bytes()), 'materials': doc['materials'], 'textures': doc['textures'],
    'images': images, 'primitives': rows, 'limits': ['Exact protected head UV/PBR bytes are preserved; old source anatomy/rig/binds not adopted.',
        'Cloth texture/details may transfer to clean original patterns; Agent2 donors are optional support.']}
(out / 'material-registration.json').write_text(json.dumps(report, indent=2) + '\n')
assert sha(donor.read_bytes()) == report['donorSHA256']
print('APPEARANCE_REGISTRATION', sha((out / 'material-registration.json').read_bytes()), flush=True)
