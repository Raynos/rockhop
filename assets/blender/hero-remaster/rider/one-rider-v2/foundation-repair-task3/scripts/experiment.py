from pathlib import Path
import json,sys,copy,hashlib
import numpy as np
from scipy.spatial.transform import Rotation as R,Slerp
sys.path.insert(0,str(Path(__file__).parent));from glb import GLB
root=Path.cwd();g0=GLB(root/'baseline/rider.glb');skin=g0.j['skins'][0];ids=skin['joints'];names=[g0.j['nodes'][n]['name'] for n in ids];N=len(names);idx={n:i for i,n in enumerate(names)}
rest=np.linalg.inv(g0.array(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float));oldP=rest[:,:3,3].copy();parents={c:i for i,n in enumerate(g0.j['nodes']) for c in n.get('children',[])}
prims=[p for m in g0.j['meshes'] for p in m['primitives']];ps=[g0.array(p['attributes']['POSITION']).astype(float) for p in prims];ns=[g0.array(p['attributes']['NORMAL']).astype(float)for p in prims];tris=[g0.array(p['indices']).reshape(-1,3).astype(int)for p in prims]
# Source contact endpoint matrices are read-only static orientation/marker data; motion is newly authored.
src=Path('/Users/raynos/Documents/Codex/2026-10-01/task-2/evidence/motion');motion=json.loads((src/'pose-manifest.json').read_text());contact=np.array(motion['rows'][-1]['dump'][0]['matrices']).reshape(N,4,4).transpose(0,2,1);contactWorld=np.einsum('nij,njk->nik',contact,rest)
bike=json.loads((src/'bike.json').read_text());bike=[x for x in bike if x['name'] and not any(s in x['name'] for s in ['Protected','textured','blur','spokes'])];(root/'evidence/bike.json').write_text(json.dumps(bike))
def getarr(g,ai):
 a=g.j['accessors'][ai];k={'SCALAR':1,'VEC3':3}[a['type']];v=g.array(ai).astype(float) if 'bufferView' in a else np.zeros((a['count'],k))
 if 'sparse' in a:
  s=a['sparse'];vi=g.j['bufferViews'][s['indices']['bufferView']];ii=np.frombuffer(g.bin,dtype={5121:'u1',5123:'<u2',5125:'<u4'}[s['indices']['componentType']],count=s['count'],offset=vi.get('byteOffset',0)+s['indices'].get('byteOffset',0));vv=g.j['bufferViews'][s['values']['bufferView']];vals=np.frombuffer(g.bin,dtype='<f4',count=s['count']*k,offset=vv.get('byteOffset',0)+s['values'].get('byteOffset',0)).reshape(-1,k);v[ii]=vals
 return v
closed=[p.copy() for p in ps]
for i,p in enumerate(prims):
 for tar in p.get('targets',[]):closed[i]+=getarr(g0,tar['POSITION'])
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def weights(P,centres,helpers=False):
 W=np.zeros((len(P),N+4 if helpers else N));x,y,z=P.T
 # Leg field is from geometric side and longitudinal position, independent of old weights.
 torso=smooth((y-.91)/.09)
 for side,sg in [('L',1),('R',-1)]:
  h=idx['thigh.'+side];k=idx['shin.'+side];f=idx['foot.'+side];lat=smooth((sg*z+.025)/.05)
  hip=centres[h];knee=centres[k];ank=centres[f]
  ht=smooth((hip[1]+.055-y)/.15);kt=smooth((knee[1]+.065-y)/.13);ft=smooth((ank[1]+.055-y)/.11)
  leg=(1-torso)*lat
  if helpers:
   hh=N+(0 if side=='L' else 2);kh=hh+1
   W[:,0]+=leg*(1-ht)**2;W[:,hh]+=leg*2*ht*(1-ht);W[:,h]+=leg*ht**2*(1-kt)**2;W[:,kh]+=leg*ht**2*2*kt*(1-kt);W[:,k]+=leg*ht**2*kt**2*(1-ft);W[:,f]+=leg*ht**2*kt**2*ft
  else:
   W[:,0]+=leg*(1-ht);W[:,h]+=leg*ht*(1-kt);W[:,k]+=leg*ht*kt*(1-ft);W[:,f]+=leg*ht*kt*ft
 # Upper body nearest capsule classification, smooth along bones. Head/hair rigid.
 arms=np.zeros_like(W)
 for side,sg in [('L',1),('R',-1)]:
  a=idx['upperArm.'+side];b=idx['forearm.'+side];c=idx['hand.'+side];q=centres[[a,b,c]]
  ds=[];ts=[]
  for u,v in zip(q[:-1],q[1:]):
   t=np.clip(np.einsum('ij,j->i',P-u,v-u,optimize=False)/np.dot(v-u,v-u),0,1);ds.append(np.linalg.norm(P-(u+t[:,None]*(v-u)),axis=1));ts.append(t)
  near=np.minimum(ds[0],ds[1]);armzone=smooth((abs(z)-(.24-.08*smooth((y-1.08)/.12)))/.055)*smooth((.14-near)/.055)*smooth((y-.70)/.08)*(sg*z>0)
  upper=(ds[0]<ds[1]);el=smooth((ts[0]-.78)/.22);wrist=smooth((ts[1]-.78)/.22)
  arms[:,a]+=armzone*upper*(1-el);arms[:,b]+=armzone*(upper*el+(~upper)*(1-wrist));arms[:,c]+=armzone*(~upper)*wrist
 ar=np.minimum(arms.sum(1),1);W*= (1-ar[:,None]);W+=arms
 rem=torso*(1-ar)
 # vertical torso between named joints; shoulders are translation links, clothes follow chest.
 levels=[centres[i,1]for i in [0,1,2,3,4]]
 for j in range(4):
  t=smooth((y-levels[j])/(levels[j+1]-levels[j]));prev=smooth((y-levels[j-1])/(levels[j]-levels[j-1])) if j else np.ones(len(P));W[:,j]+=rem*prev*(1-t)
 W[:,4]+=rem*smooth((y-levels[3])/(levels[4]-levels[3]))
 W/=np.maximum(W.sum(1,keepdims=True),1e-20)
 # Four-lane runtime contract. Identical positions receive identical geometric field.
 select=np.argsort(W,axis=1)[:,-4:][:,::-1];v=np.take_along_axis(W,select,axis=1);v/=v.sum(1,keepdims=True);out=np.zeros_like(W);np.put_along_axis(out,select,v,axis=1);return out

def align(a,b):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=np.dot(a,b)
 if c<-.999999:return R.from_rotvec(np.array([0,0,np.pi])).as_matrix()
 K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]);return np.eye(3)+K+K@K/(1+c)
def mat(rot,p):m=np.eye(4);m[:3,:3]=rot;m[:3,3]=p;return m
def ik(a,b,l1,l2,pole):
 d=b-a;r=np.linalg.norm(d);u=d/r;cl=np.clip(r,abs(l1-l2)+1e-6,l1+l2-1e-6);along=(l1*l1-l2*l2+cl*cl)/(2*cl);h=np.sqrt(max(0,l1*l1-along*along));v=np.array(pole)-u*np.dot(pole,u);v/=np.linalg.norm(v);return a+u*along+v*h,max(0,r-l1-l2)
def pose(P,t,kind='sit',helpers=False):
 n=len(P);G=np.repeat(np.eye(4)[None],n,axis=0);out=P.copy();rots=np.repeat(np.eye(3)[None],n,axis=0);u=smooth(t)
 if kind=='rest':out=P.copy()
 elif kind=='sit':
  hip=np.array([-.15,.91,0])*(1-u)+np.array([-.346,.738,0])*u;ang=.72*(1-u)+.46*u;tor=R.from_euler('z',-ang).as_matrix();out[0]=hip;rots[[0,1,2]]=tor
  for j in [1,2,3,4,5,6,9,10]:out[j]=hip+tor@(P[j]-P[0]);rots[j]=tor
  # rigid head counter-rotated to preserve looking ahead.
  rots[3]=rots[4]=np.eye(3);out[4]=out[3]+P[4]-P[3]
  for side,sg in [('L',1),('R',-1)]:
   h,k,f=[idx[s+'.'+side]for s in ['thigh','shin','foot']];a,b,c=[idx[s+'.'+side]for s in ['upperArm','forearm','hand']]
   out[h]=hip+tor@(P[h]-P[0]);out[f]=contactWorld[f,:3,3];out[k],_=ik(out[h],out[f],np.linalg.norm(P[k]-P[h]),np.linalg.norm(P[f]-P[k]),[1,0,sg*.28]);rots[h]=align(P[k]-P[h],out[k]-out[h]);rots[k]=align(P[f]-P[k],out[f]-out[k]);rots[f]=contact[f,:3,:3]
   out[c]=contactWorld[c,:3,3];out[b],_=ik(out[a],out[c],np.linalg.norm(P[b]-P[a]),np.linalg.norm(P[c]-P[b]),[-1,0,sg*.20]);rots[a]=align(P[b]-P[a],out[b]-out[a]);rots[b]=align(P[c]-P[b],out[c]-out[b]);rots[c]=contact[c,:3,:3]
 else:
  # isolated hinge sweeps: flexion, abduction, knee; pelvis fixed and no IK.
  angle=np.deg2rad(t);axis={'flex':[0,0,1],'abd':[1,0,0],'knee':[0,0,-1]}[kind]
  for side,sg in [('L',1),('R',-1)]:
   h,k,f=[idx[s+'.'+side]for s in ['thigh','shin','foot']];r=R.from_rotvec(np.array(axis)*angle*(sg if kind=='abd' else 1)).as_matrix();pivot=k if kind=='knee' else h
   for j in ([k,f]if kind=='knee' else [h,k,f]):out[j]=P[pivot]+r@(P[j]-P[pivot]);rots[j]=r
 if helpers:
  for side in ['L','R']:
   h,k=[idx[s+'.'+side]for s in ['thigh','shin']];hh=N+(0 if side=='L' else 2);kh=hh+1
   out[hh]=out[h];out[kh]=out[k]
   rots[hh]=Slerp([0,1],R.from_matrix([rots[0],rots[h]]))([.5]).as_matrix()[0];rots[kh]=Slerp([0,1],R.from_matrix([rots[h],rots[k]]))([.5]).as_matrix()[0]
 for j in range(n):G[j]=mat(rots[j],out[j])@mat(np.eye(3),-P[j])
 return G

def skinpos(P,W,D):return np.einsum('vj,jab,vb->va',W,D[:,:3,:],np.c_[P,np.ones(len(P))],optimize=False)
variants={}
for name in ['A','B','C19','C']:
 fresh=name.startswith('C');helper=name=='C';P=oldP.copy()
 if fresh:
  # surface-based estimate under jeans, with spine centred over hip line.
  P[0]=[.645,.918,0];P[1]=[.637,1.065,0];P[2]=[.630,1.265,0]
  for side,sg in [('L',1),('R',-1)]:P[idx['thigh.'+side]]=[.638,.913,sg*.110];P[idx['shin.'+side]]=[.647,.505,sg*.145]
 if helper:P=np.vstack([P,P[[13,14,16,17]]])
 W=[]
 for pi,p in enumerate(prims):
  if name=='A':
   si=g0.array(p['attributes']['JOINTS_0']).astype(int);sw=g0.array(p['attributes']['WEIGHTS_0']);w=np.zeros((len(ps[pi]),N));np.add.at(w,(np.arange(len(w))[:,None],si),sw)
  else:
   w=weights(ps[pi],P,helper)
   if pi==1:
    w[:]=0;w[np.arange(len(w)),np.where(ps[pi][:,2]>0,idx['hand.L'],idx['hand.R'])]=1
   if pi>=3:w[:]=0;w[:,idx['head']]=1
  W.append(w)
 if name!='A':
  allpos=np.concatenate(ps);allw=np.concatenate(W);_,inv,cnt=np.unique(allpos,axis=0,return_inverse=True,return_counts=True);offsets=np.r_[0,np.cumsum([len(x)for x in ps])]
  for group in np.flatnonzero(cnt>1):
   ix=np.flatnonzero(inv==group)
   if np.all(allw[ix]==allw[ix[0]]):continue
   hand=ix[(ix>=offsets[1])&(ix<offsets[2])];head=ix[ix>=offsets[3]];owner=hand[0]if len(hand)else head[0]if len(head)else ix[0];allw[ix]=allw[owner]
  W=[allw[offsets[i]:offsets[i+1]].copy()for i in range(len(ps))]
 variants[name]=(P,W,helper)
 np.savez(root/'experiments'/f'{name}-bind.npz',centres=P,**{f'W{i}':w for i,w in enumerate(W)})
# Stand to sit controls plus withheld intermediate samples and flexion/abd/knee sweeps.
metrics={};expected={};manifest={'variants':[],'ordering':'mesh primitives in GLB mesh order','source':str(root/'baseline/rider.glb')}
for name,(P,W,helper) in variants.items():
 g=GLB(root/'baseline/rider.glb');fresh=name.startswith('C');nodeids=ids.copy();rworld=rest.copy();localparents=[None if parents.get(n)==25 else nodeids.index(parents[n]) for n in ids]
 if fresh:
  count=len(P);rworld=np.array([mat(np.eye(3),p)for p in P]);newnames=names+(['hipHalf.L','kneeHalf.L','hipHalf.R','kneeHalf.R']if helper else []);localparents=[None,0,1,2,3,2,5,6,7,2,9,10,11,0,13,14,0,16,17]+([0,13,0,16]if helper else [])
  nodeids=[]
  for j,nm in enumerate(newnames):nodeids.append(len(g.j['nodes']));g.j['nodes'].append({'name':'fresh.'+nm})
  for j,n in enumerate(nodeids):
   par=localparents[j];g.j['nodes'][n]['translation']=(P[j]-(P[par]if par is not None else 0)).tolist();g.j['nodes'][n]['children']=[nodeids[k]for k,p in enumerate(localparents)if p==j]
  g.j['nodes'][25]['children']=[23,24,nodeids[0]];g.j['nodes'][25]['translation']=[0,0,0];g.j['nodes'][25]['rotation']=[0,0,0,1];g.j['nodes'][25]['scale']=[1,1,1]
 def add(a,typ,comp=5126):
  a=np.ascontiguousarray(a,dtype='<f4'if comp==5126 else '<u2');g.bin.extend(b'\0'*((-len(g.bin))%4));vi=len(g.j['bufferViews']);g.j['bufferViews'].append({'buffer':0,'byteOffset':len(g.bin),'byteLength':a.nbytes});g.bin.extend(a.tobytes());ai=len(g.j['accessors']);ac={'bufferView':vi,'componentType':comp,'count':len(a),'type':typ}
  if typ=='SCALAR' and comp==5126:ac.update(min=[float(a.min())],max=[float(a.max())])
  g.j['accessors'].append(ac);return ai
 if fresh:g.j['skins']=[{'joints':nodeids,'skeleton':nodeids[0],'inverseBindMatrices':add(np.linalg.inv(rworld).transpose(0,2,1).reshape(-1,16),'MAT4')}]
 for i,p in enumerate([p for m in g.j['meshes']for p in m['primitives']]):
  if name!='A':
   si=np.argsort(W[i],axis=1)[:,-4:][:,::-1];sw=np.take_along_axis(W[i],si,axis=1);p['attributes']['JOINTS_0']=add(si,'VEC4',5123);p['attributes']['WEIGHTS_0']=add(sw,'VEC4')
 g.j['animations']=[];mrows=[]
 for clip,kind,vals in [('rigid_length_stand_to_sit','sit',np.linspace(0,1,25)),('bind_restore','rest',[0,1]),('hip_flexion_sweep','flex',np.linspace(0,120,13)),('hip_abduction_sweep','abd',np.linspace(0,45,10)),('knee_bend_sweep','knee',np.linspace(0,135,10))]:
  times=np.linspace(0,2,len(vals));ti=add(times,'SCALAR');G=[pose(P,float(t),kind,helper)for t in vals];worlds=[np.einsum('nij,njk->nik',d,rworld)for d in G];clipj={'name':clip,'samplers':[],'channels':[]}
  def channel(node,path,a,typ):clipj['samplers'].append({'input':ti,'output':add(a,typ),'interpolation':'LINEAR'});clipj['channels'].append({'sampler':len(clipj['samplers'])-1,'target':{'node':node,'path':path}})
  locals=[]
  for world in worlds:locals.append([np.linalg.inv(world[par])@world[j]if par is not None else world[j]for j,par in enumerate(localparents)])
  locals=np.array(locals)
  for j,node in enumerate(nodeids):
   channel(node,'translation',locals[:,j,:3,3],'VEC3');scales=np.linalg.norm(locals[:,j,:3,:3],axis=1);rot=R.from_matrix(locals[:,j,:3,:3]/scales[:,None,:]).as_quat();rot=np.array([r if k==0 or np.dot(r,rot[k-1])>=0 else -r for k,r in enumerate(rot)]);channel(node,'rotation',rot,'VEC4');channel(node,'scale',scales,'VEC3')
  for path,arr,typ in [('translation',np.zeros((len(vals),3)),'VEC3'),('rotation',np.tile([0,0,0,1],(len(vals),1)),'VEC4'),('scale',np.ones((len(vals),3)),'VEC3')]:channel(25,path,arr,typ)
  channel(23,'weights',np.ones((len(vals)*2,))*(0 if kind=='rest'else 1),'SCALAR');g.j['animations'].append(clipj)
  for k,(val,D)in enumerate(zip(vals,G)):
   poses=[skinpos(p if kind=='rest'else closed[i],w,D)for i,(p,w)in enumerate(zip(ps,W))];file=f'{name}-{clip}-{k:03d}.npz';np.savez(root/'experiments'/file,**{f'p{i}':p for i,p in enumerate(poses)},matrices=D)
   base=ps[0];tri=tris[0];roi=np.all((base[tri,:,] if False else base[tri])[:,:,1]>.69,axis=1)&np.all(base[tri][:,:,1]<1.08,axis=1)&np.all(abs(base[tri][:,:,2])<.245,axis=1);rt=tri[roi];q=poses[0];area0=np.linalg.norm(np.cross(base[rt[:,1]]-base[rt[:,0]],base[rt[:,2]]-base[rt[:,0]]),axis=1);area=np.linalg.norm(np.cross(q[rt[:,1]]-q[rt[:,0]],q[rt[:,2]]-q[rt[:,0]]),axis=1);edges=np.unique(np.sort(np.concatenate([rt[:,[0,1]],rt[:,[1,2]],rt[:,[0,2]]]),axis=1),axis=0);ratio=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/np.maximum(np.linalg.norm(base[edges[:,0]]-base[edges[:,1]],axis=1),1e-12);blend=np.einsum('vj,jab->vab',W[0],D[:,:3,:3]);det=np.linalg.det(blend);mrows.append({'clip':clip,'k':k,'value':float(val),'collapsedQuarter':int(np.sum(area<area0*.25)),'maxStretch':float(ratio.max()),'p99Stretch':float(np.quantile(ratio,.99)),'minBlendDetHip':float(det[np.unique(rt)].min()),'medianBlendDetHip':float(np.median(det[np.unique(rt)]))})
 
 if fresh:
  g.j['nodes'][25]['extras']={'freshRigComparison':'Isolated new armature; old private19 contact/conditioning contract intentionally unavailable','oldContactAdapterNotCompatible':True,'jointCount':len(P)}
 if fresh:
  kept=[23,24,25]+nodeids;remap={n:i for i,n in enumerate(kept)};g.j['nodes']=[g.j['nodes'][n]for n in kept]
  for n in g.j['nodes']:
   if 'children' in n:n['children']=[remap[c]for c in n['children']if c in remap]
  for scn in g.j['scenes']:scn['nodes']=[remap[n]for n in scn['nodes']if n in remap]
  g.j['skins'][0]['joints']=[remap[n]for n in nodeids];g.j['skins'][0]['skeleton']=remap[nodeids[0]]
  for anim in g.j['animations']:
   for ch in anim['channels']:ch['target']['node']=remap[ch['target']['node']]
 g.j['buffers'][0]['byteLength']=len(g.bin);g.j['asset'].setdefault('extras',{})['freshRigComparison']={'sourceSHA256':hashlib.sha256(g0.raw).hexdigest(),'variant':name,'sourceGeometryAndTexturesRetained':True,'freshSkeleton':fresh,'joints':len(P),'linearBlendSkinning':True,'scope':'isolated unaccepted rig comparison'};g.write(root/'deliverables'/f'{name}.glb')
 metrics[name]=mrows;manifest['variants'].append({'name':name,'glb':str(root/'deliverables'/f'{name}.glb'),'clips':['rigid_length_stand_to_sit','bind_restore','hip_flexion_sweep','hip_abduction_sweep','knee_bend_sweep'],'expectedFolder':str(root/'experiments'),'keyExpectedPattern':name+'-{clip}-{key:03d}.npz'})
(root/'evidence/metrics.json').write_text(json.dumps(metrics,indent=2));(root/'evidence/manifest.json').write_text(json.dumps(manifest,indent=2));print({n:[r for r in rows if r['clip']=='rigid_length_stand_to_sit' and r['k']in [0,12,24]]for n,rows in metrics.items()})
