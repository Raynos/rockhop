"""Read-only saved photo/played-pixel controls. Manual masks are explicit, not segmentation truth."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
REPO=Path('/Users/raynos/projects/games/rockhop');OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind27'
paths={'approved_bust':REPO/'assets/design/hero-remaster/one-rider-v2/head/buzz-bust-reference.png','actual22':REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind22/played01/actual-front-textured.png','actual24':REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind24/played01/actual-front-textured.png'}
# Pixel coordinates selected visibly from retained full-resolution controls.
# Annuli avoid the upper lid and pupil; mild eyebrow/skin contamination remains possible.
regions={'approved_bust':[(476,413,9,17),(696,415,9,17)],'actual22':[(1149,685,8,14),(1380,692,8,14)],'actual24':[(1149,685,8,14),(1380,692,8,14)]}
rows={};panels=[]
for name,path in paths.items():
 raw=path.read_bytes();image=Image.open(path).convert('RGB');rgb=np.array(image).astype(float)/255;Y,X=np.indices(rgb.shape[:2]);stats=[]
 for cx,cy,r0,r1 in regions[name]:
  rr=(X-cx)**2+(Y-cy)**2;mask=(rr>=r0*r0)&(rr<=r1*r1)&(Y>=cy-3)&(Y<=cy+7)
  values=rgb[mask];lum=np.sum(values*[.2126,.7152,.0722],axis=1)
  stats.append({'manualAnnulus':[cx,cy,r0,r1],'verticalLimits':[cy-3,cy+7],'sampledPixels':len(values),'medianRGB':np.median(values,axis=0).tolist(),'encodedSRGBLumaPercentiles':np.percentile(lum,[0,10,50,90,100]).tolist(),'notLightingMatched':True})
 # No source is edited; these are labelled diagnostic copies with explicit manual sample rings.
 annotated=image.copy();draw=ImageDraw.Draw(annotated)
 for cx,cy,r0,r1 in regions[name]:
  for radius in [r0,r1]:draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),outline=(0,255,255),width=1)
 rect=(370,365,780,462) if name=='approved_bust' else (1060,625,1450,735)
 crop=annotated.crop(rect).resize((1230,330),Image.Resampling.NEAREST);panel=Image.new('RGB',(1230,370),'#202020');panel.paste(crop,(0,40));ImageDraw.Draw(panel).text((12,12),name+' retained source pixels; cyan manual annuli; lights/pose not matched',fill='white');panels.append(panel)
 rows[name]={'path':str(path),'SHA256':hashlib.sha256(raw).hexdigest(),'dimensions':list(image.size),'manualIrisPixelControls':stats,'cropRect':list(rect)}
board=Image.new('RGB',(1230,len(panels)*370),'#202020')
for i,panel in enumerate(panels):board.paste(panel,(0,i*370))
board.save(OUT/'saved-reference-actual-eye-controls.png')
report={'status':'READONLY retained full-resolution pixel controls; no relighting or candidate','sources':rows,'limits':['Reference and gameplay have different head pose, light, tone mapping and sample scale. These are observed pixels, not equivalent material reflectance.','Manual annuli are reviewer-visible and may include lid/skin pixels; use source texture + UV audit for the causal albedo claim.','No anatomical iris diameter inferred from photographs.','Actual24 cloudiness is the parent-rejected shader trial, not a new candidate.']}
(OUT/'saved-pixel-controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
