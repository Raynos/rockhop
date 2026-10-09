#!/usr/bin/env python3
"""PNG lossless recompression; verify decoded RGBA byte identity, including hidden RGB."""
import hashlib, json, subprocess, time
from pathlib import Path
from PIL import Image

out = Path('harness/out/rider-rebuild/download-opt01/textures01')
original = json.loads((out/'inventory.json').read_text())
target = out/'lossless-png'
target.mkdir(exist_ok=True)
rows=[]
for image in original['images']:
    source=Path(image['path'])
    destination=target/source.name
    command=['/opt/homebrew/bin/oxipng','-o','2','--threads','2','--out',str(destination),str(source)]
    start=time.monotonic()
    log=target/f"image-{image['image']:02d}-optimize.log"
    with log.open('w') as handle:
        subprocess.run(command,stdout=handle,stderr=subprocess.STDOUT,check=True)
    if not destination.exists():
        destination.write_bytes(source.read_bytes())
    a=Image.open(source).convert('RGBA')
    b=Image.open(destination).convert('RGBA')
    assert a.size==b.size and a.tobytes()==b.tobytes()
    rows.append({'image':image['image'],'originalBytes':image['bytes'],'pngBytes':destination.stat().st_size,
                 'decodedRGBAIdentical':True,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                 'seconds':time.monotonic()-start,'command':command})
    (out/'lossless-png.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows[-1]),flush=True)
