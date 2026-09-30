"""Pixel-only layout of preserved rider references and exact rendered frames."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont

REPO=Path(__file__).resolve().parents[5]
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
OUT=REPO/'docs/evidence/hero-remaster/rider-search-v1/review';OUT.mkdir(exist_ok=True)
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(fontpath,20);big=ImageFont.truetype(fontpath,30)
names=['Faithful Street','Solid Workwear','Compact Athlete','Relaxed Premium','Readable Sculpted']
def fit(im,w,h):
    im=im.convert('RGBA');im.thumbnail((w,h),Image.Resampling.LANCZOS)
    tile=Image.new('RGBA',(w,h),(88,88,88,255));tile.alpha_composite(im,((w-im.width)//2,(h-im.height)//2));return tile.convert('RGB')
def sheet(native=False):
    w,h,head=360,540,50;im=Image.new('RGB',(5*w,84+4*(h+head)),(24,27,31));draw=ImageDraw.Draw(im)
    draw.text((18,16),'RIDER BODY SEARCH — references and fifteen raw bodies',font=big,fill='white')
    draw.text((18,54),'Native geometry' if native else 'Working exports / common dielectric studio diagnostic',font=font,fill=(190,200,215))
    for row,engine in enumerate(['reference','hunyuan','trellis','pixal']):
        for i in range(1,6):
            d=f'{i:02d}';x=(i-1)*w;y=84+row*(h+head)
            if engine=='reference':path=REPO/f'assets/blender/hero-remaster/rider/search-v1/refs/{d}.png';label=f'REF {i} — {names[i-1]}'
            else:
                tier='native-gray' if native else 'working';path=ROOT/'rendered'/engine/d/tier/'0000.png'
                label=f'{engine[0].upper()}{i} — {engine.upper()}'
            im.paste(fit(Image.open(path),w,h),(x,y+head));draw.text((x+12,y+15),label,font=font,fill='white')
    path=OUT/('native-overview.jpg' if native else 'front-overview.jpg');im.save(path,quality=95,subsampling=0);return path

files=[sheet(),sheet(True)]
for i in range(1,6):
    d=f'{i:02d}';parts=[REPO/f'assets/design/hero-remaster/rider-search-v1/targets/{d}.png']+[ROOT/'rendered'/e/d/'working/board.png' for e in ['hunyuan','trellis','pixal']]
    w,h,head=600,940,50;im=Image.new('RGB',(4*w,h+head),(24,27,31));draw=ImageDraw.Draw(im)
    labels=[f'TARGET {i} / approximate views',f'H{i} / Hunyuan3D',f'T{i} / TRELLIS.2',f'P{i} / Pixal3D']
    for j,p in enumerate(parts):
        im.paste(fit(Image.open(p),w,h),(j*w,head));draw.text((j*w+10,15),labels[j],font=font,fill='white')
    path=OUT/f'design-{d}-comparison.jpg';im.save(path,quality=95,subsampling=0);files.append(path)
manifest={'status':'Layout of preserved inputs and real render frames; no body retouch','sourceFrames':'working/native-gray frame0000; exact canonical front alignment','limits':['Target view angles approximate','Working vs native gray geometry differs due provider export','Layout resizes with preserved aspect ratio; no face/limb retouch'],'files':[{'path':str(p.relative_to(REPO)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files]}
(OUT/'layout.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(OUT)
