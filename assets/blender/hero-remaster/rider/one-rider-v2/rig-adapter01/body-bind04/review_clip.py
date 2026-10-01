from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageDraw
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind04');receipts=[]
for yaw in ['000','090']:
 movie=O/f'actual-sit-{yaw}.mp4';decoded=O/f'decoded-{yaw}';decoded.mkdir(exist_ok=True)
 cmd=['ffmpeg','-v','error','-framerate','12','-i',str(O/f'actual-sit-{yaw}-%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-an',str(movie)]
 subprocess.run(cmd,check=True);subprocess.run(['ffmpeg','-v','error','-i',str(movie),str(decoded/'frame-%04d.png')],check=True)
 files=sorted(decoded.glob('frame-*.png'));assert len(files)==24
 board=Image.new('RGB',(6*192,4*260),(28,28,28));draw=ImageDraw.Draw(board)
 for i,p in enumerate(files):
  im=Image.open(p).convert('RGB').resize((192,240));x=i%6*192;y=i//6*260;board.paste(im,(x,y));draw.text((x+5,y+241),str(i+1),fill='white')
 board.save(O/f'decoded-{yaw}-all24.png');receipts.append({'movie':str(movie),'frames':24,'FPS':12,'seconds':2,'movieSHA256':hashlib.sha256(movie.read_bytes()).hexdigest(),'board':str(O/f'decoded-{yaw}-all24.png'),'scope':'Actual decoded animation frames, no retouch or AI'} )
(O/'clip-review-manifest.json').write_text(json.dumps(receipts,indent=2)+'\n')
