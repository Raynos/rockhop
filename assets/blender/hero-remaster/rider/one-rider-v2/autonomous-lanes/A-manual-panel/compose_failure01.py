"""Pixel-only board of actual failed seam views; no visual asset alterations."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib,sys,PIL
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-manual-panel/trial01')
if (O/'failure-board.jpg').exists():raise RuntimeError('Frozen board exists')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
board=Image.new('RGB',(1300,1400),(24,26,29));draw=ImageDraw.Draw(board)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
draw.text((15,12),'A: EXPLICIT SEAM PANEL — FAILED BEFORE REMOVAL OR HEAD JOIN',(245,225,185),font=font)
inputs={}
for i,label in enumerate(['front','profile','rear','three-quarter']):
 p=O/f'failed-seam-{label}.png';inputs[str(p)]=sha(p);x=10+(i%2)*650;y=55+(i//2)*660
 board.paste(Image.open(p).convert('RGB'),(x,y));draw.text((x+8,y+642),label.upper(),(235,235,235),font=small)
draw.text((15,1372),'Red = exact 88-edge seam; flood reaches ALL 42,505 retained faces. No accepted rider.',(245,225,185),font=small)
board.save(O/'failure-board.jpg',quality=92)
(O/'failure-board.json').write_text(json.dumps({'status':'Unaccepted failed prefix, no new head',
 'operations':'Layout and labels only; source PNG pixels unchanged before JPEG encoding',
 'sourceSHA256':inputs,'outputSHA256':sha(O/'failure-board.jpg'),'recipeSHA256':sha(Path(__file__)),
 'sharedPixelOnlyInterpreter':sys.executable,'sharedInterpreterSHA256':sha(Path(sys.executable)),
 'PillowVersion':PIL.__version__,'PillowPath':PIL.__file__,'PillowInitSHA256':sha(Path(PIL.__file__)),
 'geometryDependency':False},indent=2)+'\n')
