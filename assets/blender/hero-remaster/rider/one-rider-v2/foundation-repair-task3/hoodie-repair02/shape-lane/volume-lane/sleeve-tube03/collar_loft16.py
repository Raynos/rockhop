from pathlib import Path
import numpy as np,json,hashlib
from responding_surface import curve_frames,smooth
HERE=Path(__file__).resolve().parent;src=HERE/'source-sleeve-tube-rest13-natural.npz';f=dict(np.load(src));old=np.load(src);report=[];oldTubeFaces=np.r_[f['newTubeFaceIDsL'],f['newTubeFaceIDsR']];keep=~np.isin(np.arange(len(f['tr0'])),oldTubeFaces)
for key in ['tr0','sourceFaceAncestry0','faceKind0','restDoubleArea0']:f[key]=f[key][keep]
for sg,side in [(1,'L'),(-1,'R')]:
 oldrows=old['tubeRows'+side];slope=0 if sg==1 else .2;direction=np.array([0,-slope*sg,sg],float);direction/=np.linalg.norm(direction);offset=.020*direction;C=old['curveControlRest'+side].copy();cc0,M0=curve_frames(C,len(oldrows));local=np.einsum('rij,rnj->rni',M0.transpose(0,2,1),old['p0'][oldrows]-cc0[:,None]);C[:2]+=offset;cc,M=curve_frames(C,len(oldrows));end=old['p0'][oldrows[-1]];expected=cc[-1]+np.einsum('ij,nj->ni',M[-1],local[-1]);res=np.einsum('ij,nj->ni',M[-1].T,end-expected);blend=smooth(np.linspace(0,1,len(oldrows)));local+=blend[:,None,None]*res;newq=cc[:,None]+np.einsum('rij,rnj->rni',M,local);newq[0]=old['p0'][oldrows[0]]+offset;newq[-1]=end;f['p0'][oldrows[1:-1]]=newq[1:-1];n=len(f['p0']);keys=[k for k,v in f.items()if k.endswith('0')and v.ndim>0 and len(v)==n and k not in ['tr0','sourceFaceAncestry0','faceKind0','restDoubleArea0']];collar=np.arange(n,n+len(oldrows[0]));
 for key in keys:f[key]=np.concatenate([f[key],f[key][oldrows[0]]])
 f['p0'][collar]=newq[0];maxweld=int(max(f['physicalWeld0'].max(),f['physicalWeld2'].max()));f['physicalWeld0'][collar]=np.arange(maxweld+1,maxweld+1+len(collar));f['oldVertex0'][collar]=-1;f['sourceUniqueVertex0'][collar]=-1;f['sourceVertexParents0'][collar]=-1;f['sourceVertexBarycentric0'][collar]=0;rows=np.r_[oldrows[:1],collar[None],oldrows[1:]];N=rows.shape[1];tt=[]
 for row,nextrow in zip(rows,rows[1:]):
  for j in range(N):k=(j+1)%N;tt.extend([[row[j],row[k],nextrow[j]],[row[k],nextrow[k],nextrow[j]]])
 start=len(f['tr0']);f['tr0']=np.r_[f['tr0'],np.array(tt)];f['sourceFaceAncestry0']=np.r_[f['sourceFaceAncestry0'],np.full(len(tt),-1)];f['faceKind0']=np.r_[f['faceKind0'],np.full(len(tt),'new-tube-'+side)];f['restDoubleArea0']=np.r_[f['restDoubleArea0'],np.zeros(len(tt))];f['newTubeFaceIDs'+side]=np.arange(start,start+len(tt));f['tubeRows'+side]=rows;f['tubeRestRows'+side]=f['p0'][rows].copy();f['curveControlRest'+side]=C;f['curveStartTubeRow'+side]=np.array(1);f['collarDepthDirectionRest'+side]=direction;f['collarLength'+side]=np.array(.020);report.append({'side':side,'addedCollarRowVertices':N,'addedFacesVs13':2*N,'materialCurveStartsAfterCollar':True,'collarLengthM':.020,'retainedSourceEndRingExact':bool(np.array_equal(f['p0'][rows[-1]],old['p0'][oldrows[-1]]))})
for side in ['L','R']:f['bodyCapFaceIDs'+side]=np.flatnonzero(f['faceKind0']=='body-cap-'+side)
# New-only geometric normal baseline, source prefixes remain exact.
for pi in [0,2]:
 p=f[f'p{pi}'];t=f[f'tr{pi}'];q=p[t];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);n=np.zeros_like(p)
 for j in range(3):np.add.at(n,t[:,j],fn)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30);sourceCount=22240 if pi==0 else 3112;f[f'n{pi}'][sourceCount:]=n[sourceCount:]
for pi in range(5):
 q=f[f'p{pi}'][f[f'tr{pi}']];f[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
out=HERE/'source-sleeve-tube-rest16-loft.npz';np.savez_compressed(out,**f);r={'status':'UNACCEPTED COHERENT COLLAR+SLEEVE LOFT; allrest/UV/sourceN pending','parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'method':'Explicit20mm chart-depth sewn collar followed by independent smoothRMF sleeve curve startingat collar endpoint. Insertone newrow; translate curve start/outgoingcontrol bycollardepth, preserve source-derived profile locals and exact cuff-connected retained ring. Removes15return intooldring2; geometric construction, no motion/weightfit.','rows':report};(HERE/'source-sleeve-tube-rest16-loft-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
