"""Ordered actual-movie pairs at authored key windows; no pose/image repaint."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
out=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/played');private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind34/played/decoded-evidence');dest=out/'matched-boards';dest.mkdir(exist_ok=True);rows=[]
for angle in ['side','rear-three-quarter']:
 for surface in ['textured','gray']:
  samples=json.loads((out/'candidate'/angle/surface/'report.json').read_text())['samples'];assert all(r['sleeveCorrective'] is None for r in samples)
  for key in [114,186,304,426]:
   ids=list(range(max(0,key-5),min(480,key+7)));board=Image.new('RGB',(1920,1800),(24,24,24));draw=ImageDraw.Draw(board)
   for k,i in enumerate(ids):
    for col,label in enumerate(['baseline','candidate']):
     root=private if label=='candidate' else private.parent.parent.parent/'body-bind25/morph01/played/decoded-evidence';im=Image.open(root/label/angle/surface/'decoded'/f'{i+1:04d}.png').convert('RGB');im.thumbnail((480,270));x=(k%2*2+col)*480;y=k//2*300;board.paste(im,(x,y));draw.text((x+8,y+275),f'{label} sample{i}',fill='white')
   filename=f'{angle}-{surface}-key{key:03d}.jpg';board.save(dest/filename,quality=94);rows.append({'angle':angle,'surface':surface,'key':key,'samples':ids,'file':filename})
(dest/'index.json').write_text(json.dumps({'rows':rows,'limits':'Only explicit ordered windows shown; all480 source/decoded movie frames retained privately. No full-body/face or whole motion acceptance from these strips.'},indent=2)+'\n')
