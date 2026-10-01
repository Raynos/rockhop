"""Compose unchanged render boards and freeze the raw display error explicitly."""
from pathlib import Path
import json,hashlib,datetime
from PIL import Image,ImageDraw
BASE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/whole-hood-donor-comparison')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((BASE/'manifest.json').read_text())
assert not (BASE/'freeze-manifest.json').exists()
ids=['01','02','03','05'];font='/System/Library/Fonts/Supplemental/Arial.ttf'
from PIL import ImageFont
f=ImageFont.truetype(font,18);small=ImageFont.truetype(font,14)
def board(name,title,rows):
 w=400;h=438;top=88;out=Image.new('RGB',(w*4,top+h*len(rows)),(24,24,24));d=ImageDraw.Draw(out)
 d.text((12,8),title,font=f,fill='white');d.text((12,32),'Untouched NEW donors; displayed height1.8m old-hair-inclusive; +Zup/front-Y/profile+X/rear+Y',font=small,fill='white')
 d.text((12,54),'Original faces/hair remain rejected. Hood comparison only; no extraction, rig or character acceptance.',font=small,fill=(255,200,90))
 for col,i in enumerate(ids):
  s=m['candidates'][i]['sources'];p=next(p for p in s if p.endswith('working-display2.glb'));sh=s[p]['sha256'][:12]
  for row,(key,label) in enumerate(rows):
   y=top+row*h;x=col*w;im=Image.open(BASE/i/f'{key}.png').convert('RGB');im.thumbnail((400,400));out.paste(im,(x,y+38));d.text((x+8,y+3),f'H21-{i} {label}',font=f,fill='white');d.text((x+8,y+23),f'working-display2 SHA {sh}',font=small,fill='white')
 p=BASE/name;out.save(p,quality=94);return str(p)
boards={
 'PBR':board('wholehood-pbr-board.jpg','Matched native PBR wholehood donors',[(f'pbr-hood-{a}',a) for a in ['front','profile','rear']]),
 'gray':board('wholehood-gray-board.jpg','Matched neutral-gray shape; textured 55k-triangle reduction',[(f'gray-hood-{a}',a) for a in ['front','profile','rear']]),
 'torso':board('wholehood-torso-board.jpg','Source torso context; PBR and gray',[(f'{a}-torso-front',a+' front') for a in ['pbr','gray']]),
}
failure={'status':'REJECTED diagnostic display setup; all12RAW images excluded from hood comparison','cause':'Recipe applied worldX180 to imported raw that was already upright; actual image raw-gray-hood-front01 contains upside-down legs rather than hood. This is our display transform error, not generator failure.','wrongRawViews':{v['path']:v['sha256'] for v in m['views'] if v['source'].startswith('higher-resolution')},'nextCorrection':'Separate correction after parent checkpoint: no worldX180; retain identical PBR canonical normalization; inspect one real RAW frontal witness before other11 renders.','noSourcesModified':m['allSourcesUnchanged']}
(BASE/'raw-display-failure.json').write_text(json.dumps(failure,indent=2)+'\n')
report={'status':'UNACCEPTED comparison-only; parent alone selects donor','actualStartUTC':m['actualStartUTC'],'renderFinishedUTC':m['finishedUTC'],'freezeUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadlineUTC':m['deadlineUTC'],'actualValidViews':32,'failedRawViews':12,'sourceCount':20,'allSourcesUnchanged':m['allSourcesUnchanged'],'boardPaths':boards,'sourcePreservationScope':'All20 source files byte-identical. No extraction, cuts, topology/UV/material alteration or geometry export. Rigid/uniform display transforms only; gray is scene material override.','parentPreliminaryObservations':{'01':'Broad cowl and coherent backfold; original head/hair BAD and ineligible.','02':'Plausible hood albeit flatter folds.','03':'Dark rear neck band/material contamination.','05':'Actual large rear holes; rejected as donor by parent.'},'limitations':['Parent still/profile/gray review pending; source states are not accepted character assets.','Higher-resolution316k–344k NPZ/GLB retained untouched; raw render orientation failed, so this round cannot infer pre/post reduction defects.','No neck bending, motion, hood isolation topology or clearance/contact evidence; no rig/production changes.','No numeric quality claim; mockup lighting differs.'],'recipeSHA256':{p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('compare_whole_hood_donors.py')]}}
(BASE/'report.json').write_text(json.dumps(report,indent=2)+'\n')
(BASE/'README.md').write_text('''# NEW wholehood donor comparison — unaccepted

H21-01/02/03/05 original PBR sources are compared unchanged in matched front/profile/rear hood views and frontal torso context. The existing H21-04 body is unchanged. No donor is extracted or accepted. Parent preliminary visual reading favors 01 broad cowl/backfold and regards 02 as plausible; 03 has dark rear neck contamination; 05 has rear holes and is rejected as donor. Original heads/hair are rejected and remain comparison-only.

- `wholehood-pbr-board.jpg`: all4donors, front/profile/rear native PBR.
- `wholehood-gray-board.jpg`: same4donors, same3views, neutral-gray55k reduction.
- `wholehood-torso-board.jpg`: source frontal torso context, nativePBR/gray.
- `manifest.json`: exact20sourceSHA/bytes,32valid/12failed renderSHA, source matrices, retained rawNPZ shape counts, source-after proof.
- `raw-display-failure.json`: all12higher-resolution raw renders are WRONG (upside-down legs); excluded. WorldX180 was our incorrect display transform. No inference about reducer vs generator is supported by those images. Freeze before correction; next step needs an actual upright RAW front witness, then matched raw views.

CPUBlender5.2.1 shared read-only executable,2threads16samples640pxAgX. LaneC configuration/temp/CLIvenv isolated; system-site Pillow used read-only for composition. Existing source materials are preserved and gray uses scene override. Geometry, UV and source textures remain untouched. Displaynormalization1.8m includes old hair; +Zup,frontcamera-Y,profile+X,rear+Y. Uniformscale/matrices are recorded. Higher-resolution raws (316248/344464/338506/312878 NPZtriangles) stay separate, untouched.

No topology, neck deformation, body integration, gameplay or contact pass. No source face eligibility, rigging or production asset claim. Parent judges actual evidence. Old H21-04 cut/strip/lining repair lineage remains retired at15failures.
''')
paths=[p for p in BASE.rglob('*') if p.is_file()];freeze={'freezeUTC':report['freezeUTC'],'allSourcesUnchanged':True,'files':{str(p.relative_to(BASE)):sha(p) for p in sorted(paths)}}
(BASE/'freeze-manifest.json').write_text(json.dumps(freeze,indent=2)+'\n')
print(json.dumps(report,indent=2))
