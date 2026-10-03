from weights import *
source=HERE.parent/'shape-lane';rest=np.load(source/'envelope-rest.npz');pp=[rest[f'p{i}']for i in range(5)];rp=np.zeros_like(U);np.add.at(rp,INV,np.concatenate(pp));rp/=cnt[:,None]
roi=((U[CT][:,:,1]>1.08)&(U[CT][:,:,1]<1.49)&(abs(U[CT][:,:,2])<.405)).all(1);t=CT[roi];e=np.unique(np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[0,2]]]),axis=1),axis=0)
l0=np.linalg.norm(rp[e[:,0]]-rp[e[:,1]],axis=1);a0=np.linalg.norm(np.cross(rp[t[:,1]]-rp[t[:,0]],rp[t[:,2]]-rp[t[:,0]]),axis=1)
rows=[]
for f in [0,.25,.5,.75,1]:
 dat=np.load(source/f'raise-target-{f}.npz');D=dat['matrices'];pts=[dat[f'p{i}']for i in range(5)];q=np.zeros_like(U);np.add.at(q,INV,np.concatenate(pts));q/=cnt[:,None]
 ratio=np.linalg.norm(q[e[:,0]]-q[e[:,1]],axis=1)/l0;area=np.linalg.norm(np.cross(q[t[:,1]]-q[t[:,0]],q[t[:,2]]-q[t[:,0]]),axis=1)/a0
 condmax=0;parmax=0;deltamax=0;target={}
 for i in range(5):
  mat=np.einsum('vj,jab->vab',out[i],D[:,:3,:],optimize=False)
  sv=np.linalg.svd(mat[:,:,:3],compute_uv=False);condmax=max(condmax,float((sv[:,0]/sv[:,-1]).max()))
  delta=np.linalg.solve(mat[:,:,:3],(pts[i]-mat[:,:,3])[...,None])[...,0]-pp[i]
  delta=delta.astype('f4');back=np.einsum('vab,vb->va',mat,np.c_[pp[i]+delta,np.ones(len(delta))],optimize=False)
  parmax=max(parmax,float(np.linalg.norm(back-pts[i],axis=1).max()));deltamax=max(deltamax,float(np.linalg.norm(delta,axis=1).max()));target[f'delta{i}']=delta
 np.savez(HERE/f'raise-morph-{f}.npz',**target,matrices=D)
 r={'fraction':f,'maxEdgeRatio':float(ratio.max()),'p99EdgeRatio':float(np.quantile(ratio,.99)),'facesBelowQuarterRestArea':int((area<.25).sum()),'facesBelowTenthRestArea':int((area<.10).sum()),'facesAreaExpandedAbove4x':int((area>4).sum()),'minimumAreaRatio':float(area.min()),'maxInverseLBSCondition':condmax,'maxFloat32MorphParityM':parmax,'maxBindMorphDisplacementM':deltamax};rows.append(r);print(r)
(HERE/'target-portability-gate.json').write_text(json.dumps({'rows':rows,'reference':'Same corrected rest envelope and actual combined upper garment source ROI. Float32 morph offsets applied BEFORE exact linear skin matrices. No collision acceptance, no arbitrary pose/interpolation certification.','weightsSHA256':hashlib.sha256((HERE/'anatomical-weights.npz').read_bytes()).hexdigest()},indent=2))
