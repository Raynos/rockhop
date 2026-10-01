"""Compose actual unchanged source PNGs; no retouching or asset acceptance."""
from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/gray-diagnostic03')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
def board(name,columns,rows,cells,note):
 out=O/name
 if out.exists():raise RuntimeError('Frozen board exists')
 w=440;h=472;image=Image.new('RGB',(columns*w,rows*h+60),'#202328');draw=ImageDraw.Draw(image);sources=[]
 for i,(label,p) in enumerate(cells):
  source=Image.open(p).convert('RGB');source.thumbnail((w,h-32));x=(i%columns)*w;y=(i//columns)*h;image.paste(source,(x+(w-source.width)//2,y+32));draw.text((x+10,y+9),label,fill='white');sources.append({'path':str(p),'SHA256':sha(p)})
 draw.text((12,rows*h+12),note,fill='white');image.save(out);records.append({'path':str(out),'SHA256':sha(out),'sourcePNGs':sources})
variants=['raw-gray','reduced-gray','painted-gray','painted-PBR'];views=['front','profile','three-quarter','rear']
board('actual-four-variants-four-views.jpg',4,4,[(v+' | '+view,O/f'{v}-face-{view}.png') for v in variants for view in views],'Raw: 985183 retained / 985175 imported (8 zero-area exclusions). Same camera; explicit display frames. Unaccepted.')
board('actual-front-comparison.jpg',4,1,[(v,O/f'{v}-face-front.png') for v in variants],'Cheek defects already visible in pre-cleanup/pre-reduction raw gray. No geometry or paint edits. Parent alone judges.')
nine=['front','front-left','left','rear-left','rear','rear-right','right','front-right','top-front']
for v in variants:board(v+'-nine-angle-board.jpg',3,3,[(v+' | '+view,O/f'{v}-nine-{view}.png') for view in nine],'Actual unchanged NEW Hunyuan 2.1 bust. Static source audit; no rig, neck join, contact or in-game acceptance.')
(O/'board-manifest.json').open('x').write(json.dumps({'status':'UNACCEPTED actual render contact sheets','recipeSHA256':sha(Path(__file__)),'boards':records,'limits':['Original render PNGs unchanged; only scaled into labelled sheets.','Shared camera/display framing not an exact per-vertex painted/reduced mapping.']},indent=2)+'\n')
