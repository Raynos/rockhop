from pathlib import Path
import json,subprocess,shutil,hashlib
from PIL import Image,ImageDraw
E=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05');O=E/'played04';P=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind05/decoded-evidence')
reports=[json.loads((O/m/'report.json').read_text()) for m in ['textured','gray']]
a,b=reports
assert len(a['samples'])==len(b['samples'])==480
assert [(s['tick'],s['state'],s['debug']) for s in a['samples']]==[(s['tick'],s['state'],s['debug']) for s in b['samples']]
for start in range(0,40,8):
 im=Image.new('RGB',(1280,8*385),(24,24,24));draw=ImageDraw.Draw(im)
 for row,second in enumerate(range(start,min(start+8,40))):
  for col,m in enumerate(['textured','gray']):
   index=second*12;frame=Image.open(O/m/'frames'/('%04d.png'%index)).convert('RGB').resize((640,360));x=col*640;y=row*385;im.paste(frame,(x,y));draw.text((x+8,y+363),'%s actual replay frame%d'%(m,index),fill='white')
 im.save(O/('matched-motion-page%d.jpg'%(start//8)),quality=94)
im=Image.new('RGB',(1920,4*565),(24,24,24));d=ImageDraw.Draw(im)
for row,i in enumerate([49,120,420,468]):
 for col,m in enumerate(['textured','gray']):
  frame=Image.open(O/m/'frames'/('%04d.png'%i)).convert('RGB').resize((960,540));x=col*960;y=row*565;im.paste(frame,(x,y));d.text((x+8,y+542),'%s same actual tick%d'%(m,(i+1)*10),fill='white')
im.save(O/'matched-defect-frames.jpg',quality=95)
for m in ['textured','gray']:
 p=O/m/'played.mp4';dest=P/'played04'/m/'played-original.mp4';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);h=hashlib.sha256(p.read_bytes()).hexdigest();temp=p.with_name('played-720.mp4');subprocess.run(['ffmpeg','-v','error','-y','-i',str(p),'-vf','scale=1280:720','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',str(temp)],check=True);temp.replace(p);(p.parent/'movie-archive.json').write_text(json.dumps({'privateOriginal':str(dest),'originalSHA256':h,'reviewSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'reviewTransform':'ffmpeg scale1280:720 libx264CRF20; no pose or repaint'},indent=2)+'\n')
(O/'paired-replay-parity.json').write_text(json.dumps({'samples':480,'physicsStateDebugAndTicksExact':True,'cameraAndLighting':'Same capture recipe, surface override only','parentCoverage':'40seconds at1second intervals, plus four full-resolution defect samples. No claim every480frame judged.'},indent=2)+'\n')
