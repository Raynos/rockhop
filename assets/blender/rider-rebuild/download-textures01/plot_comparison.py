#!/usr/bin/env python3
"""Diagnostic texel crop comparison; supplements played evidence, never art acceptance."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

out=Path('harness/out/rider-rebuild/download-opt01/textures01')
inventory=json.loads((out/'inventory.json').read_text())['images']
canvas=Image.new('RGB',(1084,1000),'#eeeeee')
draw=ImageDraw.Draw(canvas)
font=ImageFont.load_default(size=14)
small=ImageFont.load_default(size=12)
draw.text((12,12),'Texel diagnostics: worst source-authored grid crops; played review pending',font=font,fill='black')
for column,title in enumerate(['Original PNG','UASTC no RDO','RDO 0.5 ASTC decode','Max RGB delta x16']):
    draw.text((12+column*268,42),title,font=font,fill='black')
rows=[]
for row_index,index in enumerate([0,4,10]):
    record=inventory[index]
    source=np.asarray(Image.open(record['path']).convert('RGBA'))
    height,width=source.shape[:2]
    baseline=np.memmap(out/'uastc-decoded-rgba'/f'image-{index:02d}.rgba',dtype=np.uint8,shape=source.shape)
    candidate=np.memmap(out/'uastc-rdo05-astc-decoded-rgba'/f'image-{index:02d}.rgba',dtype=np.uint8,shape=source.shape)
    # Choose the 256x256 grid crop with greatest mean authored RGB absolute error.
    best=(-1,0,0)
    for y in range(0,height,256):
        for x in range(0,width,256):
            a=source[y:y+256,x:x+256]
            b=candidate[y:y+256,x:x+256]
            mask=a[:,:,3]>0
            if np.count_nonzero(mask)<16384:
                continue
            error=np.mean(np.abs(a[:,:,:3].astype(np.int16)-b[:,:,:3].astype(np.int16))[mask])
            if error>best[0]:
                best=(float(error),x,y)
    error,x,y=best
    a=source[y:y+256,x:x+256,:3]
    b=baseline[y:y+256,x:x+256,:3]
    c=candidate[y:y+256,x:x+256,:3]
    delta=np.max(np.abs(a.astype(np.int16)-c.astype(np.int16)),axis=2)
    for column,pixels in enumerate([a,b,c]):
        canvas.paste(Image.fromarray(np.asarray(pixels)),(12+column*268,110+row_index*296))
    heat=np.zeros((*delta.shape,3),dtype=np.uint8)
    heat[:,:,0]=np.minimum(255,delta*16).astype(np.uint8)
    canvas.paste(Image.fromarray(heat),(12+3*268,110+row_index*296))
    rows.append({'image':index,'crop':[x,y,256,256],'selection':'greatest mean source-authored RGB absolute error grid crop',
                 'meanAuthoredAbsoluteRGB8bit':error})
    draw.text((12,82+row_index*296),f"Map {index}: {record['name']}; crop ({x},{y}) 256 x 256",font=small,fill='black')
draw.text((12,978),'Native ASTC linear software profile; GPU blocks match pinned Three. sRGB played review pending.',font=small,fill='black')
canvas.save(out/'uastc-rdo05-texel-proof.png')
(out/'uastc-rdo05-texel-proof.json').write_text(json.dumps(rows,indent=2)+'\n')
