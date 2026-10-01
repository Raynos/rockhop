"""Freeze exact source-preserved RAW/55k/PBR matched display witnesses."""
from pathlib import Path
import json,hashlib,datetime
from PIL import Image,ImageDraw,ImageFont
BASE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern')
OUT=BASE/'raw-hood01-display-correction';prior=BASE/'whole-hood-donor-comparison';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((OUT/'report.json').read_text());assert len(r['views'])==3;assert not (OUT/'freeze-manifest.json').exists()
f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19);s=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
im=Image.new('RGB',(1200,1400),(24,24,24));d=ImageDraw.Draw(im);d.text((8,8),'H21-01 untouched wholehood: high-resolution RAW vs55k reduction vsnativePBR',font=f,fill='white');d.text((8,34),'Canonical1.8m including oldhair; camera matchedfront-Y/profile+X/rear+Y. RAW source is preserved316248triangles.',font=s,fill='white');d.text((8,56),'Corrected displayonly; oldhead/hair rejected. No donor extraction, clearance or neck deformation pass.',font=s,fill=(255,190,70))
rows=[('RAW316248triangles',OUT,'raw-gray-hood-','42b23ca04f82'),('55kreductiongray',prior/'01','gray-hood-','783b58fec94a'),('55kreductionnativePBR',prior/'01','pbr-hood-','783b58fec94a')]
for y,(label,p,prefix,h) in enumerate(rows):
 for x,view in enumerate(['front','profile','rear']):
  top=80+y*440;d.text((x*400+8,top),label+' '+view,font=f,fill='white');d.text((x*400+8,top+23),'sourceSHA '+h,font=s,fill='white');a=Image.open(p/(prefix+view+'.png')).convert('RGB');a=a.resize((400,400),Image.Resampling.LANCZOS);im.paste(a,(x*400,top+40))
im.save(OUT/'raw-reduced-pbr-hood01-board.jpg',quality=94)
r['freezeUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();r['actualVisualOrientationWitness']='All3actualRAWviews inspected upright; front torso/hood/head, profile and rear hood match same55k source camera. Old rejectedhead/hair visible only as source orientation/context.';r['comparisonBoard']=str(OUT/'raw-reduced-pbr-hood01-board.jpg');r['sourceSHAAfter']={p:sha(p) for p in r['sourceSHA256']};r['sourceHashesUnchanged']=r['sourceSHA256']==r['sourceSHAAfter'];assert r['sourceHashesUnchanged']
r['limitations']=['Read-only comparison; originalrawandtexturedsourceheads rejected.','No meshisolation/hoodheadseparation/topology pass; donor extraction only after parentcheckpoint.','SameRGBAneutralshader onraw smoothnormalsto sourceimportdefaults; no re-topology/smoothing/sourcechanges.','No calibration score versusmockup, rigging/deformation/contact or production changes.','H21-02 rawleft untouched/unrenderedhere; donor01isprimaryparentdirection,02secondaryactualPBR/graypreviouscomparison remains unchanged.']
(OUT/'report.json').write_text(json.dumps(r,indent=2)+'\n')
(OUT/'README.md').write_text('''# H21-01 corrected high-resolution raw display — unaccepted

Three actual upright raw front/profile/rear hood views use the same canonical display scale, camera and lighting as preserved55k reduction/nativePBR. Removing our extraneous object-worldX180 rotation fixes previous upside-down display. Source geometry, materials, UVs and files are untouched; previous12failedRAWviews/log remain frozen in priorcomparison. This corrects a diagnostic only.

`raw-reduced-pbr-hood01-board.jpg` compares source316248triangle RAW,55kreductiongray andnativePBR in matched3views. Frontal witness was inspected and sent to parent before profile/rear. Originalheads/hair remain rejected and comparison-only. Fullhoodprofile/rearfolds visible in bothrawandreduction; no extraction, integration or characteracceptance.

Sources: raw-shapeNPZ158114vertices316248faces SHAe4580ff1b95af69c0cfe4273f34913950ae284ab32d4d38254cfbd5f55e6055d; rawGLB SHA42b23ca04f82728299caca26e958996e8ffaeb8fc491d2e77b1983ef4880e0c2. PBRworking-display2 SHA783b58fec94aa9657dc44bed14d4767af610bfa29b336f916d5107118a01d5cb. Exactmatrices/importmeshcoordinateSHA/env/source-afterhashes inreport.json. All3sourcefiles unchanged.

CPUBlender5.2.1,2threads16samples640pxAgX; sharedinstalledbinarywithlaneCisolatedconfig/extensions/scripts/temp, noGPU. Same1.8mold-hair-inclusiveuniformscale; front-Y/profile+X/rear+Y. Pillowboardcompositionreadsrenderpixels withoutretouching. Tenminute bound02:52:02→03:02:02UTC, completionrecordedreport. No neckclearance/bend, isolatedhoodtopology, gameplay/contact/rigpass. Parentjudges. RetiredH21-04hoodrepairlineage notused.
''')
fs={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()};(OUT/'freeze-manifest.json').write_text(json.dumps({'freezeUTC':r['freezeUTC'],'sourceHashesUnchanged':True,'files':fs,'recipeSHA256':{p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('correct_raw_hood_display01.py')]}},indent=2)+'\n');print(r['freezeUTC'])
