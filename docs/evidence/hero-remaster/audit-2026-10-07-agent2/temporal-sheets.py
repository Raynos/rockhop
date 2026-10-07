from pathlib import Path
import json
from PIL import Image,ImageDraw
out=Path('harness/out/rider-finish/agent2-audit-sheets01');out.mkdir(exist_ok=True)
results=[]
p=Path('harness/out/rider-finish/agent2-audit-media01/playback.json')
if p.exists():results.extend(json.load(p.open())['results'])
for p in sorted(Path('harness/out/rider-finish/agent2-audit-media-serial02').glob('*/playback.json')):
 results.extend(json.load(p.open())['results'])
for r in results:
 frames=[f for f in r['frames'] if f.get('path')];selected=sorted(set(round(i*(len(frames)-1)/15) for i in range(16)))
 im=Image.new('RGB',(1024,4*284),(20,22,25));draw=ImageDraw.Draw(im)
 for k,idx in enumerate(selected):
  fr=frames[idx];pic=Image.open(fr['path']).convert('RGB');pic.thumbnail((256,256));x=(k%4)*256;y=(k//4)*284
  im.paste(pic,(x+(256-pic.width)//2,y));draw.text((x+4,y+258),f"t={fr['mediaTime']:.3f} presented={fr['presentedFrames']}",fill='white')
 name=Path(r['source']['path']).parent.name+'-'+Path(r['source']['path']).stem+'.jpg';im.save(out/name,quality=90)
 print(name)
