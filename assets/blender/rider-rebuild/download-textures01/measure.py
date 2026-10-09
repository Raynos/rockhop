#!/usr/bin/env python3
"""Compare source decoded texels with pinned runtime RGBA transcode in bounded row chunks."""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

out=Path('harness/out/rider-rebuild/download-opt01/textures01')
variant=sys.argv[1] if len(sys.argv)>1 else 'uastc'
rows=[]
for image in json.loads((out/'inventory.json').read_text())['images']:
    src=Image.open(image['path']).convert('RGBA')
    width,height=src.size
    dst=np.memmap(out/f'{variant}-decoded-rgba'/f"image-{image['image']:02d}.rgba",dtype=np.uint8,mode='r',shape=(height,width,4))
    hist=np.zeros((4,256),dtype=np.int64)
    squared=np.zeros(4)
    bias=np.zeros(4)
    angle_hist=np.zeros(18001,dtype=np.int64)
    angle_sum=angle_count=0
    exact=0
    for y in range(0,height,64):
        a=np.asarray(src.crop((0,y,width,min(height,y+64))),dtype=np.int16)
        b=np.asarray(dst[y:y+64],dtype=np.int16)
        d=b-a
        absdiff=np.abs(d)
        for c in range(4):
            hist[c]+=np.bincount(absdiff[:,:,c].ravel(),minlength=256)
        squared+=np.sum(d.astype(np.float64)**2,axis=(0,1))
        bias+=np.sum(d,axis=(0,1))
        exact+=int(np.count_nonzero(np.all(d==0,axis=2)))
        if any(u['slot']=='normalTexture' for u in image['usage']):
            # Restrict angles to authored alpha>0 pixels; background values are not normals.
            mask=a[:,:,3]>0
            av=a[:,:,:3].astype(np.float32)/127.5-1
            bv=b[:,:,:3].astype(np.float32)/127.5-1
            denom=np.linalg.norm(av,axis=2)*np.linalg.norm(bv,axis=2)
            angles=np.degrees(np.arccos(np.clip(np.sum(av*bv,axis=2)/np.maximum(denom,1e-10),-1,1)))[mask]
            angle_sum+=float(np.sum(angles));angle_count+=angles.size
            angle_hist+=np.bincount(np.minimum(18000,np.rint(angles*100).astype(np.int32)),minlength=18001)
    count=width*height
    channels=[]
    for c,name in enumerate('RGBA'):
        nonzero=np.nonzero(hist[c])[0]
        cumulative=np.cumsum(hist[c])
        mse=float(squared[c]/count)
        channels.append({'channel':name,'rmse8bit':math.sqrt(mse),'psnrDB':10*math.log10(255**2/mse) if mse else None,
                         'meanSigned8bit':float(bias[c]/count),'maxAbsolute8bit':int(nonzero[-1]),
                         'p95Absolute8bit':int(np.searchsorted(cumulative,count*.95)),
                         'p99Absolute8bit':int(np.searchsorted(cumulative,count*.99)),
                         'identicalFraction':float(hist[c,0]/count)})
    row={'image':image['image'],'width':width,'height':height,'sourceBytes':image['bytes'],
         'exactRGBAFraction':exact/count,'channels':channels,'decoder':'Three.js0.186.1 bundled Basis wasm RGBA32'}
    if angle_count:
        cumulative=np.cumsum(angle_hist)
        row['normalAngularDegrees']={'authoredPixels':angle_count,'mean':angle_sum/angle_count,
            'p95':int(np.searchsorted(cumulative,angle_count*.95))/100,
            'p99':int(np.searchsorted(cumulative,angle_count*.99))/100,
            'max':int(np.nonzero(angle_hist)[0][-1])/100}
    rows.append(row)
    (out/f'{variant}-decoded-difference.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(row),flush=True)
