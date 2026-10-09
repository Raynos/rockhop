#!/usr/bin/env python3
"""Match native ETC1 GPU blocks and pixels to actual pinned ETC2-compatible output."""
import argparse, hashlib, json, struct
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=Path('harness/out/rider-rebuild/mobile-textures02/etc1s01'))
args = parser.parse_args()
p = args.out
ktx = (p / 'native-etc1/image-01_transcoded_ETC1_RGB_layer_0000.ktx').read_bytes()
assert ktx[:12] == b'\xabKTX 11\xbb\r\n\x1a\n'
fields = struct.unpack_from('<13I', ktx, 12)
assert fields[0] == 0x04030201 and fields[4] == 0x8d64
assert fields[6:8] == (2048, 2048) and fields[10] == 1 and fields[11] == 12
offset = 64 + fields[12]
levels = []
for level in range(fields[11]):
    size = struct.unpack_from('<I', ktx, offset)[0]
    offset += 4
    blocks = ktx[offset:offset + size]
    runtime = (p / 'etc1s-max-etc-blocks' / f'image-01-level-{level}.blocks').read_bytes()
    assert blocks == runtime
    levels.append({'level': level, 'bytes': size, 'sha256': hashlib.sha256(blocks).hexdigest(), 'nativeETC1RuntimeETC2CompatibleBlocksExact': True})
    offset += size + (-size % 4)
assert offset == len(ktx)
with Image.open(p / 'native-etc1/image-01_unpacked_rgb_ETC1_RGB_level_0_face_0_layer_0000.png') as image:
    pixels = image.convert('RGBA').tobytes()
assert pixels == (p / 'etc1s-max-decoded-rgba/image-01.rgba').read_bytes()
report = {'accepted': False, 'pass': True, 'levels': levels, 'nativeETC1PixelsMatchPinnedRGBA32': True,
          'nativeRGBA_SHA256': hashlib.sha256(pixels).hexdigest(),
          'pinnedLoaderFormat': 'r186 ETC1S prefers ETC2RGB without alpha when etc2Supported; these ETC1 blocks are valid ETC2RGB subset. BC7 is selected only when higher-priority ETC2/ETC1 unavailable.',
          'limits': ['Native ETC1 linear software pixels prove this GPU block decode, not material rendering/phone acceptance.', 'BC7 transcodes pass but BC7 decoded pixels are not measured.']}
(p / 'native-pixel-block-proof.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'pass': True, 'levels': len(levels), 'pixelsExact': True}))
