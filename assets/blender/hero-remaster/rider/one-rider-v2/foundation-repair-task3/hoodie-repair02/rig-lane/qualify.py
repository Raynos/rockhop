from weights import *
OUT=HERE;poses=HERE/('soft-anchor-poses'if SOFTANCHOR else'c1-poses'if C1 else'softened-poses'if SOFT else'poses');poses.mkdir(exist_ok=True)
roi=((U[CT][:,:,1]>1.08)&(U[CT][:,:,1]<1.49)&(abs(U[CT][:,:,2])<.405)).all(1)
t=CT[roi];e=np.unique(np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[0,2]]]),axis=1),axis=0)
models=[('source',POS,W),('soft-anchor'if SOFTANCHOR else'c1'if C1 else'softened'if SOFT else'weights',POS,out)]
r1=np.load(HERE.parent/'round1-bind.npz');models+=[('shape-weights',[r1[f'p{i}']for i in range(5)],out)]
if SOFT or SOFTANCHOR:
 er=np.load(HERE.parent/'shape-lane/envelope-rest.npz');models+=[('corrected-rest',[er[f'p{i}']for i in range(5)],out)]
rows=[]
for name,ps,ws in models:
 basep=np.zeros_like(U);np.add.at(basep,INV,np.concatenate(ps));basep/=cnt[:,None]
 l0=np.linalg.norm(basep[e[:,0]]-basep[e[:,1]],axis=1)
 a0=np.linalg.norm(np.cross(basep[t[:,1]]-basep[t[:,0]],basep[t[:,2]]-basep[t[:,0]]),axis=1)
 for kind,v in [('rest',0),('raise',.25),('raise',.5),('raise',.75),('raise',1),('sit',0),('sit',.5),('sit',1)]:
  D=raise_pose(v)if kind=='raise'else sit_pose(v,natural=True)if kind=='sit'else np.repeat(np.eye(4)[None],N,axis=0)
  pts=deform(ps,ws,D,kind=='sit');q=np.zeros_like(U);np.add.at(q,INV,np.concatenate(pts));q/=cnt[:,None]
  ratio=np.linalg.norm(q[e[:,0]]-q[e[:,1]],axis=1)/np.maximum(l0,1e-15)
  area=np.linalg.norm(np.cross(q[t[:,1]]-q[t[:,0]],q[t[:,2]]-q[t[:,0]]),axis=1)/np.maximum(a0,1e-15)
  r={'model':name,'kind':kind,'fraction':v,'maxEdgeRatio':float(ratio.max()),'p99EdgeRatio':float(np.quantile(ratio,.99)),'collapsedFacesBelowQuarter':int((area<.25).sum())}
  rows.append(r);print(r)
  np.savez(poses/f'{name}-{kind}-{v}.npz',**{f'p{i}':p for i,p in enumerate(pts)},matrices=D)
sel=(POS[0][:,1]>1.08)&(POS[0][:,1]<1.32)&(abs(POS[0][:,2])<.19)
field={}
for name,ws in [('source',W),('weights',out)]:
 a=ws[0][:,[5,6,7,8,9,10,11,12]].sum(1);field[name]={'sideTorsoAbove25pct':int((a[sel]>.25).sum()),'sideTorsoMean':float(a[sel].mean())}
(HERE/('soft-anchor-gates.json'if SOFTANCHOR else'c1-gates.json'if C1 else'softened-gates.json'if SOFT else'quick-gates.json')).write_text(json.dumps({'rows':rows,'selectors':field,'region':'Matched all-corner source upper garment ROI. Numerical metrics only; requires visual and literal triangle gates. Shape-weights rest denominators from changed rest mesh, source field denominators source rest.','finite':all(np.isfinite(w).all()for w in out)},indent=2))
