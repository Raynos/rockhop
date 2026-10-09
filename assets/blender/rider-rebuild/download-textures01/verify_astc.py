#!/usr/bin/env python3
"""Decode ASTC pixels and prove blocks match the actual pinned runtime output."""
import argparse, hashlib, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument('--variant',default='uastc-rdo05')
parser.add_argument('--images',help='Explicit comma-separated subset for early diagnostics')
parser.add_argument('--out',type=Path,default=Path('harness/out/rider-rebuild/download-opt01/textures01'))
args=parser.parse_args()
variant=args.variant
out=args.out
maps=json.loads((out/f'{variant}-encode.json').read_text())
selected=set(map(int,args.images.split(','))) if args.images else None
rows=[]
for image in maps:
    index=image['image']
    if selected is not None and index not in selected:
        continue
    basename=f'image-{index:02d}'
    destination=out/f'{variant}-native-astc'/basename
    destination.mkdir(parents=True,exist_ok=True)
    command=['/opt/homebrew/bin/basisu','-unpack','-file',image['path'],'-format_only','10',
             '-no_ktx','-max_threads','2','-output_path',str(destination)]
    with (destination/'decode.log').open('w') as handle:
        subprocess.run(command,stdout=handle,stderr=subprocess.STDOUT,check=True)
    levels=[]
    for level in range(image['levels']):
        prefix=f'{basename}_unpacked_ASTC_LDR_4X4_RGBA_level_{level}_face_0_layer_0000'
        encoded=(destination/f'{prefix}.astc').read_bytes()
        runtime=(out/f'{variant}-astc-blocks'/f'{basename}-level-{level}.blocks').read_bytes()
        assert encoded[16:]==runtime, f'Pinned runtime ASTC block mismatch {index}/{level}'
        levels.append({'level':level,'gpuBlockBytes':len(runtime),'runtimeBlockSHA256':hashlib.sha256(runtime).hexdigest(),
                       'nativeBlocksByteIdentical':True})
    png=destination/f'{basename}_unpacked_rgba_ASTC_LDR_4X4_RGBA_level_0_face_0_layer_0000.png'
    pixels=np.asarray(Image.open(png).convert('RGBA'))
    runtime_pixels=np.memmap(out/f'{variant}-decoded-rgba'/f'{basename}.rgba',dtype=np.uint8,shape=pixels.shape)
    different=np.abs(pixels.astype(np.int16)-runtime_pixels.astype(np.int16))
    row={'image':index,'levels':levels,'astcSoftwareDecodedRGBAIdenticalToRuntimeRGBA':bool(np.array_equal(pixels,runtime_pixels)),
         'astcSoftwareVsRuntimeRGBAAbsMax':int(different.max()),
         'profile':'Basisu native ASTC linear software decode; sRGB GPU filtering/render remains a played-review gate',
         'nativeLevel0RGBA_SHA256':hashlib.sha256(pixels.tobytes()).hexdigest()}
    actual_dir=out/f'{variant}-astc-decoded-rgba'
    actual_dir.mkdir(exist_ok=True)
    (actual_dir/f'{basename}.rgba').write_bytes(pixels.tobytes())
    rows.append(row)
    (out/f'{variant}-astc-proof.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:v for k,v in row.items() if k!='levels'}),flush=True)
