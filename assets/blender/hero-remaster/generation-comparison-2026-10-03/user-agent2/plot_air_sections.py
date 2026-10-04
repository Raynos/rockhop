"""Planar section diagnostic, never a shaded/posed art review."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--sections',required=True);p.add_argument('--out',required=True);args=p.parse_args()
data=json.loads(Path(args.sections).read_text());columns=4;size=350
im=Image.new('RGB',(columns*size,((len(data)+columns-1)//columns)*size),(250,250,250));draw=ImageDraw.Draw(im)
colors=[(32,92,169),(211,84,37),(39,134,80),(145,60,160)]
for index,s in enumerate(data):
 ox=(index%columns)*size;oy=(index//columns)*size;axes=[k for k in range(3) if k!=s['axis']]
 closed=[l for l in s['loops'] if l['closed'] and l['area']>1e-10]
 points=np.concatenate([np.asarray(l['points'])[:,axes] for l in closed]) if closed else np.array([[0,0],[1,1]])
 low=points.min(axis=0);high=points.max(axis=0);center=(low+high)/2;scale=(size-75)/max(float((high-low).max()),.01)
 def convert(p):return [(ox+size/2+(a-center[0])*scale,oy+size/2+20-(b-center[1])*scale) for a,b in p]
 draw.text((ox+10,oy+10),s.get('name',str(s['value'])),fill=(0,0,0));draw.text((ox+10,oy+25),f'{len(closed)} loops; {len(s["loops"])-len(closed)} other; axes {axes}',fill=(0,0,0))
 for n,l in enumerate(sorted(closed,key=lambda x:-x['area'])):
  xy=convert(np.asarray(l['points'])[:,axes]);draw.line(xy+[xy[0]],fill=colors[n%len(colors)],width=2)
 draw.text((ox+10,oy+size-25),f'Bounds {low.round(3)} to {high.round(3)}',fill=(0,0,0))
im.save(args.out)
