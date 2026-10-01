"""Validate matched physical recordings, preserve pixels, compose actual A/B clips."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image,ImageDraw
ROOT=Path('/Users/raynos/projects/games/rockhop')
BASE=ROOT/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/physical-v5-control157'
OLD=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/played'
PRIVATE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OLDPIX=PRIVATE/'rig-adapter01/body-bind34/played/decoded-evidence/candidate'
DEST=BASE/'played/matched';DEST.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
header=DEST/'comparison-labels.png'
label=Image.new('RGB',(1920,40),'#171c25');d=ImageDraw.Draw(label)
d.text((16,10),'C19 retained | actual physical driver',fill='white');d.text((976,10),'V5 static | actual physical driver | UNACCEPTED',fill='white');label.save(header)
rows=[]
for angle in ['side','rear-three-quarter']:
 for surface in ['textured','gray']:
  folder=BASE/'played/candidate'/angle/surface
  a=json.loads((OLD/'candidate'/angle/surface/'report.json').read_text())
  b=json.loads((folder/'report.json').read_text())
  assert not b.get('failure') and not b['errors'] and len(b['samples'])==480
  expected=json.loads((BASE/'mapping-report.json').read_text())['candidateSHA256']
  assert b['sourceSHA256']==expected and any(r['sha256']==expected for r in b['loaded'])
  for x,y in zip(a['samples'],b['samples']):
   for key in ['state','hash','phase','orbit','camera','bones','bonesInBikeFrame','restAxes']:
    assert x[key]==y[key],(angle,surface,y['i'],key)
   assert y['debug']['physicalPose'] and y['debug']['bones']==19 and y['sleeveCorrective'] is None
  for key in [114,186,304,426]:
   ids=list(range(key-5,key+7));board=Image.new('RGB',(1920,1800),'#171c25');draw=ImageDraw.Draw(board)
   for k,i in enumerate(ids):
    for col,label in enumerate(['C19','V5-static']):
     p=(OLDPIX/angle/surface/'original'/f'{i:04d}.png') if col==0 else(folder/'frames'/f'{i:04d}.png')
     with Image.open(p) as im:
      x,y=(k%2*2+col)*480,(k//2)*300;board.paste(im.convert('RGB').resize((480,270)),(x,y))
     draw.text((x+8,y+275),f'{label} actual frame{i}',fill='white')
   board.save(DEST/f'{angle}-{surface}-{key:03d}.jpg',quality=94)
  # Preserve every original pixel privately; tracked receipts pin source films.
  archive=PRIVATE/'garment-rebuild01/physical-v5-control157/played/original'/angle/surface
  archive.mkdir(parents=True,exist_ok=True)
  receipts=[]
  for p in sorted((folder/'frames').glob('*.png')):
   q=archive/p.name
   if q.exists():assert sha(q)==sha(p)
   else:shutil.copyfile(p,q)
   receipts.append({'frame':p.name,'sha256':sha(p)})
  assert len(receipts)==480
  (folder/'frames-archive.json').write_text(json.dumps({'privateOriginalFrames':str(archive),'frames':receipts,'sourceMovieSHA256':sha(folder/'played.mp4')},indent=2)+'\n')
  destination=DEST/f'{angle}-{surface}-before-after.mp4'
  assert not destination.exists(),'Preserve frozen movie comparison'
  # Both source clips have exact same480 state/camera samples. CPU composition only.
  filter='[0:v]scale=960:540[a];[1:v]scale=960:540[b];[a][b]hstack=inputs=2[body];[2:v][body]vstack=inputs=2:shortest=1'
  subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(OLD/'candidate'/angle/surface/'played.mp4'),'-threads','2','-i',str(folder/'played.mp4'),'-framerate','12','-loop','1','-i',str(header),'-filter_complex_threads','2','-filter_complex',filter,'-threads','2','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(destination)],check=True)
  rows.append({'angle':angle,'surface':surface,'frames':480,'stateCameraAll19BoneWorldAndBikeFrameExact':True,'actualSourceSHA256':expected,'beforeAfterMovie':str(destination),'movieSHA256':sha(destination),'sourceOriginalFrames':str(archive)})
  # Remove only owned duplicates after hash-verifying every private source pixel.
  for p in (folder/'frames').glob('*.png'):p.unlink()
  (folder/'frames').rmdir()
for angle in ['side','rear-three-quarter']:
 a=json.loads((BASE/'played/candidate'/angle/'textured/report.json').read_text())
 b=json.loads((BASE/'played/candidate'/angle/'gray/report.json').read_text())
 for x,y in zip(a['samples'],b['samples']):
  for key in ['state','hash','debug','bones','bonesInBikeFrame','restAxes','orbit','camera','anchor']:assert x[key]==y[key]
(BASE/'played/matched-validation.json').write_text(json.dumps({'rows':rows,'pairedGrayPBRStates':960,'limits':'Actual physical motion, no authored compression. This verifies matched rendering inputs; parent appearance, geometric collision and visible contact gates remain independent.'},indent=2)+'\n')
print(json.dumps({'recordings':4,'matchedFrames':1920,'pairs':len(rows),'source':expected}))
