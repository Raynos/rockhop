"""Compose frozen actual matched baseline/rejected orbits; no geometry edits."""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image,ImageDraw
R=Path('/Users/raynos/projects/games/rockhop');F=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01'
E=F/'continuous-sculpt179';M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/continuous-sculpt179');pairs=[]
for mode in ['pbr','gray']:
    movie=E/f'UNACCEPTED-neutral-{mode}-turntable.mp4';d=M/f'decoded-{mode}';d.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(movie),str(d/'%02d.png')],check=True)
    images=sorted(d.glob('*.png'));assert len(images)==24
    canvas=Image.new('RGB',(1200,1000),'#222222');draw=ImageDraw.Draw(canvas)
    for i,p in enumerate(images):
        im=Image.open(p).convert('RGB').resize((200,225));x=(i%6)*200;y=(i//6)*250;canvas.paste(im,(x,y));draw.text((x+4,y+229),f'{mode} frame{i} / {i/6:.3f}s',fill='white')
    canvas.save(M/f'{mode}-decoded-24.png')
    header=Image.new('RGB',(800,50),'#222222');dr=ImageDraw.Draw(header)
    dr.text((12,7),'NEW C19 BASELINE',fill='white');dr.text((412,7),'REJECTED SCULPT: UNRIGGED / UNBAKED',fill='#ffbb88')
    dr.text((12,28),'Matched actual neutral orbit; NOT pose / contact approval',fill='white')
    hp=M/f'{mode}-comparison-header.png';header.save(hp)
    before=F/'neutral-control179'/f'CONTROL-neutral-{mode}-turntable.mp4';out=E/f'REJECTED-matched-neutral-{mode}.mp4'
    assert not out.exists(),'Freeze comparison media; reproduce only into a new isolated output'
    subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(before),'-threads','2','-i',str(movie),'-loop','1','-i',str(hp),'-filter_complex','[0:v][1:v]hstack=inputs=2[b];[2:v][b]vstack=inputs=2[v]','-map','[v]','-t','4','-r','6','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','19',str(out)],check=True)
    pairs.append({'movie':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
(E/'matched-comparison.json').write_text(json.dumps({'matched':pairs,'settings':'Both frozen render recipes same camera/light/resolution/gray,24frames6fps4s; side-by-side before left/rejected sculpt right, header added only. No re-render or source geometry changes.','limits':'Prototype plain material lacks PBR bake and detail. Source baseline already unaccepted for motion. Not improvement or game-ready claim.'},indent=2)+'\n')
