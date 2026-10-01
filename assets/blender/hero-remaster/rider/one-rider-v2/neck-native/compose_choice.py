"""Pixel-only paired actual geometry evidence, no asset/render edits."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/neck-native')
if (O/'choice-board.jpg').exists():raise RuntimeError('Frozen choice board exists')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
board=Image.new('RGB',(1320,1550),(25,27,30));draw=ImageDraw.Draw(board);draw.text((12,12),'ACTUAL NECK EVIDENCE — TWO FAILED TRIALS, TECHNIQUE STOPPED',(240,225,180),font=font)
inputs={};labels=[('baseline','SOURCE OPEN COLLAR — head removed, comparison only'),('trial01','TRIAL01 REJECTED — jagged remnants + material reset'),('trial02','TRIAL02 FAILED OPEN PREFIX — branched boundary, NO head join')]
for row,(folder,title) in enumerate(labels):
 y=50+row*485;draw.text((12,y),title,(235,235,235),font=font)
 for col,view in enumerate(['front','profile','rear']):
  p=O/folder/f'gray-{view}.png';inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();x=10+col*440;board.paste(Image.open(p).convert('RGB').resize((430,430),Image.Resampling.LANCZOS),(x,y+30));draw.text((x+5,y+463),view.upper(),(230,230,230),font=small)
draw.text((12,1512),'Next alternative requires human choice: authored local collar panel45min + native brows15min.',(240,225,180),font=small)
board.save(O/'choice-board.jpg',quality=92)
(O/'choice-board.json').write_text(json.dumps({'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sourceSHA256':inputs,'outputSHA256':hashlib.sha256((O/'choice-board.jpg').read_bytes()).hexdigest(),'operations':'Resize/layout/labels only; no source pixel changes','headAddedToFailedPrefix':False},indent=2)+'\n')
