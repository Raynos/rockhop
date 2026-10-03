from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json
root=Path.cwd();p=root/'evidence/movie-frames';out=root/'deliverables'
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16)
for movie,views in [('fresh-rig-before-after',['front','side','back']),('fresh-rig-hip-motion',['hip'])]:
 folder=root/'evidence'/movie;folder.mkdir(exist_ok=True);seq=[]
 for view in views:
  seq +=[(view,k)for k in range(25)]+[(view,24)]*12+[(view,k)for k in range(23,-1,-1)]+[(view,0)]*8
 for j,(view,k)in enumerate(seq):
  im=Image.new('RGB',(960,556),(27,31,35));d=ImageDraw.Draw(im);d.text((16,8),'A · current rig / weights',font=font,fill=(255,205,143));d.text((496,8),'C19 · fresh rig / weights',font=font,fill=(133,225,206));
  for col,n in enumerate(['A','C19']):im.paste(Image.open(p/view/n/f'{k:03d}.png'),(col*480,40))
  d.text((16,529),f'{view.upper()} · stand-to-sit {k/24:.0%} · same mesh, contacts and control',font=small,fill='white');d.text((651,529),'Collision gate: not passed',font=small,fill=(255,175,141));im.save(folder/f'{j:04d}.png')
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(folder/'%04d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out/f'{movie}.mp4')],check=True)
# Final full-angle filmstrip, latest independently frozen pose arrays.
o=Image.new('RGB',(960,540*4),(27,31,35));d=ImageDraw.Draw(o)
for row,(view,k)in enumerate([('front',24),('side',24),('back',24),('hip',12)]):
 for col,n in enumerate(['A','C19']):o.paste(Image.open(p/view/n/f'{k:03d}.png'),(col*480,row*540+35));d.text((col*480+15,row*540+7),f'{n} {view} key {k}',font=small,fill='white')
o.save(out/'fresh-rig-review.jpg')
# Gray endpoint and unchanged standing bind proof.
for title,clip in [('gray-seated','rigid_length_stand_to_sit'),('gray-standing-bind','bind_restore')]:
 o=Image.new('RGB',(1024,540*3),(27,31,35));d=ImageDraw.Draw(o)
 for row,view in enumerate(['front','side','back']):
  for col,n in enumerate(['A','C19']):o.paste(Image.open(root/'evidence/gray'/f'{n}-{clip}-{view}.png'),(col*512,row*540+28));d.text((col*512+15,row*540+5),f'{n} {view}',font=small,fill='white')
 o.save(out/f'{title}.jpg')
print('MOVIES AND REVIEW SHEETS WRITTEN')
