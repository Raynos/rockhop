"""Decode every sampled actual clip frame, retaining immutable review boards."""
from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw
R=Path('/Users/raynos/projects/games/rockhop');O=R/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/unimate-new01';rows=[]
for kind in ['gt','raw']:
 for yaw in ['000','090']:
  movie=O/f'actual-{kind}-{yaw}.mp4';decoded=O/f'decoded-{kind}-{yaw}';decoded.mkdir();subprocess.run(['ffmpeg','-v','error','-framerate','15','-i',str(O/f'actual-{kind}-{yaw}-%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-an',str(movie)],check=True);subprocess.run(['ffmpeg','-v','error','-i',str(movie),str(decoded/'frame-%04d.png')],check=True);files=sorted(decoded.glob('frame-*.png'));assert len(files)==29
  board=Image.new('RGB',(6*160,5*218),(28,28,28));draw=ImageDraw.Draw(board)
  for i,p in enumerate(files):
   im=Image.open(p).convert('RGB').resize((160,200));x=i%6*160;y=i//6*218;board.paste(im,(x,y));draw.text((x+4,y+201),str(i*2)+' / '+format(i*2/30,'.2f')+'s',fill='white')
  board.save(O/f'decoded-{kind}-{yaw}-all29.png');rows.append({'kind':kind,'yaw':yaw,'movie':str(movie),'movieSHA256':hashlib.sha256(movie.read_bytes()).hexdigest(),'frames':29,'FPS':15,'sampleTimes':'Original exported frames0,2,...56 /30fps; fixedcamera, no retouch','decodedBoard':str(O/f'decoded-{kind}-{yaw}-all29.png')})
ref=Image.open(R/'assets/design/hero-remaster/one-rider-v2/sitting-target01/target.png').convert('RGB');w,h=ref.size;boards=[];chosen=[1,4,8,11,15,18,22,26,29]
for kind in ['gt','raw']:
 board=Image.new('RGB',(w,h),(76,76,76))
 for i,f in enumerate(chosen):
  im=Image.open(O/f'decoded-{kind}-090/frame-{f:04d}.png').convert('RGB');cw=w//3;ch=h//3;k=min(cw/im.width,ch/im.height);im=im.resize((round(im.width*k),round(im.height*k)));board.paste(im,(i%3*cw+(cw-im.width)//2,i//3*ch+(ch-im.height)//2))
 board.save(O/(kind+'-nine-frames.png'));boards.append(board)
combined=Image.new('RGB',(3*w,h));combined.paste(ref,(0,0));combined.paste(boards[0],(w,0));combined.paste(boards[1],(2*w,0));combined.save(O/'target-left-blender-middle-unimate-right.png');(O/'review-manifest.json').write_text(json.dumps({'clips':rows,'nineFrameSamples':chosen,'comparison':'Reference left, actualBlenderGTdecode middle, actualneuraldecode right','limits':'Canonical review-frame only; not restored gamecontact or physicaldevice evidence'},indent=2)+'\n')
