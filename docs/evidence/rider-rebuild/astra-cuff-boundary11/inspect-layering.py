"""Read-only garment order check: two declared rays at existing anchor5187 station."""
import numpy as np,json
from pathlib import Path
root=Path('/Users/raynos/projects/games/rockhop');base=root/'harness/out/rider-rebuild/glove-cuff-construction07/inspection01';placement=json.load(open(root/'assets/blender/rider-rebuild/glove-anatomical04/controls-orientation02.json'));out={}
def ray(origin,direction,vertices,faces):
 tri=vertices[faces];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];p=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.sum(e1*p,1);valid=np.abs(det)>1e-15;inv=1/np.where(valid,det,1);s=origin-tri[:,0];u=np.sum(s*p,1)*inv;q=np.cross(s,e1);v=np.sum(direction*q,1)*inv;t=np.sum(e2*q,1)*inv;ids=np.flatnonzero(valid&(u>=0)&(v>=0)&(u+v<=1)&(t>0)&(t<.1));return [{'face':int(i),'radiusMm':float(t[i]*1000)} for i in ids[np.argsort(t[ids])]]
for side in ['L','R']:
 a=np.load(base/f'guide-{side}.npz');l=np.load(root/f'assets/blender/rider-rebuild/glove-anatomical04/local-offsets04-{side}.npz');hood=np.load(base/f'sleeve-{side}.npz');body=np.load(base/f'wearer-{side}.npz');lin=np.array(placement['hands'][side]['initialPlacement']['linear']);trans=np.array(placement['hands'][side]['initialPlacement']['translation']);old=np.sum(l['corrected'][:,None,:]*lin[None,:,:],axis=2)+trans
 axis=a['forearmAxisWorld'];wrist=a['wristWorld'];station=float(np.sum((a['currentWorldXYZ'][5187]-wrist)*axis));origin=wrist+station*axis;d=lin[:,2];d=d-np.sum(d*axis)*axis;d/=np.linalg.norm(d);mask=a['originalSourceXYZ'][:,1]<-.65;delta=np.sum((l['corrected']-a['originalSourceXYZ'])[:,None,:]*lin[None,:,:],axis=2)
 row={'stationDefinition':'current05 lip anchor5187 axial projection along anatomical forearm','stationMm':station*1000,'local04CuffVsSelectedOriginalMaxMm':float(np.linalg.norm(delta[mask],axis=1).max()*1000),'local04NewCuffOffsetCount':int(np.count_nonzero(np.linalg.norm(l['offsets'][mask],axis=1)>0)),'rays':{}}
 for label,direction in [('dorsal',d),('palm',-d)]:
  row['rays'][label]={name:ray(origin,direction,vs,fs) for name,vs,fs in [('wearer',body['worldXYZ'],body['faces']),('hoodie',hood['worldXYZ'],hood['faces']),('glove04',old,a['faces']),('glove05',a['currentWorldXYZ'],a['faces'])]}
 out[side]=row
out['limits']=['Only two declared radial rays per hand, at one existing anchor station; not an enclosure or clearance qualification.','Small source/control guide for glove versus actual current sleeve/wearer crop.','Local04 is prior fitted source, not undeformed original. No geometry edit or candidate generation.']
Path('/tmp/astra-cuff-boundary11-layering.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
