#!/usr/bin/env python3
"""Prove composed runtime maps against native-verified source families."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
p.add_argument('--graft-receipt', type=Path, required=True)
args = p.parse_args()
base = args.directory
composition = json.loads((base / 'composition.json').read_text())
runtime = json.loads((base / 'uastc-rdo05-runtime-transcode.json').read_text())
graft = json.loads(args.graft_receipt.read_text())
assert graft['output']['sha256'] == composition['sourceGraft']['sha256']
components = {info['image']:(part['name'],local) for part in graft['components'] for local,kind in enumerate(['albedo','orm','normal']) for info in [part['images'][kind]]}
rows = []
def sha(data):
    return hashlib.sha256(data).hexdigest()
for row, rt in zip(composition['maps'], runtime):
    index,old = row['image'],row['sourceImage']
    assert rt['image'] == index and rt['levels'] == row['levels']
    assert all(f['allLevelsSucceeded'] for f in rt['formats'])
    if old in components:
        name, origin = components[old]
        src = Path('harness/out/rider-rebuild/mobile-textures02/components01') / name
    else:
        origin = old
        src = Path('harness/out/rider-rebuild/download-opt01/textures01/atlas01')
    offset = 1 if old == 11 else 0
    native_path = src / 'uastc-rdo05-astc-proof.json'
    native = {r['image']:r for r in json.loads(native_path.read_text())}[origin]
    assert native['astcSoftwareDecodedRGBAIdenticalToRuntimeRGBA']
    assert all(level['nativeBlocksByteIdentical'] for level in native['levels'])
    blocks = []
    for level in range(row['levels']):
        current = (base / 'uastc-rdo05-astc-blocks' / f'image-{index:02d}-level-{level}.blocks').read_bytes()
        reference = (src / 'uastc-rdo05-astc-blocks' / f'image-{origin:02d}-level-{level+offset}.blocks').read_bytes()
        assert current == reference
        blocks.append({'level':level,'sourceLevel':level+offset,'bytes':len(current),'sha256':sha(current),'nativeVerifiedSourceBlocksExact':True})
    if offset:
        png = src / 'uastc-rdo05-native-astc' / f'image-{origin:02d}' / f'image-{origin:02d}_unpacked_rgba_ASTC_LDR_4X4_RGBA_level_1_face_0_layer_0000.png'
        with Image.open(png) as image:
            reference = image.convert('RGBA').tobytes()
    else:
        reference = (src / 'uastc-rdo05-astc-decoded-rgba' / f'image-{origin:02d}.rgba').read_bytes()
    current = (base / 'uastc-rdo05-decoded-rgba' / f'image-{index:02d}.rgba').read_bytes()
    assert current == reference
    rows.append({'image':index,'sourceImage':old,'sourceFamily':str(src),'sourceLocalImage':origin,'sourceMip':offset,
                 'nativeProofPath':str(native_path),'nativeProofSHA256':sha(native_path.read_bytes()),'levels':blocks,
                 'pinnedRGBAIdenticalToNativeASTCLinearPixels':True,'level0RGBA_SHA256':sha(current),
                 'width':rt['width'],'height':rt['height'],'hasAlpha':rt['hasAlpha']})
assert len(rows) == len(runtime) == len(composition['maps'])
result = {'accepted':False,'pass':True,'candidate':composition['candidate'],'maps':rows,
          'nativeVerifiedASTCBlocksExactEveryMip':True,'nativeASTCLinearPixelsMatchPinnedRuntimeEveryMap':True,
          'scope':'Actual composed KTX runtime transcodes versus prior independent native ASTC decodes. Jeans ORM base is native source mip1. No hardware sRGB/filtering, BC7 pixel or moving/device judgment.'}
(base / 'native-runtime-reuse.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'pass':True,'maps':len(rows),'mips':sum(len(row['levels']) for row in rows)}))
