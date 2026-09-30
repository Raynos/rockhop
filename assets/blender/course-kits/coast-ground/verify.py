"""Decode delivered maps, verify immutable bytes/physical data and tiling scale."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent;D=ROOT/'delivery';m=json.loads((D/'manifest.json').read_text());report=[]
for entry in m['files']:
    path=D/entry['file'];data=path.read_bytes();assert len(data)==entry['bytes'];assert hashlib.sha256(data).hexdigest()==entry['sha256']
    image=Image.open(path);image.load();assert image.size==(entry['width'],entry['height']);pixels=np.asarray(image).astype(float)/255
    if entry['channel']=='normal':
        n=pixels*2-1;length=np.sqrt(np.sum(n*n,axis=2));assert np.max(np.abs(length-1))<.015;assert np.min(n[:,:,2])>.7
    if entry['channel']=='arm':
        assert np.max(pixels[:,:,2])==0,'cement/silt cannot be metallic';assert .45<np.min(pixels[:,:,1])<.92;assert np.min(pixels[:,:,0])>.4
    if entry['channel']=='albedo':
        assert np.min(pixels)>.2 and np.max(pixels)<.99
        # Physical broad variation survives compression. Fine grain must be
        # restrained relative to old 9–13k high-contrast canvas speckles.
        local=(pixels-np.roll(pixels,1,axis=1));assert np.sqrt(np.mean(local*local))<.035
    report.append({'file':entry['file'],'decoded':True,'width':image.width,'height':image.height,'min':float(pixels.min()),'max':float(pixels.max())})
result={'status':'CPU image/hash/normal/ARM/contrast validation only; no GPU/played approval','files':report,'totalBytes':sum(f['bytes'] for f in m['files']),'residentMiB':m['residentRgba8MipsBytes']/1048576}
(D/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
