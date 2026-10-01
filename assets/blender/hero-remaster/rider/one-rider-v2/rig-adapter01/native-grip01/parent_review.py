from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-grip01');D=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/native-grip01/parent-decoded');records=[]
for view in ['front','palm','profile']:
 d=D/view;d.mkdir(parents=True,exist_ok=True);subprocess.run(['ffmpeg','-v','error','-i',str(O/f'actual-{view}-open-wrap-open.mp4'),str(d/'%03d.png')],check=True)
 files=sorted(d.glob('*.png'));assert len(files)==33;board=Image.new('RGB',(6*170,6*185),(30,30,30));draw=ImageDraw.Draw(board)
 for i,p in enumerate(files):
  board.paste(Image.open(p).convert('RGB').resize((170,170)),(i%6*170,i//6*185));draw.text((i%6*170+4,i//6*185+171),str(i),fill='white')
 board.save(O/f'parent-decoded-{view}-all33.png');records.append({'view':view,'decodedFrames':33,'board':str(O/f'parent-decoded-{view}-all33.png')})
(O/'parent-decoding.json').write_text(json.dumps(records,indent=2)+'\n')
