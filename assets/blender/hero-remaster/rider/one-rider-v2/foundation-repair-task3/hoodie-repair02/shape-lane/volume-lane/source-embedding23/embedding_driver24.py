"""Preferred original surface driven by an unqualified hidden material cage.
Bindings are fixed at rest; no animated nearest-face switches or pose atlas.
"""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
HERE=Path(__file__).resolve().parent;LANE=HERE.parent;CAGE=LANE/'sleeve-tube03';sys.path.insert(0,str(LANE));sys.path.insert(0,str(CAGE));from chart_labels import SourceCharts,POS,NOR,U,INV,OFF,MORPH,unit
from responding_surface22 import RespondingSleeve
from build_embedding import frames
class SourceEmbeddedSleeve:
 def __init__(self,path=None):
  self.path=Path(path or HERE/'original-source-embedded-rest23.npz');self.f=dict(np.load(self.path));self.c=SourceCharts();self.cage=RespondingSleeve(Path(self.f['cagePath'].item()));assert hashlib.sha256(self.cage.path.read_bytes()).hexdigest()==self.f['cageSHA256'].item();self.mapping={};self.lastCage=None
  for side in ['L','R']:
   f=self.f;faces=f['embedCageFaceIDs'+side];lookup=np.full(len(self.cage.f['tr0']),-1,int);lookup[faces]=np.arange(len(faces));slots=lookup[f['embedCageFace'+side]];assert (slots>=0).all();ids=f['embedSourceAliases'+side];aliasToRow=np.full(len(U),-1,int);aliasToRow[ids]=np.arange(len(ids));self.mapping[side]=(faces,slots,aliasToRow)
 def cage_map(self,qc,with_rotation=False):
  result={};rotations={};diagnostics=[]
  for side in ['L','R']:
   f=self.f;faces,slots,_=self.mapping[side];T=qc[0][self.cage.f['tr0'][faces]];F,area=frames(T);idx=f['embedCSR'+side][:-1];b=f['embedBarycentric'+side];w=f['embedWeight'+side];o=f['embedLocalOffset'+side];points=np.einsum('rv,rvk->rk',b,T[slots])+np.einsum('rij,rj->ri',F[slots],o);result[side]=np.add.reduceat(w[:,None]*points,idx,axis=0)
   if with_rotation:
    rest=f['embedCageFramesRest'+side];R=np.einsum('rij,rkj->rik',F[slots],rest[slots]);rotations[side]=np.add.reduceat(w[:,None,None]*R,idx,axis=0)
   diagnostics.append({'side':side,'minimumControlDoubleAreaM2':float(area.min()),'singularControlFacesBelow1e-12':int((area<1e-12).sum())})
  self.lastDiagnostics=diagnostics;return result,rotations
 def deform(self,D,closed=False):
  f=self.f;q=[]
  for pi in range(5):
   p=f[f'p{pi}']+(MORPH[pi] if closed else 0);q.append(np.einsum('vb,bjk,vk->vj',f[f'W{pi}'],D,np.c_[p,np.ones(len(p))])[:,:3])
  qc=self.cage.deform(D,closed);mapped,_=self.cage_map(qc);self.lastCage=qc;self.lastD=D.copy();self.lastClosed=closed
  for side in ['L','R']:
   _,_,lookup=self.mapping[side];alpha=f['embedAlpha'+side]
   for pi in [0,2]:
    u=f[f'physicalWeld{pi}'];select=lookup[u]>=0;row=lookup[u[select]];a=alpha[row];q[pi][select]=(1-a[:,None])*q[pi][select]+a[:,None]*mapped[side][row]
  return q
 def normal_transport(self,D,closed=False):
  if self.lastCage is None or not np.array_equal(D,self.lastD) or closed!=self.lastClosed:self.deform(D,closed)
  _,rot=self.cage_map(self.lastCage,True);f=self.f;n=[]
  for pi in range(5):
   original=f[f'n{pi}'];base=np.einsum('vb,bij,vj->vi',f[f'W{pi}'],D[:,:3,:3],original)
   for side in ['L','R']:
    _,_,lookup=self.mapping[side];u=f[f'physicalWeld{pi}'];select=lookup[u]>=0;row=lookup[u[select]];a=f['embedAlpha'+side][row];mapped=np.einsum('nij,nj->ni',rot[side][row],original[select]);base[select]=(1-a[:,None])*base[select]+a[:,None]*mapped
   n.append(unit(base))
  if np.max(abs(D-np.broadcast_to(np.eye(4),D.shape)))<1e-14:n=[f[f'n{i}'].copy()for i in range(5)]
  return n
if __name__=='__main__':
 driver=SourceEmbeddedSleeve();f=driver.f;D=np.broadcast_to(np.eye(4),(19,4,4)).copy();start=time.perf_counter();q=driver.deform(D);elapsed=time.perf_counter()-start;n=driver.normal_transport(D);delta=max(float(abs(q[i]-f[f'p{i}']).max())for i in range(5));assert delta<1e-10,delta;normal=max(float(abs(n[i]-f[f'n{i}']).max())for i in range(5));assert normal==0
 from scipy.spatial.transform import Rotation
 R=Rotation.from_rotvec([.13,-.21,.08]).as_matrix();t=np.array([.04,-.03,.02]);rigid=D.copy();rigid[:,:3,:3]=R;rigid[:,:3,3]=t;qr=driver.deform(rigid);expected=[np.einsum('ij,nj->ni',R,f[f'p{i}'])+t for i in range(5)];rigidError=max(float(abs(qr[i]-expected[i]).max())for i in range(5));assert rigidError<1e-10,rigidError
 # Every declared old-source boundary, cuff, head and glove receives exact
 # source skinning; only source aliases with alpha>0 are material-driven.
 r={'status':'NEUTRAL_AND_GLOBAL_RIGID_COVARIANCE_ONLY; actual304 pending','candidateSHA256':hashlib.sha256(driver.path.read_bytes()).hexdigest(),'driverSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'maximumNeutralDeltaM':delta,'maximumNeutralNormalDelta':normal,'neutralNormalPolicy':'Original authored NORMAL arrays restored at exactidentity after shader normalization; no new normal sculpting. Animated originals use baseline weightedshader normals outside region and fixed bary-frame material rotations inside.','maximumGlobalRigidCovarianceDeltaM':rigidError,'neutralCPUWallSeconds':elapsed,'sourcePNUVTriangleOriginal':True,'weights':'FrozenV7 source-prefix field, not nativebody11W; no optimization.','remaining':'Exact304 literal/source controls/appearance, offset amplification, mapcontinuity and runtime/mobile cost unqualified. Hidden21/22 cage is already a failed304control. Baseline originalthin-source crossings remain. No productionpromotion.'};(HERE/'embedding-driver24-neutral.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
