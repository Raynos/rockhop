from pathlib import Path
import numpy as np,json,hashlib

def normalize(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-30)
def rotate_between(a,b):
 v=np.cross(a,b);d=float(np.clip(a@b,-1,1));s=np.linalg.norm(v)
 if s<1e-10:return np.eye(3)
 K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]);return np.eye(3)+K+K@K*((1-d)/(s*s))
def arc_frames(start,end,side,N=13):
 sg=1 if side=='L'else-1;R=sg*(end[2]-start[2]);assert R>.01;arc=R*np.pi/2;straight=start[1]-R-end[1];assert straight>0;length=arc+straight;l=np.linspace(0,length,N);centres=[];tangents=[]
 for d in l:
  if d<=arc:
   theta=d/R;phase=d/arc;blend=phase*phase*(3-2*phase);x=start[0]+blend*(end[0]-start[0]);dx=(6*phase*(1-phase)/arc)*(end[0]-start[0]);centres.append([x,start[1]-R*(1-np.cos(theta)),start[2]+sg*R*np.sin(theta)]);tangents.append(normalize(np.array([dx,-np.sin(theta),sg*np.cos(theta)])))
  else:centres.append([end[0],start[1]-R-(d-arc),end[2]]);tangents.append(np.array([0.,-1.,0.]))
 tangents=np.array(tangents);e=np.array([1.,0,0]);frames=[]
 for i,T in enumerate(tangents):
  if i:e=rotate_between(tangents[i-1],T)@e
  e=normalize(e-T*(e@T));frames.append(np.c_[e,np.cross(T,e),T])
 centres=np.array(centres);centres[0]=start;centres[-1]=end;return centres,np.array(frames),{'arcRadiusM':float(R),'arcLengthM':float(arc),'straightLengthM':float(straight),'totalLengthM':float(length),'XTranslationM':float(end[0]-start[0])}

if __name__=='__main__':
 from responding_surface import curve_frames
 HERE=Path(__file__).resolve().parent;src=HERE/'source-sleeve-tube-rest16-loft.npz';f=dict(np.load(src));old=np.load(src);report=[]
 for side in ['L','R']:
  rows=f['tubeRows'+side];curveRows=rows[1:];C=f['curveControlRest'+side];cc0,M0=curve_frames(C,len(curveRows));local=np.einsum('rij,rnj->rni',M0.transpose(0,2,1),old['p0'][curveRows]-cc0[:,None]);start=old['p0'][curveRows[0]].mean(0);end=old['p0'][curveRows[-1]].mean(0);cc,M,info=arc_frames(start,end,side,len(curveRows));newq=cc[:,None]+np.einsum('rij,rnj->rni',M,local);newq[0]=old['p0'][curveRows[0]];newq[-1]=old['p0'][curveRows[-1]];f['p0'][curveRows]=newq;f['tubeRestRows'+side]=f['p0'][rows].copy();f['materialCurveCentresRest'+side]=cc;f['materialCurveFramesRest'+side]=M;f['materialCurveKind'+side]=np.array('quarter-circle-plus-straight');profile=np.linalg.norm(local[0,:,:2],axis=1).max();axial=abs(local[0,:,2]).max();info.update({'side':side,'rootRadialMaximumM':float(profile),'rootAxialResidualMaximumM':float(axial),'radiusMinusRootProfileM':float(info['arcRadiusM']-profile),'rootAndSourceEndExact':bool(np.array_equal(f['p0'][rows[[0,1,-1]]],old['p0'][rows[[0,1,-1]]]))});report.append(info)
 # Newtube geometric normals only; originalprefix and cap normals held.
 for side in ['L','R']:
  rows=f['tubeRows'+side];t=f['tr0'][f['newTubeFaceIDs'+side]];q=f['p0'][t];fn=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);nn=np.zeros_like(f['p0']);
  for j in range(3):np.add.at(nn,t[:,j],fn)
  ids=rows[1:-1].ravel();f['n0'][ids]=normalize(nn[ids])
 for pi in range(5):
  q=f[f'p{pi}'][f[f'tr{pi}']];f[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
 out=HERE/'source-sleeve-tube-rest17-arc.npz';np.savez_compressed(out,**f);r={'status':'UNACCEPTED QUARTERCIRCLE+STRAIGHT CONSTRUCTION; literalrest/UV/N pending','parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'method':'Analyticalquarter-circle from actual chartcollar endpoint to retained source-ring lateral coordinate, then straightvertical run.13RMFmaterial stations at uniform arclength retain sourceprofile locals/axialresiduals, root/collar/end fixed. Replaces16cubic radius deficit, no parametersearch/poseatlas. Radius-minus-section margin is diagnostic, strict alltriangle gate decisive.','rows':report};(HERE/'source-sleeve-tube-rest17-arc-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
