"""Actual unretouched PNG contact sheets, explicit source labels and mockup crop."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json,hashlib,sys,PIL
P=Path('/Users/raynos/projects/games/rockhop');O=P/'docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (O/'sheets-aligned01.json').exists():raise RuntimeError('Frozen sheet exists')
rows=json.loads((O/'audit.json').read_text())['candidates'];h21Root=O/'alignment-correction01';alignedH21=json.loads((h21Root/'audit.json').read_text())['candidates'][0];rows[1]=alignedH21;ref=P/'assets/design/hero-remaster/one-rider-v2/head/buzz-bust-reference.png'
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
names=['N1 Pixal generated export','N2 actual Hunyuan 2.1 export','N3 TRELLIS.2 generated export','N4 Blender loft / projected paint','N5 Blender loft + separate eyes','N6 Blender focused eyes/lids','N7 Blender modeled swept locks']
hashes={str(ref):sha(ref)};outputs=[]
def sheet(filename,title,tiles,columns=4):
 w=536;h=574;board=Image.new('RGB',(columns*w,65+((len(tiles)+columns-1)//columns)*h),(24,26,29));draw=ImageDraw.Draw(board);draw.text((12,12),title,(245,230,200),font=font)
 for i,(path,label,sub,crop) in enumerate(tiles):
  im=Image.open(path).convert('RGBA')
  if crop:im=im.crop(crop)
  im=ImageOps.contain(im,(520,520),Image.Resampling.LANCZOS);x=(i%columns)*w+8;y=65+(i//columns)*h;bg=Image.new('RGB',(520,520),(75,75,75));bg.paste(im,((520-im.width)//2,(520-im.height)//2),im);board.paste(bg,(x,y));draw.text((x,y+524),label,(240,240,240),font=small);draw.text((x,y+547),sub,(210,205,180),font=small);hashes[str(path)]=sha(path)
 board.save(O/filename,quality=94);outputs.append({'file':filename,'SHA256':sha(O/filename)})
target=(ref,'APPROVED BUZZ MOCKUP','Target illustration; not 3D output',(200,20,975,940))
sheet('pbr-front-sheet-aligned01.jpg','NEW FACE CANDIDATES: ACTUAL PBR FRONTS VS APPROVED TARGET', [target]+[((h21Root if i==1 else O)/r['label']/'PBR-front.png',names[i],r['sourceSHA256'][:12]+' / unaccepted',None) for i,r in enumerate(rows)])
sheet('gray-profile-sheet-aligned01.jpg','GEOMETRY CHECK: ACTUAL GRAY PROFILES (TARGET HAS FRONT VIEW ONLY)',[(ref,'APPROVED FRONT MOCKUP','No corresponding target profile supplied',(200,20,975,940))]+[((h21Root if i==1 else O)/r['label']/'gray-profile.png',names[i],r['sourceSHA256'][:12]+' / neutral gray',None) for i,r in enumerate(rows)])
tiles=[]
for view in ['front','profile']:
 for label,title,count in [('N1-Pixal-raw','PIXAL','10,163,546'),('N3-TRELLIS2-raw','TRELLIS.2','15,915,612')]:
  tiles.extend([(O/label/f'pre-reduction-gray-{view}.png',title+' native raw '+view,count+' triangles; no reduction',None),(O/label/f'gray-{view}.png',title+' reduced export '+view,'Same camera and frame / diagnostic',None)])
sheet('pre-reduction-vs-export-sheet-aligned01.jpg','ACTUAL RETAINED RAW SHAPE VS REDUCED EXPORT — NO REPAIR',tiles)
(O/'sheets-aligned01.json').write_text(json.dumps({'status':'Parent-only judgment, no acceptance score assigned','sourceSHA256':hashes,'outputs':outputs,'recipeSHA256':sha(Path(__file__)),'referenceCrop':[200,20,975,940],'renderCrop':None,'operations':'Contain/resize, alpha composite on gray, labels/layout, JPEG encode only; no retouching','sharedPixelOnlyPython':sys.executable,'PythonSHA256':sha(Path(sys.executable)),'PillowVersion':PIL.__version__,'PillowPath':PIL.__file__},indent=2)+'\n')
