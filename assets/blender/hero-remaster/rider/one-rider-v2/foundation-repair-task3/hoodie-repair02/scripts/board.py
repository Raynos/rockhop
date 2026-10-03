from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
out=Path(__file__).resolve().parents[1];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
board=Image.new('RGB',(1440,1150),'#171c25');d=ImageDraw.Draw(board)
d.text((25,18),'Preferred rider: isolated foundation progress — candidate, not a finished repair',font=font,fill='white')
cols=[('Current field','cuff-source-1-pbr-front.png','v2-control-sit-1-pbr-side.png'),('New cuff ownership / local chest + neck','cuff-anatomical-1-pbr-front.png','v2-posture-sit-1-pbr-side.png'),('Gray check: material-independent','cuff-anatomical-1-gray-front.png','v2-posture-sit-1-gray-side.png')]
for i,(label,a,b) in enumerate(cols):
 d.text((i*480+15,57),label,font=small,fill='#d0d9e8')
 for y,file in [(85,a),(580,b)]:board.paste(Image.open(out/'renders'/file).convert('RGB'),(i*480,y))
d.text((20,1070),'Matched ±65° wrist test: actual glove/cloth crossings 28/25 → 0/0; sewn aliases stay closed.',font=small,fill='white')
d.text((20,1100),'Cuff folds and raised-arm stretch still need work. Hip cloth crossings and saddle support remain unresolved.',font=small,fill='#ffcc88')
board.save(out/'deliverables/foundation-progress-before-after.png')
