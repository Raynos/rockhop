"""Freeze existing CC0 garment topology sources; no character replacement yet."""
from pathlib import Path
import zipfile,hashlib,json
from PIL import Image,ImageDraw
archive=Path('/Users/raynos/projects/localai/assets/makehuman/system-assets-cc0.zip');run=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/source');out=Path('docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01');run.mkdir(parents=True,exist_ok=True);out.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(archive.read_bytes())=='b542127a8e25547c7c29c19f2d1d2adb9a664c80396ecd694095dbc8028a0107'
rows=[];board=Image.new('RGB',(900,960),(28,28,28));draw=ImageDraw.Draw(board)
with zipfile.ZipFile(archive) as z:
 for i in range(1,7):
  name=f'male_casualsuit{i:02d}';files=[]
  for suffix in ['obj','mhclo','thumb']:
   entry=f'clothes/{name}/{name}.{suffix}';raw=z.read(entry);dest=run/f'{name}.{suffix}'
   if dest.exists():assert dest.read_bytes()==raw
   else:dest.write_bytes(raw)
   files.append({'entry':entry,'privatePath':str(dest),'sha256':sha(raw),'bytes':len(raw)})
  lines=(run/f'{name}.obj').read_text().splitlines();faces=[s.split()[1:] for s in lines if s.startswith('f ')];v=[s.split()[1:] for s in lines if s.startswith('v ')];header=(run/f'{name}.mhclo').read_text().splitlines()[:20]
  im=Image.open(run/f'{name}.thumb').convert('RGB');im.thumbnail((430,280));x=(i-1)%2*450;y=(i-1)//2*320;board.paste(im,(x,y));draw.text((x+8,y+285),f'{name}: {len(v)}vertices / {len(faces)}faces',fill='white')
  rows.append({'name':name,'files':files,'vertices':len(v),'faces':len(faces),'quads':sum(len(f)==4 for f in faces),'triangles':sum(len(f)==3 for f in faces),'nativeHeader':header})
board.save(out/'native-template-board.jpg',quality=95)
(out/'source-inventory.json').write_text(json.dumps({'archive':str(archive),'archiveSHA256':sha(archive.read_bytes()),'officialSource':'https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html','rows':rows,'purpose':'Choose a clean separately authored garment topology template as a fundamentally different construction architecture. Source34H21shape/textures remain a retained target/detail donor; native template is not a new accepted rider or substitution for generator comparison.','limits':'Thumbnail/source topology inventory only, no source fit, rig, material bake, gameplay or appearance gate.'},indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k not in ['files','nativeHeader']} for r in rows]))
