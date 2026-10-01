"""Append a padded cheek bake without changing occupied texels or GLB geometry."""
from pathlib import Path
import copy
import hashlib
import io
import json
import struct
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

source, destination, evidence = map(Path, sys.argv[1:])
assert not destination.exists(), 'Freeze every trial; never overwrite a master'
destination.parent.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
original = source.read_bytes()
sha = lambda data: hashlib.sha256(data).hexdigest()
length = struct.unpack_from('<I', original, 12)[0]
document = json.loads(original[20:20 + length])
binary = original[28 + length:]
assert document['images'][6]['name'] == 'CPU baked coherent cheek skin'
view = document['bufferViews'][document['images'][6]['bufferView']]
image_bytes = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
image = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
pixels = np.asarray(image).copy()
occupied = pixels[:, :, :3].max(axis=2) > 0
assert occupied.sum() > 500000 and pixels.shape[:2] == (1024, 1024)
distance, nearest = distance_transform_edt(~occupied, return_indices=True)
margin = (~occupied) & (distance <= 16)
padded = pixels.copy()
padded[margin, :3] = pixels[nearest[0][margin], nearest[1][margin], :3]
assert np.array_equal(padded[occupied], pixels[occupied])
assert np.array_equal(padded[~margin], pixels[~margin])
assert np.array_equal(padded[:, :, 3], pixels[:, :, 3]), 'Alpha remains exact'
encoded = io.BytesIO()
Image.fromarray(padded).save(encoded, format='PNG')
encoded = encoded.getvalue()
updated = copy.deepcopy(document)
offset = len(binary)
updated['images'][6]['bufferView'] = len(updated['bufferViews'])
updated['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(encoded)})
new_binary = binary + encoded
new_binary += b'\0' * (-len(new_binary) % 4)
updated['buffers'][0]['byteLength'] = len(new_binary)
json_bytes = json.dumps(updated, separators=(',', ':')).encode()
json_bytes += b' ' * (-len(json_bytes) % 4)
total = 12 + 8 + len(json_bytes) + 8 + len(new_binary)
result = (struct.pack('<III', 0x46546c67, 2, total) + struct.pack('<II', len(json_bytes), 0x4e4f534a)
          + json_bytes + struct.pack('<II', len(new_binary), 0x004e4942) + new_binary)
assert new_binary[:len(binary)] == binary
for key in ['meshes', 'accessors', 'skins', 'nodes', 'materials', 'animations', 'textures', 'samplers']:
    assert updated.get(key) == document.get(key), key
assert source.read_bytes() == original
destination.write_bytes(result)
Image.fromarray(padded).save(evidence / 'padded-cheek-bake.png')
report = {'source': str(source), 'sourceSHA256': sha(original), 'destination': str(destination),
          'destinationSHA256': sha(result), 'marginPixels': 16, 'occupiedPixels': int(occupied.sum()),
          'backgroundPixelsPadded': int(margin.sum()), 'allOriginalBinaryBytesRetainedExact': True,
          'occupiedTexelsAndAlphaExact': True, 'geometryUVSkinMorphClipsMaterialsExact': True,
          'sourceUnchanged': True, 'CPUOnly': True,
          'mechanism': 'Extend baked skin into black gutter using nearest occupied texel; preserve all occupied pixels. Append image, redirect only image6 bufferView.',
          'limits': 'Hypothesis trial, appearance unaccepted until actual matched replay. No eye anatomy, source resolution or skin color change.'}
(evidence / 'bake-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
