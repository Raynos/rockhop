"""Reproducible offline C1 concrete / tidal substrate PBR, physical metre scale.
No photo inputs, runtime noise, scene RNG, geometry or private animation clocks.
"""
import hashlib, json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'out'; DELIVERY=ROOT/'delivery'; OUT.mkdir(exist_ok=True); DELIVERY.mkdir(exist_ok=True)
TAU=math.pi*2

def periodic(x,y):
    return (np.sin(TAU*(x+2*y)+.6)*.42+np.cos(TAU*(3*x-y)+1.3)*.28+np.sin(TAU*(5*x+3*y)+2.1)*.18+np.cos(TAU*(7*x-4*y)+.3)*.12)

def gaussian(u,v,cx,cy,sx,sy):
    dx=np.abs(u-cx);dx=np.minimum(dx,1-dx)
    dy=np.abs(v-cy);dy=np.minimum(dy,1-dy)
    return np.exp(-(dx/sx)**2-(dy/sy)**2)

def build(kind,w,h,metres):
    u,v=np.meshgrid(np.arange(w)/w,np.arange(h)/h); macro=periodic(u,v)
    # The tiny aggregate is below old painter's high-contrast grain and has no
    # broad black/white pebble stipple. Fixed analytic frequencies are tileable.
    grain=(np.sin(TAU*(u*103+v*67))*.45+np.cos(TAU*(u*47-v*131))*.3+np.sin(TAU*(u*173+v*151))*.25)
    height=np.zeros((h,w)); ao=np.ones((h,w)); rust=np.zeros((h,w)); damp=np.zeros((h,w))
    if kind=='quay-top':
        base=np.array([137.,143.,132.]); variation=macro*5+grain*1.9
        damp=np.maximum(gaussian(u,v,.18,.37,.22,.15),gaussian(u,v,.73,.83,.29,.17))*.64
        damp=np.maximum(damp,gaussian(u,v,.58,.17,.10,.07)*.45)
        # Four 3m pours over the 12m U tile; one longitudinal joint every 3m.
        jointU=np.abs(np.sin(TAU*u*2));jointV=np.abs(np.sin(TAU*v))
        seam=np.exp(-(jointU/.018)**2)+np.exp(-(jointV/.015)**2)
        height-=seam*.0028;ao-=np.minimum(.20,seam*.16)
        variation-=np.minimum(27,seam*24)
        # One different repaired pour, without a black patch under the tire.
        repair=((u>.50)&(u<.75)&(v>.50)).astype(float)
        variation+=repair*4
        rust=gaussian(u,v,.36,.91,.055,.06)*.28+gaussian(u,v,.88,.72,.04,.08)*.23
        rough=.81-damp*.29
        height+=grain*.00010+macro*.00022
    elif kind=='quay-wall':
        base=np.array([155.,154.,142.]);variation=macro*4+grain*1.35
        # Image V=0 is quay top; loader flipY=false matches existing v=(py-y)/1.45.
        foot=np.clip((v-.65)/.35,0,1);damp=foot*(.55+.12*np.sin(TAU*u*3)+macro*.09)
        tide=np.exp(-((v-.77-.018*np.sin(TAU*u*3))/.06)**2)
        variation+=tide*4
        seam=np.exp(-(np.abs(np.sin(TAU*u*2))/.016)**2)
        height-=seam*.0015;variation-=seam*16;ao-=seam*.13
        pourline=np.exp(-((v-.49)/.008)**2);height-=pourline*.0005;variation-=pourline*3
        for x in (.075,.175,.325,.425,.575,.675,.825,.925):
            for y in (.23,.69):
                dx=np.minimum(np.abs(u-x),1-np.abs(u-x))*metres[0];dy=(v-y)*metres[1]
                hole=np.exp(-((dx/.018)**2+(dy/.016)**2));height-=hole*.006;variation-=hole*43;ao-=hole*.29
        for x,reach in ((.10,.41),(.37,.57),(.62,.32),(.89,.63)):
            dx=np.minimum(np.abs(u-x-.0015*np.sin(v*19)),1-np.abs(u-x-.0015*np.sin(v*19)))*metres[0]
            run=np.exp(-(dx/.035)**2)*np.clip(1-v/reach,0,1)
            rust+=run*.43
        rough=.84-damp*.22;height+=grain*.00007
    else:
        # Pale low-contrast multiplier: existing vertex palette supplies yard /
        # sand / damp tide-silt colour; adding a second brown tint crushes it.
        base=np.array([222.,218.,204.]);variation=macro*7+grain*1.1
        damp=np.maximum(gaussian(u,v,.23,.48,.29,.21),gaussian(u,v,.82,.12,.21,.24))*.29
        bed=np.sin(TAU*(u*3+v*2)+.21*np.sin(TAU*(u*2-v)))
        variation+=bed*1.1;height+=bed*.0003+grain*.00012
        rough=.9-damp*.14
        # Sparse small shells/gravel, not wallpaper-wide pepper.
        for i in range(28):
            x=(i*.61803398875+.17)%1;y=(i*.41421356237+.31)%1
            shell=gaussian(u,v,x,y,.0025,.0018);variation+=shell*(4 if i%2 else -4);height+=shell*.0007
    rgb=np.broadcast_to(base,(h,w,3)).copy()+variation[:,:,None]
    # Broad damp absorption and muted physical rust deposits.
    rgb*=1-damp[:,:,None]*.21
    rust=np.clip(rust,0,.5);rgb=rgb*(1-rust[:,:,None])+np.array([138.,91.,54.])*rust[:,:,None]
    if kind=='quay-wall':rgb=rgb*(1-foot[:,:,None]*.13)+np.array([69.,84.,65.])*foot[:,:,None]*.13
    albedo=np.clip(rgb,0,255).astype(np.uint8)
    # Heights are metres, gradients use metres per pixel. These are OpenGL
    # tangent normals; image rows correspond directly to increasing mesh V.
    du=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))/(2*metres[0]/w)
    if kind=='quay-wall':dv=np.gradient(height,metres[1]/h,axis=0)
    else:dv=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))/(2*metres[1]/h)
    normals=np.stack((-du,-dv,np.ones_like(height)),axis=2);normals/=np.linalg.norm(normals,axis=2)[:,:,None]
    normal=np.clip((normals*.5+.5)*255,0,255).astype(np.uint8)
    arm=np.stack((np.clip(ao,.4,1),np.clip(rough,.48,.95),np.zeros_like(height)),axis=2)
    arm=np.clip(arm*255,0,255).astype(np.uint8)
    output=[]
    for channel,data in (('albedo',albedo),('normal',normal),('arm',arm)):
        image=Image.fromarray(data,'RGB');name=f'{kind}-{channel}.phone.webp';path=DELIVERY/name
        image.save(path,'WEBP',lossless=channel!='albedo',quality=90,method=6,exact=True)
        image.save(OUT/f'{kind}-{channel}.png')
        output.append({'file':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width':w,'height':h,'channel':channel,'colorSpace':'sRGB' if channel=='albedo' else 'linear','physicalMetres':metres})
    return output

materials=[('quay-top',512,512,(12,6)),('quay-wall',512,128,(12,1.45)),('tidal-ground',256,256,(8,8))]
files=[]
for entry in materials:files+=build(*entry)
# Offline colour/PBR contact board, not a production render or art acceptance.
board=Image.new('RGB',(1024,900),(29,42,43));draw=ImageDraw.Draw(board)
for row,(kind,_,_,metres) in enumerate(materials):
    draw.text((12,row*300+8),f'{kind}: {metres[0]}m x {metres[1]}m  | albedo / OpenGL normal / ARM',(228,228,210))
    for col,channel in enumerate(('albedo','normal','arm')):
        image=Image.open(DELIVERY/f'{kind}-{channel}.phone.webp');image.thumbnail((326,260));board.paste(image,(12+col*338,row*300+32))
board.save(DELIVERY/'source-board.jpg',quality=92)
# 2x2 repetitions expose any U/V seam before parent played review.
for kind in ('quay-top','tidal-ground'):
    img=Image.open(DELIVERY/f'{kind}-albedo.phone.webp');tiling=Image.new('RGB',(img.width*2,img.height*2))
    for x in (0,img.width):
        for y in (0,img.height):tiling.paste(img,(x,y))
    tiling.save(DELIVERY/f'{kind}-tiling.jpg',quality=90)
manifest={'status':'unapplied offline C1 material candidate; no played/device approval','authoring':'physical dimensions, manufactured joints/tie holes, damp/salt/rust deposits; no photo inputs','sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'files':files,'compressedBytes':sum(f['bytes'] for f in files),'residentRgba8MipsBytes':sum(f['width']*f['height']*4*4/3 for f in files),'mapping':{'top':{'existingUV':'arc/6,z/6','repeat':[.5,1],'tileMetres':[12,6],'wrap':['repeat','repeat']},'wall':{'existingUV':'x/4,(profileY-y)/1.45','repeat':[1/3,1],'tileMetres':[12,1.45],'wrap':['repeat','clamp'],'flipY':False},'terrain':{'existingUV':'x/4,z/4','repeat':[.5,.5],'tileMetres':[8,8],'wrap':['repeat','repeat']}}}
(DELIVERY/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
