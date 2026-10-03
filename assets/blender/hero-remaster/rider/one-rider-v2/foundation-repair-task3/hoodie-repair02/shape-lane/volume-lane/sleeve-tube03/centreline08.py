from pathlib import Path
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;src=HERE/'source-sleeve-tube-rest07-uvchart.npz';f=dict(np.load(src));old=np.load(src);report=[]
for sg,side in [(1,'L'),(-1,'R')]:
 rows=f['tubeRows'+side];C=f['curveControlRest'+side].copy();C[1,2]-=sg*.055;C[2,2]-=sg*.020;delta=C-old['curveControlRest'+side];s=np.linspace(0,1,len(rows));d=3*(1-s[:,None])**2*s[:,None]*delta[1]+3*(1-s[:,None])*s[:,None]**2*delta[2];d[1]=0;d[2]*=.5
 for r in range(1,len(rows)-1):f['p0'][rows[r]]+=d[r]
 # All explicit UV aliases are physical duplicates, including seam column.
 grid=f['tubeUVRows'+side];f['p0'][grid[:,-1]]=f['p0'][grid[:,0]];f['curveControlRest'+side]=C;f['tubeRestRows'+side]=f['p0'][rows].copy();report.append({'side':side,'upperOutgoingControlInwardM':.055,'lowerIncomingControlInwardM':.020,'maximumInteriorTranslationM':float(np.linalg.norm(d,axis=1).max()),'protectedRootCollarAndEndpointExact':bool(np.array_equal(f['p0'][rows[[0,1,-1]]],old['p0'][rows[[0,1,-1]]]))})
for side in ['L','R']:
 rows=f['tubeRows'+side];t=f['tr0'][f['newTubeFaceIDs'+side]];q=f['p0'][t];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);nn=np.zeros((int(f['physicalWeld0'].max())+1,3));w=f['physicalWeld0'];
 for j in range(3):np.add.at(nn,w[t[:,j]],fn)
 ids=rows[2:-1].ravel();n=nn[w[ids]];n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30);f['n0'][ids]=n;f['n0'][f['tubeUVRows'+side][:,-1]]=f['n0'][rows[:,0]]
for pi in range(5):
 q=f[f'p{pi}'][f[f'tr{pi}']];f[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
out=HERE/'source-sleeve-tube-rest08-centreline.npz';np.savez_compressed(out,**f);r={'status':'UNACCEPTED STANDING CONSTRUCTION; source-shaped07 visually retains underarm gaps','parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'method':'Bring overly lateral analytical upper curve toward source arm axis: shorten85mm outward control to30mm, move lower incoming control20mm inward. Preserve validated sewn collar row0/1 and endpoints, halfshiftrow2, translate source-shaped interior row cross sections without radial shrink. Fullliteral rest and standing silhouette required. Existing sourceface ray ancestry labels donor shape before declared row translation.','rows':report,'UVWeightsTopologyPhysicalWeldExact':all(np.array_equal(f[k],old[k])for k in ['uv0','W0','tr0','physicalWeld0'])};(HERE/'source-sleeve-tube-rest08-centreline-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
