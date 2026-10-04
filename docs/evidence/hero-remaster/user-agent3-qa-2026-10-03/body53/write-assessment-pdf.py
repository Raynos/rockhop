"""Create a report from existing measured fields and played movie extracts."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
from reportlab import rl_config
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,Color,white
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
root=Path.cwd();out=Path(__file__).resolve().parent;tmp=out/'tmp/pdfs';pdf=out/'whole-body-assessment.pdf'
r=json.loads((out/'assessment.json').read_text());local=json.loads((out/'local-witnesses.json').read_text());pins=json.loads((out.parent/'body52/source.json').read_text());bind=json.loads((out/'bind-and-stream-proof.json').read_text());play=json.loads((out/'playback.json').read_text());checks=json.loads((out/'witness-check.json').read_text())
tmp.mkdir(parents=True,exist_ok=True)
if not (tmp/'native-01.png').exists():
 subprocess.run(['ffmpeg','-v','error','-i',str(root/play['results'][0]['path']),'-vf','select=eq(n\\,24)+eq(n\\,60),scale=960:576','-vsync','0','-frames:v','2',str(tmp/'native-%02d.png')],check=True)
if not (tmp/'actual50.png').exists():
 subprocess.run(['ffmpeg','-v','error','-ss','3','-i',str(root/play['results'][1]['path']),'-frames:v','1','-vf','scale=960:360',str(tmp/'actual50.png')],check=True)
assert len(play['results'])==2 and all(x['audioContexts']==0 for x in play['results'])
BLUE=HexColor('#1D5E7A');ORANGE=HexColor('#C45C29');INK=HexColor('#172A35');GRAY=HexColor('#536773');LIGHT=HexColor('#EAF0F3');FONT='Helvetica'
rl_config.useA85=0
c=canvas.Canvas(str(pdf),pagesize=(612,792),pageCompression=1);c.setTitle('Rockhop frozen rider: whole-body assessment');c.setAuthor('Agent 3 / Codex gpt-6.1-sol');page=0
style=ParagraphStyle('body',fontName=FONT,fontSize=10,leading=14,textColor=INK,spaceAfter=0)
def para(text,x,y,width=516,size=10,color=INK):
 st=ParagraphStyle('p',parent=style,fontSize=size,leading=size*1.35,textColor=color);p=Paragraph(text,st);w,h=p.wrap(width,720);p.drawOn(c,x,y-h);return y-h

def title(label,subtitle):
 global page;page+=1;c.setFillColor(BLUE);c.rect(0,775,612,17,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Helvetica-Bold',22);c.drawString(48,738,label);para(subtitle,48,719,size=10,color=GRAY)
 c.setFont(FONT,8);c.setFillColor(GRAY);c.drawString(48,27,'2026-10-04  |  Frozen evidence only  |  All M0-M5 open');c.drawRightString(564,27,f'{page} / 4')
def section(label,y):
 c.setFillColor(BLUE);c.setFont('Helvetica-Bold',12);c.drawString(48,y,label);return y-14

def table(headers,rows,y,widths,size=9):
 st=ParagraphStyle('cell',parent=style,fontSize=size,leading=size*1.35)
 heights=[max(30,max(Paragraph(str(value),st).wrap(width-14,720)[1] for width,value in zip(widths,row))+14) for row in [headers,*rows]]
 for ri,row in enumerate([headers,*rows]):
  h=heights[ri];c.setFillColor(BLUE if ri==0 else LIGHT if ri%2 else white);c.rect(48,y-h,sum(widths),h,fill=1,stroke=0);x=48
  for width,text in zip(widths,row):para(str(text),x+7,y-7,width-14,size,white if ri==0 else INK);x+=width
  y-=h
 return y

def graph(domain,x,y,width,height,xlabel):
 rows=[v for v in r['records'] if v['domain']==domain];peak=max(v['strictCrossingPairs'] for v in rows);last=max(v['frame'] for v in rows);c.setStrokeColor(GRAY);c.setLineWidth(.6);c.line(x,y,x+width,y);c.line(x,y,x,y+height)
 for value in [0,peak//2,peak]:
  yy=y+height*value/peak;c.setStrokeColor(LIGHT);c.line(x,yy,x+width,yy);c.setFont(FONT,8);c.setFillColor(GRAY);c.drawRightString(x-6,yy-3,str(value))
 p=c.beginPath()
 for i,row in enumerate(rows):
  xx=x+width*row['frame']/last;yy=y+height*row['strictCrossingPairs']/peak
  (p.moveTo if i==0 else p.lineTo)(xx,yy)
 c.setStrokeColor(BLUE);c.setLineWidth(1.25);c.drawPath(p)
 c.setFont(FONT,8);c.setFillColor(GRAY);c.drawString(x,y-15,'0');c.drawRightString(x+width,y-15,xlabel);c.drawString(x,y+height+9,f'{domain}: strict finite crossing pairs')

def triangles(row,x,y,width,height):
 a=np.array(row['XYZ_A']);b=np.array(row['XYZ_B']);points=np.concatenate([a,b]);center=points.mean(0);rotation=np.array([[.7071,0,-.7071],[-.4082,.8165,-.4082]]);pa=(a-center)@rotation.T*1000;pb=(b-center)@rotation.T*1000;combined=np.concatenate([pa,pb]);span=np.ptp(combined,axis=0);scale=min((width-20)/max(span[0],.1),(height-20)/max(span[1],.1));middle=(combined.min(0)+combined.max(0))/2
 for points,color in [(pa,BLUE),(pb,ORANGE)]:
  points=(points-middle)*scale+[x+width/2,y+height/2];path=c.beginPath();path.moveTo(*points[0]);[path.lineTo(*q) for q in points[1:]];path.close();c.setFillColor(Color(color.red,color.green,color.blue,alpha=.2));c.setStrokeColor(color);c.setLineWidth(1.4);c.drawPath(path,fill=1,stroke=1)
 c.setFont(FONT,8);c.setFillColor(GRAY);c.drawString(x,y-9,'Isometric projection of existing numeric witness')

title('Retain the body; investigate local repairs','Whole-body QA recommendation. This is an unaccepted finding, not asset or player approval.')
y=para('<b>Retain the frozen 13,380-vertex fitting body as the anatomical base.</b> Its rest surface is closed, connected and consistently wound. Motion produces shoulder, hip and knee folds in both full-native and normalized-four fields. The evidence supports a bounded local deformation investigation before any body replacement.',48,684)
y=section('What the measurements distinguish',y-25)
y=table(['Domain','Finding / disposition'],[
 ['Rest topology','One component; 26,756 triangles; Euler 2. No boundary, non-manifold edge, inconsistent edge winding, zero-area face or detected non-adjacent self-contact.'],
 ['Pose / weights','Synthetic peak: 220 strict pairs. Actual47 peak: 414. Finite contact totals match at every pose. Strict counts differ by two at one tick; a fifth slot alone cannot resolve these folds.'],
 ['Export consumption','Appearance10 diagnostic body maps all 9,037 native vertices and 18,016 oriented triangles. Primary-four field matches existing native-four stream within 0.669 micrometre.'],
 ['Protected head','Assess separately. Native head seams join virtually to one component / six boundary loops. Neck interface overlap is deliberate; actual native head skin also develops self-crossings. Head oriented export ancestry remains unproven.'],
 ['Visual decision','Existing continuous films are dressed. Exposed shoulder/hip quality, target garment19 export, facial behavior and physical iOS remain unreviewed. Parent judges art.']
],y,[112,404],9)
y=section('Shoulder and hip proxies',y-26)
y=para('Rest spheres have radius 145.8 mm (8% of 1.82257 m figure height), centered on upper-arm and thigh bone heads. These overlap nearby torso surfaces; they are not anatomical segmentation.',48,y,size=9)
y=table(['Region','Synthetic strict peak','Actual47 strict peak','Four-slot loss maximum'],[['Shoulder L / R','22 / 22','69 / 69','0.261 mm synthetic / 0.357 mm actual'],['Hip L / R','35 / 40','49 / 53','0.000137 mm synthetic / 0.00000455 mm actual']],y-12,[110,105,105,196],8)
c.showPage()

title('Contacts arise under motion','Counts are sampled finite triangle crossings; they are not penetration depth or visible severity.')
graph('syntheticFour',80,499,450,140,'529 samples / 11 s');graph('actual47Four',80,287,450,140,'703 input ticks / 5.858 s')
para('Synthetic Full and Four: 274 / 529 samples have strict crossings, with a 220-pair peak at frame 240 (5.0 s). Full/four maxima differ by 7.811 mm at native vertex 931 near the shoulder-neck blend. Actual47 full/four maximum is 6.012 mm. At actual input 478, both fields have 223 finite contacts; strict counts are Full 221 / Four 223. Regional strict counts match at every native/actual47 sample.',48,257,size=9)
left=next(v for v in local['witnesses'] if v['domain']=='actual47Four' and v['region']=='shoulder.L');right=next(v for v in local['witnesses'] if v['domain']=='actual47Four' and v['region']=='hip.L')
triangles(left,55,82,235,104);triangles(right,322,82,235,104)
para(f"<b>Shoulder L, input {left['frameOrInputTick']}</b><br/>Triangles {left['triangleA']} / {left['triangleB']}; chest / upper arm. Strict plane endpoint excursion: 15.105 mm.",55,67,235,8)
para(f"<b>Hip L, input {right['frameOrInputTick']}</b><br/>Triangles {right['triangleA']} / {right['triangleB']}; thigh / pelvis. Strict plane endpoint excursion: 12.750 mm.",322,67,235,8)
c.showPage()

title('Played evidence has a visibility limit','Existing movies replayed silently in headless WebKit; these are extracts, not new posed captures.')
c.drawImage(str(tmp/'native-01.png'),66,407,width=480,height=288)
para('<b>Native stream, 2.0 s / frame 96</b> - TOP original full-native weights; BOTTOM normalized four. Four yaw columns. Existing shirt and jeans conceal the exposed body surface.',48,397,size=9)
c.drawImage(str(tmp/'native-02.png'),66,70,width=480,height=288)
para('<b>Native stream, 5.0 s / frame 240</b> - Existing backward-seated FK endpoint, within an uninterrupted forward/reverse movie. This visual evidence does not prove naked shoulder or hip clearance.',48,60,size=8)
c.showPage()

title('Provenance and remaining coverage','No body/head/rig/weights were edited. No new scene capture, export, installation or model job ran.')
c.drawImage(str(tmp/'actual50.png'),48,475,width=516,height=193.5)
y=para('<b>Separate actual50 OFF / ON film, 3.0 s.</b> Its 176 existing OFF bone-world samples also show a 414-pair body peak. Actual47 and actual50 poses differ (matrix component gap 0.293341); shared body attributes and inverse binds are byte-exact. Do not pair film50 frames with numeric47 witnesses. Cause is not established.',48,463,size=9)
y=section('Method and scope',y-21)
y=para('Canonical rest: identity pose basis on all 51 native bones; no action/NLA; default zero shape values. File-world glTF metres: +X forward, +Y up, +Z left. Blender +X / +Z / -Y converts once; X+0.65 is baked once. GLTFLoader uses identity bind; attached mesh-world cancellation prevents a second translation.',48,y,size=8)
y=para('CPU BVH broadphase; normalized finite triangle SAT epsilon 1e-9 m. Vertex-sharing adjacency excluded. Strict crossing requires >2 micrometre opposite endpoint distances and interior barycentrics >1e-6. Fixed rest tessellation. 32 analytic checks and 36,632 independent JS witness checks pass. No degenerate candidate pair was treated as clear. Head uses native fields; complete oriented head export ancestry is not proven.',48,y-7,size=8)
y=para('Coverage: native 529 samples / 48 Hz / 11 s, plus existing actual47 703 ticks / 120 Hz / 5.858 s and separate actual50 176 samples. One Rookie backward-lean window; no arbitrary pose, full 86-bank, Pro, landing, face, stranger or physical-device clearance. 68 strict head/body rest-interface overlaps are separate from body self-contact. Existing underwear is a fitting control; no fresh exposed-body film was generated.',48,y-7,size=8)
y=section('Exact source hashes (full registry: body52/source.json)',y-19)
source_suffixes=[('Native19 profile-fit.blend','selected-hoodie19/profile-fit.blend'),('Existing appearance10 GLB','appearance10/rider-source-normals.glb'),('Appearance10 controller','appearance10/source-normals-controller.json'),('Native pose driver','diagnostic02/driver.json'),('Native full stream','diagnostic02/body-native-full.f64'),('Native four stream','diagnostic02/body-native-four.f64')]
for label,suffix in source_suffixes:
 pin=next(v for k,v in pins['pins'].items() if k.endswith(suffix));y=para(label,48,y,size=7.5);c.setFont('Courier',7);c.setFillColor(INK);c.drawString(48,y-10,pin['sha256']);y-=24
c.showPage();c.save()
assert b'\0' in pdf.read_bytes(),'PDF must retain binary compressed streams for Git binary detection'
print(json.dumps({'PDF':str(pdf.relative_to(root)),'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'pages':page}))
