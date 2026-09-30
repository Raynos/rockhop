from pathlib import Path
import json, hashlib, shutil
from PIL import Image, ImageDraw, ImageFont
root=Path('harness/out/hero-remaster/rider-selection')
out=Path('docs/evidence/hero-remaster/rider-selection')
out.mkdir(parents=True,exist_ok=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
def f(size): return ImageFont.truetype(font,size)
items=json.loads((root/'inventory.json').read_text())
titles={'A':'Original, current and fresh Blender bodies','B':'Other original outfit models — unchanged this session','C':'Fitted neural rider revisions','D':'Head and forearm experiments — never promoted','E':'Raw generated sources and discarded head topology'}
audits=[]
def tile(board,n,item,raw=None):
 x=20+(n%2)*1020;y=120+(n//2)*950
 draw=ImageDraw.Draw(board);draw.rounded_rectangle((x,y,x+1000,y+930),radius=12,fill='#15232b')
 draw.text((x+24,y+18),item['id']+'  '+item['label'],font=f(30),fill='#ffffff')
 draw.text((x+24,y+58),item.get('note','Actual Garage • full-detail rider • same bike, camera and light'),font=f(21),fill='#b6c8d0')
 if raw:
  im=Image.open(raw).convert('RGB');im=im.resize((810,810),Image.Resampling.LANCZOS);board.paste(im,(x+95,y+101))
  audits.append(dict(id=item['id'],label=item['label'],source=str(raw),sourceSha256=hashlib.sha256(Path(raw).read_bytes()).hexdigest(),kind='existing Blender diagnostic, unrigged source'))
  return
 source=root/item['id']/'frames/0002.png';front=root/item['id']/'frames/0007.png'
 im=Image.open(source).convert('RGB').crop((350,60,1010,660)).resize((900,818),Image.Resampling.LANCZOS);board.paste(im,(x+25,y+96))
 inset=Image.open(front).convert('RGB').crop((590,60,765,245)).resize((220,233),Image.Resampling.LANCZOS)
 board.paste(inset,(x+755,y+117));draw.rectangle((x+753,y+115,x+977,y+352),outline='#b6c8d0',width=2);draw.text((x+759,y+359),'Front face crop',font=f(20),fill='#ffffff')
 report=json.loads((root/item['id']/'report.json').read_text());assert not report.get('failure') and report['errors']==[]
 model=next(m for m in report['manifest']['models'] if m['logical']=='models/rider-'+item['slot']+'.glb')
 assert any(r['sha256']==model['sha256'] for r in report['loaded'])
 shutil.copy2(source,out/(item['id']+'-engine.png'))
 shutil.copy2(root/item['id']/'orbit.mp4',out/(item['id']+'-orbit.mp4'))
 audits.append(dict(**item,sha256=model['sha256'],sourceFrame=2,sourceFrontFrame=7,view=report['view'],lighting=report['lighting'],aa=report['aa'],errors=report['errors'],fullTier=report['initial']['info']['heroDoc'],captureReport=str(root/item['id']/'report.json')))
for letter in 'ABCDE':
 board=Image.new('RGB',(2060,2040),'#09141b');draw=ImageDraw.Draw(board)
 draw.text((30,25),'ROCKHOP RIDER SELECTION  /  '+letter,font=f(35),fill='#ffffff')
 draw.text((30,71),titles[letter],font=f(25),fill='#b6c8d0')
 if letter!='E':
  for n,item in enumerate(i for i in items if i['board']==letter):tile(board,n,item)
 else:
  p=Path('docs/evidence/hero-remaster/rider-generation')
  for n,(identifier,label,directory) in enumerate([('E1','Raw Hunyuan — textured','hunyuan-raw-frames'),('E2','Raw Hunyuan — shape only','hunyuan-shape-frames'),('E3','Raw TRELLIS.2 — textured','trellis-raw-frames')]):
   tile(board,n,dict(id=identifier,label=label,note='Blender source preview • unrigged • different studio lighting'),p/directory/'0000.png')
  tile(board,3,dict(id='E4',label='V7b discarded fragmented neck',slot='street-mustard',note='Actual Garage • failed neck topology • never promoted'))
 draw.text((30,2020),'Native animation poses can differ. IDs identify choices; boards do not approve any candidate.',font=f(17),fill='#b6c8d0')
 board.save(out/('board-'+letter+'.png'))
(out/'capture-audit.json').write_text(json.dumps(audits,indent=2)+'\n')
print('Created five 2x2 boards; exact engine hashes verified.')
