"""Lay out unaltered diagnostic renders with explicit scope labels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, hashlib
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/hoodie-repair03/renders/sleeve-tube03')
OUT=Path('deliverables'); font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',26); title=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',32)
boards=[('Standing-comparison21-REJECTED.png','Standing comparison: construction21 REJECTED', [('preferred-body11','Preferred body11','rest-front'),('tube21-dart','New construction21: oversized shoulders','rest-front')],640,640),('Recorded304-comparison21-REJECTED.png','Exact recorded frame304: construction21/driver22 REJECTED',[('v7-control304','Frozen V7 control: existing torso damage','304-exact-side'),('tube21-material304','New material response: crossing shoulder surfaces','304-exact-side')],960,540)]
proof=[]
for filename,heading,cols,w,h in boards:
 canvas=Image.new('RGB',(2*w,160+2*h+100),(245,245,245));d=ImageDraw.Draw(canvas);d.text((24,20),heading,font=title,fill=(100,20,20));d.text((24,68),'Matched cameras and source PBR images. CPU snapshots; no runtime or motion pass.',font=font,fill=(30,30,30))
 sources=[]
 for j,(lane,label,stem) in enumerate(cols):
  d.text((j*w+20,120),label,font=font,fill=(30,30,30))
  for k,mode in enumerate(['pbr','gray']):
   p=R/lane/(stem+'-'+mode+'.png');im=Image.open(p).convert('RGB');im=im.resize((w,h),Image.Resampling.LANCZOS);canvas.paste(im,(j*w,160+k*h));d.text((j*w+18,174+k*h),mode.upper(),font=font,fill=(255,255,255));sources.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 d.text((24,172+2*h),'Rest: zero strict crossings still changes preferred silhouette.' if filename.startswith('Standing') else 'Recorded304: 597 new-cap/tube crossing pairs; 81 new faces below one-quarter rest area.',font=font,fill=(100,20,20))
 d.text((24,210+2*h),'Quality failure retained. No production promotion.',font=font,fill=(30,30,30));out=OUT/filename;canvas.save(out);proof.append({'board':str(out),'sources':sources,'operation':'Only labeled layout and uniform image resampling; no surface or pixel repair.'})
(OUT/'Inspected21-board-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
