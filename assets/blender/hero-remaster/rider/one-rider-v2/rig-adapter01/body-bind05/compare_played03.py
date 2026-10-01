"""Arrange actual replay frames; retain original camera following measured wrists."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
base=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind05/decoded-evidence')
out=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05/played03')
for start in range(0,40,8):
 canvas=Image.new('RGB',(1280,4*385),(24,24,24));draw=ImageDraw.Draw(canvas)
 for k,second in enumerate(range(start,min(40,start+8))):
  index=second*12;im=Image.open(base/'played03/hands/frames'/('%04d.png'%index)).convert('RGB');im=im.resize((640,360));x=k%2*640;y=k//2*385;canvas.paste(im,(x,y));draw.text((x+8,y+363),'Actual replay %.3fs, frame%d'%((index+1)/12,index),fill='white')
 canvas.save(out/('motion-second-page%d.jpg'%(start//8)),quality=94)
indices=[49,146,189,195,408]
for page,start in enumerate(range(0,len(indices),2)):
 canvas=Image.new('RGB',(1920,2*565),(24,24,24));draw=ImageDraw.Draw(canvas)
 for row,index in enumerate(indices[start:start+2]):
  for column,run in enumerate(['played02','played03']):
   im=Image.open(base/run/'hands/frames'/('%04d.png'%index)).convert('RGB');im=im.resize((960,540));x=column*960;y=row*565;canvas.paste(im,(x,y));draw.text((x+8,y+542),('Before: hovering' if column==0 else 'After: orthogonal pole')+'; actual tick%d'%((index+1)*10),fill='white')
 canvas.save(out/('before-after-page%d.jpg'%page),quality=95)
(out/'board-recipe.json').write_text(json.dumps({'motionPages':'All40seconds sampled at1second intervals, actual captured PNGs; not every480frame visually judged','comparisonFrames':indices,'camera':'Same orbit recipe; focus follows measured wrists and therefore shifts slightly when the old contact fails. No fixed-camera pixel comparison claimed.','noImageRepaint':True},indent=2)+'\n')
