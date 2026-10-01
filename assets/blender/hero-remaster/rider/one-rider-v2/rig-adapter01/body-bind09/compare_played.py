"""Matched actual screenshots, common crops only; no repaint or injected pose."""
from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw
repo=Path('/Users/raynos/projects/games/rockhop');base=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01');out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind09/played01'
a=json.loads((repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05/played04/textured/report.json').read_text())['samples'];b=json.loads((out/'textured/report.json').read_text())['samples'];assert len(a)==len(b)==480
assert [(s['tick'],s['state']) for s in a]==[(s['tick'],s['state']) for s in b]
board=Image.new('RGB',(1600,2*790),(24,24,24));d=ImageDraw.Draw(board)
for row,(index,box) in enumerate([(49,(1300,250,2090,1350)),(420,(1630,230,2490,1060))]):
 for col,(stage,run) in enumerate([('body-bind05','played04'),('body-bind09','played01')]):
  image=Image.open(base/stage/'decoded-evidence'/run/'textured/frames'/('%04d.png'%index)).convert('RGB').crop(box);image.thumbnail((800,750));x=col*800+(800-image.width)//2;y=row*790;board.paste(image,(x,y));d.text((col*800+12,y+758),('Before' if col==0 else 'Baked seam correction')+' - actual tick%d'%((index+1)*10),fill='white')
board.save(out/'actual-before-after.jpg',quality=95)
shutil.copy2(base/'body-bind09/decoded-evidence/played01/textured/frames/0049.png',out/'actual-white-rider.png')
(out/'before-after-recipe.json').write_text(json.dumps({'before':'body05played04','after':'body09played01','actualPhysicsStatesAndTicksExact':480,'crops':{'49':[1300,250,2090,1350],'420':[1630,230,2490,1060]},'transform':'Same crop box per pair; uniform aspect-preserving thumbnail. No pixel repaint, pose change or bike edit.'},indent=2)+'\n')
