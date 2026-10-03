from pathlib import Path
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;base=np.load(HERE/'source-sleeve-tube-rest04-normal.npz');src=HERE/'source-sleeve-tube-rest05-envelope.npz';f=dict(np.load(src));changes=[]
for side in ['L','R']:
 rows=f['tubeRows'+side];ids=rows[1];f['p0'][ids]=base['p0'][ids];f['n0'][ids]=base['n0'][ids];ids=rows[2];f['p0'][ids]=base['p0'][ids]+.5*(f['p0'][ids]-base['p0'][ids]);f['tubeRestRows'+side]=f['p0'][rows].copy();changes.append({'side':side,'unmodifiedRootCollarRows':[0,1],'halfEnvelopeBlendRow':2,'fullSourceEnvelopeRows':[3,10],'endpointExact':bool(np.array_equal(f['p0'][rows[[0,1,-1]]],base['p0'][rows[[0,1,-1]]]))})
# Source and exact sewn seam normal rows remain04; geometric interior normal.
for side in ['L','R']:
 rows=f['tubeRows'+side];t=f['tr0'][f['newTubeFaceIDs'+side]];q=f['p0'][t];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);nn=np.zeros_like(f['p0']);
 for j in range(3):np.add.at(nn,t[:,j],fn)
 ids=rows[2:-1].ravel();nn=nn[ids];nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-30);f['n0'][ids]=nn
for pi in range(5):
 q=f[f'p{pi}'][f[f'tr{pi}']];f[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
out=HERE/'source-sleeve-tube-rest06-envelope.npz';np.savez_compressed(out,**f);r={'status':'UNACCEPTED SOURCE-SHAPED STANDING CLONE; fullrest/render pending','parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'method':'Source-envelope05 exposed6 collar/cap crosses exclusively on first tube row. Retain validated neutral root rows0/1, halfsource displacement row2, fullbounded source envelope elsewhere. Source atlas/UV/W/sourceprefix/physicalweld/endpoint/head unchanged. This is an explicit clearance collar, not accepted envelope/pose response.','rows':changes};(HERE/'source-sleeve-tube-rest06-envelope-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
