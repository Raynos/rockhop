"""Whole-body report addition with locally embedded fonts; old PDF untouched."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from PIL import Image
from reportlab import rl_config
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor,white
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
root=Path.cwd();out=Path(__file__).resolve().parent;qa=out.parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();r=json.loads((qa/'body53/assessment.json').read_text());f=json.loads((qa/'body53/finding.json').read_text());prep=json.loads((qa/'body55/preparation.json').read_text());obs=json.loads((out/'visual-observations.json').read_text());play=json.loads((out/'playback.json').read_text());movies={d:json.loads((out/(d+'-movie.json')).read_text()) for d in ['native','actual47']};assert obs['status']=='UNACCEPTED_INDEPENDENT_PLAYED_VISUAL_OBSERVATIONS' and len(play['results'])==2 and not play['errors'];fonts={'Body':Path('/System/Library/Fonts/Supplemental/Arial.ttf'),'BodyBold':Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf'),'Code':Path('/System/Library/Fonts/Supplemental/Courier New.ttf')}
for name,path in fonts.items():pdfmetrics.registerFont(TTFont(name,str(path)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='Body',boldItalic='BodyBold');rl_config.useA85=0;pdf=out/'whole-body-assessment-addition.pdf';c=canvas.Canvas(str(pdf),pagesize=(612,792),pageCompression=1,initialFontName='Body',initialFontSize=10);c.setTitle('Frozen rider whole-body assessment: modest moving evidence');c.setAuthor('Agent3 / Codex gpt-6.1-sol');BLUE=HexColor('#1D5E7A');INK=HexColor('#172A35');GRAY=HexColor('#536773');LIGHT=HexColor('#EAF0F3');style=ParagraphStyle('body',fontName='Body',fontSize=10,leading=14,textColor=INK);page=0;layout=[]

def para(text,x,y,width=516,size=10,color=INK):
 st=ParagraphStyle('p',parent=style,fontSize=size,leading=size*1.35,textColor=color);p=Paragraph(text,st);w,h=p.wrap(width,720);assert y-h>=40,(page,y,h,text);layout.append({'page':page,'x':x,'topY':y,'bottomY':y-h,'width':width,'fontSize':size});p.drawOn(c,x,y-h);return y-h

def title(text,subtitle):
 global page;page+=1;c.setFillColor(BLUE);c.rect(0,775,612,17,fill=1,stroke=0);c.setFillColor(INK);c.setFont('BodyBold',21);c.drawString(48,738,text);para(subtitle,48,718,size=10,color=GRAY);c.setFillColor(GRAY);c.setFont('Body',8);c.drawString(48,27,'2026-10-04 | Frozen source controls preserved | All M0-M5 open');c.drawRightString(564,27,f'{page} / 6')
def section(text,y):c.setFillColor(BLUE);c.setFont('BodyBold',12);c.drawString(48,y,text);return y-14

def table(headers,rows,y,widths,size=9):
 st=ParagraphStyle('cell',parent=style,fontSize=size,leading=size*1.35)
 for i,row in enumerate([headers,*rows]):
  h=max(30,max(Paragraph(str(v),st).wrap(w-14,720)[1] for w,v in zip(widths,row))+14);c.setFillColor(BLUE if i==0 else LIGHT if i%2 else white);c.rect(48,y-h,sum(widths),h,fill=1,stroke=0);x=48
  for width,text in zip(widths,row):para(str(text),x+7,y-7,width-14,size,white if i==0 else INK);x+=width
  y-=h
 return y

def graph(domain,x,y,width,height,xlabel):
 rows=[v for v in r['records'] if v['domain']==domain];peak=max(v['strictCrossingPairs'] for v in rows);last=max(v['frame'] for v in rows);c.setStrokeColor(GRAY);c.setLineWidth(.6);c.line(x,y,x+width,y);c.line(x,y,x,y+height)
 for value in [0,peak//2,peak]:
  yy=y+height*value/peak;c.setStrokeColor(LIGHT);c.line(x,yy,x+width,yy);c.setFont('Body',8);c.setFillColor(GRAY);c.drawRightString(x-6,yy-3,str(value))
 p=c.beginPath()
 for i,row in enumerate(rows):
  xx=x+width*row['frame']/last;yy=y+height*row['strictCrossingPairs']/peak;(p.moveTo if i==0 else p.lineTo)(xx,yy)
 c.setStrokeColor(BLUE);c.setLineWidth(1.25);c.setLineJoin(1);c.drawPath(p);c.setLineJoin(0);c.setFont('Body',8);c.setFillColor(GRAY);c.drawString(x,y-15,'0');c.drawRightString(x+width,y-15,xlabel);c.drawString(x,y+height+9,domain+': strict finite crossing pairs')

def played_image(key,x,y,width,height,lower_row=False):
 path=out/'played'/obs['playedFrames'][key]['file'];assert sha(path)==obs['playedFrames'][key]['sha256']
 if lower_row:
  image=Image.open(path);assert image.size==(1920,1280);derived=out/'tmp/played'/(key+'-four-row.png');image.crop((0,660,1920,1240)).save(derived);path=derived
 c.drawImage(str(path),x,y,width=width,height=height)

title('Frozen body: retain and test local repairs','Numeric body53 findings retained; new modest moving evidence narrows the visual coverage gap.')
y=para('<b>'+obs['recommendation']+'</b> No repair has been attempted or accepted. These independent observations concern the body surface; parent alone judges candidate art and fit.',48,680)
y=section('Existing body findings remain unchanged',y-23)
y=table(['Domain','Frozen finding / remaining limit'],[
 ['Rest body','13,380 vertices / 26,756 triangles. One closed Euler 2 component; all vertex links manifold cycles; no rest self-contact, non-manifold edge, inconsistent winding or zero-area triangle.'],
 ['Moving body','529 native Full/Four samples: peak 220 strict pairs. 703 actual47 Full/Four samples: peak 414. Finite totals match throughout; strict counts differ by 2 at actual 478 only. Shoulder/hip regional strict counts match.'],
 ['Export / weights','Current diagnostic body maps all 9,037 native vertices and 18,016 oriented triangles. Native-four parity 0.669 micrometre. Shoulder four-slot loss max 0.357mm actual; hip essentially zero. Fifth-slot recovery alone cannot resolve folds.'],
 ['Protected head','Unchanged head/cheek rendered. Head oriented export ancestry remains unproven; rest body/head interface 68 strict overlaps is separate from body self-contact. No face/head repair or garment/head clearance certificate.'],
 ['New visual scope','Front, left side and rear (source-native +X / -Y / -X). Full top / Four bottom; later Four-only shoulder and hip crops. Existing opaque fitting boxers remain; covered hip surfaces still cannot receive a visible-clearance pass.']
],y,[110,406],9)
y=section('Independent played observations',y-24)
for label,text in obs['observations'].items():y=para('<b>'+label+'</b>: '+text,48,y,size=9)-8
c.showPage()

title('Body contacts are pose-dependent','The contact metric and visual severity are separate evidence; counts do not measure penetration depth.')
graph('syntheticFour',80,505,450,140,'529 samples / 11 s');graph('actual47Four',80,300,450,140,'703 input ticks / 5.858 s')
y=para('Native Full/Four: 274/529 samples with strict crossings; peak 220 at frame 240. Actual47: 703/703 samples have strict crossings; peak 414 at input 669. Separate actual50 has 176 existing samples and peak 414, but its poses differ from actual47. That older film is not used for the new visual witnesses.',48,266,size=9)
y=table(['Proxy region','Native peak L/R','Actual47 peak L/R','Selected local witness'],[['Shoulders','22 / 22','69 / 69','Native 72: 2.754mm; actual 668: 15.105mm'],['Hips','35 / 40','49 / 53','Native 242: 3.861mm; actual 512: 12.750mm']],y-12,[104,104,112,196],8)
para('Rest sphere radius 145.8mm around upper-arm / thigh bone heads, an explicit proxy rather than anatomical segmentation. Strict plane endpoint excursion is a finite local crossing witness, not signed closed-volume depth. Body full/four maximum displacement remains 7.811mm native and 6.012mm actual47 near native vertex 931 at the shoulder-neck blend.',48,y-12,size=9)
c.showPage()

title('Native motion: exact exposed-body replay','Synthetic FK source only; no actual-bike support claim. Both full and four fields retain separate labels.')
played_image('native_fullbody',48,514,516,155.875,lower_row=True)
y=para('FOUR-row context from the paired full-body movie. '+obs['playedFrames']['native_fullbody']['caption'],48,503,size=9)
y=section('Matching body53 witness',y-22)
played_image('native_hip',48,73,516,344)
# The lower focus extract contains shoulder/hip views from the same exact sample.
para(obs['playedFrames']['native_hip']['caption'],48,62,size=8)
c.showPage()

title('Actual47: recorded fields, no resimulation','Existing 703-tick matrix stream only; scale/orientation retained, pelvis translation centers the presentation.')
played_image('actual_fullbody',48,514,516,155.875,lower_row=True)
y=para('FOUR-row context from the paired full-body movie. '+obs['playedFrames']['actual_fullbody']['caption'],48,503,size=9)
y=section('Matching shoulder/hip witness',y-22)
played_image('actual_shoulder',48,73,516,344)
para(obs['playedFrames']['actual_shoulder']['caption'],48,62,size=8)
c.showPage()

title('Method, coverage and contact targets','No candidate / whole wearer clearance is inferred from the modest body-only moving control.')
y=section('Direct-field capture contract',680)
y=para('Native body and underwear use existing Float64LE world-position streams. Actual47 body uses exactly the body53 normalized LBS formula on existing 51 effective matrices; no new controller execution. Rendered body is the 9,037-vertex subset of the 13,380 fitting body, joined visually with the unchanged protected head/cheek. All 2,944 saved body53 witnesses at selected sources and all 8 regional anchors match Float64 XYZ exactly.',48,y,size=9)
y=para('The preparation side +Y label is corrected here to source-native -Y (anatomical left); camera transforms and geometry are unchanged. Source 51 rest/pose, live original weights, positions, UV/materials and modifiers are preserved. Disposable triangle presentation meshes apply only glTF-to-native conversion, pelvis translation and yaw 0/90/180; no scale or undo of rider orientation. Source UV/material/smooth flags retained; geometric normals recomputed on presentation copies. CPU Cycles 4 samples / 2 threads per capture; production shader, GPU, LOD and physical-device equivalence are not claimed.',48,y-8,size=9)
y=para('Full top is the original full-weight body reference; Four bottom is normalized primary-four. Protected head stays in its existing primary field in both. Moving cadence is native 12 source frames/s or actual 30 source frames/s, encoded 60fps by exact repeats. Later Four-only focus repeats those samples and holds explicitly labelled exact source witnesses. There is no interpolation, pose injection or extra simulation.',48,y-8,size=9)
y=section('Separate garment target-scope correction',y-22)
y=para('Agent1 checkpoint c3315c61/native92 concerns source 26 garment, not body53 self-contact. Both full/native-four fail peak 959 garment/logical-body and 4095 native-self pairs (4116 frozen-rest tessellation), with 306 body-contact and 460 native-self frames. Full/four garment loss 4.114mm does not explain the identical peaks.',48,y,size=9)
y=para('<b>Protected textured head is a separate target:</b> garment/head 490 pairs at canonical rest, contacts in all 529 samples, peak 504; cheek 0. Earlier source 24 rest 0 body / 0 self audited the logical anatomical body and did not certify textured-head clearance. Pair definitions and tessellation scope differ from body53 finite-SAT body self metrics. New underwear films contain no source 26 garment and cannot pass its fit, appearance or head safety.',48,y-8,size=9)
y=section('Remaining limits',y-22)
para('Opaque boxers cover proximal hip and crotch surfaces; projected triangle guides have untested depth occlusion. Only sampled times and three yaw views are shown. Pro/landing/full 86-bank/facial/device/stranger clearance, successful repair and whole candidate acceptance remain absent. Body/head/bind/weights are unchanged; no source save/export, model/inference/installation/worker job, promotion or publication. All M0-M5 remain open.',48,y,size=9)
c.showPage()

title('Portable report and exact provenance','Local fonts embedded in this addition. Original PDF53 and old dressed films remain historical controls.')
y=section('Movies and full source registry',680)
for domain,m in movies.items():
 y=para('<b>'+domain+'</b>: '+str(m['frames'])+' frames / '+str(round(m['durationS'],6))+'s  / 1920x1280 / 60fps / no audio. '+m['movie'].split('/')[-1],48,y,size=9);c.setFont('Code',7);c.setFillColor(INK);c.drawString(48,y-10,m['sha256']);y-=30
source_rows=[('Native 19 source',next((k,v) for k,v in prep['pins'].items() if k.endswith('profile-fit.blend'))[1]),('Native driver',next((v for k,v in prep['pins'].items() if k.endswith('driver.json')))),('Existing actual47 matrices',next((v for k,v in prep['pins'].items() if k.endswith('first.weights.ndjson.gz')))),('Body53 assessment',sha(qa/'body53/assessment.json')),('Original PDF53, preserved',sha(qa/'body53/whole-body-assessment.pdf')),('Body55 preparation / camera pins',sha(qa/'body55/preparation.json'))]
y=section('Exact hashes',y-12)
for label,value in source_rows:
 y=para(label,48,y,size=8);c.setFont('Code',7);c.setFillColor(INK);c.drawString(48,y-11,value);y-=29
for name,path in fonts.items():y=para('<b>Embedded font '+name+'</b>: '+path.name+' / SHA256 '+sha(path),48,y-7,size=8)
y=section('Root-owned Library writeback guard',y-20)
para('Existing identity libfile_eb03359fe8fc8191b238f6f807e9af8b, expected current version 0, named whole-body-assessment.pdf. Parent handles review, guarded update of the same identity and delivery; Agent3 performs no Library write/upload or user delivery. Preserve previous version history and original local PDF53.',48,y,size=9)
c.showPage();c.save();(out/'pdf-layout.json').write_text(json.dumps({'paragraphBounds':layout,'minimumParagraphBottomY':min(v['bottomY'] for v in layout)},indent=2)+'\n');assert b'\0' in pdf.read_bytes();print(json.dumps({'PDF':str(pdf.relative_to(root)),'sha256':sha(pdf),'pages':page,'embeddedLocalFonts':{n:sha(p) for n,p in fonts.items()}}))
