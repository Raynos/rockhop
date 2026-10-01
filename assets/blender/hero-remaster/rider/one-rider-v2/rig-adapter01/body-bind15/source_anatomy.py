"""Source-only CPU orthographic anatomy inventory, never played acceptance."""
import io,json
import numpy as np
from PIL import Image,ImageDraw
from common import load,accessor,OUT
raw,j,b,p,_=load();rest,_,_=accessor(j,b,p['attributes']['POSITION']);uv,_,_=accessor(j,b,p['attributes']['TEXCOORD_0']);ix,_,_=accessor(j,b,p['indices']);tri=ix.reshape(-1,3);mat=j['materials'][0];it=j['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source'];v=j['bufferViews'][j['images'][it]['bufferView']];tex=Image.open(io.BytesIO(b[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB');pixels=np.array(tex);tuv=uv[tri].mean(1);rgb=pixels[np.clip((tuv[:,1]*tex.height).astype(int),0,tex.height-1),np.clip((tuv[:,0]*tex.width).astype(int),0,tex.width-1)];mask=np.all((rest[tri,:,][:,:,1]>.50)&(rest[tri,:,][:,:,1]<1.12),axis=1);tris=np.flatnonzero(mask)
board=Image.new('RGB',(1800,850),'#1a1d21');d=ImageDraw.Draw(board)
for col,(title,horizontal,depth,sign) in enumerate([('FRONT source +X',2,0,1),('REAR source -X',2,0,-1),('PROFILE source +Z',0,2,1)]):
 cx=300+600*col;center=0 if horizontal==2 else .65
 def xy(v):return (cx+(float(v[horizontal])-center)*1050,760-(float(v[1])-.5)*1050)
 for t in sorted(tris,key=lambda t:float(rest[tri[t],depth].mean())*sign):d.polygon([xy(v) for v in rest[tri[t]]],fill=tuple(int(v) for v in rgb[t]))
 for y,color,label in [(.959175,'#ff7766','hip bind .959m'),(.86275,'#6be8ee','old blend top .863m'),(.7917,'#6be8ee','old blend bottom .792m')]:
  yy=xy(np.array([.65,y,0]))[1];d.line([(cx-220,yy),(cx+220,yy)],fill=color,width=2);d.text((cx-230,yy-16),label,fill=color)
 d.text((cx-220,34),title,fill='white')
board.save(OUT/'source-anatomy.png');print('SOURCE_ANATOMY_CPU_ONLY',len(tris))
