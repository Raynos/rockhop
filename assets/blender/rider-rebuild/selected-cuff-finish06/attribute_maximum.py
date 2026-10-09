"""Attribute rejected radial maxima to exact local source surfaces."""
import runpy,sys,json
from pathlib import Path
import numpy as np
from mathutils import Vector
D=runpy.run_path(str(Path(__file__).with_name('fit.py')))
root=Path('harness/out/rider-rebuild/selected-cuff-finish06');receipt,comps=D['load'](root/'intake02');h=comps['RiderHoodie'];p=h['POSITION'];f=h['indices'];names=h['names'];rest=np.linalg.inv(h['ib']);ht=D['tree'](p,f)
fit=np.load(root/'fit04/patch.npz');classify,meta=D['load_canonical'](Path.cwd(),names);rows=fit['sourcePositionUniqueRows'][np.argsort(fit['requiredByUniqueRow'])[-8:]];answer=[]
for row in rows:
 side='L' if p[row,0]>0 else 'R';g=comps['ActualSelectedGlove.'+side];head=rest[names.index('DEF-hand.'+side),:3,3];axis=head-rest[names.index('DEF-forearm.'+side+'.001'),:3,3];axis/=np.linalg.norm(axis)
 station=(p[row]-head)@axis;origin=head+station*axis;radial=p[row]-origin;radius=np.linalg.norm(radial);direction=radial/radius;hh=D['hits'](ht,origin,direction,2.,1e-6)
 hood=[dict(radius=t,normalDot=nd,face=int(fi),vertices=f[fi].tolist(),stations=((p[f[fi]]-head)@axis).tolist()) for t,nd,fi in hh if t<=radius+1e-5]
 ownership,*_=classify(g['POSITION'],side);gf=np.flatnonzero(np.any(ownership[g['indices']],axis=1));gt=D['tree'](g['POSITION'],g['indices'][gf]);gh=D['hits'](gt,origin,direction,2.,1e-6)
 gloves=[dict(radius=t,normalDot=nd,face=int(gf[fi]),vertices=g['indices'][gf[fi]].tolist(),stations=((g['POSITION'][g['indices'][gf[fi]]]-head)@axis).tolist()) for t,nd,fi in gh]
 q,n,face,d=gt.find_nearest(Vector(p[row]));answer.append(dict(hoodieRow=int(row),side=side,sourcePosition=p[row].tolist(),station=float(station),sourceRadius=float(radius),hoodieHits=hood,gloveHits=gloves,nearestGloveFace=int(gf[face]),nearestGloveDistance=d,nearestGloveSigned=float((p[row]-np.array(q))@n),fields={names[int(j)]:float(w) for j,w in zip(h['JOINTS_0'][row],h['WEIGHTS_0'][row]) if w>0}))
Path(sys.argv[-1]).write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
