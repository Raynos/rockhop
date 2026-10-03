from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
root=Path.cwd();font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16);parents=[None,0,1,2,3,2,5,6,7,2,9,10,11,0,13,14,0,16,17]
canvas=Image.new('RGB',(1024,1080),(27,31,35));label=ImageDraw.Draw(canvas)
for row,clip in enumerate(['bind_restore','rigid_length_stand_to_sit']):
 k=0 if row==0 else 24;D=np.load(root/'experiments'/f'C19-{clip}-{k:03d}.npz')['matrices'];P=np.load(root/'experiments/C19-bind.npz')['centres'];j=np.einsum('jab,jb->ja',D[:,:3,:],np.c_[P,np.ones(len(P))]);j=j[:,[0,2,1]];j[:,1]*=-1
 for col,(angle,view)in enumerate([(0,'front'),(90,'side')]):
  im=Image.open(root/'evidence/gray'/f'C19-{clip}-{view}.png').convert('RGB');draw=ImageDraw.Draw(im);tar=np.array([.65,0,.94])if row==0 else np.array([-.22,0,.72]);scale=2 if row==0 else .85;eye=tar+np.array([4*np.cos(np.deg2rad(angle)),4*np.sin(np.deg2rad(angle)),.2]);fw=(tar-eye)/np.linalg.norm(tar-eye);right=np.cross(fw,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,fw);s=j-tar;xy=np.c_[(.5+s@right/scale)*512,(.5-s@up/scale)*512]
  for i,p in enumerate(parents):
   if p is not None:draw.line([tuple(xy[p]),tuple(xy[i])],fill=(45,222,255),width=3)
   xx,yy=xy[i];draw.ellipse((xx-3,yy-3,xx+3,yy+3),fill=(255,212,72))
  canvas.paste(im,(col*512,row*540+28));label.text((col*512+14,row*540+5),f'Fresh C19 {clip} {view} · actual joint centres',font=font,fill='white')
canvas.save(root/'deliverables/fresh-skeleton-gray.jpg')
