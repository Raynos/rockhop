"""Portable pose target for generated hoodie armhole.
API target(positions, weights, matrices, source=sourcePositions, joints=sourceCentres).
Returns desired world-space arrays and metadata. Root can inverse-LBS bake morphs.
No cloth simulator, materials, Blender drivers or GPU dependencies.
"""
import numpy as np

def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)

def target(positions,weights,matrices,source,joints):
 # Source exact alias consistency is maintained because each alias has same source,
 # same weight and same correction. Preserve unmodified head/hand arrays bit-exact.
 skin=[np.einsum('vj,jab,vb->va',w,matrices[:,:3,:],np.c_[p,np.ones(len(p))],optimize=False)for p,w in zip(positions,weights)]
 corrected=[p.copy()for p in skin];rows=[]
 for sg,a in [(1,6),(-1,10)]:
  rest=joints[a+1]-joints[a];rest/=np.linalg.norm(rest);axis=matrices[a,:3,:3]@rest;axis/=np.linalg.norm(axis)
  up=matrices[2,:3,:3]@np.array([0.,1.,0.]);normal=up-axis*np.dot(up,axis);ln=np.linalg.norm(normal)
  if ln<.2:rows.append({'sideSign':sg,'skipped':'arm parallel torso axis'});continue
  normal/=ln;shoulder=matrices[a,:3,:3]@joints[a]+matrices[a,:3,3]
  angle=np.arccos(np.clip(np.dot(axis,matrices[2,:3,:3]@rest),-1,1));full=np.arccos(np.clip(np.dot(rest,np.array([0,0,sg])),-1,1));activation=smooth(angle/full)
  maxlift=0.;changed=0
  for i in [0,2]:
   q=skin[i];original=source[i];along=(q-shoulder)@axis;depth=np.maximum(-.075-(q-shoulder)@normal,0)
   blend=smooth((along+.003)/.075)*smooth((.612-along)/.13)
   region=(original[:,2]*sg>0)*smooth((original[:,1]-1.105)/.055)*smooth((1.49-original[:,1])/.045)*smooth((abs(original[:,2])-.13)/.03)
   lift=.85*depth*blend*activation*region;corrected[i]+=lift[:,None]*normal
   maxlift=max(maxlift,float(lift.max(initial=0)));changed+=int((lift>1e-9).sum())
  rows.append({'sideSign':sg,'activation':float(activation),'maxCorrectionM':maxlift,'changedExportedVertices':changed,'armPlaneNormal':normal.tolist()})
 return corrected,{'method':'Monotone arm-plane compression of low generated underarm depth toward rotated lower sleeve75mm envelope, source torso/head/hands held. Rest exact. Candidate only.','sides':rows}
