"""Pixel-only layout of the four actual CPU gray views; no artwork edits."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/neck-native/trial01')
if (O/'gray-board.jpg').exists():raise RuntimeError('Frozen board already exists')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
board=Image.new('RGB',(1040,1150),(28,30,32));draw=ImageDraw.Draw(board)
draw.text((14,10),'ACTUAL CPU TRIAL01 — UNACCEPTED',(235,235,235),font=font)
draw.text((14,39),'Shared-index neck join; jagged collar and material reset remain.',(215,190,115),font=small)
inputs={}
for i,label in enumerate(['front','profile','rear','three-quarter']):
 p=O/f'gray-{label}.png';inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();x=10+(i%2)*520;y=75+(i//2)*530
 board.paste(Image.open(p).convert('RGB').resize((510,510),Image.Resampling.LANCZOS),(x,y));draw.text((x+5,y+512),label.upper(),(235,235,235),font=small)
draw.text((14,1133),'Neutral static geometry only. No texture, neck-motion, rig or contact acceptance.',(215,190,115),font=small)
board.save(O/'gray-board.jpg',quality=92)
(O/'board.json').write_text(json.dumps({'sourceImagesSHA256':inputs,'outputSHA256':hashlib.sha256((O/'gray-board.jpg').read_bytes()).hexdigest(),'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'operations':'Resize/layout/labels only; source rendered pixels unretouched'},indent=2)+'\n')
