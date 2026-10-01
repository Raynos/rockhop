"""Read-only exact evidence/contact sheet composition; no asset retouching."""
from PIL import Image,ImageDraw,ImageOps
from pathlib import Path
import json,sys,platform,hashlib
P=Path('/Users/raynos/projects/games/rockhop');O=P/'docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial04'
def cell(p,label,crop=None,size=(400,440)):
 im=Image.open(p).convert('RGB')
 if crop:im=im.crop(crop)
 im=ImageOps.contain(im,(size[0],size[1]-34));canvas=Image.new('RGB',size,(25,25,25));canvas.paste(im,((size[0]-im.width)//2,34+(size[1]-34-im.height)//2));ImageDraw.Draw(canvas).text((12,10),label,fill='white');return canvas
def board(name,columns,items,size=(400,440)):
 canvas=Image.new('RGB',(columns*size[0],((len(items)+columns-1)//columns)*size[1]),(25,25,25))
 for i,item in enumerate(items):canvas.paste(cell(*item,size=size),((i%columns)*size[0],(i//columns)*size[1]))
 canvas.save(O/name,quality=94)
items=[]
for mode in ['pbr','gray']:
 for view in ['front','profile','rear','three-quarter']:items.append((O/f'{mode}-neck-{view}.png',f'{mode.upper()} {view}: actual GLB'))
board('neck-pbr-gray-board.jpg',4,items,size=(320,354))
board('full-body-target-comparison.jpg',3,[(P/'assets/design/hero-remaster/one-rider-v2/hair/01-buzz.png','Approved MOCKUP target'),(O/'pbr-full-front.png','Actual C modular trial04 front',(145,10,495,635)),(O/'pbr-full-rear.png','Actual C modular trial04 full back',(145,10,495,635))],size=(480,730))
ref=P/'assets/design/hero-remaster/one-rider-v2/head/buzz-bust-reference.png'
items=[(ref,'Approved MOCKUP face target'),(O/'pbr-face-front.png','Actual GLB face front'),(O/'pbr-face-profile.png','Actual GLB face profile')]
board('face-target-comparison.jpg',3,items,size=(480,550))
(O/'composition-provenance.json').write_text(json.dumps({'Python':sys.version,'executable':sys.executable,'Pillow':Image.__version__,'platform':platform.platform(),'method':'Contained source images plus labels; actual full-body blank-background crop matches target displayed rider height. No retouching or asset manipulation.','actualFullBodyCrop':[145,10,495,635],'referenceFiles':[str(ref),str(P/'assets/design/hero-remaster/one-rider-v2/hair/01-buzz.png')],'faceReferenceCrop':None},indent=2)+'\n')
