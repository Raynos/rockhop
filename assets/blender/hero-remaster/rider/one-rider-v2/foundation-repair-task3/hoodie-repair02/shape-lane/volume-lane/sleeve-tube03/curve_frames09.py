from pathlib import Path
import numpy as np,json,hashlib
from responding_surface import curve_frames
HERE=Path(__file__).resolve().parent;src=HERE/'source-sleeve-tube-rest07-uvchart.npz';f=dict(np.load(src));old=np.load(src);report=[]
for sg,side in [(1,'L'),(-1,'R')]:
 rows=f['tubeRows'+side];C=f['curveControlRest'+side].copy();cc0,M0=curve_frames(C,len(rows));local=np.einsum('rij,rnj->rni',M0.transpose(0,2,1),f['p0'][rows]-cc0[:,None]);C[1,2]-=sg*.025;C[2,1]=1.285;cc,M=curve_frames(C,len(rows));proposed=cc[:,None]+np.einsum('rij,rnj->rni',M,local);proposed[0]=old['p0'][rows[0]];proposed[-1]=old['p0'][rows[-1]];f['p0'][rows]=proposed;f['p0'][f['tubeUVRows'+side][:,-1]]=proposed[:,0];f['curveControlRest'+side]=C;f['tubeRestRows'+side]=proposed.copy();report.append({'side':side,'outgoingControlM':.060,'incomingControlY':1.285,'maximumInteriorDeltaM':float(np.linalg.norm(proposed-old['p0'][rows],axis=2).max()),'rootAndEndPositionsExact':bool(np.array_equal(proposed[[0,-1]],old['p0'][rows[[0,-1]]]))})
for side in ['L','R']:
 rows=f['tubeRows'+side];t=f['tr0'][f['newTubeFaceIDs'+side]];q=f['p0'][t];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);w=f['physicalWeld0'];nn=np.zeros((int(w.max())+1,3));
 for j in range(3):np.add.at(nn,w[t[:,j]],fn)
 ids=rows[1:-1].ravel();n=nn[w[ids]];n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30);r=np.repeat(np.linspace(0,1,len(rows))[1:-1],rows.shape[1]);alpha=np.minimum(1,np.minimum(r,1-r)*6);mixed=(1-alpha[:,None])*old['n0'][ids]+alpha[:,None]*n;mixed/=np.maximum(np.linalg.norm(mixed,axis=1)[:,None],1e-30);f['n0'][ids]=mixed;f['n0'][f['tubeUVRows'+side][:,-1]]=f['n0'][rows[:,0]]
for pi in range(5):
 q=f[f'p{pi}'][f[f'tr{pi}']];f[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
out=HERE/'source-sleeve-tube-rest09-rmf.npz';np.savez_compressed(out,**f);r={'status':'UNACCEPTED CURVATURE-AWARE STANDING CLONE; gates pending','parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'method':'Retain source-shaped radial local coordinates but reconstruct row crosssections in rotation-minimizing frames along a less laterally extended, vertically distributed cubic bend. Root/cap and retained sleeve-end ring positions exact. Preserve source geometry/outside/UV/W/topology. Controls change only declared proximal material curve; donor ray ancestry refers before curve remap.','rows':report};(HERE/'source-sleeve-tube-rest09-rmf-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
