from pathlib import Path
from PIL import Image
import json
ROOT=Path('/Users/raynos/projects/games/rockhop');O=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind03';target=ROOT/'assets/design/hero-remaster/one-rider-v2/sitting-target01/target.png';ref=Image.open(target).convert('RGB');w,h=ref.size;actual=Image.new('RGB',(w,h),(76,76,76));frames=[1,4,7,10,13,16,19,22,24]
for i,f in enumerate(frames):
 p=O/f'actual-sit-090-{f:04d}.png';im=Image.open(p).convert('RGB');cw=w//3;ch=h//3;factor=min(cw/im.width,ch/im.height);im=im.resize((round(im.width*factor),round(im.height*factor)));actual.paste(im,(i%3*cw+(cw-im.width)//2,i//3*ch+(ch-im.height)//2))
actual.save(O/'actual-nine-sitting-frames.png');board=Image.new('RGB',(w*2,h));board.paste(ref,(0,0));board.paste(actual,(w,0));board.save(O/'target-left-actual-right.png');(O/'matched-board.json').write_text(json.dumps({'target':str(target),'actualFrames':frames,'transforms':'Uniformscale/letterbox only. No mirroring/retouch/warping. Fixedactual90degreeprofilecamera','limits':'Referencecamera/lighting exactparameters unavailable. Animationtiming/framing/choreography differences require judgement, not pixelerror'},indent=2)+'\n')
