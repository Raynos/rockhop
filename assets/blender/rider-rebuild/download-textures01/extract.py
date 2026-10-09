#!/usr/bin/env python3
"""Inventory and extract selected embedded PNGs without modifying the master GLB."""
import argparse, hashlib, io, json, struct
from pathlib import Path
from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,default=Path('harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb'))
parser.add_argument('--out',type=Path,default=Path('harness/out/rider-rebuild/download-opt01/textures01'))
args=parser.parse_args()
blob=args.source.read_bytes()
size=struct.unpack_from('<I',blob,12)[0]
doc=json.loads(blob[20:20+size])
binary=blob[28+size:]
(args.out/'original').mkdir(parents=True,exist_ok=True)
rows=[]
for index,image in enumerate(doc['images']):
    view=doc['bufferViews'][image['bufferView']]
    assert view.get('buffer',0)==0 and image['mimeType']=='image/png'
    offset=view.get('byteOffset',0)
    payload=binary[offset:offset+view['byteLength']]
    target=args.out/'original'/f'image-{index:02d}.png'
    target.write_bytes(payload)
    pixels=Image.open(io.BytesIO(payload))
    usages=[]
    for mi,material in enumerate(doc['materials']):
        pbr=material.get('pbrMetallicRoughness',{})
        for slot,texture in [('baseColorTexture',pbr.get('baseColorTexture')),
                             ('metallicRoughnessTexture',pbr.get('metallicRoughnessTexture')),
                             ('normalTexture',material.get('normalTexture'))]:
            if texture and doc['textures'][texture['index']]['source']==index:
                usages.append({'material':mi,'name':material['name'],'slot':slot})
    assert usages
    color=all(u['slot']=='baseColorTexture' for u in usages)
    assert color or all(u['slot']!='baseColorTexture' for u in usages), 'Mixed transfer usages require duplication'
    rows.append({'image':index,'name':image.get('name'),'path':str(target),'bytes':len(payload),
                 'sha256':hashlib.sha256(payload).hexdigest(),'size':pixels.size,'mode':pixels.mode,
                 'alphaExtrema':pixels.convert('RGBA').getchannel('A').getextrema(),'usage':usages,'srgb':color})
report={'source':str(args.source),'sourceBytes':len(blob),'sourceSha256':hashlib.sha256(blob).hexdigest(),
        'originalTextureBytes':sum(row['bytes'] for row in rows),'images':rows}
(args.out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
