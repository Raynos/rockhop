"""Preserve lossless originals privately; keep whole-clip boards and movie evidence."""
from pathlib import Path
import json,hashlib,shutil,sys
from PIL import Image,ImageDraw
repo=Path('/Users/raynos/projects/games/rockhop')
run=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind08/decoded-evidence')
folder=Path(sys.argv[1]).resolve();relative=folder.relative_to(repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind08');frames=sorted((folder/'frames').glob('*.png'));assert frames
archive=run/relative/'frames';archive.mkdir(parents=True,exist_ok=True);manifest=[]
for p in frames:
 dest=archive/p.name
 if dest.exists():assert dest.read_bytes()==p.read_bytes()
 else:shutil.copy2(p,dest)
 manifest.append({'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
boards=[]
for start in range(0,len(frames),24):
 canvas=Image.new('RGB',(1920,6*300),(24,24,24));draw=ImageDraw.Draw(canvas)
 for k,p in enumerate(frames[start:start+24]):
  im=Image.open(p).convert('RGB');im.thumbnail((480,270));x=(k%4)*480;y=(k//4)*300;canvas.paste(im,(x,y));draw.text((x+8,y+275),p.stem,fill='white')
 out=folder/('decoded-%03d.jpg'%(start//24));canvas.save(out,quality=94);boards.append(out.name)
(folder/'frames-archive.json').write_text(json.dumps({'privateLosslessFrames':str(archive),'frames':manifest,'decodedBoards':boards,'scope':'All captured PNGs retained untouched; whole movie decoded in ordered boards for parent review. No pose or image editing.'},indent=2)+'\n')
for p in frames:p.unlink()
(folder/'frames').rmdir();print(folder,len(frames),'ARCHIVED_EXACT')
