"""Read-only containment diagnosis after failed trial03; no repaired geometry."""
from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume');src=ROOT/'trial02';run=ROOT/'trial03';out=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/B-local-volume/trial03');out.mkdir(exist_ok=True)
l=json.loads((src/'exact-three-loops.json').read_text());outer=np.array(l[0]['coordinatesMetres']);h=np.load(src/'head-source.npz');hv=h['vertices'];hf=h['faces']
def section(z):
 p=[]
 for tri in hv[hf]:
  for a,b in zip(tri,np.roll(tri,-1,axis=0)):
   if (a[2]<z)!=(b[2]<z):p.append(a+(z-a[2])/(b[2]-a[2])*(b-a))
 q=np.unique(np.round(p,6),axis=0);cen=np.median(q[:,:2],axis=0);q=q[np.argsort(np.arctan2(q[:,1]-cen[1],q[:,0]-cen[0]))];rad=q[:,:2]-cen;inner=q.copy();inner[:,:2]+=rad/np.maximum(np.linalg.norm(rad,axis=1)[:,None],1e-12)*.005;return q,inner

def outside(pts,poly):
 inside=np.zeros(len(pts),bool)
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  if abs(b[1]-a[1])<1e-14:continue
  cross=(a[1]>pts[:,1])!=(b[1]>pts[:,1]);xx=(b[0]-a[0])*(pts[:,1]-a[1])/(b[1]-a[1])+a[0];inside^=cross&(pts[:,0]<xx)
 return ~inside
rows=[]
for z in [1.49,1.505,1.515,1.53,1.545,1.56,1.575]:
 q,inner=section(z);rows.append(dict(z=z,sectionBounds=[q.min(0).tolist(),q.max(0).tolist()],sectionSamples=len(q),clearanceOutsideFraction=float(np.mean(outside(inner[:,:2],outer[:,:2])))))
q,inner=section(1.515);bad=outside(inner[:,:2],outer[:,:2]);np.savez(run/'failed-projection-measurement.npz',sourceHoodLoop=outer,skinSection=q,clearanceSection=inner,outside=bad)
report={'status':'Read-only failed containment diagnosis, no parameter or repaired mesh experiment','failedSectionZ':1.515,'failedOutsideFractionIndependentScalarCheck':float(bad.mean()),'sectionScanPurpose':'Anatomical cross-section measurement only; not generation sweeps','sections':rows,'sourceSkinUnchanged':True,'noConstructedVolume':True};(run/'projection-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');(out/'projection-diagnosis.json').write_bytes((run/'projection-diagnosis.json').read_bytes())
im=Image.new('RGB',(800,780),'#20252b');d=ImageDraw.Draw(im)
def px(q):return (400+q[0]*2100,400-q[1]*2100)
for x,col in zip(l,['#65d98b','#63adff','#b682ff']):
 pts=[px(p) for p in x['coordinatesMetres']];d.line(pts+[pts[0]],fill=col,width=4)
d.line([px(p) for p in q]+[px(q[0])],fill='#eeeeee',width=3);d.line([px(p) for p in inner]+[px(inner[0])],fill='#ffbf69',width=3)
for p,b in zip(inner,bad):
 if b:x,y=px(p);d.ellipse((x-4,y-4,x+4,y+4),fill='#ff665e')
for y,text in enumerate(['FAILED trial03: actual projected hood seams / fixed native skin','Green:194-edge neck cloth opening; Blue/Purple:43/23-edge holes','White: native skin cross-section at Z1.515; Orange:+5mm clearance','Red: outside retained garment footprint. No volume constructed.']):d.text((25,22+y*25),text,fill='white')
d.text((25,735),'Plan view in metres; coordinates from preserved source meshes, not a mockup.',fill='white');im.save(out/'failed-projection-plan.png')
print(json.dumps(report))
