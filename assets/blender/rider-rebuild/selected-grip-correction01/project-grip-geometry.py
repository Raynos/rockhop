"""Diagnostic actual selected surface projections. Static geometry, never art acceptance."""
import json, sys, math
from pathlib import Path
from PIL import Image, ImageDraw
root=Path(sys.argv[1])
colours={'thumb':'#e48d21','index':'#e23d4b','middle':'#29b16b','ring':'#418cec','pinky':'#b96bd7','palm':'#8d98a8'}
for side in ['left','right']:
 data=json.loads((root/f'geometry-{side}.json').read_text())
 chain=json.loads((root/'chain-construction.json').read_text()) if (root/'chain-construction.json').exists() else None
 diagnostics=next((s for s in chain['sides'] if s['side']==side),None) if chain else None
 panels=[(0,1,'Cross-bar projection X/Y'),(0,2,'Top projection X/Z'),(2,1,'Rear projection Z/Y')]
 image=Image.new('RGB',(1500,680),'#10151e');draw=ImageDraw.Draw(image)
 draw.text((20,12),f'{side.upper()} / actual selected75 glove surface + exact finite authored bar / rejected candidate diagnostic',fill='#ffffff')
 draw.text((20,32),'Cloud: actual source every64th vertex. Lines: native phalanges. White: current pads. Yellow: rear/below diagnostic target, unqualified reach.',fill='#bcc6d5')
 def digit_for(name):
  for digit in ['thumb','index','middle','ring','pinky']:
   if digit in name:return digit
  return 'palm'
 for pi,(u,v,title) in enumerate(panels):
  origin=pi*500
  points=[p['point'] for p in data['points']]+[p for tri in data['bar'] for p in tri]
  lowu=min(p[u] for p in points);highu=max(p[u] for p in points);lowv=min(p[v] for p in points);highv=max(p[v] for p in points)
  scale=min(455/(highu-lowu),520/(highv-lowv));cx=(lowu+highu)/2;cy=(lowv+highv)/2
  def project(p):return (origin+250+(p[u]-cx)*scale,335-(p[v]-cy)*scale)
  draw.text((origin+18,62),title,fill='#ffffff')
  for tri in data['bar']:
   draw.polygon([project(p) for p in tri],fill='#3c424b',outline='#718398')
  for p in data['points']:
   x,y=project(p['point']);c=colours[digit_for(p['dominantJoint'])];draw.ellipse((x-1,y-1,x+1,y+1),fill=c)
  for bone in data['bones']:
   c=colours[bone['digit']]
   for j in bone['joints']:
    a,b=project(j['head']),project(j['tail']);draw.line((a,b),fill=c,width=3)
    x,y=a;draw.ellipse((x-3,y-3,x+3,y+3),fill='#ffffff')
  for c in data['contacts']:
   a=project(c['witnesses'][0]['point']);b=project(c['witnesses'][0]['barPoint']);draw.line((a,b),fill='#ffffff',width=1)
   x,y=a;draw.ellipse((x-4,y-4,x+4,y+4),outline='#ffffff',width=2)
  if diagnostics:
   target=diagnostics['desiredThumbContact'];a=project(target['padPointBike']);x,y=a;draw.line((x-7,y,x+7,y),fill='#f8ee76',width=2);draw.line((x,y-7,x,y+7),fill='#f8ee76',width=2);
   n=target['desiredPadOutwardNormalBike'];p=target['padPointBike'];b=project([p[k]+.012*n[k] for k in range(3)]);draw.line((a,b),fill='#f8ee76',width=2)
  # A declared10mm scale in each independent orthogonal view.
  draw.line((origin+25,600,origin+25+.01*scale,600),fill='#ffffff',width=3);draw.text((origin+25,610),'10 mm',fill='#ffffff')
 for i,(digit,c) in enumerate(colours.items()):
  x=30+i*240;draw.rectangle((x,650,x+12,662),fill=c);draw.text((x+20,648),digit,fill='#ffffff')
 image.save(root/f'geometry-{side}.png')
print('Saved actual source geometric projections; no acceptance implied.')
