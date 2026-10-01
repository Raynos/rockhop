"""Keep lossless actual frame/buffer masters privately; decoded boards are inspection indexes."""
from pathlib import Path
import json,shutil,hashlib,sys
from PIL import Image,ImageDraw
repo=Path('/Users/raynos/projects/games/rockhop');adapter=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01';out=Path(sys.argv[1]) if len(sys.argv)>1 else adapter/'played-surfaces11';base=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')/out.relative_to(adapter);base.mkdir(parents=True,exist_ok=True)
for focus in ['hands','feet']:
 frames=sorted((out/focus/'frames').glob('*.png'));assert len(frames)==240;dest=base/focus/'frames';dest.mkdir(parents=True,exist_ok=True);manifest=[]
 for p in frames:
  manifest.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});shutil.move(str(p),str(dest/p.name))
 for batch in range(10):
  board=Image.new('RGB',(1280,1200),(18,18,18));draw=ImageDraw.Draw(board)
  for k in range(24):
   p=dest/frames[batch*24+k].name;im=Image.open(p).convert('RGB');im.thumbnail((320,180));x=(k%4)*320;y=(k//4)*200;board.paste(im,(x,y));draw.text((x+4,y+182),f'{focus} sample {2*(batch*24+k)+(focus=="feet")}',fill='white')
  board.save(out/focus/f'decoded-{batch:03d}.jpg',quality=91)
 (out/focus/'frames-archive.json').write_text(json.dumps({'privateFrames':str(dest),'count':len(frames),'frames':manifest,'transform':'Decoded original capture PNGs, aspect-preserving thumbnails only. No pose or pixels edited.'},indent=2)+'\n');(out/focus/'frames').rmdir()
for p in out.glob('*.f32'):
 shutil.move(str(p),str(base/p.name))
print('PRIVATE_MASTERS_ARCHIVED')
