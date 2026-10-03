"""Distinct sleeve volume/surface deformation via anatomical centreline and RMF.
Reference rest surface coordinates are transported around a C1 upper/forearm
curve with measured normalized arc length and distributed forearm/wrist roll.
No dynamics, spring shell, height band or pose atlas. Proxy clearance optional.
"""
from pathlib import Path
import sys,json,hashlib,numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent

def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-15)
def transport(n,a,b):
 c=float(np.clip(np.dot(a,b),-1,1));v=np.cross(a,b)
 if c<-.999999:return -n # extreme180degunsupportedbyqualifiedelbowlimits
 k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
 r=np.eye(3)+k+k@k/max(1+c,1e-12);return unit(r@n)
class Curve:
 def __init__(self,centres,startNormal,samples=73):
  p0,p1,p2=np.asarray(centres);m0=p1-p0;m1=(p2-p0)*.5;m2=p2-p1;points=[];tangents=[]
  for j,(a,b,ma,mb)in enumerate([(p0,p1,m0,m1),(p1,p2,m1,m2)]):
   u=np.linspace(0,1,samples);u=u[1:]if j else u
   h00=2*u**3-3*u**2+1;h10=u**3-2*u**2+u;h01=-2*u**3+3*u**2;h11=u**3-u**2
   point=h00[:,None]*a+h10[:,None]*ma+h01[:,None]*b+h11[:,None]*mb
   derivative=(6*u*u-6*u)[:,None]*a+(3*u*u-4*u+1)[:,None]*ma+(-6*u*u+6*u)[:,None]*b+(3*u*u-2*u)[:,None]*mb
   points.extend(point);tangents.extend(unit(derivative))
  self.p=np.array(points);self.t=np.array(tangents);self.s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(self.p,axis=0),axis=1))];self.length=float(self.s[-1]);n=unit(startNormal-self.t[0]*np.dot(startNormal,self.t[0]));normal=[n]
  for a,b in zip(self.t[:-1],self.t[1:]):n=transport(n,a,b);normal.append(n)
  self.n=np.array(normal);self.b=unit(np.cross(self.t,self.n))
 def at(self,s):
  s=np.asarray(s);c=np.column_stack([np.interp(s,self.s,self.p[:,j])for j in range(3)]);t=unit(np.column_stack([np.interp(s,self.s,self.t[:,j])for j in range(3)]));n=np.column_stack([np.interp(s,self.s,self.n[:,j])for j in range(3)]);n=unit(n-t*np.einsum('ij,ij->i',n,t)[:,None]);b=unit(np.cross(t,n));return c,t,n,b
 def closest(self,points):
  # Four nearby segmentcentres sufficefor this monotonicrestcurve. Exact segment
  # projection locally; no nearestvertex approximation in stored materialcoord.
  a=self.p[:-1];v=np.diff(self.p,axis=0);_,ix=cKDTree((a+self.p[1:])*.5).query(points,k=4);aa=a[ix];vv=v[ix];tau=np.clip(np.einsum('nkj,nkj->nk',points[:,None]-aa,vv)/np.einsum('nkj,nkj->nk',vv,vv),0,1);foot=aa+tau[:,:,None]*vv;which=np.argmin(np.linalg.norm(points[:,None]-foot,axis=2),axis=1);ii=ix[np.arange(len(points)),which];u=tau[np.arange(len(points)),which];return self.s[ii]+u*(self.s[ii+1]-self.s[ii])
class SleeveCurve:
 def __init__(self):
  self.input=ROOT/'hoodie-repair02/v7-bind.npz';d=np.load(self.input);self.pos=[d[f'p{i}']for i in range(5)];self.w=[d[f'W{i}']for i in range(5)];self.tri=[d[f'tr{i}']for i in range(5)];self.unique=np.zeros_like(U);np.add.at(self.unique,INV,np.concatenate(self.pos));self.unique/=np.bincount(INV)[:,None];self.uw=np.zeros((len(U),N));np.add.at(self.uw,INV,np.concatenate(self.w));self.uw/=np.bincount(INV)[:,None];self.cloth=np.zeros(len(U),bool);self.cloth[np.unique(np.concatenate([INV[self.tri[i]+OFF[i]]for i in [0,2]]))]=True;self.ref={}
  for sg,a in [(1,6),(-1,10)]:
   joints=P[[a,a+1,a+2]];t=unit(joints[1]-joints[0]);normal=unit(np.array([1.,0,0])-t*t[0]);curve=Curve(joints,normal);arm=self.uw[:,a:a+3].sum(1);hand=self.uw[:,a+2];mix=smooth((arm-.12)/.65)*smooth((1-hand)/.15)*self.cloth*(U[:,2]*sg>0);ids=np.flatnonzero(mix>1e-8);s=curve.closest(self.unique[ids]);c,t,n,b=curve.at(s);r=self.unique[ids]-c;local=np.stack([np.einsum('ij,ij->i',r,t),np.einsum('ij,ij->i',r,n),np.einsum('ij,ij->i',r,b)],axis=1);self.ref[sg]={'a':a,'curve':curve,'ids':ids,'s':s,'local':local,'mix':mix[ids],'startNormal':normal}
 def target(self,D,posed=None,clearance=False):
  skin=deform(self.pos,self.w,D)if posed is None else posed
  if np.max(abs(D-np.eye(4)))<1e-10:return [p.copy()for p in skin],{'neutralIdentityExact':True,'maxCorrectionM':0.,'sides':[]}
  world=np.zeros_like(U);np.add.at(world,INV,np.concatenate(skin));world/=np.bincount(INV)[:,None];target=world.copy();rows=[]
  for sg,r in self.ref.items():
   a=r['a'];Q=np.einsum('nij,nj->ni',D[[a,a+1,a+2],:3,:],np.c_[P[[a,a+1,a+2]],np.ones(3)]);curve=Curve(Q,D[a,:3,:3]@r['startNormal']);s=r['s']/r['curve'].length*curve.length;c,t,n,b=curve.at(s)
   # Actual bone roll vs rotation-minimizing curve frame, interpolated along material
   # length. Hand roll extends smoothlytowardcuff; exact rigidcuff vertices held.
   phis=[]
   for fraction,j in [(.75,a+1),(.97,a+2)]:
    sr=np.array([r['curve'].length*fraction]);_,_,nr,_=r['curve'].at(sr);_,tp,np_,bp=curve.at(sr/r['curve'].length*curve.length);want=D[j,:3,:3]@nr[0];want=unit(want-tp[0]*np.dot(want,tp[0]));phi=float(np.arctan2(np.dot(want,bp[0]),np.dot(want,np_[0])));phis.append(phi)
   f=r['s']/r['curve'].length;fore=phis[0]*smooth((f-.35)/.40);hand=phis[0]+np.arctan2(np.sin(phis[1]-phis[0]),np.cos(phis[1]-phis[0]))*smooth((f-.76)/.21);phi=np.where(f<.76,fore,hand);cs=np.cos(phi);sn=np.sin(phi);nn=n*cs[:,None]+b*sn[:,None];bb=b*cs[:,None]-n*sn[:,None];local=r['local'];warped=c+t*local[:,0,None]+nn*local[:,1,None]+bb*local[:,2,None]
   projectedCount=0;maxProxyPush=0.
   if clearance:
    # Estimated proxycapsulesonly, not scannedarm anatomy/contactcertificate.
    for iteration in range(2):
     for j,radius in [(0,.050),(1,.040)]:
      v=Q[j+1]-Q[j];tau=np.clip(np.einsum('ij,j->i',warped-Q[j],v)/np.dot(v,v),0,1);foot=Q[j]+tau[:,None]*v;offset=warped-foot;dist=np.linalg.norm(offset,axis=1);vr=P[a+j+1]-P[a+j];taur=np.clip(np.einsum('ij,j->i',self.unique[r['ids']]-P[a+j],vr)/np.dot(vr,vr),0,1);refDistance=np.linalg.norm(self.unique[r['ids']]-(P[a+j]+taur[:,None]*vr),axis=1);effectiveRadius=np.minimum(radius,np.maximum(0,refDistance-.0015));push=np.maximum(effectiveRadius+.0015-dist,0);direction=np.divide(offset,dist[:,None],out=nn.copy(),where=dist[:,None]>1e-9);warped+=push[:,None]*direction;projectedCount+=int((push>1e-8).sum());maxProxyPush=max(maxProxyPush,float(push.max(initial=0)))
   ids=r['ids'];delta=(warped-world[ids])*r['mix'][:,None];target[ids]+=delta;rows.append({'side':sg,'referenceCurveLengthM':r['curve'].length,'posedCurveLengthM':curve.length,'curveArcLengthRatio':curve.length/r['curve'].length,'boneSegmentLengthRatios':(np.linalg.norm(np.diff(Q,axis=0),axis=1)/np.linalg.norm(np.diff(P[[a,a+1,a+2]],axis=0),axis=1)).tolist(),'forearmRollDegrees':float(np.degrees(phis[0])),'handRollDegrees':float(np.degrees(phis[1])),'mappedUniqueVertices':len(ids),'maxMappedCorrectionM':float(np.linalg.norm(delta,axis=1).max(initial=0)),'proxyPushCount':projectedCount,'maxProxyPushM':maxProxyPush})
  delta=target-world;out=[skin[i]+delta[INV[OFF[i]:OFF[i+1]]]for i in range(5)];return out,{'neutralIdentityExact':False,'maxCorrectionM':float(np.linalg.norm(delta,axis=1).max()),'headExact':all(np.array_equal(out[i],skin[i])for i in [3,4]),'handsExact':np.array_equal(out[1],skin[1]),'sides':rows,'method':'C1 anatomical centreline, rotation-minimizing radialframe, normalizedmaterialarc length, distributedbone/wristroll. Softtorso attachment usingfrozennormalizedweights, exactrigidcuff/headheld.','limits':'Preservesreference radialcoordinates beforeoptionalproxyprojection, notglobalclothvolume/contact/CCD. Centrelinecurvature canstillinvert innerthicktube; literaltrianglegate mandatory.'}
