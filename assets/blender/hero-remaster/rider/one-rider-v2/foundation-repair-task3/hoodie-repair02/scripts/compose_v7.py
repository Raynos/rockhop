from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'hoodie-repair02';frames=OUT/'renders/movie-v7';seq=OUT/'renders/encoded-v7';seq.mkdir(exist_ok=True);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
order=['front','side','rear'];ks=[0]*12+list(range(49))+[48]*24
for j,k in enumerate(ks):
 im=Image.new('RGB',(1152,878),'#171c25');d=ImageDraw.Draw(im);d.text((15,10),'Preferred rider | C19 control → local foundation + portable compression | Normal speed',font=font,fill='white')
 for row,variant in enumerate(['control','candidate']):
  y=56+row*395
  for col,view in enumerate(order):im.paste(Image.open(frames/f'{variant}-{k:03d}-{view}.png'),(col*384,y))
  d.text((12,y+8),'C19 CONTROL'if row==0 else'REPAIR v7 — UNACCEPTED',font=small,fill='white'if row==0 else'#c1ffdd')
 d.text((15,849),'Remaining: broad arm-motion failures; hip crossings; 16.4 mm saddle hover. No production edits.',font=small,fill='#ffcc88');im.save(seq/f'{j:04d}.png')
video=OUT/'deliverables/foundation-v7-before-after-normal-speed.mp4';subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','24','-i',str(seq/'%04d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
board=Image.new('RGB',(1152,915),'#171c25');d=ImageDraw.Draw(board);d.text((15,12),'Inspected motion comparison | Same preferred head, textures and contact targets',font=font,fill='white')
for col,k in enumerate([0,24,48]):
 for row,variant in enumerate(['control','candidate']):board.paste(Image.open(frames/f'{variant}-{k:03d}-side.png'),(col*384,72+row*395))
 d.text((col*384+12,48),['BIKE STAND','MID TRANSITION','SEATED'][col],font=small,fill='white')
d.text((12,81),'C19 CONTROL',font=small,fill='white');d.text((12,476),'REPAIR v7 — UNACCEPTED',font=small,fill='#c1ffdd');d.text((15,873),'Cleaner sleeve/chest profile; broader arm-motion + hip/support failures still block acceptance.',font=small,fill='#ffcc88');board.save(OUT/'deliverables/foundation-v7-inspected-before-after.png')
(OUT/'v7-film-provenance.json').write_text(json.dumps({'fps':24,'frames':len(ks),'motionSeconds':2,'startHoldSeconds':.5,'endHoldSeconds':1,'views':order,'normalMethod':'CPU emulation of ordinary glTF morph-before-LBS skin normals; original imported hard head corner normals rotated rigidly','source':'C19 control, exact body11 geometry and textures','candidate':'v7 from original source; local shape/W/posture/compression','renderer':'installed Blender Cycles CPU,2threads,3samples,matched lighting/materials/cameras,exact exported topology','visualLimits':'Blender BSDF/display differs fromThree; no actual GPU PBR appearance/performance certificate','videoSHA256':hashlib.sha256(video.read_bytes()).hexdigest()},indent=2));print(video)
