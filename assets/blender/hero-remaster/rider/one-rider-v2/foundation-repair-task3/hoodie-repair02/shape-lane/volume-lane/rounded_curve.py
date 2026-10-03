"""Rounded anatomical garment centreline + original skin ownership decomposition.
Unlike first RMF trial, ONLY arm's normalized skin contribution is replaced; all
nonarm weights stay exact. Finite Jacobian limiter is a separate ablation.
"""
from sleeve_curve import *
from scipy.spatial.transform import Rotation as R
class RoundedCurve(Curve):
 def __init__(self,centres,startNormal,radius=.110):
  p0,p1,p2=np.asarray(centres);du=unit(p1-p0);dv=unit(p2-p1);theta=float(np.arccos(np.clip(np.dot(du,dv),-1,1)));bend=np.cross(du,dv);L1=np.linalg.norm(p1-p0);L2=np.linalg.norm(p2-p1)
  if theta<1e-5:
   self.p=np.linspace(p0,p2,201);self.t=np.repeat(unit(p2-p0)[None],201,axis=0)
  else:
   bend=unit(bend);radius=min(radius,.78*min(L1,L2)/max(np.tan(theta/2),1e-6));back=radius*np.tan(theta/2);a=p1-back*du;b=p1+back*dv;centre=a+radius*unit(np.cross(bend,du));v0=a-centre;angles=np.linspace(0,theta,73);rot=R.from_rotvec(angles[:,None]*bend).as_matrix();arc=centre+np.einsum('nij,j->ni',rot,v0);arct=np.einsum('nij,j->ni',rot,du);self.p=np.concatenate([np.linspace(p0,a,65)[:-1],arc,np.linspace(b,p2,65)[1:]]);self.t=np.concatenate([np.repeat(du[None],64,axis=0),arct,np.repeat(dv[None],64,axis=0)])
  self.s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(self.p,axis=0),axis=1))];self.length=float(self.s[-1]);n=unit(startNormal-self.t[0]*np.dot(startNormal,self.t[0]));normal=[n]
  for ta,tb in zip(self.t[:-1],self.t[1:]):n=transport(n,ta,tb);normal.append(n)
  self.n=np.array(normal);self.b=unit(np.cross(self.t,self.n));self.curvature=np.gradient(self.t,self.s,axis=0)
 def curvature_at(self,s):return np.column_stack([np.interp(s,self.s,self.curvature[:,j])for j in range(3)])
class RoundedSleeve(SleeveCurve):
 def __init__(self):
  super().__init__()
  for sg,r in self.ref.items():
   a=r['a'];curve=RoundedCurve(P[[a,a+1,a+2]],r['startNormal']);arm=self.uw[:,a:a+3].sum(1);hand=self.uw[:,a+2];mix=arm*smooth((1-hand)/.15)*self.cloth*(U[:,2]*sg>0);ids=np.flatnonzero(mix>1e-8);s=curve.closest(self.unique[ids]);c,t,n,b=curve.at(s);rr=self.unique[ids]-c;local=np.stack([np.einsum('ij,ij->i',rr,t),np.einsum('ij,ij->i',rr,n),np.einsum('ij,ij->i',rr,b)],axis=1);r.update(curve=curve,ids=ids,s=s,local=local,mix=mix[ids],armTotal=arm[ids])
 def target(self,D,posed=None,jacobian=False):
  skin=deform(self.pos,self.w,D)if posed is None else posed
  if np.max(abs(D-np.eye(4)))<1e-10:return [p.copy()for p in skin],{'neutralIdentityExact':True,'maxCorrectionM':0.,'sides':[]}
  world=np.zeros_like(U);np.add.at(world,INV,np.concatenate(skin));world/=np.bincount(INV)[:,None];target=world.copy();rows=[]
  for sg,r in self.ref.items():
   a=r['a'];ids=r['ids'];Q=np.einsum('nij,nj->ni',D[[a,a+1,a+2],:3,:],np.c_[P[[a,a+1,a+2]],np.ones(3)]);curve=RoundedCurve(Q,D[a,:3,:3]@r['startNormal']);s=r['s']/r['curve'].length*curve.length;c,t,n,b=curve.at(s);phis=[]
   for fraction,j in [(.75,a+1),(.97,a+2)]:
    sr=np.array([r['curve'].length*fraction]);_,_,nr,_=r['curve'].at(sr);_,tp,np_,bp=curve.at(sr/r['curve'].length*curve.length);want=D[j,:3,:3]@nr[0];want=unit(want-tp[0]*np.dot(want,tp[0]));phis.append(float(np.arctan2(np.dot(want,bp[0]),np.dot(want,np_[0]))))
   f=r['s']/r['curve'].length;fore=phis[0]*smooth((f-.35)/.40);hand=phis[0]+np.arctan2(np.sin(phis[1]-phis[0]),np.cos(phis[1]-phis[0]))*smooth((f-.76)/.21);phi=np.where(f<.76,fore,hand);cs=np.cos(phi);sn=np.sin(phi);nn=n*cs[:,None]+b*sn[:,None];bb=b*cs[:,None]-n*sn[:,None];local=r['local'].copy();radial=nn*local[:,1,None]+bb*local[:,2,None];curvature=curve.curvature_at(s);dot=np.einsum('ij,ij->i',curvature,radial);preJac=1-dot;limitedCount=0
   if jacobian:
    # Do not change an already imperfect rest coordinate tube atzero motion;
    # constrain newly induced inner-radius inversion, not repaint all sourcecloth.
    cr,tr,nr,br=r['curve'].at(r['s']);refRadial=nr*local[:,1,None]+br*local[:,2,None];refDot=np.einsum('ij,ij->i',r['curve'].curvature_at(r['s']),refRadial);bound=np.maximum(.8,refDot);excess=np.maximum(dot-bound,0);curv2=np.einsum('ij,ij->i',curvature,curvature);radial-=np.divide(excess,curv2,out=np.zeros_like(excess),where=curv2>1e-12)[:,None]*curvature;limitedCount=int((excess>1e-8).sum())
   warped=c+t*local[:,0,None]+radial
   armSkin=np.einsum('vj,jab,vb->va',self.uw[ids,a:a+3],D[a:a+3,:3,:],np.c_[self.unique[ids],np.ones(len(ids))],optimize=False)/r['armTotal'][:,None]
   delta=(warped-armSkin)*r['mix'][:,None];target[ids]+=delta;rows.append({'side':sg,'referenceCurveLengthM':r['curve'].length,'posedCurveLengthM':curve.length,'curveArcRatio':curve.length/r['curve'].length,'boneLengthRatios':(np.linalg.norm(np.diff(Q,axis=0),axis=1)/np.linalg.norm(np.diff(P[[a,a+1,a+2]],axis=0),axis=1)).tolist(),'minTubeJacBeforeLimit':float(preJac.min(initial=1)),'minTubeJacAfterLimit':float((1-np.einsum('ij,ij->i',curvature,radial)).min(initial=1)),'jacLimitedPoints':limitedCount,'maxCorrectionM':float(np.linalg.norm(delta,axis=1).max(initial=0)),'forearmRollDegrees':float(np.degrees(phis[0])),'handRollDegrees':float(np.degrees(phis[1]))})
  delta=target-world;out=[skin[i]+delta[INV[OFF[i]:OFF[i+1]]]for i in range(5)];return out,{'neutralIdentityExact':False,'maxCorrectionM':float(np.linalg.norm(delta,axis=1).max()),'headExact':all(np.array_equal(out[i],skin[i])for i in [3,4]),'handsExact':np.array_equal(out[1],skin[1]),'sides':rows,'method':'Roundedbonefilletgarmentcentreline withrotation-minimizingradial frame +ONLYreplacementofarmnormalizedskincontribution; originaltorsoownershipunchanged. OptionalpositiveJacobianradiallimiter.','limits':'Analytic tubeJacobiansareNOT triangleselfcollision certificate. Arc ratio measuredratherthanexactisometryclaim. No actualbody/timing/GPU/CCD guarantees.'}
