"""Plot actual authored topology gates; no art edit or fitted face claim."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--gate1',required=True);ap.add_argument('--gate2',required=True)
ap.add_argument('--output',required=True);a=ap.parse_args()
im=Image.new('RGB',(1400,1000),'#25282a');d=ImageDraw.Draw(im)
for k,path in enumerate([a.gate1,a.gate2]):
    p=np.load(path);v=p['vertices'];f=p['faces'];region=p['guide_region']
    e,c=np.unique(np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1),axis=0,return_counts=True)
    def pixel(index):return (k*700+350+float(v[index,0])*1750,600-float(v[index,1])*1750)
    for edge in e:
        if np.all(region[edge]==1):d.line([pixel(edge[0]),pixel(edge[1])],fill='#62676b',width=1)
    for edge in e[(c==1)|(c>2)]:
        if np.all(region[edge]==1):d.line([pixel(edge[0]),pixel(edge[1])],fill='#ff6155' if c[np.all(e==edge,axis=1)][0]==1 else '#55b7ff',width=3)
    d.text((k*700+20,20),f'Actual authored gate {k+1}: failed / no source fit',fill='white')
    d.text((k*700+20,44),'Red: unexpected boundaries. Blue: nonmanifold edges.',fill='white')
Path(a.output).parent.mkdir(parents=True,exist_ok=True);im.save(a.output)
