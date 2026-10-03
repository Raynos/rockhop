from pathlib import Path
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;src=HERE/'source-sleeve-tube-rest11-oblique.npz';f=dict(np.load(src));report=[]
for sg,side in [(1,'L'),(-1,'R')]:
 rows=f['tubeRows'+side];cap=f['tr0'][f['bodyCapFaceIDs'+side]];q=f['p0'][cap];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);nn=np.zeros_like(f['p0']);
 for j in range(3):np.add.at(nn,cap[:,j],fn)
 n=nn[rows[0]];n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30);slope=0 if sg==1 else .2;assert (sg*(n[:,2]-slope*n[:,1])>0).all(),('actual chart outward normal',side);oldrow=f['p0'][rows[1]].copy();f['p0'][rows[1]]=f['p0'][rows[0]]+.020*n;f['tubeRestRows'+side]=f['p0'][rows].copy();f['sewnCollarNormals'+side]=n;report.append({'side':side,'collarLengthM':.020,'minimumChartOutwardNormal':float((sg*(n[:,2]-slope*n[:,1])).min()),'worldOutwardZNegativeRows':int((n[:,2]*sg<=0).sum()),'maxCollarChangeFrom11M':float(np.linalg.norm(f['p0'][rows[1]]-oldrow,axis=1).max())})
for pi in range(5):
 q=f[f'p{pi}'][f[f'tr{pi}']];f[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
out=HERE/'source-sleeve-tube-rest12-collar.npz';np.savez_compressed(out,**f);r={'status':'UNACCEPTED SEWN-COLLAR CONSTRUCTION; rest/UV/shading/render pending','candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'method':'11enlarged oblique loop fits, but first tube row pierces actual cap. A20mm local material collar follows each sewn cap boundary vertex actual area-weighted cap-only geometric normal; no worldheight shift. Subsequent rows stayRMF/loose source ring, exact bodyopening/source loop/head/cuffs held. This matches the local surface derivative rather than assuming global ring-plane normal.','rows':report};(HERE/'source-sleeve-tube-rest12-collar-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
