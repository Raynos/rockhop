#!/usr/bin/env python3
"""Compare source decoded texels with pinned runtime RGBA transcode in bounded row chunks."""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

out=Path('harness/out/rider-rebuild/download-opt01/textures01')
variant=sys.argv[1] if len(sys.argv)>1 else 'uastc'
selected=set(map(int,sys.argv[2].split(','))) if len(sys.argv)>2 else None
rows=[]
for image in json.loads((out/'inventory.json').read_text())['images']:
    if selected is not None and image['image'] not in selected:
        continue
    src=Image.open(image['path']).convert('RGBA')
    width,height=src.size
    dst=np.memmap(out/f'{variant}-decoded-rgba'/f"image-{image['image']:02d}.rgba",dtype=np.uint8,mode='r',shape=(height,width,4))
    hist=np.zeros((4,256),dtype=np.int64)
    squared=np.zeros(4)
    bias=np.zeros(4)
    authored_hist=np.zeros((3,256),dtype=np.int64)
    authored_squared=np.zeros(3)
    authored_count=0
    alpha_changed=opaque_changed=transparent_changed=0
    decoded_alpha_min=255
    decoded_alpha_max=0
    angle_hist=np.zeros(18001,dtype=np.int64)
    angle_sum=angle_count=0
    exact=0
    for y in range(0,height,64):
        a=np.asarray(src.crop((0,y,width,min(height,y+64))),dtype=np.int16)
        b=np.asarray(dst[y:y+64],dtype=np.int16)
        d=b-a
        absdiff=np.abs(d)
        authored=a[:,:,3]>0
        authored_count+=int(np.count_nonzero(authored))
        for c in range(3):
            authored_hist[c]+=np.bincount(absdiff[:,:,c][authored].ravel(),minlength=256)
            authored_squared[c]+=np.sum(d[:,:,c][authored].astype(np.float64)**2)
        alpha_changed+=int(np.count_nonzero(d[:,:,3]))
        opaque_changed+=int(np.count_nonzero((a[:,:,3]==255)&(b[:,:,3]!=255)))
        transparent_changed+=int(np.count_nonzero((a[:,:,3]==0)&(b[:,:,3]!=0)))
        decoded_alpha_min=min(decoded_alpha_min,int(b[:,:,3].min()))
        decoded_alpha_max=max(decoded_alpha_max,int(b[:,:,3].max()))
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
         'exactRGBAFraction':exact/count,'channels':channels,'decoder':('Basisu native ASTC linear software profile; all GPU blocks byte-identical to pinned Three wasm' if variant.endswith('-astc') else 'Three.js0.186.1 bundled Basis wasm RGBA32')}
    row['authoredRGB']={'mask':'source alpha > 0; no candidate-alpha masking', 'pixels':authored_count,
        'channels':[{'channel':name,'rmse8bit':math.sqrt(float(authored_squared[c]/authored_count)),
                     'p99Absolute8bit':int(np.searchsorted(np.cumsum(authored_hist[c]),authored_count*.99)),
                     'maxAbsolute8bit':int(np.nonzero(authored_hist[c])[0][-1])} for c,name in enumerate('RGB')]}
    row['alpha']={'sourceExtrema':image['alphaExtrema'],'decodedExtrema':[decoded_alpha_min,decoded_alpha_max],
                  'changedPixels':alpha_changed,'originalOpaquePixelsChanged':opaque_changed,
                  'originalZeroPixelsChanged':transparent_changed}
    if angle_count:
        cumulative=np.cumsum(angle_hist)
        row['normalAngularDegrees']={'authoredPixels':angle_count,'mean':angle_sum/angle_count,
            'p95':int(np.searchsorted(cumulative,angle_count*.95))/100,
            'p99':int(np.searchsorted(cumulative,angle_count*.99))/100,
            'max':int(np.nonzero(angle_hist)[0][-1])/100}
    rows.append(row)
    (out/f'{variant}-decoded-difference.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(row),flush=True)
