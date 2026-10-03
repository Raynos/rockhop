from pathlib import Path
import sys,json,numpy as np
from scipy.spatial.transform import Rotation as R,Slerp
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra,connected_components
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'hoodie-repair02';sys.path.insert(0,str(ROOT/'scripts'));from glb import GLB
G=GLB(ROOT/'deliverables/C19.glb');PR=[p for m in G.j['meshes']for p in m['primitives']];POS=[G.array(p['attributes']['POSITION']).astype(float)for p in PR];NOR=[G.array(p['attributes']['NORMAL']).astype(float)for p in PR];TRI=[G.array(p['indices']).astype(int).reshape(-1,3)for p in PR];bind=np.load(ROOT/'experiments/C19-bind.npz');P=bind['centres'];W=[bind[f'W{i}']for i in range(5)];N=19
IND={s:j for j,s in enumerate(['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','forearm.L','hand.L','shoulder.R','upperArm.R','forearm.R','hand.R','thigh.L','shin.L','foot.L','thigh.R','shin.R','foot.R'])}
END=np.load(ROOT/'experiments/C19-rigid_length_stand_to_sit-024.npz')['matrices'];CW=np.einsum('nij,nj->ni',END[:,:3,:],np.c_[P,np.ones(N)])
OFF=np.r_[0,np.cumsum([len(p)for p in POS])];ALL=np.concatenate(POS);U,INV=np.unique(ALL,axis=0,return_inverse=True);UT=[INV[t+OFF[i]]for i,t in enumerate(TRI)];CT=np.concatenate([UT[0],UT[2]]);edges=np.unique(np.sort(np.concatenate([CT[:,[0,1]],CT[:,[1,2]],CT[:,[0,2]]]),axis=1),axis=0)

def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def align(a,b):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=np.dot(a,b);K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]);return np.eye(3)+K+K@K/max(1+c,1e-12)
def ik(a,b,l1,l2,pole):
 d=b-a;r=np.linalg.norm(d);u=d/r;c=np.clip(r,abs(l1-l2)+1e-6,l1+l2-1e-6);s=(l1*l1-l2*l2+c*c)/(2*c);h=np.sqrt(max(0,l1*l1-s*s));v=np.array(pole)-u*np.dot(pole,u);v/=np.linalg.norm(v);return a+u*s+v*h

def source_morph(i,ai):
 a=G.j['accessors'][ai];k=3;v=G.array(ai).astype(float)if 'bufferView'in a else np.zeros((a['count'],k))
 if 'sparse'in a:
  s=a['sparse'];b=G.j['bufferViews'][s['indices']['bufferView']];ix=np.frombuffer(G.bin,dtype={5121:'u1',5123:'<u2',5125:'<u4'}[s['indices']['componentType']],count=s['count'],offset=b.get('byteOffset',0)+s['indices'].get('byteOffset',0));b=G.j['bufferViews'][s['values']['bufferView']];v[ix]=np.frombuffer(G.bin,dtype='<f4',count=s['count']*3,offset=b.get('byteOffset',0)+s['values'].get('byteOffset',0)).reshape(-1,3)
 return v
CLOSE=[p.copy()for p in POS]
for i,pr in enumerate(PR):
 for t in pr.get('targets',[]):CLOSE[i]+=source_morph(i,t['POSITION'])
MORPH=[c-p for c,p in zip(CLOSE,POS)]

def deform(pos,weights,D,closed=False):return [np.einsum('vj,jab,vb->va',w,D[:,:3,:],np.c_[p+(MORPH[i]if closed else 0),np.ones(len(p))],optimize=False)for i,(p,w)in enumerate(zip(pos,weights))]
def raise_pose(t):
 D=np.repeat(np.eye(4)[None],N,axis=0)
 for sg,a in [(1,6),(-1,10)]:
  direction=P[a+1]-P[a];target=np.array([0,0,sg]);axis=np.cross(direction,target);axis/=np.linalg.norm(axis);theta=np.arccos(np.dot(direction,target)/np.linalg.norm(direction));rot=R.from_rotvec(axis*theta*t).as_matrix()
  for j in [a,a+1,a+2]:D[j,:3,:3]=rot;D[j,:3,3]=P[a]-rot@P[a]
 return D

def sit_pose(t,natural=False,leanoffset=0,neckfraction=.20,headfraction=.20):
 u=smooth(t);hip=np.array([-.15,.91,0])*(1-u)+np.array([-.346,.738,0])*u;ang=.72*(1-u)+.46*u+leanoffset;tor=R.from_euler('z',-ang).as_matrix();Q=P.copy();rot=np.repeat(np.eye(3)[None],N,axis=0);Q[0]=hip;rot[[0,1,2]]=tor
 for j in [1,2,3,4,5,6,9,10]:Q[j]=hip+tor@(P[j]-P[0]);rot[j]=tor
 neckangle=ang*neckfraction if natural else 0
 rot[3]=R.from_euler('z',-neckangle).as_matrix();rot[4]=R.from_euler('z',-headfraction*ang if natural else 0).as_matrix();Q[4]=Q[3]+rot[3]@(P[4]-P[3])
 for side,sg in [('L',1),('R',-1)]:
  h,k,f=[IND[s+'.'+side]for s in ['thigh','shin','foot']];a,b,c=[IND[s+'.'+side]for s in ['upperArm','forearm','hand']];Q[h]=hip+tor@(P[h]-P[0]);Q[f]=CW[f];Q[k]=ik(Q[h],Q[f],np.linalg.norm(P[k]-P[h]),np.linalg.norm(P[f]-P[k]),[1,0,sg*.28]);rot[h]=align(P[k]-P[h],Q[k]-Q[h]);rot[k]=align(P[f]-P[k],Q[f]-Q[k]);rot[f]=END[f,:3,:3];Q[c]=CW[c];Q[b]=ik(Q[a],Q[c],np.linalg.norm(P[b]-P[a]),np.linalg.norm(P[c]-P[b]),[-1,0,sg*.20]);rot[a]=align(P[b]-P[a],Q[b]-Q[a]);rot[b]=align(P[c]-P[b],Q[c]-Q[b]);rot[c]=END[c,:3,:3]
 D=np.repeat(np.eye(4)[None],N,axis=0);D[:,:3,:3]=rot;D[:,:3,3]=Q-np.einsum('nij,nj->ni',rot,P);return D

def normals(points,tris):
 n=np.zeros_like(points);q=points[tris];f=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0])
 for j in range(3):np.add.at(n,tris[:,j],f)
 return n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-15)
