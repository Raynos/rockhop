"""Verify the preserved neutral control and decode every actual film frame."""
from pathlib import Path
import copy,hashlib,json,struct,subprocess
from PIL import Image,ImageDraw
R=Path('/Users/raynos/projects/games/rockhop')
E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/neutral-control179'
M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/neutral-control179')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def glb(p):
    b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
manifest=json.loads((E/'manifest.json').read_text());source=Path(manifest['source']);control=Path(manifest['control'])
assert sha(source)==manifest['sourceSHA256'] and sha(control)==manifest['controlSHA256']
j,b=glb(source);k,c=glb(control);expected=copy.deepcopy(j)
for node in expected['nodes']:node.pop('skin',None)
expected.pop('skins',None);expected.pop('animations',None)
assert expected==k and b==c
recipe=R/'assets/blender/hero-remaster/rider/one-rider-v2/clean-upper-shell01/drafted-raglan/render.py'
assert sha(recipe)==manifest['matchedOriginalRecipeSHA256']
assert Path(manifest['renderRecipe']).read_text()==recipe.read_text().replace('/clean-upper-shell01/drafted-raglan','/clean-upper-shell01/neutral-control179')
decoded=[]
for i,record in enumerate(manifest['movies']):
    movie=Path(record['path']);assert sha(movie)==record['sha256'] and movie.stat().st_size==record['bytes']
    played=json.loads((E/'parent-playback'/f'played-{i}.json').read_text())
    assert played['video']['ended'] and played['video']['muted'] and not played['errors']
    assert played['SHA256']==record['sha256']
    mode='gray' if 'gray'in movie.name else'pbr';frames=M/('decoded-'+mode);frames.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(movie),str(frames/'%02d.png')],check=True)
    images=sorted(frames.glob('*.png'));assert len(images)==24
    sheet=Image.new('RGB',(1200,1000),'#222222');draw=ImageDraw.Draw(sheet)
    for n,p in enumerate(images):
        im=Image.open(p).convert('RGB').resize((200,225));x=(n%6)*200;y=(n//6)*250;sheet.paste(im,(x,y));draw.text((x+4,y+229),f'{mode} frame{n} / {n/6:.3f}s',fill='white')
    sheet.save(M/f'{mode}-decoded-24.png');decoded.append({'movieSHA256':sha(movie),'frames':24,'sheet':str(M/f'{mode}-decoded-24.png')})
(E/'parent-review.json').write_text(json.dumps({'status':'BYTE_VERIFIED_MATCHED_NEUTRAL_BASELINE_NOT_ACCEPTED_RIDER','originalBINAndAllOtherJSONExact':True,'explicitDifferences':'Skins/animations and node skin references removed only; nothing else changed.','exactCameraLightCPUGrayRecipeExceptNamespace':True,'decoded':decoded,'limits':'Current NEW C19 baseline, not historical production body. Neutral turntable does not validate broad arm/hip motion or donor topology; independent rest and gameplay defects remain.'},indent=2)+'\n')
print(json.dumps({'sourceExact':True,'frameCount':48}))
